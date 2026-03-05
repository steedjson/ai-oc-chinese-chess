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
