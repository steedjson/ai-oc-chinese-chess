"""
匹配系统 WebSocket Consumer

提供匹配队列的实时通信支持：
- 加入/退出匹配队列
- 匹配进度通知
- 匹配成功通知
- 预估等待时间推送
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from channels.db import database_sync_to_async

from websocket.consumers import BaseConsumer
from websocket.middleware import JWTAuthMiddleware
from .queue import MatchmakingQueue, QueueUser
from .algorithm import Matchmaker
from .models import MatchQueue as MatchQueueModel

logger = logging.getLogger(__name__)


class MatchmakingConsumer(BaseConsumer):
    """
    匹配系统 WebSocket Consumer
    
    WebSocket 路由：/ws/matchmaking/
    
    消息类型：
    - JOIN_QUEUE: 加入匹配队列
    - LEAVE_QUEUE: 退出匹配队列
    - MATCH_FOUND: 找到匹配
    - QUEUE_STATUS: 队列状态
    - ESTIMATE_UPDATE: 预估时间更新
    - HEARTBEAT: 心跳
    - ERROR: 错误消息
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type = 'matchmaking'
        self.queue = MatchmakingQueue()
        self.matchmaker = Matchmaker()
        self.user_queue_data = None
    
    async def connect(self):
        """建立 WebSocket 连接"""
        try:
            # 认证 - 使用父类的 authenticate 方法
            authenticated = await self.authenticate()
            if not authenticated:
                # authenticate 方法已经发送了错误并关闭连接
                return
            
            # 设置资源信息
            self.resource_id = 'matchmaking'
            
            # 加入房间组
            self.room_group_name = 'matchmaking'
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # 调用父类的 connect 初始化心跳追踪
            await super().connect()
            
            # 发送连接确认
            await self.send(text_data=self._format_message(
                'connected',
                {
                    'status': 'connected',
                    'user_id': self.user['id']
                }
            ))
            
            logger.info(f"User {self.user['username']} connected to matchmaking")
            
        except Exception as e:
            logger.error(f"Error in matchmaking connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code: int):
        """断开 WebSocket 连接"""
        try:
            # 离开房间组
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # 如果用户在队列中，自动退出
            if self.user_queue_data:
                await self._remove_from_queue()
            
            # 调用父类的 disconnect
            await super().disconnect(close_code)
            
            logger.info(f"User {self.user['username']} disconnected from matchmaking")
            
        except Exception as e:
            logger.error(f"Error in matchmaking disconnect: {e}")
    
    async def receive(self, text_data: str):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 更新心跳
            self.update_heartbeat()
            
            if message_type == 'JOIN_QUEUE':
                await self._handle_join_queue(data)
            elif message_type == 'LEAVE_QUEUE':
                await self._handle_leave_queue(data)
            elif message_type == 'GET_STATUS':
                await self._handle_get_status(data)
            elif message_type == 'HEARTBEAT':
                await self.handle_heartbeat(data)
            else:
                await self._send_error('INVALID_MESSAGE_TYPE', f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError:
            await self._send_error('INVALID_JSON', 'Invalid JSON format')
        except Exception as e:
            logger.error(f"Error in matchmaking receive: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
    
    async def _handle_join_queue(self, data: Dict[str, Any]):
        """处理加入匹配队列"""
        try:
            payload = data.get('payload', {})
            game_type = payload.get('game_type', 'ranked')  # ranked 或 casual
            
            # 获取用户 Elo（从数据库）
            user_elo = await self._get_user_elo()
            
            # 创建队列用户 - 使用 QueueUser 定义的正确参数
            import time
            queue_user = QueueUser(
                user_id=self.user['id'],
                rating=user_elo,
                joined_at=time.time(),
                search_range=100,  # INITIAL_SEARCH_RANGE
                game_type=game_type
            )
            
            # 加入队列
            success = await self._add_to_queue(queue_user)
            
            if success:
                self.user_queue_data = queue_user
                
                # 发送加入成功响应
                await self.send(text_data=self._format_message(
                    'queue_joined',
                    {
                        'success': True,
                        'game_type': game_type,
                        'rating': user_elo,
                        'queue_position': await self._get_queue_position(),
                        'estimated_wait_time': await self._estimate_wait_time()
                    }
                ))
                
                # 广播队列状态更新
                await self._broadcast_queue_status()
                
                # 开始匹配循环
                # 实际实现应该使用 Celery 任务或后台循环
                # 这里简化处理
                
            else:
                await self._send_error('QUEUE_JOIN_FAILED', 'Failed to join queue')
                
        except Exception as e:
            logger.error(f"Error joining queue: {e}")
            await self._send_error('QUEUE_JOIN_ERROR', str(e))
    
    async def _handle_leave_queue(self, data: Dict[str, Any]):
        """处理退出匹配队列"""
        try:
            success = await self._remove_from_queue()
            
            if success:
                self.user_queue_data = None
                
                # 发送退出成功响应
                await self.send(text_data=self._format_message(
                    'queue_left',
                    {
                        'success': True
                    }
                ))
                
                # 广播队列状态更新
                await self._broadcast_queue_status()
            else:
                await self._send_error('QUEUE_LEAVE_FAILED', 'Not in queue')
                
        except Exception as e:
            logger.error(f"Error leaving queue: {e}")
            await self._send_error('QUEUE_LEAVE_ERROR', str(e))
    
    async def _handle_get_status(self, data: Dict[str, Any]):
        """处理获取队列状态"""
        try:
            status = await self._get_queue_status()
            
            await self.send(text_data=self._format_message(
                'queue_status',
                status
            ))
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            await self._send_error('STATUS_ERROR', str(e))
    
    async def _add_to_queue(self, queue_user: QueueUser) -> bool:
        """
        添加用户到队列
        
        Args:
            queue_user: 队列用户对象
        
        Returns:
            是否成功
        """
        try:
            # 添加到 Redis 队列
            success = self.queue.join_queue(
                user_id=queue_user.user_id,
                rating=queue_user.rating,
                game_type=queue_user.game_type
            )
            
            if success:
                # 同时保存到数据库（用于持久化）
                await self._save_queue_record(queue_user)
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            return False
    
    async def _remove_from_queue(self) -> bool:
        """
        从队列移除用户
        
        Returns:
            是否成功
        """
        try:
            if not self.user_queue_data:
                return False
            
            # 从 Redis 队列移除
            success = self.queue.leave_queue(
                user_id=self.user['id'],
                game_type=self.user_queue_data.game_type
            )
            
            if success:
                # 从数据库标记为退出
                await self._update_queue_record_status('cancelled')
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing from queue: {e}")
            return False
    
    async def _get_queue_position(self) -> int:
        """获取队列位置"""
        try:
            game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
            queue_info = self.queue.get_queue_position(self.user['id'], game_type)
            return queue_info.get('position', -1)
        except Exception:
            return -1
    
    async def _estimate_wait_time(self) -> int:
        """预估等待时间（秒）"""
        try:
            game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
            queue_info = self.queue.get_queue_position(self.user['id'], game_type)
            return int(queue_info.get('wait_time', 0))
        except Exception:
            return -1
    
    async def _get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
            stats = self.queue.get_queue_stats(game_type)
            position = await self._get_queue_position()
            estimated_wait = await self._estimate_wait_time()
            
            return {
                'total_in_queue': stats.get('total_players', 0),
                'your_position': position if self.user_queue_data else None,
                'estimated_wait_time': estimated_wait if self.user_queue_data else None,
                'in_queue': self.user_queue_data is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {}
    
    async def _broadcast_queue_status(self):
        """广播队列状态更新"""
        try:
            status = await self._get_queue_status()
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'queue_status_update',
                    'data': status
                }
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting queue status: {e}")
    
    @database_sync_to_async
    def _get_user_elo(self) -> int:
        """获取用户 Elo 等级分"""
        try:
            from users.models import User
            user = User.objects.get(id=self.user['id'])
            return user.elo_rating
        except Exception:
            return 1500  # 默认分数
    
    @database_sync_to_async
    def _save_queue_record(self, queue_user: QueueUser):
        """保存队列记录到数据库"""
        try:
            from .models import MatchQueue, MatchQueueStatus
            MatchQueue.objects.create(
                user_id=queue_user.user_id,
                status=MatchQueueStatus.WAITING,
                game_type=queue_user.game_type,
                rating=queue_user.rating
            )
        except Exception as e:
            logger.error(f"Error saving queue record: {e}")
    
    @database_sync_to_async
    def _update_queue_record_status(self, status: str):
        """更新队列记录状态"""
        try:
            from .models import MatchQueue, MatchQueueStatus
            record = MatchQueue.objects.filter(
                user_id=self.user['id'],
                status=MatchQueueStatus.WAITING
            ).order_by('-created_at').first()
            
            if record:
                record.status = status
                record.save()
        except Exception as e:
            logger.error(f"Error updating queue record: {e}")
    
    # Channel layer 消息处理器
    async def queue_status_update(self, event):
        """广播队列状态更新"""
        await self.send(text_data=self._format_message(
            'queue_status',
            event['data']
        ))
    
    async def match_found(self, event):
        """匹配成功通知"""
        await self.send(text_data=self._format_message(
            'match_found',
            {
                'success': True,
                'game_id': event['data'].get('game_id'),
                'opponent': event['data'].get('opponent'),
                'game_type': event['data'].get('game_type')
            }
        ))
