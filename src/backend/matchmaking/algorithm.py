"""
匹配算法

实现基于 Elo 的匹配算法，支持动态搜索范围、优先匹配等待时间长的玩家、防止重复匹配
"""
import time
import asyncio
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from django.conf import settings
from django.utils import timezone
import redis

from .queue import MatchmakingQueue, QueueUser


# 常量配置
INITIAL_SEARCH_RANGE = getattr(settings, 'MATCHMAKING_INITIAL_RANGE', 100)
SEARCH_EXPANSION = getattr(settings, 'MATCHMAKING_EXPANSION', 50)
MAX_SEARCH_RANGE = getattr(settings, 'MATCHMAKING_MAX_RANGE', 300)
EXPANSION_INTERVAL = getattr(settings, 'MATCHMAKING_EXPANSION_INTERVAL', 30)
MATCH_TIMEOUT = getattr(settings, 'MATCHMAKING_TIMEOUT', 180)
MAX_REMATCH_INTERVAL = getattr(settings, 'MATCHMAKING_REMATCH_INTERVAL', 300)  # 5 分钟内不重复匹配


@dataclass
class MatchResult:
    """匹配结果"""
    user_id: str
    opponent_id: str
    game_id: Optional[str]
    user_rating: int
    opponent_rating: int
    rating_diff: int
    wait_time: float
    success: bool = True


class Matchmaker:
    """
    匹配器
    
    实现基于 Elo 的匹配算法：
    1. 初始搜索范围±100 分
    2. 每 30 秒扩大±50 分
    3. 最大搜索范围±300 分
    4. 优先匹配等待时间长的玩家
    5. 防止重复匹配（5 分钟内不遇到同一对手）
    """
    
    def __init__(self):
        self.queue = MatchmakingQueue()
        self.redis = redis.from_url(settings.REDIS_URL)
        self.config = self._load_config()
        
        # 最近对手缓存 key 前缀
        self.recent_opponents_prefix = "matchmaking:recent_opponents:"
    
    def _load_config(self) -> Dict:
        """加载匹配配置"""
        return {
            'initial_range': INITIAL_SEARCH_RANGE,
            'expansion': SEARCH_EXPANSION,
            'max_range': MAX_SEARCH_RANGE,
            'expansion_interval': EXPANSION_INTERVAL,
            'timeout': MATCH_TIMEOUT,
            'rematch_interval': MAX_REMATCH_INTERVAL
        }
    
    def find_opponent(
        self,
        user_id: str,
        game_type: str = 'online'
    ) -> Optional[MatchResult]:
        """
        寻找对手
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            Optional[MatchResult]: 匹配结果
        """
        # 获取用户数据
        user_data = self.queue.get_user_data(user_id)
        if not user_data:
            return None
        
        # 搜索对手
        opponent_id = self.queue.search_opponent(user_id, game_type)
        
        if not opponent_id:
            return None
        
        # 检查是否应该过滤（防止重复匹配）
        if self.should_filter_opponent(user_id, opponent_id):
            # 尝试找下一个对手
            return self._find_next_opponent(user_id, opponent_id, game_type)
        
        # 获取对手数据
        opponent_data = self.queue.get_user_data(opponent_id)
        if not opponent_data:
            return None
        
        # 计算等级分差
        rating_diff = abs(user_data.rating - opponent_data.rating)
        
        # 计算等待时间
        wait_time = time.time() - user_data.joined_at
        
        return MatchResult(
            user_id=user_id,
            opponent_id=opponent_id,
            game_id=None,
            user_rating=user_data.rating,
            opponent_rating=opponent_data.rating,
            rating_diff=rating_diff,
            wait_time=wait_time
        )
    
    def _find_next_opponent(
        self,
        user_id: str,
        exclude_opponent: str,
        game_type: str
    ) -> Optional[MatchResult]:
        """寻找下一个对手（排除指定对手）"""
        # 实际实现中可以从队列获取更多候选
        # 这里简化处理
        return None
    
    def should_expand_search(self, joined_at: float) -> bool:
        """
        判断是否应该扩大搜索范围
        
        Args:
            joined_at: 加入时间戳
        
        Returns:
            bool: 是否应该扩大
        """
        elapsed = time.time() - joined_at
        return elapsed >= self.config['expansion_interval']
    
    def calculate_dynamic_range(self, elapsed_seconds: float) -> int:
        """
        计算动态搜索范围
        
        Args:
            elapsed_seconds: 已等待秒数
        
        Returns:
            int: 搜索范围
        """
        # 计算扩大次数
        expansions = int(elapsed_seconds / self.config['expansion_interval'])
        
        # 计算新范围
        new_range = self.config['initial_range'] + (expansions * self.config['expansion'])
        
        # 限制在最大值
        return min(new_range, self.config['max_range'])
    
    def is_timeout(self, joined_at: float) -> bool:
        """
        检查是否超时
        
        Args:
            joined_at: 加入时间戳
        
        Returns:
            bool: 是否超时
        """
        elapsed = time.time() - joined_at
        return elapsed > self.config['timeout']
    
    def select_best_opponent(
        self,
        opponent_ids: List[str],
        user_rating: int
    ) -> Optional[str]:
        """
        选择最佳对手
        
        优先级：
        1. 等级分最接近
        2. 等待时间最长
        
        Args:
            opponent_ids: 对手 ID 列表
            user_rating: 用户等级分
        
        Returns:
            Optional[str]: 最佳对手 ID
        """
        if not opponent_ids:
            return None
        
        candidates = []
        
        for opp_id in opponent_ids:
            opp_data = self.queue.get_user_data(opp_id)
            if opp_data:
                rating_diff = abs(user_rating - opp_data.rating)
                wait_time = time.time() - opp_data.joined_at
                
                candidates.append({
                    'user_id': opp_id,
                    'rating': opp_data.rating,
                    'rating_diff': rating_diff,
                    'wait_time': wait_time
                })
        
        if not candidates:
            return None
        
        # 排序：先按分数差（升序），再按等待时间（降序）
        candidates.sort(key=lambda x: (x['rating_diff'], -x['wait_time']))
        
        return candidates[0]['user_id']
    
    def record_recent_opponent(self, user_id: str, opponent_id: str):
        """
        记录最近匹配的对手
        
        Args:
            user_id: 用户 ID
            opponent_id: 对手 ID
        """
        key = f"{self.recent_opponents_prefix}{user_id}"
        
        # 添加到集合
        self.redis.sadd(key, opponent_id)
        
        # 设置过期时间（5 分钟）
        self.redis.expire(key, self.config['rematch_interval'])
    
    def should_filter_opponent(self, user_id: str, opponent_id: str) -> bool:
        """
        检查是否应该过滤对手（防止重复匹配）
        
        Args:
            user_id: 用户 ID
            opponent_id: 对手 ID
        
        Returns:
            bool: 是否应该过滤
        """
        key = f"{self.recent_opponents_prefix}{user_id}"
        
        # 检查是否在最近对手集合中
        return self.redis.sismember(key, opponent_id)
    
    def get_wait_time_estimate(
        self,
        game_type: str,
        user_rating: int
    ) -> Dict:
        """
        获取等待时间预估
        
        Args:
            game_type: 游戏类型
            user_rating: 用户等级分
        
        Returns:
            Dict: 预估信息
        """
        stats = self.queue.get_queue_stats(game_type)
        
        # 根据队列人数和平均等待时间估算
        total_players = stats.get('total_players', 0)
        avg_wait = stats.get('avg_wait_time', 60)
        
        # 简单估算：队列人数越少，等待时间越长
        if total_players < 10:
            estimated = avg_wait * 3
        elif total_players < 30:
            estimated = avg_wait * 2
        else:
            estimated = avg_wait
        
        return {
            'estimated_seconds': int(estimated),
            'queue_size': total_players,
            'your_rating': user_rating
        }
    
    async def matchmaking_loop(
        self,
        user_id: str,
        game_type: str = 'online'
    ) -> Optional[MatchResult]:
        """
        匹配循环（异步）
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            Optional[MatchResult]: 匹配结果
        """
        start_time = time.time()
        
        while True:
            # 检查用户是否还在队列
            if not self.queue.is_in_queue(user_id, game_type):
                return None
            
            # 获取用户数据
            user_data = self.queue.get_user_data(user_id)
            if not user_data:
                return None
            
            # 检查是否超时
            if self.is_timeout(user_data.joined_at):
                # 超时处理
                await self._handle_timeout(user_id, game_type)
                return None
            
            # 搜索对手
            result = self.find_opponent(user_id, game_type)
            
            if result:
                # 找到对手，尝试匹配
                success = await self._try_match(result)
                if success:
                    return result
            
            # 扩大搜索范围
            elapsed = time.time() - user_data.joined_at
            if self.should_expand_search(user_data.joined_at):
                new_range = self.calculate_dynamic_range(elapsed)
                self.queue.expand_search_range(
                    user_id,
                    game_type,
                    expansion=SEARCH_EXPANSION,
                    max_range=MAX_SEARCH_RANGE
                )
            
            # 等待下次搜索
            await asyncio.sleep(self.config['expansion_interval'])
    
    async def _try_match(self, result: MatchResult) -> bool:
        """
        尝试匹配
        
        Args:
            result: 匹配结果
        
        Returns:
            bool: 是否匹配成功
        """
        # 使用分布式锁防止重复匹配
        lock_key = f"match:lock:{min(result.user_id, result.opponent_id)}:{max(result.user_id, result.opponent_id)}"
        
        if not self.redis.set(lock_key, "1", nx=True, ex=30):
            return False  # 已被其他进程处理
        
        try:
            # 检查对手是否还在队列
            if not self.queue.is_in_queue(result.opponent_id):
                return False
            
            # 双方确认匹配
            user_confirmed = await self._request_confirmation(result.user_id)
            opponent_confirmed = await self._request_confirmation(result.opponent_id)
            
            if user_confirmed and opponent_confirmed:
                # 创建游戏
                game_id = await self._create_game(result.user_id, result.opponent_id)
                result.game_id = game_id
                
                # 从队列移除
                self.queue.leave_queue(result.user_id)
                self.queue.leave_queue(result.opponent_id)
                
                # 记录最近对手
                self.record_recent_opponent(result.user_id, result.opponent_id)
                self.record_recent_opponent(result.opponent_id, result.user_id)
                
                # 发送匹配成功通知
                await self._send_match_success(result)
                
                return True
            
            return False
        finally:
            self.redis.delete(lock_key)
    
    async def _request_confirmation(self, user_id: str) -> bool:
        """
        请求匹配确认
        
        Args:
            user_id: 用户 ID
        
        Returns:
            bool: 是否确认
        """
        # P0 版本：自动确认
        # 后续可扩展为手动确认
        return True
    
    async def _create_game(self, user_id: str, opponent_id: str) -> str:
        """
        创建游戏对局
        
        Args:
            user_id: 用户 ID
            opponent_id: 对手 ID
        
        Returns:
            str: 游戏 ID
        """
        # 导入游戏服务
        from games.models import Game
        from django.db import transaction
        
        with transaction.atomic():
            # 创建游戏记录
            game = Game.objects.create(
                game_type='online',
                status='pending',
                is_rated=True
            )
            
            # 添加玩家（假设 Game 模型有 players 关联）
            # 实际实现根据 Game 模型结构调整
            game.red_player_id = user_id
            game.black_player_id = opponent_id
            game.save()
            
            return str(game.id)
    
    async def _handle_timeout(self, user_id: str, game_type: str):
        """
        处理超时
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        """
        # 从队列移除
        self.queue.leave_queue(user_id, game_type)
        
        # 发送超时通知
        await self._send_timeout_notification(user_id)
    
    async def _send_match_success(self, result: MatchResult):
        """
        发送匹配成功通知
        
        Args:
            result: 匹配结果
        """
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # 通知双方
        for user_id in [result.user_id, result.opponent_id]:
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                {
                    'type': 'match_found',
                    'data': {
                        'game_id': result.game_id,
                        'opponent_id': result.opponent_id if user_id == result.user_id else result.user_id,
                        'opponent_rating': result.opponent_rating if user_id == result.user_id else result.user_rating,
                        'your_side': 'red' if user_id == result.user_id else 'black'
                    }
                }
            )
    
    async def _send_timeout_notification(self, user_id: str):
        """
        发送超时通知
        
        Args:
            user_id: 用户 ID
        """
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'matchmaking_timeout',
                'data': {
                    'message': '匹配超时，未找到合适对手',
                    'suggestions': [
                        {'type': 'ai', 'text': '试试 AI 对战'},
                        {'type': 'friend', 'text': '邀请好友对战'}
                    ]
                }
            }
        )


# 工具函数
def calculate_rating_difference(rating1: int, rating2: int) -> int:
    """
    计算等级分差
    
    Args:
        rating1: 等级分 1
        rating2: 等级分 2
    
    Returns:
        int: 分差
    """
    return rating1 - rating2


def is_valid_match(rating1: int, rating2: int, max_diff: int) -> bool:
    """
    检查匹配是否有效（分差在允许范围内）
    
    Args:
        rating1: 等级分 1
        rating2: 等级分 2
        max_diff: 最大允许分差
    
    Returns:
        bool: 是否有效
    """
    diff = abs(rating1 - rating2)
    return diff <= max_diff
