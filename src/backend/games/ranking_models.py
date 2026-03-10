"""
中国象棋排行榜数据模型

包含：
- GameRecord: 游戏记录模型（用于排行榜统计）
- DailyRanking: 每日排行榜缓存
- WeeklyRanking: 每周排行榜缓存
- AllTimeRanking: 总排行榜缓存
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date, timedelta


class GameResult(models.TextChoices):
    """游戏结果枚举"""
    WIN = 'win', '胜利'
    LOSS = 'loss', '失败'
    DRAW = 'draw', '和棋'


class GameRecord(models.Model):
    """
    游戏记录模型
    
    用于排行榜统计的游戏记录，从 Game 模型同步而来
    包含排行榜计算所需的冗余字段以提高查询性能
    """
    id = models.BigAutoField(primary_key=True)
    
    # 关联游戏
    game = models.OneToOneField(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='ranking_record',
        null=True,
        blank=True
    )
    
    # 玩家信息
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ranking_records'
    )
    
    # 游戏信息
    game_type = models.CharField(
        max_length=20,
        choices=[
            ('single', '单机'),
            ('online', '联网'),
            ('friend', '好友'),
        ],
        default='online'
    )
    
    # 游戏结果
    result = models.CharField(
        max_length=10,
        choices=GameResult.choices
    )
    
    # 得分计算
    score_gained = models.IntegerField(default=0)  # 本局获得的分数
    elo_change = models.IntegerField(default=0)  # Elo 评分变化
    
    # 游戏表现
    moves_made = models.IntegerField(default=0)  # 走棋步数
    duration = models.IntegerField(default=0)  # 游戏时长（秒）
    is_rated = models.BooleanField(default=True)  # 是否计分局
    
    # 时间信息（用于快速查询）
    game_date = models.DateField()  # 游戏日期
    game_week = models.IntegerField()  # 游戏周数 (ISO week)
    game_year = models.IntegerField()  # 游戏年份
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'game_ranking_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'game_date']),
            models.Index(fields=['game_date']),
            models.Index(fields=['game_week', 'game_year']),
            models.Index(fields=['-score_gained']),
            models.Index(fields=['user', 'result']),
            models.Index(fields=['is_rated', 'game_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.result} - {self.game_date}"
    
    @classmethod
    def create_from_game(cls, game, user, result, score_gained=0, elo_change=0):
        """
        从游戏对局创建排行榜记录
        
        Args:
            game: Game 实例
            user: 用户实例
            result: 游戏结果 ('win', 'loss', 'draw')
            score_gained: 获得的分数
            elo_change: Elo 变化
        """
        game_date = game.finished_at.date() if game.finished_at else timezone.now().date()
        iso_calendar = game_date.isocalendar()
        
        record = cls.objects.create(
            game=game,
            user=user,
            game_type=game.game_type,
            result=result,
            score_gained=score_gained,
            elo_change=elo_change,
            moves_made=game.move_count,
            duration=game.duration or 0,
            is_rated=game.is_rated,
            game_date=game_date,
            game_week=iso_calendar[1],
            game_year=iso_calendar[0],
        )
        
        return record


class RankingCache(models.Model):
    """
    排行榜缓存模型
    
    缓存排行榜数据以提高查询性能
    支持每日、每周、总榜三种类型
    """
    
    RANKING_TYPE_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('all_time', '总榜'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # 缓存类型
    ranking_type = models.CharField(
        max_length=20,
        choices=RANKING_TYPE_CHOICES
    )
    
    # 时间范围标识
    cache_date = models.DateField(null=True, blank=True)  # 每日榜日期
    cache_week = models.IntegerField(null=True, blank=True)  # 每周榜周数
    cache_year = models.IntegerField(null=True, blank=True)  # 每年榜年份
    
    # 缓存数据
    leaderboard_data = models.JSONField(
        default=list,
        help_text="排行榜数据 JSON"
    )
    
    # 缓存元数据
    total_players = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # 是否有效
    is_valid = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ranking_caches'
        ordering = ['-cache_date', '-cache_week', '-cache_year']
        unique_together = [
            ['ranking_type', 'cache_date'],  # 每日榜唯一
            ['ranking_type', 'cache_week', 'cache_year'],  # 每周榜唯一
            ['ranking_type'],  # 总榜唯一
        ]
        indexes = [
            models.Index(fields=['ranking_type', 'is_valid']),
            models.Index(fields=['ranking_type', 'cache_date', 'is_valid']),
            models.Index(fields=['ranking_type', 'cache_week', 'cache_year', 'is_valid']),
        ]
    
    def __str__(self):
        if self.ranking_type == 'daily':
            return f"Daily Ranking - {self.cache_date}"
        elif self.ranking_type == 'weekly':
            return f"Weekly Ranking - {self.cache_year}-W{self.cache_week}"
        else:
            return "All-Time Ranking"
    
    @classmethod
    def get_daily_cache(cls, cache_date=None):
        """获取每日排行榜缓存"""
        if cache_date is None:
            cache_date = date.today()
        
        try:
            return cls.objects.get(
                ranking_type='daily',
                cache_date=cache_date,
                is_valid=True
            )
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_weekly_cache(cls, week=None, year=None):
        """获取每周排行榜缓存"""
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        try:
            return cls.objects.get(
                ranking_type='weekly',
                cache_week=week,
                cache_year=year,
                is_valid=True
            )
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_all_time_cache(cls):
        """获取总排行榜缓存"""
        try:
            return cls.objects.get(
                ranking_type='all_time',
                is_valid=True
            )
        except cls.DoesNotExist:
            return None
    
    def invalidate(self):
        """使缓存失效"""
        self.is_valid = False
        self.save(update_fields=['is_valid'])
    
    def update_cache(self, leaderboard_data, total_players):
        """
        更新缓存数据
        
        Args:
            leaderboard_data: 排行榜数据列表
            total_players: 总玩家数
        """
        self.leaderboard_data = leaderboard_data
        self.total_players = total_players
        self.expires_at = timezone.now() + timedelta(hours=1)  # 1 小时后过期
        self.is_valid = True
        self.save()


class UserRankingStats(models.Model):
    """
    用户排行榜统计模型
    
    存储用户在排行榜中的统计数据
    """
    id = models.BigAutoField(primary_key=True)
    
    # 用户
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ranking_stats'
    )
    
    # 总统计
    total_games = models.IntegerField(default=0)
    total_wins = models.IntegerField(default=0)
    total_losses = models.IntegerField(default=0)
    total_draws = models.IntegerField(default=0)
    
    # 得分统计
    total_score = models.IntegerField(default=0)
    highest_score = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # 连胜统计
    current_win_streak = models.IntegerField(default=0)
    longest_win_streak = models.IntegerField(default=0)
    
    # 排名统计
    current_daily_rank = models.IntegerField(null=True, blank=True)
    current_weekly_rank = models.IntegerField(null=True, blank=True)
    current_all_time_rank = models.IntegerField(null=True, blank=True)
    
    # 时间戳
    last_game_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_ranking_stats'
        ordering = ['-total_score']
        indexes = [
            models.Index(fields=['-total_score']),
            models.Index(fields=['-total_wins']),
            models.Index(fields=['current_daily_rank']),
            models.Index(fields=['current_weekly_rank']),
            models.Index(fields=['current_all_time_rank']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Ranking Stats"
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """获取或创建用户排行榜统计"""
        stats, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'total_games': 0,
                'total_wins': 0,
                'total_losses': 0,
                'total_draws': 0,
                'total_score': 0,
            }
        )
        return stats, created
    
    def update_stats(self):
        """更新用户统计数据"""
        records = GameRecord.objects.filter(user=self.user, is_rated=True)
        
        self.total_games = records.count()
        self.total_wins = records.filter(result=GameResult.WIN).count()
        self.total_losses = records.filter(result=GameResult.LOSS).count()
        self.total_draws = records.filter(result=GameResult.DRAW).count()
        
        self.total_score = records.aggregate(models.Sum('score_gained'))['score_gained__sum'] or 0
        self.highest_score = records.aggregate(models.Max('score_gained'))['score_gained__max'] or 0
        
        if self.total_games > 0:
            self.average_score = round(self.total_score / self.total_games, 2)
        else:
            self.average_score = 0.00
        
        # 更新最后游戏日期
        last_record = records.order_by('-game_date').first()
        if last_record:
            self.last_game_date = last_record.game_date
        
        self.save()
