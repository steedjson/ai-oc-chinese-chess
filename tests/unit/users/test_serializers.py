"""
测试用户序列化器

测试 users/serializers.py 中的所有序列化器
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from users.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer,
    UserStatsSerializer,
    UserDetailSerializer,
)
from users.models import UserProfile, UserStats

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializer:
    """测试 UserSerializer"""
    
    def test_serialize_user(self, user):
        """测试序列化用户对象"""
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert data['username'] == user.username
        assert data['email'] == user.email
        assert 'id' in data
        assert 'created_at' in data
    
    def test_read_only_fields(self, user):
        """测试只读字段"""
        serializer = UserSerializer(user, data={
            'username': 'newusername',
            'elo_rating': 9999,  # 应该被忽略
        }, partial=True)
        
        if serializer.is_valid():
            serializer.save()
        
        # elo_rating 不应该被修改
        user.refresh_from_db()
        assert user.elo_rating != 9999 or 'elo_rating' not in serializer.validated_data


@pytest.mark.django_db
class TestRegisterSerializer:
    """测试 RegisterSerializer"""
    
    def test_valid_registration(self):
        """测试有效注册"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        
        serializer = RegisterSerializer(data=data)
        
        assert serializer.is_valid(), f"验证失败：{serializer.errors}"
        
        user = serializer.save()
        
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123!')
        
        # 检查是否自动创建档案和统计
        assert hasattr(user, 'userprofile')
        assert hasattr(user, 'userstats')
    
    def test_password_mismatch(self):
        """测试密码不匹配"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass456!',
        }
        
        serializer = RegisterSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors
    
    def test_duplicate_email(self, user):
        """测试重复邮箱"""
        data = {
            'username': 'anotheruser',
            'email': user.email,  # 已存在的邮箱
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        
        serializer = RegisterSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_short_username(self):
        """测试用户名过短"""
        data = {
            'username': 'ab',  # 少于 3 个字符
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        
        serializer = RegisterSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'username' in serializer.errors
    
    def test_long_username(self):
        """测试用户名过长"""
        data = {
            'username': 'a' * 51,  # 超过 50 个字符
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        
        serializer = RegisterSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'username' in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """测试 LoginSerializer"""
    
    def test_valid_login(self, user):
        """测试有效登录"""
        data = {
            'username': user.username,
            'password': 'testpass123',
        }
        
        serializer = LoginSerializer(data=data)
        
        assert serializer.is_valid(), f"验证失败：{serializer.errors}"
        assert 'user' in serializer.validated_data
        assert serializer.validated_data['user'] == user
    
    def test_invalid_credentials(self, user):
        """测试无效凭证"""
        data = {
            'username': user.username,
            'password': 'wrongpassword',
        }
        
        serializer = LoginSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors or 'password' in serializer.errors
    
    def test_empty_credentials(self):
        """测试空凭证"""
        data = {
            'username': '',
            'password': '',
        }
        
        serializer = LoginSerializer(data=data)
        
        assert not serializer.is_valid()
    
    def test_inactive_user(self):
        """测试非活跃用户"""
        user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpass123',
            is_active=False,
        )
        
        data = {
            'username': 'inactiveuser',
            'password': 'testpass123',
        }
        
        serializer = LoginSerializer(data=data)
        
        assert not serializer.is_valid()
        assert '账号已被禁用' in str(serializer.errors)
    
    def test_banned_user(self):
        """测试被封禁用户"""
        user = User.objects.create_user(
            username='banneduser',
            email='banned@example.com',
            password='testpass123',
        )
        user.status = 'banned'
        user.save()
        
        data = {
            'username': 'banneduser',
            'password': 'testpass123',
        }
        
        serializer = LoginSerializer(data=data)
        
        assert not serializer.is_valid()
        assert '账号已被封禁' in str(serializer.errors)


@pytest.mark.django_db
class TestChangePasswordSerializer:
    """测试 ChangePasswordSerializer"""
    
    def test_valid_password_change(self, user, api_client):
        """测试有效密码修改"""
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }
        
        # 设置 request context
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/fake-url')
        request.user = user
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        
        assert serializer.is_valid(), f"验证失败：{serializer.errors}"
    
    def test_wrong_old_password(self, user, api_client):
        """测试错误的旧密码"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/fake-url')
        request.user = user
        
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'NewSecurePass456!',
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'old_password' in serializer.errors
    
    def test_password_mismatch(self, user, api_client):
        """测试新密码不匹配"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/fake-url')
        request.user = user
        
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewSecurePass456!',
            'new_password_confirm': 'DifferentPass789!',
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'new_password_confirm' in serializer.errors
    
    def test_same_password(self, user, api_client):
        """测试新密码与旧密码相同"""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/fake-url')
        request.user = user
        
        data = {
            'old_password': 'testpass123',
            'new_password': 'testpass123',
            'new_password_confirm': 'testpass123',
        }
        
        serializer = ChangePasswordSerializer(data=data, context={'request': request})
        
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors


@pytest.mark.django_db
class TestUserProfileSerializer:
    """测试 UserProfileSerializer"""
    
    def test_serialize_profile(self, user):
        """测试序列化用户档案"""
        profile = UserProfile.objects.create(
            user=user,
            bio='Test bio',
            location='Beijing',
            gender='M',
        )
        
        serializer = UserProfileSerializer(profile)
        data = serializer.data
        
        assert data['bio'] == 'Test bio'
        assert data['location'] == 'Beijing'
        assert data['gender'] == 'M'
    
    def test_update_profile(self, user):
        """测试更新用户档案"""
        profile = UserProfile.objects.create(user=user)
        
        data = {
            'bio': 'Updated bio',
            'location': 'Shanghai',
        }
        
        serializer = UserProfileSerializer(profile, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
        
        profile.refresh_from_db()
        assert profile.bio == 'Updated bio'
        assert profile.location == 'Shanghai'


@pytest.mark.django_db
class TestUserStatsSerializer:
    """测试 UserStatsSerializer"""
    
    def test_serialize_stats(self, user):
        """测试序列化用户统计"""
        stats = UserStats.objects.create(
            user=user,
            total_games=100,
            wins=60,
            losses=30,
            draws=10,
        )
        
        serializer = UserStatsSerializer(stats)
        data = serializer.data
        
        assert data['total_games'] == 100
        assert data['wins'] == 60
        assert data['losses'] == 30
        assert data['draws'] == 10
        assert abs(data['win_rate'] - 0.6) < 0.01
    
    def test_win_rate_calculation(self, user):
        """测试胜率计算"""
        stats = UserStats.objects.create(
            user=user,
            total_games=50,
            wins=25,
            losses=20,
            draws=5,
        )
        
        serializer = UserStatsSerializer(stats)
        data = serializer.data
        
        # 胜率 = (wins + draws/2) / total_games
        expected_win_rate = (25 + 5/2) / 50
        assert abs(data['win_rate'] - expected_win_rate) < 0.01


@pytest.mark.django_db
class TestUserDetailSerializer:
    """测试 UserDetailSerializer"""
    
    def test_serialize_user_detail(self, user):
        """测试序列化用户详情"""
        # 确保档案和统计存在
        UserProfile.objects.get_or_create(user=user)
        UserStats.objects.get_or_create(user=user)
        
        serializer = UserDetailSerializer(user)
        data = serializer.data
        
        assert 'profile' in data
        assert 'stats' in data
        assert data['username'] == user.username
        assert data['email'] == user.email
    
    def test_nested_data(self, user):
        """测试嵌套数据"""
        profile = UserProfile.objects.create(
            user=user,
            bio='Test bio',
        )
        
        stats = UserStats.objects.create(
            user=user,
            total_games=50,
            wins=30,
        )
        
        serializer = UserDetailSerializer(user)
        data = serializer.data
        
        assert data['profile']['bio'] == 'Test bio'
        assert data['stats']['total_games'] == 50


@pytest.fixture
def user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    from rest_framework.test import APIClient
    return APIClient()
