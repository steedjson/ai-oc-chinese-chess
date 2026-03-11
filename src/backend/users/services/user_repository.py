"""
User Repository - 用户数据仓库

提供用户数据的持久化操作：
- 用户创建、查询、更新、删除
- 用户状态管理
- 用户统计
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from users.models import User, UserProfile, UserStats, UserStatus


class UserRepository:
    """用户数据仓库类"""
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据 ID 获取用户
        
        Args:
            user_id: 用户 ID
        
        Returns:
            User 对象，未找到返回 None
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
        
        Returns:
            User 对象，未找到返回 None
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱
        
        Returns:
            User 对象，未找到返回 None
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def update_user_elo(self, user_id: str, new_elo: int) -> bool:
        """
        更新用户 Elo 等级分
        
        Args:
            user_id: 用户 ID
            new_elo: 新等级分
        
        Returns:
            bool: 是否成功
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.elo_rating = new_elo
            user.save()
            return True
            
        except Exception:
            return False
    
    def update_user_status(self, user_id: str, status: UserStatus) -> bool:
        """
        更新用户状态
        
        Args:
            user_id: 用户 ID
            status: 新状态
        
        Returns:
            bool: 是否成功
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.status = status
            user.save()
            return True
            
        except Exception:
            return False
    
    def get_top_players(self, limit: int = 10) -> List[User]:
        """
        获取顶级玩家（按 Elo 排序）
        
        Args:
            limit: 返回数量限制
        
        Returns:
            User 列表
        """
        return list(User.objects.filter(
            is_active=True,
            status=UserStatus.ACTIVE
        ).order_by('-elo_rating')[:limit])
    
    def get_active_users(self, limit: int = 100) -> List[User]:
        """
        获取活跃用户
        
        Args:
            limit: 返回数量限制
        
        Returns:
            User 列表
        """
        return list(User.objects.filter(
            is_active=True,
            status=UserStatus.ACTIVE
        )[:limit])
    
    def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户 ID
        
        Returns:
            bool: 是否成功
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.delete()
            return True
            
        except Exception:
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        获取用户档案
        
        Args:
            user_id: 用户 ID
        
        Returns:
            UserProfile 对象，未找到返回 None
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            return user.userprofile
            
        except UserProfile.DoesNotExist:
            return None
    
    def create_user_profile(
        self,
        user_id: str,
        bio: str = '',
        location: str = '',
        birthday: Optional[datetime] = None,
        gender: str = ''
    ) -> Optional[UserProfile]:
        """
        创建用户档案
        
        Args:
            user_id: 用户 ID
            bio: 个人简介
            location: 所在地
            birthday: 生日
            gender: 性别
        
        Returns:
            UserProfile 对象，失败返回 None
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            profile = UserProfile.objects.create(
                user=user,
                bio=bio,
                location=location,
                birthday=birthday,
                gender=gender
            )
            return profile
            
        except Exception:
            return None
    
    def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """
        获取用户统计
        
        Args:
            user_id: 用户 ID
        
        Returns:
            UserStats 对象，未找到返回 None
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            return user.userstats
            
        except UserStats.DoesNotExist:
            return None
    
    def create_user_stats(
        self,
        user_id: str,
        total_games: int = 0,
        wins: int = 0,
        losses: int = 0,
        draws: int = 0
    ) -> Optional[UserStats]:
        """
        创建用户统计
        
        Args:
            user_id: 用户 ID
            total_games: 总局数
            wins: 胜场
            losses: 负场
            draws: 平局
        
        Returns:
            UserStats 对象，失败返回 None
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            stats = UserStats.objects.create(
                user=user,
                total_games=total_games,
                wins=wins,
                losses=losses,
                draws=draws
            )
            return stats
            
        except Exception:
            return None
    
    def update_user_stats(
        self,
        user_id: str,
        total_games: Optional[int] = None,
        wins: Optional[int] = None,
        losses: Optional[int] = None,
        draws: Optional[int] = None
    ) -> bool:
        """
        更新用户统计
        
        Args:
            user_id: 用户 ID
            total_games: 总局数
            wins: 胜场
            losses: 负场
            draws: 平局
        
        Returns:
            bool: 是否成功
        """
        try:
            stats = self.get_user_stats(user_id)
            if not stats:
                return False
            
            if total_games is not None:
                stats.total_games = total_games
            if wins is not None:
                stats.wins = wins
            if losses is not None:
                stats.losses = losses
            if draws is not None:
                stats.draws = draws
            
            stats.save()  # 会自动计算胜率
            return True
            
        except Exception:
            return False
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """
        搜索用户
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            User 列表
        """
        return list(User.objects.filter(
            username__icontains=query,
            is_active=True
        )[:limit])
