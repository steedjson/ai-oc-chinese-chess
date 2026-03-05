"""
游戏对局 Django 模型

包含：
- Game: 游戏对局模型
- GameMove: 走棋记录模型
"""
import uuid
from django.db import models
from django.conf import settings


class GameStatus(models.TextChoices):
    """游戏状态枚举"""
    PENDING = 'pending', '等待开始'
    PLAYING = 'playing', '进行中'
    RED_WIN = 'red_win', '红方胜'
    BLACK_WIN = 'black_win', '黑方胜'
    DRAW = 'draw', '和棋'
    ABORTED = 'aborted', '已取消'


class Game(models.Model):
    """
    游戏对局模型
    
    存储对局信息、状态、结果等
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 对局信息
    game_type = models.CharField(
        max_length=20,
        choices=[
            ('single', '单机'),
            ('online', '联网'),
            ('friend', '好友'),
        ],
        default='single'
    )
    status = models.CharField(
        max_length=20,
        choices=GameStatus.choices,
        default=GameStatus.PENDING
    )
    
    # 玩家信息
    red_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='red_games',
        null=True,
        blank=True
    )
    black_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='black_games',
        null=True,
        blank=True
    )
    
    # 游戏状态
    fen_start = models.TextField()
    fen_current = models.TextField()
    turn = models.CharField(max_length=5, default='w')  # 'w' 红方，'b' 黑方
    
    # 结果信息
    winner = models.CharField(
        max_length=10,
        choices=[
            ('red', '红方'),
            ('black', '黑方'),
            ('draw', '和棋'),
        ],
        null=True,
        blank=True
    )
    win_reason = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='获胜原因：checkmate, resign, timeout, agreement'
    )
    
    # 时间控制
    time_control_base = models.IntegerField(default=600)  # 基础时间（秒）
    time_control_increment = models.IntegerField(default=0)  # 每步加时（秒）
    red_time_remaining = models.IntegerField(default=600)
    black_time_remaining = models.IntegerField(default=600)
    
    # AI 配置（单机模式）
    ai_level = models.IntegerField(null=True, blank=True)
    ai_side = models.CharField(max_length=5, null=True, blank=True)
    
    # 统计信息
    move_count = models.IntegerField(default=0)
    duration = models.IntegerField(null=True, blank=True)  # 对局时长（秒）
    
    # 评级信息
    is_rated = models.BooleanField(default=True)
    
    # 时间戳
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'games'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['red_player', 'status']),
            models.Index(fields=['black_player', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Game {self.id} - {self.status}"


class GameMove(models.Model):
    """
    走棋记录模型
    
    存储每步走棋的详细信息
    """
    id = models.BigAutoField(primary_key=True)
    
    # 外键
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='moves'
    )
    
    # 走棋信息
    move_number = models.IntegerField()  # 第几步
    piece = models.CharField(max_length=1)  # 棋子类型
    from_pos = models.CharField(max_length=3)  # 起始位置
    to_pos = models.CharField(max_length=3)  # 目标位置
    captured = models.CharField(max_length=1, null=True, blank=True)  # 被吃棋子
    is_check = models.BooleanField(default=False)  # 是否将军
    is_capture = models.BooleanField(default=False)  # 是否吃子
    
    # 走棋描述
    notation = models.CharField(max_length=10, null=True, blank=True)  # 中文记谱
    san = models.CharField(max_length=10, null=True, blank=True)  # 标准代数记谱
    
    # FEN 快照
    fen_after = models.TextField()
    
    # 时间信息
    time_remaining = models.IntegerField(null=True, blank=True)  # 走棋后剩余时间
    time_used = models.IntegerField(null=True, blank=True)  # 本步用时
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'game_moves'
        ordering = ['move_number']
        unique_together = ['game', 'move_number']
        indexes = [
            models.Index(fields=['game', 'move_number']),
            models.Index(fields=['piece']),
        ]
    
    def __str__(self):
        return f"Move {self.move_number}: {self.piece} {self.from_pos}-{self.to_pos}"
