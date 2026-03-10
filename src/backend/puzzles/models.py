"""
残局挑战 Django 模型

包含：
- Puzzle: 残局关卡模型
- PuzzleAttempt: 挑战记录模型
- PuzzleProgress: 用户进度模型
"""
import uuid
from django.db import models
from django.conf import settings


class PuzzleDifficulty(models.IntegerChoices):
    """难度等级"""
    BEGINNER = 1, '入门 (1 星)'
    EASY = 2, '入门 (2 星)'
    INTERMEDIATE = 3, '入门 (3 星)'
    EASY_PLUS = 4, '进阶 (4 星)'
    MEDIUM = 5, '进阶 (5 星)'
    MEDIUM_PLUS = 6, '进阶 (6 星)'
    HARD = 7, '高手 (7 星)'
    HARD_PLUS = 8, '高手 (8 星)'
    EXPERT = 9, '大师 (9 星)'
    MASTER = 10, '大师 (10 星)'


class Puzzle(models.Model):
    """
    残局关卡模型
    
    存储残局信息、初始位置、解法等
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 基本信息
    title = models.CharField(max_length=100, verbose_name='关卡名称')
    description = models.TextField(blank=True, verbose_name='关卡描述')
    source = models.CharField(max_length=200, blank=True, verbose_name='来源/名称')
    
    # 游戏状态
    fen_initial = models.TextField(verbose_name='初始 FEN 位置')
    solution_moves = models.JSONField(verbose_name='解法序列', help_text='正确走法序列 [{"from": "e2", "to": "e4", "piece": "P"}, ...]')
    
    # 难度配置
    difficulty = models.IntegerField(
        choices=PuzzleDifficulty.choices,
        verbose_name='难度等级 (1-10)'
    )
    move_limit = models.IntegerField(null=True, blank=True, verbose_name='步数限制')
    time_limit = models.IntegerField(null=True, blank=True, verbose_name='时间限制 (秒)')
    
    # 提示内容
    hint = models.TextField(blank=True, verbose_name='提示内容')
    
    # 统计信息
    total_attempts = models.IntegerField(default=0, verbose_name='总挑战次数')
    total_completions = models.IntegerField(default=0, verbose_name='总通关次数')
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='通关率 (%)')
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'puzzles'
        ordering = ['difficulty', 'created_at']
        indexes = [
            models.Index(fields=['difficulty', 'is_active']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['total_completions']),
        ]
    
    def __str__(self):
        return f"Puzzle {self.title} (难度:{self.difficulty})"
    
    def update_statistics(self):
        """更新统计数据"""
        attempts = PuzzleAttempt.objects.filter(puzzle=self)
        self.total_attempts = attempts.count()
        self.total_completions = attempts.filter(status='success').count()
        if self.total_attempts > 0:
            self.completion_rate = (self.total_completions / self.total_attempts * 100)
        self.save()


class PuzzleAttemptStatus(models.TextChoices):
    """挑战状态"""
    IN_PROGRESS = 'in_progress', '进行中'
    SUCCESS = 'success', '成功'
    FAILED = 'failed', '失败'
    TIMEOUT = 'timeout', '超时'
    ABANDONED = 'abandoned', '放弃'


class PuzzleAttempt(models.Model):
    """
    挑战记录模型
    
    存储用户挑战残局的详细记录
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 用户和关卡
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='puzzle_attempts'
    )
    puzzle = models.ForeignKey(
        Puzzle,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    
    # 挑战状态
    status = models.CharField(
        max_length=20,
        choices=PuzzleAttemptStatus.choices,
        default=PuzzleAttemptStatus.IN_PROGRESS
    )
    
    # 游戏状态
    fen_current = models.TextField(verbose_name='当前 FEN 位置')
    current_move_index = models.IntegerField(default=0, verbose_name='当前解法步骤')
    
    # 走棋历史
    move_history = models.JSONField(default=list, verbose_name='走棋历史', help_text='用户走棋记录 [{"from": "e2", "to": "e4", "piece": "P", "correct": true}, ...]')
    
    # 统计信息
    moves_used = models.IntegerField(default=0, verbose_name='使用步数')
    time_used = models.IntegerField(default=0, verbose_name='耗时 (秒)')
    
    # 评分
    stars = models.IntegerField(null=True, blank=True, verbose_name='星级评价 (1-3)')
    points_earned = models.IntegerField(default=0, verbose_name='获得积分')
    
    # 时间戳
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'puzzle_attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['puzzle', 'status']),
            models.Index(fields=['user', 'puzzle']),
        ]
    
    def __str__(self):
        return f"Attempt {self.user.username} - {self.puzzle.title} ({self.status})"


class PuzzleProgress(models.Model):
    """
    用户进度模型
    
    存储用户残局挑战的整体进度
    """
    id = models.BigAutoField(primary_key=True)
    
    # 用户
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='puzzle_progress'
    )
    
    # 进度统计
    total_completed = models.IntegerField(default=0, verbose_name='总通关数')
    total_attempts = models.IntegerField(default=0, verbose_name='总挑战次数')
    
    # 难度进度
    max_difficulty_passed = models.IntegerField(default=0, verbose_name='最高通过难度')
    
    # 星级统计
    total_stars = models.IntegerField(default=0, verbose_name='总星级')
    stars_1 = models.IntegerField(default=0, verbose_name='1 星通关数')
    stars_2 = models.IntegerField(default=0, verbose_name='2 星通关数')
    stars_3 = models.IntegerField(default=0, verbose_name='3 星通关数')
    
    # 排名积分
    ranking_points = models.IntegerField(default=0, verbose_name='排名积分')
    
    # 通关的关卡 ID 列表
    completed_puzzle_ids = models.JSONField(default=list, verbose_name='已通关关卡 ID')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'puzzle_progress'
        indexes = [
            models.Index(fields=['-ranking_points']),
            models.Index(fields=['-total_completed']),
        ]
    
    def __str__(self):
        return f"Progress {self.user.username} (通关:{self.total_completed}, 积分:{self.ranking_points})"
    
    def update_progress(self):
        """更新用户进度"""
        attempts = PuzzleAttempt.objects.filter(user=self.user, status='success')
        self.total_completed = attempts.count()
        self.total_attempts = PuzzleAttempt.objects.filter(user=self.user).count()
        
        # 计算最高难度
        max_diff = attempts.values_list('puzzle__difficulty', flat=True).order_by('-puzzle__difficulty').first()
        self.max_difficulty_passed = max_diff or 0
        
        # 计算星级
        self.stars_1 = attempts.filter(stars=1).count()
        self.stars_2 = attempts.filter(stars=2).count()
        self.stars_3 = attempts.filter(stars=3).count()
        self.total_stars = self.stars_1 + self.stars_2 * 2 + self.stars_3 * 3
        
        # 通关关卡 ID (转换为字符串以支持 JSON 序列化)
        self.completed_puzzle_ids = [str(pid) for pid in attempts.values_list('puzzle_id', flat=True).distinct()]
        
        self.save()
