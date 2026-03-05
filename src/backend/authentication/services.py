"""
Authentication services.
"""

from datetime import datetime, timedelta, timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone as django_timezone

User = get_user_model()


class TokenService:
    """Token 服务类"""
    
    @staticmethod
    def generate_tokens(user: User) -> dict:
        """
        生成 Access Token 和 Refresh Token
        
        Args:
            user: 用户对象
        
        Returns:
            dict: 包含 access_token, refresh_token, expires_in
        """
        refresh = RefreshToken.for_user(user)
        
        return {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'expires_in': int(timedelta(hours=2).total_seconds()),
        }
    
    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> dict:
        """
        验证 Token 有效性
        
        Args:
            token: Token 字符串
            token_type: 'access' 或 'refresh'
        
        Returns:
            dict: Token payload
        
        Raises:
            Exception: Token 无效或过期
        """
        from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            if token_type == 'access':
                token_obj = AccessToken(token)
            else:
                token_obj = RefreshToken(token)
            
            # 使用 payload 属性获取 token 内容
            return dict(token_obj.payload)
        except TokenError as e:
            error_msg = str(e)
            if 'expired' in error_msg.lower() or 'exp' in error_msg.lower():
                raise Exception('Token 已过期')
            raise Exception(f'无效 Token: {str(e)}')
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        使用 Refresh Token 获取新的 Access Token
        
        Args:
            refresh_token: Refresh Token 字符串
        
        Returns:
            str: 新的 Access Token
        
        Raises:
            Exception: Refresh Token 无效或过期
        """
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        try:
            refresh = RefreshToken(refresh_token)
            return str(refresh.access_token)
        except TokenError as e:
            error_msg = str(e)
            if 'expired' in error_msg.lower() or 'exp' in error_msg.lower():
                raise Exception('Refresh Token 已过期')
            raise Exception(f'无效 Refresh Token: {str(e)}')


class AuthService:
    """认证服务类"""
    
    @staticmethod
    def register_user(username: str, email: str, password: str) -> User:
        """
        注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
        
        Returns:
            User: 创建的用户对象
        
        Raises:
            ValidationError: 验证失败
        """
        from users.models import UserProfile, UserStats
        
        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'username': '该用户名已被使用'}, code='USERNAME_EXISTS')
        
        # 检查邮箱是否已存在
        if User.objects.filter(email=email).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'email': '该邮箱已被注册'}, code='EMAIL_EXISTS')
        
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # 自动创建用户档案和统计
        UserProfile.objects.create(user=user)
        UserStats.objects.create(user=user)
        
        return user
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> User:
        """
        验证用户凭证
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            User: 认证通过的用户对象
        
        Raises:
            Exception: 认证失败
        """
        from django.contrib.auth import authenticate
        
        user = authenticate(username=username, password=password)
        
        if not user:
            raise Exception('INVALID_CREDENTIALS:用户名或密码错误')
        
        if not user.is_active:
            raise Exception('USER_INACTIVE:账号已被禁用')
        
        if user.status == 'banned':
            raise Exception('USER_BANNED:账号已被封禁')
        
        return user
    
    @staticmethod
    def update_last_login(user: User) -> None:
        """
        更新用户最后登录时间
        
        Args:
            user: 用户对象
        """
        user.last_login_at = django_timezone.now()
        user.save(update_fields=['last_login_at'])
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        """
        修改用户密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
        
        Raises:
            Exception: 密码验证失败
        """
        if not user.check_password(old_password):
            raise Exception('WRONG_OLD_PASSWORD:旧密码错误')
        
        if old_password == new_password:
            raise Exception('SAME_PASSWORD:新密码不能与旧密码相同')
        
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
