"""
游戏计时器服务

实现中国象棋对局的计时功能：
- 开局初始化计时器
- 走棋时更新剩余时间
- 实时推送剩余时间给前端
- 超时判定和处理
"""
import logging
from typing import Optional, Tuple
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async

from .models import Game

logger = logging.getLogger(__name__)


class TimerService:
    """
    游戏计时器服务
    
    功能：
    - 初始化对局计时器
    - 更新剩余时间
    - 检查超时
    - 推送时间更新
    """
    
    @staticmethod
    def init_timer(game: Game, base_time: int = 7200) -> None:
        """
        初始化对局计时器
        
        Args:
            game: 游戏对局
            base_time: 基础时间（秒），默认 7200 秒（2 小时）
        """
        game.red_time_remaining = base_time
        game.black_time_remaining = base_time
        game.timeout_seconds = base_time
        game.last_move_time = timezone.now()
        game.save(update_fields=[
            'red_time_remaining',
            'black_time_remaining',
            'timeout_seconds',
            'last_move_time',
            'updated_at'
        ])
        logger.info(f"Game {game.id}: 计时器初始化，基础时间 {base_time}秒")
    
    @staticmethod
    def update_timer(game: Game, player_color: str) -> Tuple[int, bool]:
        """
        更新计时器（走棋时调用）
        
        计算从上次走棋到现在经过的时间，从当前玩家剩余时间中扣除
        
        Args:
            game: 游戏对局
            player_color: 当前玩家颜色 ('red' 或 'black')
            
        Returns:
            (剩余时间，是否超时)
        """
        now = timezone.now()
        last_time = game.last_move_time or game.created_at
        
        # 计算经过的时间（秒）
        elapsed = (now - last_time).total_seconds()
        elapsed = int(elapsed)
        
        # 更新剩余时间
        if player_color == 'red':
            game.red_time_remaining = max(0, game.red_time_remaining - elapsed)
            is_timeout = game.red_time_remaining <= 0
        else:
            game.black_time_remaining = max(0, game.black_time_remaining - elapsed)
            is_timeout = game.black_time_remaining <= 0
        
        # 更新时间戳
        game.last_move_time = now
        game.save(update_fields=[
            'red_time_remaining' if player_color == 'red' else 'black_time_remaining',
            'last_move_time',
            'updated_at'
        ])
        
        logger.info(
            f"Game {game.id}: {player_color}方走棋，耗时{elapsed}秒，"
            f"剩余{game.red_time_remaining if player_color == 'red' else game.black_time_remaining}秒"
        )
        
        return (
            game.red_time_remaining if player_color == 'red' else game.black_time_remaining,
            is_timeout
        )
    
    @staticmethod
    def get_remaining_time(game: Game, player_color: str) -> int:
        """
        获取玩家当前剩余时间（实时计算，包含从上次走棋到现在的时间）
        
        Args:
            game: 游戏对局
            player_color: 玩家颜色 ('red' 或 'black')
            
        Returns:
            剩余时间（秒）
        """
        base_time = game.red_time_remaining if player_color == 'red' else game.black_time_remaining
        
        if not game.last_move_time or game.status != 'playing':
            return base_time
        
        # 计算从上次走棋到现在经过的时间
        now = timezone.now()
        elapsed = (now - game.last_move_time).total_seconds()
        
        return max(0, base_time - int(elapsed))
    
    @staticmethod
    def check_timeout(game: Game, player_color: str) -> bool:
        """
        检查玩家是否超时
        
        Args:
            game: 游戏对局
            player_color: 玩家颜色
            
        Returns:
            是否超时
        """
        remaining = TimerService.get_remaining_time(game, player_color)
        return remaining <= 0
    
    @staticmethod
    async def async_update_timer(game: Game, player_color: str) -> Tuple[int, bool]:
        """
        异步版本：更新计时器
        
        Args:
            game: 游戏对局
            player_color: 当前玩家颜色
            
        Returns:
            (剩余时间，是否超时)
        """
        return await sync_to_async(TimerService.update_timer)(game, player_color)
    
    @staticmethod
    async def async_check_timeout(game: Game, player_color: str) -> bool:
        """
        异步版本：检查超时
        
        Args:
            game: 游戏对局
            player_color: 玩家颜色
            
        Returns:
            是否超时
        """
        return await sync_to_async(TimerService.check_timeout)(game, player_color)
    
    @staticmethod
    def handle_timeout(game: Game, timeout_player: str) -> None:
        """
        处理超时情况
        
        Args:
            game: 游戏对局
            timeout_player: 超时玩家颜色 ('red' 或 'black')
        """
        # 超时玩家判负，对方获胜
        winner = 'black' if timeout_player == 'red' else 'red'
        
        game.status = 'finished'
        game.winner = winner
        game.win_reason = 'timeout'
        game.save(update_fields=['status', 'winner', 'win_reason', 'updated_at'])
        
        logger.info(f"Game {game.id}: {timeout_player}方超时，{winner}方获胜")


# 全局单例
_timer_service = TimerService()


def get_timer_service() -> TimerService:
    """获取计时器服务单例"""
    return _timer_service
