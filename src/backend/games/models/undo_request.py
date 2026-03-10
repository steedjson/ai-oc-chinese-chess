"""
悔棋记录模型

记录每局游戏的悔棋操作，支持有限次数悔棋（每局 3 次）
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
import json


class UndoRequest(models.Model):
    """
    悔棋记录
    
    记录玩家的悔棋请求和操作
    """
    
    # 悔棋状态
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
        ('auto', '自动通过'),  # 对手未确认，超时自动通过
    ]
    
    # 基本信息
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='undo_requests',
        verbose_name='游戏对局'
    )
    
    # 请求信息
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='undo_requests',
        verbose_name='请求者'
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='请求时间'
    )
    
    # 悔棋内容
    move_to_undo = models.ForeignKey(
        'games.GameMove',
        on_delete=models.CASCADE,
        related_name='undo_requests',
        verbose_name='要撤销的走棋',
        null=True,
        blank=True
    )
    undo_count = models.IntegerField(
        default=1,
        verbose_name='悔棋步数'
    )
    
    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='undo_responses',
        verbose_name='响应者'
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='响应时间'
    )
    
    # 自动过期
    auto_accept_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='自动接受时间'
    )
    
    # 备注
    reason = models.TextField(
        blank=True,
        default='',
        verbose_name='悔棋原因'
    )
    
    class Meta:
        db_table = 'games_undo_request'
        verbose_name = '悔棋记录'
        verbose_name_plural = '悔棋记录'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"UndoRequest #{self.id} - Game {self.game.id} - {self.status}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'game_id': self.game.id,
            'requester_id': self.requester.id,
            'requester_username': self.requester.username,
            'requested_at': self.requested_at.isoformat(),
            'move_to_undo_id': self.move_to_undo.id if self.move_to_undo else None,
            'undo_count': self.undo_count,
            'status': self.status,
            'responded_by_id': self.responded_by.id if self.responded_by else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'reason': self.reason,
            'auto_accept_at': self.auto_accept_at.isoformat() if self.auto_accept_at else None,
        }
