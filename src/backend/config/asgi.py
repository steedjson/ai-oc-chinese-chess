"""
ASGI config for chinese_chess project.

支持 WebSocket 和 HTTP 协议
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 首先初始化 Django ASGI 应用
django_asgi_app = get_asgi_application()

# 导入 WebSocket 路由（必须在 get_asgi_application() 之后）
# 使用统一的 websocket 路由配置（包含所有 WebSocket 端点）
from websocket.routing import websocket_urlpatterns

# ASGI 应用配置
application = ProtocolTypeRouter({
    # HTTP 协议使用 Django 标准 ASGI 应用
    "http": django_asgi_app,
    
    # WebSocket 协议使用 Channels
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
