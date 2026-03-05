"""
AI Engine 序列化器

用于 API 请求和响应的数据序列化
"""
from rest_framework import serializers
from .models import AIGame, AIDifficulty, AIAnalysis


class AIDifficultySerializer(serializers.ModelSerializer):
    """AI 难度配置序列化器"""
    
    class Meta:
        model = AIDifficulty
        fields = [
            'id', 'level', 'name', 'description', 'skill_level', 
            'search_depth', 'think_time_ms', 'elo_estimate', 'is_active'
        ]
        read_only_fields = ['id']


class AIGameCreateSerializer(serializers.ModelSerializer):
    """AI 对局创建序列化器"""
    
    class Meta:
        model = AIGame
        fields = [
            'id', 'player', 'ai_level', 'ai_side', 'fen_start', 
            'fen_current', 'status'
        ]
        read_only_fields = ['id', 'player', 'fen_current', 'status', 'created_at']
    
    def create(self, validated_data):
        """创建 AI 对局"""
        validated_data['status'] = 'pending'
        validated_data['fen_current'] = validated_data.get('fen_start')
        return super().create(validated_data)


class AIGameSerializer(serializers.ModelSerializer):
    """AI 对局详情序列化器"""
    
    class Meta:
        model = AIGame
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIMoveRequestSerializer(serializers.Serializer):
    """AI 走棋请求序列化器"""
    
    fen = serializers.CharField(help_text="当前 FEN 字符串")
    difficulty = serializers.IntegerField(min_value=1, max_value=10, default=5, help_text="难度等级")
    time_limit = serializers.IntegerField(min_value=100, max_value=10000, default=2000, help_text="思考时间（毫秒）")
    
    def validate_fen(self, value):
        """验证 FEN 格式"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("无效的 FEN 格式")
        return value


class AIMoveResponseSerializer(serializers.Serializer):
    """AI 走棋响应序列化器"""
    
    from_pos = serializers.CharField(help_text="起始位置")
    to_pos = serializers.CharField(help_text="目标位置")
    piece = serializers.CharField(help_text="棋子类型")
    evaluation = serializers.FloatField(help_text="局面评估分数")
    depth = serializers.IntegerField(help_text="搜索深度")
    thinking_time = serializers.IntegerField(help_text="思考时间（毫秒）")
    notation = serializers.CharField(help_text="棋谱记号", required=False)


class AIHintRequestSerializer(serializers.Serializer):
    """AI 走棋提示请求序列化器"""
    
    fen = serializers.CharField(help_text="当前 FEN 字符串")
    difficulty = serializers.IntegerField(min_value=1, max_value=10, default=5, help_text="难度等级")
    count = serializers.IntegerField(min_value=1, max_value=5, default=3, help_text="提示数量")


class AIHintResponseSerializer(serializers.Serializer):
    """AI 走棋提示响应序列化器"""
    
    hints = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField()
        ),
        help_text="候选走法列表"
    )
    thinking_time = serializers.IntegerField(help_text="思考时间（毫秒）")


class AIAnalysisRequestSerializer(serializers.Serializer):
    """AI 棋局分析请求序列化器"""
    
    fen = serializers.CharField(help_text="当前 FEN 字符串")
    depth = serializers.IntegerField(min_value=5, max_value=25, default=15, help_text="搜索深度")


class AIAnalysisResponseSerializer(serializers.Serializer):
    """AI 棋局分析响应序列化器"""
    
    score = serializers.FloatField(help_text="评估分数")
    score_text = serializers.CharField(help_text="评估文字描述")
    best_move = serializers.CharField(help_text="最佳走棋")
    depth = serializers.IntegerField(help_text="搜索深度")
    thinking_time = serializers.IntegerField(help_text="思考时间（毫秒）")


class AIAnalysisCreateSerializer(serializers.ModelSerializer):
    """AI 分析结果创建序列化器"""
    
    class Meta:
        model = AIAnalysis
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
