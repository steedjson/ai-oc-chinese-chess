"""
游戏状态枚举
"""
from django.db import models


class GameStatus(models.TextChoices):
    """游戏状态枚举"""
    PENDING = 'pending', '等待开始'
    PLAYING = 'playing', '进行中'
    RED_WIN = 'red_win', '红方胜'
    BLACK_WIN = 'black_win', '黑方胜'
    DRAW = 'draw', '和棋'
    ABORTED = 'aborted', '已取消'
