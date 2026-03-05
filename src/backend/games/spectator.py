"""
观战系统数据模型

包含：
- Spectator: 观战者模型
- SpectatorManager: 观战管理器
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from django.db import models
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async

from .models import Game


class SpectatorStatus(models.TextChoices):
    """观战状态枚举"""
    WATCHING = 'watching', '观战中'
    LEFT = 'left', '已离开'
    KICKED = 'kicked', '被踢出'


class Spectator(models.Model):
    """
    观战者模型
    
    记录用户观战对局的信息
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 外键关联
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='spectators'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='spectated_games'
    )
    
    # 观战状态
    status = models.CharField(
        max_length=20,
        choices=SpectatorStatus.choices,
        default=SpectatorStatus.WATCHING
    )
    
    # 观战信息
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text='观战时长（秒）')
    
    # 观战设置
    is_anonymous = models.BooleanField(default=False, help_text='是否匿名观战')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'spectators'
        ordering = ['-joined_at']
        unique_together = ['game', 'user']
        indexes = [
            models.Index(fields=['game', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-joined_at']),
        ]
    
    def __str__(self):
        return f"Spectator {self.user.username} watching Game {self.game.id}"
    
    def save(self, *args, **kwargs):
        """保存时自动计算时长"""
        if self.status != SpectatorStatus.WATCHING and self.left_at is None:
            self.left_at = timezone.now()
        
        if self.left_at and self.duration is None:
            self.duration = int((self.left_at - self.joined_at).total_seconds())
        
        super().save(*args, **kwargs)
    
    @classmethod
    @sync_to_async(thread_sensitive=True)
    def async_create(cls, **kwargs):
        """异步创建观战记录"""
        return cls.objects.create(**kwargs)
    
    @classmethod
    @sync_to_async(thread_sensitive=True)
    def async_get(cls, **kwargs):
        """异步获取观战记录"""
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist:
            return None
    
    @sync_to_async(thread_sensitive=True)
    def async_delete(self):
        """异步删除观战记录"""
        return self.delete()


class SpectatorManager:
    """
    观战管理器
    
    提供观战相关的高级操作
    """
    
    @staticmethod
    def join_spectate_sync(game_id: str, user_id: str, is_anonymous: bool = False) -> Dict:
        """
        加入观战（同步版本）
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            is_anonymous: 是否匿名观战
            
        Returns:
            结果字典：{'success': bool, 'spectator': Spectator or None, 'error': str or None}
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 验证游戏存在
            game = Game.objects.get(id=UUID(game_id))
            
            # 验证游戏状态（只能观战进行中的游戏）
            if game.status not in ['playing', 'pending']:
                return {
                    'success': False,
                    'spectator': None,
                    'error': '游戏未进行中，无法观战'
                }
            
            # 验证用户存在
            user = User.objects.get(id=user_id)
            
            # 检查是否已经在观战
            existing = Spectator.objects.filter(
                game=game,
                user=user,
                status=SpectatorStatus.WATCHING
            ).first()
            
            if existing:
                return {
                    'success': True,
                    'spectator': existing,
                    'error': None,
                    'message': '已在观战中'
                }
            
            # 检查用户是否是游戏参与者（参与者不能同时是观战者）
            if (game.red_player and str(game.red_player.id) == str(user.id)) or \
               (game.black_player and str(game.black_player.id) == str(user.id)):
                return {
                    'success': False,
                    'spectator': None,
                    'error': '游戏参与者不能观战'
                }
            
            # 创建观战记录
            spectator = Spectator.objects.create(
                game=game,
                user=user,
                is_anonymous=is_anonymous
            )
            
            return {
                'success': True,
                'spectator': spectator,
                'error': None
            }
            
        except Game.DoesNotExist:
            return {
                'success': False,
                'spectator': None,
                'error': '游戏不存在'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'spectator': None,
                'error': '用户不存在'
            }
        except Exception as e:
            return {
                'success': False,
                'spectator': None,
                'error': str(e)
            }
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def join_spectate(game_id: str, user_id: str, is_anonymous: bool = False) -> Dict:
        """加入观战（异步版本）"""
        return SpectatorManager.join_spectate_sync(game_id, user_id, is_anonymous)
        """
        加入观战
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            is_anonymous: 是否匿名观战
            
        Returns:
            结果字典：{'success': bool, 'spectator': Spectator or None, 'error': str or None}
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 验证游戏存在
            game = Game.objects.get(id=UUID(game_id))
            
            # 验证游戏状态（只能观战进行中的游戏）
            if game.status not in ['playing', 'pending']:
                return {
                    'success': False,
                    'spectator': None,
                    'error': '游戏未进行中，无法观战'
                }
            
            # 验证用户存在
            user = User.objects.get(id=user_id)
            
            # 检查是否已经在观战
            existing = Spectator.objects.filter(
                game=game,
                user=user,
                status=SpectatorStatus.WATCHING
            ).first()
            
            if existing:
                return {
                    'success': True,
                    'spectator': existing,
                    'error': None,
                    'message': '已在观战中'
                }
            
            # 检查用户是否是游戏参与者（参与者不能同时是观战者）
            if (game.red_player and str(game.red_player.id) == str(user.id)) or \
               (game.black_player and str(game.black_player.id) == str(user.id)):
                return {
                    'success': False,
                    'spectator': None,
                    'error': '游戏参与者不能观战'
                }
            
            # 创建观战记录
            spectator = Spectator.objects.create(
                game=game,
                user=user,
                is_anonymous=is_anonymous
            )
            
            return {
                'success': True,
                'spectator': spectator,
                'error': None
            }
            
        except Game.DoesNotExist:
            return {
                'success': False,
                'spectator': None,
                'error': '游戏不存在'
            }
        except User.DoesNotExist:
            return {
                'success': False,
                'spectator': None,
                'error': '用户不存在'
            }
        except Exception as e:
            return {
                'success': False,
                'spectator': None,
                'error': str(e)
            }
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def leave_spectate(game_id: str, user_id: str) -> Dict:
        """
        离开观战
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            结果字典
        """
        from uuid import UUID
        
        try:
            # 获取观战记录
            spectator = Spectator.objects.filter(
                game_id=UUID(game_id),
                user_id=user_id,
                status=SpectatorStatus.WATCHING
            ).first()
            
            if not spectator:
                return {
                    'success': False,
                    'error': '未在观战中'
                }
            
            # 更新状态
            spectator.status = SpectatorStatus.LEFT
            spectator.left_at = timezone.now()
            spectator.duration = int((spectator.left_at - spectator.joined_at).total_seconds())
            spectator.save()
            
            return {
                'success': True,
                'duration': spectator.duration
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def get_spectators(game_id: str, limit: int = 50) -> List[Dict]:
        """
        获取观战列表
        
        Args:
            game_id: 游戏 ID
            limit: 返回数量限制
            
        Returns:
            观战者列表
        """
        from uuid import UUID
        
        try:
            spectators = Spectator.objects.filter(
                game_id=UUID(game_id),
                status=SpectatorStatus.WATCHING
            ).select_related('user')[:limit]
            
            result = []
            for spec in spectators:
                result.append({
                    'id': str(spec.id),
                    'user_id': str(spec.user.id) if not spec.is_anonymous else None,
                    'username': spec.user.username if not spec.is_anonymous else '匿名用户',
                    'joined_at': spec.joined_at.isoformat(),
                    'duration': int((timezone.now() - spec.joined_at).total_seconds()) if spec.joined_at else 0,
                    'is_anonymous': spec.is_anonymous
                })
            
            return result
            
        except Exception as e:
            return []
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def get_spectator_count(game_id: str) -> int:
        """
        获取观战人数
        
        Args:
            game_id: 游戏 ID
            
        Returns:
            观战人数
        """
        from uuid import UUID
        
        try:
            return Spectator.objects.filter(
                game_id=UUID(game_id),
                status=SpectatorStatus.WATCHING
            ).count()
        except Exception:
            return 0
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def kick_spectator(game_id: str, spectator_id: str, operator_id: str) -> Dict:
        """
        踢出观战者（仅游戏创建者或管理员可用）
        
        Args:
            game_id: 游戏 ID
            spectator_id: 观战者 ID
            operator_id: 操作者 ID
            
        Returns:
            结果字典
        """
        from uuid import UUID
        from users.models import User
        
        try:
            # 验证操作者权限
            operator = User.objects.get(id=operator_id)
            game = Game.objects.get(id=UUID(game_id))
            
            # 只有游戏创建者（红方）或管理员可以踢人
            is_owner = game.red_player and str(game.red_player.id) == str(operator.id)
            if not is_owner and not operator.is_staff:
                return {
                    'success': False,
                    'error': '无权限执行此操作'
                }
            
            # 获取观战记录
            spectator = Spectator.objects.get(id=UUID(spectator_id), game=game)
            
            # 更新状态
            spectator.status = SpectatorStatus.KICKED
            spectator.left_at = timezone.now()
            spectator.duration = int((spectator.left_at - spectator.joined_at).total_seconds())
            spectator.save()
            
            return {
                'success': True,
                'message': f'已将 {spectator.user.username} 踢出观战'
            }
            
        except Spectator.DoesNotExist:
            return {
                'success': False,
                'error': '观战者不存在'
            }
        except Game.DoesNotExist:
            return {
                'success': False,
                'error': '游戏不存在'
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
    def cleanup_inactive_spectators_sync(game_id: str, timeout_minutes: int = 30) -> int:
        """
        清理不活跃的观战者（同步版本）
        
        Args:
            game_id: 游戏 ID
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            清理的数量
        """
        from uuid import UUID
        
        try:
            timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
            
            # 更新状态并获取影响行数
            result = Spectator.objects.filter(
                game_id=UUID(game_id),
                status=SpectatorStatus.WATCHING,
                updated_at__lt=timeout_threshold
            ).update(
                status=SpectatorStatus.LEFT,
                left_at=timezone.now()
            )
            
            return result
            
        except Exception:
            return 0
    
    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def cleanup_inactive_spectators(game_id: str, timeout_minutes: int = 30) -> int:
        """
        清理不活跃的观战者（异步包装）
        
        Args:
            game_id: 游戏 ID
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            清理的数量
        """
        return SpectatorManager.cleanup_inactive_spectators_sync(game_id, timeout_minutes)
