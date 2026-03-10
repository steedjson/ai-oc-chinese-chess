"""
WebSocket 路由配置

定义 WebSocket 端点路由
"""
from django.urls import re_path
from . import consumers
from .spectator_consumer import SpectatorConsumer
from .chat_consumer import ChatConsumer
from ai_engine import consumers as ai_consumers

# WebSocket URL 模式
websocket_urlpatterns = [
    # 游戏房间 WebSocket
    # 使用示例：ws://localhost:8000/ws/game/{game_id}/?token={jwt_token}
    re_path(r'ws/game/(?P<game_id>[^/]+)/$', consumers.GameConsumer.as_asgi()),
    
    # AI 对弈 WebSocket
    # 使用示例：ws://localhost:8000/ws/ai/game/{game_id}/?token={jwt_token}
    re_path(r'ws/ai/game/(?P<game_id>[^/]+)/$', ai_consumers.AIGameConsumer.as_asgi()),
    
    # 观战 WebSocket
    # 使用示例：ws://localhost:8000/ws/spectate/{game_id}/?token={jwt_token}
    re_path(r'ws/spectate/(?P<game_id>[^/]+)/$', SpectatorConsumer.as_asgi()),
    
    # 聊天 WebSocket
    # 对局聊天：ws://localhost:8000/ws/chat/game/{game_id}/?token={jwt_token}
    # 观战聊天：ws://localhost:8000/ws/chat/spectator/{game_id}/?token={jwt_token}
    re_path(r'ws/chat/(?P<room_type>game|spectator)/(?P<game_id>[^/]+)/$', ChatConsumer.as_asgi()),
]
