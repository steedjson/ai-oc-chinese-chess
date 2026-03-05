"""
匹配系统模块

提供 Elo 等级分、匹配队列、匹配算法等功能
"""

# Elo - 这些可以在 Django 加载前导入
from .elo import (
    calculate_expected_score,
    calculate_elo_change,
    update_elo_rating,
    get_rank_segment,
    RankSegment,
    EloService,
    K_FACTOR,
    INITIAL_RATING,
    MIN_RATING,
    MAX_RATING,
)

# Queue - 这些可以在 Django 加载前导入
from .queue import (
    MatchmakingQueue,
    QueueUser,
    MATCH_TIMEOUT,
    SEARCH_EXPANSION_INTERVAL,
    INITIAL_SEARCH_RANGE,
    SEARCH_EXPANSION,
    MAX_SEARCH_RANGE,
)

# Algorithm - 这些可以在 Django 加载前导入
from .algorithm import (
    Matchmaker,
    MatchResult,
    calculate_rating_difference,
    is_valid_match,
    MAX_REMATCH_INTERVAL,
)

# Models - 这些需要 Django 加载后才能导入
# 使用延迟导入避免 AppRegistryNotReady 错误
def __getattr__(name):
    """延迟导入模型"""
    if name in ['MatchQueue', 'MatchHistory', 'PlayerRank', 'Season', 
                'MatchQueueStatus', 'MatchResultChoices', 'RankSegmentChoices']:
        from . import models
        if name == 'MatchQueueStatus':
            return models.MatchQueueStatus
        elif name == 'MatchResultChoices':
            return models.MatchResult
        elif name == 'RankSegmentChoices':
            return models.RankSegment
        else:
            return getattr(models, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Elo
    'calculate_expected_score',
    'calculate_elo_change',
    'update_elo_rating',
    'get_rank_segment',
    'RankSegment',
    'EloService',
    'K_FACTOR',
    'INITIAL_RATING',
    'MIN_RATING',
    'MAX_RATING',
    
    # Queue
    'MatchmakingQueue',
    'QueueUser',
    'MATCH_TIMEOUT',
    'SEARCH_EXPANSION_INTERVAL',
    'INITIAL_SEARCH_RANGE',
    'SEARCH_EXPANSION',
    'MAX_SEARCH_RANGE',
    
    # Algorithm
    'Matchmaker',
    'MatchResult',
    'calculate_rating_difference',
    'is_valid_match',
    'MAX_REMATCH_INTERVAL',
    
    # Models (延迟导入)
    'MatchQueue',
    'MatchHistory',
    'PlayerRank',
    'Season',
    'MatchQueueStatus',
    'MatchResultChoices',
    'RankSegmentChoices',
]
