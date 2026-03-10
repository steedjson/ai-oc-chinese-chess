"""
用户模型扩展测试
测试 UserProfile 和 UserStats 模型以及 User 模型的额外功能
"""
import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from users.models import User, UserProfile, UserStats, UserStatus

User = get_user_model()


@pytest.mark.django_db
class TestUserModelExtended:
    """User 模型扩展测试"""
    
    def test_user_password_hash_synchronized(self):
        """测试密码哈希同步"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
        
        # password_hash 字段应该被设置
        assert user.password_hash is not None
        assert user.password_hash == user.password
    
    def test_user_set_password_marks_changed(self):
        """测试设置密码时标记变化"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123'
        )
        
        user.set_password('NewPass456')
        
        # 应该标记密码已变化
        assert hasattr(user, '_password_changed')
        assert user._password_changed is True
    
    def test_user_save_syncs_password_hash_on_create(self):
        """测试创建用户时同步密码哈希"""
        user = User(
            username='newuser',
            email='new@example.com'
        )
        user.set_password('Password123')
        user.save()
        
        # 刷新后验证
        user.refresh_from_db()
        assert user.password_hash is not None
    
    def test_user_get_full_name_empty(self):
        """测试空全名返回用户名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        # 没有 first_name 和 last_name
        full_name = user.get_full_name()
        assert full_name == 'testuser'
    
    def test_user_get_full_name_with_first_only(self):
        """测试只有名字的全名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            first_name='John'
        )
        
        full_name = user.get_full_name()
        assert full_name == 'John'
    
    def test_user_get_full_name_with_last_only(self):
        """测试只有姓氏的全名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            last_name='Doe'
        )
        
        full_name = user.get_full_name()
        assert full_name == 'Doe'
    
    def test_user_get_full_name_with_both(self):
        """测试有名字和姓氏的全名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            first_name='John',
            last_name='Doe'
        )
        
        full_name = user.get_full_name()
        assert full_name == 'John Doe'
    
    def test_user_get_short_name_empty(self):
        """测试空短名返回用户名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        short_name = user.get_short_name()
        assert short_name == 'testuser'
    
    def test_user_get_short_name_with_first_name(self):
        """测试有名字的短名"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            first_name='John'
        )
        
        short_name = user.get_short_name()
        assert short_name == 'John'
    
    def test_user_is_banned_false(self):
        """测试未封禁用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            status=UserStatus.ACTIVE
        )
        
        assert user.is_banned() is False
    
    def test_user_is_banned_true(self):
        """测试封禁用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            status=UserStatus.BANNED
        )
        
        assert user.is_banned() is True
    
    def test_user_is_banned_inactive(self):
        """测试不活跃用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            status=UserStatus.INACTIVE
        )
        
        assert user.is_banned() is False
    
    def test_user_status_choices(self):
        """测试用户状态选择"""
        assert UserStatus.ACTIVE.value == 'active'
        assert UserStatus.INACTIVE.value == 'inactive'
        assert UserStatus.BANNED.value == 'banned'
    
    def test_user_update_status_preserves_other_fields(self):
        """测试更新状态时保留其他字段"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            elo_rating=1800,
            first_name='John'
        )
        
        user.status = UserStatus.BANNED
        user.save()
        
        user.refresh_from_db()
        assert user.status == UserStatus.BANNED
        assert user.elo_rating == 1800
        assert user.first_name == 'John'
    
    def test_user_timestamps_auto_updated(self):
        """测试时间戳自动更新"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        created_at = user.created_at
        updated_at = user.updated_at
        
        # 等待一小段时间
        import time
        time.sleep(0.01)
        
        # 更新用户
        user.elo_rating = 1600
        user.save()
        
        user.refresh_from_db()
        
        # created_at 不应改变
        assert user.created_at == created_at
        # updated_at 应该改变
        assert user.updated_at > updated_at
    
    def test_user_email_normalized(self):
        """测试邮箱标准化"""
        user = User.objects.create_user(
            username='testuser',
            email='TEST@EXAMPLE.COM',  # 大写
            password='password'
        )
        
        # Django 应该标准化邮箱为小写
        assert user.email == 'test@example.com'
    
    def test_user_check_password_correct(self):
        """测试密码验证正确"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
        
        assert user.check_password('SecurePass123') is True
    
    def test_user_check_password_incorrect(self):
        """测试密码验证错误"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123'
        )
        
        assert user.check_password('WrongPass') is False
    
    def test_user_is_active_flag(self):
        """测试 is_active 标志"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            is_active=True
        )
        
        assert user.is_active is True
        
        user.is_active = False
        user.save()
        
        user.refresh_from_db()
        assert user.is_active is False
    
    def test_user_is_staff_flag(self):
        """测试 is_staff 标志"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            is_staff=False
        )
        
        assert user.is_staff is False
        
        user.is_staff = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_staff is True
    
    def test_user_is_superuser_flag(self):
        """测试 is_superuser 标志"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            is_superuser=False
        )
        
        assert user.is_superuser is False
    
    def test_user_has_usable_password(self):
        """测试可用密码"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        assert user.has_usable_password() is True
    
    def test_user_ordering_by_created_at(self):
        """测试按创建时间排序"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        
        users = list(User.objects.all())
        
        # 应该按 created_at 降序排列
        assert users[0] == user2
        assert users[1] == user1


@pytest.mark.django_db
class TestUserProfile:
    """UserProfile 模型测试"""
    
    def test_create_profile(self):
        """测试创建用户档案"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='这是一个测试简介',
            location='北京',
            birthday=date(1990, 1, 1),
            gender='male'
        )
        
        assert profile.user == user
        assert profile.bio == '这是一个测试简介'
        assert profile.location == '北京'
        assert profile.birthday == date(1990, 1, 1)
        assert profile.gender == 'male'
    
    def test_create_profile_minimal(self):
        """测试创建最小用户档案"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        assert profile.user == user
        assert profile.bio is None
        assert profile.location is None
        assert profile.birthday is None
        assert profile.gender is None
    
    def test_profile_str_representation(self):
        """测试档案字符串表示"""
        user = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        assert str(profile) == "john_doe's profile"
    
    def test_profile_one_to_one_with_user(self):
        """测试档案与用户的一对一关系"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile1 = UserProfile.objects.create(user=user)
        
        # 尝试创建第二个档案应该失败
        with pytest.raises(IntegrityError):
            UserProfile.objects.create(user=user)
    
    def test_profile_cascade_delete(self):
        """测试级联删除"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        profile_id = profile.id
        
        # 删除用户
        user.delete()
        
        # 档案也应该被删除
        assert not UserProfile.objects.filter(id=profile_id).exists()
    
    def test_profile_get_or_create(self):
        """测试获取或创建档案"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        # 获取或创建
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        assert created is True
        assert profile.user == user
        
        # 再次获取
        profile2, created2 = UserProfile.objects.get_or_create(user=user)
        
        assert created2 is False
        assert profile2.id == profile.id
    
    def test_profile_update(self):
        """测试更新档案"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='原始简介'
        )
        
        profile.bio = '更新后的简介'
        profile.location = '上海'
        profile.save()
        
        profile.refresh_from_db()
        
        assert profile.bio == '更新后的简介'
        assert profile.location == '上海'
    
    def test_profile_timestamps(self):
        """测试档案时间戳"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.created_at <= profile.updated_at
    
    def test_profile_user_relation(self):
        """测试档案用户关系"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        
        # 通过用户访问档案
        assert hasattr(user, 'userprofile')
        assert user.userprofile == profile


@pytest.mark.django_db
class TestUserStats:
    """UserStats 模型测试"""
    
    def test_create_stats(self):
        """测试创建用户统计"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10,
            favorite_opening='中炮对屏风马'
        )
        
        assert stats.user == user
        assert stats.total_games == 100
        assert stats.wins == 60
        assert stats.losses == 30
        assert stats.draws == 10
        assert stats.favorite_opening == '中炮对屏风马'
    
    def test_create_stats_minimal(self):
        """测试创建最小用户统计"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(user=user)
        
        assert stats.user == user
        assert stats.total_games == 0
        assert stats.wins == 0
        assert stats.losses == 0
        assert stats.draws == 0
        assert stats.win_rate == 0.0
        assert stats.favorite_opening is None
    
    def test_stats_win_rate_auto_calculated(self):
        """测试胜率自动计算"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10
        )
        
        # 胜率应该是 60%
        assert stats.win_rate == 60.00
    
    def test_stats_win_rate_zero_games(self):
        """测试零场游戏时的胜率"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=0,
            wins=0,
            losses=0,
            draws=0
        )
        
        assert stats.win_rate == 0.0
    
    def test_stats_win_rate_calculation_edge_cases(self):
        """测试胜率计算边界情况"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        # 100% 胜率
        stats1 = UserStats.objects.create(
            user=user,
            total_games=10,
            wins=10,
            losses=0,
            draws=0
        )
        assert stats1.win_rate == 100.00
        
        # 50% 胜率
        stats2 = UserStats.objects.create(
            user=user,
            total_games=20,
            wins=10,
            losses=10,
            draws=0
        )
        assert stats2.win_rate == 50.00
        
        # 小数胜率
        stats3 = UserStats.objects.create(
            user=user,
            total_games=33,
            wins=10,
            losses=23,
            draws=0
        )
        assert stats3.win_rate == 30.30  # 10/33 = 0.3030...
    
    def test_stats_str_representation(self):
        """测试统计字符串表示"""
        user = User.objects.create_user(
            username='chess_master',
            email='master@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(user=user)
        
        assert str(stats) == "chess_master's stats"
    
    def test_stats_one_to_one_with_user(self):
        """测试统计与用户的一对一关系"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats1 = UserStats.objects.create(user=user)
        
        # 尝试创建第二个统计应该失败
        with pytest.raises(IntegrityError):
            UserStats.objects.create(user=user)
    
    def test_stats_cascade_delete(self):
        """测试级联删除"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(user=user)
        stats_id = stats.id
        
        # 删除用户
        user.delete()
        
        # 统计也应该被删除
        assert not UserStats.objects.filter(id=stats_id).exists()
    
    def test_stats_update_win_rate_on_save(self):
        """测试保存时更新胜率"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=10,
            wins=5,
            losses=3,
            draws=2
        )
        
        assert stats.win_rate == 50.00
        
        # 更新数据
        stats.total_games = 20
        stats.wins = 15
        stats.losses = 3
        stats.draws = 2
        stats.save()
        
        stats.refresh_from_db()
        
        # 胜率应该自动更新
        assert stats.win_rate == 75.00
    
    def test_stats_timestamps(self):
        """测试统计时间戳"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(user=user)
        
        assert stats.created_at is not None
        assert stats.updated_at is not None
        assert stats.created_at <= stats.updated_at
    
    def test_stats_user_relation(self):
        """测试统计用户关系"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        stats = UserStats.objects.create(user=user)
        
        # 通过用户访问统计
        assert hasattr(user, 'userstats')
        assert user.userstats == stats
    
    def test_stats_games_sum_consistency(self):
        """测试游戏总数一致性"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        # 创建统计，wins + losses + draws = total_games
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=50,
            losses=30,
            draws=20
        )
        
        # 验证总和
        assert stats.wins + stats.losses + stats.draws == stats.total_games


@pytest.mark.django_db
class TestUserWithProfileAndStats:
    """用户与档案和统计的集成测试"""
    
    def test_user_with_complete_profile_and_stats(self):
        """测试用户有完整的档案和统计"""
        user = User.objects.create_user(
            username='complete_user',
            email='complete@example.com',
            password='password',
            first_name='Complete',
            last_name='User',
            elo_rating=2000
        )
        
        profile = UserProfile.objects.create(
            user=user,
            bio='完整的用户档案',
            location='北京',
            birthday=date(1990, 1, 1),
            gender='male'
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=200,
            wins=120,
            losses=60,
            draws=20,
            favorite_opening='中炮对屏风马'
        )
        
        # 验证所有关系
        assert user.userprofile == profile
        assert user.userstats == stats
        assert stats.win_rate == 60.00
    
    def test_user_delete_cascades_to_profile_and_stats(self):
        """测试删除用户时级联删除档案和统计"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        
        profile = UserProfile.objects.create(user=user)
        stats = UserStats.objects.create(user=user)
        
        profile_id = profile.id
        stats_id = stats.id
        
        # 删除用户
        user.delete()
        
        # 档案和统计都应该被删除
        assert not UserProfile.objects.filter(id=profile_id).exists()
        assert not UserStats.objects.filter(id=stats_id).exists()
    
    def test_create_user_with_related_objects(self):
        """测试创建用户及相关对象"""
        user = User.objects.create_user(
            username='new_player',
            email='player@example.com',
            password='password'
        )
        
        # 创建档案和统计
        UserProfile.objects.create(user=user, bio='新玩家')
        UserStats.objects.create(user=user, total_games=0)
        
        # 验证
        assert user.userprofile.bio == '新玩家'
        assert user.userstats.total_games == 0
