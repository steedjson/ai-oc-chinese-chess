"""
Serializers for user data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import UserProfile, UserStats

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户数据序列化器"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar_url', 'elo_rating', 'status', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'elo_rating', 'status', 'is_verified', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate_username(self, value):
        """验证用户名"""
        if len(value) < 3:
            raise serializers.ValidationError('用户名至少 3 个字符')
        if len(value) > 50:
            raise serializers.ValidationError('用户名不能超过 50 个字符')
        return value
    
    def validate_email(self, value):
        """验证邮箱"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被注册')
        return value
    
    def validate_username_unique(self, value):
        """验证用户名唯一性"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('该用户名已被使用')
        return value
    
    def validate(self, attrs):
        """验证密码匹配"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '两次输入的密码不一致'
            })
        return attrs
    
    def create(self, validated_data):
        """创建用户"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # 自动创建用户档案和统计
        UserProfile.objects.create(user=user)
        UserStats.objects.create(user=user)
        
        return user


class LoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """验证用户凭证"""
        from django.contrib.auth import authenticate
        
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError('用户名和密码不能为空')
        
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        
        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')
        
        if user.status == 'banned':
            raise serializers.ValidationError('账号已被封禁')
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """验证旧密码"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('旧密码错误')
        return value
    
    def validate(self, attrs):
        """验证新密码匹配"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '两次输入的新密码不一致'
            })
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': '新密码不能与旧密码相同'
            })
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """用户档案序列化器"""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birthday', 'gender']


class UserStatsSerializer(serializers.ModelSerializer):
    """用户统计序列化器"""
    
    class Meta:
        model = UserStats
        fields = ['total_games', 'wins', 'losses', 'draws', 'win_rate', 'favorite_opening']


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详细信息序列化器（包含档案和统计）"""
    
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    stats = UserStatsSerializer(source='userstats', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar_url', 'elo_rating', 'status', 'is_verified',
            'profile', 'stats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'elo_rating', 'status', 'is_verified', 'created_at', 'updated_at']
