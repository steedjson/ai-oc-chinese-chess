"""
匹配队列管理

使用 Redis Sorted Set 实现匹配队列，支持按 Elo 分段管理
"""
import time
import json
from typing import Optional, List, Dict
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
import redis


# 常量配置
MATCH_TIMEOUT = getattr(settings, 'MATCHMAKING_TIMEOUT', 180)  # 3 分钟
SEARCH_EXPANSION_INTERVAL = getattr(settings, 'MATCHMAKING_EXPANSION_INTERVAL', 30)  # 30 秒
INITIAL_SEARCH_RANGE = getattr(settings, 'MATCHMAKING_INITIAL_RANGE', 100)  # 初始搜索范围
SEARCH_EXPANSION = getattr(settings, 'MATCHMAKING_EXPANSION', 50)  # 每次扩大范围
MAX_SEARCH_RANGE = getattr(settings, 'MATCHMAKING_MAX_RANGE', 300)  # 最大搜索范围


@dataclass
class QueueUser:
    """队列中的用户信息"""
    user_id: str
    rating: int
    joined_at: float
    search_range: int
    game_type: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueueUser':
        """从字典创建"""
        return cls(
            user_id=data.get('user_id', ''),
            rating=int(data.get('rating', 1500)),
            joined_at=float(data.get('joined_at', time.time())),
            search_range=int(data.get('search_range', INITIAL_SEARCH_RANGE)),
            game_type=data.get('game_type', 'online')
        )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'rating': self.rating,
            'joined_at': self.joined_at,
            'search_range': self.search_range,
            'game_type': self.game_type
        }


class MatchmakingQueue:
    """
    匹配队列管理
    
    使用 Redis Sorted Set 实现：
    - Key: matchmaking:queue:{game_type}
    - Member: user_id
    - Score: rating (天梯分)
    
    用户元数据使用 Hash 存储：
    - Key: matchmaking:user:{user_id}
    - Fields: rating, joined_at, search_range, game_type
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.queue_prefix = "matchmaking:queue"
        self.user_prefix = "matchmaking:user"
        self.lock_prefix = "matchmaking:lock"
    
    def join_queue(
        self,
        user_id: str,
        rating: int,
        game_type: str = 'online'
    ) -> bool:
        """
        加入匹配队列
        
        Args:
            user_id: 用户 ID
            rating: 天梯分
            game_type: 游戏类型
        
        Returns:
            bool: 是否成功加入
        """
        # 检查是否已在队列中
        if self.is_in_queue(user_id, game_type):
            return False
        
        # 使用分布式锁防止并发
        lock_key = f"{self.lock_prefix}:{user_id}:{game_type}"
        if not self.redis.set(lock_key, "1", nx=True, ex=10):
            return False
        
        try:
            queue_key = f"{self.queue_prefix}:{game_type}"
            user_key = f"{self.user_prefix}:{user_id}"
            
            # 添加到 Sorted Set（分数=天梯分）
            self.redis.zadd(queue_key, {user_id: rating})
            
            # 存储用户元数据
            user_data = QueueUser(
                user_id=user_id,
                rating=rating,
                joined_at=time.time(),
                search_range=INITIAL_SEARCH_RANGE,
                game_type=game_type
            )
            
            self.redis.hset(user_key, mapping=user_data.to_dict())
            self.redis.expire(user_key, MATCH_TIMEOUT + 60)  # 超时 + 缓冲时间
            
            return True
        finally:
            self.redis.delete(lock_key)
    
    def leave_queue(self, user_id: str, game_type: str = 'online') -> bool:
        """
        离开匹配队列
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            bool: 是否成功离开
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 从队列移除
        removed = self.redis.zrem(queue_key, user_id)
        
        # 删除用户数据
        self.redis.delete(user_key)
        
        return removed > 0
    
    def is_in_queue(self, user_id: str, game_type: str = 'online') -> bool:
        """
        检查用户是否在队列中
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            bool: 是否在队列中
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        return self.redis.zrank(queue_key, user_id) is not None
    
    def search_opponent(
        self,
        user_id: str,
        game_type: str = 'online'
    ) -> Optional[str]:
        """
        搜索对手
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            Optional[str]: 对手用户 ID，未找到返回 None
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 获取用户信息
        user_data = self.get_user_data(user_id)
        if not user_data:
            return None
        
        rating = user_data.rating
        search_range = user_data.search_range
        
        # 搜索范围内的对手（排除自己）
        min_rating = rating - search_range
        max_rating = rating + search_range
        
        opponents = self.redis.zrangebyscore(
            queue_key,
            min_rating,
            max_rating,
            start=0,
            num=10  # 最多返回 10 个候选
        )
        
        # 过滤自己并转换为字符串
        opponent_ids = [
            opp.decode() if isinstance(opp, bytes) else opp
            for opp in opponents
            if (opp.decode() if isinstance(opp, bytes) else opp) != user_id
        ]
        
        if opponent_ids:
            # 选择最接近的对手（第一个）
            return opponent_ids[0]
        
        return None
    
    def expand_search_range(
        self,
        user_id: str,
        game_type: str = 'online',
        expansion: int = SEARCH_EXPANSION,
        max_range: int = MAX_SEARCH_RANGE
    ) -> int:
        """
        扩大搜索范围
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
            expansion: 扩展值
            max_range: 最大范围
        
        Returns:
            int: 新的搜索范围
        """
        user_key = f"{self.user_prefix}:{user_id}"
        
        current_range = int(self.redis.hget(user_key, 'search_range') or INITIAL_SEARCH_RANGE)
        new_range = min(current_range + expansion, max_range)
        
        self.redis.hset(user_key, 'search_range', new_range)
        
        return new_range
    
    def get_queue_position(
        self,
        user_id: str,
        game_type: str = 'online'
    ) -> Dict:
        """
        获取队列位置信息
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            Dict: 队列信息
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 用户排名
        rank = self.redis.zrank(queue_key, user_id)
        
        # 队列总人数
        total = self.redis.zcard(queue_key)
        
        # 用户信息
        user_data = self.redis.hgetall(user_key)
        
        # 计算等待时间
        joined_at = float(user_data.get(b'joined_at', time.time()))
        wait_time = time.time() - joined_at
        
        return {
            'position': (rank + 1) if rank is not None else 0,
            'total': total,
            'search_range': int(user_data.get(b'search_range', INITIAL_SEARCH_RANGE)),
            'wait_time': wait_time
        }
    
    def get_queue_stats(self, game_type: str = 'online') -> Dict:
        """
        获取队列统计信息
        
        Args:
            game_type: 游戏类型
        
        Returns:
            Dict: 统计信息
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        
        # 按分数段统计
        ranges = [
            (0, 1000, "0-1000"),
            (1001, 1200, "1001-1200"),
            (1201, 1400, "1201-1400"),
            (1401, 1600, "1401-1600"),
            (1601, 1800, "1601-1800"),
            (1801, 99999, "1801+")
        ]
        
        stats = []
        for min_r, max_r, label in ranges:
            count = self.redis.zcount(queue_key, min_r, max_r)
            stats.append({'range': label, 'players': count})
        
        # 总人数
        total = self.redis.zcard(queue_key)
        
        # 计算平均等待时间
        avg_wait = self._calculate_avg_wait_time(game_type)
        
        return {
            'total_players': total,
            'rating_ranges': stats,
            'avg_wait_time': avg_wait
        }
    
    def get_user_data(self, user_id: str) -> Optional[QueueUser]:
        """
        获取用户队列数据
        
        Args:
            user_id: 用户 ID
        
        Returns:
            Optional[QueueUser]: 用户数据
        """
        user_key = f"{self.user_prefix}:{user_id}"
        data = self.redis.hgetall(user_key)
        
        if not data:
            return None
        
        # 转换字节为字符串
        decoded_data = {
            k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()
        }
        
        return QueueUser.from_dict(decoded_data)
    
    def is_match_timeout(self, joined_at: float) -> bool:
        """
        检查是否匹配超时
        
        Args:
            joined_at: 加入时间戳
        
        Returns:
            bool: 是否超时
        """
        elapsed = time.time() - joined_at
        return elapsed > MATCH_TIMEOUT
    
    def _calculate_avg_wait_time(self, game_type: str) -> int:
        """
        计算平均等待时间
        
        Args:
            game_type: 游戏类型
        
        Returns:
            int: 平均等待时间（秒）
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        
        # 获取所有玩家
        all_players = self.redis.zrange(queue_key, 0, -1, withscores=True)
        
        if not all_players:
            return 0
        
        total_wait = 0
        count = 0
        
        for user_id, _ in all_players:
            user_id_str = user_id.decode() if isinstance(user_id, bytes) else user_id
            user_data = self.get_user_data(user_id_str)
            
            if user_data:
                wait = time.time() - user_data.joined_at
                total_wait += wait
                count += 1
        
        return int(total_wait / count) if count > 0 else 0
    
    def get_all_queued_users(
        self,
        game_type: str = 'online',
        limit: int = 100
    ) -> List[QueueUser]:
        """
        获取所有队列中的用户
        
        Args:
            game_type: 游戏类型
            limit: 返回数量限制
        
        Returns:
            List[QueueUser]: 用户列表
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        
        # 获取所有用户 ID
        user_ids = self.redis.zrange(queue_key, 0, limit - 1)
        
        users = []
        for user_id in user_ids:
            user_id_str = user_id.decode() if isinstance(user_id, bytes) else user_id
            user_data = self.get_user_data(user_id_str)
            
            if user_data:
                users.append(user_data)
        
        return users
    
    def clear_expired_queues(self):
        """
        清理超期的队列
        
        应该定期调用（如每分钟）
        """
        # 获取所有游戏类型的队列
        # 实际实现中可以从配置获取游戏类型列表
        game_types = ['online', 'ranked', 'casual']
        
        for game_type in game_types:
            queue_key = f"{self.queue_prefix}:{game_type}"
            
            # 获取所有用户
            user_ids = self.redis.zrange(queue_key, 0, -1)
            
            for user_id in user_ids:
                user_id_str = user_id.decode() if isinstance(user_id, bytes) else user_id
                user_data = self.get_user_data(user_id_str)
                
                if user_data and self.is_match_timeout(user_data.joined_at):
                    # 超时，移除
                    self.leave_queue(user_id_str, game_type)
