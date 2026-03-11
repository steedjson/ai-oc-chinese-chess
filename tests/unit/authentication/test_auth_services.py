"""
Authentication Service 测试
测试认证服务核心功能：Token 生成、验证、刷新、密码管理
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# 导入被测试模块
from authentication.services import TokenService, AuthService


# ==================== TokenService 测试 ====================

class TestTokenServiceGenerateTokens:
    """Token 生成测试"""
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_generate_tokens_success(self, mock_settings, mock_jwt):
        """测试成功生成 tokens"""
        # Mock settings
        mock_settings.SECRET_KEY = 'test_secret_key'
        mock_settings.SIMPLE_JWT = {
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=7)
        }
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        
        # Mock JWT encode
        mock_jwt.encode.return_value = 'encoded_token'
        
        tokens = TokenService.generate_tokens(mock_user)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['access_token'] == 'encoded_token'
        assert tokens['refresh_token'] == 'encoded_token'
        mock_jwt.encode.assert_called()
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_generate_tokens_payload(self, mock_settings, mock_jwt):
        """测试 token payload 内容"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        mock_settings.SIMPLE_JWT = {
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=7)
        }
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        
        tokens = TokenService.generate_tokens(mock_user)
        
        # 验证 JWT encode 被调用
        assert mock_jwt.encode.called
        
        # 验证调用参数
        call_args = mock_jwt.encode.call_args
        payload = call_args[0][0]
        
        assert payload['user_id'] == 1
        assert payload['username'] == 'testuser'


class TestTokenServiceVerifyToken:
    """Token 验证测试"""
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_success(self, mock_settings, mock_jwt):
        """测试成功验证 token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        # Mock JWT decode
        mock_jwt.decode.return_value = {
            'user_id': 1,
            'username': 'testuser',
            'exp': time.time() + 3600
        }
        
        payload = TokenService.verify_token('valid_token')
        
        assert payload is not None
        assert payload['user_id'] == 1
        assert payload['username'] == 'testuser'
        mock_jwt.decode.assert_called_once()
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_expired(self, mock_settings, mock_jwt):
        """测试过期 token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        # Mock JWT decode 抛出过期异常
        mock_jwt.decode.side_effect = Exception("Token expired")
        
        with pytest.raises(Exception):
            TokenService.verify_token('expired_token')
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_invalid(self, mock_settings, mock_jwt):
        """测试无效 token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        # Mock JWT decode 抛出异常
        mock_jwt.decode.side_effect = Exception("Invalid token")
        
        with pytest.raises(Exception):
            TokenService.verify_token('invalid_token')
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_missing_user_id(self, mock_settings, mock_jwt):
        """测试 payload 缺少 user_id"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        # Mock JWT decode 返回无 user_id 的 payload
        mock_jwt.decode.return_value = {
            'exp': time.time() + 3600,
            'other': 'data'
        }
        
        payload = TokenService.verify_token('token_no_user_id')
        
        assert payload is not None
        assert 'user_id' not in payload


class TestTokenServiceRefreshToken:
    """Token 刷新测试"""
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_refresh_token_success(self, mock_settings, mock_jwt):
        """测试成功刷新 token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        mock_settings.SIMPLE_JWT = {
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=7)
        }
        
        # Mock refresh token decode
        mock_jwt.decode.return_value = {
            'user_id': 1,
            'username': 'testuser',
            'type': 'refresh'
        }
        
        # Mock new token encode
        mock_jwt.encode.return_value = 'new_access_token'
        
        new_token = TokenService.refresh_token('valid_refresh_token')
        
        assert new_token == 'new_access_token'
        mock_jwt.decode.assert_called_once()
        mock_jwt.encode.assert_called()
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_refresh_token_invalid_type(self, mock_settings, mock_jwt):
        """测试使用 access token 刷新"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        # Mock decode 返回 access token
        mock_jwt.decode.return_value = {
            'user_id': 1,
            'type': 'access'  # 不是 refresh token
        }
        
        with pytest.raises(Exception, match="Invalid token type"):
            TokenService.refresh_token('access_token')


class TestTokenServiceBlacklistToken:
    """Token 黑名单测试"""
    
    @patch('authentication.services.redis')
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_blacklist_token_success(self, mock_settings, mock_jwt, mock_redis):
        """测试成功将 token 加入黑名单"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        
        # Mock token decode 获取 exp
        mock_jwt.decode.return_value = {
            'exp': time.time() + 3600
        }
        
        TokenService.blacklist_token('token_to_blacklist')
        
        mock_redis_instance.set.assert_called_once()
    
    @patch('authentication.services.redis')
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_blacklist_token_redis_error(self, mock_settings, mock_jwt, mock_redis):
        """测试 Redis 错误"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.set.side_effect = Exception("Redis error")
        
        mock_jwt.decode.return_value = {
            'exp': time.time() + 3600
        }
        
        # 应该不抛出异常
        TokenService.blacklist_token('token_to_blacklist')


class TestTokenServiceIsTokenBlacklisted:
    """检查 token 是否在黑名单测试"""
    
    @patch('authentication.services.redis')
    def test_is_token_blacklisted_true(self, mock_redis):
        """测试 token 在黑名单中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = b'1'  # 在黑名单中
        
        result = TokenService.is_token_blacklisted('blacklisted_token')
        
        assert result is True
    
    @patch('authentication.services.redis')
    def test_is_token_blacklisted_false(self, mock_redis):
        """测试 token 不在黑名单中"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.get.return_value = None  # 不在黑名单中
        
        result = TokenService.is_token_blacklisted('valid_token')
        
        assert result is False


# ==================== AuthService 测试 ====================

class TestAuthServiceRegister:
    """用户注册测试"""
    
    @patch('authentication.services.User')
    def test_register_success(self, mock_user_model):
        """测试成功注册"""
        # Mock user creation
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'newuser'
        mock_user.email = 'new@example.com'
        mock_user_model.objects.create_user.return_value = mock_user
        
        # Mock TokenService
        with patch('authentication.services.TokenService') as mock_token_service:
            mock_token_service.generate_tokens.return_value = {
                'access_token': 'access_123',
                'refresh_token': 'refresh_123'
            }
            
            result = AuthService.register(
                username='newuser',
                email='new@example.com',
                password='password123'
            )
            
            assert result['success'] is True
            assert result['user']['id'] == 1
            assert result['tokens']['access_token'] == 'access_123'
            mock_user_model.objects.create_user.assert_called_once()
    
    @patch('authentication.services.User')
    def test_register_username_exists(self, mock_user_model):
        """测试用户名已存在"""
        # Mock IntegrityError
        from django.db import IntegrityError
        mock_user_model.objects.create_user.side_effect = IntegrityError("Username exists")
        
        result = AuthService.register(
            username='existinguser',
            email='test@example.com',
            password='password123'
        )
        
        assert result['success'] is False
        assert result['error']['code'] == 'USERNAME_EXISTS'
    
    @patch('authentication.services.User')
    def test_register_email_exists(self, mock_user_model):
        """测试邮箱已存在"""
        from django.db import IntegrityError
        mock_user_model.objects.create_user.side_effect = IntegrityError("Email exists")
        
        result = AuthService.register(
            username='newuser',
            email='existing@example.com',
            password='password123'
        )
        
        assert result['success'] is False
        assert result['error']['code'] == 'EMAIL_EXISTS'


class TestAuthServiceLogin:
    """用户登录测试"""
    
    @patch('authentication.services.User')
    @patch('authentication.services.TokenService')
    def test_login_success(self, mock_token_service, mock_user_model):
        """测试成功登录"""
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.check_password.return_value = True
        mock_user_model.objects.get.return_value = mock_user
        
        # Mock token generation
        mock_token_service.generate_tokens.return_value = {
            'access_token': 'access_123',
            'refresh_token': 'refresh_123'
        }
        
        result = AuthService.login('testuser', 'password123')
        
        assert result['success'] is True
        assert result['user']['id'] == 1
        assert result['tokens']['access_token'] == 'access_123'
        mock_user_model.objects.get.assert_called_once()
        mock_user.check_password.assert_called_once()
    
    @patch('authentication.services.User')
    def test_login_user_not_found(self, mock_user_model):
        """测试用户不存在"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        result = AuthService.login('nonexistent', 'password123')
        
        assert result['success'] is False
        assert result['error']['code'] == 'USER_NOT_FOUND'
    
    @patch('authentication.services.User')
    def test_login_wrong_password(self, mock_user_model):
        """测试密码错误"""
        mock_user = Mock()
        mock_user.check_password.return_value = False
        mock_user_model.objects.get.return_value = mock_user
        
        result = AuthService.login('testuser', 'wrongpassword')
        
        assert result['success'] is False
        assert result['error']['code'] == 'WRONG_PASSWORD'
    
    @patch('authentication.services.User')
    def test_login_inactive_user(self, mock_user_model):
        """测试非活跃用户"""
        mock_user = Mock()
        mock_user.is_active = False
        mock_user.check_password.return_value = True
        mock_user_model.objects.get.return_value = mock_user
        
        result = AuthService.login('testuser', 'password123')
        
        assert result['success'] is False
        assert result['error']['code'] == 'USER_INACTIVE'


class TestAuthServiceLogout:
    """用户登出测试"""
    
    @patch('authentication.services.TokenService')
    def test_logout_success(self, mock_token_service):
        """测试成功登出"""
        mock_token_service.blacklist_token = Mock()
        
        result = AuthService.logout('access_token', 'refresh_token')
        
        assert result['success'] is True
        assert result['message'] == '登出成功'
        mock_token_service.blacklist_token.assert_called()
    
    @patch('authentication.services.TokenService')
    def test_logout_token_error(self, mock_token_service):
        """测试 token 错误"""
        mock_token_service.blacklist_token.side_effect = Exception("Token error")
        
        result = AuthService.logout('invalid_token', 'invalid_refresh')
        
        assert result['success'] is False
        assert result['error']['code'] == 'TOKEN_ERROR'


class TestAuthServiceChangePassword:
    """修改密码测试"""
    
    @patch('authentication.services.User')
    def test_change_password_success(self, mock_user_model):
        """测试成功修改密码"""
        mock_user = Mock()
        mock_user.check_password.return_value = True
        mock_user_model.objects.get.return_value = mock_user
        
        AuthService.change_password(
            user=mock_user,
            old_password='oldpass123',
            new_password='newpass456'
        )
        
        mock_user.check_password.assert_called_once_with('oldpass123')
        mock_user.set_password.assert_called_once_with('newpass456')
        mock_user.save.assert_called_once()
    
    @patch('authentication.services.User')
    def test_change_password_wrong_old(self, mock_user_model):
        """测试旧密码错误"""
        mock_user = Mock()
        mock_user.check_password.return_value = False
        
        with pytest.raises(Exception, match="WRONG_OLD_PASSWORD"):
            AuthService.change_password(
                user=mock_user,
                old_password='wrongpass',
                new_password='newpass456'
            )
    
    @patch('authentication.services.User')
    def test_change_password_same_password(self, mock_user_model):
        """测试新密码与旧密码相同"""
        mock_user = Mock()
        mock_user.check_password.return_value = True
        
        with pytest.raises(Exception, match="SAME_PASSWORD"):
            AuthService.change_password(
                user=mock_user,
                old_password='samepass',
                new_password='samepass'
            )


class TestAuthServiceGetUserById:
    """根据 ID 获取用户测试"""
    
    @patch('authentication.services.User')
    def test_get_user_by_id_success(self, mock_user_model):
        """测试成功获取用户"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.elo_rating = 1500
        mock_user_model.objects.get.return_value = mock_user
        
        user_data = AuthService.get_user_by_id('1')
        
        assert user_data is not None
        assert user_data['id'] == '1'
        assert user_data['username'] == 'testuser'
        assert user_data['email'] == 'test@example.com'
        assert user_data['elo_rating'] == 1500
    
    @patch('authentication.services.User')
    def test_get_user_by_id_not_found(self, mock_user_model):
        """测试用户不存在"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        user_data = AuthService.get_user_by_id('999')
        
        assert user_data is None
    
    @patch('authentication.services.User')
    def test_get_user_by_id_invalid_id(self, mock_user_model):
        """测试无效 ID"""
        mock_user_model.objects.get.side_effect = ValueError("Invalid ID")
        
        user_data = AuthService.get_user_by_id('invalid')
        
        assert user_data is None


class TestAuthServiceGetUserByEmail:
    """根据邮箱获取用户测试"""
    
    @patch('authentication.services.User')
    def test_get_user_by_email_success(self, mock_user_model):
        """测试成功获取用户"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user_model.objects.get.return_value = mock_user
        
        user_data = AuthService.get_user_by_email('test@example.com')
        
        assert user_data is not None
        assert user_data['email'] == 'test@example.com'
    
    @patch('authentication.services.User')
    def test_get_user_by_email_not_found(self, mock_user_model):
        """测试用户不存在"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        user_data = AuthService.get_user_by_email('nonexistent@example.com')
        
        assert user_data is None


# ==================== Edge Cases 测试 ====================

class TestAuthServiceEdgeCases:
    """认证服务边界条件测试"""
    
    @patch('authentication.services.User')
    @patch('authentication.services.TokenService')
    def test_login_empty_username(self, mock_token_service, mock_user_model):
        """测试空用户名登录"""
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        result = AuthService.login('', 'password123')
        
        assert result['success'] is False
    
    @patch('authentication.services.User')
    @patch('authentication.services.TokenService')
    def test_login_empty_password(self, mock_token_service, mock_user_model):
        """测试空密码登录"""
        mock_user = Mock()
        mock_user.check_password.return_value = False
        mock_user_model.objects.get.return_value = mock_user
        
        result = AuthService.login('testuser', '')
        
        assert result['success'] is False
        assert result['error']['code'] == 'WRONG_PASSWORD'
    
    @patch('authentication.services.User')
    def test_register_weak_password(self, mock_user_model):
        """测试弱密码注册"""
        mock_user = Mock()
        mock_user_model.objects.create_user.return_value = mock_user
        
        # 当前实现不验证密码强度
        result = AuthService.register(
            username='newuser',
            email='new@example.com',
            password='123'  # 弱密码
        )
        
        # 应该成功（密码强度验证未实现）
        assert result['success'] is True
    
    @patch('authentication.services.User')
    def test_register_invalid_email(self, mock_user_model):
        """测试无效邮箱注册"""
        mock_user = Mock()
        mock_user_model.objects.create_user.return_value = mock_user
        
        # 当前实现不验证邮箱格式
        result = AuthService.register(
            username='newuser',
            email='invalid-email',
            password='password123'
        )
        
        # 应该成功（邮箱格式验证未实现）
        assert result['success'] is True


# ==================== TokenService Edge Cases 测试 ====================

class TestTokenServiceEdgeCases:
    """Token 服务边界条件测试"""
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_generate_tokens_null_user(self, mock_settings, mock_jwt):
        """测试 None 用户"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        
        with pytest.raises(Exception):
            TokenService.generate_tokens(None)
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_none(self, mock_settings, mock_jwt):
        """测试 None token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        mock_jwt.decode.side_effect = Exception("Invalid token")
        
        with pytest.raises(Exception):
            TokenService.verify_token(None)
    
    @patch('authentication.services.jwt')
    @patch('authentication.services.settings')
    def test_verify_token_empty_string(self, mock_settings, mock_jwt):
        """测试空字符串 token"""
        mock_settings.SECRET_KEY = 'test_secret_key'
        mock_jwt.decode.side_effect = Exception("Invalid token")
        
        with pytest.raises(Exception):
            TokenService.verify_token('')


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
