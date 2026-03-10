"""
游戏日志模型
记录所有对局操作历史，用于审计和追踪
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any


class GameLog(models.Model):
    """
    游戏对局日志
    记录所有对局相关操作，用于审计和追踪
    """
    
    # 操作类型
    ACTION_CHOICES = [
        ('create', '创建对局'),
        ('start', '开始对局'),
        ('move', '走棋'),
        ('abort', '中止对局'),
        ('auto_abort', '自动中止'),
        ('finish', '结束对局'),
        ('mark_abnormal', '标记异常'),
        ('unmark_abnormal', '取消异常标记'),
        ('join', '加入对局'),
        ('leave', '离开对局'),
        ('spectator_join', '观战者加入'),
        ('spectator_leave', '观战者离开'),
        ('chat_message', '聊天消息'),
        ('other', '其他操作'),
    ]
    
    # 严重程度
    SEVERITY_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    ]
    
    # 关联的游戏
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='游戏对局'
    )
    
    # 操作者
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='game_logs',
        verbose_name='操作者'
    )
    
    # 操作类型
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='操作类型'
    )
    
    # 操作详情（JSON 格式）
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='操作详情'
    )
    
    # 严重程度
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='info',
        verbose_name='严重程度'
    )
    
    # 操作时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    # IP 地址（用于审计）
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP 地址'
    )
    
    # 用户代理
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='用户代理'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', '-created_at']),
            models.Index(fields=['operator', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
        verbose_name = '游戏日志'
        verbose_name_plural = '游戏日志'
    
    def __str__(self):
        return f"[{self.created_at}] {self.game.id} - {self.operator} - {self.action}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'game_id': self.game.id if self.game else None,
            'operator': {
                'id': self.operator.id if self.operator else None,
                'username': self.operator.username if self.operator else 'System',
            },
            'action': self.action,
            'action_display': self.get_action_display(),
            'details': self.details,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
        }
    
    @classmethod
    def log_action(
        cls,
        game,
        action: str,
        operator=None,
        details: Dict[str, Any] = None,
        severity: str = 'info',
        request=None
    ):
        """
        记录操作日志的便捷方法
        
        Args:
            game: 游戏对局对象
            action: 操作类型
            operator: 操作者
            details: 操作详情
            severity: 严重程度
            request: HTTP 请求对象（用于获取 IP 和 UA）
        """
        log_data = {
            'game': game,
            'action': action,
            'operator': operator,
            'details': details or {},
            'severity': severity,
        }
        
        # 从请求中获取 IP 和 UA
        if request:
            log_data['ip_address'] = cls._get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """获取客户端 IP 地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class GameLogQuerySet(models.QuerySet):
    """游戏日志查询集"""
    
    def by_action(self, action: str):
        """按操作类型过滤"""
        return self.filter(action=action)
    
    def by_game(self, game):
        """按游戏过滤"""
        return self.filter(game=game)
    
    def by_operator(self, operator):
        """按操作者过滤"""
        return self.filter(operator=operator)
    
    def by_severity(self, severity: str):
        """按严重程度过滤"""
        return self.filter(severity=severity)
    
    def recent(self, hours: int = 24):
        """获取最近 N 小时的日志"""
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        return self.filter(created_at__gte=cutoff)
    
    def export_csv(self):
        """
        导出为 CSV 格式
        返回字典列表，可用于生成 CSV
        """
        return [
            {
                '时间': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                '游戏 ID': log.game.id if log.game else '',
                '操作者': log.operator.username if log.operator else 'System',
                '操作类型': log.get_action_display(),
                '严重程度': log.get_severity_display(),
                '详情': str(log.details),
                'IP 地址': log.ip_address or '',
            }
            for log in self
        ]


class GameLogManager(models.Manager):
    """游戏日志管理器"""
    
    def get_queryset(self):
        return GameLogQuerySet(self.model, using=self._db)
    
    def by_action(self, action: str):
        return self.get_queryset().by_action(action)
    
    def by_game(self, game):
        return self.get_queryset().by_game(game)
    
    def by_operator(self, operator):
        return self.get_queryset().by_operator(operator)
    
    def recent(self, hours: int = 24):
        return self.get_queryset().recent(hours)


# 更新 GameLog 模型使用自定义管理器
GameLog.add_to_class('objects', GameLogManager())
