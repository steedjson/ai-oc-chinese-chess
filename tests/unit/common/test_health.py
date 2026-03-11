"""
测试健康检查模块

测试 common/health.py 中的健康检查视图
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient
from django.db import connections
from django.core.cache import cache


@pytest.mark.django_db
class TestHealthCheckView:
    """测试健康检查视图"""
    
    def test_health_check_success(self, api_client):
        """测试健康检查成功"""
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'
        assert 'components' in response.data
        assert 'django' in response.data['components']
        assert 'database' in response.data['components']
        assert 'cache' in response.data['components']
        assert 'python' in response.data['components']
    
    def test_health_check_django_version(self, api_client):
        """测试 Django 版本信息"""
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_200_OK
        
        django_component = response.data['components']['django']
        assert django_component['status'] == 'healthy'
        assert 'version' in django_component
        assert django_component['version']  # 版本号不为空
    
    def test_health_check_database(self, api_client):
        """测试数据库健康检查"""
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_200_OK
        
        db_component = response.data['components']['database']
        assert db_component['status'] == 'healthy'
        assert 'backend' in db_component
    
    def test_health_check_cache(self, api_client):
        """测试缓存健康检查"""
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_200_OK
        
        cache_component = response.data['components']['cache']
        assert cache_component['status'] == 'healthy'
        assert 'backend' in cache_component
    
    def test_health_check_python_version(self, api_client):
        """测试 Python 版本信息"""
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_200_OK
        
        python_component = response.data['components']['python']
        assert python_component['status'] == 'healthy'
        assert 'version' in python_component
    
    @patch('common.health.connections')
    def test_health_check_database_failure(self, mock_connections, api_client):
        """测试数据库故障时的健康检查"""
        mock_connections.__getitem__.side_effect = Exception("Database connection failed")
        
        response = api_client.get('/api/health/')
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['status'] == 'unhealthy'
        assert response.data['components']['database']['status'] == 'unhealthy'
    
    @patch('common.health.cache')
    def test_health_check_cache_failure(self, mock_cache, api_client):
        """测试缓存故障时的健康检查"""
        mock_cache.set.side_effect = Exception("Cache connection failed")
        
        response = api_client.get('/api/health/')
        
        # 如果缓存失败，整体应该是不健康的
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data['status'] == 'unhealthy'
        assert response.data['components']['cache']['status'] == 'unhealthy'


class TestHealthCheckFunction:
    """测试健康检查函数"""
    
    def test_health_check_function_exists(self):
        """测试健康检查函数存在"""
        from common.health import health_check
        
        assert callable(health_check)
    
    def test_health_check_function_returns_response(self):
        """测试健康检查函数返回响应"""
        from common.health import health_check
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.method = 'GET'
        
        # 函数应该返回 Response 对象
        response = health_check(request)
        
        assert response is not None
        assert hasattr(response, 'data')


class TestHealthCheckAuthentication:
    """测试健康检查认证"""
    
    def test_health_check_no_auth_required(self, api_client):
        """测试健康检查不需要认证"""
        # 未认证用户应该也能访问
        response = api_client.get('/api/health/')
        
        # 应该返回 200 或 503（取决于健康状态）
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_health_check_no_permission_required(self, api_client):
        """测试健康检查不需要权限"""
        response = api_client.get('/api/health/')
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]


class TestHealthCheckPerformance:
    """测试健康检查性能"""
    
    def test_health_check_response_time(self, api_client):
        """测试健康检查响应时间"""
        import time
        
        start = time.time()
        response = api_client.get('/api/health/')
        elapsed = time.time() - start
        
        # 健康检查应该在 1 秒内完成
        assert elapsed < 1.0
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    return APIClient()
