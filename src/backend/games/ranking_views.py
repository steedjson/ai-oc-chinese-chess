"""
中国象棋排行榜 API 视图

提供每日、每周、总榜排行榜接口
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from .ranking_services import RankingService, RankingCacheService
from .ranking_models import UserRankingStats


class DailyLeaderboardView(APIView):
    """
    每日排行榜
    
    GET /api/ranking/daily/
    
    查询参数:
    - date: 日期 (YYYY-MM-DD)，默认为今天
    - limit: 返回数量，默认 100，最大 500
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        date_param = request.query_params.get('date')
        limit = min(int(request.query_params.get('limit', 100)), 500)
        
        if date_param:
            try:
                cache_date = date.fromisoformat(date_param)
            except ValueError:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE',
                        'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            cache_date = date.today()
        
        # 获取排行榜（带缓存）
        leaderboard, from_cache = RankingCacheService.get_or_generate_daily_leaderboard(
            cache_date, limit
        )
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = RankingService.get_user_daily_rank(request.user, cache_date)
        
        return Response({
            'success': True,
            'data': {
                'ranking_type': 'daily',
                'date': cache_date.isoformat(),
                'leaderboard': leaderboard,
                'user_rank': user_rank,
                'from_cache': from_cache,
            }
        })


class WeeklyLeaderboardView(APIView):
    """
    每周排行榜
    
    GET /api/ranking/weekly/
    
    查询参数:
    - week_start: 周起始日期 (YYYY-MM-DD)，默认为本周一
    - limit: 返回数量，默认 100，最大 500
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        week_start_param = request.query_params.get('week_start')
        limit = min(int(request.query_params.get('limit', 100)), 500)
        
        if week_start_param:
            try:
                week_start = date.fromisoformat(week_start_param)
                # 获取该日期所在周的周一
                week_start = week_start - timedelta(days=week_start.weekday())
            except ValueError:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE',
                        'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 获取本周一
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        iso_calendar = week_start.isocalendar()
        week = iso_calendar[1]
        year = iso_calendar[0]
        week_end = week_start + timedelta(days=6)
        
        # 获取排行榜（带缓存）
        leaderboard, from_cache = RankingCacheService.get_or_generate_weekly_leaderboard(
            week, year, limit
        )
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = RankingService.get_user_weekly_rank(request.user, week, year)
        
        return Response({
            'success': True,
            'data': {
                'ranking_type': 'weekly',
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'week_number': week,
                'year': year,
                'leaderboard': leaderboard,
                'user_rank': user_rank,
                'from_cache': from_cache,
            }
        })


class AllTimeLeaderboardView(APIView):
    """
    总排行榜
    
    GET /api/ranking/all-time/
    
    查询参数:
    - limit: 返回数量，默认 100，最大 500
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        limit = min(int(request.query_params.get('limit', 100)), 500)
        
        # 获取排行榜（带缓存）
        leaderboard, from_cache = RankingCacheService.get_or_generate_all_time_leaderboard(limit)
        
        # 获取用户排名（如果已认证）
        user_rank = None
        if request.user.is_authenticated:
            user_rank = RankingService.get_user_all_time_rank(request.user)
        
        return Response({
            'success': True,
            'data': {
                'ranking_type': 'all_time',
                'leaderboard': leaderboard,
                'user_rank': user_rank,
                'from_cache': from_cache,
            }
        })


class UserRankingView(APIView):
    """
    用户排名查询
    
    GET /api/ranking/user/<user_id>/
    
    查询参数:
    - type: 排行榜类型 (daily/weekly/all-time)，默认 all-time
    - date: 日期（仅 daily 类型需要）
    - week_start: 周起始日期（仅 weekly 类型需要）
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        # 验证用户 ID 格式
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValidationError, ValueError):
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        rank_type = request.query_params.get('type', 'all-time')
        
        if rank_type == 'daily':
            date_param = request.query_params.get('date')
            try:
                cache_date = date.fromisoformat(date_param) if date_param else date.today()
            except ValueError:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE',
                        'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_rank = RankingService.get_user_daily_rank(user, cache_date)
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'username': user.username,
                        'rank_type': 'daily',
                        'date': cache_date.isoformat(),
                        'message': '该用户在今日没有游戏记录',
                        'rank': None,
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'username': user.username,
                    'rank_type': 'daily',
                    'date': cache_date.isoformat(),
                    **user_rank,
                }
            })
        
        elif rank_type == 'weekly':
            week_start_param = request.query_params.get('week_start')
            try:
                if week_start_param:
                    week_start = date.fromisoformat(week_start_param)
                    week_start = week_start - timedelta(days=week_start.weekday())
                else:
                    today = date.today()
                    week_start = today - timedelta(days=today.weekday())
            except ValueError:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE',
                        'message': '日期格式错误，请使用 YYYY-MM-DD 格式'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            iso_calendar = week_start.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
            week_end = week_start + timedelta(days=6)
            
            user_rank = RankingService.get_user_weekly_rank(user, week, year)
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'username': user.username,
                        'rank_type': 'weekly',
                        'message': '该用户在本周没有游戏记录',
                        'rank': None,
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'username': user.username,
                    'rank_type': 'weekly',
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'week_number': week,
                    'year': year,
                    **user_rank,
                }
            })
        
        else:  # all-time
            user_rank = RankingService.get_user_all_time_rank(user)
            
            if not user_rank:
                return Response({
                    'success': True,
                    'data': {
                        'user_id': str(user.id),
                        'username': user.username,
                        'rank_type': 'all_time',
                        'message': '该用户没有游戏记录',
                        'rank': None,
                    }
                })
            
            return Response({
                'success': True,
                'data': {
                    'user_id': str(user.id),
                    'username': user.username,
                    'rank_type': 'all_time',
                    **user_rank,
                }
            })


class UserRankingStatsView(APIView):
    """
    用户排行榜统计
    
    GET /api/ranking/user/<user_id>/stats/
    
    获取用户的详细排行榜统计数据
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        # 验证用户 ID 格式
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValidationError, ValueError):
            return Response({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 获取用户统计
        stats = RankingService.get_user_stats(user)
        
        # 获取当前排名
        daily_rank = RankingService.get_user_daily_rank(user)
        weekly_rank = RankingService.get_user_weekly_rank(user)
        all_time_rank = RankingService.get_user_all_time_rank(user)
        
        return Response({
            'success': True,
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'statistics': stats,
                'current_ranks': {
                    'daily': daily_rank,
                    'weekly': weekly_rank,
                    'all_time': all_time_rank,
                }
            }
        })


class MyRankingView(APIView):
    """
    我的排行榜
    
    GET /api/ranking/my/
    
    获取当前登录用户的排行榜信息
    需要认证
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # 获取用户统计
        stats = RankingService.get_user_stats(user)
        
        # 获取各类型排名
        daily_rank = RankingService.get_user_daily_rank(user)
        weekly_rank = RankingService.get_user_weekly_rank(user)
        all_time_rank = RankingService.get_user_all_time_rank(user)
        
        return Response({
            'success': True,
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'statistics': stats,
                'ranks': {
                    'daily': daily_rank,
                    'weekly': weekly_rank,
                    'all_time': all_time_rank,
                }
            }
        })


# 管理端点（需要管理员权限）

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def refresh_ranking_cache(request):
    """
    刷新排行榜缓存
    
    POST /api/ranking/admin/refresh-cache/
    
    查询参数:
    - type: 缓存类型 (daily/weekly/all-time/all)，默认 all
    """
    cache_type = request.data.get('type', 'all')
    
    try:
        if cache_type == 'daily':
            RankingCacheService.invalidate_daily_cache()
            RankingCacheService.get_or_generate_daily_leaderboard()
        elif cache_type == 'weekly':
            RankingCacheService.invalidate_weekly_cache()
            RankingCacheService.get_or_generate_weekly_leaderboard()
        elif cache_type == 'all-time':
            RankingCacheService.invalidate_all_time_cache()
            RankingCacheService.get_or_generate_all_time_leaderboard()
        else:  # all
            RankingCacheService.invalidate_daily_cache()
            RankingCacheService.invalidate_weekly_cache()
            RankingCacheService.invalidate_all_time_cache()
            RankingCacheService.get_or_generate_daily_leaderboard()
            RankingCacheService.get_or_generate_weekly_leaderboard()
            RankingCacheService.get_or_generate_all_time_leaderboard()
        
        return Response({
            'success': True,
            'message': '排行榜缓存已刷新'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'REFRESH_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def cleanup_expired_cache(request):
    """
    清理过期缓存
    
    POST /api/ranking/admin/cleanup-cache/
    """
    try:
        RankingCacheService.cleanup_expired_caches()
        
        return Response({
            'success': True,
            'message': '过期缓存已清理'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'CLEANUP_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
