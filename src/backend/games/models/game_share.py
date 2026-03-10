"""
棋局分享模型

实现棋局分享功能：
- 生成分享链接
- 生成分享二维码
- 分享统计
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import hashlib


class GameShare(models.Model):
    """
    棋局分享记录
    
    每个分享链接对应一个唯一的 share_token
    """
    
    # 分享类型
    SHARE_TYPE_CHOICES = [
        ('public', '公开分享'),
        ('private', '私密分享'),  # 需要密码
        ('link', '链接分享'),  # 仅链接可访问
    ]
    
    # 基本信息
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name='游戏对局'
    )
    
    # 分享者
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_shares',
        verbose_name='分享者'
    )
    
    # 分享标识
    share_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='分享令牌'
    )
    
    # 分享配置
    share_type = models.CharField(
        max_length=20,
        choices=SHARE_TYPE_CHOICES,
        default='public',
        verbose_name='分享类型'
    )
    
    share_password = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='分享密码'
    )
    
    # 分享控制
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否有效'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='过期时间'
    )
    
    # 分享统计
    view_count = models.IntegerField(
        default=0,
        verbose_name='浏览次数'
    )
    
    # 时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 备注
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='分享说明'
    )
    
    class Meta:
        db_table = 'games_share'
        verbose_name = '棋局分享'
        verbose_name_plural = '棋局分享'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Share #{self.id} - Game {self.game.id} - {self.share_type}"
    
    def save(self, *args, **kwargs):
        """保存时生成 share_token"""
        if not self.share_token:
            self.share_token = self._generate_share_token()
        super().save(*args, **kwargs)
    
    def _generate_share_token(self) -> str:
        """生成唯一分享令牌"""
        unique_id = f"{self.game.id}-{self.shared_by.id}-{timezone.now().isoformat()}-{uuid.uuid4()}"
        return hashlib.sha256(unique_id.encode()).hexdigest()[:32]
    
    def get_share_url(self, request=None) -> str:
        """获取分享链接"""
        base_url = request.build_absolute_uri('/') if request else 'http://localhost:3000/'
        return f"{base_url}share/{self.share_token}/"
    
    def get_qr_code_data(self) -> str:
        """获取二维码数据（URL）"""
        return self.get_share_url()
    
    def increment_view_count(self):
        """增加浏览次数"""
        self.view_count += 1
        self.save(update_fields=['view_count', 'updated_at'])
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'game_id': self.game.id,
            'shared_by_id': self.shared_by.id,
            'shared_by_username': self.shared_by.username,
            'share_token': self.share_token,
            'share_type': self.share_type,
            'has_password': bool(self.share_password),
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat(),
            'description': self.description,
            'share_url': self.get_share_url(),
        }
