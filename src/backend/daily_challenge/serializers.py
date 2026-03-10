"""
每日挑战序列化器
"""

from rest_framework import serializers
from .models import DailyChallenge, ChallengeAttempt, ChallengeStreak


class UserMinimalSerializer(serializers.Serializer):
    """用户最小信息序列化器"""
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()
    
    def get_avatar(self, obj):
        return getattr(obj, 'avatar', None)


class LeaderboardEntrySerializer(serializers.Serializer):
    """排行榜条目序列化器"""
    rank = serializers.IntegerField()
    user = UserMinimalSerializer()
    score = serializers.IntegerField()
    moves_used = serializers.IntegerField()
    time_used = serializers.IntegerField()
    stars = serializers.IntegerField()
    completed_at = serializers.DateTimeField()


class DailyChallengeLeaderboardSerializer(serializers.Serializer):
    """每日挑战排行榜序列化器"""
    challenge_date = serializers.DateField()
    leaderboard = LeaderboardEntrySerializer(many=True)
    user_rank = serializers.DictField(allow_null=True)


class UserRankSerializer(serializers.Serializer):
    """用户排名序列化器"""
    rank = serializers.IntegerField()
    score = serializers.IntegerField()
    total_players = serializers.IntegerField()
    percentile = serializers.FloatField()


class WeeklyLeaderboardEntrySerializer(serializers.Serializer):
    """周排行榜条目序列化器"""
    rank = serializers.IntegerField()
    user = UserMinimalSerializer()
    total_score = serializers.IntegerField()
    challenges_completed = serializers.IntegerField()
    best_stars = serializers.IntegerField()
    avg_score = serializers.FloatField()


class AllTimeLeaderboardEntrySerializer(serializers.Serializer):
    """总排行榜条目序列化器"""
    rank = serializers.IntegerField()
    user = UserMinimalSerializer()
    total_score = serializers.IntegerField()
    total_challenges = serializers.IntegerField()
    total_perfect = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    avg_score = serializers.FloatField()


class ChallengeAttemptSerializer(serializers.ModelSerializer):
    """挑战尝试序列化器"""
    class Meta:
        model = ChallengeAttempt
        fields = [
            'id', 'challenge', 'user', 'status', 'moves_used',
            'time_used', 'score', 'stars_earned', 'is_optimal', 'attempted_at'
        ]
        read_only_fields = fields


class ChallengeStreakSerializer(serializers.ModelSerializer):
    """连续打卡序列化器"""
    class Meta:
        model = ChallengeStreak
        fields = [
            'id', 'user', 'current_streak', 'longest_streak',
            'last_completion_date', 'total_completions', 'total_perfect'
        ]
        read_only_fields = fields


class UserStatisticsSerializer(serializers.Serializer):
    """用户统计信息序列化器"""
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    total_completions = serializers.IntegerField()
    total_perfect = serializers.IntegerField()
    total_score = serializers.IntegerField()
    rank = serializers.IntegerField()
