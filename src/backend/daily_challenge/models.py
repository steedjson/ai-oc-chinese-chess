"""
每日挑战数据模型
"""

from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import uuid


class DailyChallengeManager(models.Manager):
    """每日挑战管理器"""
    
    def get_todays_challenge(self):
        """获取今日挑战"""
        today = date.today()
        try:
            return self.get(date=today, is_active=True)
        except self.model.DoesNotExist:
            return None
    
    def get_or_create_todays_challenge(self):
        """获取或创建今日挑战"""
        today = date.today()
        challenge, created = self.get_or_create(
            date=today,
            defaults={
                'is_active': True
            }
        )
        return challenge, created


class DailyChallenge(models.Model):
    """
    每日挑战
    
    每天提供一道精心挑选的棋局，全球玩家同步挑战
    """
    
    # 主键
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 挑战信息
    date = models.DateField(unique=True, verbose_name="挑战日期")
    puzzle = models.ForeignKey(
        'puzzles.Puzzle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_challenges',
        verbose_name="关联残局"
    )
    
    # 自定义局面
    fen = models.CharField(max_length=255, verbose_name="初始 FEN")
    target_description = models.TextField(blank=True, verbose_name="目标描述")
    solution_moves = models.JSONField(default=list, verbose_name="正确解法序列")
    
    # 限制条件
    max_moves = models.IntegerField(null=True, blank=True, verbose_name="最大步数限制")
    time_limit = models.IntegerField(null=True, blank=True, verbose_name="时间限制（秒）")
    
    # 难度
    difficulty = models.IntegerField(default=5, verbose_name="难度等级")
    stars = models.IntegerField(default=3, verbose_name="星级")
    
    # 统计
    total_attempts = models.IntegerField(default=0, verbose_name="总挑战次数")
    unique_players = models.IntegerField(default=0, verbose_name="参与人数")
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="完成率"
    )
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    # 管理器
    objects = DailyChallengeManager()
    
    class Meta:
        db_table = 'daily_challenges'
        verbose_name = '每日挑战'
        verbose_name_plural = '每日挑战'
        ordering = ['-date']
    
    def __str__(self):
        return f"每日挑战 {self.date} (难度{self.difficulty})"
    
    def update_statistics(self):
        """更新挑战统计"""
        attempts = self.attempts.all()
        
        self.total_attempts = attempts.count()
        self.unique_players = attempts.values('user').distinct().count()
        
        successful_attempts = attempts.filter(status='success').count()
        if self.total_attempts > 0:
            self.completion_rate = Decimal(successful_attempts) / Decimal(self.total_attempts) * 100
        else:
            self.completion_rate = Decimal(0)
        
        self.save()
    
    def get_optimal_moves_count(self):
        """获取最优解步数"""
        if self.solution_moves:
            return len(self.solution_moves)
        return self.max_moves or 6


class ChallengeAttempt(models.Model):
    """
    挑战尝试
    
    记录用户对每日挑战的尝试
    """
    
    # 状态选择
    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('abandoned', '放弃'),
    ]
    
    # 主键
    id = models.BigAutoField(primary_key=True)
    
    # 外键
    challenge = models.ForeignKey(
        DailyChallenge,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name="挑战"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='challenge_attempts',
        verbose_name="用户"
    )
    
    # 尝试信息
    start_fen = models.CharField(max_length=255, verbose_name="初始 FEN")
    move_history = models.JSONField(default=list, verbose_name="走棋历史")
    
    # 结果
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success',
        verbose_name="状态"
    )
    moves_used = models.IntegerField(null=True, blank=True, verbose_name="使用步数")
    time_used = models.IntegerField(null=True, blank=True, verbose_name="使用时间（秒）")
    is_optimal = models.BooleanField(default=False, verbose_name="是否最优解")
    
    # 评分
    score = models.IntegerField(default=0, verbose_name="得分")
    stars_earned = models.IntegerField(default=0, verbose_name="获得星级")
    
    # 时间戳
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="尝试时间")
    
    class Meta:
        db_table = 'challenge_attempts'
        verbose_name = '挑战尝试'
        verbose_name_plural = '挑战尝试'
        ordering = ['-attempted_at']
        # 用户每天只能有一次挑战记录
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'attempted_at'],
                name='unique_user_daily_challenge',
                condition=models.Q(attempted_at__gte=models.F('attempted_at') - timedelta(days=1))
            )
        ]
        indexes = [
            models.Index(fields=['challenge', 'user']),
            models.Index(fields=['-attempted_at']),
            models.Index(fields=['-score']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.date} - {self.status}"
    
    def calculate_score(self):
        """
        计算挑战得分
        
        得分 = 基础分 + 步数奖励 + 时间奖励 + 连击奖励
        
        基础分：1000 分
        步数奖励：每少于最优解 1 步 +50 分
        时间奖励：每少于限制时间 10 秒 +10 分
        连击奖励：连续完成 * 10 分
        """
        base_score = 1000
        
        # 步数奖励
        optimal_moves = self.challenge.get_optimal_moves_count()
        move_bonus = max(0, (optimal_moves - self.moves_used)) * 50 if self.moves_used else 0
        
        # 时间奖励
        time_bonus = 0
        if self.time_used and self.challenge.time_limit:
            time_bonus = max(0, (self.challenge.time_limit - self.time_used) // 10) * 10
        
        # 连击奖励
        streak = ChallengeStreak.objects.filter(user=self.user).first()
        streak_bonus = streak.current_streak * 10 if streak else 0
        
        total_score = base_score + move_bonus + time_bonus + streak_bonus
        
        return min(total_score, 2000)  # 上限 2000 分
    
    def calculate_stars(self):
        """
        计算星级（1-3 星）
        
        3 星：最优解 + 时间奖励
        2 星：完成挑战
        1 星：尝试但未完成
        """
        if self.status != 'success':
            return 1
        
        optimal_moves = self.challenge.get_optimal_moves_count()
        
        # 3 星：最优解且时间少于 50%
        if (self.moves_used == optimal_moves and 
            self.time_used and 
            self.challenge.time_limit and
            self.time_used < self.challenge.time_limit * 0.5):
            return 3
        
        # 2 星：完成挑战
        return 2
    
    def save(self, *args, **kwargs):
        """保存时自动计算得分和星级"""
        if self.status == 'success':
            self.score = self.calculate_score()
            self.stars_earned = self.calculate_stars()
            self.is_optimal = (self.stars_earned == 3)
        super().save(*args, **kwargs)


class ChallengeStreak(models.Model):
    """
    连续打卡记录
    
    追踪用户的每日挑战连续完成记录
    """
    
    # 主键
    id = models.BigAutoField(primary_key=True)
    
    # 外键
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='challenge_streak',
        verbose_name="用户"
    )
    
    # 打卡信息
    current_streak = models.IntegerField(default=0, verbose_name="当前连续天数")
    longest_streak = models.IntegerField(default=0, verbose_name="最长连续天数")
    last_completion_date = models.DateField(null=True, blank=True, verbose_name="最后完成日期")
    
    # 总统计
    total_completions = models.IntegerField(default=0, verbose_name="总完成次数")
    total_perfect = models.IntegerField(default=0, verbose_name="完美解法次数")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'challenge_streaks'
        verbose_name = '连续打卡记录'
        verbose_name_plural = '连续打卡记录'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['-current_streak']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - 连续{self.current_streak}天"
    
    def update_streak(self, completion_date=None):
        """
        更新连续打卡记录
        
        Args:
            completion_date: 完成日期，默认为今天
        """
        if completion_date is None:
            completion_date = date.today()
        
        # 检查是否连续
        if self.last_completion_date:
            days_diff = (completion_date - self.last_completion_date).days
            
            if days_diff == 0:
                # 今天已经打卡过
                return
            elif days_diff == 1:
                # 连续打卡
                self.current_streak += 1
            else:
                # 中断，重置为 1
                self.current_streak = 1
        else:
            # 首次打卡
            self.current_streak = 1
        
        # 更新最长记录
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        # 更新其他统计
        self.last_completion_date = completion_date
        self.total_completions += 1
        
        self.save()
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """获取或创建用户的连续打卡记录"""
        streak, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'current_streak': 0,
                'longest_streak': 0,
            }
        )
        return streak, created
