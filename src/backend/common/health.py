"""
健康检查 API

提供系统健康状态检查端点
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import django
from django.db import connections
from django.core.cache import cache


class HealthCheckView(APIView):
    """
    健康检查视图
    
    检查系统各组件的健康状态：
    - Django 应用状态
    - 数据库连接
    - 缓存服务
    - Python 版本
    """
    
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'components': {}
        }
        
        overall_healthy = True
        
        # 检查 Django 应用
        health_status['components']['django'] = {
            'status': 'healthy',
            'version': django.get_version()
        }
        
        # 检查数据库连接
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
            health_status['components']['database'] = {
                'status': 'healthy',
                'backend': db_conn.settings_dict['ENGINE']
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # 检查缓存服务
        try:
            cache.set('health_check', 'ok', timeout=1)
            result = cache.get('health_check')
            if result == 'ok':
                health_status['components']['cache'] = {
                    'status': 'healthy',
                    'backend': cache.__class__.__name__
                }
            else:
                raise Exception("Cache read/write mismatch")
        except Exception as e:
            health_status['components']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_healthy = False
        
        # 检查 Python 版本
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        health_status['components']['python'] = {
            'status': 'healthy',
            'version': python_version
        }
        
        # 更新总体状态
        if not overall_healthy:
            health_status['status'] = 'unhealthy'
        
        # 返回适当的 HTTP 状态码
        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_status, status=http_status)


# 用于 URL 路由的简单视图函数
def health_check(request):
    """健康检查函数视图"""
    from rest_framework.request import Request
    from rest_framework.parsers import JSONParser
    
    drf_request = Request(request)
    view = HealthCheckView()
    return view.get(drf_request)
