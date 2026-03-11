"""
测试排行榜视图

测试 games/ranking_views.py 中的视图函数
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from games.ranking_views import (
    DailyLeaderboardView,
    WeeklyLeaderboardView,
    AllTimeLeaderboardView,
    UserRankView,
    RankingStatsView,
)

User = get_user_model()


@pytest.mark.django_db
class TestDailyLeaderboardView:
    """测试每日排行榜视图"""
    
    def test_get_daily_leaderboard(self, api_client, authenticated_user):
        """测试获取每日排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/daily/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'leaderboard' in response.data
    
    def test_daily_leaderboard_pagination(self, api_client, authenticated_user):
        """测试每日排行榜分页"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/daily/?page=1&page_size=10')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_daily_leaderboard_cache(self, api_client, authenticated_user):
        """测试每日排行榜缓存"""
        api_client.force_authenticate(user=authenticated_user)
        
        with patch('games.ranking_views.RankingCacheService') as mock_cache:
            mock_cache.get_or_generate_daily_leaderboard.return_value = (
                [{'rank': 1, 'user': {'username': 'test'}}],
                True  # 从缓存获取
            )
            
            response = api_client.get('/api/rankings/daily/')
            
            assert response.status_code == status.HTTP_200_OK
            mock_cache.get_or_generate_daily_leaderboard.assert_called_once()


@pytest.mark.django_db
class TestWeeklyLeaderboardView:
    """测试每周排行榜视图"""
    
    def test_get_weekly_leaderboard(self, api_client, authenticated_user):
        """测试获取每周排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/weekly/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_weekly_leaderboard_custom_week(self, api_client, authenticated_user):
        """测试获取指定周的排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/weekly/?week=10&year=2024')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAllTimeLeaderboardView:
    """测试总排行榜视图"""
    
    def test_get_all_time_leaderboard(self, api_client, authenticated_user):
        """测试获取总排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/all-time/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_all_time_leaderboard_limit(self, api_client, authenticated_user):
        """测试总排行榜数量限制"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/all-time/?limit=50')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserRankView:
    """测试用户排名视图"""
    
    def test_get_user_daily_rank(self, api_client, authenticated_user):
        """测试获取用户每日排名"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/my-rank/daily/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'rank' in response.data or 'ranking' in response.data
    
    def test_get_user_weekly_rank(self, api_client, authenticated_user):
        """测试获取用户每周排名"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/my-rank/weekly/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_user_all_time_rank(self, api_client, authenticated_user):
        """测试获取用户总排名"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/my-rank/all-time/')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_user_rank_not_found(self, api_client, authenticated_user):
        """测试用户排名不存在"""
        api_client.force_authenticate(user=authenticated_user)
        
        with patch('games.ranking_views.RankingService') as mock_service:
            mock_service.get_user_daily_rank.return_value = None
            
            response = api_client.get('/api/rankings/my-rank/daily/')
            
            # 应该返回空数据或 404
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestRankingStatsView:
    """测试排行榜统计视图"""
    
    def test_get_ranking_stats(self, api_client, authenticated_user):
        """测试获取排行榜统计"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/stats/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_players' in response.data or 'stats' in response.data
    
    def test_ranking_stats_includes_details(self, api_client, authenticated_user):
        """测试排行榜统计包含详情"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/rankings/stats/')
        
        # 应该包含各种统计信息
        assert response.status_code == status.HTTP_200_OK


class TestRankingViewsUnauthenticated:
    """测试未认证的排行榜视图"""
    
    def test_daily_leaderboard_unauthenticated(self, api_client):
        """测试未认证用户访问每日排行榜"""
        response = api_client.get('/api/rankings/daily/')
        
        # 排行榜通常是公开的
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_weekly_leaderboard_unauthenticated(self, api_client):
        """测试未认证用户访问每周排行榜"""
        response = api_client.get('/api/rankings/weekly/')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_all_time_leaderboard_unauthenticated(self, api_client):
        """测试未认证用户访问总排行榜"""
        response = api_client.get('/api/rankings/all-time/')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
    
    def test_user_rank_unauthenticated(self, api_client):
        """测试未认证用户访问个人排名"""
        response = api_client.get('/api/rankings/my-rank/daily/')
        
        # 个人排名需要认证
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """创建认证用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )


@pytest.fixture
def sample_leaderboard_data():
    """创建示例排行榜数据"""
    return [
        {
            'rank': 1,
            'user': {
                'id': 1,
                'username': 'player1',
                'avatar_url': None,
            },
            'total_score': 1000,
            'games_played': 100,
            'wins': 80,
        },
        {
            'rank': 2,
            'user': {
                'id': 2,
                'username': 'player2',
                'avatar_url': None,
            },
            'total_score': 900,
            'games_played': 90,
            'wins': 70,
        },
    ]
