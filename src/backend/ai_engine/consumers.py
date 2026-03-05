"""
AI Engine WebSocket Consumer

提供 AI 对弈的实时通信支持
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken


class AIGameConsumer(AsyncWebsocketConsumer):
    """
    AI 对弈 WebSocket Consumer
    
    支持：
    - AI 走棋通知
    - 思考进度通知
    - 分析结果推送
    """
    
    async def connect(self):
        """建立 WebSocket 连接"""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'ai_game_{self.game_id}'
        
        # 验证用户身份
        user = await self.get_user_from_token()
        if not user:
            await self.close()
            return
        
        # 验证用户权限
        has_permission = await self.check_game_permission(str(user.id), self.game_id)
        if not has_permission:
            await self.close()
            return
        
        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 发送连接确认
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'data': {'game_id': self.game_id}
        }))
    
    async def disconnect(self, close_code):
        """断开 WebSocket 连接"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_move':
                await self.handle_request_move(data)
            elif message_type == 'request_hint':
                await self.handle_request_hint(data)
            elif message_type == 'request_analysis':
                await self.handle_request_analysis(data)
            elif message_type == 'heartbeat':
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_ack',
                    'timestamp': data.get('timestamp')
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': {'code': 'INVALID_JSON', 'message': '无效的 JSON 格式'}
            }))
    
    async def ai_thinking(self, event):
        """AI 思考中通知"""
        await self.send(text_data=json.dumps({
            'type': 'ai_thinking',
            'data': event['data']
        }))
    
    async def ai_move(self, event):
        """AI 走棋完成通知"""
        await self.send(text_data=json.dumps({
            'type': 'ai_move',
            'data': event['data']
        }))
    
    async def ai_hint(self, event):
        """AI 提示返回通知"""
        await self.send(text_data=json.dumps({
            'type': 'ai_hint',
            'data': event['data']
        }))
    
    async def ai_analysis(self, event):
        """AI 分析结果推送"""
        await self.send(text_data=json.dumps({
            'type': 'ai_analysis',
            'data': event['data']
        }))
    
    async def ai_error(self, event):
        """AI 错误通知"""
        await self.send(text_data=json.dumps({
            'type': 'ai_error',
            'data': event['data']
        }))
    
    async def handle_request_move(self, data):
        """处理请求 AI 走棋"""
        # 这里应该触发 Celery 任务
        # 简化实现：直接返回
        await self.send(text_data=json.dumps({
            'type': 'move_requested',
            'data': {'status': 'processing'}
        }))
    
    async def handle_request_hint(self, data):
        """处理请求 AI 提示"""
        await self.send(text_data=json.dumps({
            'type': 'hint_requested',
            'data': {'status': 'processing'}
        }))
    
    async def handle_request_analysis(self, data):
        """处理请求 AI 分析"""
        await self.send(text_data=json.dumps({
            'type': 'analysis_requested',
            'data': {'status': 'processing'}
        }))
    
    @database_sync_to_async
    def get_user_from_token(self):
        """从 Token 获取用户"""
        try:
            query_string = self.scope.get('query_string', b'').decode()
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')
            
            if not token:
                return None
            
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.get(id=user_id)
        
        except Exception:
            return None
    
    @database_sync_to_async
    def check_game_permission(self, user_id: str, game_id: str) -> bool:
        """检查用户是否有权访问此对局"""
        try:
            from .models import AIGame
            game = AIGame.objects.get(id=game_id)
            return str(game.player_id) == user_id
        except Exception:
            return False
