"""
游戏走棋记录模型
"""
from django.db import models
from django.conf import settings


class GameMove(models.Model):
    """
    游戏走棋记录
    记录每一步走棋的详细信息
    """
    
    # 关联的游戏
    game = models.ForeignKey(
        'Game',
        on_delete=models.CASCADE,
        related_name='moves',
        verbose_name='游戏对局'
    )
    
    # 走棋信息
    move_number = models.IntegerField(
        default=1,
        verbose_name='第几步'
    )
    
    # 走棋玩家
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_moves',
        verbose_name='走棋玩家'
    )
    
    # 走棋颜色
    color = models.CharField(
        max_length=10,
        choices=[('red', '红方'), ('black', '黑方')],
        default='red',
        verbose_name='颜色'
    )
    
    # 走棋坐标
    from_x = models.IntegerField(null=True, blank=True, verbose_name='起始 x 坐标')
    from_y = models.IntegerField(null=True, blank=True, verbose_name='起始 y 坐标')
    to_x = models.IntegerField(null=True, blank=True, verbose_name='目标 x 坐标')
    to_y = models.IntegerField(null=True, blank=True, verbose_name='目标 y 坐标')
    
    # 棋子类型
    piece_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='棋子类型'
    )
    
    # 走棋时间
    move_time = models.DateTimeField(auto_now_add=True, verbose_name='走棋时间')
    
    # 走棋用时（秒）
    time_taken = models.FloatField(
        null=True,
        blank=True,
        verbose_name='走棋用时（秒）'
    )
    
    # FEN 状态（走棋后）
    fen_after = models.TextField(
        null=True,
        blank=True,
        verbose_name='走棋后棋盘状态'
    )
    
    # 是否是吃子
    is_capture = models.BooleanField(
        default=False,
        verbose_name='是否吃子'
    )
    
    # 是否是将军
    is_check = models.BooleanField(
        default=False,
        verbose_name='是否将军'
    )
    
    # 备注
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='备注'
    )
    
    class Meta:
        verbose_name = '走棋记录'
        verbose_name_plural = '走棋记录'
        ordering = ['move_number']
        indexes = [
            models.Index(fields=['game', 'move_number']),
            models.Index(fields=['player']),
        ]
    
    def __str__(self):
        return f"Move {self.move_number} - {self.color} {self.piece_type}"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'move_number': self.move_number,
            'player': self.player.username,
            'color': self.color,
            'from': (self.from_x, self.from_y),
            'to': (self.to_x, self.to_y),
            'piece_type': self.piece_type,
            'move_time': self.move_time.isoformat(),
            'time_taken': self.time_taken,
            'fen_after': self.fen_after,
            'is_capture': self.is_capture,
            'is_check': self.is_check,
        }
