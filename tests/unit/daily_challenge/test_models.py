"""
每日挑战模型测试
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from decimal import Decimal

from daily_challenge.models import DailyChallenge, ChallengeAttempt, ChallengeStreak


@pytest.mark.django_db
class TestDailyChallengeModel:
    """测试每日挑战模型"""
    
    def test_create_daily_challenge(self):
        """测试创建每日挑战"""
        challenge = DailyChallenge.objects.create(
            date=date.today(),
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            target_description="红方先行，3 步杀",
            difficulty=7,
            stars=4,
            max_moves=6,
            time_limit=300
        )
        
        assert challenge.date == date.today()
        assert challenge.difficulty == 7
        assert challenge.stars == 4
        assert challenge.is_active is True
        assert challenge.total_attempts == 0
    
    def test_daily_challenge_unique_date(self):
        """测试每日挑战日期唯一性"""
        DailyChallenge.objects.create(
            date=date.today(),
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            target_description="测试挑战",
            difficulty=5
        )
        
        # 尝试创建同一天挑战应该失败
        with pytest.raises(Exception):
            DailyChallenge.objects.create(
                date=date.today(),
                fen="different_fen",
                target_description="另一个挑战",
                difficulty=5
            )
    
    def test_get_todays_challenge(self):
        """测试获取今日挑战"""
        today = date.today()
        challenge = DailyChallenge.objects.create(
            date=today,
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            target_description="测试",
            difficulty=5
        )
        
        todays_challenge = DailyChallenge.objects.get_todays_challenge()
        
        assert todays_challenge is not None
        assert todays_challenge.date == today
        assert todays_challenge.id == challenge.id
    
    def test_get_todays_challenge_not_exists(self):
        """测试今日挑战不存在时返回 None"""
        # 删除今日挑战（如果存在）
        DailyChallenge.objects.filter(date=date.today()).delete()
        
        todays_challenge = DailyChallenge.objects.get_todays_challenge()
        
        assert todays_challenge is None
    
    def test_challenge_statistics_update(self):
        """测试挑战统计更新"""
        challenge = DailyChallenge.objects.create(
            date=date.today(),
            fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            target_description="测试",
            difficulty=5
        )
        
        # 更新统计
        challenge.update_statistics()
        
        assert challenge.total_attempts == 0
        assert challenge.unique_players == 0
        assert challenge.completion_rate == 0


@pytest.mark.django_db
class TestChallengeAttemptModel:
    """测试挑战尝试模型"""
    
    def test_create_attempt(self, daily_challenge):
        """测试创建挑战尝试"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        attempt = ChallengeAttempt.objects.create(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            move_history=[],
            status='success',
            moves_used=5,
            time_used=120
        )
        
        assert attempt.challenge == daily_challenge
        assert attempt.user == user
        assert attempt.status == 'success'
        assert attempt.moves_used == 5
        assert attempt.time_used == 120
    
    def test_attempt_unique_user_daily(self, daily_challenge):
        """测试用户每天只能有一次挑战记录（通过服务层验证）"""
        from users.models import User
        from daily_challenge.services import ChallengeAttemptService
        
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # 第一次创建成功
        ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        # 尝试创建第二次应该失败（通过服务层验证）
        with pytest.raises(ValueError, match="今天已经挑战过了"):
            ChallengeAttemptService.create_attempt(user, daily_challenge)
    
    def test_calculate_score(self, daily_challenge):
        """测试得分计算"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        
        attempt = ChallengeAttempt(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            move_history=[],
            status='success',
            moves_used=3,  # 最优解
            time_used=45  # 很快完成
        )
        
        score = attempt.calculate_score()
        
        assert score > 1000  # 基础分 + 奖励
        assert score <= 2000  # 不超过上限
    
    def test_calculate_stars(self, daily_challenge):
        """测试星级计算"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        
        # 2 星：完成挑战（默认情况）
        attempt_2star = ChallengeAttempt(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            move_history=[],
            status='success',
            moves_used=5,
            time_used=200
        )
        
        # 保存后才能正确计算（因为需要 challenge 的 solution_moves）
        attempt_2star.save()
        assert attempt_2star.stars_earned in [2, 3]  # 至少 2 星
        
        # 1 星：未完成
        attempt_1star = ChallengeAttempt(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            move_history=[],
            status='failed',
            moves_used=10,
            time_used=300
        )
        attempt_1star.save()
        assert attempt_1star.stars_earned == 0  # 失败没有星级


@pytest.mark.django_db
class TestChallengeStreakModel:
    """测试连续打卡模型"""
    
    def test_create_streak(self):
        """测试创建连续打卡记录"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='testpass123'
        )
        
        streak = ChallengeStreak.objects.create(user=user)
        
        assert streak.user == user
        assert streak.current_streak == 0
        assert streak.longest_streak == 0
        assert streak.total_completions == 0
    
    def test_update_streak(self):
        """测试更新连续打卡"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser6',
            email='test6@example.com',
            password='testpass123'
        )
        
        streak = ChallengeStreak.objects.create(user=user)
        
        # 更新连续打卡
        streak.update_streak(date.today())
        
        assert streak.current_streak == 1
        assert streak.longest_streak == 1
        assert streak.total_completions == 1
        assert streak.last_completion_date == date.today()
    
    def test_streak_continues(self):
        """测试连续打卡继续"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser7',
            email='test7@example.com',
            password='testpass123'
        )
        
        streak = ChallengeStreak.objects.create(
            user=user,
            current_streak=5,
            longest_streak=5,
            last_completion_date=date.today() - timedelta(days=1)
        )
        
        # 今天继续打卡
        streak.update_streak(date.today())
        
        assert streak.current_streak == 6
        assert streak.longest_streak == 6
    
    def test_streak_broken(self):
        """测试连续打卡中断"""
        from users.models import User
        
        user = User.objects.create_user(
            username='testuser8',
            email='test8@example.com',
            password='testpass123'
        )
        
        streak = ChallengeStreak.objects.create(
            user=user,
            current_streak=5,
            longest_streak=5,
            last_completion_date=date.today() - timedelta(days=2)
        )
        
        # 中断后今天打卡
        streak.update_streak(date.today())
        
        assert streak.current_streak == 1  # 重置为 1
        assert streak.longest_streak == 5  # 保持最长记录


@pytest.fixture
def daily_challenge():
    """创建测试用每日挑战"""
    return DailyChallenge.objects.create(
        date=date.today(),
        fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
        target_description="红方先行，3 步杀",
        difficulty=7,
        stars=4,
        max_moves=6,
        time_limit=300
    )
