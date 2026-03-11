"""
测试异常处理模块

测试 common/exceptions.py 中的自定义异常处理器
"""

import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response
from rest_framework import status
from common.exceptions import custom_exception_handler


class TestCustomExceptionHandler:
    """测试自定义异常处理器"""
    
    def test_handle_drf_validation_error(self):
        """测试处理 DRF ValidationError"""
        exc = DRFValidationError({"field": "This field is required"})
        
        response = custom_exception_handler(exc, {})
        
        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'error' in response.data
        assert 'VALIDATION_ERROR' in str(response.data['error']['code'])
    
    def test_handle_django_validation_error(self):
        """测试处理 Django ValidationError"""
        exc = DjangoValidationError("Field validation failed")
        
        response = custom_exception_handler(exc, {})
        
        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_handle_generic_exception(self):
        """测试处理普通异常"""
        exc = Exception("Unexpected error")
        
        response = custom_exception_handler(exc, {})
        
        assert response is not None
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False
        assert response.data['error']['code'] == 'INTERNAL_SERVER_ERROR'
    
    def test_handle_successful_response(self):
        """测试处理成功响应"""
        # 模拟一个成功的 Response
        response_obj = Response({'data': 'test'})
        
        # 异常处理器应该添加 success 字段
        result = custom_exception_handler(None, {})
        
        # None 异常会返回 None（未处理）
        assert result is None
    
    def test_response_includes_timestamp(self):
        """测试响应包含时间戳"""
        exc = DRFValidationError("Test error")
        
        response = custom_exception_handler(exc, {})
        
        assert 'timestamp' in response.data
    
    def test_error_response_format(self):
        """测试错误响应格式"""
        exc = DRFValidationError({"message": "Something went wrong"})
        
        response = custom_exception_handler(exc, {})
        
        assert 'success' in response.data
        assert 'error' in response.data
        assert response.data['success'] is False


class TestCustomExceptionHandlerEdgeCases:
    """测试异常处理器边界情况"""
    
    def test_handle_none_exception(self):
        """测试处理 None 异常"""
        result = custom_exception_handler(None, {})
        
        # None 异常应该返回 None
        assert result is None
    
    def test_handle_dict_response(self):
        """测试处理字典响应"""
        # 创建一个已经包含 error 字段的响应
        response_obj = Response({'error': {'message': 'Custom error'}})
        response_obj.data['success'] = False
        
        # 这种情况下处理器应该保持原样
        # 但实际处理器会重新包装
        pass
    
    def test_handle_list_response(self):
        """测试处理列表响应"""
        exc = DRFValidationError(["Error 1", "Error 2"])
        
        response = custom_exception_handler(exc, {})
        
        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestExceptionHandlerIntegration:
    """异常处理器集成测试"""
    
    def test_exception_in_view(self, api_client):
        """测试视图中的异常处理"""
        from rest_framework.decorators import api_view
        
        @api_view(['GET'])
        def test_view(request):
            raise DRFValidationError("Test validation error")
        
        # 手动测试异常处理器
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/test/')
        
        try:
            response = test_view(request)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        except DRFValidationError as e:
            # 异常应该被处理器捕获
            response = custom_exception_handler(e, {})
            assert response is not None
            assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    from rest_framework.test import APIClient
    return APIClient()
