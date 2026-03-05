"""
WebSocket 统一路由配置

集中管理所有 WebSocket 路由，提供统一的路由注册和配置。

路由列表：
- /ws/game/{game_id}/ - 游戏对弈
- /ws/ai/game/{game_id}/ - AI 对弈
- /ws/matchmaking/ - 匹配系统

使用方式：
    在 config/asgi.py 中：
        from websocket.routing import websocket_urlpatterns
        
        application = ProtocolTypeRouter({
            "http": get_asgi_application(),
            "websocket": AllowedHostsOriginValidator(
                AuthMiddlewareStack(
                    URLRouter(websocket_urlpatterns)
                )
            ),
        })
"""
from django.urls import re_path, path

# 导入各模块的 Consumer
from games.consumers import GameConsumer
from ai_engine.consumers import AIGameConsumer
from matchmaking.consumers import MatchmakingConsumer


# WebSocket URL 模式
# 所有路由统一在此处配置，便于管理和维护
websocket_urlpatterns = [
    # ========== 游戏对弈 ==========
    # 路由：/ws/game/{game_id}/
    # 说明：在线对战游戏房间
    # 参数：game_id - 游戏对局 ID
    # 认证：需要 JWT Token
    # 示例：ws://localhost:8000/ws/game/12345/?token=eyJhbG...
    re_path(
        r'ws/game/(?P<game_id>[^/]+)/$',
        GameConsumer.as_asgi(),
        name='ws-game'
    ),
    
    # ========== AI 对弈 ==========
    # 路由：/ws/ai/game/{game_id}/
    # 说明：AI 对弈房间
    # 参数：game_id - AI 对局 ID
    # 认证：需要 JWT Token
    # 示例：ws://localhost:8000/ws/ai/game/67890/?token=eyJhbG...
    re_path(
        r'ws/ai/game/(?P<game_id>[^/]+)/$',
        AIGameConsumer.as_asgi(),
        name='ws-ai-game'
    ),
    
    # ========== 匹配系统 ==========
    # 路由：/ws/matchmaking/
    # 说明：匹配队列
    # 认证：需要 JWT Token
    # 示例：ws://localhost:8000/ws/matchmaking/?token=eyJhbG...
    re_path(
        r'ws/matchmaking/$',
        MatchmakingConsumer.as_asgi(),
        name='ws-matchmaking'
    ),
]


# 路由配置信息
# 用于文档生成和运行时检查
ROUTE_CONFIG = {
    'game': {
        'pattern': r'ws/game/(?P<game_id>[^/]+)/$',
        'consumer': 'games.consumers.GameConsumer',
        'description': '游戏对弈房间',
        'auth_required': True,
        'parameters': ['game_id'],
    },
    'ai_game': {
        'pattern': r'ws/ai/game/(?P<game_id>[^/]+)/$',
        'consumer': 'ai_engine.consumers.AIGameConsumer',
        'description': 'AI 对弈房间',
        'auth_required': True,
        'parameters': ['game_id'],
    },
    'matchmaking': {
        'pattern': r'ws/matchmaking/$',
        'consumer': 'matchmaking.consumers.MatchmakingConsumer',
        'description': '匹配队列',
        'auth_required': True,
        'parameters': [],
    },
}


def get_route_config(route_name: str) -> dict:
    """
    获取路由配置信息
    
    Args:
        route_name: 路由名称 ('game', 'ai_game', 'matchmaking')
    
    Returns:
        路由配置字典
    """
    return ROUTE_CONFIG.get(route_name, {})


def get_all_routes() -> dict:
    """
    获取所有路由配置
    
    Returns:
        所有路由配置字典
    """
    return ROUTE_CONFIG.copy()


def validate_route(route_name: str) -> bool:
    """
    验证路由是否存在
    
    Args:
        route_name: 路由名称
    
    Returns:
        路由是否存在
    """
    return route_name in ROUTE_CONFIG
