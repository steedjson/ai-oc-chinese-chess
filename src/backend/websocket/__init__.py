"""
WebSocket 统一配置中心

提供统一的 WebSocket 路由、配置、中间件和基础 Consumer 类。

模块结构：
- config: WebSocket 配置（心跳、超时、认证、日志等）
- middleware: WebSocket 中间件（JWT 认证、权限检查、日志等）
- consumers: 基础 Consumer 类（复用逻辑）
- routing: 统一 WebSocket 路由配置

使用示例：
    from websocket.consumers import BaseConsumer
    from websocket.middleware import JWTAuthMiddleware, PermissionMiddleware
    from websocket.config import WebSocketConfig
    
    class GameConsumer(BaseConsumer):
        async def connect(self):
            # 使用统一认证中间件
            user = await JWTAuthMiddleware().authenticate(self.scope)
            if not user:
                await self.close()
                return
            
            # 使用统一权限检查
            game_data = await self._get_game_data()
            if not PermissionMiddleware().check_game_permission(user, game_data):
                await self.close()
                return
            
            # 继续连接逻辑...
"""

__version__ = '1.0.0'
__author__ = 'Chinese Chess Team'

from .config import WebSocketConfig, get_logger
from .middleware import JWTAuthMiddleware, PermissionMiddleware, LoggingMiddleware
from .consumers import BaseConsumer

__all__ = [
    'WebSocketConfig',
    'get_logger',
    'JWTAuthMiddleware',
    'PermissionMiddleware',
    'LoggingMiddleware',
    'BaseConsumer',
]
