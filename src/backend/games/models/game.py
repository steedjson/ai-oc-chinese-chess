"""
游戏对局模型
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any


class Game(models.Model):
    """
    游戏对局
    记录一局完整的象棋对局
    """
    
    # 对局状态
    STATUS_CHOICES = [
        ('waiting', '等待中'),
        ('playing', '对局中'),
        ('finished', '已结束'),
        ('aborted', '已中止'),
    ]
    
    # 对局类型
    TYPE_CHOICES = [
        ('ai', 'AI 对战'),
        ('match', '匹配对战'),
        ('friend', '好友对战'),
        ('custom', '自定义对局'),
    ]
    
    # 基本信息
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 对局信息
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        verbose_name='对局状态'
    )
    game_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='ai',
        verbose_name='对局类型'
    )
    
    # 玩家信息（映射到数据库字段）
    player_red = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_red',
        null=True,
        blank=True,
        verbose_name='红方玩家',
        db_column='red_player_id'
    )
    player_black = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_black',
        null=True,
        blank=True,
        verbose_name='黑方玩家',
        db_column='black_player_id'
    )
    
    # 当前回合（映射到数据库字段）
    current_player = models.CharField(
        max_length=10,
        choices=[('red', '红方'), ('black', '黑方')],
        default='red',
        verbose_name='当前回合',
        db_column='turn'
    )
    
    # 棋盘状态（FEN 格式，映射到数据库字段）
    fen_start = models.TextField(
        default='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
        verbose_name='初始棋盘状态',
        db_column='fen_start',
        null=True,
        blank=True
    )
    fen_current = models.TextField(
        default='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1',
        verbose_name='当前棋盘状态',
        db_column='fen_current'
    )
    
    # 胜负信息
    winner = models.CharField(
        max_length=10,
        choices=[('red', '红方'), ('black', '黑方'), ('draw', '和棋')],
        null=True,
        blank=True,
        verbose_name='获胜方'
    )
    win_reason = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='获胜原因'
    )
    
    # 走棋次数（映射到数据库字段）
    move_count = models.IntegerField(
        default=0,
        verbose_name='走棋次数',
        db_column='move_count'
    )
    
    # 是否计分
    is_rated = models.BooleanField(
        default=False,
        verbose_name='是否计分'
    )
    
    # 超时信息
    timeout_seconds = models.IntegerField(
        default=7200,  # 2 小时
        verbose_name='超时时间（秒）',
        db_column='time_control_base'
    )
    
    # 计时器信息（秒）
    red_time_remaining = models.IntegerField(
        default=7200,
        verbose_name='红方剩余时间（秒）',
        db_column='red_time_remaining'
    )
    black_time_remaining = models.IntegerField(
        default=7200,
        verbose_name='黑方剩余时间（秒）',
        db_column='black_time_remaining'
    )
    last_move_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后走棋时间',
        db_column='last_move_time'
    )
    
    class Meta:
        verbose_name = '游戏对局'
        verbose_name_plural = '游戏对局'
        db_table = 'games'  # 指定实际表名
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['player_red']),
            models.Index(fields=['player_black']),
        ]
    
    def __str__(self):
        return f"Game {self.id} ({self.get_status_display()})"
    
    def get_player(self, color: str) -> Optional[settings.AUTH_USER_MODEL]:
        """获取指定颜色的玩家"""
        if color == 'red':
            return self.player_red
        elif color == 'black':
            return self.player_black
        return None
    
    def update_fen(self, fen: str):
        """更新棋盘状态"""
        self.fen_current = fen
        self.save(update_fields=['fen_current', 'updated_at'])
    
    def add_move(self, move: Dict[str, Any]):
        """添加走棋记录（实际存储在 GameMove 模型中）"""
        # move_count 在数据库中已存在，通过 GameMove 信号自动更新
        pass
    
    def mark_finished(self, winner: str, reason: str = ''):
        """标记对局结束"""
        self.status = 'finished'
        self.winner = winner
        self.win_reason = reason
        self.save(update_fields=['status', 'winner', 'win_reason', 'updated_at'])
    

    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'status': self.status,
            'game_type': self.game_type,
            'player_red': self.player_red.username if self.player_red else None,
            'player_black': self.player_black.username if self.player_black else None,
            'current_player': self.current_player,
            'fen_current': self.fen_current,
            'fen_start': self.fen_start,
            'move_count': self.move_count,
            'winner': self.winner,
            'win_reason': self.win_reason,
            'red_time_remaining': self.red_time_remaining,
            'black_time_remaining': self.black_time_remaining,
            'last_move_time': self.last_move_time.isoformat() if self.last_move_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
