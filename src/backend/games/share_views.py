"""
棋局分享 API 视图

提供棋局分享相关的 REST API 端点：
- POST /games/{game_id}/share/ - 创建分享
- GET /games/{game_id}/shares/ - 获取分享列表
- GET /share/{token}/ - 获取分享详情
- POST /share/{token}/verify/ - 验证分享密码
- DELETE /share/{share_id}/ - 禁用分享
- GET /shares/my/ - 获取我的分享
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.decorators import api_view, permission_classes

from games.models import Game, GameShare
from games.share_service import get_share_service
from games.serializers_share import GameShareSerializer, GameShareCreateSerializer

logger = logging.getLogger(__name__)


class GameShareCreateView(APIView):
    """创建棋局分享视图"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, game_id):
        """
        创建棋局分享
        
        Request Body:
        {
            "share_type": "public",  // public/private/link
            "password": "123456",  // 私密分享需要
            "expiry_days": 7,  // 过期天数，0 表示永不过期
            "description": "精彩的对局"  // 分享说明
        }
        """
        try:
            # 获取游戏
            game = Game.objects.get(id=game_id)
            
            # 创建分享
            share_service = get_share_service()
            
            serializer = GameShareCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            share = share_service.create_share(
                game=game,
                user=request.user,
                share_type=serializer.validated_data.get('share_type', 'public'),
                password=serializer.validated_data.get('password', ''),
                expiry_days=serializer.validated_data.get('expiry_days', 7),
                description=serializer.validated_data.get('description', '')
            )
            
            if not share:
                return Response({
                    'success': False,
                    'error': '创建分享失败，请检查权限'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                'success': True,
                'data': GameShareSerializer(share).data,
                'message': '分享链接创建成功'
            }, status=status.HTTP_201_CREATED)
            
        except Game.DoesNotExist:
            raise NotFound("游戏不存在")
        except Exception as e:
            logger.error(f"创建分享失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GameSharesListView(APIView):
    """获取游戏分享列表视图"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, game_id):
        """获取游戏的所有分享"""
        try:
            # 获取游戏
            game = Game.objects.get(id=game_id)
            
            # 检查权限（只有参与者可以查看）
            if game.player_red != request.user and game.player_black != request.user:
                raise PermissionDenied("你不是此游戏的玩家")
            
            # 获取分享列表
            share_service = get_share_service()
            shares = share_service.get_game_shares(game)
            
            return Response({
                'success': True,
                'data': {
                    'shares': GameShareSerializer(shares, many=True).data,
                    'total': len(shares)
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
            logger.error(f"获取分享列表失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def share_detail_view(request, token):
    """
    获取分享详情（公开访问）
    
    GET /share/{token}/
    """
    try:
        share_service = get_share_service()
        share = share_service.get_share_by_token(token)
        
        if not share:
            return Response({
                'success': False,
                'error': '分享链接不存在或已失效'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 记录浏览
        share_service.record_view(share)
        
        return Response({
            'success': True,
            'data': {
                'share': GameShareSerializer(share).data,
                'game': {
                    'id': share.game.id,
                    'fen_current': share.game.fen_current,
                    'move_count': share.game.move_count,
                    'status': share.game.status,
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取分享详情失败：{e}", exc_info=True)
        return Response({
            'success': False,
            'error': '服务器内部错误'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShareVerifyView(APIView):
    """验证分享密码视图"""
    
    permission_classes = [AllowAny]
    
    def post(self, request, token):
        """
        验证分享密码
        
        Request Body:
        {
            "password": "123456"
        }
        """
        try:
            share_service = get_share_service()
            share = share_service.get_share_by_token(token)
            
            if not share:
                return Response({
                    'success': False,
                    'error': '分享链接不存在或已失效'
                }, status=status.HTTP_404_NOT_FOUND)
            
            password = request.data.get('password', '')
            
            if share_service.verify_password(share, password):
                return Response({
                    'success': True,
                    'message': '密码验证通过'
                })
            else:
                return Response({
                    'success': False,
                    'error': '密码错误'
                }, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            logger.error(f"验证密码失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShareDeactivateView(APIView):
    """禁用分享视图"""
    
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, share_id):
        """禁用分享链接"""
        try:
            share = GameShare.objects.get(id=share_id)
            
            share_service = get_share_service()
            success = share_service.deactivate_share(share, request.user)
            
            if success:
                return Response({
                    'success': True,
                    'message': '分享链接已禁用'
                })
            else:
                return Response({
                    'success': False,
                    'error': '无权操作此分享'
                }, status=status.HTTP_403_FORBIDDEN)
            
        except GameShare.DoesNotExist:
            raise NotFound("分享不存在")
        except Exception as e:
            logger.error(f"禁用分享失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MySharesView(APIView):
    """获取我的分享视图"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取当前用户的分享列表"""
        try:
            share_service = get_share_service()
            shares = share_service.get_user_shares(request.user, limit=50)
            
            return Response({
                'success': True,
                'data': {
                    'shares': GameShareSerializer(shares, many=True).data,
                    'total': len(shares)
                }
            })
            
        except Exception as e:
            logger.error(f"获取我的分享失败：{e}", exc_info=True)
            return Response({
                'success': False,
                'error': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
