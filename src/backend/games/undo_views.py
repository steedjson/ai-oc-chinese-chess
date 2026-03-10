"""
悔棋 API 视图

提供悔棋相关的 REST API 端点：
- POST /games/{game_id}/undo/request/ - 请求悔棋
- POST /games/{game_id}/undo/respond/ - 响应悔棋
- GET /games/{game_id}/undo/requests/ - 获取悔棋历史
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from games.models import Game, UndoRequest
from games.undo_service import get_undo_service
from games.serializers_undo import UndoRequestSerializer

logger = logging.getLogger(__name__)


class UndoRequestView(APIView):
    """请求悔棋视图"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, game_id):
        """
        请求悔棋
        
        Request Body:
        {
            "undo_count": 1,  // 悔棋步数，默认 1
            "reason": "不小心点错了"  // 悔棋原因，可选
        }
        """
        try:
            # 获取游戏
            game = Game.objects.get(id=game_id)
            
            # 检查玩家权限
            if game.player_red != request.user and game.player_black != request.user:
                raise PermissionDenied("你不是此游戏的玩家")
            
            # 获取请求参数
            undo_count = request.data.get('undo_count', 1)
            reason = request.data.get('reason', '')
            
            # 验证悔棋步数
            if not isinstance(undo_count, int) or undo_count < 1 or undo_count > 3:
                raise ValidationError("悔棋步数必须是 1-3 之间的整数")
            
            # 执行悔棋请求
            undo_service = get_undo_service()
            undo_request = undo_service.request_undo(
                game=game,
                player=request.user,
                undo_count=undo_count,
                reason=reason
            )
            
            if not undo_request:
                return Response({
                    'success': False,
                    'error': '悔棋请求失败，请检查是否满足悔棋条件'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'data': UndoRequestSerializer(undo_request).data,
                'message': '悔棋请求已发送，等待对手确认'
            }, status=status.HTTP_201_CREATED)
            
        except Game.DoesNotExist:
            raise NotFound("游戏不存在")
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"悔棋请求失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UndoRespondView(APIView):
    """响应悔棋视图"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, game_id):
        """
        响应悔棋请求
        
        Request Body:
        {
            "request_id": 123,  // 悔棋请求 ID
            "accept": true  // 是否接受
        }
        """
        try:
            # 获取游戏
            game = Game.objects.get(id=game_id)
            
            # 检查玩家权限
            if game.player_red != request.user and game.player_black != request.user:
                raise PermissionDenied("你不是此游戏的玩家")
            
            # 获取请求参数
            request_id = request.data.get('request_id')
            accept = request.data.get('accept')
            
            if not request_id:
                raise ValidationError("缺少悔棋请求 ID")
            
            if accept is None:
                raise ValidationError("缺少 accept 参数")
            
            # 获取悔棋请求
            try:
                undo_request = UndoRequest.objects.get(
                    id=request_id,
                    game=game
                )
            except UndoRequest.DoesNotExist:
                raise NotFound("悔棋请求不存在")
            
            # 检查是否是对手
            if undo_request.requester == request.user:
                raise PermissionDenied("你不能响应自己的悔棋请求")
            
            # 响应悔棋
            undo_service = get_undo_service()
            success = undo_service.respond_to_undo(
                undo_request=undo_request,
                responder=request.user,
                accept=accept
            )
            
            if not success:
                return Response({
                    'success': False,
                    'error': '响应悔棋失败'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'data': {
                    'request_id': undo_request.id,
                    'accepted': accept,
                    'status': undo_request.get_status_display()
                },
                'message': f'已{"接受" if accept else "拒绝"}悔棋请求'
            })
            
        except Game.DoesNotExist:
            raise NotFound("游戏不存在")
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"响应悔棋失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UndoHistoryView(APIView):
    """悔棋历史视图"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, game_id):
        """获取游戏的悔棋历史"""
        try:
            # 获取游戏
            game = Game.objects.get(id=game_id)
            
            # 检查玩家权限
            if game.player_red != request.user and game.player_black != request.user:
                raise PermissionDenied("你不是此游戏的玩家")
            
            # 获取悔棋历史
            undo_requests = UndoRequest.objects.filter(
                game=game
            ).order_by('-requested_at')
            
            return Response({
                'success': True,
                'data': {
                    'requests': UndoRequestSerializer(undo_requests, many=True).data,
                    'undo_limit': game.undo_limit,
                    'undo_count_red': game.undo_count_red,
                    'undo_count_black': game.undo_count_black
                }
            })
            
        except Game.DoesNotExist:
            raise NotFound("游戏不存在")
        except PermissionDenied as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"获取悔棋历史失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
