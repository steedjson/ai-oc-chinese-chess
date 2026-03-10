"""
健康检查 API 视图

提供系统各组件的健康状态检测：
- 综合健康检查
- 数据库连接状态
- Redis 连接状态
- WebSocket 服务状态
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connections
from django.core.cache import cache
from django.conf import settings

# 导入 Channels 相关模块
try:
    from channels.layers import get_channel_layer
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    get_channel_layer = None


class BaseHealthView(APIView):
    """健康检查基类"""
    
    authentication_classes = []
    permission_classes = []
    
    def get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    def check_component(self, name: str, check_func, timeout: int = 5) -> Dict[str, Any]:
        """
        检查组件状态
        
        Args:
            name: 组件名称
            check_func: 检查函数
            timeout: 超时时间（秒）
            
        Returns:
            组件状态字典
        """
        start_time = time.time()
        try:
            result = check_func()
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'timestamp': self.get_timestamp(),
                **result
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': round(response_time, 2),
                'timestamp': self.get_timestamp()
            }


class DatabaseHealthView(BaseHealthView):
    """数据库健康检查视图"""
    
    def check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        db_conn = connections['default']
        
        # 确保连接
        db_conn.ensure_connection()
        
        # 获取数据库信息
        db_settings = db_conn.settings_dict
        
        # 执行简单查询测试
        with db_conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            if result[0] != 1:
                raise Exception("Database query returned unexpected result")
        
        # 获取数据库版本
        db_version = None
        try:
            with db_conn.cursor() as cursor:
                if 'sqlite' in db_settings['ENGINE']:
                    cursor.execute('SELECT sqlite_version()')
                elif 'postgresql' in db_settings['ENGINE']:
                    cursor.execute('SELECT version()')
                elif 'mysql' in db_settings['ENGINE']:
                    cursor.execute('SELECT version()')
                
                db_version = cursor.fetchone()[0]
        except Exception:
            pass  # 可选，不影响健康状态
        
        # 将 NAME 转换为字符串（可能是 PosixPath）
        db_name = str(db_settings['NAME']) if db_settings['NAME'] else None
        
        return {
            'engine': db_settings['ENGINE'],
            'name': db_name,
            'version': db_version
        }
    
    def get(self, request):
        result = self.check_component('database', self.check_database)
        
        http_status = (
            status.HTTP_200_OK 
            if result['status'] == 'healthy' 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return Response({
            'component': 'database',
            **result
        }, status=http_status)


class RedisHealthView(BaseHealthView):
    """Redis 健康检查视图"""
    
    def check_redis(self) -> Dict[str, Any]:
        """检查 Redis 连接"""
        # 使用 Django cache 后端检查 Redis
        try:
            # 测试写入
            test_key = 'health_check:test_key'
            test_value = 'test_value'
            cache.set(test_key, test_value, timeout=5)
            
            # 测试读取
            result = cache.get(test_key)
            if result != test_value:
                raise Exception("Cache read/write mismatch")
            
            # 测试删除
            cache.delete(test_key)
            
            # 获取缓存后端信息
            cache_backend = cache.__class__.__name__
            
            # 尝试获取 Redis 信息（如果是 Redis 后端）
            redis_info = {}
            try:
                # 对于 RedisCache，尝试获取客户端
                if hasattr(cache, '_client'):
                    client = cache._client
                    if hasattr(client, 'info'):
                        redis_info['redis_version'] = client.info().get('redis_version')
            except Exception:
                pass  # 可选信息
            
            return {
                'backend': cache_backend,
                'location': getattr(settings, 'REDIS_URL', 'configured'),
                **redis_info
            }
        except Exception as e:
            # 如果 cache 不是 Redis，尝试直接连接
            raise e
    
    def get(self, request):
        result = self.check_component('redis', self.check_redis)
        
        http_status = (
            status.HTTP_200_OK 
            if result['status'] == 'healthy' 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return Response({
            'component': 'redis',
            **result
        }, status=http_status)


class WebSocketHealthView(BaseHealthView):
    """WebSocket 健康检查视图"""
    
    def check_websocket(self) -> Dict[str, Any]:
        """检查 WebSocket 服务状态"""
        if not CHANNELS_AVAILABLE:
            raise Exception("Channels library not available")
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            raise Exception("Channel layer not configured")
        
        # 检查 channel layer 类型
        layer_type = channel_layer.__class__.__name__
        
        # 如果是内存层，检查是否可用
        if 'InMemory' in layer_type:
            return {
                'backend': layer_type,
                'status': 'development_mode',
                'note': 'Using in-memory channel layer (development only)'
            }
        
        # 如果是 Redis 层，测试连接
        if 'Redis' in layer_type:
            try:
                # 尝试发送和接收消息
                test_channel = 'health_check_test'
                test_message = {'type': 'health.check', 'data': 'test'}
                
                # 对于异步 channel layer，需要同步调用
                if hasattr(channel_layer, 'send'):
                    # 同步包装器
                    from asgiref.sync import async_to_sync
                    async_to_sync(channel_layer.send)(test_channel, test_message)
                
                return {
                    'backend': layer_type,
                    'config': getattr(settings, 'CHANNEL_LAYERS', {})
                }
            except Exception as e:
                raise Exception(f"Redis channel layer error: {str(e)}")
        
        return {
            'backend': layer_type
        }
    
    def get(self, request):
        result = self.check_component('websocket', self.check_websocket)
        
        http_status = (
            status.HTTP_200_OK 
            if result['status'] == 'healthy' 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return Response({
            'component': 'websocket',
            **result
        }, status=http_status)


class ComprehensiveHealthView(BaseHealthView):
    """综合健康检查视图"""
    
    def check_all_components(self) -> Dict[str, Any]:
        """检查所有组件"""
        components = {}
        overall_healthy = True
        
        # 1. Django 应用状态
        import django
        components['django'] = {
            'status': 'healthy',
            'version': django.get_version(),
            'debug': settings.DEBUG
        }
        
        # 2. 数据库状态
        db_view = DatabaseHealthView()
        db_result = db_view.check_component('database', db_view.check_database)
        components['database'] = db_result
        if db_result['status'] != 'healthy':
            overall_healthy = False
        
        # 3. Redis 状态
        redis_view = RedisHealthView()
        redis_result = redis_view.check_component('redis', redis_view.check_redis)
        components['redis'] = redis_result
        if redis_result['status'] != 'healthy':
            overall_healthy = False
        
        # 4. WebSocket 状态
        websocket_view = WebSocketHealthView()
        websocket_result = websocket_view.check_component('websocket', websocket_view.check_websocket)
        components['websocket'] = websocket_result
        # 开发模式 (development_mode) 也被认为是健康的
        if websocket_result['status'] not in ('healthy', 'development_mode'):
            overall_healthy = False
        
        # 5. Python 环境
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        components['python'] = {
            'status': 'healthy',
            'version': python_version
        }
        
        # 6. 系统信息
        components['system'] = {
            'status': 'healthy',
            'timestamp': self.get_timestamp(),
            'uptime_seconds': time.time()  # 简化版本，实际应该计算进程启动时间
        }
        
        return {
            'components': components,
            'overall_healthy': overall_healthy
        }
    
    def get(self, request):
        result = self.check_all_components()
        
        http_status = (
            status.HTTP_200_OK 
            if result['overall_healthy'] 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return Response({
            'status': 'healthy' if result['overall_healthy'] else 'unhealthy',
            'timestamp': self.get_timestamp(),
            **result
        }, status=http_status)
