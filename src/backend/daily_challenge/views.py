"""
每日挑战 API 视图
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from django.utils import timezone

from .models import DailyChallenge, ChallengeAttempt, ChallengeStreak
from .services import (
    DailyChallengeService,
    ChallengeAttemptService,
    ChallengeStreakService,
    ChallengeLeaderboardService,
)
from .serializers import (
    DailyChallengeLeaderboardSerializer,
    WeeklyLeaderboardEntrySerializer,
    AllTimeLeaderboardEntrySerializer,
    UserRankSerializer,
    UserStatisticsSerializer,
)


class TodayChallengeView(APIView):
    """获取今日挑战"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """获取今日挑战详情"""
        challenge = DailyChallengeService.get_todays_challenge()
        
        if not challenge:
            # 如果没有今日挑战，自动创建
            challenge, created = DailyChallengeService.get_or_create_todays_challenge()
        
        # 获取用户尝试（如果已认证）
        user_attempt_info = {'has_attempted': False}
        
        if request.user.is_authenticated:
            user_attempt = ChallengeAttemptService.get_user_attempt_for_today(
                request.user, challenge
            )
            if user_attempt:
                user_attempt_info = {
                    'has_attempted': True,
                    'attempt_id': str(user_attempt.id),
                    'best_score': user_attempt.score,
                    'best_stars': user_attempt.stars_earned,
                    'status': user_attempt.status,
                }
        
        return Response({
            'success': True,
            'data': {
                'challenge': {
                    'id': str(challenge.id),
                    'date': challenge.date.isoformat(),
                    'fen': challenge.fen,
                    'target_description': challenge.target_description,
                    'difficulty': challenge.difficulty,
                    'stars': challenge.stars,
                    'max_moves': challenge.max_moves,
                    'time_limit': challenge.time_limit,
                    'total_attempts': challenge.total_attempts,
                    'unique_players': challenge.unique_players,
                    'completion_rate': float(challenge.completion_rate),
                },
                'user_attempt': user_attempt_info,
            }
        })


class StartChallengeView(APIView):
    """开始挑战"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """开始今日挑战"""
        challenge = DailyChallengeService.get_todays_challenge()
        
        if not challenge:
            return Response({
                'success': False,
                'error': {'code': 'NO_CHALLENGE', 'message': '今日挑战尚未发布'}
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            attempt = ChallengeAttemptService.create_attempt(request.user, challenge)
            
            return Response({
                'success': True,
                'data': {
                    'attempt_id': str(attempt.id),
                    'challenge_id': str(challenge.id),
                    'fen': challenge.fen,
                    'started_at': attempt.attempted_at.isoformat(),
                    'time_limit': challenge.time_limit,
                    'max_moves': challenge.max_moves,
                }
            })
        except ValueError as e:
            return Response({
                'success': False,
                'error': {'code': 'ALREADY_ATTEMPTED', 'message': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)


class SubmitMoveView(APIView):
    """提交走法"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """提交挑战走法"""
        attempt_id = request.data.get('attempt_id')
        
        if not attempt_id:
            return Response({
                'success': False,
                'error': {'code': 'MISSING_ATTEMPT_ID', 'message': '缺少尝试 ID'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attempt = get_object_or_404(ChallengeAttempt, id=attempt_id, user=request.user)
        
        move = {
            'from': request.data.get('from'),
            'to': request.data.get('to'),
            'piece': request.data.get('piece'),
        }
        
        result = ChallengeAttemptService.submit_move(attempt, move)
        
        if not result['valid']:
            return Response({
                'success': False,
                'error': {'code': 'INVALID_MOVE', 'message': result.get('error', '无效的走法')}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        })


class CompleteChallengeView(APIView):
    """完成挑战"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """完成挑战"""
        attempt_id = request.data.get('attempt_id')
        status_param = request.data.get('status', 'success')
        
        if not attempt_id:
            return Response({
                'success': False,
                'error': {'code': 'MISSING_ATTEMPT_ID', 'message': '缺少尝试 ID'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attempt = get_object_or_404(ChallengeAttempt, id=attempt_id, user=request.user)
        
        result = ChallengeAttemptService.complete_attempt(attempt, status_param)
        
        return Response({
            'success': True,
            'data': result
        })


class ChallengeLeaderboardView(APIView):
    """挑战排行榜"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """获取排行榜"""
        date_param = request.query_params.get('date')
        limit = int(request.query_params.get('limit', 100))
        
        if date_param:
            try:
                challenge_date = date.fromisoformat(date_param)
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DATE', 'message': '日期格式错误'}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            challenge_date = date.today()
        
        leaderboard = ChallengeLeaderboardService.get_daily_leaderboard(
            challenge_date, limit
        )
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = ChallengeLeaderboardService.get_user_rank(
                request.user, challenge_date
            )
        
        return Response({
            'success': True,
            'data': {
                'challenge_date': challenge_date.isoformat(),
                'leaderboard': leaderboard,
                'user_rank': user_rank,
            }
        })


class UserStreakView(APIView):
    """用户连续打卡"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """获取用户连续打卡记录"""
        streak = ChallengeStreakService.get_user_streak(request.user)
        statistics = ChallengeStreakService.get_user_statistics(request.user)
        
        return Response({
            'success': True,
            'data': {
                'streak': {
                    'current_streak': streak.current_streak,
                    'longest_streak': streak.longest_streak,
                    'last_completion_date': (
                        streak.last_completion_date.isoformat() 
                        if streak.last_completion_date else None
                    ),
                },
                'statistics': statistics,
            }
        })


class ChallengeHistoryView(APIView):
    """挑战历史"""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """获取历史挑战"""
        limit = int(request.query_params.get('limit', 30))
        
        # 获取过去的挑战
        challenges = DailyChallenge.objects.filter(
            date__lt=date.today(),
            is_active=True
        ).order_by('-date')[:limit]
        
        history = []
        for challenge in challenges:
            history.append({
                'id': str(challenge.id),
                'date': challenge.date.isoformat(),
                'difficulty': challenge.difficulty,
                'stars': challenge.stars,
                'target_description': challenge.target_description,
                'total_attempts': challenge.total_attempts,
                'unique_players': challenge.unique_players,
                'completion_rate': float(challenge.completion_rate),
            })
        
        return Response({
            'success': True,
            'data': {
                'history': history,
            }
        })


# 快捷 API 端点（函数视图）

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_tomorrow_challenge_view(request):
    """生成明日挑战（管理员专用）"""
    if not request.user.is_staff:
        return Response({
            'success': False,
            'error': {'code': 'PERMISSION_DENIED', 'message': '需要管理员权限'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        challenge = DailyChallengeService.generate_tomorrow_challenge()
        
        return Response({
            'success': True,
            'data': {
                'challenge_id': str(challenge.id),
                'date': challenge.date.isoformat(),
                'difficulty': challenge.difficulty,
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': {'code': 'GENERATION_ERROR', 'message': str(e)}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyLeaderboardView(APIView):
    """
    每日挑战排行榜
    
    GET /api/leaderboard/daily/
    可选参数：
    - date: 日期 (YYYY-MM-DD)，默认为今天
    - limit: 返回数量，默认 100
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        date_param = request.query_params.get('date')
        limit = int(request.query_params.get('limit', 100))
        
        if date_param:
            try:
                challenge_date = date.fromisoformat(date_param)
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DATE', 'message': '日期格式错误，请使用 YYYY-MM-DD'}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            challenge_date = date.today()
        
        leaderboard = ChallengeLeaderboardService.get_daily_leaderboard(
            challenge_date, limit
        )
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = ChallengeLeaderboardService.get_user_rank(
                request.user, challenge_date
            )
        
        data = {
            'challenge_date': challenge_date.isoformat(),
            'leaderboard': leaderboard,
            'user_rank': user_rank,
        }
        
        serializer = DailyChallengeLeaderboardSerializer(data)
        return Response({
            'success': True,
            'data': serializer.data
        })


class WeeklyLeaderboardView(APIView):
    """
    周排行榜
    
    GET /api/leaderboard/weekly/
    可选参数：
    - week_start: 周起始日期 (YYYY-MM-DD)，默认为本周一
    - limit: 返回数量，默认 100
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        week_start_param = request.query_params.get('week_start')
        limit = int(request.query_params.get('limit', 100))
        
        if week_start_param:
            try:
                week_start = date.fromisoformat(week_start_param)
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DATE', 'message': '日期格式错误，请使用 YYYY-MM-DD'}
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 获取本周一
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        leaderboard = ChallengeLeaderboardService.get_weekly_leaderboard(
            week_start, week_end, limit
        )
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = ChallengeLeaderboardService.get_user_weekly_rank(
                request.user, week_start, week_end
            )
        
        return Response({
            'success': True,
            'data': {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'leaderboard': leaderboard,
                'user_rank': user_rank,
            }
        })


class AllTimeLeaderboardView(APIView):
    """
    总排行榜
    
    GET /api/leaderboard/all-time/
    可选参数：
    - limit: 返回数量，默认 100
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 100))
        
        leaderboard = ChallengeLeaderboardService.get_all_time_leaderboard(limit)
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = ChallengeLeaderboardService.get_user_all_time_rank(
                request.user
            )
        
        return Response({
            'success': True,
            'data': {
                'leaderboard': leaderboard,
                'user_rank': user_rank,
            }
        })


class UserLeaderboardRankView(APIView):
    """
    用户排名查询
    
    GET /api/leaderboard/user/<user_id>/
    可选参数：
    - type: 排行榜类型 (daily/weekly/all-time)，默认 all-time
    - date: 日期（仅 daily 类型需要）
    - week_start: 周起始日期（仅 weekly 类型需要）
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError
        
        User = get_user_model()
        
        # 验证用户 ID 格式
        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValidationError, ValueError):
            return Response({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': '用户不存在'}
            }, status=status.HTTP_404_NOT_FOUND)
        
        rank_type = request.query_params.get('type', 'all-time')
        
        if rank_type == 'daily':
            date_param = request.query_params.get('date')
            try:
                challenge_date = date.fromisoformat(date_param) if date_param else date.today()
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DATE', 'message': '日期格式错误'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_rank = ChallengeLeaderboardService.get_user_rank(user, challenge_date)
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'rank_type': 'daily',
                        'challenge_date': challenge_date.isoformat(),
                        'message': '该用户在今日挑战中没有记录',
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'rank_type': 'daily',
                    'challenge_date': challenge_date.isoformat(),
                    **user_rank,
                }
            })
        
        elif rank_type == 'weekly':
            week_start_param = request.query_params.get('week_start')
            try:
                if week_start_param:
                    week_start = date.fromisoformat(week_start_param)
                else:
                    today = date.today()
                    week_start = today - timedelta(days=today.weekday())
            except ValueError:
                return Response({
                    'success': False,
                    'error': {'code': 'INVALID_DATE', 'message': '日期格式错误'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            week_end = week_start + timedelta(days=6)
            
            user_rank = ChallengeLeaderboardService.get_user_weekly_rank(
                user, week_start, week_end
            )
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'rank_type': 'weekly',
                        'message': '该用户在本周没有挑战记录',
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'rank_type': 'weekly',
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    **user_rank,
                }
            })
        
        else:  # all-time
            user_rank = ChallengeLeaderboardService.get_user_all_time_rank(user)
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'rank_type': 'all-time',
                        'message': '该用户没有挑战记录',
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'rank_type': 'all-time',
                    **user_rank,
                }
            })
