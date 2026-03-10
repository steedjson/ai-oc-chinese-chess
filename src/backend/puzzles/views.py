"""
残局挑战 API 视图

包含：
- PuzzleListView: 关卡列表
- PuzzleDetailView: 关卡详情
- PuzzleAttemptCreateView: 创建挑战
- PuzzleMoveView: 提交走法
- PuzzleCompleteView: 完成挑战
- PuzzleProgressView: 用户进度
- PuzzleLeaderboardView: 排行榜
"""
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress
from puzzles.services import PuzzleService, PuzzleAttemptService, PuzzleProgressService


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PuzzleListView(APIView):
    """关卡列表视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        获取关卡列表
        
        Query Parameters:
            - difficulty: 难度筛选 (1-10)
            - page: 页码
            - page_size: 每页数量
        """
        difficulty = request.query_params.get('difficulty')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        if difficulty:
            difficulty = int(difficulty)
        
        result = PuzzleService.get_puzzle_list(
            difficulty=difficulty,
            page=page,
            page_size=page_size
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


class PuzzleDetailView(APIView):
    """关卡详情视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, puzzle_id):
        """
        获取关卡详情
        
        URL Parameters:
            - id: 关卡 ID
        """
        result = PuzzleService.get_puzzle_detail(puzzle_id)
        
        if not result:
            return Response({
                'success': False,
                'error': {
                    'code': 'PUZZLE_NOT_FOUND',
                    'message': '关卡不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 检查用户是否已通关此关卡
        attempt = PuzzleAttempt.objects.filter(
            user=request.user,
            puzzle_id=puzzle_id,
            status=PuzzleAttemptStatus.SUCCESS
        ).order_by('-completed_at').first()
        
        result['user_completed'] = attempt is not None
        if attempt:
            result['user_stars'] = attempt.stars
            result['user_moves_used'] = attempt.moves_used
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


class PuzzleAttemptCreateView(APIView):
    """创建挑战视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, puzzle_id):
        """
        开始挑战
        
        URL Parameters:
            - id: 关卡 ID
        """
        attempt = PuzzleAttemptService.create_attempt(request.user, puzzle_id)
        
        if not attempt:
            return Response({
                'success': False,
                'error': {
                    'code': 'PUZZLE_NOT_FOUND',
                    'message': '关卡不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': {
                'attempt_id': str(attempt.id),
                'puzzle_id': str(attempt.puzzle.id),
                'fen_current': attempt.fen_current,
                'status': attempt.status,
                'current_move_index': attempt.current_move_index,
                'move_limit': attempt.puzzle.move_limit,
                'time_limit': attempt.puzzle.time_limit,
                'started_at': attempt.started_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)


class PuzzleMoveView(APIView):
    """提交走法视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, puzzle_id, attempt_id):
        """
        提交走法
        
        URL Parameters:
            - id: 关卡 ID
            - attempt_id: 挑战 ID
            
        Request Body:
            {
                "from": "e2",
                "to": "e4",
                "piece": "P"
            }
        """
        try:
            puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
            attempt = PuzzleAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                status=PuzzleAttemptStatus.IN_PROGRESS
            )
        except (Puzzle.DoesNotExist, PuzzleAttempt.DoesNotExist):
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '关卡或挑战不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 验证走法
        move_data = request.data
        is_correct, message = PuzzleService.verify_move(puzzle, attempt, move_data)
        
        if not is_correct:
            return Response({
                'success': False,
                'data': {
                    'correct': False,
                    'message': message,
                    'fen_current': attempt.fen_current,
                    'remaining_moves': len(puzzle.solution_moves) - attempt.current_move_index,
                }
            }, status=status.HTTP_200_OK)
        
        # 更新挑战记录
        result = PuzzleAttemptService.update_attempt(attempt, move_data, is_correct)
        
        # 更新 FEN（简化处理，实际应该根据走法更新）
        if result['is_complete']:
            # 完成挑战，更新用户进度
            PuzzleProgressService.update_progress(request.user)
            PuzzleProgressService.add_ranking_points(request.user, result['points_earned'])
        
        return Response({
            'success': True,
            'data': {
                'correct': True,
                'message': message,
                'fen_current': attempt.fen_current,
                'current_move_index': result['current_move_index'],
                'remaining_moves': len(puzzle.solution_moves) - result['current_move_index'],
                'is_complete': result['is_complete'],
                'stars': result.get('stars'),
                'points_earned': result.get('points_earned'),
            }
        }, status=status.HTTP_200_OK)


class PuzzleCompleteView(APIView):
    """完成挑战视图"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, puzzle_id, attempt_id):
        """
        完成挑战（手动结束）
        
        URL Parameters:
            - id: 关卡 ID
            - attempt_id: 挑战 ID
        """
        try:
            attempt = PuzzleAttempt.objects.get(
                id=attempt_id,
                user=request.user,
                status=PuzzleAttemptStatus.IN_PROGRESS
            )
        except PuzzleAttempt.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'ATTEMPT_NOT_FOUND',
                    'message': '挑战不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否已完成
        if PuzzleService.is_puzzle_complete(attempt):
            return Response({
                'success': True,
                'data': {
                    'status': attempt.status,
                    'stars': attempt.stars,
                    'points_earned': attempt.points_earned,
                    'moves_used': attempt.moves_used,
                    'time_used': attempt.time_used,
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_COMPLETE',
                'message': '挑战尚未完成'
            }
        }, status=status.HTTP_400_BAD_REQUEST)


class PuzzleProgressView(APIView):
    """用户进度视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        获取用户进度
        """
        statistics = PuzzleProgressService.get_user_statistics(request.user)
        
        return Response({
            'success': True,
            'data': statistics
        }, status=status.HTTP_200_OK)


class PuzzleLeaderboardView(APIView):
    """排行榜视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        获取排行榜
        
        Query Parameters:
            - time_range: 时间范围 (daily, weekly, all)
            - limit: 返回数量 (默认 100)
        """
        time_range = request.query_params.get('time_range', 'all')
        limit = int(request.query_params.get('limit', 100))
        
        leaderboard = PuzzleProgressService.get_leaderboard(
            time_range=time_range,
            limit=limit
        )
        
        # 获取用户自己的排名
        user_progress = PuzzleProgress.objects.filter(user=request.user).first()
        user_rank = None
        if user_progress:
            user_rank = PuzzleProgress.objects.filter(
                ranking_points__gt=user_progress.ranking_points
            ).count() + 1
        
        return Response({
            'success': True,
            'data': {
                'leaderboard': leaderboard,
                'user_rank': {
                    'rank': user_rank,
                    'ranking_points': user_progress.ranking_points if user_progress else 0,
                    'total_completed': user_progress.total_completed if user_progress else 0,
                } if user_rank else None
            }
        }, status=status.HTTP_200_OK)


# 导入 PuzzleAttemptStatus 用于视图
from puzzles.models import PuzzleAttemptStatus
