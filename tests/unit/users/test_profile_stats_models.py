"""
Unit tests for UserProfile and UserStats models.
"""

import pytest
from django.contrib.auth import get_user_model
from users.models import UserProfile, UserStats

User = get_user_model()


@pytest.mark.django_db
class TestUserProfileModel:
    """UserProfile 模型测试"""
    
    def test_create_user_profile_success(self):
        """测试成功创建用户档案"""
        user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='SecurePass123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='这是一个测试用户',
            location='北京',
        )
        
        assert profile.user == user
        assert profile.bio == '这是一个测试用户'
        assert profile.location == '北京'
        assert profile.id is not None
    
    def test_user_profile_one_to_one_relationship(self):
        """测试用户档案与用户的一对一关系"""
        user = User.objects.create_user(
            username='profileuser2',
            email='profile2@example.com',
            password='SecurePass123'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        # 通过用户访问档案
        assert user.userprofile == profile
    
    def test_user_profile_cascade_delete(self):
        """测试用户删除时档案级联删除"""
        user = User.objects.create_user(
            username='profileuser3',
            email='profile3@example.com',
            password='SecurePass123'
        )
        
        profile = UserProfile.objects.create(user=user)
        profile_id = profile.id
        
        # 删除用户
        user.delete()
        
        # 档案应该也被删除
        with pytest.raises(UserProfile.DoesNotExist):
            UserProfile.objects.get(id=profile_id)
    
    def test_user_profile_unique_user_id(self):
        """测试用户档案 user_id 唯一性"""
        user = User.objects.create_user(
            username='profileuser4',
            email='profile4@example.com',
            password='SecurePass123'
        )
        
        UserProfile.objects.create(user=user)
        
        # 不能为同一用户创建两个档案
        from django.db.utils import IntegrityError
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user)
    
    def test_user_profile_optional_fields(self):
        """测试用户档案可选字段"""
        user = User.objects.create_user(
            username='profileuser5',
            email='profile5@example.com',
            password='SecurePass123'
        )
        
        # 只创建必填字段
        profile = UserProfile.objects.create(user=user)
        
        assert profile.bio is None
        assert profile.location is None
        assert profile.birthday is None
        assert profile.gender is None


@pytest.mark.django_db
class TestUserStatsModel:
    """UserStats 模型测试"""
    
    def test_create_user_stats_success(self):
        """测试成功创建用户统计"""
        user = User.objects.create_user(
            username='statsuser',
            email='stats@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10,
        )
        
        assert stats.user == user
        assert stats.total_games == 100
        assert stats.wins == 60
        assert stats.losses == 30
        assert stats.draws == 10
        assert stats.win_rate == 60.0  # 60/100 * 100
        assert stats.id is not None
    
    def test_user_stats_auto_calculate_win_rate(self):
        """测试自动计算胜率"""
        user = User.objects.create_user(
            username='statsuser2',
            email='stats2@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10,
        )
        
        # 胜率应该是 60%
        assert stats.win_rate == 60.0
    
    def test_user_stats_zero_games_win_rate(self):
        """测试 0 场游戏时胜率为 0"""
        user = User.objects.create_user(
            username='statsuser3',
            email='stats3@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=0,
            wins=0,
            losses=0,
            draws=0,
        )
        
        assert stats.win_rate == 0.0
    
    def test_user_stats_one_to_one_relationship(self):
        """测试用户统计与用户的一对一关系"""
        user = User.objects.create_user(
            username='statsuser4',
            email='stats4@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(user=user)
        
        # 通过用户访问统计
        assert user.userstats == stats
    
    def test_user_stats_cascade_delete(self):
        """测试用户删除时统计级联删除"""
        user = User.objects.create_user(
            username='statsuser5',
            email='stats5@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(user=user)
        stats_id = stats.id
        
        # 删除用户
        user.delete()
        
        # 统计应该也被删除
        with pytest.raises(UserStats.DoesNotExist):
            UserStats.objects.get(id=stats_id)
    
    def test_user_stats_unique_user_id(self):
        """测试用户统计 user_id 唯一性"""
        user = User.objects.create_user(
            username='statsuser6',
            email='stats6@example.com',
            password='SecurePass123'
        )
        
        UserStats.objects.create(user=user)
        
        # 不能为同一用户创建两个统计
        from django.db.utils import IntegrityError
        with pytest.raises(IntegrityError):
            UserStats.objects.create(user=user)
    
    def test_user_stats_update_stats(self):
        """测试更新用户统计"""
        user = User.objects.create_user(
            username='statsuser7',
            email='stats7@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=10,
            wins=5,
            losses=3,
            draws=2,
        )
        
        # 更新统计
        stats.total_games = 20
        stats.wins = 12
        stats.losses = 5
        stats.draws = 3
        stats.save()
        
        stats.refresh_from_db()
        assert stats.total_games == 20
        assert stats.win_rate == 60.0  # 12/20 * 100
    
    def test_user_stats_default_values(self):
        """测试用户统计默认值"""
        user = User.objects.create_user(
            username='statsuser8',
            email='stats8@example.com',
            password='SecurePass123'
        )
        
        stats = UserStats.objects.create(user=user)
        
        assert stats.total_games == 0
        assert stats.wins == 0
        assert stats.losses == 0
        assert stats.draws == 0
        assert stats.win_rate == 0.0
        assert stats.favorite_opening is None
