"""
匹配系统 Django 模型

实现匹配队列、匹配历史、玩家段位、赛季配置等模型
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from uuid import uuid4
import uuid


# 常量配置
MATCH_TIMEOUT_SECONDS = getattr(settings, 'MATCHMAKING_TIMEOUT', 180)


class MatchQueueStatus(models.TextChoices):
    """匹配队列状态"""
    WAITING = 'waiting', '等待中'
    SEARCHING = 'searching', '搜索中'
    MATCHED = 'matched', '已匹配'
    CANCELLED = 'cancelled', '已取消'
    TIMEOUT = 'timeout', '超时'


class MatchResult(models.TextChoices):
    """比赛结果"""
    WIN = 'win', '胜利'
    LOSS = 'loss', '失败'
    DRAW = 'draw', '和棋'


class RankSegment(models.TextChoices):
    """段位"""
    BRONZE = 'bronze', '青铜'
    SILVER = 'silver', '白银'
    GOLD = 'gold', '黄金'
    PLATINUM = 'platinum', '铂金'
    DIAMOND = 'diamond', '钻石'
    MASTER = 'master', '大师'


class MatchQueueManager(models.Manager):
    """MatchQueue 管理器"""
    
    def active(self):
        """获取活跃的队列（未取消、未超时）"""
        return self.filter(
            status__in=[MatchQueueStatus.SEARCHING, MatchQueueStatus.MATCHED]
        )
    
    def searching(self):
        """获取搜索中的队列"""
        return self.filter(status=MatchQueueStatus.SEARCHING)
    
    def get_user_queue(self, user_id: str, game_type: str = 'online'):
        """获取用户的队列记录"""
        try:
            return self.filter(
                user_id=user_id,
                game_type=game_type,
                status=MatchQueueStatus.SEARCHING
            ).first()
        except self.model.DoesNotExist:
            return None


class MatchQueue(models.Model):
    """
    匹配队列模型
    
    记录当前正在排队的玩家信息
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    game_type = models.CharField(max_length=50, default='online')
    rating = models.IntegerField(default=1500)
    search_range = models.IntegerField(default=100)
    status = models.CharField(
        max_length=20,
        choices=MatchQueueStatus.choices,
        default=MatchQueueStatus.SEARCHING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    opponent_id = models.CharField(max_length=255, null=True, blank=True)
    game_id = models.UUIDField(null=True, blank=True)
    
    objects = MatchQueueManager()
    
    class Meta:
        db_table = 'match_queues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['game_type', 'status']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Queue({self.user_id}, {self.game_type}, {self.status})"
    
    def is_timeout(self) -> bool:
        """检查是否超时"""
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return elapsed > MATCH_TIMEOUT_SECONDS
    
    def get_wait_time(self) -> float:
        """获取等待时间（秒）"""
        return (timezone.now() - self.created_at).total_seconds()
    
    def mark_matched(self, opponent_id: str, game_id: uuid.UUID):
        """标记为已匹配"""
        self.status = MatchQueueStatus.MATCHED
        self.opponent_id = opponent_id
        self.game_id = game_id
        self.matched_at = timezone.now()
        self.save(update_fields=['status', 'opponent_id', 'game_id', 'matched_at', 'updated_at'])
    
    def mark_cancelled(self):
        """标记为已取消"""
        self.status = MatchQueueStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_timeout(self):
        """标记为超时"""
        self.status = MatchQueueStatus.TIMEOUT
        self.save(update_fields=['status', 'updated_at'])


class MatchHistoryManager(models.Manager):
    """MatchHistory 管理器"""
    
    def for_user(self, user_id: str):
        """获取用户的匹配历史"""
        return self.filter(user_id=user_id).order_by('-created_at')
    
    def wins(self):
        """获取胜利记录"""
        return self.filter(result=MatchResult.WIN)
    
    def losses(self):
        """获取失败记录"""
        return self.filter(result=MatchResult.LOSS)
    
    def draws(self):
        """获取和棋记录"""
        return self.filter(result=MatchResult.DRAW)


class MatchHistory(models.Model):
    """
    匹配历史模型
    
    记录每次匹配的结果和详情
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    opponent_id = models.CharField(max_length=255)
    game_id = models.UUIDField()
    user_rating = models.IntegerField()
    opponent_rating = models.IntegerField()
    rating_change = models.IntegerField(default=0)
    result = models.CharField(max_length=10, choices=MatchResult.choices)
    match_duration = models.IntegerField(null=True, blank=True, help_text='匹配耗时（秒）')
    queue_time = models.IntegerField(null=True, blank=True, help_text='排队耗时（秒）')
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = MatchHistoryManager()
    
    class Meta:
        db_table = 'match_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['game_id']),
            models.Index(fields=['result']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Match({self.user_id} vs {self.opponent_id}, {self.result})"
    
    def get_rating_diff(self) -> int:
        """获取等级分差"""
        return self.user_rating - self.opponent_rating
    
    def is_win(self) -> bool:
        """是否胜利"""
        return self.result == MatchResult.WIN
    
    def is_loss(self) -> bool:
        """是否失败"""
        return self.result == MatchResult.LOSS
    
    def is_draw(self) -> bool:
        """是否和棋"""
        return self.result == MatchResult.DRAW


class PlayerRankManager(models.Manager):
    """PlayerRank 管理器"""
    
    def get_current_rank(self, user_id: str):
        """获取用户当前段位"""
        return self.filter(user_id=user_id).order_by('-season_id').first()
    
    def by_segment(self, segment: RankSegment):
        """按段位过滤"""
        return self.filter(segment=segment)
    
    def leaderboard(self, season_id: int = None, limit: int = 100):
        """获取排行榜"""
        queryset = self.all()
        
        if season_id:
            queryset = queryset.filter(season_id=season_id)
        
        return queryset.order_by('-rating', '-total_games')[:limit]


class PlayerRank(models.Model):
    """
    玩家段位模型
    
    记录玩家的段位和排名信息
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    rating = models.IntegerField(default=1500)
    segment = models.CharField(
        max_length=20,
        choices=RankSegment.choices,
        default=RankSegment.BRONZE
    )
    season_id = models.IntegerField(default=1)
    total_games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    peak_rating = models.IntegerField(default=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = PlayerRankManager()
    
    class Meta:
        db_table = 'player_ranks'
        ordering = ['-rating']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['segment', '-rating']),
            models.Index(fields=['season_id', '-rating']),
            models.Index(fields=['-rating']),
        ]
    
    def __str__(self):
        return f"Rank({self.user_id}, {self.get_segment_display()}, {self.rating})"
    
    def get_segment_display(self) -> str:
        """获取段位显示名称"""
        # 使用 Django 的 choices 机制获取显示名称
        segment_choices = {
            RankSegment.BRONZE: '青铜',
            RankSegment.SILVER: '白银',
            RankSegment.GOLD: '黄金',
            RankSegment.PLATINUM: '铂金',
            RankSegment.DIAMOND: '钻石',
            RankSegment.MASTER: '大师',
        }
        return segment_choices.get(self.segment, self.segment)
    
    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100
    
    def update_stats(self, result: str):
        """更新统计数据"""
        self.total_games += 1
        
        if result == MatchResult.WIN:
            self.wins += 1
        elif result == MatchResult.LOSS:
            self.losses += 1
        elif result == MatchResult.DRAW:
            self.draws += 1
        
        self.save(update_fields=['total_games', 'wins', 'losses', 'draws', 'updated_at'])
    
    def update_rating(self, new_rating: int):
        """更新等级分"""
        self.rating = new_rating
        
        if new_rating > self.peak_rating:
            self.peak_rating = new_rating
        
        # 更新段位
        self.segment = self._calculate_segment(new_rating)
        
        self.save(update_fields=['rating', 'peak_rating', 'segment', 'updated_at'])
    
    def _calculate_segment(self, rating: int) -> str:
        """根据等级分计算段位"""
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


class SeasonManager(models.Manager):
    """Season 管理器"""
    
    def current(self):
        """获取当前赛季"""
        now = timezone.now().date()
        return self.filter(
            start_date__lte=now,
            end_date__gte=now,
            is_active=True
        ).first()
    
    def active(self):
        """获取活跃的赛季"""
        return self.filter(is_active=True)


class Season(models.Model):
    """
    赛季模型
    
    配置赛季信息
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    season_number = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = SeasonManager()
    
    class Meta:
        db_table = 'seasons'
        ordering = ['-season_number']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return self.name
    
    def is_current_season(self) -> bool:
        """是否为当前赛季"""
        now = timezone.now().date()
        return self.start_date <= now <= self.end_date and self.is_active
    
    def days_remaining(self) -> int:
        """获取剩余天数"""
        now = timezone.now().date()
        if now > self.end_date:
            return 0
        return (self.end_date - now).days
    
    def days_elapsed(self) -> int:
        """获取已过天数"""
        now = timezone.now().date()
        if now < self.start_date:
            return 0
        return (now - self.start_date).days
    
    def total_days(self) -> int:
        """获取赛季总天数"""
        return (self.end_date - self.start_date).days + 1
