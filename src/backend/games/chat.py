"""
聊天系统数据模型

包含：
- ChatMessage: 聊天消息模型
- ChatMessageManager: 聊天消息管理器
- MessageType: 消息类型枚举
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from django.db import models
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

from .models import Game


class MessageType(models.TextChoices):
    """消息类型枚举"""
    TEXT = 'text', '文本消息'
    SYSTEM = 'system', '系统消息'
    EMOJI = 'emoji', '表情消息'


class ChatMessage(models.Model):
    """
    聊天消息模型
    
    存储对局或房间内的聊天消息
    """
    id = models.BigAutoField(primary_key=True)
    
    # 消息 ID（用于 WebSocket 消息追踪）
    message_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # 外键关联
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        null=True,
        blank=True,
        help_text='关联的对局（对局聊天或观战聊天）'
    )
    
    # 发送者（系统消息可以为空）
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        null=True,
        blank=True,
        help_text='消息发送者（系统消息为空）'
    )
    
    # 消息内容
    content = models.TextField(help_text='消息内容')
    
    # 消息类型
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT
    )
    
    # 房间类型（区分对局内聊天和观战聊天）
    room_type = models.CharField(
        max_length=20,
        choices=[
            ('game', '对局房间'),
            ('spectator', '观战房间'),
        ],
        default='game',
        help_text='聊天房间类型'
    )
    
    # 消息状态
    is_deleted = models.BooleanField(default=False, help_text='是否已删除')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'room_type', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['message_uuid']),
            models.Index(fields=['is_deleted', '-created_at']),
        ]
    
    def __str__(self):
        sender_name = self.sender.username if self.sender else 'System'
        return f"ChatMessage from {sender_name} in {self.room_type}:{self.game_id}"
    
    @classmethod
    @sync_to_async(thread_sensitive=True)
    def async_create(cls, **kwargs):
        """异步创建消息"""
        return cls.objects.create(**kwargs)
    
    @classmethod
    @sync_to_async(thread_sensitive=True)
    def async_get(cls, **kwargs):
        """异步获取消息"""
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist:
            return None
    
    @sync_to_async(thread_sensitive=True)
    def async_delete(self):
        """异步删除消息"""
        self.is_deleted = True
        self.save()
        return True
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': str(self.message_uuid),
            'game_id': str(self.game.id) if self.game else None,
            'sender': {
                'id': str(self.sender.id) if self.sender else None,
                'username': self.sender.username if self.sender else 'System',
            } if self.sender else None,
            'content': self.content,
            'message_type': self.message_type,
            'room_type': self.room_type,
            'created_at': self.created_at.isoformat(),
        }


class ChatMessageManager:
    """
    聊天消息管理器
    
    提供聊天相关的高级操作
    """
    
    # 消息限流配置（秒）
    RATE_LIMIT_SECONDS = 2  # 每条消息间隔至少 2 秒
    MAX_MESSAGE_LENGTH = 500  # 最大消息长度
    
    # 简单的表情符号列表
    ALLOWED_EMOJIS = [
        '😀', '😂', '😍', '🥰', '😎', '🤔', '👍', '👎',
        '❤️', '🔥', '✨', '🎉', '🏆', '♟️', '🎯', '💪',
        '😅', '😭', '😱', '🙏', '💯', '🚀', '⭐', '🌟',
    ]
    
    @staticmethod
    def send_message_sync(
        game_id: str,
        user_id: str,
        content: str,
        message_type: str = 'text',
        room_type: str = 'game'
    ) -> Dict:
        """
        发送消息（同步版本）
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            content: 消息内容
            message_type: 消息类型（text/system/emoji）
            room_type: 房间类型（game/spectator）
            
        Returns:
            结果字典：{'success': bool, 'message': ChatMessage or None, 'error': str or None}
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 验证游戏存在
            from .models import Game
            game = Game.objects.get(id=UUID(game_id))
            
            # 验证用户存在
            user = User.objects.get(id=user_id)
            
            # 验证消息内容
            if not content or not content.strip():
                return {
                    'success': False,
                    'message': None,
                    'error': '消息内容不能为空'
                }
            
            # 限制消息长度
            if len(content) > ChatMessageManager.MAX_MESSAGE_LENGTH:
                return {
                    'success': False,
                    'message': None,
                    'error': f'消息长度不能超过 {ChatMessageManager.MAX_MESSAGE_LENGTH} 字符'
                }
            
            # 表情消息验证
            if message_type == 'emoji':
                # 检查是否是允许的表情
                is_valid_emoji = any(emoji in content for emoji in ChatMessageManager.ALLOWED_EMOJIS)
                if not is_valid_emoji:
                    return {
                        'success': False,
                        'message': None,
                        'error': '不支持的表情符号'
                    }
            
            # 限流检查（非系统消息）
            if message_type != 'system':
                last_message = ChatMessage.objects.filter(
                    game=game,
                    sender=user,
                    room_type=room_type,
                    created_at__gt=timezone.now() - timedelta(seconds=ChatMessageManager.RATE_LIMIT_SECONDS)
                ).first()
                
                if last_message:
                    return {
                        'success': False,
                        'message': None,
                        'error': '发送频率过快，请稍后再试'
                    }
            
            # 创建消息
            message = ChatMessage.objects.create(
                game=game,
                sender=user if message_type != 'system' else None,
                content=content.strip(),
                message_type=message_type,
                room_type=room_type
            )
            
            return {
                'success': True,
                'message': message,
                'error': None
            }
            
        except Game.DoesNotExist:
            return {
                'success': False,
                'message': None,
                'error': '游戏不存在'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'message': None,
                'error': '用户不存在'
            }
        except Exception as e:
            return {
                'success': False,
                'message': None,
                'error': str(e)
            }
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def send_message(
        game_id: str,
        user_id: str,
        content: str,
        message_type: str = 'text',
        room_type: str = 'game'
    ) -> Dict:
        """发送消息（异步版本）"""
        return ChatMessageManager.send_message_sync(
            game_id, user_id, content, message_type, room_type
        )
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def get_message_history(
        game_id: str,
        room_type: str = 'game',
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[Dict]:
        """
        获取消息历史
        
        Args:
            game_id: 游戏 ID
            room_type: 房间类型
            limit: 返回数量限制
            before: 分页游标（消息 created_at ISO 格式）
            
        Returns:
            消息列表（按时间正序）
        """
        from uuid import UUID
        
        try:
            # 基础查询
            query = ChatMessage.objects.filter(
                game_id=UUID(game_id),
                room_type=room_type,
                is_deleted=False
            ).select_related('sender')
            
            # 分页
            if before:
                query = query.filter(created_at__lt=before)
            
            # 获取消息（倒序取 limit 条，然后反转成正序）
            messages = list(query.order_by('-created_at')[:limit])
            messages.reverse()
            
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            return []
    
    @staticmethod
    def get_message_history_sync(
        game_id: str,
        room_type: str = 'game',
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[Dict]:
        """
        获取消息历史（同步版本）
        
        Args:
            game_id: 游戏 ID
            room_type: 房间类型
            limit: 返回数量限制
            before: 分页游标
            
        Returns:
            消息列表（按时间正序）
        """
        from uuid import UUID
        from django.utils import timezone
        
        try:
            # 基础查询
            query = ChatMessage.objects.filter(
                game_id=UUID(game_id),
                room_type=room_type,
                is_deleted=False
            ).select_related('sender')
            
            # 分页
            if before:
                query = query.filter(created_at__lt=before)
            
            # 获取消息（倒序取 limit 条，然后反转成正序）
            messages = list(query.order_by('-created_at')[:limit])
            messages.reverse()
            
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            return []
    
    @staticmethod
    def get_message_count_sync(game_id: str, room_type: str = 'game') -> int:
        """
        获取消息数量（同步版本）
        
        Args:
            game_id: 游戏 ID
            room_type: 房间类型
            
        Returns:
            消息数量
        """
        from uuid import UUID
        
        try:
            return ChatMessage.objects.filter(
                game_id=UUID(game_id),
                room_type=room_type,
                is_deleted=False
            ).count()
        except Exception:
            return 0
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def get_message_count(game_id: str, room_type: str = 'game') -> int:
        """
        获取消息数量
        
        Args:
            game_id: 游戏 ID
            room_type: 房间类型
            
        Returns:
            消息数量
        """
        from uuid import UUID
        
        try:
            return ChatMessage.objects.filter(
                game_id=UUID(game_id),
                room_type=room_type,
                is_deleted=False
            ).count()
        except Exception:
            return 0
    
    @staticmethod
    def delete_message_sync(message_uuid: str, user_id: str) -> Dict:
        """
        删除消息（同步版本）
        
        Args:
            message_uuid: 消息 UUID
            user_id: 用户 ID
            
        Returns:
            结果字典
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 获取消息
            message = ChatMessage.objects.get(message_uuid=UUID(message_uuid))
            
            # 验证权限
            user = User.objects.get(id=user_id)
            is_sender = message.sender and str(message.sender.id) == str(user_id)
            is_staff = user.is_staff
            
            if not is_sender and not is_staff:
                return {
                    'success': False,
                    'error': '无权限删除此消息'
                }
            
            # 软删除
            message.is_deleted = True
            message.save()
            
            return {
                'success': True,
                'message': '消息已删除'
            }
            
        except ChatMessage.DoesNotExist:
            return {
                'success': False,
                'error': '消息不存在'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'error': '用户不存在'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def delete_message(message_uuid: str, user_id: str) -> Dict:
        """
        删除消息
        
        Args:
            message_uuid: 消息 UUID
            user_id: 用户 ID（只有发送者或管理员可删除）
            
        Returns:
            结果字典
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 获取消息
            message = ChatMessage.objects.get(message_uuid=UUID(message_uuid))
            
            # 验证权限
            user = User.objects.get(id=user_id)
            is_sender = message.sender and str(message.sender.id) == str(user_id)
            is_staff = user.is_staff
            
            if not is_sender and not is_staff:
                return {
                    'success': False,
                    'error': '无权限删除此消息'
                }
            
            # 软删除
            message.is_deleted = True
            message.save()
            
            return {
                'success': True,
                'message': '消息已删除'
            }
            
        except ChatMessage.DoesNotExist:
            return {
                'success': False,
                'error': '消息不存在'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'error': '用户不存在'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def cleanup_old_messages_sync(game_id: str, days: int = 7) -> int:
        """
        清理旧消息（同步版本）
        
        Args:
            game_id: 游戏 ID
            days: 保留天数
            
        Returns:
            清理的数量
        """
        from uuid import UUID
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 软删除旧消息
            result = ChatMessage.objects.filter(
                game_id=UUID(game_id),
                created_at__lt=cutoff_date
            ).update(is_deleted=True)
            
            return result
            
        except Exception:
            return 0
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def cleanup_old_messages(game_id: str, days: int = 7) -> int:
        """清理旧消息（异步包装）"""
        return ChatMessageManager.cleanup_old_messages_sync(game_id, days)
    
    @staticmethod
    def is_valid_emoji(content: str) -> bool:
        """
        检查是否是有效的表情消息
        
        Args:
            content: 消息内容
            
        Returns:
            是否有效
        """
        return any(emoji in content for emoji in ChatMessageManager.ALLOWED_EMOJIS)
