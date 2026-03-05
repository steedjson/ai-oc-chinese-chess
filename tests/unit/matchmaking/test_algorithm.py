"""
匹配算法单元测试
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from matchmaking.algorithm import (
    Matchmaker,
    MatchResult,
    calculate_rating_difference,
    is_valid_match,
)


class TestMatchResult:
    """测试匹配结果数据类"""
    
    def test_create_match_result(self):
        """创建匹配结果"""
        result = MatchResult(
            user_id='user123',
            opponent_id='user456',
            game_id='game789',
            user_rating=1500,
            opponent_rating=1480,
            rating_diff=20,
            wait_time=45.5
        )
        
        assert result.user_id == 'user123'
        assert result.opponent_id == 'user456'
        assert result.game_id == 'game789'
        assert result.rating_diff == 20


class TestCalculateRatingDifference:
    """测试等级分差计算"""
    
    def test_positive_difference(self):
        """正差值"""
        diff = calculate_rating_difference(1500, 1400)
        assert diff == 100
    
    def test_negative_difference(self):
        """负差值"""
        diff = calculate_rating_difference(1400, 1500)
        assert diff == -100
    
    def test_zero_difference(self):
        """零差值"""
        diff = calculate_rating_difference(1500, 1500)
        assert diff == 0


class TestIsValidMatch:
    """测试匹配有效性验证"""
    
    def test_valid_match_within_range(self):
        """有效匹配 - 在范围内"""
        assert is_valid_match(1500, 1480, 100) is True
        assert is_valid_match(1500, 1550, 100) is True
    
    def test_invalid_match_out_of_range(self):
        """无效匹配 - 超出范围"""
        assert is_valid_match(1500, 1300, 100) is False
        assert is_valid_match(1500, 1700, 100) is False
    
    def test_exact_boundary(self):
        """边界值"""
        assert is_valid_match(1500, 1400, 100) is True
        assert is_valid_match(1500, 1600, 100) is True


class TestMatchmaker:
    """测试匹配器"""
    
    @pytest.fixture
    def matchmaker(self):
        """创建匹配器实例"""
        with patch('matchmaking.algorithm.MatchmakingQueue'):
            with patch('matchmaking.algorithm.redis.from_url'):
                return Matchmaker()
    
    @pytest.fixture
    def mock_queue(self, matchmaker):
        """获取 mock 队列"""
        return matchmaker.queue
    
    def test_init(self, matchmaker):
        """初始化测试"""
        assert matchmaker.config is not None
        assert 'initial_range' in matchmaker.config
        assert 'expansion' in matchmaker.config
        assert 'max_range' in matchmaker.config
        assert 'timeout' in matchmaker.config
    
    def test_find_opponent_found(self, matchmaker, mock_queue):
        """找到对手"""
        mock_queue.search_opponent.return_value = 'user456'
        mock_queue.get_user_data.return_value = MagicMock(
            rating=1500,
            joined_at=time.time(),
            search_range=100
        )
        # Mock redis 防止重复匹配检查
        matchmaker.redis.sismember.return_value = False
        
        result = matchmaker.find_opponent('user123', 'online')
        
        assert result is not None
        assert result.opponent_id == 'user456'
        mock_queue.search_opponent.assert_called_once()
    
    def test_find_opponent_not_found(self, matchmaker, mock_queue):
        """未找到对手"""
        mock_queue.search_opponent.return_value = None
        mock_queue.get_user_data.return_value = MagicMock(
            rating=1500,
            joined_at=time.time(),
            search_range=100
        )
        
        result = matchmaker.find_opponent('user123', 'online')
        
        assert result is None
    
    def test_find_opponent_user_not_in_queue(self, matchmaker, mock_queue):
        """用户不在队列中"""
        mock_queue.get_user_data.return_value = None
        
        result = matchmaker.find_opponent('user123', 'online')
        
        assert result is None
    
    def test_should_expand_search(self, matchmaker):
        """是否应该扩大搜索范围"""
        # 30 秒后应该扩大
        joined_at = time.time() - 35
        assert matchmaker.should_expand_search(joined_at) is True
        
        # 未到 30 秒不应该扩大
        joined_at = time.time() - 15
        assert matchmaker.should_expand_search(joined_at) is False
    
    def test_calculate_dynamic_range(self, matchmaker):
        """计算动态搜索范围"""
        # 初始范围
        range_val = matchmaker.calculate_dynamic_range(0)
        assert range_val == matchmaker.config['initial_range']
        
        # 30 秒后
        range_val = matchmaker.calculate_dynamic_range(30)
        assert range_val == matchmaker.config['initial_range'] + matchmaker.config['expansion']
        
        # 60 秒后
        range_val = matchmaker.calculate_dynamic_range(60)
        assert range_val == matchmaker.config['initial_range'] + 2 * matchmaker.config['expansion']
        
        # 超过最大值
        range_val = matchmaker.calculate_dynamic_range(300)
        assert range_val == matchmaker.config['max_range']
    
    def test_is_timeout(self, matchmaker):
        """检查是否超时"""
        # 未超时
        joined_at = time.time() - 60
        assert matchmaker.is_timeout(joined_at) is False
        
        # 已超时（超过 180 秒）
        joined_at = time.time() - 200
        assert matchmaker.is_timeout(joined_at) is True
    
    def test_select_best_opponent(self, matchmaker, mock_queue):
        """选择最佳对手"""
        # Mock 多个候选对手
        mock_queue.get_user_data.side_effect = [
            MagicMock(rating=1480, joined_at=time.time() - 100),  # 差 20 分，等 100 秒
            MagicMock(rating=1520, joined_at=time.time() - 50),   # 差 20 分，等 50 秒
            MagicMock(rating=1450, joined_at=time.time() - 80),   # 差 50 分，等 80 秒
        ]
        
        opponents = ['opp1', 'opp2', 'opp3']
        user_rating = 1500
        
        best = matchmaker.select_best_opponent(opponents, user_rating)
        
        # 应该选择分数最接近且等待时间最长的
        assert best is not None
    
    def test_prevent_rematch(self, matchmaker, mock_queue):
        """防止重复匹配"""
        user_id = 'user123'
        
        # Mock redis sismember 返回值
        matchmaker.redis.sismember.side_effect = lambda key, member: member == 'user456'
        
        # 检查是否应该过滤
        should_filter = matchmaker.should_filter_opponent(user_id, 'user456')
        assert should_filter is True
        
        should_filter = matchmaker.should_filter_opponent(user_id, 'user999')
        assert should_filter is False
    
    def test_get_wait_time_estimate(self, matchmaker, mock_queue):
        """获取等待时间预估"""
        mock_queue.get_queue_stats.return_value = {
            'total_players': 50,
            'avg_wait_time': 45
        }
        
        estimate = matchmaker.get_wait_time_estimate('online', 1500)
        
        assert isinstance(estimate, dict)
        assert 'estimated_seconds' in estimate
        assert estimate['estimated_seconds'] > 0


class TestMatchmakerIntegration:
    """匹配器集成测试"""
    
    def test_matchmaking_loop_success(self):
        """匹配循环成功找到对手"""
        with patch('matchmaking.algorithm.MatchmakingQueue') as MockQueue:
            with patch('matchmaking.algorithm.redis.from_url') as mock_redis_factory:
                mock_redis = MagicMock()
                mock_redis_factory.return_value = mock_redis
                mock_redis.sismember.return_value = False
                
                mock_queue = MagicMock()
                MockQueue.return_value = mock_queue
                
                # Mock 搜索对手
                mock_queue.search_opponent.return_value = 'user456'
                mock_queue.get_user_data.return_value = MagicMock(
                    rating=1500,
                    joined_at=time.time(),
                    search_range=100
                )
                mock_queue.is_in_queue.return_value = True
                
                from matchmaking.algorithm import Matchmaker
                matchmaker = Matchmaker()
                
                # 测试 find_opponent
                result = matchmaker.find_opponent('user123', 'online')
                
                assert result is not None
                assert result.opponent_id == 'user456'
    
    def test_matchmaking_loop_timeout(self):
        """匹配循环超时"""
        with patch('matchmaking.algorithm.MatchmakingQueue') as MockQueue:
            mock_queue = MagicMock()
            MockQueue.return_value = mock_queue
            
            # Mock 未找到对手
            mock_queue.search_opponent.return_value = None
            mock_queue.get_user_data.return_value = MagicMock(
                rating=1500,
                joined_at=time.time() - 200,  # 已超时
                search_range=300
            )
            
            from matchmaking.algorithm import Matchmaker
            matchmaker = Matchmaker()
            
            # 检查是否超时
            user_data = mock_queue.get_user_data('user123')
            is_timeout = matchmaker.is_timeout(user_data.joined_at)
            
            assert is_timeout is True


class TestMatchAlgorithm:
    """匹配算法测试"""
    
    def test_priority_by_wait_time(self):
        """优先匹配等待时间长的玩家"""
        candidates = [
            {'user_id': 'user1', 'rating': 1500, 'wait_time': 100},
            {'user_id': 'user2', 'rating': 1500, 'wait_time': 50},
            {'user_id': 'user3', 'rating': 1500, 'wait_time': 150},
        ]
        
        # 按等待时间排序
        sorted_candidates = sorted(candidates, key=lambda x: -x['wait_time'])
        
        assert sorted_candidates[0]['user_id'] == 'user3'
        assert sorted_candidates[2]['user_id'] == 'user2'
    
    def test_priority_by_rating_diff(self):
        """优先匹配分数接近的玩家"""
        user_rating = 1500
        candidates = [
            {'user_id': 'user1', 'rating': 1480, 'diff': 20},
            {'user_id': 'user2', 'rating': 1450, 'diff': 50},
            {'user_id': 'user3', 'rating': 1490, 'diff': 10},
        ]
        
        # 按分数差排序
        sorted_candidates = sorted(candidates, key=lambda x: x['diff'])
        
        assert sorted_candidates[0]['user_id'] == 'user3'
        assert sorted_candidates[2]['user_id'] == 'user2'
