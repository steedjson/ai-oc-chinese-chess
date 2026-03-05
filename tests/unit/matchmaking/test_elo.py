"""
Elo 等级分系统单元测试
"""
import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime

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
