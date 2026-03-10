"""
匹配队列管理单元测试
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone

from matchmaking.queue import (
    MatchmakingQueue,
    QueueUser,
    MATCH_TIMEOUT,
    SEARCH_EXPANSION_INTERVAL,
)


class TestQueueUser:
    """测试队列用户数据类"""
    
    def test_create_queue_user(self):
        """创建队列用户"""
        user = QueueUser(
            user_id='user123',
            rating=1500,
            joined_at=time.time(),
            search_range=100,
            game_type='online'
        )
        
        assert user.user_id == 'user123'
        assert user.rating == 1500
        assert user.search_range == 100
        assert user.game_type == 'online'


class TestMatchmakingQueue:
    """测试匹配队列管理"""
    
    @pytest.fixture
    def queue(self):
        """创建队列实例"""
        with patch('matchmaking.queue.redis.from_url'):
            return MatchmakingQueue()
    
    @pytest.fixture
    def mock_redis(self, queue):
        """获取 mock redis"""
        return queue.redis
    
    def test_join_queue_success(self, queue, mock_redis):
        """成功加入队列"""
        mock_redis.zrank.return_value = None  # 不在队列中
        mock_redis.set.return_value = True  # 锁获取成功
        
        result = queue.join_queue('user123', 1500, 'online')
        
        assert result is True
        mock_redis.zadd.assert_called_once()
        mock_redis.hset.assert_called_once()
    
    def test_join_queue_already_in_queue(self, queue, mock_redis):
        """已在队列中，加入失败"""
        mock_redis.zrank.return_value = 5  # 已在队列中
        
        result = queue.join_queue('user123', 1500, 'online')
        
        assert result is False
        mock_redis.zadd.assert_not_called()
    
    def test_join_queue_failed_to_get_lock(self, queue, mock_redis):
        """获取锁失败"""
        mock_redis.zrank.return_value = None  # 不在队列中
        mock_redis.set.return_value = False  # 锁获取失败
        
        result = queue.join_queue('user123', 1500, 'online')
        
        assert result is False
        mock_redis.zadd.assert_not_called()
    
    def test_leave_queue_success(self, queue, mock_redis):
        """成功离开队列"""
        mock_redis.zrem.return_value = 1  # 成功移除
        
        result = queue.leave_queue('user123', 'online')
        
        assert result is True
        mock_redis.zrem.assert_called_once()
        mock_redis.delete.assert_called_once()
    
    def test_leave_queue_not_in_queue(self, queue, mock_redis):
        """不在队列中，离开失败"""
        mock_redis.zrem.return_value = 0  # 未移除
        
        result = queue.leave_queue('user123', 'online')
        
        assert result is False
    
    def test_is_in_queue_true(self, queue, mock_redis):
        """检查在队列中 - 返回 True"""
        mock_redis.zrank.return_value = 5
        
        result = queue.is_in_queue('user123', 'online')
        
        assert result is True
    
    def test_is_in_queue_false(self, queue, mock_redis):
        """检查在队列中 - 返回 False"""
        mock_redis.zrank.return_value = None
        
        result = queue.is_in_queue('user123', 'online')
        
        assert result is False
    
    def test_search_opponent_found(self, queue, mock_redis):
        """搜索到对手"""
        # Mock 用户数据
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': str(time.time()).encode()
        }
        
        # Mock 搜索结果
        mock_redis.zrangebyscore.return_value = [b'user456', b'user789']
        
        result = queue.search_opponent('user123', 'online')
        
        assert result is not None
        mock_redis.zrangebyscore.assert_called_once()
    
    def test_search_opponent_not_found(self, queue, mock_redis):
        """未搜索到对手"""
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': str(time.time()).encode()
        }
        
        # 只返回自己
        mock_redis.zrangebyscore.return_value = [b'user123']
        
        result = queue.search_opponent('user123', 'online')
        
        assert result is None
    
    def test_search_opponent_user_not_in_queue(self, queue, mock_redis):
        """用户不在队列中，搜索失败"""
        mock_redis.hgetall.return_value = {}
        
        result = queue.search_opponent('user123', 'online')
        
        assert result is None
    
    def test_expand_search_range(self, queue, mock_redis):
        """扩大搜索范围"""
        mock_redis.hget.return_value = b'100'  # 当前范围 100
        
        new_range = queue.expand_search_range(
            'user123',
            'online',
            expansion=50,
            max_range=300
        )
        
        assert new_range == 150
        mock_redis.hset.assert_called_once()
    
    def test_expand_search_range_reaches_max(self, queue, mock_redis):
        """搜索范围达到最大值"""
        mock_redis.hget.return_value = b'280'  # 当前范围 280
        
        new_range = queue.expand_search_range(
            'user123',
            'online',
            expansion=50,
            max_range=300
        )
        
        assert new_range == 300  # 限制在最大值
    
    def test_get_queue_position(self, queue, mock_redis):
        """获取队列位置"""
        mock_redis.zrank.return_value = 5
        mock_redis.zcard.return_value = 50
        mock_redis.hgetall.return_value = {
            b'search_range': b'100',
            b'joined_at': str(time.time() - 60).encode()  # 1 分钟前加入
        }
        
        position = queue.get_queue_position('user123', 'online')
        
        assert position['position'] == 6  # rank + 1
        assert position['total'] == 50
        assert position['search_range'] == 100
        assert position['wait_time'] > 59  # 约 60 秒
    
    def test_get_queue_stats(self, queue, mock_redis):
        """获取队列统计信息"""
        # Mock 各分数段人数
        mock_redis.zcount.side_effect = [3, 5, 8, 6, 2, 1]
        mock_redis.zrange.return_value = []
        
        stats = queue.get_queue_stats('online')
        
        assert 'total_players' in stats
        assert 'rating_ranges' in stats
        assert len(stats['rating_ranges']) == 6  # 6 个分数段
    
    def test_get_user_data(self, queue, mock_redis):
        """获取用户队列数据"""
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': b'1234567890',
            b'game_type': b'online'
        }
        
        user_data = queue.get_user_data('user123')
        
        assert user_data is not None
        assert user_data.rating == 1500
        assert user_data.search_range == 100
    
    def test_get_user_data_not_found(self, queue, mock_redis):
        """用户数据不存在"""
        mock_redis.hgetall.return_value = {}
        
        user_data = queue.get_user_data('user123')
        
        assert user_data is None
    
    def test_is_match_timeout_false(self, queue):
        """检查是否超时 - 未超时"""
        joined_at = time.time() - 60  # 1 分钟前
        
        result = queue.is_match_timeout(joined_at)
        
        assert result is False
    
    def test_is_match_timeout_true(self, queue):
        """检查是否超时 - 已超时"""
        joined_at = time.time() - 200  # 200 秒前
        
        result = queue.is_match_timeout(joined_at)
        
        assert result is True


class TestMatchmakingQueueIntegration:
    """匹配队列集成测试"""
    
    @pytest.mark.django_db
    def test_full_queue_flow(self):
        """完整队列流程测试"""
        with patch('matchmaking.queue.redis.from_url') as mock_redis_factory:
            mock_redis = MagicMock()
            mock_redis_factory.return_value = mock_redis
            
            queue = MatchmakingQueue()
            
            # 1. 加入队列
            mock_redis.zrank.return_value = None
            mock_redis.set.return_value = True
            assert queue.join_queue('user1', 1500, 'online') is True
            
            # 2. 检查在队列中
            mock_redis.zrank.return_value = 0
            assert queue.is_in_queue('user1', 'online') is True
            
            # 3. 搜索对手
            mock_redis.hgetall.return_value = {
                b'rating': b'1500',
                b'search_range': b'100',
                b'joined_at': str(time.time()).encode()
            }
            mock_redis.zrangebyscore.return_value = [b'user2']
            opponent = queue.search_opponent('user1', 'online')
            assert opponent is not None
            
            # 4. 离开队列
            mock_redis.zrem.return_value = 1
            assert queue.leave_queue('user1', 'online') is True
            
            # 5. 检查不在队列中
            mock_redis.zrank.return_value = None
            assert queue.is_in_queue('user1', 'online') is False


class TestMatchmakingQueueCleanup:
    """测试队列清理功能"""
    
    @pytest.fixture
    def queue(self):
        """创建队列实例"""
        with patch('matchmaking.queue.redis.from_url'):
            return MatchmakingQueue()
    
    @pytest.fixture
    def mock_redis(self, queue):
        """获取 mock redis"""
        return queue.redis
    
    def test_get_all_queued_users(self, queue, mock_redis):
        """测试获取所有队列中的用户"""
        mock_redis.zrange.return_value = [b'user1', b'user2', b'user3']
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': str(time.time()).encode(),
            b'game_type': b'online'
        }
        
        users = queue.get_all_queued_users('online', limit=10)
        
        assert len(users) == 3
        mock_redis.zrange.assert_called_once()
    
    def test_get_all_queued_users_empty(self, queue, mock_redis):
        """测试获取空队列"""
        mock_redis.zrange.return_value = []
        
        users = queue.get_all_queued_users('online')
        
        assert users == []
    
    def test_get_all_queued_users_with_missing_data(self, queue, mock_redis):
        """测试获取用户时部分数据缺失"""
        mock_redis.zrange.return_value = [b'user1', b'user2']
        # 第一个用户有数据，第二个没有
        mock_redis.hgetall.side_effect = [
            {
                b'rating': b'1500',
                b'search_range': b'100',
                b'joined_at': str(time.time()).encode(),
                b'game_type': b'online'
            },
            {}  # 空数据
        ]
        
        users = queue.get_all_queued_users('online')
        
        assert len(users) == 1  # 只有第一个用户
    
    def test_clear_expired_queues(self, queue, mock_redis):
        """测试清理超期队列"""
        # Mock 队列中的用户
        mock_redis.zrange.return_value = [b'user1', b'user2', b'user3']
        
        # Mock 用户数据 - user1 和 user3 超时，user2 未超时
        def get_user_data_side_effect(user_id):
            if user_id == 'user1':
                return QueueUser(
                    user_id='user1',
                    rating=1500,
                    joined_at=time.time() - 200,  # 超时
                    search_range=100,
                    game_type='online'
                )
            elif user_id == 'user2':
                return QueueUser(
                    user_id='user2',
                    rating=1600,
                    joined_at=time.time() - 30,  # 未超时
                    search_range=100,
                    game_type='online'
                )
            elif user_id == 'user3':
                return QueueUser(
                    user_id='user3',
                    rating=1700,
                    joined_at=time.time() - 250,  # 超时
                    search_range=100,
                    game_type='online'
                )
            return None
        
        queue.get_user_data = get_user_data_side_effect
        mock_redis.zrem.return_value = 1
        
        queue.clear_expired_queues()
        
        # 应该调用 leave_queue 两次（user1 和 user3）
        assert mock_redis.zrem.call_count >= 2
    
    def test_clear_expired_queues_empty(self, queue, mock_redis):
        """测试清理空队列"""
        mock_redis.zrange.return_value = []
        
        queue.clear_expired_queues()
        
        # 不应该有任何操作
        mock_redis.zrem.assert_not_called()
    
    def test_clear_expired_queues_multiple_game_types(self, queue, mock_redis):
        """测试清理多种游戏类型的队列"""
        mock_redis.zrange.return_value = []  # 所有队列都为空
        
        queue.clear_expired_queues()
        
        # 应该检查多种游戏类型
        assert mock_redis.zrange.call_count >= 3  # online, ranked, casual
    
    def test_is_match_timeout_edge_cases(self, queue):
        """测试超时判断边界情况"""
        current_time = time.time()
        
        # 刚好在超时边界 - 使用 > 判断，所以相等时不超时
        joined_at_exactly = current_time - MATCH_TIMEOUT
        # 超时 1 秒
        joined_at_over = current_time - MATCH_TIMEOUT - 1
        # 差 1 秒超时
        joined_at_under = current_time - MATCH_TIMEOUT + 1
        
        # 注意：is_match_timeout 使用 > 而不是 >=
        # 当 elapsed == MATCH_TIMEOUT 时，返回 False
        # 当 elapsed > MATCH_TIMEOUT 时，返回 True
        # 由于时间精度问题，我们使用近似判断
        result_exactly = queue.is_match_timeout(joined_at_exactly)
        result_over = queue.is_match_timeout(joined_at_over)
        result_under = queue.is_match_timeout(joined_at_under)
        
        # 超时 1 秒应该返回 True
        assert result_over is True
        # 差 1 秒超时应该返回 False
        assert result_under is False


class TestMatchmakingQueueEdgeCases:
    """测试队列边界情况"""
    
    @pytest.fixture
    def queue(self):
        """创建队列实例"""
        with patch('matchmaking.queue.redis.from_url'):
            return MatchmakingQueue()
    
    @pytest.fixture
    def mock_redis(self, queue):
        """获取 mock redis"""
        return queue.redis
    
    def test_search_opponent_filters_self(self, queue, mock_redis):
        """测试搜索对手时过滤自己"""
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': str(time.time()).encode()
        }
        
        # 只返回自己
        mock_redis.zrangebyscore.return_value = [b'user123']
        
        result = queue.search_opponent('user123', 'online')
        
        assert result is None
    
    def test_search_opponent_bytes_handling(self, queue, mock_redis):
        """测试处理字节类型的用户 ID"""
        mock_redis.hgetall.return_value = {
            b'rating': b'1500',
            b'search_range': b'100',
            b'joined_at': str(time.time()).encode()
        }
        
        # 返回字节类型的用户 ID
        mock_redis.zrangebyscore.return_value = [b'user456', b'user789']
        
        result = queue.search_opponent('user123', 'online')
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_get_queue_position_user_not_found(self, queue, mock_redis):
        """测试获取队列位置时用户不存在"""
        mock_redis.zrank.return_value = None
        mock_redis.zcard.return_value = 10
        mock_redis.hgetall.return_value = {}
        
        position = queue.get_queue_position('invalid_user', 'online')
        
        assert position['position'] == 0
        assert position['total'] == 10
    
    def test_get_queue_stats_empty_queue(self, queue, mock_redis):
        """测试空队列的统计信息"""
        mock_redis.zcount.return_value = 0
        mock_redis.zcard.return_value = 0
        mock_redis.zrange.return_value = []
        
        stats = queue.get_queue_stats('online')
        
        assert stats['total_players'] == 0
        assert stats['avg_wait_time'] == 0
    
    def test_expand_search_range_below_initial(self, queue, mock_redis):
        """测试搜索范围低于初始值"""
        mock_redis.hget.return_value = b'50'  # 当前范围 50（低于初始值）
        
        new_range = queue.expand_search_range('user123', 'online', expansion=50, max_range=300)
        
        assert new_range == 100  # 50 + 50
    
    def test_join_queue_concurrent_lock(self, queue, mock_redis):
        """测试并发加入队列时的锁处理"""
        mock_redis.zrank.return_value = None
        mock_redis.set.return_value = False  # 获取锁失败
        
        result = queue.join_queue('user123', 1500, 'online')
        
        assert result is False
        mock_redis.zadd.assert_not_called()
    
    def test_leave_queue_user_not_in_queue(self, queue, mock_redis):
        """测试离开不在的队列"""
        mock_redis.zrem.return_value = 0
        
        result = queue.leave_queue('user123', 'online')
        
        assert result is False
    
    def test_calculate_avg_wait_time_no_users(self, queue, mock_redis):
        """测试计算平均等待时间时无用户"""
        mock_redis.zrange.return_value = []
        
        avg_wait = queue._calculate_avg_wait_time('online')
        
        assert avg_wait == 0
    
    def test_queue_user_to_dict(self):
        """测试 QueueUser 转换为字典"""
        user = QueueUser(
            user_id='user123',
            rating=1500,
            joined_at=1234567890.0,
            search_range=100,
            game_type='ranked'
        )
        
        data = user.to_dict()
        
        assert data['user_id'] == 'user123'
        assert data['rating'] == 1500
        assert data['search_range'] == 100
        assert data['game_type'] == 'ranked'
    
    def test_queue_user_from_dict(self):
        """测试从字典创建 QueueUser"""
        data = {
            'user_id': 'user456',
            'rating': 1600,
            'joined_at': 1234567890.0,
            'search_range': 150,
            'game_type': 'casual'
        }
        
        user = QueueUser.from_dict(data)
        
        assert user.user_id == 'user456'
        assert user.rating == 1600
        assert user.search_range == 150
        assert user.game_type == 'casual'
    
    def test_queue_user_from_dict_defaults(self):
        """测试从字典创建 QueueUser 使用默认值"""
        data = {}
        
        user = QueueUser.from_dict(data)
        
        assert user.user_id == ''
        assert user.rating == 1500  # 默认值
        assert user.search_range == 100  # 默认值
        assert user.game_type == 'online'  # 默认值
