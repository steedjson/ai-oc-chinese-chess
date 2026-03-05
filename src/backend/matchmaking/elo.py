"""
Elo 等级分系统

实现 Elo 分数计算、段位系统、等级分历史追踪和排行榜功能
"""
from enum import Enum
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import redis
from django.conf import settings
from django.utils import timezone


# 常量配置
K_FACTOR = getattr(settings, 'MATCHMAKING_K_FACTOR', 32)
INITIAL_RATING = getattr(settings, 'MATCHMAKING_INITIAL_RATING', 1500)
MIN_RATING = getattr(settings, 'MATCHMAKING_MIN_RATING', 0)
MAX_RATING = getattr(settings, 'MATCHMAKING_MAX_RATING', 3000)


class RankSegment(Enum):
    """段位枚举"""
    BRONZE = 'bronze'  # 青铜: 0-1000
    SILVER = 'silver'  # 白银: 1001-1200
    GOLD = 'gold'      # 黄金: 1201-1400
    PLATINUM = 'platinum'  # 铂金: 1401-1600
    DIAMOND = 'diamond'    # 钻石: 1601-1800
    MASTER = 'master'      # 大师: 1801+


@dataclass
class RatingHistory:
    """等级分历史记录"""
    rating: int
    change: int
    game_id: str
    opponent_id: str
    result: str  # 'win', 'loss', 'draw'
    created_at: datetime = field(default_factory=timezone.now)


def calculate_expected_score(player_rating: int, opponent_rating: int) -> float:
    """
    计算预期胜率
    
    使用标准 Elo 公式:
    E = 1 / (1 + 10^((R_opponent - R_player) / 400))
    
    Args:
        player_rating: 玩家等级分
        opponent_rating: 对手等级分
    
    Returns:
        float: 预期胜率 (0-1)
    """
    rating_diff = opponent_rating - player_rating
    expected = 1 / (1 + 10 ** (rating_diff / 400))
    return expected


def calculate_elo_change(
    player_rating: int,
    opponent_rating: int,
    result: str,
    k_factor: int = K_FACTOR
) -> int:
    """
    计算 Elo 积分变化
    
    公式: ΔR = K * (S - E)
    其中:
        K = K 因子 (决定变化幅度)
        S = 实际得分 (1=胜，0.5=和，0=负)
        E = 预期得分
    
    Args:
        player_rating: 玩家当前积分
        opponent_rating: 对手积分
        result: 比赛结果 ('win', 'loss', 'draw')
        k_factor: K 因子
    
    Returns:
        int: 积分变化 (正数增加，负数减少)
    """
    # 计算预期得分
    expected = calculate_expected_score(player_rating, opponent_rating)
    
    # 实际得分
    actual_scores = {
        'win': 1.0,
        'draw': 0.5,
        'loss': 0.0
    }
    actual = actual_scores.get(result.lower(), 0.0)
    
    # 计算变化
    change = k_factor * (actual - expected)
    
    return round(change)


def update_elo_rating(
    current_rating: int,
    opponent_rating: int,
    result: str,
    k_factor: int = K_FACTOR
) -> int:
    """
    更新等级分
    
    Args:
        current_rating: 当前等级分
        opponent_rating: 对手等级分
        result: 比赛结果 ('win', 'loss', 'draw')
        k_factor: K 因子
    
    Returns:
        int: 更新后的等级分
    """
    change = calculate_elo_change(current_rating, opponent_rating, result, k_factor)
    new_rating = current_rating + change
    
    # 限制在最小和最大值之间
    new_rating = max(MIN_RATING, min(MAX_RATING, new_rating))
    
    return new_rating


def get_rank_segment(rating: int) -> RankSegment:
    """
    根据等级分获取段位
    
    Args:
        rating: 等级分
    
    Returns:
        RankSegment: 段位枚举
    """
    if rating <= 1000:
        return RankSegment.BRONZE
    elif rating <= 1200:
        return RankSegment.SILVER
    elif rating <= 1400:
        return RankSegment.GOLD
    elif rating <= 1600:
        return RankSegment.PLATINUM
    elif rating <= 1800:
        return RankSegment.DIAMOND
    else:
        return RankSegment.MASTER


class EloService:
    """
    Elo 等级分服务
    
    提供等级分计算、历史追踪、排行榜等功能
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.leaderboard_key = "matchmaking:leaderboard"
        self.history_prefix = "matchmaking:history:"
    
    def update_player_rating(
        self,
        player_id: str,
        opponent_id: str,
        game_id: str,
        result: str,
        k_factor: int = K_FACTOR
    ) -> Tuple[int, int]:
        """
        更新玩家等级分
        
        Args:
            player_id: 玩家 ID
            opponent_id: 对手 ID
            game_id: 游戏 ID
            result: 比赛结果 ('win', 'loss', 'draw')
            k_factor: K 因子
        
        Returns:
            Tuple[int, int]: (玩家新分数，对手新分数)
        """
        from users.models import User
        
        # 获取玩家和对手
        try:
            player = User.objects.get(id=player_id)
            opponent = User.objects.get(id=opponent_id)
        except User.DoesNotExist:
            raise ValueError(f"玩家或对手不存在")
        
        # 计算新等级分
        player_new_rating = update_elo_rating(
            player.elo_rating, opponent.elo_rating, result, k_factor
        )
        
        # 对手的结果相反
        opponent_result = 'loss' if result == 'win' else ('win' if result == 'loss' else 'draw')
        opponent_new_rating = update_elo_rating(
            opponent.elo_rating, player.elo_rating, opponent_result, k_factor
        )
        
        # 更新数据库
        player.elo_rating = player_new_rating
        player.save(update_fields=['elo_rating'])
        
        opponent.elo_rating = opponent_new_rating
        opponent.save(update_fields=['elo_rating'])
        
        # 更新 Redis 排行榜
        self._update_leaderboard(player_id, player_new_rating)
        self._update_leaderboard(opponent_id, opponent_new_rating)
        
        # 记录历史
        self._record_history(player_id, game_id, opponent_id, result, player_new_rating)
        self._record_history(opponent_id, game_id, player_id, opponent_result, opponent_new_rating)
        
        return player_new_rating, opponent_new_rating
    
    def _update_leaderboard(self, user_id: str, rating: int):
        """更新排行榜"""
        self.redis.zadd(self.leaderboard_key, {user_id: rating})
    
    def _record_history(
        self,
        user_id: str,
        game_id: str,
        opponent_id: str,
        result: str,
        new_rating: int
    ):
        """记录等级分历史"""
        history_key = f"{self.history_prefix}{user_id}"
        
        history_data = {
            'rating': new_rating,
            'game_id': game_id,
            'opponent_id': opponent_id,
            'result': result,
            'created_at': timezone.now().isoformat()
        }
        
        # 使用 List 存储历史记录
        self.redis.lpush(history_key, str(history_data))
        
        # 限制历史记录数量（保留最近 100 条）
        self.redis.ltrim(history_key, 0, 99)
    
    def get_leaderboard(
        self,
        page: int = 1,
        page_size: int = 20,
        segment: Optional[RankSegment] = None
    ) -> Dict:
        """
        获取排行榜
        
        Args:
            page: 页码
            page_size: 每页数量
            segment: 段位过滤
        
        Returns:
            Dict: 排行榜数据
        """
        # 获取所有玩家（按分数降序）
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        # 从 Redis Sorted Set 获取
        players = self.redis.zrevrange(
            self.leaderboard_key,
            start,
            end,
            withscores=True
        )
        
        # 构建返回数据
        leaderboard = []
        for user_id, rating in players:
            user_id_str = user_id.decode() if isinstance(user_id, bytes) else user_id
            rating_int = int(rating)
            
            leaderboard.append({
                'user_id': user_id_str,
                'rating': rating_int,
                'segment': get_rank_segment(rating_int).value,
                'rank': start + len(leaderboard) + 1
            })
        
        # 获取总数
        total = self.redis.zcard(self.leaderboard_key)
        
        return {
            'players': leaderboard,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def get_user_rating(self, user_id: str) -> Optional[Dict]:
        """
        获取用户等级分信息
        
        Args:
            user_id: 用户 ID
        
        Returns:
            Optional[Dict]: 用户等级分信息
        """
        from users.models import User
        
        try:
            user = User.objects.get(id=user_id)
            rating = user.elo_rating
            
            return {
                'user_id': str(user.id),
                'rating': rating,
                'segment': get_rank_segment(rating).value,
                'total_games': getattr(user, 'total_games', 0),
                'wins': getattr(user, 'wins', 0),
                'losses': getattr(user, 'losses', 0),
                'draws': getattr(user, 'draws', 0)
            }
        except User.DoesNotExist:
            return None
    
    def get_rating_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        获取用户等级分历史
        
        Args:
            user_id: 用户 ID
            limit: 返回数量
        
        Returns:
            List[Dict]: 历史记录列表
        """
        history_key = f"{self.history_prefix}{user_id}"
        history_data = self.redis.lrange(history_key, 0, limit - 1)
        
        history = []
        for item in history_data:
            if isinstance(item, bytes):
                item = item.decode()
            # 这里需要解析字符串，实际实现中应使用 JSON
            history.append({'raw': item})
        
        return history
    
    def get_users_in_rating_range(
        self,
        min_rating: int,
        max_rating: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        获取指定分数范围内的用户
        
        Args:
            min_rating: 最低分数
            max_rating: 最高分数
            limit: 返回数量
        
        Returns:
            List[Dict]: 用户列表
        """
        # 从 Redis Sorted Set 获取
        users = self.redis.zrangebyscore(
            self.leaderboard_key,
            min_rating,
            max_rating,
            start=0,
            num=limit,
            withscores=True
        )
        
        result = []
        for user_id, rating in users:
            user_id_str = user_id.decode() if isinstance(user_id, bytes) else user_id
            result.append({
                'user_id': user_id_str,
                'rating': int(rating),
                'segment': get_rank_segment(int(rating)).value
            })
        
        return result


# 工具函数
def get_segment_boundaries() -> Dict[str, Dict[str, int]]:
    """
    获取段位边界
    
    Returns:
        Dict: 段位边界配置
    """
    return {
        'bronze': {'min': 0, 'max': 1000},
        'silver': {'min': 1001, 'max': 1200},
        'gold': {'min': 1201, 'max': 1400},
        'platinum': {'min': 1401, 'max': 1600},
        'diamond': {'min': 1601, 'max': 1800},
        'master': {'min': 1801, 'max': MAX_RATING}
    }
