"""
User Repository 测试
测试用户数据仓库核心功能：用户创建、查询、更新、删除
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from users.models import User, UserProfile, UserStats, UserStatus


# ==================== User Model 测试 ====================

class TestUserModel:
    """User 模型测试"""
    
    @pytest.mark.django_db
    def test_user_creation(self):
        """测试用户创建"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')
        assert user.elo_rating == 1500
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.is_verified is False
    
    @pytest.mark.django_db
    def test_user_str(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert str(user) == 'testuser'
    
    @pytest.mark.django_db
    def test_user_default_values(self):
        """测试用户默认值"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.elo_rating == 1500
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_verified is False
        assert user.first_name == ''
        assert user.last_name == ''
    
    @pytest.mark.django_db
    def test_user_get_full_name(self):
        """测试获取全名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    @pytest.mark.django_db
    def test_user_get_full_name_empty(self):
        """测试空全名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.get_full_name() == 'testuser'
    
    @pytest.mark.django_db
    def test_user_get_short_name(self):
        """测试获取短名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='John'
        )
        
        assert user.get_short_name() == 'John'
    
    @pytest.mark.django_db
    def test_user_get_short_name_empty(self):
        """测试空短名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.get_short_name() == 'testuser'
    
    @pytest.mark.django_db
    def test_user_is_banned(self):
        """测试用户是否被封禁"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            status=UserStatus.ACTIVE
        )
        
        assert user.is_banned() is False
        
        user.status = UserStatus.BANNED
        user.save()
        
        assert user.is_banned() is True
    
    @pytest.mark.django_db
    def test_user_set_password(self):
        """测试设置密码"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        
        user.set_password('newpass456')
        user.save()
        
        user.refresh_from_db()
        assert user.check_password('newpass456')
        assert not user.check_password('oldpass123')
    
    @pytest.mark.django_db
    def test_user_password_hash_sync(self):
        """测试密码哈希同步"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # 新创建用户时 password_hash 应该同步
        assert user.password_hash is not None
    
    @pytest.mark.django_db
    def test_user_unique_username(self):
        """测试用户名唯一性"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                email='another@example.com',
                password='password456'
            )
    
    @pytest.mark.django_db
    def test_user_unique_email(self):
        """测试邮箱唯一性"""
        User.objects.create_user(
            username='testuser1',
            email='test@example.com',
            password='password123'
        )
        
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',
                password='password456'
            )
    
    @pytest.mark.django_db
    def test_user_create_superuser(self):
        """测试创建超级用户"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert admin.username == 'admin'
        assert admin.email == 'admin@example.com'
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.is_verified is True
    
    @pytest.mark.django_db
    def test_user_create_superuser_staff_required(self):
        """测试创建超级用户必须 is_staff"""
        from django.core.exceptions import ValueError
        
        with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
    
    @pytest.mark.django_db
    def test_user_create_superuser_superuser_required(self):
        """测试创建超级用户必须 is_superuser"""
        from django.core.exceptions import ValueError
        
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )
    
    @pytest.mark.django_db
    def test_user_without_email(self):
        """测试创建无邮箱用户"""
        from django.core.exceptions import ValueError
        
        with pytest.raises(ValueError, match="Users must have an email address"):
            User.objects.create_user(
                username='testuser',
                email='',
                password='password123'
            )
    
    @pytest.mark.django_db
    def test_user_without_username(self):
        """测试创建无用户名用户"""
        from django.core.exceptions import ValueError
        
        with pytest.raises(ValueError, match="Users must have a username"):
            User.objects.create_user(
                username='',
                email='test@example.com',
                password='password123'
            )


# ==================== UserProfile Model 测试 ====================

class TestUserProfileModel:
    """UserProfile 模型测试"""
    
    @pytest.mark.django_db
    def test_userprofile_creation(self):
        """测试用户档案创建"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='This is a test bio',
            location='Beijing, China',
            gender='male'
        )
        
        assert profile.id is not None
        assert profile.user == user
        assert profile.bio == 'This is a test bio'
        assert profile.location == 'Beijing, China'
        assert profile.gender == 'male'
    
    @pytest.mark.django_db
    def test_userprofile_str(self):
        """测试用户档案字符串表示"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        assert str(profile) == "testuser's profile"
    
    @pytest.mark.django_db
    def test_userprofile_optional_fields(self):
        """测试用户档案可选字段"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        assert profile.bio is None or profile.bio == ''
        assert profile.location is None
        assert profile.birthday is None
        assert profile.gender is None
    
    @pytest.mark.django_db
    def test_userprofile_cascade_delete(self):
        """测试用户档案级联删除"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        profile = UserProfile.objects.create(user=user)
        profile_id = profile.id
        
        user.delete()
        
        assert UserProfile.objects.filter(id=profile_id).count() == 0


# ==================== UserStats Model 测试 ====================

class TestUserStatsModel:
    """UserStats 模型测试"""
    
    @pytest.mark.django_db
    def test_userstats_creation(self):
        """测试用户统计创建"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10
        )
        
        assert stats.id is not None
        assert stats.user == user
        assert stats.total_games == 100
        assert stats.wins == 60
        assert stats.losses == 30
        assert stats.draws == 10
    
    @pytest.mark.django_db
    def test_userstats_str(self):
        """测试用户统计字符串表示"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(user=user)
        
        assert str(stats) == "testuser's stats"
    
    @pytest.mark.django_db
    def test_userstats_win_rate_calculation(self):
        """测试胜率自动计算"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10
        )
        
        assert stats.win_rate == 60.00
    
    @pytest.mark.django_db
    def test_userstats_win_rate_zero_games(self):
        """测试零场对局时胜率"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=0,
            wins=0,
            losses=0,
            draws=0
        )
        
        assert stats.win_rate == 0.00
    
    @pytest.mark.django_db
    def test_userstats_win_rate_update(self):
        """测试胜率更新"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=10,
            wins=5,
            losses=3,
            draws=2
        )
        
        assert stats.win_rate == 50.00
        
        # 更新统计
        stats.total_games = 20
        stats.wins = 12
        stats.save()
        
        stats.refresh_from_db()
        assert stats.win_rate == 60.00
    
    @pytest.mark.django_db
    def test_userstats_cascade_delete(self):
        """测试用户统计级联删除"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        stats = UserStats.objects.create(user=user)
        stats_id = stats.id
        
        user.delete()
        
        assert UserStats.objects.filter(id=stats_id).count() == 0


# ==================== User QuerySet 测试 ====================

class TestUserQuerySet:
    """User 查询集测试"""
    
    @pytest.mark.django_db
    def test_user_filter_by_status(self):
        """测试按状态过滤用户"""
        User.objects.create_user(username='active_user', email='active@example.com', password='pass123')
        User.objects.create_user(username='banned_user', email='banned@example.com', password='pass123', status=UserStatus.BANNED)
        
        active_users = User.objects.filter(status=UserStatus.ACTIVE)
        assert active_users.count() == 1
        
        banned_users = User.objects.filter(status=UserStatus.BANNED)
        assert banned_users.count() == 1
    
    @pytest.mark.django_db
    def test_user_filter_by_elo_range(self):
        """测试按 Elo 范围过滤用户"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass123', elo_rating=1200)
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass123', elo_rating=1500)
        user3 = User.objects.create_user(username='user3', email='user3@example.com', password='pass123', elo_rating=1800)
        
        mid_elo_users = User.objects.filter(elo_rating__gte=1400, elo_rating__lte=1600)
        assert mid_elo_users.count() == 1
        assert mid_elo_users.first().username == 'user2'
    
    @pytest.mark.django_db
    def test_user_order_by_elo(self):
        """测试按 Elo 排序"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass123', elo_rating=1200)
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass123', elo_rating=1800)
        user3 = User.objects.create_user(username='user3', email='user3@example.com', password='pass123', elo_rating=1500)
        
        users_by_elo = User.objects.order_by('-elo_rating')
        user_ids = [u.username for u in users_by_elo]
        
        assert user_ids[0] == 'user2'  # 最高分
        assert user_ids[1] == 'user3'
        assert user_ids[2] == 'user1'  # 最低分
    
    @pytest.mark.django_db
    def test_user_filter_active(self):
        """测试过滤活跃用户"""
        User.objects.create_user(username='active_user', email='active@example.com', password='pass123', is_active=True)
        User.objects.create_user(username='inactive_user', email='inactive@example.com', password='pass123', is_active=False)
        
        active_users = User.objects.filter(is_active=True)
        assert active_users.count() == 1


# ==================== User Repository Service 测试 ====================

class TestUserRepository:
    """用户仓库服务测试"""
    
    @pytest.mark.django_db
    def test_get_user_by_id_success(self):
        """测试成功获取用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        retrieved_user = repo.get_user_by_id(str(user.id))
        
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
    
    @pytest.mark.django_db
    def test_get_user_by_id_not_found(self):
        """测试用户不存在"""
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        user = repo.get_user_by_id('nonexistent-id')
        
        assert user is None
    
    @pytest.mark.django_db
    def test_get_user_by_username_success(self):
        """测试成功按用户名获取用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        retrieved_user = repo.get_user_by_username('testuser')
        
        assert retrieved_user is not None
        assert retrieved_user.email == 'test@example.com'
    
    @pytest.mark.django_db
    def test_get_user_by_username_not_found(self):
        """测试用户不存在"""
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        user = repo.get_user_by_username('nonexistent')
        
        assert user is None
    
    @pytest.mark.django_db
    def test_get_user_by_email_success(self):
        """测试成功按邮箱获取用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        retrieved_user = repo.get_user_by_email('test@example.com')
        
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
    
    @pytest.mark.django_db
    def test_update_user_elo(self):
        """测试更新用户 Elo"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            elo_rating=1500
        )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        updated = repo.update_user_elo(str(user.id), 1550)
        
        assert updated is True
        user.refresh_from_db()
        assert user.elo_rating == 1550
    
    @pytest.mark.django_db
    def test_update_user_status(self):
        """测试更新用户状态"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            status=UserStatus.ACTIVE
        )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        updated = repo.update_user_status(str(user.id), UserStatus.BANNED)
        
        assert updated is True
        user.refresh_from_db()
        assert user.status == UserStatus.BANNED
    
    @pytest.mark.django_db
    def test_get_top_players(self):
        """测试获取顶级玩家"""
        for i in range(10):
            User.objects.create_user(
                username=f'player{i}',
                email=f'player{i}@example.com',
                password='pass123',
                elo_rating=1500 + i * 100
            )
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        top_players = repo.get_top_players(limit=5)
        
        assert len(top_players) == 5
        # 应该按 Elo 降序排列
        assert top_players[0].elo_rating >= top_players[1].elo_rating
    
    @pytest.mark.django_db
    def test_get_active_users(self):
        """测试获取活跃用户"""
        User.objects.create_user(username='active1', email='active1@example.com', password='pass123', is_active=True)
        User.objects.create_user(username='active2', email='active2@example.com', password='pass123', is_active=True)
        User.objects.create_user(username='inactive', email='inactive@example.com', password='pass123', is_active=False)
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        active_users = repo.get_active_users()
        
        assert len(active_users) == 2
        for user in active_users:
            assert user.is_active is True
    
    @pytest.mark.django_db
    def test_delete_user(self):
        """测试删除用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        user_id = str(user.id)
        
        from users.services.user_repository import UserRepository
        
        repo = UserRepository()
        deleted = repo.delete_user(user_id)
        
        assert deleted is True
        assert User.objects.filter(id=user_id).count() == 0


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
