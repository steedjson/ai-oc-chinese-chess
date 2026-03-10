"""
每日挑战服务层测试
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from daily_challenge.models import DailyChallenge, ChallengeAttempt, ChallengeStreak
from daily_challenge.services import (
    DailyChallengeService,
    ChallengeAttemptService,
    ChallengeStreakService,
    ChallengeLeaderboardService,
)


@pytest.mark.django_db
class TestDailyChallengeService:
    """测试每日挑战服务"""
    
    def test_get_todays_challenge(self, daily_challenge):
        """测试获取今日挑战"""
        challenge = DailyChallengeService.get_todays_challenge()
        
        assert challenge is not None
        assert challenge.date == date.today()
        assert challenge.id == daily_challenge.id
    
    def test_get_or_create_todays_challenge(self):
        """测试获取或创建今日挑战"""
        # 删除今日挑战（如果存在）
        DailyChallenge.objects.filter(date=date.today()).delete()
        
        challenge, created = DailyChallengeService.get_or_create_todays_challenge()
        
        assert challenge is not None
        assert challenge.date == date.today()
        assert created is True
        
        # 再次获取应该返回已存在的
        challenge2, created2 = DailyChallengeService.get_or_create_todays_challenge()
        
        assert challenge2.id == challenge.id
        assert created2 is False
    
    def test_generate_tomorrow_challenge(self):
        """测试生成明日挑战"""
        tomorrow = date.today() + timedelta(days=1)
        
        # 删除明日挑战（如果存在）
        DailyChallenge.objects.filter(date=tomorrow).delete()
        
        challenge = DailyChallengeService.generate_tomorrow_challenge()
        
        assert challenge is not None
        assert challenge.date == tomorrow
        assert challenge.is_active is True
    
    def test_get_difficulty_for_weekday(self):
        """测试根据星期几获取难度范围"""
        # 周一（0）- 简单
        assert list(DailyChallengeService._get_difficulty_for_weekday(0)) == [1, 2, 3, 4]
        
        # 周三（2）- 中等
        assert list(DailyChallengeService._get_difficulty_for_weekday(2)) == [4, 5, 6]
        
        # 周六（5）- 困难
        assert list(DailyChallengeService._get_difficulty_for_weekday(5)) == [6, 7, 8]
        
        # 周日（6）- 大师
        assert list(DailyChallengeService._get_difficulty_for_weekday(6)) == [8, 9, 10]
    
    def test_get_challenge_statistics(self, daily_challenge):
        """测试获取挑战统计"""
        stats = DailyChallengeService.get_challenge_statistics(daily_challenge)
        
        assert 'total_attempts' in stats
        assert 'unique_players' in stats
        assert 'completion_rate' in stats


@pytest.mark.django_db
class TestChallengeAttemptService:
    """测试挑战尝试服务"""
    
    def test_create_attempt(self, daily_challenge, user):
        """测试创建挑战尝试"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        assert attempt is not None
        assert attempt.user == user
        assert attempt.challenge == daily_challenge
        assert attempt.start_fen == daily_challenge.fen
        assert attempt.status == 'success'
    
    def test_create_attempt_already_exists(self, daily_challenge, user):
        """测试重复创建尝试"""
        # 创建第一次尝试
        ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        # 尝试创建第二次应该失败
        with pytest.raises(ValueError, match="今天已经挑战过了"):
            ChallengeAttemptService.create_attempt(user, daily_challenge)
    
    def test_submit_move(self, daily_challenge, user):
        """测试提交走法"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        move = {'from': 'c1', 'to': 'c4', 'piece': 'C'}
        result = ChallengeAttemptService.submit_move(attempt, move)
        
        assert result['valid'] is True
        assert attempt.moves_used == 1
        assert len(attempt.move_history) == 1
    
    def test_submit_invalid_move(self, daily_challenge, user):
        """测试提交无效走法"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        move = {'invalid': 'move'}
        result = ChallengeAttemptService.submit_move(attempt, move)
        
        assert result['valid'] is False
    
    def test_complete_attempt_success(self, daily_challenge, user):
        """测试完成挑战（成功）"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        # 提交一些走法
        for i in range(3):
            move = {'from': 'c1', 'to': 'c4', 'piece': 'C'}
            ChallengeAttemptService.submit_move(attempt, move)
        
        result = ChallengeAttemptService.complete_attempt(attempt, 'success')
        
        assert result['status'] == 'success'
        assert result['score'] > 0
        assert result['stars_earned'] in [1, 2, 3]
        assert 'rank' in result
    
    def test_complete_attempt_updates_streak(self, daily_challenge, user):
        """测试完成挑战更新连续打卡"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        result = ChallengeAttemptService.complete_attempt(attempt, 'success')
        
        # 检查用户连续打卡是否更新
        streak = ChallengeStreak.objects.filter(user=user).first()
        assert streak is not None
        assert streak.current_streak >= 1
    
    def test_get_user_attempt_for_today(self, daily_challenge, user):
        """测试获取用户今日尝试"""
        attempt = ChallengeAttemptService.create_attempt(user, daily_challenge)
        
        retrieved = ChallengeAttemptService.get_user_attempt_for_today(user, daily_challenge)
        
        assert retrieved is not None
        assert retrieved.id == attempt.id


@pytest.mark.django_db
class TestChallengeStreakService:
    """测试连续打卡服务"""
    
    def test_get_user_streak(self, user):
        """测试获取用户连续打卡"""
        streak = ChallengeStreakService.get_user_streak(user)
        
        assert streak is not None
        assert streak.user == user
        assert streak.current_streak == 0
    
    def test_get_leaderboard(self, user, user2):
        """测试获取排行榜"""
        # 创建一些打卡记录
        streak1 = ChallengeStreak.objects.create(user=user, current_streak=5, total_completions=10)
        streak2 = ChallengeStreak.objects.create(user=user2, current_streak=3, total_completions=5)
        
        leaderboard = ChallengeStreakService.get_leaderboard(limit=10)
        
        assert len(leaderboard) >= 2
        assert leaderboard[0].current_streak == 5  # 按连续天数排序
    
    def test_get_user_statistics(self, user):
        """测试获取用户统计"""
        streak = ChallengeStreak.objects.create(
            user=user,
            current_streak=7,
            longest_streak=12,
            total_completions=20,
            total_perfect=5
        )
        
        stats = ChallengeStreakService.get_user_statistics(user)
        
        assert stats['current_streak'] == 7
        assert stats['longest_streak'] == 12
        assert stats['total_completions'] == 20
        assert stats['total_perfect'] == 5


@pytest.mark.django_db
class TestChallengeLeaderboardService:
    """测试挑战排行榜服务"""
    
    def test_get_daily_leaderboard(self, daily_challenge, user, user2):
        """测试获取每日排行榜"""
        # 创建两个尝试（save() 会自动计算 score）
        attempt1 = ChallengeAttempt.objects.create(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            status='success',
            moves_used=3,
            time_used=60,
        )
        
        attempt2 = ChallengeAttempt.objects.create(
            challenge=daily_challenge,
            user=user2,
            start_fen=daily_challenge.fen,
            status='success',
            moves_used=5,
            time_used=120,
        )
        
        leaderboard = ChallengeLeaderboardService.get_daily_leaderboard(date.today())
        
        assert len(leaderboard) == 2
        assert leaderboard[0]['rank'] == 1
        # 第一个用户步数少、时间少，应该排第一
        assert leaderboard[0]['score'] >= leaderboard[1]['score']
        assert leaderboard[1]['rank'] == 2
    
    def test_get_user_rank(self, daily_challenge, user):
        """测试获取用户排名"""
        attempt = ChallengeAttempt.objects.create(
            challenge=daily_challenge,
            user=user,
            start_fen=daily_challenge.fen,
            status='success',
            moves_used=3,
            time_used=60,
        )
        
        rank_info = ChallengeLeaderboardService.get_user_rank(user, date.today())
        
        assert rank_info is not None
        assert rank_info['rank'] == 1
        assert rank_info['score'] == attempt.score


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


@pytest.fixture
def user(db):
    """创建测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2(db):
    """创建第二个测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )
