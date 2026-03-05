"""
User views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserDetailSerializer, ChangePasswordSerializer
from authentication.services import AuthService

User = get_user_model()


class UserDetailView(APIView):
    """用户详情视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_object(self, pk):
        """获取用户对象"""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """获取用户详情"""
        user = self.get_object(pk)
        
        if not user:
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserDetailSerializer(user)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """更新用户信息（全量更新）"""
        user = self.get_object(pk)
        
        if not user:
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 只能更新自己的信息（或管理员）
        if request.user != user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': '无权修改其他用户信息'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserSerializer(user, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': '用户信息更新成功'
        }, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        """更新用户信息（部分更新）"""
        user = self.get_object(pk)
        
        if not user:
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 只能更新自己的信息（或管理员）
        if request.user != user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': '无权修改其他用户信息'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': '用户信息更新成功'
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """修改密码视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_object(self, pk):
        """获取用户对象"""
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None
    
    def put(self, request, pk):
        """修改用户密码"""
        user = self.get_object(pk)
        
        if not user:
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 只能修改自己的密码（或管理员）
        if request.user != user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': '无权修改其他用户密码'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            AuthService.change_password(
                user=user,
                old_password=serializer.validated_data['old_password'],
                new_password=serializer.validated_data['new_password']
            )
            
            return Response({
                'success': True,
                'message': '密码修改成功，请重新登录'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_code = 'PASSWORD_CHANGE_FAILED'
            error_message = str(e)
            
            if 'WRONG_OLD_PASSWORD' in str(e):
                error_code = 'WRONG_OLD_PASSWORD'
                error_message = '旧密码错误'
            elif 'SAME_PASSWORD' in str(e):
                error_code = 'SAME_PASSWORD'
                error_message = '新密码不能与旧密码相同'
            
            return Response({
                'success': False,
                'error': {
                    'code': error_code,
                    'message': error_message
                }
            }, status=status.HTTP_400_BAD_REQUEST)
