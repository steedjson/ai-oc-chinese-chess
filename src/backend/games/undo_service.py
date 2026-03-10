"""
悔棋服务

实现悔棋功能的核心逻辑：
- 检查悔棋次数限制
- 创建悔棋请求
- 处理悔棋响应
- 执行悔棋操作
- 通知对手
"""
import logging
from typing import Optional, Tuple, Dict, Any
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from games.models import Game, GameMove, UndoRequest
from games.fen_service import FenService
from games.engine import Board

logger = logging.getLogger(__name__)


class UndoService:
    """悔棋服务类"""
    
    # 悔棋确认超时时间（5 分钟）
    UNDO_TIMEOUT_MINUTES = 5
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def can_request_undo(self, game: Game, player) -> Tuple[bool, str]:
        """
        检查是否可以请求悔棋
        
        Args:
            game: 游戏对局
            player: 请求玩家
            
        Returns:
            (是否可以，原因)
        """
        # 检查游戏状态
        if game.status != 'playing':
            return False, "游戏未进行中"
        
        # 检查是否是玩家的回合
        current_side = 'red' if game.current_player == 'red' else 'black'
        player_side = self._get_player_side(game, player)
        
        if player_side != current_side:
            return False, "不是你的回合"
        
        # 检查悔棋次数
        undo_count = game.undo_count_red if player_side == 'red' else game.undo_count_black
        if undo_count >= game.undo_limit:
            return False, f"悔棋次数已达上限（{game.undo_limit}次）"
        
        # 检查是否有可悔的棋
        last_move = self._get_last_move_by_player(game, player)
        if not last_move:
            return False, "没有可悔的棋"
        
        return True, "可以悔棋"
    
    def request_undo(
        self,
        game: Game,
        player,
        undo_count: int = 1,
        reason: str = ''
    ) -> Optional[UndoRequest]:
        """
        请求悔棋
        
        Args:
            game: 游戏对局
            player: 请求玩家
            undo_count: 悔棋步数（默认 1）
            reason: 悔棋原因
            
        Returns:
            UndoRequest 或 None
        """
        # 检查是否可以悔棋
        can_undo, msg = self.can_request_undo(game, player)
        if not can_undo:
            logger.warning(f"悔棋请求被拒绝：{msg}")
            return None
        
        # 获取要撤销的走棋
        move_to_undo = self._get_last_move_by_player(game, player)
        if not move_to_undo:
            return None
        
        # 创建悔棋请求
        auto_accept_at = timezone.now() + timedelta(minutes=self.UNDO_TIMEOUT_MINUTES)
        
        undo_request = UndoRequest.objects.create(
            game=game,
            requester=player,
            move_to_undo=move_to_undo,
            undo_count=min(undo_count, 3),  # 最多一次悔 3 步
            reason=reason,
            auto_accept_at=auto_accept_at
        )
        
        logger.info(f"创建悔棋请求：#{undo_request.id} - Game {game.id}")
        
        # 通知对手
        self._notify_opponent(game, player, undo_request)
        
        return undo_request
    
    def respond_to_undo(
        self,
        undo_request: UndoRequest,
        responder,
        accept: bool
    ) -> bool:
        """
        响应悔棋请求
        
        Args:
            undo_request: 悔棋请求
            responder: 响应玩家
            accept: 是否接受
            
        Returns:
            是否成功
        """
        # 检查权限（只有对手可以响应）
        if responder == undo_request.requester:
            logger.warning("玩家不能响应自己的悔棋请求")
            return False
        
        # 检查请求状态
        if undo_request.status != 'pending':
            logger.warning(f"悔棋请求状态不正确：{undo_request.status}")
            return False
        
        # 更新请求状态
        undo_request.status = 'accepted' if accept else 'rejected'
        undo_request.responded_by = responder
        undo_request.responded_at = timezone.now()
        undo_request.save()
        
        logger.info(f"悔棋请求被{'接受' if accept else '拒绝'}: #{undo_request.id}")
        
        # 如果接受，执行悔棋
        if accept:
            success = self._execute_undo(undo_request)
            if not success:
                logger.error(f"执行悔棋失败：#{undo_request.id}")
                return False
        
        # 通知双方
        self._notify_response(undo_request, accept)
        
        return True
    
    def auto_accept_pending(self):
        """自动接受超时的悔棋请求"""
        from django.utils import timezone
        
        pending_requests = UndoRequest.objects.filter(
            status='pending',
            auto_accept_at__lte=timezone.now()
        )
        
        for undo_request in pending_requests:
            logger.info(f"自动接受超时悔棋请求：#{undo_request.id}")
            self.respond_to_undo(undo_request, None, True)
        
        return pending_requests.count()
    
    def _get_player_side(self, game: Game, player) -> Optional[str]:
        """获取玩家在哪一方"""
        if game.player_red == player:
            return 'red'
        elif game.player_black == player:
            return 'black'
        return None
    
    def _get_last_move_by_player(self, game: Game, player) -> Optional[GameMove]:
        """获取玩家最后一步棋"""
        last_move = GameMove.objects.filter(
            game=game,
            player=player
        ).order_by('-move_number').first()
        
        return last_move
    
    def _execute_undo(self, undo_request: UndoRequest) -> bool:
        """
        执行悔棋
        
        Args:
            undo_request: 悔棋请求
            
        Returns:
            是否成功
        """
        try:
            game = undo_request.game
            player_side = 'red' if game.player_red == undo_request.requester else 'black'
            
            # 更新悔棋次数
            if player_side == 'red':
                game.undo_count_red += 1
            else:
                game.undo_count_black += 1
            
            # 回退 FEN 状态
            board = Board(game.fen_current)
            
            # 撤销指定步数
            undo_count = undo_request.undo_count
            moves_to_undo = GameMove.objects.filter(
                game=game,
                move_number__gt=(undo_request.move_to_undo.move_number - undo_count)
            ).order_by('-move_number')
            
            # 恢复到最后一步之前的状态
            target_move = moves_to_undo.last()
            if target_move:
                # 获取目标局面的 FEN
                prev_fen = target_move.fen_before
                game.fen_current = prev_fen
                
                # 解析 FEN 获取当前回合
                fen_data = FenService.parse_fen(prev_fen)
                game.current_player = 'red' if fen_data['turn'] == 'w' else 'black'
            
            # 删除悔棋之后的走棋记录
            moves_to_undo.delete()
            
            # 更新走棋次数
            game.move_count = GameMove.objects.filter(game=game).count()
            
            game.save()
            
            logger.info(f"执行悔棋成功：Game {game.id}, 撤销{undo_count}步")
            return True
            
        except Exception as e:
            logger.error(f"执行悔棋失败：{e}", exc_info=True)
            return False
    
    def _notify_opponent(self, game: Game, requester, undo_request: UndoRequest):
        """通知对手有悔棋请求"""
        opponent = game.player_black if requester == game.player_red else game.player_red
        
        if opponent:
            message = {
                'type': 'undo_request',
                'data': {
                    'request_id': undo_request.id,
                    'requester': requester.username,
                    'move_number': undo_request.move_to_undo.move_number,
                    'undo_count': undo_request.undo_count,
                    'reason': undo_request.reason,
                    'timeout_minutes': self.UNDO_TIMEOUT_MINUTES
                }
            }
            
            try:
                async_to_sync(self.channel_layer.group_send)(
                    f'game_{game.id}',
                    message
                )
            except Exception as e:
                logger.error(f"发送悔棋通知失败：{e}")
    
    def _notify_response(self, undo_request: UndoRequest, accepted: bool):
        """通知双方悔棋响应结果"""
        message = {
            'type': 'undo_response',
            'data': {
                'request_id': undo_request.id,
                'accepted': accepted,
                'status': undo_request.get_status_display()
            }
        }
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'game_{undo_request.game.id}',
                message
            )
        except Exception as e:
            logger.error(f"发送悔棋响应通知失败：{e}")


# 全局单例
_undo_service = None

def get_undo_service() -> UndoService:
    """获取悔棋服务单例"""
    global _undo_service
    if _undo_service is None:
        _undo_service = UndoService()
    return _undo_service
