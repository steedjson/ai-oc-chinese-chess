"""
健康检查 API 视图测试

测试范围：
- 综合健康检查
- 数据库健康检查
- Redis 健康检查
- WebSocket 健康检查
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import override_settings


@pytest.mark.django_db
class TestDatabaseHealthView:
    """数据库健康检查视图测试"""

    def test_database_health_success(self):
        """测试数据库健康检查成功"""
        client = APIClient()
        url = reverse('health-database')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['component'] == 'database'
        assert response.data['status'] == 'healthy'
        assert 'response_time_ms' in response.data
        assert 'timestamp' in response.data
        assert 'engine' in response.data

    def test_database_health_no_auth_required(self):
        """测试数据库健康检查无需认证"""
        client = APIClient()
        url = reverse('health-database')
        
        response = client.get(url)
        
        # 应该返回 200 或 503（取决于数据库状态），但不应该是 401/403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]


@pytest.mark.django_db
class TestRedisHealthView:
    """Redis 健康检查视图测试"""

    def test_redis_health_success(self):
        """测试 Redis 健康检查成功"""
        client = APIClient()
        url = reverse('health-redis')
        
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['component'] == 'redis'
        assert response.data['status'] == 'healthy'
        assert 'response_time_ms' in response.data
        assert 'timestamp' in response.data
        assert 'backend' in response.data

    def test_redis_health_no_auth_required(self):
        """测试 Redis 健康检查无需认证"""
        client = APIClient()
        url = reverse('health-redis')
        
        response = client.get(url)
        
        # 应该返回 200 或 503（取决于 Redis 状态），但不应该是 401/403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    def test_redis_health_write_read_test(self):
        """测试 Redis 写读测试"""
        from django.core.cache import cache
        
        # 测试写入
        test_key = 'health_test:key1'
        test_value = 'test_value_123'
        cache.set(test_key, test_value, timeout=10)
        
        # 测试读取
        result = cache.get(test_key)
        assert result == test_value
        
        # 清理
        cache.delete(test_key)


@pytest.mark.django_db
class TestWebSocketHealthView:
    """WebSocket 健康检查视图测试"""

    def test_websocket_health_success(self):
        """测试 WebSocket 健康检查成功"""
        client = APIClient()
        url = reverse('health-websocket')
        
        response = client.get(url)
        
        # WebSocket 健康检查应该返回 200 或 503
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        
        if response.status_code == status.HTTP_200_OK:
            assert response.data['component'] == 'websocket'
            assert response.data['status'] in ['healthy', 'development_mode']
            assert 'response_time_ms' in response.data
            assert 'timestamp' in response.data
            assert 'backend' in response.data

    def test_websocket_health_no_auth_required(self):
        """测试 WebSocket 健康检查无需认证"""
        client = APIClient()
        url = reverse('health-websocket')
        
        response = client.get(url)
        
        # 应该返回 200 或 503，但不应该是 401/403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]


@pytest.mark.django_db
class TestComprehensiveHealthView:
    """综合健康检查视图测试"""

    def test_comprehensive_health_success(self):
        """测试综合健康检查成功"""
        client = APIClient()
        url = reverse('health-comprehensive')
        
        response = client.get(url)
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        
        if response.status_code == status.HTTP_200_OK:
            assert response.data['status'] == 'healthy'
            assert response.data['overall_healthy'] is True
            assert 'timestamp' in response.data
            assert 'components' in response.data
            
            # 检查所有组件都存在
            components = response.data['components']
            assert 'django' in components
            assert 'database' in components
            assert 'redis' in components
            assert 'websocket' in components
            assert 'python' in components
            assert 'system' in components
            
            # 检查 Django 组件信息
            assert components['django']['status'] == 'healthy'
            assert 'version' in components['django']
            
            # 检查 Python 组件信息
            assert components['python']['status'] == 'healthy'
            assert 'version' in components['python']

    def test_comprehensive_health_no_auth_required(self):
        """测试综合健康检查无需认证"""
        client = APIClient()
        url = reverse('health-comprehensive')
        
        response = client.get(url)
        
        # 应该返回 200 或 503，但不应该是 401/403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]

    def test_comprehensive_health_components_structure(self):
        """测试综合健康检查组件结构"""
        client = APIClient()
        url = reverse('health-comprehensive')
        
        response = client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            components = response.data['components']
            
            # 检查数据库组件结构
            db_component = components['database']
            assert 'status' in db_component
            assert 'response_time_ms' in db_component
            assert 'timestamp' in db_component
            
            # 检查 Redis 组件结构
            redis_component = components['redis']
            assert 'status' in redis_component
            assert 'response_time_ms' in redis_component
            assert 'timestamp' in redis_component
            
            # 检查 WebSocket 组件结构
            ws_component = components['websocket']
            assert 'status' in ws_component or 'backend' in ws_component
            assert 'response_time_ms' in ws_component or 'backend' in ws_component


@pytest.mark.django_db
class TestHealthViewEdgeCases:
    """健康检查视图边界情况测试"""

    def test_health_check_timestamp_format(self):
        """测试健康检查时间戳格式"""
        from datetime import datetime
        client = APIClient()
        url = reverse('health-database')
        
        response = client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            timestamp = response.data['timestamp']
            # 验证时间戳可以解析
            try:
                datetime.fromisoformat(timestamp)
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_health_check_response_time_positive(self):
        """测试健康检查响应时间为正数"""
        client = APIClient()
        url = reverse('health-database')
        
        response = client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            response_time = response.data['response_time_ms']
            assert response_time >= 0
            assert isinstance(response_time, (int, float))

    def test_health_check_concurrent_requests(self):
        """测试并发健康检查请求"""
        client = APIClient()
        url = reverse('health-database')
        
        # 发送多个请求
        responses = []
        for _ in range(5):
            response = client.get(url)
            responses.append(response)
        
        # 所有请求都应该成功
        for response in responses:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ]

    def test_health_check_different_endpoints_independent(self):
        """测试不同健康检查端点独立工作"""
        client = APIClient()
        
        endpoints = [
            'health-database',
            'health-redis',
            'health-websocket',
            'health-comprehensive'
        ]
        
        results = {}
        for endpoint in endpoints:
            url = reverse(endpoint)
            response = client.get(url)
            results[endpoint] = response.status_code
        
        # 所有端点都应该可访问（返回 200 或 503）
        for endpoint, status_code in results.items():
            assert status_code in [
                status.HTTP_200_OK,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ], f"{endpoint} returned {status_code}"
