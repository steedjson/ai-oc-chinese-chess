"""
好友对战房间 API 视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.utils import timezone

from ..models import FriendRoom, Game
from .serializers.friend_room import (
    FriendRoomCreateSerializer,
    FriendRoomSerializer,
    JoinRoomSerializer
)


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
        serializer = FriendRoomCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        
        output_serializer = FriendRoomSerializer(room, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
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
            raise NotFound('房间不存在')
        
        serializer = FriendRoomSerializer(room, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def join(self, request):
        """
        加入好友房间
        
        POST /api/games/friend/join/
        """
        serializer = JoinRoomSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        room_code = serializer.validated_data['room_code']
        room = FriendRoom.objects.select_related('game').get(room_code=room_code)
        
        # 加入游戏（作为黑方）
        game = room.game
        game.player_black = request.user
        game.status = 'playing'
        game.save()
        
        # 更新房间状态
        room.start_game()
        
        output_serializer = FriendRoomSerializer(room, context={'request': request})
        return Response({
            'message': '加入成功',
            'room': output_serializer.data,
            'game_id': game.id,
            'your_color': 'black'
        })
    
    @action(detail=False, methods=['get'])
    def my_rooms(self, request):
        """
        获取我创建的房间列表
        
        GET /api/games/friend/my_rooms/
        """
        rooms = FriendRoom.objects.filter(
            creator=request.user
        ).select_related('game').order_by('-created_at')[:10]
        
        serializer = FriendRoomSerializer(rooms, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_rooms(self, request):
        """
        获取活跃房间列表
        
        GET /api/games/friend/active_rooms/
        """
        rooms = FriendRoom.objects.filter(
            status='waiting'
        ).select_related('creator', 'game').order_by('-created_at')[:20]
        
        serializer = FriendRoomSerializer(rooms, many=True, context={'request': request})
        return Response(serializer.data)


# 导出视图集实例
friend_room_viewset = FriendRoomViewSet.as_view({
    'post': 'create',
    'get': 'retrieve',
})

friend_room_join_view = FriendRoomViewSet.as_view({
    'post': 'join',
})

friend_room_my_rooms_view = FriendRoomViewSet.as_view({
    'get': 'my_rooms',
})

friend_room_active_rooms_view = FriendRoomViewSet.as_view({
    'get': 'active_rooms',
})
