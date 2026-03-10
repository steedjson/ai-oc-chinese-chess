"""
健康检查 API URL 路由

端点：
- GET /api/health/ - 综合健康检查
- GET /api/health/db/ - 数据库状态
- GET /api/health/redis/ - Redis 状态
- GET /api/health/websocket/ - WebSocket 状态
"""

from django.urls import path
from .views import (
    ComprehensiveHealthView,
    DatabaseHealthView,
    RedisHealthView,
    WebSocketHealthView,
)

urlpatterns = [
    # 综合健康检查
    path('', ComprehensiveHealthView.as_view(), name='health-comprehensive'),
    
    # 组件健康检查
    path('db/', DatabaseHealthView.as_view(), name='health-database'),
    path('redis/', RedisHealthView.as_view(), name='health-redis'),
    path('websocket/', WebSocketHealthView.as_view(), name='health-websocket'),
]
