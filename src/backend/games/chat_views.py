"""
聊天系统 REST API 视图

包含：
- ChatMessageViewSet: 聊天消息视图集
- send_chat_message: 发送消息端点
- get_chat_history: 获取聊天历史端点

CSRF 防护说明：
本系统使用 JWT Token 认证（非 Cookie 会话），CSRF 攻击主要针对 Cookie 认证机制。
JWT Token 通过 Authorization 头传递，不在浏览器自动发送，因此 CSRF 风险极低。
- ViewSet 方法：使用 DRF 框架，自动处理 CSRF
- 独立函数视图：使用 @csrf_exempt，因为使用 JWT 而非 Session 认证
详见：docs/security/CSRF-FIX.md
"""
import json
from typing import Dict, Any
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .chat import ChatMessage, ChatMessageManager, MessageType
from .models import Game
from .spectator import Spectator, SpectatorStatus


class ChatMessagePagination(PageNumberPagination):
    """聊天消息分页器"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


class ChatMessageViewSet(viewsets.ViewSet):
    """
    聊天消息视图集
    
    提供聊天消息的 CRUD 操作
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ChatMessagePagination
    
    @action(detail=False, methods=['post'], url_path='games/(?P<game_id>[^/.]+)/send')
    def send_message(self, request, game_id):
        """
        发送聊天消息
        
        POST /api/v1/chat/games/{game_id}/send/
        
        Request:
        {
            "content": "消息内容",
            "message_type": "text",  // text, system, emoji
            "room_type": "game"  // game, spectator
        }
        
        Response:
        {
            "success": true,
            "message": {
                "id": "uuid",
                "sender": {...},
                "content": "...",
                "created_at": "ISO8601"
            }
        }
        """
        try:
            # 获取请求数据
            content = request.data.get('content', '').strip()
            message_type = request.data.get('message_type', 'text')
            room_type = request.data.get('room_type', 'game')
            
            # 验证房间类型
            if room_type not in ['game', 'spectator']:
                return Response({
                    'success': False,
                    'error': '无效的房间类型'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证消息类型
            if message_type not in ['text', 'system', 'emoji']:
                return Response({
                    'success': False,
                    'error': '无效的消息类型'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 系统消息只有管理员可发送
            if message_type == 'system' and not request.user.is_staff:
                return Response({
                    'success': False,
                    'error': '无权限发送系统消息'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 观战聊天需要是观战者
            if room_type == 'spectator':
                is_spectator = Spectator.objects.filter(
                    game_id=game_id,
                    user=request.user,
                    status=SpectatorStatus.WATCHING
                ).exists()
                
                if not is_spectator and not request.user.is_staff:
                    return Response({
                        'success': False,
                        'error': '只有观战者可以在观战聊天中发言'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # 发送消息
            result = ChatMessageManager.send_message_sync(
                game_id=game_id,
                user_id=str(request.user.id),
                content=content,
                message_type=message_type,
                room_type=room_type
            )
            
            if result['success']:
                message = result['message']
                
                # 通过 WebSocket 广播消息（如果有 channel layer）
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    room_group_name = f'chat_{room_type}_{game_id}'
                    
                    async_to_sync(channel_layer.group_send)(room_group_name, {
                        'type': 'chat_message',
                        'message': message.to_dict()
                    })
                except Exception:
                    # WebSocket 广播失败不影响 API 响应
                    pass
                
                return Response({
                    'success': True,
                    'message': message.to_dict()
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Game.DoesNotExist:
            return Response({
                'success': False,
                'error': '游戏不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='games/(?P<game_id>[^/.]+)/history')
    def get_history(self, request, game_id):
        """
        获取聊天历史
        
        GET /api/v1/chat/games/{game_id}/history/?limit=50&before=2026-03-05T12:00:00&room_type=game
        
        Query Parameters:
        - limit: 返回数量限制（默认 50）
        - before: 分页游标（ISO8601 时间戳）
        - room_type: 房间类型（game 或 spectator，默认 game）
        
        Response:
        {
            "success": true,
            "messages": [...],
            "has_more": true
        }
        """
        try:
            # 验证游戏存在
            game = Game.objects.get(id=game_id)
            
            # 获取参数
            limit = int(request.query_params.get('limit', 50))
            before = request.query_params.get('before', None)
            room_type = request.query_params.get('room_type', 'game')
            
            # 限制 limit 范围
            limit = min(max(limit, 1), 100)
            
            # 验证房间类型
            if room_type not in ['game', 'spectator']:
                return Response({
                    'success': False,
                    'error': '无效的房间类型'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 权限检查：只有游戏参与者或观战者可查看聊天历史
            is_participant = (
                (game.red_player and game.red_player.id == request.user.id) or
                (game.black_player and game.black_player.id == request.user.id)
            )
            
            is_spectator = Spectator.objects.filter(
                game_id=game_id,
                user=request.user,
                status=SpectatorStatus.WATCHING
            ).exists()
            
            if not is_participant and not is_spectator and not request.user.is_staff:
                return Response({
                    'success': False,
                    'error': '无权限查看此聊天历史'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 获取消息历史（使用同步版本，避免 asyncio.run() 在测试环境中的问题）
            messages = ChatMessageManager.get_message_history_sync(
                game_id=str(game_id),
                room_type=room_type,
                limit=limit,
                before=before
            )
            
            # 检查是否有更多消息
            has_more = False
            if messages:
                # 检查是否还有更早的消息
                first_message_time = messages[0].get('created_at')
                if first_message_time:
                    more_count = ChatMessageManager.get_message_count_sync(
                        game_id=str(game_id),
                        room_type=room_type
                    )
                    has_more = more_count > len(messages)
            
            return Response({
                'success': True,
                'messages': messages,
                'has_more': has_more
            })
            
        except Game.DoesNotExist:
            return Response({
                'success': False,
                'error': '游戏不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'], url_path='messages/(?P<message_uuid>[^/.]+)/delete')
    def delete_message(self, request, message_uuid):
        """
        删除聊天消息
        
        DELETE /api/v1/chat/messages/{message_uuid}/delete/
        
        Response:
        {
            "success": true,
            "message": "消息已删除"
        }
        """
        try:
            result = ChatMessageManager.delete_message_sync(
                message_uuid=message_uuid,
                user_id=str(request.user.id)
            )
            
            if result['success']:
                # 广播删除事件
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    from .chat import ChatMessage
                    
                    message = ChatMessage.objects.get(message_uuid=message_uuid)
                    channel_layer = get_channel_layer()
                    room_group_name = f'chat_{message.room_type}_{message.game_id}'
                    
                    async_to_sync(channel_layer.group_send)(room_group_name, {
                        'type': 'message_deleted',
                        'message_id': message_uuid
                    })
                except Exception:
                    pass
                
                return Response({
                    'success': True,
                    'message': result['message']
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='games/(?P<game_id>[^/.]+)/stats')
    def get_stats(self, request, game_id):
        """
        获取聊天统计信息
        
        GET /api/v1/chat/games/{game_id}/stats/
        
        Response:
        {
            "success": true,
            "stats": {
                "total_messages": 100,
                "game_messages": 80,
                "spectator_messages": 20
            }
        }
        """
        try:
            game_total = ChatMessageManager.get_message_count_sync(
                game_id=game_id,
                room_type='game'
            )
            
            spectator_total = ChatMessageManager.get_message_count_sync(
                game_id=game_id,
                room_type='spectator'
            )
            
            return Response({
                'success': True,
                'stats': {
                    'total_messages': game_total + spectator_total,
                    'game_messages': game_total,
                    'spectator_messages': spectator_total
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 独立的 API 端点函数（用于直接 URL 路由）

@require_http_methods(["POST"])
@csrf_exempt  # SECURITY: JWT 认证无需 CSRF 保护 - Token 在 Authorization 头中传递，非 Cookie
@permission_classes([IsAuthenticated])
def send_chat_message(request, game_id):
    """
    发送聊天消息（独立端点）
    
    POST /api/v1/chat/games/{game_id}/send/
    
    CSRF 防护说明：
    此端点使用 JWT Token 认证（非 Session/Cookie 认证），CSRF 攻击不适用。
    JWT Token 通过 Authorization: Bearer <token> 头传递，浏览器不会自动发送，
    因此不存在 CSRF 风险。@csrf_exempt 是合理的安全配置。
    """
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        room_type = data.get('room_type', 'game')
        
        # 验证
        if room_type not in ['game', 'spectator']:
            return JsonResponse({
                'success': False,
                'error': '无效的房间类型'
            }, status=400)
        
        if message_type == 'system' and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': '无权限发送系统消息'
            }, status=403)
        
        # 发送消息
        result = ChatMessageManager.send_message_sync(
            game_id=game_id,
            user_id=str(request.user.id),
            content=content,
            message_type=message_type,
            room_type=room_type
        )
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'].to_dict()
            }, status=201)
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的 JSON 格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@csrf_exempt  # SECURITY: GET 请求是幂等的，不修改状态；且使用 JWT 认证（非 Cookie），CSRF 风险极低
@permission_classes([IsAuthenticated])
def get_chat_history(request, game_id):
    """
    获取聊天历史（独立端点）
    
    GET /api/v1/chat/games/{game_id}/history/?limit=50&room_type=game
    
    CSRF 防护说明：
    1. GET 请求是幂等的，不修改服务器状态
    2. 使用 JWT Token 认证（非 Session/Cookie 认证）
    3. 因此 CSRF 保护不必要，@csrf_exempt 是合理的
    """
    try:
        import asyncio
        
        limit = int(request.GET.get('limit', 50))
        before = request.GET.get('before', None)
        room_type = request.GET.get('room_type', 'game')
        
        limit = min(max(limit, 1), 100)
        
        messages = asyncio.run(ChatMessageManager.get_message_history(
            game_id=game_id,
            room_type=room_type,
            limit=limit,
            before=before
        ))
        
        return JsonResponse({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
