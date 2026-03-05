"""
Integration tests for authentication APIs.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegisterAPI:
    """用户注册 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.url = reverse('auth:register')
    
    def test_register_success(self):
        """测试注册成功"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'data' in response.data
        assert 'user_id' in response.data['data']
        assert 'access_token' in response.data['data']
        assert 'refresh_token' in response.data['data']
        
        # 验证用户已创建
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123')
    
    def test_register_duplicate_username(self):
        """测试重复用户名"""
        # 先创建一个用户
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='SecurePass123'
        )
        
        # 尝试用相同用户名注册
        data = {
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'USERNAME_EXISTS' in response.data['error']['code']
    
    def test_register_duplicate_email(self):
        """测试重复邮箱"""
        # 先创建一个用户
        User.objects.create_user(
            username='user1',
            email='duplicate@example.com',
            password='SecurePass123'
        )
        
        # 尝试用相同邮箱注册
        data = {
            'username': 'user2',
            'email': 'duplicate@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'EMAIL_EXISTS' in response.data['error']['code']
    
    def test_register_password_mismatch(self):
        """测试密码不匹配"""
        data = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'DifferentPass456',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_register_weak_password(self):
        """测试弱密码"""
        data = {
            'username': 'newuser3',
            'email': 'newuser3@example.com',
            'password': '123',
            'password_confirm': '123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_register_invalid_email(self):
        """测试无效邮箱"""
        data = {
            'username': 'newuser4',
            'email': 'invalid-email',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_register_short_username(self):
        """测试用户名太短"""
        data = {
            'username': 'ab',  # 至少 3 个字符
            'email': 'short@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False


@pytest.mark.django_db
class TestLoginAPI:
    """用户登录 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.url = reverse('auth:login')
        self.user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='SecurePass123'
        )
    
    def test_login_success(self):
        """测试登录成功"""
        data = {
            'username': 'loginuser',
            'password': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, content_type='application/json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access_token' in response.data['data']
        assert 'refresh_token' in response.data['data']
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        data = {
            'username': 'loginuser',
            'password': 'WrongPassword',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
        assert 'INVALID_CREDENTIALS' in response.data['error']['code']
    
    def test_login_nonexistent_user(self):
        """测试用户不存在"""
        data = {
            'username': 'nonexistent',
            'password': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False
    
    def test_login_banned_user(self):
        """测试被封禁用户登录"""
        self.user.status = 'banned'
        self.user.save()
        
        data = {
            'username': 'loginuser',
            'password': 'SecurePass123',
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert 'USER_BANNED' in response.data['error']['code']


@pytest.mark.django_db
class TestLogoutAPI:
    """用户登出 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.url = reverse('auth:logout')
        self.user = User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='SecurePass123'
        )
    
    def test_logout_success(self):
        """测试登出成功"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'logoutuser',
            'password': 'SecurePass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 登出
        response = self.client.post(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_logout_without_authentication(self):
        """测试未认证用户登出"""
        response = self.client.post(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefreshTokenAPI:
    """Token 刷新 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.url = reverse('auth:refresh')
        self.user = User.objects.create_user(
            username='refreshuser',
            email='refresh@example.com',
            password='SecurePass123'
        )
    
    def test_refresh_token_success(self):
        """测试刷新 Token 成功"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'refreshuser',
            'password': 'SecurePass123',
        })
        
        refresh_token = login_response.data['data']['refresh_token']
        
        # 刷新 token
        response = self.client.post(self.url, {
            'refresh_token': refresh_token,
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access_token' in response.data['data']
    
    def test_refresh_token_invalid(self):
        """测试无效刷新 Token"""
        response = self.client.post(self.url, {
            'refresh_token': 'invalid_token',
        }, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['success'] is False


@pytest.mark.django_db
class TestGetCurrentUserAPI:
    """获取当前用户信息 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.url = reverse('auth:me')
        self.user = User.objects.create_user(
            username='meuser',
            email='me@example.com',
            password='SecurePass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_get_current_user_success(self):
        """测试获取当前用户信息成功"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'meuser',
            'password': 'SecurePass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 获取当前用户信息
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['username'] == 'meuser'
        assert response.data['data']['email'] == 'me@example.com'
    
    def test_get_current_user_unauthenticated(self):
        """测试未认证用户获取信息"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUpdateUserAPI:
    """更新用户信息 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='updateuser',
            email='update@example.com',
            password='SecurePass123',
            first_name='John',
            last_name='Doe'
        )
        self.url = reverse('users:detail', kwargs={'pk': self.user.id})
    
    def test_update_user_success(self):
        """测试更新用户信息成功"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'updateuser',
            'password': 'SecurePass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 更新用户信息
        response = self.client.put(self.url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 验证更新
        self.user.refresh_from_db()
        assert self.user.first_name == 'Jane'
        assert self.user.last_name == 'Smith'


@pytest.mark.django_db
class TestChangePasswordAPI:
    """修改密码 API 测试"""
    
    def setup_method(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='passworduser',
            email='password@example.com',
            password='OldPass123'
        )
        self.url = reverse('users:change-password', kwargs={'pk': self.user.id})
    
    def test_change_password_success(self):
        """测试修改密码成功"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'passworduser',
            'password': 'OldPass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 修改密码
        response = self.client.put(self.url, {
            'old_password': 'OldPass123',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456',
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        
        # 验证新密码生效
        self.user.refresh_from_db()
        assert self.user.check_password('NewPass456')
    
    def test_change_password_wrong_old_password(self):
        """测试旧密码错误"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'passworduser',
            'password': 'OldPass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 修改密码（旧密码错误）
        response = self.client.put(self.url, {
            'old_password': 'WrongOldPass',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456',
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_change_password_mismatch(self):
        """测试新密码不匹配"""
        # 先登录获取 token
        login_response = self.client.post(reverse('auth:login'), {
            'username': 'passworduser',
            'password': 'OldPass123',
        })
        
        access_token = login_response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 修改密码（两次输入不一致）
        response = self.client.put(self.url, {
            'old_password': 'OldPass123',
            'new_password': 'NewPass456',
            'new_password_confirm': 'DifferentPass789',
        }, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
