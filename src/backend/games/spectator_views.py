"""
观战系统 API 视图

提供观战相关的 REST API 接口
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models as django_models

from .models import Game
from .spectator import Spectator, SpectatorManager, SpectatorStatus
from .serializers_backup import GameListSerializer


class SpectatorViewSet(viewsets.ViewSet):
    """
    观战视图集
    
    提供观战相关的 API 接口
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def spectate(self, request, pk=None):
        """
        加入观战
        
        POST /api/v1/games/:id/spectate/
        
        Request:
        {
            "is_anonymous": false  // 可选，是否匿名观战
        }
        
        Response:
        {
            "success": true,
            "spectator": {
                "id": "uuid",
                "game_id": "uuid",
                "user_id": "uuid",
                "joined_at": "ISO8601",
                "is_anonymous": false
            },
            "game_state": {...}  // 当前游戏状态
        }
        """
        game_id = pk
        user = request.user
        is_anonymous = request.data.get('is_anonymous', False)
        
        # 加入观战
        result = SpectatorManager.join_spectate(
            game_id=game_id,
            user_id=str(user.id),
            is_anonymous=is_anonymous
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        spectator = result['spectator']
        
        # 获取游戏状态
        game = spectator.game
        game_state = {
            'id': str(game.id),
            'fen': game.fen_current,
            'turn': game.turn,
            'status': game.status,
            'move_count': game.move_count,
            'red_player': {
                'id': str(game.red_player.id) if game.red_player else None,
                'username': game.red_player.username if game.red_player else None
            },
            'black_player': {
                'id': str(game.black_player.id) if game.black_player else None,
                'username': game.black_player.username if game.black_player else None
            }
        }
        
        return Response({
            'success': True,
            'spectator': {
                'id': str(spectator.id),
                'game_id': str(spectator.game.id),
                'user_id': str(spectator.user.id) if not spectator.is_anonymous else None,
                'joined_at': spectator.joined_at.isoformat(),
                'is_anonymous': spectator.is_anonymous
            },
            'game_state': game_state,
            'message': result.get('message', '加入观战成功')
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        离开观战
        
        POST /api/v1/games/:id/spectate/leave/
        
        Response:
        {
            "success": true,
            "duration": 120  // 观战时长（秒）
        }
        """
        game_id = pk
        user = request.user
        
        result = SpectatorManager.leave_spectate(
            game_id=game_id,
            user_id=str(user.id)
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'duration': result.get('duration', 0),
            'message': '离开观战成功'
        })
    
    @action(detail=True, methods=['get'])
    def spectators(self, request, pk=None):
        """
        获取观战列表
        
        GET /api/v1/games/:id/spectators/
        
        Response:
        {
            "count": 10,
            "spectators": [
                {
                    "id": "uuid",
                    "user_id": "uuid",
                    "username": "xxx",
                    "joined_at": "ISO8601",
                    "duration": 120,
                    "is_anonymous": false
                }
            ]
        }
        """
        game_id = pk
        limit = request.query_params.get('limit', 50)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 50
        
        spectators_list = SpectatorManager.get_spectators(game_id=game_id, limit=limit)
        
        return Response({
            'count': len(spectators_list),
            'spectators': spectators_list
        })
    
    @action(detail=True, methods=['post'])
    def kick(self, request, pk=None):
        """
        踢出观战者（仅游戏创建者或管理员）
        
        POST /api/v1/games/:id/spectators/:spectator_id/kick/
        
        Request:
        {
            "spectator_id": "uuid"
        }
        
        Response:
        {
            "success": true,
            "message": "已将 xxx 踢出观战"
        }
        """
        game_id = pk
        user = request.user
        spectator_id = request.data.get('spectator_id')
        
        if not spectator_id:
            return Response({
                'success': False,
                'error': '缺少 spectator_id 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = SpectatorManager.kick_spectator(
            game_id=game_id,
            spectator_id=spectator_id,
            operator_id=str(user.id)
        )
        
        if not result['success']:
            status_code = status.HTTP_403_FORBIDDEN if '权限' in result.get('error', '') else status.HTTP_400_BAD_REQUEST
            return Response({
                'success': False,
                'error': result['error']
            }, status=status_code)
        
        return Response({
            'success': True,
            'message': result['message']
        })
    
    @action(detail=False, methods=['get'])
    def active_games(self, request):
        """
        获取可观看的对局列表
        
        GET /api/v1/spectator/active-games/?limit=20
        
        Response:
        {
            "count": 10,
            "games": [
                {
                    "id": "uuid",
                    "status": "playing",
                    "move_count": 15,
                    "spectator_count": 5,
                    "red_player": {...},
                    "black_player": {...}
                }
            ]
        }
        """
        limit = request.query_params.get('limit', 20)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 20
        
        # 获取进行中的游戏，按观战人数排序
        games = Game.objects.filter(
            status='playing'
        ).annotate(
            spectator_count=django_models.Count(
                'spectators',
                filter=django_models.Q(spectators__status=SpectatorStatus.WATCHING)
            )
        ).order_by('-spectator_count', '-move_count')[:limit]
        
        games_data = []
        for game in games:
            games_data.append({
                'id': str(game.id),
                'status': game.status,
                'move_count': game.move_count,
                'spectator_count': game.spectator_count,
                'red_player': {
                    'id': str(game.red_player.id) if game.red_player else None,
                    'username': game.red_player.username if game.red_player else None,
                    'rating': game.red_player.rating if game.red_player else None
                },
                'black_player': {
                    'id': str(game.black_player.id) if game.black_player else None,
                    'username': game.black_player.username if game.black_player else None,
                    'rating': game.black_player.rating if game.black_player else None
                },
                'time_control': {
                    'base': game.time_control_base,
                    'increment': game.time_control_increment
                },
                'created_at': game.created_at.isoformat()
            })
        
        return Response({
            'count': len(games_data),
            'games': games_data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_spectator_info(request, game_id, spectator_id):
    """
    获取观战者详细信息
    
    GET /api/v1/games/:game_id/spectators/:id/
    """
    from uuid import UUID
    
    try:
        spectator = Spectator.objects.select_related('user').get(
            id=UUID(spectator_id),
            game_id=UUID(game_id)
        )
        
        # 权限检查：只能查看自己的信息，或者是游戏参与者/管理员
        user = request.user
        is_self = str(spectator.user.id) == str(user.id)
        is_game_participant = (
            (spectator.game.red_player and str(spectator.game.red_player.id) == str(user.id)) or
            (spectator.game.black_player and str(spectator.game.black_player.id) == str(user.id))
        )
        
        if not is_self and not is_game_participant and not user.is_staff:
            return Response({
                'error': '无权限查看此信息'
            }, status=status.HTTP_403_FORBIDDEN)
        
        duration = 0
        if spectator.status == SpectatorStatus.WATCHING:
            duration = int((timezone.now() - spectator.joined_at).total_seconds())
        elif spectator.duration:
            duration = spectator.duration
        
        return Response({
            'id': str(spectator.id),
            'game_id': str(spectator.game.id),
            'user': {
                'id': str(spectator.user.id),
                'username': spectator.user.username
            },
            'status': spectator.status,
            'joined_at': spectator.joined_at.isoformat(),
            'left_at': spectator.left_at.isoformat() if spectator.left_at else None,
            'duration': duration,
            'is_anonymous': spectator.is_anonymous
        })
        
    except Spectator.DoesNotExist:
        return Response({
            'error': '观战记录不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
