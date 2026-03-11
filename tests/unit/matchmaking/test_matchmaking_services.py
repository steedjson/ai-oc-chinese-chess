"""
Matchmaking Service 测试
测试匹配服务层核心功能：队列管理、匹配算法、Elo 等级分系统
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import asdict

# 导入被测试模块
from matchmaking.queue import MatchmakingQueue, QueueUser
from matchmaking.algorithm import Matchmaker, MatchResult
from matchmaking.elo import (
    EloService, RankSegment, calculate_expected_score,
    calculate_elo_change, update_elo_rating, get_rank_segment
)


# ==================== QueueUser 测试 ====================

class TestQueueUser:
    """QueueUser 数据类测试"""
    
    def test_queue_user_creation(self):
        """测试 QueueUser 实例创建"""
        user = QueueUser(
            user_id='user_123',
            rating=1500,
            joined_at=time.time(),
            search_range=100,
            game_type='ranked'
        )
        
        assert user.user_id == 'user_123'
        assert user.rating == 1500
        assert user.search_range == 100
        assert user.game_type == 'ranked'
    
    def test_queue_user_to_dict(self):
        """测试转换为字典"""
        user = QueueUser(
            user_id='user_456',
            rating=1600,
            joined_at=1234567890.0,
            search_range=150,
            game_type='casual'
        )
        
        data = user.to_dict()
        
        assert data['user_id'] == 'user_456'
        assert data['rating'] == 1600
        assert data['joined_at'] == 1234567890.0
        assert data['search_range'] == 150
        assert data['game_type'] == 'casual'
    
    def test_queue_user_from_dict(self):
        """测试从字典创建"""
        data = {
            'user_id': 'user_789',
            'rating': 1400,
            'joined_at': 1234567890.0,
            'search_range': 200,
            'game_type': 'online'
        }
        
        user = QueueUser.from_dict(data)
        
        assert user.user_id == 'user_789'
        assert user.rating == 1400
        assert user.search_range == 200
        assert user.game_type == 'online'
    
    def test_queue_user_from_dict_defaults(self):
        """测试从字典创建的默认值"""
        data = {}  # 空字典
        
        user = QueueUser.from_dict(data)
        
        assert user.user_id == ''
        assert user.rating == 1500  # 默认值
        assert user.search_range == 100  # 默认值
        assert user.game_type == 'online'  # 默认值


# ==================== MatchmakingQueue 测试 ====================

class TestMatchmakingQueueInit:
    """MatchmakingQueue 初始化测试"""
    
    @patch('matchmaking.queue.redis')
    def test_queue_initialization(self, mock_redis):
        """测试队列初始化"""
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            
            assert queue.queue_prefix == 'matchmaking:queue'
            assert queue.user_prefix == 'matchmaking:user'
            assert queue.lock_prefix == 'matchmaking:lock'
            mock_redis.from_url.assert_called_once_with('redis://localhost:6379')


class TestJoinQueue:
    """加入队列测试"""
    
    @patch('matchmaking.queue.redis')
    def test_join_queue_success(self, mock_redis):
        """测试成功加入队列"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.set.return_value = True  # 锁获取成功
        mock_redis_instance.zrank.return_value = None  # 不在队列中
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.join_queue('user_123', 1500, 'ranked')
            
            assert result is True
            mock_redis_instance.zadd.assert_called_once()
            mock_redis_instance.hset.assert_called_once()
            mock_redis_instance.expire.assert_called_once()
            mock_redis_instance.delete.assert_called_once()  # 释放锁
    
    @patch('matchmaking.queue.redis')
    def test_join_queue_already_in_queue(self, mock_redis):
        """测试用户已在队列中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrank.return_value = 0  # 已在队列中
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.join_queue('user_123', 1500, 'ranked')
            
            assert result is False
            mock_redis_instance.zadd.assert_not_called()
    
    @patch('matchmaking.queue.redis')
    def test_join_queue_lock_failed(self, mock_redis):
        """测试获取锁失败"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.set.return_value = False  # 锁获取失败
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.join_queue('user_123', 1500, 'ranked')
            
            assert result is False
            mock_redis_instance.zadd.assert_not_called()


class TestLeaveQueue:
    """离开队列测试"""
    
    @patch('matchmaking.queue.redis')
    def test_leave_queue_success(self, mock_redis):
        """测试成功离开队列"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrem.return_value = 1  # 成功移除
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.leave_queue('user_123', 'ranked')
            
            assert result is True
            mock_redis_instance.zrem.assert_called_once()
            mock_redis_instance.delete.assert_called_once()
    
    @patch('matchmaking.queue.redis')
    def test_leave_queue_not_in_queue(self, mock_redis):
        """测试用户不在队列中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrem.return_value = 0  # 未移除
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.leave_queue('user_123', 'ranked')
            
            assert result is False


class TestIsInQueue:
    """检查是否在队列中测试"""
    
    @patch('matchmaking.queue.redis')
    def test_is_in_queue_true(self, mock_redis):
        """测试用户在队列中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrank.return_value = 0  # 在队列中
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.is_in_queue('user_123', 'ranked')
            
            assert result is True
    
    @patch('matchmaking.queue.redis')
    def test_is_in_queue_false(self, mock_redis):
        """测试用户不在队列中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrank.return_value = None  # 不在队列中
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.is_in_queue('user_123', 'ranked')
            
            assert result is False


class TestSearchOpponent:
    """搜索对手测试"""
    
    @patch('matchmaking.queue.redis')
    def test_search_opponent_found(self, mock_redis):
        """测试找到对手"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        
        # Mock 用户数据
        mock_redis_instance.hgetall.return_value = {
            b'rating': b'1500',
            b'joined_at': b'1234567890.0',
            b'search_range': b'100',
            b'game_type': b'ranked'
        }
        
        # Mock 搜索结果
        mock_redis_instance.zrangebyscore.return_value = [b'user_456', b'user_789']
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.search_opponent('user_123', 'ranked')
            
            assert result == 'user_456'  # 返回第一个对手
    
    @patch('matchmaking.queue.redis')
    def test_search_opponent_not_found(self, mock_redis):
        """测试未找到对手"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.hgetall.return_value = {}
        mock_redis_instance.zrangebyscore.return_value = []
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.search_opponent('user_123', 'ranked')
            
            assert result is None
    
    @patch('matchmaking.queue.redis')
    def test_search_opponent_filter_self(self, mock_redis):
        """测试过滤自己"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.hgetall.return_value = {
            b'rating': b'1500',
            b'joined_at': b'1234567890.0',
            b'search_range': b'100',
            b'game_type': b'ranked'
        }
        # 只返回自己
        mock_redis_instance.zrangebyscore.return_value = [b'user_123']
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.search_opponent('user_123', 'ranked')
            
            assert result is None


class TestExpandSearchRange:
    """扩大搜索范围测试"""
    
    @patch('matchmaking.queue.redis')
    def test_expand_search_range_success(self, mock_redis):
        """测试成功扩大搜索范围"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.hget.return_value = b'100'  # 当前范围
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.expand_search_range('user_123', 'ranked')
            
            assert result == 150  # 100 + 50
            mock_redis_instance.hset.assert_called_once()
    
    @patch('matchmaking.queue.redis')
    def test_expand_search_range_max_limit(self, mock_redis):
        """测试达到最大范围限制"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.hget.return_value = b'280'  # 接近最大值
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.expand_search_range('user_123', 'ranked')
            
            assert result == 300  # 最大值


class TestGetQueuePosition:
    """获取队列位置测试"""
    
    @patch('matchmaking.queue.redis')
    def test_get_queue_position_success(self, mock_redis):
        """测试成功获取队列位置"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrank.return_value = 5  # 排名第 6
        mock_redis_instance.zcard.return_value = 20  # 总共 20 人
        mock_redis_instance.hgetall.return_value = {
            b'joined_at': str(time.time() - 60).encode(),  # 1 分钟前加入
            b'search_range': b'100'
        }
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.get_queue_position('user_123', 'ranked')
            
            assert result['position'] == 6
            assert result['total'] == 20
            assert result['search_range'] == 100
            assert result['wait_time'] >= 60


class TestGetQueueStats:
    """获取队列统计测试"""
    
    @patch('matchmaking.queue.redis')
    def test_get_queue_stats_success(self, mock_redis):
        """测试成功获取队列统计"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zcard.return_value = 50  # 总人数
        mock_redis_instance.zcount.side_effect = [5, 10, 15, 10, 5, 5]  # 各分数段人数
        
        with patch('matchmaking.queue.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            queue = MatchmakingQueue()
            result = queue.get_queue_stats('ranked')
            
            assert result['total_players'] == 50
            assert len(result['rating_ranges']) == 6


# ==================== Matchmaker 测试 ====================

class TestMatchmakerInit:
    """Matchmaker 初始化测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_matchmaker_initialization(self, mock_queue_class, mock_redis):
        """测试匹配器初始化"""
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            
            assert matchmaker.queue is not None
            assert matchmaker.config is not None
            assert 'initial_range' in matchmaker.config


class TestFindOpponent:
    """寻找对手测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_find_opponent_success(self, mock_queue_class, mock_redis):
        """测试成功找到对手"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        # Mock 用户数据
        mock_user_data = QueueUser(
            user_id='user_123',
            rating=1500,
            joined_at=time.time(),
            search_range=100,
            game_type='ranked'
        )
        mock_queue.get_user_data.return_value = mock_user_data
        mock_queue.search_opponent.return_value = 'user_456'
        
        # Mock 对手数据
        mock_opponent_data = QueueUser(
            user_id='user_456',
            rating=1520,
            joined_at=time.time(),
            search_range=100,
            game_type='ranked'
        )
        mock_queue.get_user_data.side_effect = [mock_user_data, mock_opponent_data]
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            matchmaker.should_filter_opponent = Mock(return_value=False)
            
            result = matchmaker.find_opponent('user_123', 'ranked')
            
            assert result is not None
            assert result.user_id == 'user_123'
            assert result.opponent_id == 'user_456'
            assert result.rating_diff == 20
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_find_opponent_no_user_data(self, mock_queue_class, mock_redis):
        """测试用户数据不存在"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        mock_queue.get_user_data.return_value = None
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.find_opponent('user_123', 'ranked')
            
            assert result is None
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_find_opponent_no_opponent(self, mock_queue_class, mock_redis):
        """测试未找到对手"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        mock_user_data = QueueUser(
            user_id='user_123',
            rating=1500,
            joined_at=time.time(),
            search_range=100,
            game_type='ranked'
        )
        mock_queue.get_user_data.return_value = mock_user_data
        mock_queue.search_opponent.return_value = None
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.find_opponent('user_123', 'ranked')
            
            assert result is None


class TestShouldExpandSearch:
    """判断是否扩大搜索测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_should_expand_search_true(self, mock_queue_class, mock_redis):
        """测试应该扩大搜索"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            # 等待时间超过 30 秒
            joined_at = time.time() - 35
            
            result = matchmaker.should_expand_search(joined_at)
            
            assert result is True
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_should_expand_search_false(self, mock_queue_class, mock_redis):
        """测试不应该扩大搜索"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            # 等待时间不足 30 秒
            joined_at = time.time() - 15
            
            result = matchmaker.should_expand_search(joined_at)
            
            assert result is False


class TestCalculateDynamicRange:
    """计算动态搜索范围测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_calculate_dynamic_range_initial(self, mock_queue_class, mock_redis):
        """测试初始搜索范围"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.calculate_dynamic_range(0)  # 刚加入
            
            assert result == 100  # 初始范围
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_calculate_dynamic_range_expanded(self, mock_queue_class, mock_redis):
        """测试扩大后的搜索范围"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.calculate_dynamic_range(60)  # 等待 60 秒
            
            # 60 / 30 = 2 次扩大，100 + 2*50 = 200
            assert result == 200
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_calculate_dynamic_range_max(self, mock_queue_class, mock_redis):
        """测试最大搜索范围"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.calculate_dynamic_range(300)  # 等待 5 分钟
            
            assert result == 300  # 最大值


class TestSelectBestOpponent:
    """选择最佳对手测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_select_best_opponent_by_rating(self, mock_queue_class, mock_redis):
        """测试按等级分选择最佳对手"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        # Mock 对手数据
        opponent1 = QueueUser(user_id='opp1', rating=1400, joined_at=time.time(), search_range=100, game_type='ranked')
        opponent2 = QueueUser(user_id='opp2', rating=1490, joined_at=time.time(), search_range=100, game_type='ranked')
        opponent3 = QueueUser(user_id='opp3', rating=1600, joined_at=time.time(), search_range=100, game_type='ranked')
        
        mock_queue.get_user_data.side_effect = [opponent1, opponent2, opponent3]
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.select_best_opponent(['opp1', 'opp2', 'opp3'], 1500)
            
            assert result == 'opp2'  # 最接近 1500 分
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_select_best_opponent_empty_list(self, mock_queue_class, mock_redis):
        """测试空对手列表"""
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.select_best_opponent([], 1500)
            
            assert result is None


class TestRecentOpponentFilter:
    """最近对手过滤测试"""
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_record_recent_opponent(self, mock_queue_class, mock_redis):
        """测试记录最近对手"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            matchmaker.record_recent_opponent('user_123', 'user_456')
            
            mock_redis_instance.sadd.assert_called_once()
            mock_redis_instance.expire.assert_called_once()
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_should_filter_opponent_true(self, mock_queue_class, mock_redis):
        """测试应该过滤对手"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.sismember.return_value = True  # 在最近对手中
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.should_filter_opponent('user_123', 'user_456')
            
            assert result is True
    
    @patch('matchmaking.algorithm.redis')
    @patch('matchmaking.algorithm.MatchmakingQueue')
    def test_should_filter_opponent_false(self, mock_queue_class, mock_redis):
        """测试不应该过滤对手"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.sismember.return_value = False  # 不在最近对手中
        mock_queue = Mock()
        mock_queue_class.return_value = mock_queue
        
        with patch('matchmaking.algorithm.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            matchmaker = Matchmaker()
            result = matchmaker.should_filter_opponent('user_123', 'user_456')
            
            assert result is False


# ==================== Elo 工具函数测试 ====================

class TestEloUtilityFunctions:
    """Elo 工具函数测试"""
    
    def test_calculate_expected_score_equal(self):
        """测试计算预期胜率 - 分数相同"""
        expected = calculate_expected_score(1500, 1500)
        assert expected == 0.5  # 50% 胜率
    
    def test_calculate_expected_score_higher(self):
        """测试计算预期胜率 - 分数更高"""
        expected = calculate_expected_score(1600, 1500)
        assert expected > 0.5  # 胜率大于 50%
        assert expected < 1.0
    
    def test_calculate_expected_score_lower(self):
        """测试计算预期胜率 - 分数更低"""
        expected = calculate_expected_score(1400, 1500)
        assert expected < 0.5  # 胜率小于 50%
        assert expected > 0.0
    
    def test_calculate_elo_change_win(self):
        """测试计算 Elo 变化 - 胜利"""
        change = calculate_elo_change(1500, 1500, 'win')
        assert change > 0  # 胜利加分
    
    def test_calculate_elo_change_loss(self):
        """测试计算 Elo 变化 - 失败"""
        change = calculate_elo_change(1500, 1500, 'loss')
        assert change < 0  # 失败扣分
    
    def test_calculate_elo_change_draw(self):
        """测试计算 Elo 变化 - 平局"""
        change = calculate_elo_change(1500, 1500, 'draw')
        assert change == 0  # 平局不变
    
    def test_update_elo_rating_increase(self):
        """测试更新等级分 - 增加"""
        new_rating = update_elo_rating(1500, 1400, 'win')
        assert new_rating > 1500
    
    def test_update_elo_rating_decrease(self):
        """测试更新等级分 - 减少"""
        new_rating = update_elo_rating(1500, 1600, 'loss')
        assert new_rating < 1500
    
    def test_update_elo_rating_min_limit(self):
        """测试更新等级分 - 最小值限制"""
        new_rating = update_elo_rating(0, 2000, 'loss')
        assert new_rating >= 0
    
    def test_update_elo_rating_max_limit(self):
        """测试更新等级分 - 最大值限制"""
        new_rating = update_elo_rating(3000, 1000, 'win')
        assert new_rating <= 3000


class TestGetRankSegment:
    """段位获取测试"""
    
    def test_rank_bronze(self):
        """测试青铜段位"""
        assert get_rank_segment(800) == RankSegment.BRONZE
        assert get_rank_segment(1000) == RankSegment.BRONZE
    
    def test_rank_silver(self):
        """测试白银段位"""
        assert get_rank_segment(1001) == RankSegment.SILVER
        assert get_rank_segment(1200) == RankSegment.SILVER
    
    def test_rank_gold(self):
        """测试黄金段位"""
        assert get_rank_segment(1201) == RankSegment.GOLD
        assert get_rank_segment(1400) == RankSegment.GOLD
    
    def test_rank_platinum(self):
        """测试铂金段位"""
        assert get_rank_segment(1401) == RankSegment.PLATINUM
        assert get_rank_segment(1600) == RankSegment.PLATINUM
    
    def test_rank_diamond(self):
        """测试钻石段位"""
        assert get_rank_segment(1601) == RankSegment.DIAMOND
        assert get_rank_segment(1800) == RankSegment.DIAMOND
    
    def test_rank_master(self):
        """测试大师段位"""
        assert get_rank_segment(1801) == RankSegment.MASTER
        assert get_rank_segment(2500) == RankSegment.MASTER


# ==================== EloService 测试 ====================

class TestEloServiceInit:
    """EloService 初始化测试"""
    
    @patch('matchmaking.elo.redis')
    def test_elo_service_initialization(self, mock_redis):
        """测试 Elo 服务初始化"""
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            
            assert service.leaderboard_key == 'matchmaking:leaderboard'
            assert service.history_prefix == 'matchmaking:history:'


class TestUpdatePlayerRating:
    """更新玩家等级分测试"""
    
    @patch('matchmaking.elo.redis')
    @patch('matchmaking.elo.User')
    def test_update_player_rating_win(self, mock_user_model, mock_redis):
        """测试胜利后更新等级分"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        
        # Mock 玩家和对手
        mock_player = Mock()
        mock_player.id = 1
        mock_player.elo_rating = 1500
        
        mock_opponent = Mock()
        mock_opponent.id = 2
        mock_opponent.elo_rating = 1500
        
        mock_user_model.objects.get.side_effect = [mock_player, mock_opponent]
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            player_new, opponent_new = service.update_player_rating(
                '1', '2', 'game_123', 'win'
            )
            
            # 胜利加分，失败扣分
            assert player_new > 1500
            assert opponent_new < 1500
            mock_player.save.assert_called_once()
            mock_opponent.save.assert_called_once()
    
    @patch('matchmaking.elo.redis')
    @patch('matchmaking.elo.User')
    def test_update_player_rating_user_not_found(self, mock_user_model, mock_redis):
        """测试用户不存在"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            
            with pytest.raises(ValueError):
                service.update_player_rating('1', '2', 'game_123', 'win')


class TestGetLeaderboard:
    """获取排行榜测试"""
    
    @patch('matchmaking.elo.redis')
    def test_get_leaderboard_success(self, mock_redis):
        """测试成功获取排行榜"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        
        # Mock 排行榜数据
        mock_redis_instance.zrevrange.return_value = [
            (b'user_1', 1800),
            (b'user_2', 1700),
            (b'user_3', 1600)
        ]
        mock_redis_instance.zcard.return_value = 100
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_leaderboard(page=1, page_size=20)
            
            assert result['page'] == 1
            assert result['page_size'] == 20
            assert result['total'] == 100
            assert len(result['players']) == 3
    
    @patch('matchmaking.elo.redis')
    def test_get_leaderboard_empty(self, mock_redis):
        """测试空排行榜"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrevrange.return_value = []
        mock_redis_instance.zcard.return_value = 0
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_leaderboard()
            
            assert result['total'] == 0
            assert result['players'] == []


class TestGetUserRating:
    """获取用户等级分测试"""
    
    @patch('matchmaking.elo.User')
    def test_get_user_rating_success(self, mock_user_model):
        """测试成功获取用户等级分"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.elo_rating = 1500
        mock_user_model.objects.get.return_value = mock_user
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_user_rating('1')
            
            assert result is not None
            assert result['rating'] == 1500
            assert result['segment'] == 'gold'
    
    @patch('matchmaking.elo.User')
    def test_get_user_rating_not_found(self, mock_user_model):
        """测试用户不存在"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_user_rating('999')
            
            assert result is None


class TestGetRatingHistory:
    """获取等级分历史测试"""
    
    @patch('matchmaking.elo.redis')
    def test_get_rating_history_success(self, mock_redis):
        """测试成功获取历史记录"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.lrange.return_value = [
            b"{'rating': 1500, 'game_id': 'game_1'}",
            b"{'rating': 1480, 'game_id': 'game_2'}"
        ]
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_rating_history('user_123', limit=20)
            
            assert len(result) == 2


class TestGetUsersInRatingRange:
    """获取分数范围内用户测试"""
    
    @patch('matchmaking.elo.redis')
    def test_get_users_in_rating_range_success(self, mock_redis):
        """测试成功获取范围内用户"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.zrangebyscore.return_value = [
            (b'user_1', 1450),
            (b'user_2', 1480)
        ]
        
        with patch('matchmaking.elo.settings') as mock_settings:
            mock_settings.REDIS_URL = 'redis://localhost:6379'
            
            service = EloService()
            result = service.get_users_in_rating_range(1400, 1500, limit=10)
            
            assert len(result) == 2
            assert result[0]['rating'] == 1450


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
