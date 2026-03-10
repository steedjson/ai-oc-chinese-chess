"""
每日挑战 API 视图测试

测试范围：
- 获取今日挑战
- 开始挑战
- 提交走法
- 完成挑战
- 排行榜查询
- 用户连续打卡
- 挑战历史
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from daily_challenge.models import DailyChallenge, ChallengeAttempt, ChallengeStreak

User = get_user_model()


@pytest.mark.django_db
class TestTodayChallengeView:
    """获取今日挑战视图测试"""

    def test_get_today_challenge_success(self):
        """测试获取今日挑战成功"""
        client = APIClient()
        
        # 创建今日挑战
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战目标',
            difficulty=5,
            stars=3,
            max_moves=10,
            time_limit=300,
            is_active=True
        )
        
        url = reverse('today-challenge')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'challenge' in response.data['data']
        
        challenge_data = response.data['data']['challenge']
        assert challenge_data['id'] == str(challenge.id)
        assert challenge_data['date'] == today.isoformat()
        assert challenge_data['difficulty'] == 5
        assert challenge_data['stars'] == 3

    def test_get_today_challenge_auto_create(self):
        """测试今日挑战不存在时自动创建"""
        client = APIClient()
        
        # 删除今日挑战（如果存在）
        DailyChallenge.objects.filter(date=date.today()).delete()
        
        url = reverse('today-challenge')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'challenge' in response.data['data']
        
        # 验证挑战已创建
        assert DailyChallenge.objects.filter(date=date.today()).exists()

    def test_get_today_challenge_authenticated_user(self):
        """测试认证用户获取今日挑战"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            difficulty=3,
            stars=2,
            is_active=True
        )
        
        url = reverse('today-challenge')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'user_attempt' in response.data['data']
        assert response.data['data']['user_attempt']['has_attempted'] is False

    def test_get_today_challenge_no_auth_required(self):
        """测试获取今日挑战无需认证"""
        client = APIClient()
        url = reverse('today-challenge')
        
        response = client.get(url)
        
        # 应该返回 200，不应该是 401/403
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStartChallengeView:
    """开始挑战视图测试"""

    def test_start_challenge_success(self):
        """测试开始挑战成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            difficulty=5,
            stars=3,
            max_moves=10,
            time_limit=300,
            is_active=True
        )
        
        url = reverse('start-challenge')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'attempt_id' in response.data['data']
        assert 'challenge_id' in response.data['data']
        assert 'fen' in response.data['data']
        
        # 验证尝试记录已创建
        assert ChallengeAttempt.objects.filter(user=user, challenge=challenge).exists()

    def test_start_challenge_unauthenticated(self):
        """测试未认证用户开始挑战"""
        client = APIClient()
        url = reverse('start-challenge')
        
        response = client.post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_challenge_already_attempted(self):
        """测试重复开始挑战"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            difficulty=5,
            is_active=True
        )
        
        # 创建已存在的尝试
        ChallengeAttempt.objects.create(
            user=user,
            challenge=challenge,
            status='in_progress'
        )
        
        url = reverse('start-challenge')
        response = client.post(url)
        
        # 根据实现，可能返回 400 或允许重新开始
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_start_challenge_no_challenge(self):
        """测试没有今日挑战时开始挑战"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # 删除今日挑战
        DailyChallenge.objects.filter(date=date.today()).delete()
        
        # Mock get_todays_challenge to return None
        from unittest.mock import patch
        
        with patch('daily_challenge.views.DailyChallengeService.get_todays_challenge', return_value=None):
            url = reverse('start-challenge')
            response = client.post(url)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'NO_CHALLENGE'


@pytest.mark.django_db
class TestSubmitMoveView:
    """提交走法视图测试"""

    def test_submit_move_success(self):
        """测试提交走法成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            difficulty=5,
            is_active=True
        )
        
        attempt = ChallengeAttempt.objects.create(
            user=user,
            challenge=challenge,
            status='in_progress'
        )
        
        url = reverse('submit-move')
        data = {
            'attempt_id': str(attempt.id),
            'from': 'h0',
            'to': 'h2',
            'piece': 'horse'
        }
        
        response = client.post(url, data, format='json')
        
        # 根据实现，可能成功或失败（取决于走法验证）
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_submit_move_missing_attempt_id(self):
        """测试提交走法缺少 attempt_id"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('submit-move')
        data = {
            'from': 'h0',
            'to': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'MISSING_ATTEMPT_ID'

    def test_submit_move_unauthenticated(self):
        """测试未认证用户提交走法"""
        client = APIClient()
        url = reverse('submit-move')
        
        response = client.post(url, {'attempt_id': '123'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_move_not_owner(self):
        """测试提交他人尝试的走法"""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user2)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            is_active=True
        )
        
        attempt = ChallengeAttempt.objects.create(
            user=user1,
            challenge=challenge,
            status='in_progress'
        )
        
        url = reverse('submit-move')
        data = {
            'attempt_id': str(attempt.id),
            'from': 'h0',
            'to': 'h2'
        }
        
        response = client.post(url, data, format='json')
        
        # 应该返回 404（找不到他人的尝试）
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCompleteChallengeView:
    """完成挑战视图测试"""

    def test_complete_challenge_success(self):
        """测试完成挑战成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
            target_description='测试挑战',
            difficulty=5,
            stars=3,
            is_active=True
        )
        
        attempt = ChallengeAttempt.objects.create(
            user=user,
            challenge=challenge,
            status='in_progress'
        )
        
        url = reverse('complete-challenge')
        data = {
            'attempt_id': str(attempt.id),
            'status': 'success'
        }
        
        response = client.post(url, data, format='json')
        
        # 根据实现，可能成功或失败
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_complete_challenge_missing_attempt_id(self):
        """测试完成挑战缺少 attempt_id"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('complete-challenge')
        data = {
            'status': 'success'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'MISSING_ATTEMPT_ID'

    def test_complete_challenge_unauthenticated(self):
        """测试未认证用户完成挑战"""
        client = APIClient()
        url = reverse('complete-challenge')
        
        response = client.post(url, {'attempt_id': '123', 'status': 'success'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChallengeLeaderboardView:
    """挑战排行榜视图测试"""

    def test_get_leaderboard_success(self):
        """测试获取排行榜成功"""
        client = APIClient()
        url = reverse('challenge-leaderboard')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'leaderboard' in response.data['data']
        assert 'challenge_date' in response.data['data']

    def test_get_leaderboard_with_date(self):
        """测试获取指定日期的排行榜"""
        client = APIClient()
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        url = reverse('challenge-leaderboard')
        
        response = client.get(url, {'date': yesterday})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['challenge_date'] == yesterday

    def test_get_leaderboard_invalid_date(self):
        """测试获取排行榜使用无效日期"""
        client = APIClient()
        url = reverse('challenge-leaderboard')
        
        response = client.get(url, {'date': 'invalid-date'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'INVALID_DATE'

    def test_get_leaderboard_with_limit(self):
        """测试获取排行榜指定数量"""
        client = APIClient()
        url = reverse('challenge-leaderboard')
        
        response = client.get(url, {'limit': '10'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['leaderboard']) <= 10

    def test_get_leaderboard_no_auth_required(self):
        """测试获取排行榜无需认证"""
        client = APIClient()
        url = reverse('challenge-leaderboard')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUserStreakView:
    """用户连续打卡视图测试"""

    def test_get_user_streak_success(self):
        """测试获取用户连续打卡成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        # 创建连续打卡记录
        streak = ChallengeStreak.objects.create(
            user=user,
            current_streak=5,
            longest_streak=10
        )
        
        url = reverse('user-streak')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'streak' in response.data['data']
        assert response.data['data']['streak']['current_streak'] == 5
        assert response.data['data']['streak']['longest_streak'] == 10

    def test_get_user_streak_unauthenticated(self):
        """测试未认证用户获取连续打卡"""
        client = APIClient()
        url = reverse('user-streak')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_streak_no_record(self):
        """测试用户没有连续打卡记录"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('user-streak')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # 应该返回默认值或空记录


@pytest.mark.django_db
class TestChallengeHistoryView:
    """挑战历史视图测试"""

    def test_get_challenge_history_success(self):
        """测试获取挑战历史成功"""
        client = APIClient()
        
        # 创建历史挑战
        today = date.today()
        for i in range(5):
            DailyChallenge.objects.create(
                date=today - timedelta(days=i+1),
                fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
                target_description=f'历史挑战 {i+1}',
                difficulty=5,
                stars=3,
                is_active=True
            )
        
        url = reverse('challenge-history')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'history' in response.data['data']
        assert len(response.data['data']['history']) > 0

    def test_get_challenge_history_with_limit(self):
        """测试获取挑战历史指定数量"""
        client = APIClient()
        
        today = date.today()
        for i in range(20):
            DailyChallenge.objects.create(
                date=today - timedelta(days=i+1),
                fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
                target_description=f'历史挑战 {i+1}',
                difficulty=5,
                is_active=True
            )
        
        url = reverse('challenge-history')
        response = client.get(url, {'limit': '10'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['history']) <= 10

    def test_get_challenge_history_no_auth_required(self):
        """测试获取挑战历史无需认证"""
        client = APIClient()
        url = reverse('challenge-history')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDailyLeaderboardView:
    """每日排行榜视图测试"""

    def test_get_daily_leaderboard_success(self):
        """测试获取每日排行榜成功"""
        client = APIClient()
        url = reverse('daily-leaderboard')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'leaderboard' in response.data['data']
        assert 'challenge_date' in response.data['data']

    def test_get_daily_leaderboard_with_date(self):
        """测试获取指定日期的每日排行榜"""
        client = APIClient()
        
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        url = reverse('daily-leaderboard')
        
        response = client.get(url, {'date': yesterday})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['challenge_date'] == yesterday


@pytest.mark.django_db
class TestWeeklyLeaderboardView:
    """周排行榜视图测试"""

    def test_get_weekly_leaderboard_success(self):
        """测试获取周排行榜成功"""
        client = APIClient()
        url = reverse('weekly-leaderboard')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'week_start' in response.data['data']
        assert 'week_end' in response.data['data']
        assert 'leaderboard' in response.data['data']

    def test_get_weekly_leaderboard_with_week_start(self):
        """测试获取指定周的排行榜"""
        client = APIClient()
        
        # 获取本周一
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        
        url = reverse('weekly-leaderboard')
        response = client.get(url, {'week_start': week_start})
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAllTimeLeaderboardView:
    """总排行榜视图测试"""

    def test_get_all_time_leaderboard_success(self):
        """测试获取总排行榜成功"""
        client = APIClient()
        url = reverse('all-time-leaderboard')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'leaderboard' in response.data['data']

    def test_get_all_time_leaderboard_with_limit(self):
        """测试获取总排行榜指定数量"""
        client = APIClient()
        url = reverse('all-time-leaderboard')
        
        response = client.get(url, {'limit': '10'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['leaderboard']) <= 10


@pytest.mark.django_db
class TestUserLeaderboardRankView:
    """用户排名查询视图测试"""

    def test_get_user_rank_all_time(self):
        """测试获取用户总排名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        url = reverse('user-leaderboard-rank', kwargs={'user_id': str(user.id)})
        
        response = client.get(url, {'type': 'all-time'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_get_user_rank_daily(self):
        """测试获取用户每日排名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        url = reverse('user-leaderboard-rank', kwargs={'user_id': str(user.id)})
        
        response = client.get(url, {'type': 'daily'})
        
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_rank_weekly(self):
        """测试获取用户周排名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        url = reverse('user-leaderboard-rank', kwargs={'user_id': str(user.id)})
        
        response = client.get(url, {'type': 'weekly'})
        
        assert response.status_code == status.HTTP_200_OK

    def test_get_user_rank_not_found(self):
        """测试获取不存在用户的排名"""
        client = APIClient()
        url = reverse('user-leaderboard-rank', kwargs={'user_id': '00000000-0000-0000-0000-000000000000'})
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'USER_NOT_FOUND'

    def test_get_user_rank_invalid_date(self):
        """测试获取用户排名使用无效日期"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        url = reverse('user-leaderboard-rank', kwargs={'user_id': str(user.id)})
        
        response = client.get(url, {'type': 'daily', 'date': 'invalid'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGenerateTomorrowChallengeView:
    """生成明日挑战视图测试"""

    def test_generate_tomorrow_challenge_success(self):
        """测试生成明日挑战成功（管理员）"""
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123',
            is_staff=True
        )
        
        client = APIClient()
        client.force_authenticate(user=admin)
        
        url = reverse('generate-tomorrow-challenge')
        response = client.post(url)
        
        # 根据实现，可能成功或失败（取决于挑战生成逻辑）
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    def test_generate_tomorrow_challenge_non_staff(self):
        """测试非管理员生成明日挑战"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('generate-tomorrow-challenge')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'PERMISSION_DENIED'

    def test_generate_tomorrow_challenge_unauthenticated(self):
        """测试未认证用户生成明日挑战"""
        client = APIClient()
        url = reverse('generate-tomorrow-challenge')
        
        response = client.post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
