"""
User models for the Chinese Chess application.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserStatus(models.TextChoices):
    """用户状态枚举"""
    ACTIVE = 'active', '活跃'
    INACTIVE = 'inactive', '不活跃'
    BANNED = 'banned', '已封禁'


class UserManager(BaseUserManager):
    """自定义用户管理器"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """创建普通用户"""
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    用户模型
    
    包含用户认证、Elo 评分、状态等核心字段
    """
    
    # 基本信息
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)  # 兼容字段，实际使用 Django 的 password 字段
    
    # 个人资料
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    avatar_url = models.CharField(max_length=512, blank=True, null=True)
    
    # 游戏数据
    elo_rating = models.IntegerField(default=1500)
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE
    )
    
    # 账号状态
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # 时间戳
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # 使用自定义管理器
    objects = UserManager()
    
    # Django 认证所需
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='idx_users_email', condition=models.Q(deleted_at__isnull=True)),
            models.Index(fields=['username'], name='idx_users_username', condition=models.Q(deleted_at__isnull=True)),
            models.Index(fields=['-elo_rating'], name='idx_users_elo'),
            models.Index(fields=['status'], name='idx_users_status'),
        ]
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """保存时更新 updated_at"""
        if self._state.adding:
            # 新创建用户时同步 password_hash 字段
            self.password_hash = self.password
        else:
            # 更新时如果密码变化，同步 password_hash
            if hasattr(self, '_password_changed') and self._password_changed:
                self.password_hash = self.password
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """设置密码时标记密码已变化"""
        self._password_changed = True
        super().set_password(raw_password)
    
    def get_full_name(self):
        """获取全名"""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username
    
    def get_short_name(self):
        """获取短名"""
        return self.first_name or self.username
    
    def is_banned(self):
        """检查用户是否被封禁"""
        return self.status == UserStatus.BANNED


class UserProfile(models.Model):
    """
    用户档案模型
    
    存储用户的额外个人信息
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    bio = models.TextField(blank=True, null=True, help_text='个人简介')
    location = models.CharField(max_length=100, blank=True, null=True, help_text='所在地')
    birthday = models.DateField(blank=True, null=True, help_text='生日')
    gender = models.CharField(max_length=20, blank=True, null=True, help_text='性别')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id'], name='idx_user_profiles_user_id'),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class UserStats(models.Model):
    """
    用户统计模型
    
    存储用户的游戏统计数据
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userstats')
    total_games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    favorite_opening = models.CharField(max_length=100, blank=True, null=True, help_text='常用开局')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_stats'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id'], name='idx_user_stats_user_id'),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s stats"
    
    def save(self, *args, **kwargs):
        """保存时自动计算胜率"""
        if self.total_games > 0:
            self.win_rate = round((self.wins / self.total_games) * 100, 2)
        else:
            self.win_rate = 0.0
        super().save(*args, **kwargs)
