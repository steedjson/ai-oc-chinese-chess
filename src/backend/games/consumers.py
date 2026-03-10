"""
游戏 WebSocket Consumer

实现游戏房间的实时对战功能：
- 连接认证（JWT Token 验证）
- 加入/离开房间
- 走棋消息处理
- 游戏状态广播
- 游戏结束通知
- 心跳机制
- 断线重连处理（指数退避）
- 异步消息队列处理
"""
import json
import logging
import asyncio
from typing import Dict, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime

from .engine import Board, Move
from .models import Game, GameMove
from .fen_service import FenService
from .timer_service import get_timer_service
from .websocket_reconnect import get_reconnect_service, ReconnectState
from authentication.services import TokenService
from websocket.async_handler import get_async_handler, MessagePriority

logger = logging.getLogger(__name__)


class GameConsumer(AsyncWebsocketConsumer):
    """
    游戏房间 Consumer
    
    WebSocket 路由：/ws/game/{game_id}/
    
    消息类型：
    - JOIN: 加入游戏房间
    - LEAVE: 离开游戏房间
    - MOVE: 提交走棋
    - MOVE_RESULT: 走棋结果
    - GAME_STATE: 游戏状态更新
    - GAME_OVER: 游戏结束
    - HEARTBEAT: 心跳
    - RECONNECT_STATUS: 重连状态
    - ERROR: 错误消息
    """
    
    # 心跳配置
    HEARTBEAT_INTERVAL = 30  # 30 秒
    TIMEOUT_THRESHOLD = 90  # 90 秒无心跳判定掉线
    
    def __init__(self, *args, **kwargs):
        """初始化 Consumer"""
        super().__init__(*args, **kwargs)
        self.reconnect_manager = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.async_handler = None
    
    async def connect(self):
        """建立 WebSocket 连接"""
        try:
            self.game_id = self.scope['url_route']['kwargs']['game_id']
            self.room_group_name = f'game_{self.game_id}'
            self.user = None
            self.last_heartbeat = timezone.now()
            
            # 验证用户身份
            user = await self._authenticate_connection()
            if not user:
                await self.send(text_data=json.dumps({
                    'type': 'ERROR',
                    'payload': {
                        'success': False,
                        'error': {
                            'code': 'AUTH_FAILED',
                            'message': 'Invalid or expired token'
                        }
                    },
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }))
                await self.close(code=4001)
                return
            
            self.user = user
            
            # 初始化重连管理器
            reconnect_service = await get_reconnect_service()
            self.reconnect_manager = reconnect_service.create_manager(
                self, self.game_id, str(user['id'])
            )
            
            # 初始化异步处理器
            self.async_handler = get_async_handler()
            
            # 启动心跳监测任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            # 验证用户是否有权加入游戏
            can_join = await self._can_join_game()
            if not can_join:
                await self.send(text_data=json.dumps({
                    'type': 'ERROR',
                    'payload': {
                        'success': False,
                        'error': {
                            'code': 'AUTH_FORBIDDEN',
                            'message': 'Not authorized to join this game'
                        }
                    },
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }))
                await self.close(code=4003)
                return
            
            # 加入房间组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # 更新玩家在线状态
            await self._update_player_online(True)
            
            # 发送当前游戏状态
            game_state = await self._get_game_state()
            await self.send(text_data=json.dumps({
                'type': 'GAME_STATE',
                'payload': game_state,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }))
            
            # 通知其他玩家有新玩家加入
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_join',
                    'data': {
                        'user_id': str(user.id),
                        'username': user.username
                    }
                }
            )
            
            logger.info(f"User {user.username} connected to game {self.game_id}")
            
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """断开 WebSocket 连接"""
        try:
            # 取消心跳监测任务
            if self.heartbeat_task and not self.heartbeat_task.done():
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 清理重连管理器
            if self.reconnect_manager:
                self.reconnect_manager.cancel()
                if self.user:
                    reconnect_service = await get_reconnect_service()
                    reconnect_service.remove_manager(self.game_id, str(self.user['id']))
            
            # 离开房间组
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # 更新玩家在线状态
            if self.user:
                await self._update_player_online(False)
                
                # 通知其他玩家
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'player_leave',
                        'data': {
                            'user_id': str(self.user['id']),
                            'username': self.user['username']
                        }
                    }
                )
            
            logger.info(f"User {self.user['username'] if self.user else 'Unknown'} disconnected from game {self.game_id}")
            
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")
    
    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 更新心跳时间
            self.last_heartbeat = timezone.now()
            
            # 更新重连管理器心跳
            if self.reconnect_manager and self.user:
                self.reconnect_manager.update_heartbeat()
            
            if message_type == 'JOIN':
                await self._handle_join(data)
            elif message_type == 'LEAVE':
                await self._handle_leave(data)
            elif message_type == 'MOVE':
                await self._handle_move(data)
            elif message_type == 'HEARTBEAT':
                await self._handle_heartbeat(data)
            elif message_type == 'RECONNECT_REQUEST':
                await self._handle_reconnect_request(data)
            elif message_type == 'GET_RECONNECT_HISTORY':
                await self._handle_get_reconnect_history(data)
            else:
                await self._send_error(f"Unknown message type: {message_type}", 'INVALID_MESSAGE_TYPE')
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format", 'INVALID_JSON')
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self._send_error(str(e), 'INTERNAL_ERROR')
    
    async def _handle_join(self, data):
        """处理加入游戏房间"""
        game_state = await self._get_game_state()
        await self.send(text_data=json.dumps({
            'type': 'JOIN_RESULT',
            'payload': {
                'success': True,
                'game_state': game_state
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def _handle_leave(self, data):
        """处理离开游戏房间"""
        await self.close()
    
    async def _handle_move(self, data):
        """处理走棋消息（使用异步消息队列优化）"""
        try:
            payload = data.get('payload', {})
            from_pos = payload.get('from')
            to_pos = payload.get('to')
            
            if not from_pos or not to_pos:
                await self._send_error("Missing from or to position", 'INVALID_MOVE')
                return
            
            # 使用异步处理器处理走棋
            if self.async_handler:
                message_id = await self.async_handler.enqueue_message(
                    room_id=self.game_id,
                    message_type='MOVE',
                    payload={
                        'from': from_pos,
                        'to': to_pos,
                        'user': self.user,
                        'channel_name': self.channel_name
                    },
                    priority=MessagePriority.HIGH
                )
                logger.debug(f"Move message enqueued: {message_id}")
            else:
                # 降级处理：直接处理
                await self._process_move_directly(from_pos, to_pos)
                
        except Exception as e:
            logger.error(f"Error handling move: {e}")
            await self._send_error(str(e), 'MOVE_ERROR')
    
    async def _process_move_directly(self, from_pos: str, to_pos: str):
        """直接处理走棋（降级处理）"""
        result = await database_sync_to_async(self._process_move)(
            self.game_id, from_pos, to_pos, self.user
        )
        
        if result['success']:
            await self._broadcast_move_result(result, from_pos, to_pos)
        else:
            await self._send_error(
                result.get('error_message', 'Invalid move'),
                result.get('error_code', 'INVALID_MOVE')
            )
    
    async def _broadcast_move_result(self, result: Dict, from_pos: str, to_pos: str):
        """广播走棋结果"""
        move_data = {
            'move': {
                'from': from_pos,
                'to': to_pos,
                'piece': result.get('piece'),
                'captured': result.get('captured'),
                'notation': result.get('notation')
            },
            'fen': result.get('fen'),
            'turn': result.get('turn'),
            'move_count': result.get('move_count'),
            'is_check': result.get('is_check', False),
            'is_checkmate': result.get('is_checkmate', False),
            'is_stalemate': result.get('is_stalemate', False)
        }
        
        # 广播给玩家
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'move_made',
                'data': move_data
            }
        )
        
        # 通知观战者
        await self._notify_spectators_move(move_data)
        
        # 如果游戏结束
        if result.get('game_over'):
            await self._broadcast_game_over(result)
    
    async def _handle_heartbeat(self, data):
        """处理心跳消息"""
        self.last_heartbeat = timezone.now()
        
        # 更新重连管理器心跳
        if self.reconnect_manager and self.user:
            self.reconnect_manager.update_heartbeat()
        
        await self.send(text_data=json.dumps({
            'type': 'HEARTBEAT',
            'payload': {
                'acknowledged': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'state': self.reconnect_manager.state.value if self.reconnect_manager else 'unknown'
            }
        }))
    
    async def _handle_reconnect_request(self, data):
        """处理重连请求"""
        if not self.reconnect_manager:
            await self._send_error("Reconnect manager not initialized", 'RECONNECT_ERROR')
            return
        
        success = await self.reconnect_manager.start_reconnect()
        if not success:
            await self._send_error("Failed to start reconnect", 'RECONNECT_FAILED')
    
    async def _handle_get_reconnect_history(self, data):
        """处理获取重连历史请求"""
        if not self.reconnect_manager:
            await self._send_error("Reconnect manager not initialized", 'RECONNECT_ERROR')
            return
        
        limit = data.get('payload', {}).get('limit', 10)
        history = self.reconnect_manager.get_reconnect_history(limit)
        stats = self.reconnect_manager.get_stats()
        
        await self.send(text_data=json.dumps({
            'type': 'RECONNECT_HISTORY',
            'payload': {
                'history': history,
                'stats': stats
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def _heartbeat_monitor(self):
        """心跳监测任务（后台运行）"""
        try:
            while True:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                
                # 检查心跳是否超时
                if self.reconnect_manager and self.user:
                    if self.reconnect_manager.is_heartbeat_timeout(self.TIMEOUT_THRESHOLD):
                        logger.warning(
                            f"Heartbeat timeout detected for user {self.user['id']} in game {self.game_id}"
                        )
                        
                        # 启动自动重连
                        reconnect_service = await get_reconnect_service()
                        await reconnect_service.start_reconnect(self.game_id, str(self.user['id']))
                
        except asyncio.CancelledError:
            logger.info(f"Heartbeat monitor cancelled for game {self.game_id}")
            raise
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _reconnect_channel(self):
        """
        重连频道（由 ReconnectManager 调用）
        
        Returns:
            是否成功
        """
        try:
            # 重新加入房间组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # 更新玩家在线状态
            await self._update_player_online(True)
            
            # 发送当前游戏状态
            game_state = await self._get_game_state()
            await self.send(text_data=json.dumps({
                'type': 'GAME_STATE',
                'payload': game_state,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }))
            
            logger.info(f"Successfully reconnected to channel for game {self.game_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error reconnecting to channel: {e}")
            return False
    
    # Channel layer 重连状态处理器
    async def reconnect_status(self, event):
        """接收其他玩家的重连状态广播"""
        await self.send(text_data=json.dumps({
            'type': 'RECONNECT_STATUS',
            'payload': {
                'user_id': event['data'].get('user_id'),
                'state': event['data'].get('state'),
                'attempt': event['data'].get('attempt')
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def _send_error(self, message: str, code: str):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'ERROR',
            'payload': {
                'success': False,
                'error': {
                    'code': code,
                    'message': message
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def _notify_spectators_move(self, move_data: dict):
        """
        通知观战者走棋
        
        Args:
            move_data: 走棋数据
        """
        try:
            await self.channel_layer.group_send(
                f'spectate_{self.game_id}',
                {
                    'type': 'move_made',
                    'data': move_data
                }
            )
        except Exception as e:
            logger.error(f"Error notifying spectators of move: {e}")
    
    async def _notify_spectators_game_over(self, result_data: dict):
        """
        通知观战者游戏结束
        
        Args:
            result_data: 游戏结果数据
        """
        try:
            await self.channel_layer.group_send(
                f'spectate_{self.game_id}',
                {
                    'type': 'game_over',
                    'data': result_data
                }
            )
        except Exception as e:
            logger.error(f"Error notifying spectators of game over: {e}")
    
    async def _broadcast_game_over(self, result: Dict):
        """广播游戏结束"""
        game_over_data = {
            'winner': result.get('winner'),
            'reason': result.get('win_reason'),
            'rating_change': result.get('rating_change')
        }
        
        # 通知玩家
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_over',
                'data': game_over_data
            }
        )
        
        # 通知观战者
        await self._notify_spectators_game_over(game_over_data)
    
    async def _authenticate_connection(self) -> Optional[Dict]:
        """
        验证连接身份
        
        Returns:
            用户信息字典，验证失败返回 None
        """
        try:
            # 从 URL 参数或 headers 获取 token
            query_string = self.scope.get('query_string', b'').decode()
            params = {}
            if query_string:
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            
            token = params.get('token')
            if not token:
                # 尝试从 headers 获取
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
            
            if not token:
                logger.warning("No token provided in WebSocket connection")
                return None
            
            # 验证 JWT token - TokenService.verify_token 会抛出异常而不是返回 None
            try:
                payload = TokenService.verify_token(token)
            except Exception as token_error:
                logger.warning(f"Token verification failed: {token_error}")
                return None
            
            if not payload:
                return None
            
            # 获取用户信息
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning("No user_id in JWT payload")
                return None
            
            # _get_user_by_id 已经使用了 @database_sync_to_async 装饰器，直接调用
            user = await self._get_user_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    @sync_to_async(thread_sensitive=True)
    def _get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """根据 ID 获取用户（使用 thread_sensitive 避免 SQLite 锁定问题）"""
        from users.models import User
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': str(user.id),
                'username': user.username
            }
        except User.DoesNotExist:
            return None
    
    async def _can_join_game(self) -> bool:
        """
        验证用户是否有权加入游戏
        
        Returns:
            是否允许加入
        """
        try:
            # _get_game 已经使用了 @database_sync_to_async 装饰器，直接调用
            game = await self._get_game(self.game_id)
            if not game:
                return False
            
            # 检查用户是否是游戏参与者
            user_id = str(self.user['id'])
            if game.get('red_player_id') == user_id or game.get('black_player_id') == user_id:
                return True
            
            # 检查游戏是否允许观战（未来扩展）
            # 目前只允许参与者加入
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking game access: {e}")
            return False
    
    @sync_to_async(thread_sensitive=True)
    def _get_game(self, game_id: str) -> Optional[Dict]:
        """获取游戏信息（使用 thread_sensitive 避免 SQLite 锁定问题）"""
        try:
            from uuid import UUID
            game = Game.objects.select_related('red_player', 'black_player').get(id=UUID(game_id))
            return {
                'id': str(game.id),
                'status': game.status,
                'red_player_id': str(game.red_player.id) if game.red_player else None,
                'black_player_id': str(game.black_player.id) if game.black_player else None,
                'fen_current': game.fen_current,
                'turn': game.turn
            }
        except Exception:
            return None
    
    async def _update_player_online(self, is_online: bool):
        """更新玩家在线状态"""
        # 未来可以实现：在 Redis 中记录玩家在线状态
        # 用于匹配系统和好友列表
        pass
    
    async def _get_game_state(self) -> Dict:
        """获取游戏状态"""
        # _get_game 已经使用了 @database_sync_to_async 装饰器，直接调用
        game = await self._get_game(self.game_id)
        if not game:
            return {}
        
        return {
            'game_id': self.game_id,
            'fen': game.get('fen_current'),
            'turn': game.get('turn'),
            'status': game.get('status'),
            'players': {
                'red': {
                    'user_id': game.get('red_player_id'),
                    'online': False  # 实际应该查询在线状态
                },
                'black': {
                    'user_id': game.get('black_player_id'),
                    'online': False
                }
            }
        }
    
    def _process_move(self, game_id: str, from_pos: str, to_pos: str, user: Dict) -> Dict:
        """
        处理走棋（同步方法，在 database_sync_to_async 中调用）
        
        Returns:
            处理结果字典
        """
        from uuid import UUID
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # 获取游戏（加锁）
                game = Game.objects.select_for_update().get(id=UUID(game_id))
                
                # 验证游戏状态
                if game.status != 'playing':
                    return {
                        'success': False,
                        'error_code': 'GAME_NOT_PLAYING',
                        'error_message': '游戏未进行中'
                    }
                
                # 验证是否是当前玩家的回合
                user_id = str(user['id'])
                is_red_turn = game.turn == 'w'
                is_user_red = game.red_player_id and str(game.red_player_id) == user_id
                is_user_black = game.black_player_id and str(game.black_player_id) == user_id
                
                if (is_red_turn and not is_user_red) or (not is_red_turn and not is_user_black):
                    return {
                        'success': False,
                        'error_code': 'NOT_YOUR_TURN',
                        'error_message': '不是你的回合'
                    }
                
                # 更新计时器并检查超时
                timer_service = get_timer_service()
                player_color = 'red' if is_red_turn else 'black'
                remaining_time, is_timeout = timer_service.update_timer(game, player_color)
                
                if is_timeout:
                    # 超时判负
                    timer_service.handle_timeout(game, player_color)
                    return {
                        'success': True,
                        'game_over': True,
                        'winner': 'black' if player_color == 'red' else 'red',
                        'win_reason': 'timeout',
                        'timeout_player': player_color,
                        'remaining_time': remaining_time
                    }
                
                # 创建棋盘对象
                board = Board(game.fen_current)
                
                # 创建走棋对象
                piece = board.get_piece(from_pos)
                if not piece:
                    return {
                        'success': False,
                        'error_code': 'NO_PIECE',
                        'error_message': '起始位置没有棋子'
                    }
                
                move = Move(
                    from_pos=from_pos,
                    to_pos=to_pos,
                    piece=piece,
                    captured=board.get_piece(to_pos)
                )
                
                # 验证走棋合法性
                legal_moves = board.get_legal_moves_for_piece(from_pos)
                legal_positions = [m.to_pos for m in legal_moves]
                
                if to_pos not in legal_positions:
                    return {
                        'success': False,
                        'error_code': 'INVALID_MOVE',
                        'error_message': '该棋子不能移动到此位置',
                        'legal_moves': legal_positions
                    }
                
                # 执行走棋
                board.make_move(move)
                
                # 创建走棋记录
                game_move = GameMove.objects.create(
                    game=game,
                    move_number=game.move_count + 1,
                    piece=piece,
                    from_pos=from_pos,
                    to_pos=to_pos,
                    captured=move.captured,
                    is_check=board._is_in_check(piece.isupper()),
                    is_capture=move.captured is not None,
                    notation=self._to_chinese_notation(move, piece),
                    fen_after=board.to_fen()
                )
                
                # 更新游戏状态
                game.fen_current = board.to_fen()
                game.turn = board.turn
                game.move_count += 1
                game.save()
                
                # 检查游戏结束
                is_checkmate = board.is_checkmate()
                is_stalemate = board.is_stalemate()
                
                # 获取双方剩余时间
                timer_service = get_timer_service()
                red_remaining = timer_service.get_remaining_time(game, 'red')
                black_remaining = timer_service.get_remaining_time(game, 'black')
                
                result = {
                    'success': True,
                    'piece': piece,
                    'captured': move.captured,
                    'notation': game_move.notation,
                    'fen': board.to_fen(),
                    'turn': board.turn,
                    'move_count': game.move_count,
                    'is_check': board._is_in_check(piece.isupper()),
                    'is_checkmate': is_checkmate,
                    'is_stalemate': is_stalemate,
                    'game_over': is_checkmate or is_stalemate,
                    'red_time_remaining': red_remaining,
                    'black_time_remaining': black_remaining
                }
                
                if is_checkmate or is_stalemate:
                    winner = self._determine_winner(board, game)
                    result['winner'] = winner
                    result['win_reason'] = 'checkmate' if is_checkmate else 'stalemate'
                    
                    # 更新游戏状态
                    if is_checkmate:
                        game.status = 'white_win' if winner == 'red' else 'black_win'
                    else:
                        game.status = 'draw'
                    game.finished_at = timezone.now()
                    game.save()
                    
                    # 计算天梯分变化（未来实现）
                    result['rating_change'] = {'red': 0, 'black': 0}
                
                return result
                
        except Game.DoesNotExist:
            return {
                'success': False,
                'error_code': 'GAME_NOT_FOUND',
                'error_message': '游戏不存在'
            }
        except Exception as e:
            logger.error(f"Error processing move: {e}")
            return {
                'success': False,
                'error_code': 'MOVE_ERROR',
                'error_message': str(e)
            }
    
    def _to_chinese_notation(self, move: Move, piece: str) -> str:
        """
        转换为中文记谱
        
        格式：棋子名 + 起始列 + 移动方式 + 目标位置
        例如：炮二平五、马 8 进 7
        """
        # 简化实现，完整实现需要更复杂的逻辑
        piece_names = {
            'K': '帅', 'k': '将',
            'A': '仕', 'a': '士',
            'B': '相', 'b': '象',
            'N': '马', 'n': '马',
            'R': '车', 'r': '车',
            'C': '炮', 'c': '炮',
            'P': '兵', 'p': '卒'
        }
        
        piece_name = piece_names.get(piece.upper(), '?')
        from_file = move.from_pos[0]
        to_file = move.to_pos[0]
        from_rank = int(move.from_pos[1:])
        to_rank = int(move.to_pos[1:])
        
        # 简化记谱
        if from_rank == to_rank:
            action = '平'
        elif to_rank > from_rank:
            action = '进'
        else:
            action = '退'
        
        return f"{piece_name}{from_file}{action}{to_file}"
    
    def _determine_winner(self, board: Board, game: Game) -> str:
        """
        确定获胜方
        
        Returns:
            'red' 或 'black'
        """
        # 将死时，当前回合方输
        if board.turn == 'w':
            return 'black'
        else:
            return 'red'
    
    # Channel layer 消息处理器
    async def move_made(self, event):
        """广播走棋消息"""
        await self.send(text_data=json.dumps({
            'type': 'MOVE_RESULT',
            'payload': {
                'success': True,
                'move': event['data'].get('move'),
                'fen': event['data'].get('fen'),
                'turn': event['data'].get('turn'),
                'is_check': event['data'].get('is_check'),
                'is_checkmate': event['data'].get('is_checkmate'),
                'is_stalemate': event['data'].get('is_stalemate')
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def game_over(self, event):
        """广播游戏结束消息"""
        await self.send(text_data=json.dumps({
            'type': 'GAME_OVER',
            'payload': {
                'winner': event['data'].get('winner'),
                'reason': event['data'].get('reason'),
                'rating_change': event['data'].get('rating_change')
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def player_join(self, event):
        """广播玩家加入消息"""
        await self.send(text_data=json.dumps({
            'type': 'PLAYER_JOIN',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def player_leave(self, event):
        """广播玩家离开消息"""
        await self.send(text_data=json.dumps({
            'type': 'PLAYER_LEAVE',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
