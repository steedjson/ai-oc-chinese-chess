"""
残局挑战服务层测试
"""
import pytest
from django.contrib.auth import get_user_model
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress, PuzzleDifficulty, PuzzleAttemptStatus
from puzzles.services import PuzzleService, PuzzleAttemptService, PuzzleProgressService

User = get_user_model()


@pytest.mark.django_db
class TestPuzzleService:
    """测试 PuzzleService"""
    
    def test_get_puzzle_list(self):
        """测试获取关卡列表"""
        # 创建测试数据
        for i in range(5):
            Puzzle.objects.create(
                title=f"测试残局{i}",
                fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
                solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
                difficulty=1,
            )
        
        result = PuzzleService.get_puzzle_list(page=1, page_size=10)
        
        assert len(result['results']) == 5
        assert result['pagination']['total_count'] == 5
    
    def test_get_puzzle_detail(self):
        """测试获取关卡详情"""
        puzzle = Puzzle.objects.create(
            title="测试残局",
            description="测试描述",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            hint="测试提示",
        )
        
        result = PuzzleService.get_puzzle_detail(str(puzzle.id))
        
        assert result is not None
        assert result['title'] == "测试残局"
        assert result['hint'] == "测试提示"
    
    def test_verify_move_correct(self):
        """测试验证正确走法"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[
                {"from": "a1", "to": "a4", "piece": "R"},
                {"from": "a4", "to": "a6", "piece": "R"},
            ],
            difficulty=1,
        )
        
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            fen_current=puzzle.fen_initial,
        )
        
        move_data = {"from": "a1", "to": "a4", "piece": "R"}
        is_correct, message = PuzzleService.verify_move(puzzle, attempt, move_data)
        
        assert is_correct is True
        assert "正确" in message
    
    def test_verify_move_incorrect(self):
        """测试验证错误走法"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            fen_current=puzzle.fen_initial,
        )
        
        move_data = {"from": "a1", "to": "a5", "piece": "R"}  # 错误走法
        is_correct, message = PuzzleService.verify_move(puzzle, attempt, move_data)
        
        assert is_correct is False
        assert "错误" in message
    
    def test_is_puzzle_complete(self):
        """测试关卡完成判断"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        # 未完成
        attempt1 = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            current_move_index=0,
        )
        assert PuzzleService.is_puzzle_complete(attempt1) is False
        
        # 已完成
        attempt2 = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            current_move_index=1,
        )
        assert PuzzleService.is_puzzle_complete(attempt2) is True


@pytest.mark.django_db
class TestPuzzleAttemptService:
    """测试 PuzzleAttemptService"""
    
    def test_create_attempt(self):
        """测试创建挑战"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        
        assert attempt is not None
        assert attempt.user == user
        assert attempt.puzzle == puzzle
        assert attempt.status == PuzzleAttemptStatus.IN_PROGRESS
    
    def test_update_attempt_success(self):
        """测试更新挑战（成功）"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        move_data = {"from": "a1", "to": "a4", "piece": "R"}
        
        result = PuzzleAttemptService.update_attempt(attempt, move_data, is_correct=True)
        
        assert result['is_complete'] is True
        assert result['stars'] is not None
        assert result['points_earned'] > 0
    
    def test_calculate_stars(self):
        """测试星级计算"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            moves_used=1,  # 最优步数
        )
        
        stars = PuzzleAttemptService.calculate_stars(attempt)
        assert stars == 3  # 3 星 (1 <= 1 * 1.2)
        
        attempt.moves_used = 2  # 稍多步数
        stars = PuzzleAttemptService.calculate_stars(attempt)
        assert stars == 1  # 1 星 (2 > 1 * 1.5)


@pytest.mark.django_db
class TestPuzzleProgressService:
    """测试 PuzzleProgressService"""
    
    def test_get_or_create_progress(self):
        """测试获取或创建进度"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        progress = PuzzleProgressService.get_or_create_progress(user)
        
        assert progress is not None
        assert progress.user == user
        assert progress.total_completed == 0
    
    def test_get_user_statistics(self):
        """测试获取用户统计"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        statistics = PuzzleProgressService.get_user_statistics(user)
        
        assert 'total_completed' in statistics
        assert 'ranking_points' in statistics
        assert 'difficulty_stats' in statistics
    
    def test_add_ranking_points(self):
        """测试添加排名积分"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        PuzzleProgressService.add_ranking_points(user, 100)
        
        progress = PuzzleProgress.objects.get(user=user)
        assert progress.ranking_points == 100
