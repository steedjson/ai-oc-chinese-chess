"""
聊天系统 WebSocket Consumer

提供实时聊天功能：
- 加入/离开聊天房间
- 实时消息推送
- 消息限流
- 房间管理
"""
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from channels.db import database_sync_to_async

from .chat import ChatMessage, ChatMessageManager, MessageType
from .models import Game
from .spectator import Spectator, SpectatorStatus
from websocket.consumers import BaseConsumer
from websocket.config import get_logger

logger = get_logger('chat_consumer')


class ChatConsumer(BaseConsumer):
    """
    聊天 WebSocket Consumer
    
    支持两种房间类型：
    - game: 对局内聊天（玩家之间）
    - spectator: 观战聊天（观战者之间）
    
    使用示例：
    # 对局聊天
    ws://localhost:8000/ws/chat/game/{game_id}/?token={jwt_token}
    
    # 观战聊天
    ws://localhost:8000/ws/chat/spectator/{game_id}/?token={jwt_token}
    """
    
    # 消息限流配置
    RATE_LIMIT_SECONDS = 2  # 每条消息间隔至少 2 秒
    MAX_MESSAGE_LENGTH = 500  # 最大消息长度
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_id = None
        self.room_type = None
        self.room_group_name = None
        self.last_message_time = None
        self.user_info = None
    
    async def connect(self):
        """建立 WebSocket 连接"""
        try:
            # 从 URL 获取参数
            self.room_type = self.scope['url_route']['kwargs'].get('room_type', 'game')
            self.game_id = self.scope['url_route']['kwargs'].get('game_id')
            
            # 验证房间类型
            if self.room_type not in ['game', 'spectator']:
                await self._send_error('INVALID_ROOM_TYPE', '无效的房间类型')
                return
            
            # 认证
            authenticated = await self.authenticate()
            if not authenticated:
                return
            
            # 验证游戏存在
            game_exists = await self._verify_game_exists(self.game_id)
            if not game_exists:
                await self._send_error('GAME_NOT_FOUND', '游戏不存在')
                return
            
            # 权限验证
            if self.room_type == 'game':
                # 对局聊天：必须是游戏参与者
                is_participant = await self._verify_game_participant(self.game_id, self.user)
                if not is_participant and not self.user.get('is_staff', False):
                    await self._send_error('NOT_PARTICIPANT', '只有游戏参与者可以加入对局聊天')
                    await self.close(code=4003)  # 拒绝连接
                    return
            elif self.room_type == 'spectator':
                # 观战聊天：必须是观战者
                is_spectator = await self._verify_spectator(self.game_id, self.user)
                if not is_spectator and not self.user.get('is_staff', False):
                    await self._send_error('NOT_SPECTATOR', '只有观战者可以加入观战聊天')
                    await self.close(code=4003)  # 拒绝连接
                    return
            
            # 设置房间组名称
            self.room_group_name = f'chat_{self.room_type}_{self.game_id}'
            
            # 加入频道组
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # 接受连接
            await self.accept()
            
            # 初始化心跳追踪
            await super().connect()
            
            # 发送欢迎消息
            await self._send_welcome()
            
            # 发送历史消息（最近 50 条）
            await self._send_recent_history()
            
            logger.info(f"User {self.user.get('username')} joined chat room {self.room_group_name}")
            
        except Exception as e:
            logger.error(f"Error in chat connect: {e}")
            await self._send_error('CONNECTION_ERROR', str(e))
            await self.close()
    
    async def disconnect(self, close_code: int):
        """断开 WebSocket 连接"""
        try:
            # 离开频道组
            if self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
            
            # 广播离开消息（可选）
            # await self._broadcast_system_message(f"{self.user.get('username')} 离开了聊天")
            
            logger.info(f"User {self.user.get('username')} left chat room {self.room_group_name}")
            
        except Exception as e:
            logger.error(f"Error in chat disconnect: {e}")
        
        await super().disconnect(close_code)
    
    async def receive(self, text_data: str):
        """
        接收客户端消息
        
        支持的消息类型：
        - CHAT_MESSAGE: 发送聊天消息
        - HEARTBEAT: 心跳
        - GET_HISTORY: 获取历史消息
        """
        try:
            # 更新心跳
            self.update_heartbeat()
            
            # 解析消息
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 处理不同类型的消息
            if message_type == 'CHAT_MESSAGE':
                await self.handle_chat_message(data)
            elif message_type == 'HEARTBEAT':
                await self.handle_heartbeat(data)
            elif message_type == 'GET_HISTORY':
                await self.handle_get_history(data)
            elif message_type == 'DELETE_MESSAGE':
                await self.handle_delete_message(data)
            else:
                await self._send_error('UNKNOWN_MESSAGE_TYPE', f'未知的消息类型：{message_type}')
                
        except json.JSONDecodeError:
            await self._send_error('INVALID_JSON', '无效的 JSON 格式')
        except Exception as e:
            logger.error(f"Error in chat receive: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
    
    async def handle_chat_message(self, data: Dict[str, Any]):
        """
        处理聊天消息
        
        Args:
            data: 消息数据，包含 content, message_type 等
        """
        try:
            content = data.get('content', '').strip()
            message_type = data.get('message_type', 'text')
            
            # 验证消息内容
            if not content:
                await self._send_error('EMPTY_MESSAGE', '消息内容不能为空')
                return
            
            # 限制消息长度
            if len(content) > self.MAX_MESSAGE_LENGTH:
                await self._send_error('MESSAGE_TOO_LONG', f'消息长度不能超过 {self.MAX_MESSAGE_LENGTH} 字符')
                return
            
            # 验证消息类型
            if message_type not in ['text', 'emoji']:
                await self._send_error('INVALID_MESSAGE_TYPE', '无效的消息类型')
                return
            
            # 系统消息只有管理员可发送
            if message_type == 'system' and not self.user.get('is_staff', False):
                await self._send_error('NO_PERMISSION', '无权限发送系统消息')
                return
            
            # 限流检查
            current_time = time.time()
            if self.last_message_time:
                time_diff = current_time - self.last_message_time
                if time_diff < self.RATE_LIMIT_SECONDS:
                    await self._send_error('RATE_LIMITED', f'发送频率过快，请等待 {self.RATE_LIMIT_SECONDS - time_diff:.1f} 秒')
                    return
            
            # 表情消息验证
            if message_type == 'emoji':
                is_valid = await self._verify_emoji(content)
                if not is_valid:
                    await self._send_error('INVALID_EMOJI', '不支持的表情符号')
                    return
            
            # 保存消息到数据库
            result = await self._save_message(
                content=content,
                message_type=message_type
            )
            
            if result['success']:
                message = result['message']
                
                # 更新最后发送时间
                self.last_message_time = current_time
                
                # 广播消息到房间（转换为字典）
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message.to_dict() if hasattr(message, 'to_dict') else message
                    }
                )
                
                logger.info(f"Message sent in room {self.room_group_name} by {self.user.get('username')}")
            else:
                await self._send_error('SEND_FAILED', result['error'])
                
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
    
    async def handle_get_history(self, data: Dict[str, Any]):
        """
        处理获取历史消息请求
        
        Args:
            data: 包含 limit, before 等参数
        """
        try:
            limit = min(int(data.get('limit', 50)), 100)
            before = data.get('before', None)
            
            messages = await self._get_message_history(limit=limit, before=before)
            
            await self.send(text_data=json.dumps({
                'type': 'CHAT_HISTORY',
                'payload': {
                    'success': True,
                    'messages': messages,
                    'room_type': self.room_type
                }
            }))
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            await self._send_error('GET_HISTORY_FAILED', str(e))
    
    async def handle_delete_message(self, data: Dict[str, Any]):
        """
        处理删除消息请求
        
        Args:
            data: 包含 message_id
        """
        try:
            message_id = data.get('message_id')
            
            if not message_id:
                await self._send_error('MISSING_MESSAGE_ID', '缺少消息 ID')
                return
            
            result = await self._delete_message(message_id)
            
            if result['success']:
                # 广播删除事件
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id
                    }
                )
                
                await self.send(text_data=json.dumps({
                    'type': 'MESSAGE_DELETED',
                    'payload': {
                        'success': True,
                        'message_id': message_id
                    }
                }))
            else:
                await self._send_error('DELETE_FAILED', result['error'])
                
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
    
    # Channel Layer 消息处理器
    
    async def chat_message(self, event: Dict[str, Any]):
        """
        接收广播的聊天消息
        
        从 channel layer 接收其他用户发送的消息
        """
        message = event.get('message', {})
        
        await self.send(text_data=json.dumps({
            'type': 'CHAT_MESSAGE',
            'payload': {
                'success': True,
                'message': message
            }
        }))
    
    async def message_deleted(self, event: Dict[str, Any]):
        """
        接收广播的消息删除事件
        """
        message_id = event.get('message_id')
        
        await self.send(text_data=json.dumps({
            'type': 'MESSAGE_DELETED',
            'payload': {
                'success': True,
                'message_id': message_id
            }
        }))
    
    async def system_message(self, event: Dict[str, Any]):
        """
        接收广播的系统消息
        """
        content = event.get('content', '')
        
        await self.send(text_data=json.dumps({
            'type': 'SYSTEM_MESSAGE',
            'payload': {
                'content': content,
                'message_type': 'system'
            }
        }))
    
    # 辅助方法
    
    async def _send_welcome(self):
        """发送欢迎消息"""
        await self.send(text_data=json.dumps({
            'type': 'WELCOME',
            'payload': {
                'room_type': self.room_type,
                'game_id': self.game_id,
                'username': self.user.get('username'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }))
    
    async def _send_recent_history(self):
        """发送最近的历史消息"""
        messages = await self._get_message_history(limit=50)
        
        await self.send(text_data=json.dumps({
            'type': 'CHAT_HISTORY',
            'payload': {
                'success': True,
                'messages': messages,
                'room_type': self.room_type
            }
        }))
    
    async def _broadcast_system_message(self, content: str):
        """广播系统消息"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'system_message',
                'content': content
            }
        )
    
    @database_sync_to_async
    def _verify_game_exists(self, game_id: str) -> bool:
        """验证游戏是否存在"""
        try:
            from uuid import UUID
            return Game.objects.filter(id=UUID(game_id)).exists()
        except Exception:
            return False
    
    @database_sync_to_async
    def _verify_game_participant(self, game_id: str, user: Dict) -> bool:
        """验证用户是否是游戏参与者"""
        try:
            from uuid import UUID
            game = Game.objects.select_related('red_player', 'black_player').get(id=UUID(game_id))
            user_id = str(user.get('id'))
            is_red = game.red_player and str(game.red_player.id) == user_id
            is_black = game.black_player and str(game.black_player.id) == user_id
            logger.info(f"Verify participant: user_id={user_id}, red={game.red_player.id if game.red_player else None}, black={game.black_player.id if game.black_player else None}, is_red={is_red}, is_black={is_black}")
            result = is_red or is_black
            logger.info(f"Participant check result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error verifying participant: {e}")
            return False
    
    @database_sync_to_async
    def _verify_spectator(self, game_id: str, user: Dict) -> bool:
        """验证用户是否是观战者"""
        try:
            from uuid import UUID
            result = Spectator.objects.filter(
                game_id=UUID(game_id),
                user_id=user.get('id'),
                status=SpectatorStatus.WATCHING
            ).exists()
            logger.info(f"Verify spectator: user_id={user.get('id')}, game_id={game_id}, is_spectator={result}")
            return result
        except Exception as e:
            logger.error(f"Error verifying spectator: {e}")
            return False
    
    @database_sync_to_async
    def _verify_emoji(self, content: str) -> bool:
        """验证表情是否有效"""
        return ChatMessageManager.is_valid_emoji(content)
    
    @database_sync_to_async
    def _save_message(self, content: str, message_type: str) -> Dict:
        """保存消息到数据库"""
        result = ChatMessageManager.send_message_sync(
            game_id=self.game_id,
            user_id=str(self.user.get('id')),
            content=content,
            message_type=message_type,
            room_type=self.room_type
        )
        return result
    
    @database_sync_to_async
    def _get_message_history(self, limit: int = 50, before: Optional[str] = None) -> list:
        """获取消息历史"""
        return ChatMessageManager.get_message_history_sync(
            game_id=self.game_id,
            room_type=self.room_type,
            limit=limit,
            before=before
        )
    
    @database_sync_to_async
    def _delete_message(self, message_id: str) -> Dict:
        """删除消息"""
        return ChatMessageManager.delete_message_sync(
            message_uuid=message_id,
            user_id=str(self.user.get('id'))
        )
    
    def _format_error(self, code: str, message: str) -> str:
        """格式化错误消息"""
        return json.dumps({
            'type': 'ERROR',
            'payload': {
                'success': False,
                'error': {
                    'code': code,
                    'message': message
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    async def _send_error(self, code: str, message: str):
        """发送错误消息"""
        await self.send(text_data=self._format_error(code, message))


# 添加同步版本的历史消息获取方法
@database_sync_to_async
def get_message_history_sync(game_id: str, room_type: str, limit: int, before: Optional[str]) -> list:
    """同步包装的消息历史获取"""
    import asyncio
    return asyncio.run(ChatMessageManager.get_message_history(
        game_id=game_id,
        room_type=room_type,
        limit=limit,
        before=before
    ))


# 更新 ChatMessageManager 添加同步方法
def get_message_history_sync_wrapper(game_id: str, room_type: str, limit: int, before: Optional[str]) -> list:
    """ChatMessageManager 的同步历史消息获取"""
    from django.utils import timezone
    from uuid import UUID
    
    try:
        query = ChatMessage.objects.filter(
            game_id=UUID(game_id),
            room_type=room_type,
            is_deleted=False
        ).select_related('sender')
        
        if before:
            query = query.filter(created_at__lt=before)
        
        messages = list(query.order_by('-created_at')[:limit])
        messages.reverse()
        
        return [msg.to_dict() for msg in messages]
    except Exception:
        return []


#  monkey patch: 添加到 ChatMessageManager
ChatMessageManager.get_message_history_sync = staticmethod(get_message_history_sync_wrapper)
