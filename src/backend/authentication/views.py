"""
Authentication views.
"""

from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from .services import TokenService, AuthService
from users.serializers import RegisterSerializer, LoginSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """用户注册视图"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from rest_framework.exceptions import ValidationError
        
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 创建用户
            user = AuthService.register_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # 生成 Token
            tokens = TokenService.generate_tokens(user)
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    **tokens
                },
                'message': '注册成功'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            error_code = e.get_codes()
            if isinstance(error_code, dict):
                # 获取第一个错误码
                error_code = list(error_code.values())[0] if error_code else 'VALIDATION_ERROR'
            else:
                error_code = 'VALIDATION_ERROR'
            
            error_detail = e.detail
            if isinstance(error_detail, dict):
                error_message = list(error_detail.values())[0][0] if error_detail else '验证失败'
            else:
                error_message = str(error_detail)
            
            return Response({
                'success': False,
                'error': {
                    'code': error_code,
                    'message': error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """用户登录视图"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            error_message = str(serializer.errors)
            
            # 检查是否是凭证错误
            if '用户名或密码错误' in error_message:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': '用户名或密码错误'
                    }
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # 检查是否是封禁用户
            if '账号已被封禁' in error_message:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_BANNED',
                        'message': '账号已被封禁'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 检查是否是禁用账号
            if '账号已被禁用' in error_message:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_INACTIVE',
                        'message': '账号已被禁用'
                    }
                }, status=status.HTTP_403_FORBIDDEN)
            
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        
        # 生成 Token
        tokens = TokenService.generate_tokens(user)
        
        # 更新最后登录时间
        AuthService.update_last_login(user)
        
        return Response({
            'success': True,
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'email': user.email,
                **tokens
            },
            'message': '登录成功'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """用户登出视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        # 在实际应用中，这里可以将 Token 加入黑名单
        # 使用 rest_framework_simplejwt.token_blacklist
        
        return Response({
            'success': True,
            'message': '登出成功'
        }, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):
    """Token 刷新视图"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'success': False,
                'error': {
                    'code': 'TOKEN_REQUIRED',
                    'message': 'Refresh Token 不能为空'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 刷新 Token
            new_access_token = TokenService.refresh_access_token(refresh_token)
            
            return Response({
                'success': True,
                'data': {
                    'access_token': new_access_token,
                    'expires_in': int(timedelta(hours=2).total_seconds())
                },
                'message': 'Token 刷新成功'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'TOKEN_INVALID',
                    'message': str(e)
                }
            }, status=status.HTTP_401_UNAUTHORIZED)


class CurrentUserView(APIView):
    """获取当前用户信息视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
