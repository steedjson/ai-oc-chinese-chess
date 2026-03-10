"""
悔棋请求序列化器
"""
from rest_framework import serializers
from games.models import UndoRequest


class UndoRequestSerializer(serializers.ModelSerializer):
    """悔棋请求序列化器"""
    
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    responded_by_username = serializers.CharField(source='responded_by.username', read_only=True)
    move_number = serializers.IntegerField(source='move_to_undo.move_number', read_only=True)
    piece = serializers.CharField(source='move_to_undo.piece', read_only=True)
    from_pos = serializers.CharField(source='move_to_undo.from_pos', read_only=True)
    to_pos = serializers.CharField(source='move_to_undo.to_pos', read_only=True)
    notation = serializers.CharField(source='move_to_undo.notation', read_only=True)
    
    class Meta:
        model = UndoRequest
        fields = [
            'id', 'game_id', 'requester', 'requester_username',
            'requested_at', 'move_to_undo', 'move_number', 'piece',
            'from_pos', 'to_pos', 'notation', 'undo_count',
            'status', 'responded_by', 'responded_by_username',
            'responded_at', 'reason', 'auto_accept_at'
        ]
        read_only_fields = ['id', 'requested_at', 'responded_at']


class UndoRequestCreateSerializer(serializers.Serializer):
    """悔棋请求创建序列化器"""
    
    undo_count = serializers.IntegerField(
        min_value=1,
        max_value=3,
        default=1,
        help_text='悔棋步数（1-3）'
    )
    reason = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default='',
        help_text='悔棋原因'
    )
    
    def validate_undo_count(self, value):
        """验证悔棋步数"""
        if value < 1 or value > 3:
            raise serializers.ValidationError("悔棋步数必须是 1-3 之间的整数")
        return value


class UndoRespondSerializer(serializers.Serializer):
    """悔棋响应序列化器"""
    
    request_id = serializers.IntegerField(help_text='悔棋请求 ID')
    accept = serializers.BooleanField(help_text='是否接受悔棋')
