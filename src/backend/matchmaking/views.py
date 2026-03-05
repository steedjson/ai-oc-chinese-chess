"""
匹配系统 API 视图
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .queue import MatchmakingQueue, QueueUser
from .algorithm import Matchmaker


class StartMatchmakingView(APIView):
    """开始匹配"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            import time
            game_type = request.data.get('game_type', 'ranked')
            user = request.user
            
            # 创建队列用户 - 使用 QueueUser 定义的正确参数
            queue_user = QueueUser(
                user_id=str(user.id),
                rating=getattr(user, 'elo_rating', 1500),  # 默认 1500
                joined_at=time.time(),
                search_range=100,  # INITIAL_SEARCH_RANGE
                game_type=game_type
            )
            
            queue = MatchmakingQueue()
            success = queue.join_queue(
                user_id=str(user.id),
                rating=getattr(user, 'elo_rating', 1500),
                game_type=game_type
            )
            
            if not success:
                return Response({
                    'success': False,
                    'error': '已在队列中或加入失败'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取队列信息
            queue_info = queue.get_queue_position(str(user.id), game_type)
            estimated_wait = queue_info.get('wait_time', 0)
            
            return Response({
                'success': True,
                'message': '加入匹配队列成功',
                'game_type': game_type,
                'queue_position': queue_info.get('position', 0),
                'estimated_wait_time': int(estimated_wait)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelMatchmakingView(APIView):
    """取消匹配"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            game_type = request.data.get('game_type', 'ranked')
            queue = MatchmakingQueue()
            queue.leave_queue(str(user.id), game_type)
            
            return Response({
                'success': True,
                'message': '已取消匹配'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchStatusView(APIView):
    """获取匹配状态"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            game_type = request.query_params.get('game_type', 'ranked')
            queue = MatchmakingQueue()
            
            in_queue = queue.is_in_queue(str(user.id), game_type)
            queue_info = queue.get_queue_position(str(user.id), game_type) if in_queue else {}
            stats = queue.get_queue_stats(game_type)
            
            return Response({
                'success': True,
                'in_queue': in_queue,
                'queue_position': queue_info.get('position', 0) if in_queue else None,
                'estimated_wait_time': int(queue_info.get('wait_time', 0)) if in_queue else None,
                'total_in_queue': stats.get('total_players', 0)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
