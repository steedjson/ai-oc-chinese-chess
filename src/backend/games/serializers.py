"""
游戏对局序列化器
"""
from rest_framework import serializers
from .models import Game, GameMove


class GameMoveSerializer(serializers.ModelSerializer):
    """走棋记录序列化器"""
    
    class Meta:
        model = GameMove
        fields = [
            'id', 'move_number', 'piece', 'from_pos', 'to_pos',
            'captured', 'is_check', 'is_capture', 'notation',
            'fen_after', 'time_remaining', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GameListSerializer(serializers.ModelSerializer):
    """对局列表序列化器"""
    
    red_player_username = serializers.CharField(source='red_player.username', read_only=True)
    black_player_username = serializers.CharField(source='black_player.username', read_only=True)
    
    class Meta:
        model = Game
        fields = [
            'id', 'game_type', 'status', 'red_player', 'black_player',
            'red_player_username', 'black_player_username',
            'winner', 'move_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GameDetailSerializer(serializers.ModelSerializer):
    """对局详情序列化器"""
    
    red_player_username = serializers.CharField(source='red_player.username', read_only=True)
    black_player_username = serializers.CharField(source='black_player.username', read_only=True)
    moves = GameMoveSerializer(many=True, read_only=True)
    
    class Meta:
        model = Game
        fields = [
            'id', 'game_type', 'status', 'red_player', 'black_player',
            'red_player_username', 'black_player_username',
            'fen_start', 'fen_current', 'turn', 'winner', 'win_reason',
            'time_control_base', 'time_control_increment',
            'red_time_remaining', 'black_time_remaining',
            'ai_level', 'ai_side', 'move_count', 'duration',
            'is_rated', 'started_at', 'finished_at', 'created_at',
            'moves'
        ]
        read_only_fields = ['id', 'created_at']


class GameCreateSerializer(serializers.ModelSerializer):
    """对局创建序列化器"""
    
    class Meta:
        model = Game
        fields = [
            'game_type', 'ai_level', 'time_control_base',
            'time_control_increment', 'is_rated'
        ]
    
    def create(self, validated_data):
        """创建新对局"""
        from .fen_service import FenService
        
        # 获取当前用户
        user = self.context['request'].user
        
        # 设置初始 FEN
        validated_data['fen_start'] = FenService.get_initial_fen()
        validated_data['fen_current'] = FenService.get_initial_fen()
        validated_data['turn'] = 'w'
        validated_data['status'] = 'pending'
        
        # 单机模式：设置玩家和 AI
        if validated_data.get('game_type') == 'single':
            ai_side = self.initial_data.get('player_side', 'black')
            validated_data['ai_side'] = ai_side
            validated_data['ai_level'] = validated_data.get('ai_level', 5)
            
            # 根据选择的side设置玩家
            if ai_side == 'black':
                validated_data['red_player'] = user
            else:
                validated_data['black_player'] = user
        
        return super().create(validated_data)


class MoveCreateSerializer(serializers.Serializer):
    """走棋创建序列化器"""
    
    from_pos = serializers.CharField(max_length=3)
    to_pos = serializers.CharField(max_length=3)
    
    def validate(self, data):
        """验证走棋位置"""
        from .fen_service import FenService
        
        from_pos = data.get('from_pos')
        to_pos = data.get('to_pos')
        
        if not FenService.is_valid_position(from_pos):
            raise serializers.ValidationError(f"Invalid from position: {from_pos}")
        
        if not FenService.is_valid_position(to_pos):
            raise serializers.ValidationError(f"Invalid to position: {to_pos}")
        
        return data
