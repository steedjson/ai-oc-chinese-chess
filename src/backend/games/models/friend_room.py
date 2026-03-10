"""
好友对战房间模型

实现好友对战房间的管理功能：
- 房间号生成
- 房间状态管理
- 过期清理
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string


class FriendRoom(models.Model):
    """
    好友对战房间
    
    用于管理好友对战的创建、加入和状态
    """
    
    # 房间状态
    STATUS_CHOICES = [
        ('waiting', '等待中'),
        ('playing', '对局中'),
        ('finished', '已结束'),
        ('expired', '已过期'),
    ]
    
    # 基本信息
    id = models.AutoField(primary_key=True)
    room_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='房间号'
    )
    game = models.OneToOneField(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='friend_room',
        verbose_name='关联游戏'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_friend_rooms',
        verbose_name='创建者'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        verbose_name='房间状态'
    )
    
    # 时间信息
    expires_at = models.DateTimeField(
        verbose_name='过期时间'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始时间'
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束时间'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        verbose_name = '好友对战房间'
        verbose_name_plural = '好友对战房间'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room_code']),
            models.Index(fields=['status']),
            models.Index(fields=['creator']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Room {self.room_code} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        """保存时生成房间号（如果是新建）"""
        if not self.room_code:
            self.room_code = self._generate_room_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def _generate_room_code(self) -> str:
        """
        生成房间号
        
        格式：CHESS + 5 位随机字母数字
        例如：CHESS2A3B5
        """
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=5))
        return f'CHESS{random_part}'
    
    def start_game(self):
        """开始游戏"""
        self.status = 'playing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])
    
    def finish_game(self):
        """结束游戏"""
        self.status = 'finished'
        self.finished_at = timezone.now()
        self.save(update_fields=['status', 'finished_at', 'updated_at'])
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return timezone.now() > self.expires_at
    
    def is_joinable(self) -> bool:
        """检查是否可加入"""
        return self.status == 'waiting' and not self.is_expired()
    
    def get_invite_link(self, request=None) -> str:
        """
        获取邀请链接
        
        Args:
            request: Django request 对象（可选）
            
        Returns:
            邀请链接 URL
        """
        if request:
            return request.build_absolute_uri(f'/games/friend/join/{self.room_code}/')
        else:
            # 如果没有 request，返回相对路径
            return f'/games/friend/join/{self.room_code}/'
    
    @classmethod
    def cleanup_expired_rooms(cls) -> int:
        """
        清理过期房间
        
        Returns:
            清理的房间数量
        """
        expired_rooms = cls.objects.filter(
            status='waiting',
            expires_at__lt=timezone.now()
        )
        count = expired_rooms.count()
        expired_rooms.update(status='expired')
        return count
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'room_code': self.room_code,
            'status': self.status,
            'creator': self.creator.username if self.creator else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'game_id': self.game.id if self.game else None,
            'invite_link': self.get_invite_link(),
        }


# 信号处理
from django.db.models.signals import pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=FriendRoom)
def cleanup_friend_room(sender, instance, **kwargs):
    """删除房间时清理关联游戏（如果是等待状态）"""
    if instance.status == 'waiting' and instance.game:
        instance.game.delete()
