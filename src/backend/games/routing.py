"""
WebSocket 路由配置

定义 WebSocket 端点路由
"""
from django.urls import re_path
from . import consumers
from ai_engine import consumers as ai_consumers

# WebSocket URL 模式
websocket_urlpatterns = [
    # 游戏房间 WebSocket
    # 使用示例：ws://localhost:8000/ws/game/{game_id}/?token={jwt_token}
    re_path(r'ws/game/(?P<game_id>[^/]+)/$', consumers.GameConsumer.as_asgi()),
    
    # AI 对弈 WebSocket
    # 使用示例：ws://localhost:8000/ws/ai/game/{game_id}/?token={jwt_token}
    re_path(r'ws/ai/game/(?P<game_id>[^/]+)/$', ai_consumers.AIGameConsumer.as_asgi()),
]
