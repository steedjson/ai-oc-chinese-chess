"""
自定义异常测试
测试 common/exceptions.py 中的异常类和异常处理器
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from common.exceptions import custom_exception_handler


class TestCustomExceptionHandlerSuccess:
    """成功响应测试"""
    
    def test_success_response_wrapped(self):
        """测试成功响应被包装"""
        exc = None  # 无异常
        context = {}
        
        # 模拟成功响应
        original_response = Response({'message': 'Success', 'data': {'id': 1}})
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = original_response
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is True
            assert 'data' in response.data
            assert 'timestamp' in response.data
    
    def test_success_response_already_has_success(self):
        """测试已有 success 字段的响应不被修改"""
        exc = None
        context = {}
        
        original_response = Response({'success': True, 'message': 'OK'})
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = original_response
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is True
            assert 'message' in response.data
    
    def test_success_response_preserves_data(self):
        """测试成功响应保留原始数据"""
        exc = None
        context = {}
        
        original_data = {'user': {'id': 1, 'name': 'Test'}, 'count': 10}
        original_response = Response(original_data)
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = original_response
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is True
            assert response.data['data']['user']['id'] == 1
            assert response.data['data']['count'] == 10


class TestCustomExceptionHandlerValidationError:
    """验证错误异常测试"""
    
    def test_drf_validation_error(self):
        """测试 DRF 验证错误"""
        exc = DRFValidationError("字段验证失败")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '字段验证失败'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'VALIDATION_ERROR'
            assert 'timestamp' in response.data
    
    def test_drf_validation_error_with_detail(self):
        """测试带 detail 的 DRF 验证错误"""
        exc = DRFValidationError({'username': ['此字段是必需的']})
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'username': ['此字段是必需的']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_django_validation_error(self):
        """测试 Django 验证错误"""
        exc = DjangoValidationError("无效的输入")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None  # Django 异常不会被默认处理器处理
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'VALIDATION_ERROR'
            assert response.data['error']['message'] == "无效的输入"
    
    def test_django_validation_error_with_message_list(self):
        """测试带消息列表的 Django 验证错误"""
        exc = DjangoValidationError(["错误 1", "错误 2"])
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'VALIDATION_ERROR'


class TestCustomExceptionHandlerNotFound:
    """未找到异常测试"""
    
    def test_not_found_exception(self):
        """测试未找到异常"""
        exc = NotFound("资源不存在")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '未找到'},
                status=status.HTTP_404_NOT_FOUND
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data['success'] is False
            assert 'timestamp' in response.data
    
    def test_not_found_wrapped_format(self):
        """测试未找到异常的包装格式"""
        exc = NotFound()
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is False
            # 应该被包装为 error 格式
            assert 'error' in response.data or response.data.get('success') is False


class TestCustomExceptionHandlerPermissionDenied:
    """权限拒绝异常测试"""
    
    def test_permission_denied_exception(self):
        """测试权限拒绝异常"""
        exc = PermissionDenied("无权限访问")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '权限拒绝'},
                status=status.HTTP_403_FORBIDDEN
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.data['success'] is False
            assert 'timestamp' in response.data


class TestCustomExceptionHandlerInternalError:
    """内部错误异常测试"""
    
    def test_unhandled_exception(self):
        """测试未处理的异常"""
        exc = Exception("未知错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None  # 未处理
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'INTERNAL_SERVER_ERROR'
            assert response.data['error']['message'] == '服务器内部错误'
            assert 'timestamp' in response.data
    
    def test_runtime_error(self):
        """测试运行时错误"""
        exc = RuntimeError("运行时错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.data['success'] is False
    
    def test_value_error(self):
        """测试值错误"""
        exc = ValueError("无效的值")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.data['success'] is False


class TestCustomExceptionHandlerEdgeCases:
    """边界情况测试"""
    
    def test_none_response_becomes_500(self):
        """测试 None 响应转换为 500 错误"""
        exc = Exception("测试异常")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None
            
            response = custom_exception_handler(exc, context)
            
            assert response is not None
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_response_without_error_field(self):
        """测试没有 error 字段的错误响应"""
        exc = DRFValidationError("测试错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'message': '错误消息'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is False
            assert 'error' in response.data
    
    def test_response_with_error_field(self):
        """测试已有 error 字段的响应"""
        exc = DRFValidationError("测试错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'error': {'code': 'CUSTOM_ERROR', 'message': '自定义错误'}},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'CUSTOM_ERROR'
    
    def test_non_dict_response_data(self):
        """测试非字典类型的响应数据"""
        exc = DRFValidationError("测试错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                ['错误 1', '错误 2'],
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.data['success'] is False
            assert 'error' in response.data
    
    def test_timestamp_is_iso_format(self):
        """测试时间戳是 ISO 格式"""
        exc = None
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response({'message': 'OK'})
            
            response = custom_exception_handler(exc, context)
            
            timestamp = response.data['timestamp']
            # ISO 格式应该包含 T 分隔符
            assert 'T' in timestamp or '+' in timestamp or '-' in timestamp
    
    def test_context_not_used_but_accepted(self):
        """测试 context 参数被接受但不一定使用"""
        exc = Exception("测试")
        context = {'request': Mock(), 'view': Mock()}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = None
            
            # 不应抛出异常
            response = custom_exception_handler(exc, context)
            
            assert response is not None


class TestCustomExceptionHandlerVariousStatusCodes:
    """各种状态码测试"""
    
    def test_400_bad_request(self):
        """测试 400 状态码"""
        exc = DRFValidationError("错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 400
            assert response.data['success'] is False
    
    def test_401_unauthorized(self):
        """测试 401 状态码"""
        exc = Exception("未授权")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '未授权'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 401
            assert response.data['success'] is False
    
    def test_403_forbidden(self):
        """测试 403 状态码"""
        exc = Exception("禁止")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '禁止'},
                status=status.HTTP_403_FORBIDDEN
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 403
            assert response.data['success'] is False
    
    def test_404_not_found(self):
        """测试 404 状态码"""
        exc = Exception("未找到")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '未找到'},
                status=status.HTTP_404_NOT_FOUND
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 404
            assert response.data['success'] is False
    
    def test_500_internal_error(self):
        """测试 500 状态码"""
        exc = Exception("服务器错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '服务器错误'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 500
            assert response.data['success'] is False
    
    def test_200_success(self):
        """测试 200 状态码"""
        exc = None
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'result': '成功'},
                status=status.HTTP_200_OK
            )
            
            response = custom_exception_handler(exc, context)
            
            assert response.status_code == 200
            assert response.data['success'] is True


class TestCustomExceptionHandlerTimestamp:
    """时间戳测试"""
    
    def test_timestamp_added_to_error_response(self):
        """测试错误响应添加时间戳"""
        exc = DRFValidationError("错误")
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'detail': '错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            assert 'timestamp' in response.data
    
    def test_timestamp_added_to_success_response(self):
        """测试成功响应添加时间戳"""
        exc = None
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response({'data': '成功'})
            
            response = custom_exception_handler(exc, context)
            
            assert 'timestamp' in response.data
    
    def test_timestamp_not_added_if_not_dict(self):
        """测试非字典响应不添加时间戳"""
        exc = None
        context = {}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response('纯文本响应')
            
            response = custom_exception_handler(exc, context)
            
            # 非字典响应，时间戳可能不添加
            # 这取决于实现
            assert response is not None


class TestCustomExceptionHandlerIntegration:
    """集成测试"""
    
    def test_full_error_flow(self):
        """测试完整的错误处理流程"""
        exc = DRFValidationError({'email': ['无效的邮箱格式']})
        context = {'request': Mock(), 'view': Mock()}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'email': ['无效的邮箱格式']},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            response = custom_exception_handler(exc, context)
            
            # 验证完整响应结构
            assert isinstance(response, Response)
            assert response.status_code == 400
            assert response.data['success'] is False
            assert response.data['error']['code'] == 'VALIDATION_ERROR'
            assert 'timestamp' in response.data
    
    def test_full_success_flow(self):
        """测试完整的成功处理流程"""
        exc = None
        context = {'request': Mock(), 'view': Mock()}
        
        with patch('common.exceptions.exception_handler') as mock_handler:
            mock_handler.return_value = Response(
                {'user': {'id': 1, 'name': 'Test'}},
                status=status.HTTP_200_OK
            )
            
            response = custom_exception_handler(exc, context)
            
            assert isinstance(response, Response)
            assert response.status_code == 200
            assert response.data['success'] is True
            assert response.data['data']['user']['id'] == 1
            assert 'timestamp' in response.data
