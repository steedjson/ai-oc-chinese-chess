"""
好友对战房间序列化器
"""
from rest_framework import serializers
from .models import FriendRoom, Game


class FriendRoomCreateSerializer(serializers.ModelSerializer):
    """好友房间创建序列化器"""
    
    class Meta:
        model = FriendRoom
        fields = ['time_control', 'is_rated']
    
    time_control = serializers.IntegerField(default=600, min_value=60, max_value=7200)
    is_rated = serializers.BooleanField(default=False)
    
    def create(self, validated_data):
        """创建好友房间"""
        from django.utils import timezone
        from datetime import timedelta
        
        user = self.context['request'].user
        time_control = validated_data.get('time_control', 600)
        
        # 创建游戏
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=time_control,
            red_time_remaining=time_control,
            black_time_remaining=time_control,
        )
        
        # 创建房间
        room = FriendRoom.objects.create(
            game=game,
            creator=user,
            status='waiting',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        
        return room


class FriendRoomSerializer(serializers.ModelSerializer):
    """好友房间详情序列化器"""
    
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    game_id = serializers.IntegerField(source='game.id', read_only=True)
    invite_link = serializers.SerializerMethodField()
    
    class Meta:
        model = FriendRoom
        fields = [
            'id', 'room_code', 'status', 'creator', 'creator_username',
            'game_id', 'expires_at', 'started_at', 'finished_at',
            'created_at', 'updated_at', 'invite_link'
        ]
        read_only_fields = fields
    
    def get_invite_link(self, obj) -> str:
        """获取邀请链接"""
        request = self.context.get('request')
        return obj.get_invite_link(request)


class JoinRoomSerializer(serializers.Serializer):
    """加入房间序列化器"""
    
    room_code = serializers.CharField(max_length=10, min_length=5)
    
    def validate_room_code(self, value):
        """验证房间号"""
        try:
            room = FriendRoom.objects.get(room_code=value.upper())
            if not room.is_joinable():
                raise serializers.ValidationError('房间不可加入')
            if room.creator == self.context['request'].user:
                raise serializers.ValidationError('不能加入自己的房间')
            return value.upper()
        except FriendRoom.DoesNotExist:
            raise serializers.ValidationError('房间不存在')
