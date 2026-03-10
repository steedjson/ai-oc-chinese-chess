"""
Elo 等级分系统详细测试
测试 Elo 分数计算、段位系统、等级分历史追踪等功能
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

from matchmaking.elo import (
    calculate_expected_score,
    calculate_elo_change,
    update_elo_rating,
    get_rank_segment,
    RatingHistory,
    RankSegment,
    K_FACTOR,
    INITIAL_RATING,
    MIN_RATING,
    MAX_RATING
)


class TestCalculateExpectedScore:
    """计算预期胜率测试"""
    
    def test_equal_ratings(self):
        """测试相同等级分的预期胜率"""
        expected = calculate_expected_score(1500, 1500)
        assert expected == 0.5  # 相同等级分，预期胜率 50%
    
    def test_higher_rating(self):
        """测试高等级分对低等级分的预期胜率"""
        expected = calculate_expected_score(1600, 1400)
        assert expected > 0.5
        assert expected < 1.0
    
    def test_lower_rating(self):
        """测试低等级分对高等级分的预期胜率"""
        expected = calculate_expected_score(1400, 1600)
        assert expected < 0.5
        assert expected > 0.0
    
    def test_large_rating_difference(self):
        """测试大等级分差距的预期胜率"""
        # 1000 分差距
        expected = calculate_expected_score(2000, 1000)
        assert expected > 0.99  # 几乎必胜
    
    def test_extreme_rating_difference(self):
        """测试极端等级分差距"""
        # 2000 分差距
        expected = calculate_expected_score(2500, 500)
        assert abs(expected - 1.0) < 0.001
    
    def test_small_rating_difference(self):
        """测试小等级分差距"""
        # 100 分差距
        expected = calculate_expected_score(1550, 1450)
        assert 0.6 < expected < 0.7
    
    def test_formula_correctness(self):
        """测试公式正确性"""
        # E = 1 / (1 + 10^((R_opponent - R_player) / 400))
        # 当 R_player = 1600, R_opponent = 1400
        # E = 1 / (1 + 10^(-200/400)) = 1 / (1 + 10^(-0.5)) ≈ 0.76
        expected = calculate_expected_score(1600, 1400)
        assert 0.75 < expected < 0.77


class TestCalculateEloChange:
    """计算 Elo 积分变化测试"""
    
    def test_win_against_equal_opponent(self):
        """测试战胜相同等级分对手"""
        change = calculate_elo_change(1500, 1500, 'win')
        assert change > 0
        assert change == 16  # K/2 = 32/2 = 16
    
    def test_loss_against_equal_opponent(self):
        """测试输给相同等级分对手"""
        change = calculate_elo_change(1500, 1500, 'loss')
        assert change < 0
        assert change == -16
    
    def test_draw_against_equal_opponent(self):
        """测试与相同等级分对手和棋"""
        change = calculate_elo_change(1500, 1500, 'draw')
        assert change == 0  # 预期就是和棋，没有变化
    
    def test_win_against_stronger_opponent(self):
        """测试战胜强对手"""
        change = calculate_elo_change(1400, 1600, 'win')
        assert change > 16  # 战胜强敌获得更多分数
    
    def test_loss_against_weaker_opponent(self):
        """测试输给弱对手"""
        change = calculate_elo_change(1600, 1400, 'loss')
        assert change < -16  # 输给弱敌扣除更多分数
    
    def test_custom_k_factor(self):
        """测试自定义 K 因子"""
        change = calculate_elo_change(1500, 1500, 'win', k_factor=20)
        assert change == 10  # K/2 = 20/2 = 10
    
    def test_result_case_insensitive(self):
        """测试结果大小写不敏感"""
        change1 = calculate_elo_change(1500, 1500, 'WIN')
        change2 = calculate_elo_change(1500, 1500, 'Win')
        change3 = calculate_elo_change(1500, 1500, 'win')
        
        assert change1 == change2 == change3
    
    def test_invalid_result(self):
        """测试无效结果"""
        change = calculate_elo_change(1500, 1500, 'invalid')
        assert change < 0  # 默认为输


class TestGetRankSegment:
    """获取段位测试"""
    
    def test_bronze_rank(self):
        """测试青铜段位"""
        assert get_rank_segment(0) == RankSegment.BRONZE
        assert get_rank_segment(500) == RankSegment.BRONZE
        assert get_rank_segment(1000) == RankSegment.BRONZE
    
    def test_silver_rank(self):
        """测试白银段位"""
        assert get_rank_segment(1001) == RankSegment.SILVER
        assert get_rank_segment(1100) == RankSegment.SILVER
        assert get_rank_segment(1200) == RankSegment.SILVER
    
    def test_gold_rank(self):
        """测试黄金段位"""
        assert get_rank_segment(1201) == RankSegment.GOLD
        assert get_rank_segment(1300) == RankSegment.GOLD
        assert get_rank_segment(1400) == RankSegment.GOLD
    
    def test_platinum_rank(self):
        """测试铂金段位"""
        assert get_rank_segment(1401) == RankSegment.PLATINUM
        assert get_rank_segment(1500) == RankSegment.PLATINUM
        assert get_rank_segment(1600) == RankSegment.PLATINUM
    
    def test_diamond_rank(self):
        """测试钻石段位"""
        assert get_rank_segment(1601) == RankSegment.DIAMOND
        assert get_rank_segment(1700) == RankSegment.DIAMOND
        assert get_rank_segment(1800) == RankSegment.DIAMOND
    
    def test_master_rank(self):
        """测试大师段位"""
        assert get_rank_segment(1801) == RankSegment.MASTER
        assert get_rank_segment(2000) == RankSegment.MASTER
        assert get_rank_segment(3000) == RankSegment.MASTER
    
    def test_negative_rating(self):
        """测试负数等级分"""
        assert get_rank_segment(-100) == RankSegment.BRONZE
    
    def test_very_high_rating(self):
        """测试超高等级分"""
        assert get_rank_segment(5000) == RankSegment.MASTER





class TestUpdateEloRating:
    """更新 Elo 等级分测试"""
    
    def test_update_rating_win(self):
        """测试胜利后更新等级分"""
        new_rating = update_elo_rating(1500, 1500, 'win')
        
        assert new_rating > 1500
        assert new_rating == 1500 + 16  # 1500 + K/2
    
    def test_update_rating_loss(self):
        """测试失败后更新等级分"""
        new_rating = update_elo_rating(1500, 1500, 'loss')
        
        assert new_rating < 1500
        assert new_rating == 1500 - 16
    
    def test_update_rating_draw(self):
        """测试和棋后更新等级分"""
        new_rating = update_elo_rating(1500, 1500, 'draw')
        
        # 对相同等级分对手和棋，分数不变
        assert new_rating == 1500
    
    def test_update_rating_win_against_stronger(self):
        """测试战胜强对手"""
        new_rating = update_elo_rating(1400, 1600, 'win')
        
        # 战胜强敌获得更多分数
        assert new_rating > 1400 + 16
    
    def test_update_rating_loss_against_weaker(self):
        """测试输给弱对手"""
        new_rating = update_elo_rating(1600, 1400, 'loss')
        
        # 输给弱敌扣除更多分数
        assert new_rating < 1600 - 16
    
    def test_update_rating_respects_min_max(self):
        """测试等级分不超过边界"""
        # 测试最低边界
        new_rating_low = update_elo_rating(10, 3000, 'loss')
        assert new_rating_low >= MIN_RATING
        
        # 测试最高边界
        new_rating_high = update_elo_rating(2990, 1000, 'win')
        assert new_rating_high <= MAX_RATING


class TestRatingHistory:
    """等级分历史记录测试"""
    
    def test_rating_history_creation(self):
        """测试历史记录创建"""
        history = RatingHistory(
            rating=1500,
            change=16,
            game_id="game123",
            opponent_id="player2",
            result="win"
        )
        
        assert history.rating == 1500
        assert history.change == 16
        assert history.game_id == "game123"
        assert history.opponent_id == "player2"
        assert history.result == "win"
        assert isinstance(history.created_at, datetime)
    
    def test_rating_history_custom_time(self):
        """测试自定义时间的历史记录"""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        history = RatingHistory(
            rating=1600,
            change=-10,
            game_id="game456",
            opponent_id="player3",
            result="loss",
            created_at=custom_time
        )
        
        assert history.created_at == custom_time


class TestConstants:
    """常量测试"""
    
    def test_k_factor(self):
        """测试 K 因子"""
        assert K_FACTOR == 32
    
    def test_initial_rating(self):
        """测试初始等级分"""
        assert INITIAL_RATING == 1500
    
    def test_min_rating(self):
        """测试最低等级分"""
        assert MIN_RATING == 0
    
    def test_max_rating(self):
        """测试最高等级分"""
        assert MAX_RATING == 3000


class TestRankSegmentEnum:
    """段位枚举测试"""
    
    def test_rank_segment_values(self):
        """测试段位枚举值"""
        assert RankSegment.BRONZE.value == 'bronze'
        assert RankSegment.SILVER.value == 'silver'
        assert RankSegment.GOLD.value == 'gold'
        assert RankSegment.PLATINUM.value == 'platinum'
        assert RankSegment.DIAMOND.value == 'diamond'
        assert RankSegment.MASTER.value == 'master'
    
    def test_rank_segment_comparison(self):
        """测试段位比较"""
        segments = list(RankSegment)
        # 验证所有段位都可以比较
        for i in range(len(segments) - 1):
            assert segments[i] != segments[i + 1]
