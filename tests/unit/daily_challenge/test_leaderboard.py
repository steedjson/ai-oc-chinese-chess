"""
排行榜 API 测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework import status
from django.contrib.auth import get_user_model

from daily_challenge.models import DailyChallenge, ChallengeAttempt, ChallengeStreak


User = get_user_model()


@pytest.fixture
def daily_challenge(db):
    """创建每日挑战"""
    return DailyChallenge.objects.create(
        date=date.today(),
        fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
        target_description="测试挑战",
        difficulty=5,
        stars=3,
        max_moves=10,
        time_limit=300,
        is_active=True,
    )


@pytest.fixture
def yesterday_challenge(db):
    """创建昨日挑战"""
    return DailyChallenge.objects.create(
        date=date.today() - timedelta(days=1),
        fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
        target_description="昨日挑战",
        difficulty=5,
        stars=3,
        max_moves=10,
        time_limit=300,
        is_active=True,
    )


@pytest.fixture
def test_users(db):
    """创建测试用户"""
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f'testuser{i}',
            email=f'test{i}@example.com',
            password='SecurePass123',
        )
        users.append(user)
    return users


@pytest.fixture
def challenge_attempts(db, daily_challenge, test_users):
    """创建挑战尝试记录"""
    attempts = []
    # 使用固定得分，通过 update 绕过模型的自动计算
    # 得分顺序：testuser3=2000, testuser1=1800, testuser4=1600, testuser0=1500, testuser2=1200
    test_data = [
        {'user_idx': 3, 'score': 2000, 'moves': 5, 'time': 140, 'stars': 3, 'optimal': True},
        {'user_idx': 1, 'score': 1800, 'moves': 6, 'time': 160, 'stars': 2, 'optimal': False},
        {'user_idx': 4, 'score': 1600, 'moves': 7, 'time': 120, 'stars': 3, 'optimal': True},
        {'user_idx': 0, 'score': 1500, 'moves': 8, 'time': 200, 'stars': 2, 'optimal': False},
        {'user_idx': 2, 'score': 1200, 'moves': 4, 'time': 180, 'stars': 3, 'optimal': True},
    ]
    
    for data in test_data:
        user = test_users[data['user_idx']]
        attempt = ChallengeAttempt.objects.create(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            move_history=[],
            status='success',
            moves_used=data['moves'],
            time_used=data['time'],
        )
        # 使用 update 绕过 save() 中的自动计算
        ChallengeAttempt.objects.filter(id=attempt.id).update(
            score=data['score'],
            stars_earned=data['stars'],
            is_optimal=data['optimal'],
        )
        # 刷新对象
        attempt.refresh_from_db()
        attempts.append(attempt)
    
    return attempts


class TestDailyLeaderboardView:
    """每日排行榜测试"""
    
    def test_get_daily_leaderboard_success(self, api_client, daily_challenge, challenge_attempts):
        """测试获取每日排行榜成功"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'leaderboard' in response.data['data']
        assert len(response.data['data']['leaderboard']) == 5
        
        # 验证排名顺序（按得分降序）
        leaderboard = response.data['data']['leaderboard']
        assert leaderboard[0]['rank'] == 1
        assert leaderboard[0]['score'] == 2000  # testuser3 最高分
        
    def test_get_daily_leaderboard_with_date(self, api_client, yesterday_challenge, challenge_attempts):
        """测试获取指定日期的排行榜"""
        yesterday = date.today() - timedelta(days=1)
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/daily/?date={yesterday}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['challenge_date'] == yesterday.isoformat()
    
    def test_get_daily_leaderboard_invalid_date(self, api_client):
        """测试无效日期格式"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/?date=invalid')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'error' in response.data
    
    def test_get_daily_leaderboard_with_limit(self, api_client, daily_challenge, challenge_attempts):
        """测试限制返回数量"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/?limit=3')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['leaderboard']) == 3
    
    def test_get_daily_leaderboard_with_user_rank(self, api_client, daily_challenge, challenge_attempts, test_users):
        """测试已认证用户获取排行榜时包含用户排名"""
        api_client.force_authenticate(user=test_users[0])
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['user_rank'] is not None
        assert 'rank' in response.data['data']['user_rank']
        assert 'score' in response.data['data']['user_rank']


class TestWeeklyLeaderboardView:
    """周排行榜测试"""
    
    def test_get_weekly_leaderboard_success(self, api_client, daily_challenge, challenge_attempts):
        """测试获取周排行榜成功"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        
        response = api_client.get('/api/v1/daily-challenge/leaderboard/weekly/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'week_start' in response.data['data']
        assert 'week_end' in response.data['data']
        assert 'leaderboard' in response.data['data']
    
    def test_get_weekly_leaderboard_with_week_start(self, api_client, daily_challenge, challenge_attempts):
        """测试指定周起始日期"""
        week_start = date.today() - timedelta(days=7)
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/weekly/?week_start={week_start}')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['week_start'] == week_start.isoformat()
    
    def test_get_weekly_leaderboard_invalid_date(self, api_client):
        """测试无效日期格式"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/weekly/?week_start=invalid')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


class TestAllTimeLeaderboardView:
    """总排行榜测试"""
    
    def test_get_all_time_leaderboard_success(self, api_client, daily_challenge, challenge_attempts):
        """测试获取总排行榜成功"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/all-time/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'leaderboard' in response.data['data']
        assert len(response.data['data']['leaderboard']) > 0
        
        # 验证包含总排行榜特有字段
        entry = response.data['data']['leaderboard'][0]
        assert 'total_score' in entry
        assert 'total_challenges' in entry
        assert 'total_perfect' in entry
        assert 'longest_streak' in entry
    
    def test_get_all_time_leaderboard_with_limit(self, api_client, daily_challenge, challenge_attempts):
        """测试限制返回数量"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/all-time/?limit=3')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['leaderboard']) == 3


class TestUserLeaderboardRankView:
    """用户排名查询测试"""
    
    def test_get_user_rank_all_time(self, api_client, daily_challenge, challenge_attempts, test_users):
        """测试获取用户总排名"""
        user = test_users[0]
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/user/{user.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['rank_type'] == 'all-time'
        assert 'rank' in response.data['data']
        assert 'total_score' in response.data['data']
    
    def test_get_user_rank_daily(self, api_client, daily_challenge, challenge_attempts, test_users):
        """测试获取用户日排名"""
        user = test_users[0]
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/user/{user.id}/?type=daily')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['rank_type'] == 'daily'
        assert 'challenge_date' in response.data['data']
    
    def test_get_user_rank_weekly(self, api_client, daily_challenge, challenge_attempts, test_users):
        """测试获取用户周排名"""
        user = test_users[0]
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/user/{user.id}/?type=weekly')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['rank_type'] == 'weekly'
        assert 'week_start' in response.data['data']
        assert 'week_end' in response.data['data']
    
    def test_get_user_rank_user_not_found(self, api_client):
        """测试用户不存在时返回"""
        import uuid
        fake_user_id = str(uuid.uuid4())
        response = api_client.get(f'/api/v1/daily-challenge/leaderboard/user/{fake_user_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
        assert 'error' in response.data
    
    def test_get_user_rank_invalid_user(self, api_client):
        """测试无效用户 ID"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/user/invalid-id/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
        assert 'error' in response.data


class TestLeaderboardService:
    """排行榜服务测试"""
    
    def test_get_daily_leaderboard_service(self, daily_challenge, challenge_attempts):
        """测试每日排行榜服务"""
        from daily_challenge.services import ChallengeLeaderboardService
        
        leaderboard = ChallengeLeaderboardService.get_daily_leaderboard(date.today())
        
        assert len(leaderboard) == 5
        assert leaderboard[0]['rank'] == 1
        assert leaderboard[0]['score'] == 2000  # testuser3 最高分
    
    def test_get_user_rank_service(self, daily_challenge, challenge_attempts, test_users):
        """测试用户排名服务"""
        from daily_challenge.services import ChallengeLeaderboardService
        
        user = test_users[0]  # 得分 1500 (testuser0)
        rank_info = ChallengeLeaderboardService.get_user_rank(user, date.today())
        
        assert rank_info is not None
        assert 'rank' in rank_info
        assert 'score' in rank_info
        assert rank_info['score'] == 1500  # testuser0 的得分
    
    def test_get_user_rank_no_attempt(self, daily_challenge, test_users):
        """测试用户无尝试记录"""
        from daily_challenge.services import ChallengeLeaderboardService
        
        user = test_users[4]  # 没有尝试记录的用户
        # 先删除该用户的尝试
        ChallengeAttempt.objects.filter(user=user).delete()
        
        rank_info = ChallengeLeaderboardService.get_user_rank(user, date.today())
        
        assert rank_info is None


class TestLeaderboardOrdering:
    """排行榜排序测试"""
    
    def test_leaderboard_ordered_by_score(self, api_client, daily_challenge, challenge_attempts):
        """测试排行榜按得分降序排列"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/')
        
        leaderboard = response.data['data']['leaderboard']
        scores = [entry['score'] for entry in leaderboard]
        
        assert scores == sorted(scores, reverse=True)
    
    def test_leaderboard_rank_sequential(self, api_client, daily_challenge, challenge_attempts):
        """测试排行榜排名连续"""
        response = api_client.get('/api/v1/daily-challenge/leaderboard/daily/')
        
        leaderboard = response.data['data']['leaderboard']
        ranks = [entry['rank'] for entry in leaderboard]
        
        assert ranks == list(range(1, len(leaderboard) + 1))
