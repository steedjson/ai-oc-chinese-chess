"""
观战 WebSocket Consumer

实现观战房间的实时功能：
- 观战连接认证
- 加入/离开观战房间
- 实时棋盘状态推送
- 观战权限验证
- 观战者列表管理
"""
import json
import logging
from typing import Dict, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime

from .models import Game
from .spectator import Spectator, SpectatorManager, SpectatorStatus
from authentication.services import TokenService

logger = logging.getLogger(__name__)


class SpectatorConsumer(AsyncWebsocketConsumer):
    """
    观战房间 Consumer
    
    WebSocket 路由：/ws/spectate/{game_id}/
    
    消息类型：
    - JOIN: 加入观战
    - LEAVE: 离开观战
    - GAME_STATE: 游戏状态更新（从玩家端广播）
    - MOVE_MADE: 走棋通知（从玩家端广播）
    - SPECTATOR_LIST: 观战者列表更新
    - HEARTBEAT: 心跳
    - ERROR: 错误消息
    """
    
    # 心跳配置
    HEARTBEAT_INTERVAL = 30  # 30 秒
    TIMEOUT_THRESHOLD = 90  # 90 秒无心跳判定掉线
    
    async def connect(self):
        """建立 WebSocket 连接"""
        try:
            self.game_id = self.scope['url_route']['kwargs']['game_id']
            self.room_group_name = f'spectate_{self.game_id}'
            self.player_room_group_name = f'game_{self.game_id}'  # 玩家房间组
            self.user = None
            self.spectator = None
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
            
            # 验证观战权限
            can_spectate = await self._can_spectate_game()
            if not can_spectate:
                await self.send(text_data=json.dumps({
                    'type': 'ERROR',
                    'payload': {
                        'success': False,
                        'error': {
                            'code': 'AUTH_FORBIDDEN',
                            'message': 'Not authorized to spectate this game'
                        }
                    },
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }))
                await self.close(code=4003)
                return
            
            # 加入观战房间组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # 也加入玩家房间组（只接收，不发送）- 用于接收游戏状态更新
            await self.channel_layer.group_add(
                self.player_room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # 创建观战记录
            spectator_result = await self._join_spectate()
            if not spectator_result['success']:
                await self.send(text_data=json.dumps({
                    'type': 'ERROR',
                    'payload': {
                        'success': False,
                        'error': {
                            'code': 'SPECTATE_FAILED',
                            'message': spectator_result.get('error', 'Failed to join spectate')
                        }
                    },
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }))
                await self.close(code=4004)
                return
            
            self.spectator = spectator_result['spectator']
            
            # 发送当前游戏状态
            game_state = await self._get_game_state()
            await self.send(text_data=json.dumps({
                'type': 'GAME_STATE',
                'payload': game_state,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }))
            
            # 通知其他观战者有新观战者加入
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'spectator_join',
                    'data': {
                        'user_id': str(user['id']),
                        'username': user['username'] if not spectator_result.get('is_anonymous', False) else '匿名用户',
                        'spectator_count': await self._get_spectator_count()
                    }
                }
            )
            
            logger.info(f"Spectator {user['username']} connected to game {self.game_id}")
            
        except Exception as e:
            logger.error(f"Error in spectator connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """断开 WebSocket 连接"""
        try:
            # 离开房间组
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                self.player_room_group_name,
                self.channel_name
            )
            
            # 更新观战状态
            if self.spectator:
                await self._leave_spectate()
                
                # 通知其他观战者
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'spectator_leave',
                        'data': {
                            'user_id': str(self.user['id']) if self.user else None,
                            'username': self.user['username'] if self.user else 'Unknown',
                            'spectator_count': await self._get_spectator_count()
                        }
                    }
                )
            
            logger.info(f"Spectator {self.user['username'] if self.user else 'Unknown'} disconnected from game {self.game_id}")
            
        except Exception as e:
            logger.error(f"Error in spectator disconnect: {e}")
    
    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 更新心跳时间
            self.last_heartbeat = timezone.now()
            
            if message_type == 'JOIN':
                await self._handle_join(data)
            elif message_type == 'LEAVE':
                await self._handle_leave(data)
            elif message_type == 'HEARTBEAT':
                await self._handle_heartbeat(data)
            else:
                await self._send_error(f"Unknown message type: {message_type}", 'INVALID_MESSAGE_TYPE')
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format", 'INVALID_JSON')
        except Exception as e:
            logger.error(f"Error in spectator receive: {e}")
            await self._send_error(str(e), 'INTERNAL_ERROR')
    
    async def _handle_join(self, data):
        """处理加入观战"""
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
        """处理离开观战"""
        await self.close()
    
    async def _handle_heartbeat(self, data):
        """处理心跳消息"""
        self.last_heartbeat = timezone.now()
        await self.send(text_data=json.dumps({
            'type': 'HEARTBEAT',
            'payload': {
                'acknowledged': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
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
    
    async def _authenticate_connection(self) -> Optional[Dict]:
        """验证连接身份"""
        try:
            # 从 URL 参数获取 token
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
                logger.warning("No token provided in spectator WebSocket connection")
                return None
            
            # 验证 JWT token
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
        """根据 ID 获取用户"""
        from users.models import User
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': str(user.id),
                'username': user.username
            }
        except User.DoesNotExist:
            return None
    
    async def _can_spectate_game(self) -> bool:
        """验证用户是否有权观战"""
        try:
            game = await self._get_game(self.game_id)
            if not game:
                return False
            
            # 只能观战进行中的游戏
            if game.get('status') not in ['playing', 'pending']:
                return False
            
            # 检查用户是否是游戏参与者（参与者不能观战）
            user_id = str(self.user['id'])
            if game.get('red_player_id') == user_id or game.get('black_player_id') == user_id:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking spectate permission: {e}")
            return False
    
    @sync_to_async(thread_sensitive=True)
    def _get_game(self, game_id: str) -> Optional[Dict]:
        """获取游戏信息"""
        from uuid import UUID
        try:
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
    
    async def _join_spectate(self) -> Dict:
        """加入观战"""
        result = await SpectatorManager.join_spectate(
            game_id=self.game_id,
            user_id=str(self.user['id']),
            is_anonymous=False  # 默认不匿名
        )
        return result
    
    async def _leave_spectate(self):
        """离开观战"""
        await SpectatorManager.leave_spectate(
            game_id=self.game_id,
            user_id=str(self.user['id'])
        )
    
    async def _get_game_state(self) -> Dict:
        """获取游戏状态"""
        game = await self._get_game(self.game_id)
        if not game:
            return {}
        
        spectator_count = await self._get_spectator_count()
        
        return {
            'game_id': self.game_id,
            'fen': game.get('fen_current'),
            'turn': game.get('turn'),
            'status': game.get('status'),
            'move_count': game.get('move_count', 0),
            'players': {
                'red': {
                    'user_id': game.get('red_player_id'),
                    'online': False
                },
                'black': {
                    'user_id': game.get('black_player_id'),
                    'online': False
                }
            },
            'spectator_count': spectator_count
        }
    
    async def _get_spectator_count(self) -> int:
        """获取观战人数"""
        return await SpectatorManager.get_spectator_count(self.game_id)
    
    # Channel layer 消息处理器 - 从玩家房间接收消息
    
    async def move_made(self, event):
        """广播走棋消息给观战者"""
        await self.send(text_data=json.dumps({
            'type': 'MOVE_MADE',
            'payload': {
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
        """广播游戏结束消息给观战者"""
        await self.send(text_data=json.dumps({
            'type': 'GAME_OVER',
            'payload': {
                'winner': event['data'].get('winner'),
                'reason': event['data'].get('reason'),
                'rating_change': event['data'].get('rating_change')
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def game_state_update(self, event):
        """广播游戏状态更新给观战者"""
        await self.send(text_data=json.dumps({
            'type': 'GAME_STATE_UPDATE',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    # 观战者相关消息
    
    async def spectator_join(self, event):
        """广播观战者加入消息"""
        await self.send(text_data=json.dumps({
            'type': 'SPECTATOR_JOIN',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def spectator_leave(self, event):
        """广播观战者离开消息"""
        await self.send(text_data=json.dumps({
            'type': 'SPECTATOR_LEAVE',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def spectator_list(self, event):
        """广播观战者列表更新"""
        await self.send(text_data=json.dumps({
            'type': 'SPECTATOR_LIST',
            'payload': event['data'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))


class SpectatorManagerConsumer:
    """
    观战管理器（用于从 GameConsumer 通知观战者）
    
    这是一个工具类，用于从游戏房间向观战房间广播消息
    """
    
    @staticmethod
    async def notify_spectators(game_id: str, message_type: str, data: dict):
        """
        向所有观战者发送通知
        
        Args:
            game_id: 游戏 ID
            message_type: 消息类型
            data: 消息数据
        """
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        room_group_name = f'spectate_{game_id}'
        
        await channel_layer.group_send(
            room_group_name,
            {
                'type': message_type.lower().replace('_', ''),
                'data': data
            }
        )
    
    @staticmethod
    async def broadcast_move(game_id: str, move_data: dict):
        """
        向观战者广播走棋
        
        Args:
            game_id: 游戏 ID
            move_data: 走棋数据
        """
        await SpectatorManagerConsumer.notify_spectators(
            game_id,
            'GAME_STATE_UPDATE',
            {
                'type': 'move',
                'move': move_data
            }
        )
    
    @staticmethod
    async def broadcast_game_over(game_id: str, result_data: dict):
        """
        向观战者广播游戏结束
        
        Args:
            game_id: 游戏 ID
            result_data: 游戏结果数据
        """
        await SpectatorManagerConsumer.notify_spectators(
            game_id,
            'GAME_OVER',
            result_data
        )
