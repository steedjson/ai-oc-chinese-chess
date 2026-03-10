"""
User views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from .serializers import UserSerializer, UserDetailSerializer, ChangePasswordSerializer
from authentication.services import AuthService
from games.models import Game

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


class UserProfileView(APIView):
    """当前用户 Profile 视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """获取当前用户信息"""
        user = request.user
        serializer = UserDetailSerializer(user)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """更新当前用户信息（全量更新）"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': '用户信息更新成功'
        }, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """更新当前用户信息（部分更新）"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': '用户信息更新成功'
        }, status=status.HTTP_200_OK)


class UserStatsView(APIView):
    """用户统计视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, user_id=None):
        """获取用户统计数据"""
        # 如果未指定 user_id，使用当前用户
        if user_id is None:
            user = request.user
        else:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': '用户不存在'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
        
        # 统计对局数据
        total_games = Game.objects.filter(
            Q(red_player=user) | Q(black_player=user),
            status__in=['red_win', 'black_win', 'draw']
        ).count()
        
        wins = Game.objects.filter(
            (Q(red_player=user) & Q(winner='red')) |
            (Q(black_player=user) & Q(winner='black')),
            status__in=['red_win', 'black_win']
        ).count()
        
        losses = Game.objects.filter(
            (Q(red_player=user) & Q(winner='black')) |
            (Q(black_player=user) & Q(winner='red')),
            status__in=['red_win', 'black_win']
        ).count()
        
        draws = Game.objects.filter(
            Q(red_player=user) | Q(black_player=user),
            status='draw'
        ).count()
        
        win_rate = round((wins / total_games * 100), 2) if total_games > 0 else 0.0
        
        stats_data = {
            'total_games': total_games,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': win_rate,
            'current_rating': user.elo_rating,
            'highest_rating': user.elo_rating,  # TODO: 从历史记录中获取最高分
        }
        
        return Response({
            'success': True,
            'data': stats_data
        }, status=status.HTTP_200_OK)


class UserGamesView(APIView):
    """用户对局历史视图"""
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, user_id):
        """获取用户对局历史"""
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 分页参数
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page_size = min(page_size, 100)  # 限制最大页面大小
        
        # 查询对局
        games = Game.objects.filter(
            Q(red_player=user) | Q(black_player=user)
        ).select_related(
            'red_player', 'black_player'
        ).order_by('-created_at')
        
        # 分页
        total_count = games.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_games = games[start_idx:end_idx]
        
        # 构建返回数据
        games_data = []
        for game in paginated_games:
            is_red = game.red_player == user
            opponent = game.black_player if is_red else game.red_player
            
            # 确定结果
            if game.winner == 'draw':
                result = 'draw'
            elif (is_red and game.winner == 'red') or (not is_red and game.winner == 'black'):
                result = 'win'
            else:
                result = 'loss'
            
            # 计算天梯分变化（简化版）
            rating_change = 0
            if game.status in ['red_win', 'black_win', 'draw']:
                # TODO: 实现完整的 Elo 计算
                if result == 'win':
                    rating_change = 15
                elif result == 'loss':
                    rating_change = -12
                else:
                    rating_change = 2
            
            games_data.append({
                'id': str(game.id),
                'opponent': {
                    'id': opponent.id if opponent else None,
                    'username': opponent.username if opponent else 'AI',
                    'avatar_url': opponent.avatar_url if opponent else None,
                    'rating': opponent.elo_rating if opponent else 0,
                },
                'result': result,
                'rating_change': rating_change,
                'is_red': is_red,
                'game_type': game.game_type,
                'created_at': game.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'data': {
                'results': games_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size,
                    'has_next': end_idx < total_count,
                    'has_prev': page > 1,
                }
            }
        }, status=status.HTTP_200_OK)
