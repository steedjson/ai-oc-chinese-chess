"""
AI Engine Django 模型

定义 AI 对局、难度配置、分析结果等数据库模型
"""
from django.db import models
from django.utils import timezone
from uuid import uuid4


class AIDifficulty(models.Model):
    """
    AI 难度配置模型
    
    存储 10 个难度等级的配置信息
    """
    level = models.IntegerField(unique=True, help_text="难度等级 (1-10)")
    name = models.CharField(max_length=50, help_text="难度名称")
    description = models.TextField(blank=True, help_text="难度描述")
    
    # Stockfish 参数
    skill_level = models.IntegerField(help_text="Stockfish Skill Level (0-20)")
    search_depth = models.IntegerField(help_text="搜索深度")
    think_time_ms = models.IntegerField(help_text="思考时间（毫秒）")
    move_overhead = models.IntegerField(default=100, help_text="移动开销（毫秒）")
    threads = models.IntegerField(default=2, help_text="线程数")
    hash_mb = models.IntegerField(default=128, help_text="哈希表大小（MB）")
    
    # 棋力评估
    elo_estimate = models.IntegerField(help_text="预估 Elo 分数")
    
    # 启用状态
    is_active = models.BooleanField(default=True, help_text="是否启用")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_difficulties'
        ordering = ['level']
    
    def __str__(self):
        return f"难度 {self.level} - {self.name} ({self.elo_estimate} Elo)"


class AIGame(models.Model):
    """
    AI 对局记录模型
    
    记录玩家与 AI 的对局信息
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # 玩家信息
    player = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='ai_games',
        help_text="玩家",
        null=True,
        blank=True
    )
    
    # AI 信息
    ai_level = models.IntegerField(help_text="AI 难度等级 (1-10)")
    ai_side = models.CharField(
        max_length=5,
        choices=[('red', '红方'), ('black', '黑方')],
        help_text="AI 执棋方"
    )
    
    # 对局信息
    fen_start = models.TextField(help_text="初始 FEN")
    fen_current = models.TextField(help_text="当前 FEN")
    move_history = models.JSONField(default=list, help_text="走棋历史记录")
    
    # 对局状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '等待开始'),
            ('playing', '进行中'),
            ('red_win', '红方胜'),
            ('black_win', '黑方胜'),
            ('draw', '和棋'),
            ('aborted', '已取消'),
        ],
        default='pending',
        help_text="对局状态"
    )
    
    winner = models.CharField(
        max_length=10,
        choices=[('red', '红方'), ('black', '黑方'), ('draw', '和棋')],
        null=True,
        blank=True,
        help_text="获胜方"
    )
    
    # 性能指标
    total_moves = models.IntegerField(default=0, help_text="总步数")
    avg_think_time_ms = models.IntegerField(null=True, blank=True, help_text="AI 平均思考时间")
    max_think_time_ms = models.IntegerField(null=True, blank=True, help_text="AI 最大思考时间")
    avg_search_depth = models.IntegerField(null=True, blank=True, help_text="AI 平均搜索深度")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ai_games'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI 对局 {self.id} - 难度 {self.ai_level} - {self.status}"


class AIAnalysis(models.Model):
    """
    AI 棋局分析结果模型
    
    存储 AI 对棋局的分析结果
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    # 关联对局
    game = models.ForeignKey(
        AIGame,
        on_delete=models.CASCADE,
        related_name='analyses',
        null=True,
        blank=True,
        help_text="关联的 AI 对局"
    )
    
    # 棋局状态
    fen = models.TextField(help_text="FEN 字符串")
    move_number = models.IntegerField(help_text="第几步")
    
    # 分析结果
    evaluation_score = models.FloatField(help_text="评估分数")
    evaluation_text = models.CharField(max_length=50, help_text="评估文字描述")
    best_move = models.CharField(max_length=10, help_text="最佳走棋")
    search_depth = models.IntegerField(help_text="搜索深度")
    
    # 候选走法
    top_moves = models.JSONField(default=list, help_text="顶级走法列表")
    
    # 分析时间
    thinking_time_ms = models.IntegerField(help_text="思考时间（毫秒）")
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_analyses'
        ordering = ['move_number']
    
    def __str__(self):
        return f"分析 {self.id} - 第 {self.move_number} 步 - 评分 {self.evaluation_score}"
