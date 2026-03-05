"""
Custom exception handler for DRF.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，统一错误响应格式
    """
    # 调用 DRF 默认的异常处理器
    response = exception_handler(exc, context)
    
    # 如果 response 是 None，说明是未处理的异常
    if response is None:
        if isinstance(exc, DjangoValidationError):
            response = Response(
                {
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': str(exc),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            # 未处理的异常，返回 500
            response = Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_SERVER_ERROR',
                        'message': '服务器内部错误',
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    elif response is not None:
        # 包装标准 DRF 响应为统一格式
        if response.status_code >= 400:
            if isinstance(exc, DRFValidationError):
                response.data = {
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                    }
                }
            else:
                # 保持原有数据结构但添加 success 字段
                if isinstance(response.data, dict):
                    if 'error' not in response.data:
                        response.data = {
                            'success': False,
                            'error': response.data
                        }
                    else:
                        response.data['success'] = False
                else:
                    response.data = {
                        'success': False,
                        'error': {
                            'message': response.data
                        }
                    }
        elif 'success' not in response.data:
            # 成功响应添加 success 字段
            response.data = {
                'success': True,
                'data': response.data
            }
    
    # 添加时间戳
    if response and isinstance(response.data, dict):
        from datetime import datetime, timezone
        response.data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    return response
