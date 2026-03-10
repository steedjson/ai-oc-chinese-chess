"""
残局挑战服务层

包含：
- PuzzleService: 残局关卡服务
- PuzzleAttemptService: 挑战记录服务
- PuzzleProgressService: 用户进度服务
"""
import json
from typing import List, Dict, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress, PuzzleAttemptStatus


class PuzzleService:
    """残局关卡服务"""
    
    @staticmethod
    def get_puzzle_list(difficulty: Optional[int] = None, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取关卡列表
        
        Args:
            difficulty: 难度筛选 (可选)
            page: 页码
            page_size: 每页数量
            
        Returns:
            关卡列表和分页信息
        """
        puzzles = Puzzle.objects.filter(is_active=True)
        
        if difficulty:
            puzzles = puzzles.filter(difficulty=difficulty)
        
        puzzles = puzzles.order_by('difficulty', 'created_at')
        
        paginator = Paginator(puzzles, page_size)
        page_obj = paginator.page(page)
        
        return {
            'results': [
                {
                    'id': str(puzzle.id),
                    'title': puzzle.title,
                    'description': puzzle.description,
                    'difficulty': puzzle.difficulty,
                    'stars': puzzle.difficulty,  # 难度即星级
                    'move_limit': puzzle.move_limit,
                    'time_limit': puzzle.time_limit,
                    'total_attempts': puzzle.total_attempts,
                    'total_completions': puzzle.total_completions,
                    'completion_rate': float(puzzle.completion_rate),
                }
                for puzzle in page_obj.object_list
            ],
            'pagination': {
                'page': page_obj.number,
                'page_size': page_size,
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_prev': page_obj.has_previous(),
            }
        }
    
    @staticmethod
    def get_puzzle_detail(puzzle_id: str) -> Optional[Dict]:
        """
        获取关卡详情
        
        Args:
            puzzle_id: 关卡 ID
            
        Returns:
            关卡详情
        """
        try:
            puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
            return {
                'id': str(puzzle.id),
                'title': puzzle.title,
                'description': puzzle.description,
                'source': puzzle.source,
                'fen_initial': puzzle.fen_initial,
                'difficulty': puzzle.difficulty,
                'move_limit': puzzle.move_limit,
                'time_limit': puzzle.time_limit,
                'hint': puzzle.hint,
                'total_attempts': puzzle.total_attempts,
                'total_completions': puzzle.total_completions,
            }
        except Puzzle.DoesNotExist:
            return None
    
    @staticmethod
    def verify_move(puzzle: Puzzle, attempt: PuzzleAttempt, move_data: Dict) -> Tuple[bool, str]:
        """
        验证用户走法是否正确
        
        Args:
            puzzle: 残局关卡
            attempt: 挑战记录
            move_data: 走棋数据 {"from": "e2", "to": "e4", "piece": "P"}
            
        Returns:
            (是否正确，提示信息)
        """
        # 获取当前应该走的解法步骤
        current_index = attempt.current_move_index
        
        if current_index >= len(puzzle.solution_moves):
            return False, "关卡已完成"
        
        expected_move = puzzle.solution_moves[current_index]
        
        # 验证走法是否匹配
        if (move_data.get('from') == expected_move['from'] and
            move_data.get('to') == expected_move['to'] and
            move_data.get('piece') == expected_move['piece']):
            return True, "走法正确"
        else:
            return False, "走法错误，请重新思考"
    
    @staticmethod
    def is_puzzle_complete(attempt: PuzzleAttempt) -> bool:
        """
        判断关卡是否完成
        
        Args:
            attempt: 挑战记录
            
        Returns:
            是否完成
        """
        puzzle = attempt.puzzle
        return attempt.current_move_index >= len(puzzle.solution_moves)
    
    @staticmethod
    def get_hint(puzzle: Puzzle) -> Optional[str]:
        """
        获取提示
        
        Args:
            puzzle: 残局关卡
            
        Returns:
            提示内容
        """
        return puzzle.hint if puzzle.hint else None


class PuzzleAttemptService:
    """挑战记录服务"""
    
    @staticmethod
    @transaction.atomic
    def create_attempt(user, puzzle_id: str) -> Optional[PuzzleAttempt]:
        """
        创建挑战记录
        
        Args:
            user: 用户
            puzzle_id: 关卡 ID
            
        Returns:
            挑战记录
        """
        try:
            puzzle = Puzzle.objects.get(id=puzzle_id, is_active=True)
            
            # 检查是否已有进行中的挑战
            existing = PuzzleAttempt.objects.filter(
                user=user,
                puzzle=puzzle,
                status=PuzzleAttemptStatus.IN_PROGRESS
            ).first()
            
            if existing:
                return existing
            
            # 创建新挑战
            attempt = PuzzleAttempt.objects.create(
                user=user,
                puzzle=puzzle,
                status=PuzzleAttemptStatus.IN_PROGRESS,
                fen_current=puzzle.fen_initial,
                current_move_index=0,
                move_history=[],
                moves_used=0,
                time_used=0,
            )
            
            # 更新关卡统计
            puzzle.total_attempts += 1
            puzzle.save()
            
            return attempt
        except Puzzle.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def update_attempt(attempt: PuzzleAttempt, move_data: Dict, is_correct: bool) -> Dict:
        """
        更新挑战记录
        
        Args:
            attempt: 挑战记录
            move_data: 走棋数据
            is_correct: 是否正确
            
        Returns:
            更新结果
        """
        # 记录走棋历史
        move_record = {
            'from': move_data.get('from'),
            'to': move_data.get('to'),
            'piece': move_data.get('piece'),
            'correct': is_correct,
        }
        attempt.move_history.append(move_record)
        attempt.moves_used += 1
        
        if is_correct:
            attempt.current_move_index += 1
            
            # 检查是否完成
            if PuzzleService.is_puzzle_complete(attempt):
                attempt.status = PuzzleAttemptStatus.SUCCESS
                attempt.completed_at = timezone.now()
                
                # 计算评分（星级）
                stars = PuzzleAttemptService.calculate_stars(attempt)
                attempt.stars = stars
                
                # 计算积分
                points = PuzzleAttemptService.calculate_points(attempt, stars)
                attempt.points_earned = points
                
                # 更新关卡通关统计
                attempt.puzzle.total_completions += 1
                attempt.puzzle.save()
        
        attempt.save()
        
        return {
            'status': attempt.status,
            'current_move_index': attempt.current_move_index,
            'moves_used': attempt.moves_used,
            'is_complete': attempt.status == PuzzleAttemptStatus.SUCCESS,
            'stars': attempt.stars,
            'points_earned': attempt.points_earned,
        }
    
    @staticmethod
    def calculate_stars(attempt: PuzzleAttempt) -> int:
        """
        计算评分（星级）
        
        评分标准：
        - 3 星：步数 <= 解法步数 * 1.2
        - 2 星：步数 <= 解法步数 * 1.5
        - 1 星：完成即可
        
        Returns:
            星级 (1-3)
        """
        puzzle = attempt.puzzle
        optimal_moves = len(puzzle.solution_moves)
        actual_moves = attempt.moves_used
        
        if actual_moves <= optimal_moves * 1.2:
            return 3
        elif actual_moves <= optimal_moves * 1.5:
            return 2
        else:
            return 1
    
    @staticmethod
    def calculate_points(attempt: PuzzleAttempt, stars: int) -> int:
        """
        计算积分
        
        积分 = 基础分 * 星级系数 * 难度系数
        
        Returns:
            积分
        """
        puzzle = attempt.puzzle
        base_points = 100
        
        # 星级系数
        star_multiplier = {1: 1.0, 2: 1.5, 3: 2.0}.get(stars, 1.0)
        
        # 难度系数
        difficulty_multiplier = puzzle.difficulty / 5.0
        
        points = int(base_points * star_multiplier * difficulty_multiplier)
        return points
    
    @staticmethod
    @transaction.atomic
    def abandon_attempt(attempt: PuzzleAttempt) -> None:
        """
        放弃挑战
        
        Args:
            attempt: 挑战记录
        """
        attempt.status = PuzzleAttemptStatus.ABANDONED
        attempt.save()


class PuzzleProgressService:
    """用户进度服务"""
    
    @staticmethod
    def get_or_create_progress(user) -> PuzzleProgress:
        """
        获取或创建用户进度
        
        Args:
            user: 用户
            
        Returns:
            用户进度
        """
        progress, created = PuzzleProgress.objects.get_or_create(
            user=user,
            defaults={
                'total_completed': 0,
                'total_attempts': 0,
                'max_difficulty_passed': 0,
                'ranking_points': 0,
            }
        )
        return progress
    
    @staticmethod
    @transaction.atomic
    def update_progress(user) -> PuzzleProgress:
        """
        更新用户进度
        
        Args:
            user: 用户
            
        Returns:
            更新后的进度
        """
        progress = PuzzleProgressService.get_or_create_progress(user)
        progress.update_progress()
        return progress
    
    @staticmethod
    def get_user_statistics(user) -> Dict:
        """
        获取用户统计
        
        Args:
            user: 用户
            
        Returns:
            统计数据
        """
        progress = PuzzleProgressService.get_or_create_progress(user)
        
        # 获取各难度通关数
        difficulty_stats = {}
        for diff in range(1, 11):
            count = PuzzleAttempt.objects.filter(
                user=user,
                puzzle__difficulty=diff,
                status=PuzzleAttemptStatus.SUCCESS
            ).count()
            difficulty_stats[str(diff)] = count
        
        return {
            'total_completed': progress.total_completed,
            'total_attempts': progress.total_attempts,
            'max_difficulty_passed': progress.max_difficulty_passed,
            'total_stars': progress.total_stars,
            'stars_1': progress.stars_1,
            'stars_2': progress.stars_2,
            'stars_3': progress.stars_3,
            'ranking_points': progress.ranking_points,
            'completion_rate': (progress.total_completed / progress.total_attempts * 100) if progress.total_attempts > 0 else 0,
            'difficulty_stats': difficulty_stats,
        }
    
    @staticmethod
    def get_leaderboard(time_range: str = 'all', limit: int = 100) -> List[Dict]:
        """
        获取排行榜
        
        Args:
            time_range: 时间范围 (daily, weekly, all)
            limit: 返回数量
            
        Returns:
            排行榜列表
        """
        from django.utils import timezone
        from datetime import timedelta
        
        progress_list = PuzzleProgress.objects.all().order_by('-ranking_points', '-total_completed')[:limit]
        
        leaderboard = []
        for rank, progress in enumerate(progress_list, 1):
            leaderboard.append({
                'rank': rank,
                'user_id': progress.user.id,
                'username': progress.user.username,
                'ranking_points': progress.ranking_points,
                'total_completed': progress.total_completed,
                'max_difficulty_passed': progress.max_difficulty_passed,
                'total_stars': progress.total_stars,
            })
        
        return leaderboard
    
    @staticmethod
    @transaction.atomic
    def add_ranking_points(user, points: int) -> None:
        """
        添加排名积分
        
        Args:
            user: 用户
            points: 积分
        """
        progress = PuzzleProgressService.get_or_create_progress(user)
        progress.ranking_points += points
        progress.save()
