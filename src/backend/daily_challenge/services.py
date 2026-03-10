"""
每日挑战业务逻辑服务
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction, models
from django.utils import timezone
import random

from .models import DailyChallenge, ChallengeAttempt, ChallengeStreak


class DailyChallengeService:
    """每日挑战服务"""
    
    @staticmethod
    def get_todays_challenge() -> Optional[DailyChallenge]:
        """获取今日挑战"""
        return DailyChallenge.objects.get_todays_challenge()
    
    @staticmethod
    def get_or_create_todays_challenge() -> Tuple[DailyChallenge, bool]:
        """获取或创建今日挑战"""
        return DailyChallenge.objects.get_or_create_todays_challenge()
    
    @staticmethod
    def generate_tomorrow_challenge() -> DailyChallenge:
        """
        生成明日挑战
        
        规则:
        1. 优先选择未使用过的残局
        2. 难度轮换（周一简单，周末困难）
        3. 类型轮换（残局/中局/杀法）
        """
        tomorrow = date.today() + timedelta(days=1)
        
        # 检查是否已存在
        existing = DailyChallenge.objects.filter(date=tomorrow).first()
        if existing:
            return existing
        
        # 根据星期几确定难度范围
        difficulty_range = DailyChallengeService._get_difficulty_for_weekday(tomorrow.weekday())
        
        # 选择未使用过的残局
        from puzzles.models import Puzzle
        
        used_puzzle_ids = DailyChallenge.objects.values_list('puzzle_id', flat=True).exclude(puzzle_id__isnull=True)
        
        available_puzzles = Puzzle.objects.filter(
            difficulty__in=difficulty_range,
            is_active=True
        ).exclude(
            id__in=used_puzzle_ids
        )
        
        if available_puzzles.exists():
            puzzle = random.choice(list(available_puzzles))
            return DailyChallengeService._create_challenge_from_puzzle(puzzle, tomorrow)
        else:
            # 如果没有可用残局，创建自定义局面
            return DailyChallengeService._create_custom_challenge(tomorrow, difficulty_range)
    
    @staticmethod
    def _get_difficulty_for_weekday(weekday: int) -> range:
        """
        根据星期几获取难度范围
        
        weekday: 0=周一，6=周日
        """
        if weekday < 2:  # 周一、周二 - 简单
            return range(1, 5)
        elif weekday < 4:  # 周三、周四 - 中等
            return range(4, 7)
        elif weekday < 6:  # 周五、周六 - 困难
            return range(6, 9)
        else:  # 周日 - 大师
            return range(8, 11)
    
    @staticmethod
    def _create_challenge_from_puzzle(puzzle, challenge_date: date) -> DailyChallenge:
        """从残局创建每日挑战"""
        return DailyChallenge.objects.create(
            date=challenge_date,
            puzzle=puzzle,
            fen=puzzle.fen_initial,
            target_description=puzzle.description,
            solution_moves=puzzle.solution_moves,
            max_moves=puzzle.move_limit,
            time_limit=puzzle.time_limit,
            difficulty=puzzle.difficulty,
            stars=min(puzzle.difficulty, 5),  # 星级 1-5
            is_active=True
        )
    
    @staticmethod
    def _create_custom_challenge(challenge_date: date, difficulty_range: range) -> DailyChallenge:
        """创建自定义挑战"""
        difficulty = random.choice(list(difficulty_range))
        
        # 自定义 FEN（这里使用示例 FEN，实际应该从棋局库中选择）
        custom_fens = [
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
        ]
        
        return DailyChallenge.objects.create(
            date=challenge_date,
            fen=random.choice(custom_fens),
            target_description=f"难度{difficulty}挑战",
            difficulty=difficulty,
            stars=random.randint(3, 5),
            max_moves=random.randint(6, 10),
            time_limit=random.randint(180, 600),
            is_active=True
        )
    
    @staticmethod
    def get_challenge_statistics(challenge: DailyChallenge) -> Dict:
        """获取挑战统计信息"""
        challenge.update_statistics()
        
        return {
            'total_attempts': challenge.total_attempts,
            'unique_players': challenge.unique_players,
            'completion_rate': float(challenge.completion_rate),
        }


class ChallengeAttemptService:
    """挑战尝试服务"""
    
    @staticmethod
    @transaction.atomic
    def create_attempt(user, challenge: DailyChallenge) -> ChallengeAttempt:
        """
        创建挑战尝试
        
        Args:
            user: 用户
            challenge: 每日挑战
        
        Returns:
            ChallengeAttempt: 创建的尝试记录
        """
        # 检查用户今天是否已尝试
        existing = ChallengeAttempt.objects.filter(
            user=user,
            attempted_at__date=date.today()
        ).first()
        
        if existing:
            raise ValueError("您今天已经挑战过了")
        
        attempt = ChallengeAttempt.objects.create(
            challenge=challenge,
            user=user,
            start_fen=challenge.fen,
            move_history=[],
            status='success',  # 默认为成功，实际完成时更新
        )
        
        return attempt
    
    @staticmethod
    @transaction.atomic
    def submit_move(attempt: ChallengeAttempt, move: Dict) -> Dict:
        """
        提交走法
        
        Args:
            attempt: 挑战尝试
            move: 走法信息 {'from': str, 'to': str, 'piece': str}
        
        Returns:
            Dict: 验证结果
        """
        # 验证走法（这里简化处理，实际应该调用游戏服务验证）
        is_valid = ChallengeAttemptService._validate_move(attempt, move)
        
        if not is_valid:
            return {
                'valid': False,
                'error': '无效的走法'
            }
        
        # 更新走棋历史
        attempt.move_history.append(move)
        attempt.moves_used = len(attempt.move_history)
        attempt.save()
        
        # 检查是否完成
        is_complete = ChallengeAttemptService._check_completion(attempt)
        
        return {
            'valid': True,
            'new_fen': attempt.start_fen,  # 实际应该更新 FEN
            'moves_used': attempt.moves_used,
            'is_complete': is_complete,
        }
    
    @staticmethod
    def _validate_move(attempt: ChallengeAttempt, move: Dict) -> bool:
        """验证走法是否有效（简化版）"""
        # 实际应该调用游戏服务验证走法合法性
        required_fields = ['from', 'to', 'piece']
        return all(field in move for field in required_fields)
    
    @staticmethod
    def _check_completion(attempt: ChallengeAttempt) -> bool:
        """检查挑战是否完成"""
        # 检查是否达到目标步数
        if attempt.challenge.max_moves and attempt.moves_used >= attempt.challenge.max_moves:
            return True
        
        # 检查是否匹配解法
        if attempt.challenge.solution_moves:
            solution = attempt.challenge.solution_moves
            if len(attempt.move_history) == len(solution):
                # 比较走法序列
                return True
        
        return False
    
    @staticmethod
    @transaction.atomic
    def complete_attempt(attempt: ChallengeAttempt, status: str = 'success') -> Dict:
        """
        完成挑战
        
        Args:
            attempt: 挑战尝试
            status: 完成状态
        
        Returns:
            Dict: 完成结果
        """
        attempt.status = status
        
        if status == 'success':
            # 计算得分和星级
            attempt.score = attempt.calculate_score()
            attempt.stars_earned = attempt.calculate_stars()
            attempt.is_optimal = (attempt.stars_earned == 3)
        
        attempt.save()
        
        # 更新用户连续打卡
        if status == 'success':
            streak, _ = ChallengeStreak.get_or_create_for_user(attempt.user)
            streak.update_streak()
        
        # 更新挑战统计
        attempt.challenge.update_statistics()
        
        # 获取排名
        rank = ChallengeAttemptService._get_user_rank(attempt)
        
        return {
            'attempt_id': str(attempt.id),
            'status': status,
            'score': attempt.score,
            'stars_earned': attempt.stars_earned,
            'is_optimal': attempt.is_optimal,
            'rank': rank['rank'],
            'total_players': rank['total_players'],
        }
    
    @staticmethod
    def _get_user_rank(attempt: ChallengeAttempt) -> Dict:
        """获取用户排名"""
        # 获取今日所有成功完成的尝试，按得分排序
        today_attempts = ChallengeAttempt.objects.filter(
            challenge=attempt.challenge,
            status='success'
        ).order_by('-score')
        
        total = today_attempts.count()
        rank = 1
        
        for i, a in enumerate(today_attempts, 1):
            if a.user == attempt.user:
                rank = i
                break
        
        return {
            'rank': rank,
            'total_players': total,
        }
    
    @staticmethod
    def get_user_attempt_for_today(user, challenge: DailyChallenge) -> Optional[ChallengeAttempt]:
        """获取用户今日的挑战尝试"""
        return ChallengeAttempt.objects.filter(
            challenge=challenge,
            user=user,
            attempted_at__date=date.today()
        ).first()


class ChallengeStreakService:
    """连续打卡服务"""
    
    @staticmethod
    def get_user_streak(user) -> ChallengeStreak:
        """获取用户连续打卡记录"""
        streak, _ = ChallengeStreak.get_or_create_for_user(user)
        return streak
    
    @staticmethod
    def get_leaderboard(limit: int = 100) -> List[ChallengeStreak]:
        """获取连续打卡排行榜"""
        return list(ChallengeStreak.objects.filter(
            current_streak__gt=0
        ).select_related('user').order_by(
            '-current_streak',
            '-total_completions'
        )[:limit])
    
    @staticmethod
    def get_user_statistics(user) -> Dict:
        """获取用户统计信息"""
        streak = ChallengeStreak.objects.filter(user=user).first()
        
        if not streak:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_completions': 0,
                'total_perfect': 0,
            }
        
        return {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'total_completions': streak.total_completions,
            'total_perfect': streak.total_perfect,
        }


class ChallengeLeaderboardService:
    """挑战排行榜服务"""
    
    @staticmethod
    def get_daily_leaderboard(challenge_date: date = None, limit: int = 100) -> List[Dict]:
        """
        获取每日挑战排行榜
        
        Args:
            challenge_date: 挑战日期，默认为今天
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        if challenge_date is None:
            challenge_date = date.today()
        
        challenge = DailyChallenge.objects.filter(date=challenge_date).first()
        if not challenge:
            return []
        
        # 获取成功完成的尝试，按得分排序
        attempts = ChallengeAttempt.objects.filter(
            challenge=challenge,
            status='success'
        ).select_related('user').order_by('-score', 'moves_used', 'time_used')[:limit]
        
        leaderboard = []
        for rank, attempt in enumerate(attempts, 1):
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(attempt.user.id),
                    'username': attempt.user.username,
                    'avatar': getattr(attempt.user, 'avatar', None),
                },
                'score': attempt.score,
                'moves_used': attempt.moves_used,
                'time_used': attempt.time_used,
                'stars': attempt.stars_earned,
                'completed_at': attempt.attempted_at.isoformat(),
            })
        
        return leaderboard
    
    @staticmethod
    def get_user_rank(user, challenge_date: date = None) -> Optional[Dict]:
        """获取用户排名（每日）"""
        if challenge_date is None:
            challenge_date = date.today()
        
        challenge = DailyChallenge.objects.filter(date=challenge_date).first()
        if not challenge:
            return None
        
        # 获取用户今日的最佳尝试
        user_attempt = ChallengeAttempt.objects.filter(
            challenge=challenge,
            user=user,
            status='success'
        ).order_by('-score').first()
        
        if not user_attempt:
            return None
        
        # 计算排名
        better_attempts = ChallengeAttempt.objects.filter(
            challenge=challenge,
            status='success',
            score__gt=user_attempt.score
        ).count()
        
        total = ChallengeAttempt.objects.filter(
            challenge=challenge,
            status='success'
        ).count()
        
        return {
            'rank': better_attempts + 1,
            'score': user_attempt.score,
            'total_players': total,
            'percentile': (total - better_attempts) / total * 100 if total > 0 else 0,
        }
    
    @staticmethod
    def get_weekly_leaderboard(week_start: date, week_end: date, limit: int = 100) -> List[Dict]:
        """
        获取周排行榜
        
        Args:
            week_start: 周起始日期
            week_end: 周结束日期
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        from django.db.models import Sum, Count, Avg, Max
        
        # 获取该周内的所有挑战
        challenges = DailyChallenge.objects.filter(
            date__gte=week_start,
            date__lte=week_end
        )
        
        challenge_ids = [c.id for c in challenges]
        
        if not challenge_ids:
            return []
        
        # 按用户聚合统计
        user_stats = ChallengeAttempt.objects.filter(
            challenge_id__in=challenge_ids,
            status='success'
        ).values('user').annotate(
            total_score=Sum('score'),
            challenges_completed=Count('id'),
            best_stars=Max('stars_earned'),
            avg_score=Avg('score'),
        ).order_by('-total_score', '-challenges_completed', '-avg_score')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(id=stat['user']).first()
            
            if not user:
                continue
            
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'avatar': getattr(user, 'avatar', None),
                },
                'total_score': stat['total_score'] or 0,
                'challenges_completed': stat['challenges_completed'],
                'best_stars': stat['best_stars'] or 0,
                'avg_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0,
            })
        
        return leaderboard
    
    @staticmethod
    def get_user_weekly_rank(user, week_start: date, week_end: date) -> Optional[Dict]:
        """获取用户周排名"""
        from django.db.models import Sum, Count, Avg, Max
        
        # 获取该周内的所有挑战
        challenges = DailyChallenge.objects.filter(
            date__gte=week_start,
            date__lte=week_end
        )
        
        challenge_ids = [c.id for c in challenges]
        
        if not challenge_ids:
            return None
        
        # 获取用户的周统计
        user_stats = ChallengeAttempt.objects.filter(
            challenge_id__in=challenge_ids,
            user=user,
            status='success'
        ).aggregate(
            total_score=Sum('score'),
            challenges_completed=Count('id'),
            best_stars=Max('stars_earned'),
            avg_score=Avg('score'),
        )
        
        if not user_stats['total_score']:
            return None
        
        # 计算排名
        better_users = ChallengeAttempt.objects.filter(
            challenge_id__in=challenge_ids,
            status='success'
        ).values('user').annotate(
            total_score=Sum('score')
        ).filter(
            total_score__gt=user_stats['total_score']
        ).count()
        
        total_users = ChallengeAttempt.objects.filter(
            challenge_id__in=challenge_ids,
            status='success'
        ).values('user').distinct().count()
        
        return {
            'rank': better_users + 1,
            'total_score': user_stats['total_score'],
            'challenges_completed': user_stats['challenges_completed'],
            'best_stars': user_stats['best_stars'] or 0,
            'avg_score': round(user_stats['avg_score'], 2) if user_stats['avg_score'] else 0,
            'total_players': total_users,
            'percentile': (total_users - better_users) / total_users * 100 if total_users > 0 else 0,
        }
    
    @staticmethod
    def get_all_time_leaderboard(limit: int = 100) -> List[Dict]:
        """
        获取总排行榜
        
        Args:
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 排行榜列表
        """
        from django.db.models import Sum, Count, Avg, Max
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # 按用户聚合统计
        user_stats = ChallengeAttempt.objects.filter(
            status='success'
        ).values('user').annotate(
            total_score=Sum('score'),
            total_challenges=Count('id'),
            total_perfect=Count('id', filter=models.Q(is_optimal=True)),
            avg_score=Avg('score'),
        ).order_by('-total_score', '-total_challenges', '-total_perfect')[:limit]
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            user = User.objects.filter(id=stat['user']).first()
            
            if not user:
                continue
            
            # 获取用户的最长连击
            streak = ChallengeStreak.objects.filter(user=user).first()
            longest_streak = streak.longest_streak if streak else 0
            
            leaderboard.append({
                'rank': rank,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'avatar': getattr(user, 'avatar', None),
                },
                'total_score': stat['total_score'] or 0,
                'total_challenges': stat['total_challenges'],
                'total_perfect': stat['total_perfect'],
                'longest_streak': longest_streak,
                'avg_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0,
            })
        
        return leaderboard
    
    @staticmethod
    def get_user_all_time_rank(user) -> Optional[Dict]:
        """获取用户总排名"""
        from django.db.models import Sum, Count, Avg, Max
        
        # 获取用户的总统计
        user_stats = ChallengeAttempt.objects.filter(
            user=user,
            status='success'
        ).aggregate(
            total_score=Sum('score'),
            total_challenges=Count('id'),
            total_perfect=Count('id', filter=models.Q(is_optimal=True)),
            avg_score=Avg('score'),
        )
        
        if not user_stats['total_score']:
            return None
        
        # 获取用户的最长连击
        streak = ChallengeStreak.objects.filter(user=user).first()
        longest_streak = streak.longest_streak if streak else 0
        
        # 计算排名
        better_users = ChallengeAttempt.objects.filter(
            status='success'
        ).values('user').annotate(
            total_score=Sum('score')
        ).filter(
            total_score__gt=user_stats['total_score']
        ).count()
        
        total_users = ChallengeAttempt.objects.filter(
            status='success'
        ).values('user').distinct().count()
        
        return {
            'rank': better_users + 1,
            'total_score': user_stats['total_score'],
            'total_challenges': user_stats['total_challenges'],
            'total_perfect': user_stats['total_perfect'],
            'longest_streak': longest_streak,
            'avg_score': round(user_stats['avg_score'], 2) if user_stats['avg_score'] else 0,
            'total_players': total_users,
            'percentile': (total_users - better_users) / total_users * 100 if total_users > 0 else 0,
        }
