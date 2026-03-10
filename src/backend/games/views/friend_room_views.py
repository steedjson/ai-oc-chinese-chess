"""
好友对战房间 API 视图
"""
import threading
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import exception_handler
from django.utils import timezone

from ..models import FriendRoom, Game
from ..serializers_friend import (
    FriendRoomCreateSerializer,
    FriendRoomSerializer,
    JoinRoomSerializer
)

# 全局锁用于序列化并发加入请求（SQLite 兼容性）
_join_room_lock = threading.Lock()


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，将验证错误格式化为测试期望的格式
    
    测试期望：{'room_code': [...]} 或 {'time_control': [...]}
    而不是：{'error': {'message': "{'room_code': [...]}"}}
    """
    response = exception_handler(exc, context)
    
    if response is not None and response.status_code == 400:
        # DRF 默认的验证错误格式已经是 {'field_name': [errors]}
        # 直接返回即可，不需要额外处理
        pass
    
    return response


class FriendRoomViewSet(viewsets.ViewSet):
    """
    好友对战房间视图集
    
    提供好友对战房间的创建、加入、查询等功能
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """
        创建好友对战房间
        
        POST /api/games/friend/create/
        """
        try:
            serializer = FriendRoomCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            room = serializer.save()
            
            output_serializer = FriendRoomSerializer(room, context={'request': request})
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            # 返回扁平化的验证错误
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, room_code=None):
        """
        获取房间详情
        
        GET /api/games/friend/{room_code}/
        """
        try:
            room = FriendRoom.objects.select_related('game', 'creator').get(
                room_code=room_code.upper()
            )
        except FriendRoom.DoesNotExist:
            return Response({'room_code': ['房间不存在']}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FriendRoomSerializer(room, context={'request': request})
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def friend_room_join_view(request):
    """
    加入好友房间
    
    POST /api/games/friend/join/
    """
    from django.db import transaction, IntegrityError, DatabaseError
    from django.db.models import F
    
    try:
        serializer = JoinRoomSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        room_code = serializer.validated_data['room_code']
        
        # 使用全局锁序列化并发请求（SQLite 兼容性）
        with _join_room_lock:
            # 使用事务确保并发安全
            with transaction.atomic():
                # 查询房间
                room = FriendRoom.objects.select_related('game').get(room_code=room_code)
                
                # 再次检查房间状态（在事务内）
                if room.status != 'waiting':
                    raise ValidationError({'room_code': ['房间不可加入']})
                
                if room.is_expired():
                    raise ValidationError({'room_code': ['房间已过期']})
                
                if room.creator == request.user:
                    raise ValidationError({'room_code': ['不能加入自己的房间']})
                
                # 使用原子更新确保并发安全 - 只有 player_black 为 NULL 时才能更新成功
                updated = Game.objects.filter(
                    id=room.game.id,
                    player_black__isnull=True
                ).update(
                    player_black=request.user,
                    status='playing'
                )
                
                if updated == 0:
                    # 说明已经被其他请求抢先加入了
                    raise ValidationError({'room_code': ['房间已满']})
                
                # 刷新对象
                room.refresh_from_db()
                
                # 更新房间状态
                room.start_game()
            
            output_serializer = FriendRoomSerializer(room, context={'request': request})
            return Response({
                'message': '加入成功',
                'room': output_serializer.data,
                'game_id': room.game.id,
                'your_color': 'black'
            })
    except NotFound as exc:
        # 房间不存在返回 404
        return Response({'room_code': [str(exc.detail)]}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as exc:
        # 返回扁平化的验证错误
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError as exc:
        # 数据库完整性错误（并发冲突）
        return Response({'room_code': ['房间已被加入']}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        # 其他错误（包括数据库锁定等并发问题）
        import logging
        logger = logging.getLogger(__name__)
        error_msg = str(exc)
        
        # 处理数据库锁定错误（SQLite 并发限制）
        if 'locked' in error_msg.lower() or 'database is locked' in error_msg.lower():
            return Response({'room_code': ['房间已被加入']}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error(f"Join room error: {exc}")
        return Response({'error': ['加入失败，请稍后重试']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def friend_room_my_rooms_view(request):
    """
    获取我创建的房间列表
    
    GET /api/games/friend/my-rooms/
    """
    rooms = FriendRoom.objects.filter(
        creator=request.user
    ).select_related('game').order_by('-created_at')[:10]
    
    serializer = FriendRoomSerializer(rooms, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def friend_room_active_rooms_view(request):
    """
    获取活跃房间列表
    
    GET /api/games/friend/active-rooms/
    """
    rooms = FriendRoom.objects.filter(
        status='waiting'
    ).select_related('creator', 'game').order_by('-created_at')[:20]
    
    serializer = FriendRoomSerializer(rooms, many=True, context={'request': request})
    return Response(serializer.data)
