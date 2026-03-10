"""
认证 API 视图测试
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    """用户注册 API 测试"""

    def test_register_success(self):
        """测试注册成功"""
        url = reverse('auth:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'access_token' in response.data['data']
        assert 'refresh_token' in response.data['data']
        assert response.data['data']['username'] == 'testuser'
        
        # 验证用户已创建
        assert User.objects.filter(username='testuser').exists()

    def test_register_username_exists(self):
        """测试用户名已存在"""
        url = reverse('auth:register')
        data = {
            'username': 'existinguser',
            'email': 'existing@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123'
        }
        
        # 创建已存在用户
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='TestPass123'
        )
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'error' in response.data

    def test_register_email_exists(self):
        """测试邮箱已存在"""
        url = reverse('auth:register')
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123'
        }
        
        # 创建已存在邮箱的用户
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='TestPass123'
        )
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_register_invalid_email(self):
        """测试无效邮箱格式"""
        url = reverse('auth:register')
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_register_short_password(self):
        """测试密码过短"""
        url = reverse('auth:register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short',
            'password_confirm': 'short'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    def test_register_short_username(self):
        """测试用户名过短"""
        url = reverse('auth:register')
        data = {
            'username': 'te',
            'email': 'test@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginAPI:
    """用户登录 API 测试"""

    def test_login_success(self):
        """测试登录成功"""
        # 创建测试用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        url = reverse('auth:login')
        data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access_token' in response.data['data']
        assert 'refresh_token' in response.data['data']
        assert response.data['data']['user_id'] == str(user.id)

    def test_login_wrong_password(self):
        """测试密码错误"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        url = reverse('auth:login')
        data = {
            'username': 'testuser',
            'password': 'WrongPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'INVALID_CREDENTIALS'

    def test_login_user_not_found(self):
        """测试用户不存在"""
        url = reverse('auth:login')
        data = {
            'username': 'nonexistent',
            'password': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False

    def test_login_banned_user(self):
        """测试被封禁用户登录"""
        user = User.objects.create_user(
            username='banneduser',
            email='banned@example.com',
            password='TestPass123',
            is_active=False
        )
        # 模拟封禁状态 (根据实际实现调整)
        
        url = reverse('auth:login')
        data = {
            'username': 'banneduser',
            'password': 'TestPass123'
        }
        
        response = APIClient().post(url, data, format='json')
        
        # 根据实际实现，可能返回 401 或 403
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
class TestLogoutAPI:
    """用户登出 API 测试"""

    def test_logout_success(self):
        """测试登出成功"""
        # 创建并登录用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('auth:logout')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_logout_unauthenticated(self):
        """测试未认证用户登出"""
        url = reverse('auth:logout')
        response = APIClient().post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefreshTokenAPI:
    """Token 刷新 API 测试"""

    def test_refresh_token_success(self):
        """测试刷新 Token 成功"""
        # 创建用户并获取 Token
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        # 登录获取 refresh token
        login_url = reverse('auth:login')
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        login_response = APIClient().post(login_url, login_data, format='json')
        refresh_token = login_response.data['data']['refresh_token']
        
        # 刷新 Token
        url = reverse('auth:refresh')
        data = {
            'refresh_token': refresh_token
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access_token' in response.data['data']

    def test_refresh_token_missing(self):
        """测试缺少 refresh token"""
        url = reverse('auth:refresh')
        data = {}
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'TOKEN_REQUIRED'

    def test_refresh_token_invalid(self):
        """测试无效 refresh token"""
        url = reverse('auth:refresh')
        data = {
            'refresh_token': 'invalid_token'
        }
        
        response = APIClient().post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False


@pytest.mark.django_db
class TestCurrentUserAPI:
    """当前用户信息 API 测试"""

    def test_get_current_user_success(self):
        """测试获取当前用户信息成功"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        
        client = APIClient()
        client.force_authenticate(user=user)
        
        url = reverse('auth:me')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['id'] == user.id
        assert response.data['data']['username'] == user.username
        assert response.data['data']['email'] == user.email

    def test_get_current_user_unauthenticated(self):
        """测试未认证用户获取信息"""
        url = reverse('auth:me')
        response = APIClient().get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
