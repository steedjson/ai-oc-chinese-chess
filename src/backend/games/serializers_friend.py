"""
好友对战房间序列化器
"""
import re
from rest_framework import serializers
from games.models import FriendRoom, Game


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
        is_rated = validated_data.get('is_rated', False)
        
        # 创建游戏
        game = Game.objects.create(
            game_type='friend',
            status='waiting',
            player_red=user,
            timeout_seconds=time_control,
            red_time_remaining=time_control,
            black_time_remaining=time_control,
            is_rated=is_rated,
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
        from rest_framework.exceptions import NotFound
        
        # 验证房间号格式（只允许大写字母和数字）
        if not re.match(r'^[A-Z0-9]+$', value.upper()):
            raise serializers.ValidationError('房间号只能包含大写字母和数字')
        
        try:
            room = FriendRoom.objects.select_related('game').get(room_code=value.upper())
            
            # 检查是否过期
            if room.is_expired():
                raise serializers.ValidationError('房间已过期')
            
            # 检查房间状态
            if room.status == 'playing':
                raise serializers.ValidationError('房间已在对局中')
            if room.status == 'finished':
                raise serializers.ValidationError('房间已结束')
            if room.status == 'expired':
                raise serializers.ValidationError('房间已过期')
            
            # 检查是否可加入
            if not room.is_joinable():
                raise serializers.ValidationError('房间不可加入')
            
            # 检查是否自己的房间
            if room.creator == self.context['request'].user:
                raise serializers.ValidationError('不能加入自己的房间')
            
            # 检查游戏是否已有黑方
            if room.game.player_black is not None:
                raise serializers.ValidationError('房间已满')
            
            return value.upper()
        except FriendRoom.DoesNotExist:
            # 房间不存在应该返回 404
            raise NotFound('房间不存在')
