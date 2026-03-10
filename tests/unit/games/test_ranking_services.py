"""
测试排行榜服务

测试 games/ranking_services.py 中的 RankingService 和 RankingCacheService
"""

import pytest
from datetime import date, timedelta, datetime
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from django.contrib.auth import get_user_model

from games.ranking_services import RankingService, RankingCacheService
from games.ranking_models import GameRecord, GameResult, RankingCache, UserRankingStats

User = get_user_model()


def create_game_record(user, game_date=None, score_gained=0, result=GameResult.WIN, is_rated=True):
    """辅助函数：创建游戏记录"""
    if game_date is None:
        game_date = date.today()
    
    iso_calendar = game_date.isocalendar()
    return GameRecord.objects.create(
        user=user,
        game_date=game_date,
        game_week=iso_calendar[1],
        game_year=iso_calendar[0],
        is_rated=is_rated,
        score_gained=score_gained,
        result=result,
    )


@pytest.mark.django_db
class TestRankingCacheService:
    """测试排行榜缓存服务"""
    
    def test_get_or_generate_daily_leaderboard_cache_hit(self):
        """测试从缓存获取每日排行榜"""
        cache_date = date.today()
        mock_leaderboard = [
            {'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 100},
            {'rank': 2, 'user': {'id': '2', 'username': 'player2'}, 'total_score': 90},
        ]
        
        cache = RankingCache.objects.create(
            ranking_type='daily',
            cache_date=cache_date,
            leaderboard_data=mock_leaderboard,
            total_players=10,
            expires_at=timezone.now() + timedelta(hours=1),
            is_valid=True,
        )
        
        leaderboard, from_cache = RankingCacheService.get_or_generate_daily_leaderboard(
            cache_date=cache_date, limit=100
        )
        
        assert from_cache is True
        assert len(leaderboard) == 2
        assert leaderboard[0]['rank'] == 1
    
    def test_get_or_generate_daily_leaderboard_cache_miss(self):
        """测试生成新的每日排行榜（缓存未命中）"""
        cache_date = date.today()
        mock_leaderboard = [{'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 100}]
        
        with patch.object(RankingService, 'calculate_daily_leaderboard', return_value=mock_leaderboard):
            with patch.object(RankingService, 'get_daily_player_count', return_value=5):
                leaderboard, from_cache = RankingCacheService.get_or_generate_daily_leaderboard(
                    cache_date=cache_date, limit=100
                )
        
        assert from_cache is False
        assert len(leaderboard) == 1
        
        cache = RankingCache.objects.filter(ranking_type='daily', cache_date=cache_date).first()
        assert cache is not None
        assert cache.is_valid is True
    
    def test_get_or_generate_weekly_leaderboard_cache_hit(self):
        """测试从缓存获取每周排行榜"""
        today = date.today()
        iso_calendar = today.isocalendar()
        week = iso_calendar[1]
        year = iso_calendar[0]
        
        mock_leaderboard = [{'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 200}]
        
        cache = RankingCache.objects.create(
            ranking_type='weekly',
            cache_week=week,
            cache_year=year,
            leaderboard_data=mock_leaderboard,
            total_players=20,
            expires_at=timezone.now() + timedelta(hours=1),
            is_valid=True,
        )
        
        leaderboard, from_cache = RankingCacheService.get_or_generate_weekly_leaderboard(
            week=week, year=year, limit=100
        )
        
        assert from_cache is True
        assert len(leaderboard) == 1
    
    def test_get_or_generate_weekly_leaderboard_cache_miss(self):
        """测试生成新的每周排行榜"""
        today = date.today()
        iso_calendar = today.isocalendar()
        week = iso_calendar[1]
        year = iso_calendar[0]
        
        mock_leaderboard = [{'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 150}]
        
        with patch.object(RankingService, 'calculate_weekly_leaderboard', return_value=mock_leaderboard):
            with patch.object(RankingService, 'get_weekly_player_count', return_value=10):
                leaderboard, from_cache = RankingCacheService.get_or_generate_weekly_leaderboard(
                    week=week, year=year, limit=100
                )
        
        assert from_cache is False
        
        cache = RankingCache.objects.filter(ranking_type='weekly', cache_week=week, cache_year=year).first()
        assert cache is not None
    
    def test_get_or_generate_all_time_leaderboard_cache_hit(self):
        """测试从缓存获取总排行榜"""
        mock_leaderboard = [{'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 500}]
        
        cache = RankingCache.objects.create(
            ranking_type='all_time',
            leaderboard_data=mock_leaderboard,
            total_players=100,
            expires_at=timezone.now() + timedelta(hours=1),
            is_valid=True,
        )
        
        leaderboard, from_cache = RankingCacheService.get_or_generate_all_time_leaderboard(limit=100)
        
        assert from_cache is True
        assert len(leaderboard) == 1
    
    def test_get_or_generate_all_time_leaderboard_cache_miss(self):
        """测试生成新的总排行榜"""
        mock_leaderboard = [{'rank': 1, 'user': {'id': '1', 'username': 'player1'}, 'total_score': 300}]
        
        with patch.object(RankingService, 'calculate_all_time_leaderboard', return_value=mock_leaderboard):
            with patch.object(RankingService, 'get_all_time_player_count', return_value=50):
                leaderboard, from_cache = RankingCacheService.get_or_generate_all_time_leaderboard(limit=100)
        
        assert from_cache is False
        
        cache = RankingCache.objects.filter(ranking_type='all_time').first()
        assert cache is not None
    
    def test_update_daily_cache(self):
        """测试更新每日排行榜缓存"""
        cache_date = date.today()
        leaderboard_data = [{'rank': 1, 'user': {'id': '1'}, 'total_score': 100}]
        
        cache = RankingCacheService.update_daily_cache(
            cache_date=cache_date,
            leaderboard_data=leaderboard_data,
            total_players=5
        )
        
        assert cache.ranking_type == 'daily'
        assert cache.cache_date == cache_date
        assert cache.leaderboard_data == leaderboard_data
        assert cache.total_players == 5
        assert cache.is_valid is True
    
    def test_update_weekly_cache(self):
        """测试更新每周排行榜缓存"""
        leaderboard_data = [{'rank': 1, 'user': {'id': '1'}, 'total_score': 150}]
        
        cache = RankingCacheService.update_weekly_cache(
            week=10,
            year=2026,
            leaderboard_data=leaderboard_data,
            total_players=10
        )
        
        assert cache.ranking_type == 'weekly'
        assert cache.cache_week == 10
        assert cache.cache_year == 2026
    
    def test_update_all_time_cache(self):
        """测试更新总排行榜缓存"""
        leaderboard_data = [{'rank': 1, 'user': {'id': '1'}, 'total_score': 500}]
        
        cache = RankingCacheService.update_all_time_cache(
            leaderboard_data=leaderboard_data,
            total_players=100
        )
        
        assert cache.ranking_type == 'all_time'
        assert cache.leaderboard_data == leaderboard_data
    
    def test_invalidate_daily_cache(self):
        """测试使每日排行榜缓存失效"""
        cache_date = date.today()
        
        RankingCache.objects.create(
            ranking_type='daily',
            cache_date=cache_date,
            leaderboard_data=[],
            total_players=5,
            is_valid=True,
        )
        
        RankingCacheService.invalidate_daily_cache(cache_date=cache_date)
        
        cache = RankingCache.objects.filter(ranking_type='daily', cache_date=cache_date).first()
        assert cache is not None
        assert cache.is_valid is False
    
    def test_invalidate_weekly_cache(self):
        """测试使每周排行榜缓存失效"""
        RankingCache.objects.create(
            ranking_type='weekly',
            cache_week=10,
            cache_year=2026,
            leaderboard_data=[],
            total_players=10,
            is_valid=True,
        )
        
        RankingCacheService.invalidate_weekly_cache(week=10, year=2026)
        
        cache = RankingCache.objects.filter(ranking_type='weekly', cache_week=10, cache_year=2026).first()
        assert cache is not None
        assert cache.is_valid is False
    
    def test_invalidate_all_time_cache(self):
        """测试使总排行榜缓存失效"""
        RankingCache.objects.create(
            ranking_type='all_time',
            leaderboard_data=[],
            total_players=50,
            is_valid=True,
        )
        
        RankingCacheService.invalidate_all_time_cache()
        
        cache = RankingCache.objects.filter(ranking_type='all_time').first()
        assert cache is not None
        assert cache.is_valid is False
    
    def test_cleanup_expired_caches(self):
        """测试清理过期缓存"""
        RankingCache.objects.all().delete()
        
        # 创建过期缓存（使用不同的 ranking_type 避免唯一性冲突）
        RankingCache.objects.create(
            ranking_type='daily',
            cache_date=date.today() - timedelta(days=2),
            leaderboard_data=[],
            total_players=5,
            expires_at=timezone.now() - timedelta(hours=2),
            is_valid=True,
        )
        
        # 创建未过期缓存（使用 weekly 类型）
        iso_calendar = date.today().isocalendar()
        RankingCache.objects.create(
            ranking_type='weekly',
            cache_week=iso_calendar[1],
            cache_year=iso_calendar[0],
            leaderboard_data=[],
            total_players=5,
            expires_at=timezone.now() + timedelta(hours=1),
            is_valid=True,
        )
        
        RankingCacheService.cleanup_expired_caches()
        
        expired_cache = RankingCache.objects.filter(ranking_type='daily', cache_date=date.today() - timedelta(days=2)).first()
        assert expired_cache is not None
        assert expired_cache.is_valid is False
        
        valid_cache = RankingCache.objects.filter(ranking_type='weekly').first()
        assert valid_cache is not None
        assert valid_cache.is_valid is True


@pytest.mark.django_db
class TestRankingService:
    """测试排行榜核心服务"""
    
    def test_calculate_daily_leaderboard_empty(self):
        """测试计算空的每日排行榜"""
        leaderboard = RankingService.calculate_daily_leaderboard(
            cache_date=date.today(),
            limit=100
        )
        
        assert leaderboard == []
    
    def test_calculate_daily_leaderboard_with_data(self):
        """测试计算有数据的每日排行榜"""
        user1 = User.objects.create_user(username='player1', email='player1@test.com', password='pass1')
        user2 = User.objects.create_user(username='player2', email='player2@test.com', password='pass2')
        
        cache_date = date.today()
        
        create_game_record(user1, cache_date, 100, GameResult.WIN)
        create_game_record(user1, cache_date, 50, GameResult.DRAW)
        create_game_record(user2, cache_date, 80, GameResult.LOSS)
        
        leaderboard = RankingService.calculate_daily_leaderboard(cache_date=cache_date, limit=100)
        
        assert len(leaderboard) == 2
        assert leaderboard[0]['user']['username'] == 'player1'
        assert leaderboard[0]['total_score'] == 150
        assert leaderboard[0]['wins'] == 1
        assert leaderboard[0]['draws'] == 1
        assert leaderboard[1]['user']['username'] == 'player2'
        assert leaderboard[1]['total_score'] == 80
    
    def test_calculate_daily_leaderboard_limit(self):
        """测试排行榜数量限制"""
        for i in range(10):
            user = User.objects.create_user(username=f'player{i}', email=f'player{i}@test.com', password='pass')
            create_game_record(user, date.today(), 100 - i * 10, GameResult.WIN)
        
        leaderboard = RankingService.calculate_daily_leaderboard(cache_date=date.today(), limit=5)
        
        assert len(leaderboard) == 5
    
    def test_calculate_daily_leaderboard_unrated_excluded(self):
        """测试未评级游戏不计入排行榜"""
        user = User.objects.create_user(username='player1', email='player1@test.com', password='pass')
        
        create_game_record(user, date.today(), 1000, GameResult.WIN, is_rated=False)
        
        leaderboard = RankingService.calculate_daily_leaderboard(cache_date=date.today(), limit=100)
        
        assert leaderboard == []
    
    def test_calculate_weekly_leaderboard_empty(self):
        """测试计算空的每周排行榜"""
        today = date.today()
        iso_calendar = today.isocalendar()
        
        leaderboard = RankingService.calculate_weekly_leaderboard(
            week=iso_calendar[1],
            year=iso_calendar[0],
            limit=100
        )
        
        assert leaderboard == []
    
    def test_calculate_weekly_leaderboard_with_data(self):
        """测试计算有数据的每周排行榜"""
        user = User.objects.create_user(username='weekly_player', email='weekly_player@test.com', password='pass')
        
        today = date.today()
        iso_calendar = today.isocalendar()
        week = iso_calendar[1]
        year = iso_calendar[0]
        
        create_game_record(user, today, 200, GameResult.WIN)
        
        leaderboard = RankingService.calculate_weekly_leaderboard(week=week, year=year, limit=100)
        
        assert len(leaderboard) == 1
        assert leaderboard[0]['user']['username'] == 'weekly_player'
        assert leaderboard[0]['total_score'] == 200
    
    def test_calculate_all_time_leaderboard_empty(self):
        """测试计算空的总排行榜"""
        leaderboard = RankingService.calculate_all_time_leaderboard(limit=100)
        
        assert leaderboard == []
    
    def test_calculate_all_time_leaderboard_with_data(self):
        """测试计算有数据的总排行榜"""
        user = User.objects.create_user(username='alltime_player', email='alltime_player@test.com', password='pass')
        
        for i in range(5):
            create_game_record(user, date.today() - timedelta(days=i), 50, GameResult.WIN)
        
        leaderboard = RankingService.calculate_all_time_leaderboard(limit=100)
        
        assert len(leaderboard) == 1
        assert leaderboard[0]['user']['username'] == 'alltime_player'
        assert leaderboard[0]['total_score'] == 250
        assert leaderboard[0]['games_played'] == 5
        assert leaderboard[0]['wins'] == 5
    
    def test_calculate_all_time_leaderboard_ordering(self):
        """测试排行榜排序（按总分、胜场、平均分）"""
        user1 = User.objects.create_user(username='top_player', email='top_player@test.com', password='pass')
        user2 = User.objects.create_user(username='second_player', email='second_player@test.com', password='pass')
        user3 = User.objects.create_user(username='third_player', email='third_player@test.com', password='pass')
        
        # user1: 总分 300, 3 胜
        for i in range(3):
            create_game_record(user1, date.today() - timedelta(days=i), 100, GameResult.WIN)
        
        # user2: 总分 300, 2 胜 1 平
        create_game_record(user2, date.today(), 100, GameResult.WIN)
        create_game_record(user2, date.today() - timedelta(days=1), 100, GameResult.WIN)
        create_game_record(user2, date.today() - timedelta(days=2), 100, GameResult.DRAW)
        
        # user3: 总分 200
        create_game_record(user3, date.today(), 200, GameResult.WIN)
        
        leaderboard = RankingService.calculate_all_time_leaderboard(limit=100)
        
        assert len(leaderboard) == 3
        assert leaderboard[0]['user']['username'] == 'top_player'
        assert leaderboard[1]['user']['username'] == 'second_player'
        assert leaderboard[2]['user']['username'] == 'third_player'
    
    def test_get_daily_player_count(self):
        """测试获取每日玩家数量"""
        user1 = User.objects.create_user(username='count_player1', email='count_player1@test.com', password='pass')
        user2 = User.objects.create_user(username='count_player2', email='count_player2@test.com', password='pass')
        
        create_game_record(user1, date.today(), 100, GameResult.WIN)
        create_game_record(user2, date.today(), 80, GameResult.LOSS)
        create_game_record(user1, date.today() - timedelta(days=1), 90, GameResult.WIN)
        
        count = RankingService.get_daily_player_count(cache_date=date.today())
        
        assert count == 2
    
    def test_get_weekly_player_count(self):
        """测试获取每周玩家数量"""
        today = date.today()
        iso_calendar = today.isocalendar()
        
        user = User.objects.create_user(username='weekly_count_player', email='weekly_count_player@test.com', password='pass')
        
        create_game_record(user, today, 100, GameResult.WIN)
        
        count = RankingService.get_weekly_player_count(week=iso_calendar[1], year=iso_calendar[0])
        
        assert count == 1
    
    def test_get_all_time_player_count(self):
        """测试获取总玩家数量"""
        user1 = User.objects.create_user(username='alltime_count1', email='alltime_count1@test.com', password='pass')
        user2 = User.objects.create_user(username='alltime_count2', email='alltime_count2@test.com', password='pass')
        
        create_game_record(user1, date.today(), 100, GameResult.WIN)
        create_game_record(user2, date.today() - timedelta(days=1), 80, GameResult.LOSS)
        
        count = RankingService.get_all_time_player_count()
        
        assert count == 2
    
    def test_get_user_stats(self):
        """测试获取用户统计"""
        user = User.objects.create_user(username='stats_player', email='stats_player@test.com', password='pass')
        
        create_game_record(user, date.today(), 100, GameResult.WIN)
        create_game_record(user, date.today() - timedelta(days=1), 50, GameResult.DRAW)
        create_game_record(user, date.today() - timedelta(days=2), -30, GameResult.LOSS)
        
        stats = RankingService.get_user_stats(user)
        
        assert stats is not None
    
    def test_get_user_stats_no_records(self):
        """测试用户无游戏记录时的统计"""
        user = User.objects.create_user(username='no_stats_player', email='no_stats_player@test.com', password='pass')
        
        stats = RankingService.get_user_stats(user)
        
        assert stats is not None
    
    def test_get_user_daily_rank(self):
        """测试获取用户每日排名"""
        user1 = User.objects.create_user(username='rank_player1', email='rank_player1@test.com', password='pass')
        user2 = User.objects.create_user(username='rank_player2', email='rank_player2@test.com', password='pass')
        
        create_game_record(user1, date.today(), 200, GameResult.WIN)
        create_game_record(user2, date.today(), 100, GameResult.WIN)
        
        rank_info = RankingService.get_user_daily_rank(user1)
        
        assert rank_info is not None
        assert rank_info['rank'] == 1
    
    def test_get_user_daily_rank_not_in_leaderboard(self):
        """测试用户不在排行榜中的排名"""
        user = User.objects.create_user(username='unranked_player', email='unranked_player@test.com', password='pass')
        other_user = User.objects.create_user(username='other_player', email='other_player@test.com', password='pass')
        
        create_game_record(other_user, date.today(), 100, GameResult.WIN)
        
        rank = RankingService.get_user_daily_rank(user)
        
        assert rank is None
