"""
健康检查 URL 路由
"""

from django.urls import path
from .health import HealthCheckView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health'),
]
