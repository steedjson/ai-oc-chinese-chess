"""
中国象棋排行榜业务逻辑服务

包含：
- RankingService: 排行榜核心服务
- RankingCacheService: 排行榜缓存服务
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from django.db import transaction, models
from django.db.models import Sum, Count, Avg, Max, Min, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .ranking_models import (
    GameRecord,
    GameResult,
    RankingCache,
    UserRankingStats,
)


User = get_user_model()


class RankingCacheService:
    """排行榜缓存服务"""
    
    CACHE_TTL_HOURS = 1  # 缓存有效期（小时）
    
    @staticmethod
    def get_or_generate_daily_leaderboard(cache_date=None, limit=100):
        """
        获取或生成每日排行榜
        
        Args:
            cache_date: 日期，默认为今天
            limit: 返回数量限制
        
        Returns:
            Tuple[List[Dict], bool]: (排行榜数据，是否从缓存获取)
        """
        if cache_date is None:
            cache_date = date.today()
        
        # 尝试从缓存获取
        cache = RankingCache.get_daily_cache(cache_date)
        if cache and cache.is_valid:
            return cache.leaderboard_data[:limit], True
        
        # 生成新的排行榜
        leaderboard = RankingService.calculate_daily_leaderboard(cache_date, limit)
        
        # 更新缓存
        total_players = RankingService.get_daily_player_count(cache_date)
        RankingCacheService.update_daily_cache(cache_date, leaderboard, total_players)
        
        return leaderboard, False
    
    @staticmethod
    def get_or_generate_weekly_leaderboard(week=None, year=None, limit=100):
        """
        获取或生成每周排行榜
        
        Args:
            week: 周数，默认为当前周
            year: 年份，默认为当前年
            limit: 返回数量限制
        
        Returns:
            Tuple[List[Dict], bool]: (排行榜数据，是否从缓存获取)
        """
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        # 尝试从缓存获取
        cache = RankingCache.get_weekly_cache(week, year)
        if cache and cache.is_valid:
            return cache.leaderboard_data[:limit], True
        
        # 生成新的排行榜
        leaderboard = RankingService.calculate_weekly_leaderboard(week, year, limit)
        
        # 更新缓存
        total_players = RankingService.get_weekly_player_count(week, year)
        RankingCacheService.update_weekly_cache(week, year, leaderboard, total_players)
        
        return leaderboard, False
    
    @staticmethod
    def get_or_generate_all_time_leaderboard(limit=100):
        """
        获取或生成总排行榜
        
        Args:
            limit: 返回数量限制
        
        Returns:
            Tuple[List[Dict], bool]: (排行榜数据，是否从缓存获取)
        """
        # 尝试从缓存获取
        cache = RankingCache.get_all_time_cache()
        if cache and cache.is_valid:
            return cache.leaderboard_data[:limit], True
        
        # 生成新的排行榜
        leaderboard = RankingService.calculate_all_time_leaderboard(limit)
        
        # 更新缓存
        total_players = RankingService.get_all_time_player_count()
        RankingCacheService.update_all_time_cache(leaderboard, total_players)
        
        return leaderboard, False
    
    @staticmethod
    def update_daily_cache(cache_date, leaderboard_data, total_players):
        """更新每日排行榜缓存"""
        cache, _ = RankingCache.objects.update_or_create(
            ranking_type='daily',
            cache_date=cache_date,
            defaults={
                'leaderboard_data': leaderboard_data,
                'total_players': total_players,
                'expires_at': timezone.now() + timedelta(hours=RankingCacheService.CACHE_TTL_HOURS),
                'is_valid': True,
            }
        )
        return cache
    
    @staticmethod
    def update_weekly_cache(week, year, leaderboard_data, total_players):
        """更新每周排行榜缓存"""
        cache, _ = RankingCache.objects.update_or_create(
            ranking_type='weekly',
            cache_week=week,
            cache_year=year,
            defaults={
                'leaderboard_data': leaderboard_data,
                'total_players': total_players,
                'expires_at': timezone.now() + timedelta(hours=RankingCacheService.CACHE_TTL_HOURS),
                'is_valid': True,
            }
        )
        return cache
    
    @staticmethod
    def update_all_time_cache(leaderboard_data, total_players):
        """更新总排行榜缓存"""
        cache, _ = RankingCache.objects.update_or_create(
            ranking_type='all_time',
            defaults={
                'leaderboard_data': leaderboard_data,
                'total_players': total_players,
                'expires_at': timezone.now() + timedelta(hours=RankingCacheService.CACHE_TTL_HOURS),
                'is_valid': True,
            }
        )
        return cache
    
    @staticmethod
    def invalidate_daily_cache(cache_date=None):
        """使每日排行榜缓存失效"""
        if cache_date is None:
            cache_date = date.today()
        
        RankingCache.objects.filter(
            ranking_type='daily',
            cache_date=cache_date
        ).update(is_valid=False)
    
    @staticmethod
    def invalidate_weekly_cache(week=None, year=None):
        """使每周排行榜缓存失效"""
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        RankingCache.objects.filter(
            ranking_type='weekly',
            cache_week=week,
            cache_year=year
        ).update(is_valid=False)
    
    @staticmethod
    def invalidate_all_time_cache():
        """使总排行榜缓存失效"""
        RankingCache.objects.filter(
            ranking_type='all_time'
        ).update(is_valid=False)
    
    @staticmethod
    def cleanup_expired_caches():
        """清理过期的缓存"""
        expired_time = timezone.now()
        
        RankingCache.objects.filter(
            expires_at__lt=expired_time,
            is_valid=True
        ).update(is_valid=False)


class RankingService:
    """排行榜核心服务"""
    
    @staticmethod
    def calculate_daily_leaderboard(cache_date=None, limit=100):
        """
        计算每日排行榜
        
        Args:
            cache_date: 日期，默认为今天
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        if cache_date is None:
            cache_date = date.today()
        
        # 按用户聚合统计
        user_stats = GameRecord.objects.filter(
            game_date=cache_date,
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
            losses=Count('id', filter=Q(result=GameResult.LOSS)),
            draws=Count('id', filter=Q(result=GameResult.DRAW)),
            highest_score=Max('score_gained'),
            avg_score=Avg('score_gained'),
        ).order_by('-total_score', '-wins', '-avg_score')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            user = User.objects.filter(id=stat['user']).first()
            if not user:
                continue
            
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'avatar_url': getattr(user, 'avatar_url', None),
                },
                'total_score': stat['total_score'] or 0,
                'games_played': stat['games_played'],
                'wins': stat['wins'],
                'losses': stat['losses'],
                'draws': stat['draws'],
                'highest_score': stat['highest_score'] or 0,
                'avg_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0,
            })
        
        return leaderboard
    
    @staticmethod
    def calculate_weekly_leaderboard(week=None, year=None, limit=100):
        """
        计算每周排行榜
        
        Args:
            week: 周数，默认为当前周
            year: 年份，默认为当前年
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        # 按用户聚合统计
        user_stats = GameRecord.objects.filter(
            game_week=week,
            game_year=year,
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
            losses=Count('id', filter=Q(result=GameResult.LOSS)),
            draws=Count('id', filter=Q(result=GameResult.DRAW)),
            highest_score=Max('score_gained'),
            avg_score=Avg('score_gained'),
        ).order_by('-total_score', '-wins', '-avg_score')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            user = User.objects.filter(id=stat['user']).first()
            if not user:
                continue
            
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'avatar_url': getattr(user, 'avatar_url', None),
                },
                'total_score': stat['total_score'] or 0,
                'games_played': stat['games_played'],
                'wins': stat['wins'],
                'losses': stat['losses'],
                'draws': stat['draws'],
                'highest_score': stat['highest_score'] or 0,
                'avg_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0,
            })
        
        return leaderboard
    
    @staticmethod
    def calculate_all_time_leaderboard(limit=100):
        """
        计算总排行榜
        
        Args:
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        # 按用户聚合统计
        user_stats = GameRecord.objects.filter(
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
            losses=Count('id', filter=Q(result=GameResult.LOSS)),
            draws=Count('id', filter=Q(result=GameResult.DRAW)),
            highest_score=Max('score_gained'),
            avg_score=Avg('score_gained'),
        ).order_by('-total_score', '-wins', '-avg_score')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            user = User.objects.filter(id=stat['user']).first()
            if not user:
                continue
            
            # 获取用户排名统计
            user_ranking_stats = UserRankingStats.objects.filter(user=user).first()
            longest_streak = user_ranking_stats.longest_win_streak if user_ranking_stats else 0
            
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'avatar_url': getattr(user, 'avatar_url', None),
                },
                'total_score': stat['total_score'] or 0,
                'games_played': stat['games_played'],
                'wins': stat['wins'],
                'losses': stat['losses'],
                'draws': stat['draws'],
                'highest_score': stat['highest_score'] or 0,
                'avg_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0,
                'longest_win_streak': longest_streak,
            })
        
        return leaderboard
    
    @staticmethod
    def get_daily_player_count(cache_date=None):
        """获取每日玩家总数"""
        if cache_date is None:
            cache_date = date.today()
        
        return GameRecord.objects.filter(
            game_date=cache_date,
            is_rated=True
        ).values('user').distinct().count()
    
    @staticmethod
    def get_weekly_player_count(week=None, year=None):
        """获取每周玩家总数"""
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        return GameRecord.objects.filter(
            game_week=week,
            game_year=year,
            is_rated=True
        ).values('user').distinct().count()
    
    @staticmethod
    def get_all_time_player_count():
        """获取总玩家数"""
        return GameRecord.objects.filter(
            is_rated=True
        ).values('user').distinct().count()
    
    @staticmethod
    def get_user_daily_rank(user, cache_date=None):
        """
        获取用户每日排名
        
        Args:
            user: 用户实例
            cache_date: 日期，默认为今天
        
        Returns:
            Optional[Dict]: 用户排名信息
        """
        if cache_date is None:
            cache_date = date.today()
        
        # 获取用户今日统计
        user_stats = GameRecord.objects.filter(
            user=user,
            game_date=cache_date,
            is_rated=True
        ).aggregate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
        )
        
        if not user_stats['total_score']:
            return None
        
        # 计算排名
        better_users = GameRecord.objects.filter(
            game_date=cache_date,
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained')
        ).filter(
            total_score__gt=user_stats['total_score']
        ).count()
        
        total_players = RankingService.get_daily_player_count(cache_date)
        
        return {
            'rank': better_users + 1,
            'total_score': user_stats['total_score'],
            'games_played': user_stats['games_played'],
            'wins': user_stats['wins'],
            'total_players': total_players,
            'percentile': round((total_players - better_users) / total_players * 100, 2) if total_players > 0 else 0,
        }
    
    @staticmethod
    def get_user_weekly_rank(user, week=None, year=None):
        """
        获取用户周排名
        
        Args:
            user: 用户实例
            week: 周数，默认为当前周
            year: 年份，默认为当前年
        
        Returns:
            Optional[Dict]: 用户排名信息
        """
        if week is None or year is None:
            today = date.today()
            iso_calendar = today.isocalendar()
            week = iso_calendar[1]
            year = iso_calendar[0]
        
        # 获取用户本周统计
        user_stats = GameRecord.objects.filter(
            user=user,
            game_week=week,
            game_year=year,
            is_rated=True
        ).aggregate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
        )
        
        if not user_stats['total_score']:
            return None
        
        # 计算排名
        better_users = GameRecord.objects.filter(
            game_week=week,
            game_year=year,
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained')
        ).filter(
            total_score__gt=user_stats['total_score']
        ).count()
        
        total_players = RankingService.get_weekly_player_count(week, year)
        
        return {
            'rank': better_users + 1,
            'total_score': user_stats['total_score'],
            'games_played': user_stats['games_played'],
            'wins': user_stats['wins'],
            'total_players': total_players,
            'percentile': round((total_players - better_users) / total_players * 100, 2) if total_players > 0 else 0,
        }
    
    @staticmethod
    def get_user_all_time_rank(user):
        """
        获取用户总排名
        
        Args:
            user: 用户实例
        
        Returns:
            Optional[Dict]: 用户排名信息
        """
        # 获取用户总统计
        user_stats = GameRecord.objects.filter(
            user=user,
            is_rated=True
        ).aggregate(
            total_score=Sum('score_gained'),
            games_played=Count('id'),
            wins=Count('id', filter=Q(result=GameResult.WIN)),
        )
        
        if not user_stats['total_score']:
            return None
        
        # 获取用户连胜记录
        user_ranking_stats = UserRankingStats.objects.filter(user=user).first()
        longest_streak = user_ranking_stats.longest_win_streak if user_ranking_stats else 0
        
        # 计算排名
        better_users = GameRecord.objects.filter(
            is_rated=True
        ).values('user').annotate(
            total_score=Sum('score_gained')
        ).filter(
            total_score__gt=user_stats['total_score']
        ).count()
        
        total_players = RankingService.get_all_time_player_count()
        
        return {
            'rank': better_users + 1,
            'total_score': user_stats['total_score'],
            'games_played': user_stats['games_played'],
            'wins': user_stats['wins'],
            'longest_win_streak': longest_streak,
            'total_players': total_players,
            'percentile': round((total_players - better_users) / total_players * 100, 2) if total_players > 0 else 0,
        }
    
    @staticmethod
    @transaction.atomic
    def record_game_result(game, winner, loser=None, is_draw=False):
        """
        记录游戏结果到排行榜
        
        Args:
            game: Game 实例
            winner: 获胜者用户实例（和棋时为 None）
            loser: 失败者用户实例（和棋时为 None）
            is_draw: 是否和棋
        """
        # 计算得分（简化版，实际应该根据 Elo 系统计算）
        win_score = 100
        loss_score = 0
        draw_score = 50
        
        if is_draw:
            # 和棋
            if game.red_player:
                GameRecord.create_from_game(
                    game=game,
                    user=game.red_player,
                    result=GameResult.DRAW,
                    score_gained=draw_score,
                    elo_change=0
                )
            if game.black_player:
                GameRecord.create_from_game(
                    game=game,
                    user=game.black_player,
                    result=GameResult.DRAW,
                    score_gained=draw_score,
                    elo_change=0
                )
        else:
            # 有胜负
            if winner and game.red_player == winner:
                GameRecord.create_from_game(
                    game=game,
                    user=game.red_player,
                    result=GameResult.WIN,
                    score_gained=win_score,
                    elo_change=10
                )
            if loser and game.black_player == loser:
                GameRecord.create_from_game(
                    game=game,
                    user=game.black_player,
                    result=GameResult.LOSS,
                    score_gained=loss_score,
                    elo_change=-10
                )
            if winner and game.black_player == winner:
                GameRecord.create_from_game(
                    game=game,
                    user=game.black_player,
                    result=GameResult.WIN,
                    score_gained=win_score,
                    elo_change=10
                )
            if loser and game.red_player == loser:
                GameRecord.create_from_game(
                    game=game,
                    user=game.red_player,
                    result=GameResult.LOSS,
                    score_gained=loss_score,
                    elo_change=-10
                )
        
        # 更新用户统计
        if game.red_player:
            stats, _ = UserRankingStats.get_or_create_for_user(game.red_player)
            stats.update_stats()
        
        if game.black_player:
            stats, _ = UserRankingStats.get_or_create_for_user(game.black_player)
            stats.update_stats()
        
        # 使相关缓存失效
        RankingCacheService.invalidate_daily_cache()
        RankingCacheService.invalidate_weekly_cache()
        RankingCacheService.invalidate_all_time_cache()
    
    @staticmethod
    def get_user_stats(user):
        """
        获取用户排行榜统计
        
        Args:
            user: 用户实例
        
        Returns:
            Dict: 用户统计信息
        """
        stats = UserRankingStats.objects.filter(user=user).first()
        
        if not stats:
            return {
                'total_games': 0,
                'total_wins': 0,
                'total_losses': 0,
                'total_draws': 0,
                'total_score': 0,
                'highest_score': 0,
                'average_score': 0.0,
                'current_win_streak': 0,
                'longest_win_streak': 0,
            }
        
        return {
            'total_games': stats.total_games,
            'total_wins': stats.total_wins,
            'total_losses': stats.total_losses,
            'total_draws': stats.total_draws,
            'total_score': stats.total_score,
            'highest_score': stats.highest_score,
            'average_score': float(stats.average_score),
            'current_win_streak': stats.current_win_streak,
            'longest_win_streak': stats.longest_win_streak,
        }
