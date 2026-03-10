"""
棋局分享服务

实现棋局分享的核心逻辑：
- 创建分享链接
- 验证分享密码
- 记录分享统计
- 管理分享生命周期
"""
import logging
from typing import Optional, Tuple
from django.utils import timezone
from datetime import timedelta

from games.models import Game, GameShare

logger = logging.getLogger(__name__)


class ShareService:
    """棋局分享服务类"""
    
    # 默认过期时间（7 天）
    DEFAULT_EXPIRY_DAYS = 7
    
    def __init__(self):
        pass
    
    def create_share(
        self,
        game: Game,
        user,
        share_type: str = 'public',
        password: str = '',
        expiry_days: int = None,
        description: str = ''
    ) -> GameShare:
        """
        创建棋局分享
        
        Args:
            game: 游戏对局
            user: 分享用户
            share_type: 分享类型（public/private/link）
            password: 分享密码（私密分享需要）
            expiry_days: 过期天数（默认 7 天）
            description: 分享说明
            
        Returns:
            GameShare 对象
        """
        # 验证用户权限（只有对局参与者可以分享）
        if game.player_red != user and game.player_black != user:
            logger.warning(f"用户 {user.username} 无权分享游戏 {game.id}")
            return None
        
        # 计算过期时间
        if expiry_days is None:
            expiry_days = self.DEFAULT_EXPIRY_DAYS
        
        expires_at = timezone.now() + timedelta(days=expiry_days) if expiry_days > 0 else None
        
        # 创建分享记录
        share = GameShare.objects.create(
            game=game,
            shared_by=user,
            share_type=share_type,
            share_password=password if share_type == 'private' else '',
            expires_at=expires_at,
            description=description
        )
        
        logger.info(f"创建棋局分享：#{share.id} - Game {game.id} - {share.share_type}")
        
        return share
    
    def get_share_by_token(self, token: str) -> Optional[GameShare]:
        """
        通过分享令牌获取分享记录
        
        Args:
            token: 分享令牌
            
        Returns:
            GameShare 对象或 None
        """
        try:
            share = GameShare.objects.get(share_token=token)
            
            # 检查是否有效
            if not share.is_active:
                logger.warning(f"分享链接已禁用：#{share.id}")
                return None
            
            # 检查是否过期
            if share.is_expired():
                logger.warning(f"分享链接已过期：#{share.id}")
                return None
            
            return share
            
        except GameShare.DoesNotExist:
            logger.warning(f"分享链接不存在：{token}")
            return None
    
    def verify_password(self, share: GameShare, password: str) -> bool:
        """
        验证分享密码
        
        Args:
            share: 分享记录
            password: 密码
            
        Returns:
            是否匹配
        """
        if share.share_type != 'private':
            return True  # 非私密分享不需要密码
        
        return share.share_password == password
    
    def record_view(self, share: GameShare):
        """
        记录浏览次数
        
        Args:
            share: 分享记录
        """
        share.increment_view_count()
        logger.debug(f"分享浏览：#{share.id} - 当前浏览：{share.view_count}")
    
    def deactivate_share(self, share: GameShare, user) -> bool:
        """
        禁用分享链接
        
        Args:
            share: 分享记录
            user: 操作用户
            
        Returns:
            是否成功
        """
        # 验证权限（只有分享者可以禁用）
        if share.shared_by != user:
            logger.warning(f"用户 {user.username} 无权禁用分享 #{share.id}")
            return False
        
        share.is_active = False
        share.save(update_fields=['is_active', 'updated_at'])
        
        logger.info(f"禁用分享链接：#{share.id}")
        return True
    
    def get_user_shares(self, user, limit: int = 20) -> list:
        """
        获取用户的分享列表
        
        Args:
            user: 用户
            limit: 数量限制
            
        Returns:
            分享列表
        """
        return GameShare.objects.filter(
            shared_by=user
        ).select_related('game').order_by('-created_at')[:limit]
    
    def get_game_shares(self, game: Game) -> list:
        """
        获取游戏的所有分享
        
        Args:
            game: 游戏对局
            
        Returns:
            分享列表
        """
        return GameShare.objects.filter(
            game=game
        ).order_by('-created_at')
    
    def cleanup_expired_shares(self) -> int:
        """
        清理过期的分享记录
        
        Returns:
            清理数量
        """
        expired_shares = GameShare.objects.filter(
            is_active=True,
            expires_at__isnull=False,
            expires_at__lt=timezone.now()
        )
        
        count = expired_shares.count()
        expired_shares.update(is_active=False)
        
        logger.info(f"清理过期分享：{count}个")
        return count


# 全局单例
_share_service = None

def get_share_service() -> ShareService:
    """获取分享服务单例"""
    global _share_service
    if _share_service is None:
        _share_service = ShareService()
    return _share_service
