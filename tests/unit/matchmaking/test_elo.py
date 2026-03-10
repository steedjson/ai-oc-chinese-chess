"""
Elo 等级分系统单元测试
"""
import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# 设置 Django 环境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from matchmaking.elo import (
    calculate_expected_score,
    calculate_elo_change,
    update_elo_rating,
    get_rank_segment,
    RankSegment,
    K_FACTOR,
    INITIAL_RATING,
    MIN_RATING,
    MAX_RATING,
    EloService,
    get_segment_boundaries,
)


class TestCalculateExpectedScore:
    """测试预期胜率计算"""
    
    def test_equal_ratings(self):
        """相同等级分，预期胜率应为 0.5"""
        expected = calculate_expected_score(1500, 1500)
        assert expected == pytest.approx(0.5, rel=0.001)
    
    def test_higher_rating(self):
        """较高等级分，预期胜率应大于 0.5"""
        expected = calculate_expected_score(1600, 1500)
        assert expected > 0.5
        assert expected == pytest.approx(0.64, rel=0.01)
    
    def test_lower_rating(self):
        """较低等级分，预期胜率应小于 0.5"""
        expected = calculate_expected_score(1400, 1500)
        assert expected < 0.5
        assert expected == pytest.approx(0.36, rel=0.01)
    
    def test_large_difference(self):
        """等级分差距很大时，预期胜率接近 1 或 0"""
        # 400 分差距
        expected_high = calculate_expected_score(1900, 1500)
        assert expected_high > 0.9
        
        expected_low = calculate_expected_score(1100, 1500)
        assert expected_low < 0.1


class TestCalculateEloChange:
    """测试 Elo 分数变化计算"""
    
    def test_win_against_equal_opponent(self):
        """战胜相同等级分对手，应获得约 16 分"""
        change = calculate_elo_change(1500, 1500, 'win')
        assert change == pytest.approx(16, rel=0.1)
    
    def test_loss_against_equal_opponent(self):
        """输给相同等级分对手，应损失约 16 分"""
        change = calculate_elo_change(1500, 1500, 'loss')
        assert change == pytest.approx(-16, rel=0.1)
    
    def test_draw_against_equal_opponent(self):
        """与相同等级分对手和棋，分数不变"""
        change = calculate_elo_change(1500, 1500, 'draw')
        assert change == 0
    
    def test_win_against_higher_rated(self):
        """战胜较高等级分对手，应获得更多分数"""
        change = calculate_elo_change(1400, 1600, 'win')
        assert change > 16
    
    def test_loss_against_lower_rated(self):
        """输给较低等级分对手，应损失更多分数"""
        change = calculate_elo_change(1600, 1400, 'loss')
        assert change < -16
    
    def test_custom_k_factor(self):
        """自定义 K 因子"""
        change = calculate_elo_change(1500, 1500, 'win', k_factor=20)
        assert change == pytest.approx(10, rel=0.1)


class TestUpdateEloRating:
    """测试等级分更新"""
    
    def test_win_updates_rating(self):
        """胜利后等级分应增加"""
        new_rating = update_elo_rating(1500, 1500, 'win')
        assert new_rating > 1500
    
    def test_loss_updates_rating(self):
        """失败后等级分应减少"""
        new_rating = update_elo_rating(1500, 1500, 'loss')
        assert new_rating < 1500
    
    def test_draw_updates_rating(self):
        """和棋后等级分应不变（对手分数相同时）"""
        new_rating = update_elo_rating(1500, 1500, 'draw')
        assert new_rating == 1500
    
    def test_respects_min_rating(self):
        """等级分不应低于最小值"""
        new_rating = update_elo_rating(100, 2000, 'loss')
        assert new_rating >= MIN_RATING
    
    def test_respects_max_rating(self):
        """等级分不应超过最大值"""
        new_rating = update_elo_rating(2900, 1000, 'win')
        assert new_rating <= MAX_RATING


class TestGetRankSegment:
    """测试段位系统"""
    
    def test_bronze_segment(self):
        """低分段应为青铜"""
        assert get_rank_segment(800) == RankSegment.BRONZE
        assert get_rank_segment(1000) == RankSegment.BRONZE
    
    def test_silver_segment(self):
        """中段分应为白银"""
        assert get_rank_segment(1001) == RankSegment.SILVER
        assert get_rank_segment(1200) == RankSegment.SILVER
    
    def test_gold_segment(self):
        """中高分应为黄金"""
        assert get_rank_segment(1201) == RankSegment.GOLD
        assert get_rank_segment(1400) == RankSegment.GOLD
    
    def test_platinum_segment(self):
        """高分段应为铂金"""
        assert get_rank_segment(1401) == RankSegment.PLATINUM
        assert get_rank_segment(1600) == RankSegment.PLATINUM
    
    def test_diamond_segment(self):
        """很高分段应为钻石"""
        assert get_rank_segment(1601) == RankSegment.DIAMOND
        assert get_rank_segment(1800) == RankSegment.DIAMOND
    
    def test_master_segment(self):
        """顶级分段应为大师"""
        assert get_rank_segment(1801) == RankSegment.MASTER
        assert get_rank_segment(2200) == RankSegment.MASTER
    
    def test_edge_cases(self):
        """边界值测试"""
        assert get_rank_segment(1000) == RankSegment.BRONZE
        assert get_rank_segment(1001) == RankSegment.SILVER
        assert get_rank_segment(1200) == RankSegment.SILVER
        assert get_rank_segment(1201) == RankSegment.GOLD
        assert get_rank_segment(1400) == RankSegment.GOLD
        assert get_rank_segment(1401) == RankSegment.PLATINUM
        assert get_rank_segment(1600) == RankSegment.PLATINUM
        assert get_rank_segment(1601) == RankSegment.DIAMOND
        assert get_rank_segment(1800) == RankSegment.DIAMOND
        assert get_rank_segment(1801) == RankSegment.MASTER


class TestEloService:
    """测试 EloService 类"""
    
    @pytest.fixture
    def elo_service(self):
        """创建 EloService 实例"""
        with patch('matchmaking.elo.redis.from_url') as mock_redis:
            service = EloService()
            yield service
    
    @pytest.fixture
    def mock_redis(self, elo_service):
        """获取 mock redis"""
        return elo_service.redis
    
    @patch('matchmaking.elo.redis.from_url')
    def test_service_initialization(self, mock_redis):
        """测试服务初始化"""
        service = EloService()
        
        assert service.redis is not None
        assert service.leaderboard_key == "matchmaking:leaderboard"
        assert service.history_prefix == "matchmaking:history:"
    
    @patch('matchmaking.elo.update_elo_rating')
    @patch('users.models.User')
    def test_update_player_rating_win(self, mock_user, mock_update, elo_service, mock_redis):
        """测试更新玩家等级分 - 胜利"""
        # Mock 用户
        mock_player = MagicMock()
        mock_player.id = 'player1'
        mock_player.elo_rating = 1500
        
        mock_opponent = MagicMock()
        mock_opponent.id = 'player2'
        mock_opponent.elo_rating = 1450
        
        mock_user.objects.get.side_effect = [mock_player, mock_opponent]
        mock_update.side_effect = [1520, 1430]  # 玩家新分数，对手新分数
        
        new_rating, opp_new_rating = elo_service.update_player_rating(
            player_id='player1',
            opponent_id='player2',
            game_id='game123',
            result='win'
        )
        
        assert new_rating == 1520
        assert opp_new_rating == 1430
        mock_user.objects.get.assert_called()
        mock_redis.zadd.assert_called()
        mock_redis.lpush.assert_called()
    
    @patch('matchmaking.elo.update_elo_rating')
    @patch('users.models.User')
    def test_update_player_rating_loss(self, mock_user, mock_update, elo_service, mock_redis):
        """测试更新玩家等级分 - 失败"""
        mock_player = MagicMock()
        mock_player.id = 'player1'
        mock_player.elo_rating = 1500
        
        mock_opponent = MagicMock()
        mock_opponent.id = 'player2'
        mock_opponent.elo_rating = 1550
        
        mock_user.objects.get.side_effect = [mock_player, mock_opponent]
        mock_update.side_effect = [1480, 1570]
        
        new_rating, opp_new_rating = elo_service.update_player_rating(
            player_id='player1',
            opponent_id='player2',
            game_id='game123',
            result='loss'
        )
        
        assert new_rating == 1480
        assert opp_new_rating == 1570
    
    @patch('matchmaking.elo.update_elo_rating')
    @patch('users.models.User')
    def test_update_player_rating_draw(self, mock_user, mock_update, elo_service, mock_redis):
        """测试更新玩家等级分 - 和棋"""
        mock_player = MagicMock()
        mock_player.id = 'player1'
        mock_player.elo_rating = 1500
        
        mock_opponent = MagicMock()
        mock_opponent.id = 'player2'
        mock_opponent.elo_rating = 1500
        
        mock_user.objects.get.side_effect = [mock_player, mock_opponent]
        mock_update.side_effect = [1500, 1500]
        
        new_rating, opp_new_rating = elo_service.update_player_rating(
            player_id='player1',
            opponent_id='player2',
            game_id='game123',
            result='draw'
        )
        
        assert new_rating == 1500
        assert opp_new_rating == 1500
    
    def test_update_player_rating_user_not_found(self, elo_service):
        """测试更新玩家等级分 - 用户不存在"""
        with patch('users.models.User') as mock_user:
            mock_user.objects.get.side_effect = Exception("User not found")
            
            with pytest.raises(Exception):
                elo_service.update_player_rating(
                    player_id='invalid',
                    opponent_id='player2',
                    game_id='game123',
                    result='win'
                )
    
    def test_update_leaderboard(self, elo_service, mock_redis):
        """测试更新排行榜"""
        elo_service._update_leaderboard('player1', 1600)
        
        mock_redis.zadd.assert_called_once_with(
            "matchmaking:leaderboard",
            {'player1': 1600}
        )
    
    def test_record_history(self, elo_service, mock_redis):
        """测试记录等级分历史"""
        elo_service._record_history(
            user_id='player1',
            game_id='game123',
            opponent_id='player2',
            result='win',
            new_rating=1600
        )
        
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()
    
    @patch('matchmaking.elo.get_rank_segment')
    def test_get_leaderboard(self, mock_segment, elo_service, mock_redis):
        """测试获取排行榜"""
        mock_redis.zrevrange.return_value = [
            ('player1', 1800),
            ('player2', 1750),
            ('player3', 1700)
        ]
        mock_redis.zcard.return_value = 50
        mock_segment.return_value = RankSegment.DIAMOND
        
        leaderboard = elo_service.get_leaderboard(page=1, page_size=20)
        
        assert 'players' in leaderboard
        assert leaderboard['total'] == 50
        assert leaderboard['page'] == 1
        assert len(leaderboard['players']) == 3
    
    def test_get_leaderboard_empty(self, elo_service, mock_redis):
        """测试获取空排行榜"""
        mock_redis.zrevrange.return_value = []
        mock_redis.zcard.return_value = 0
        
        leaderboard = elo_service.get_leaderboard()
        
        assert leaderboard['players'] == []
        assert leaderboard['total'] == 0
    
    @patch('users.models.User')
    def test_get_user_rating(self, mock_user, elo_service):
        """测试获取用户等级分"""
        mock_user_obj = MagicMock()
        mock_user_obj.id = 'player1'
        mock_user_obj.elo_rating = 1600
        mock_user_obj.total_games = 100
        mock_user_obj.wins = 60
        mock_user_obj.losses = 35
        mock_user_obj.draws = 5
        
        mock_user.objects.get.return_value = mock_user_obj
        
        rating_info = elo_service.get_user_rating('player1')
        
        assert rating_info is not None
        assert rating_info['rating'] == 1600
        assert rating_info['total_games'] == 100
    
    def test_get_user_rating_not_found(self, elo_service):
        """测试获取用户等级分 - 用户不存在"""
        from users.models import User
        
        with patch('users.models.User') as mock_user:
            # Mock DoesNotExist 异常
            mock_user.DoesNotExist = Exception
            mock_user.objects.get.side_effect = Exception("User not found")
            
            rating_info = elo_service.get_user_rating('invalid')
            
            assert rating_info is None
    
    def test_get_rating_history(self, elo_service, mock_redis):
        """测试获取等级分历史"""
        mock_redis.lrange.return_value = [
            b'{"rating": 1600, "change": 20}',
            b'{"rating": 1580, "change": -10}'
        ]
        
        history = elo_service.get_rating_history('player1', limit=10)
        
        assert len(history) == 2
        mock_redis.lrange.assert_called_once()
    
    def test_get_rating_history_empty(self, elo_service, mock_redis):
        """测试获取空历史记录"""
        mock_redis.lrange.return_value = []
        
        history = elo_service.get_rating_history('player1')
        
        assert history == []
    
    @patch('matchmaking.elo.get_rank_segment')
    def test_get_users_in_rating_range(self, mock_segment, elo_service, mock_redis):
        """测试获取指定分数范围内的用户"""
        mock_redis.zrangebyscore.return_value = [
            ('player1', 1500),
            ('player2', 1550)
        ]
        mock_segment.return_value = RankSegment.PLATINUM
        
        users = elo_service.get_users_in_rating_range(1400, 1600, limit=10)
        
        assert len(users) == 2
        assert users[0]['rating'] == 1500
    
    def test_get_users_in_rating_range_empty(self, elo_service, mock_redis):
        """测试获取空范围用户"""
        mock_redis.zrangebyscore.return_value = []
        
        users = elo_service.get_users_in_rating_range(2000, 2500)
        
        assert users == []


class TestGetSegmentBoundaries:
    """测试获取段位边界"""
    
    def test_get_segment_boundaries(self):
        """测试获取所有段位边界"""
        boundaries = get_segment_boundaries()
        
        assert 'bronze' in boundaries
        assert 'silver' in boundaries
        assert 'gold' in boundaries
        assert 'platinum' in boundaries
        assert 'diamond' in boundaries
        assert 'master' in boundaries
        
        assert boundaries['bronze']['min'] == 0
        assert boundaries['bronze']['max'] == 1000
        assert boundaries['master']['min'] == 1801
