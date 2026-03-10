"""
残局挑战模型测试
"""
import pytest
from django.contrib.auth import get_user_model
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress, PuzzleDifficulty, PuzzleAttemptStatus

User = get_user_model()


@pytest.mark.django_db
class TestPuzzleModel:
    """测试 Puzzle 模型"""
    
    def test_create_puzzle(self):
        """测试创建残局关卡"""
        puzzle = Puzzle.objects.create(
            title="测试残局",
            description="测试描述",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[
                {"from": "a1", "to": "a4", "piece": "R"},
                {"from": "a4", "to": "a6", "piece": "R"},
            ],
            difficulty=PuzzleDifficulty.BEGINNER,
            move_limit=10,
            time_limit=120,
            hint="测试提示",
        )
        
        assert puzzle.title == "测试残局"
        assert puzzle.difficulty == 1
        assert puzzle.is_active is True
        assert len(puzzle.solution_moves) == 2
    
    def test_puzzle_statistics(self):
        """测试关卡统计数据"""
        puzzle = Puzzle.objects.create(
            title="统计测试",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        # 初始统计
        assert puzzle.total_attempts == 0
        assert puzzle.total_completions == 0
        
        # 更新统计
        puzzle.update_statistics()
        assert puzzle.completion_rate == 0


@pytest.mark.django_db
class TestPuzzleAttemptModel:
    """测试 PuzzleAttempt 模型"""
    
    def test_create_attempt(self):
        """测试创建挑战记录"""
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
        
        assert attempt.user == user
        assert attempt.puzzle == puzzle
        assert attempt.status == PuzzleAttemptStatus.IN_PROGRESS
        assert attempt.current_move_index == 0
    
    def test_attempt_move_history(self):
        """测试走棋历史记录"""
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
        
        # 添加走棋记录
        attempt.move_history.append({
            "from": "a1",
            "to": "a4",
            "piece": "R",
            "correct": True,
        })
        attempt.moves_used = 1
        attempt.current_move_index = 1
        attempt.save()
        
        assert len(attempt.move_history) == 1
        assert attempt.moves_used == 1


@pytest.mark.django_db
class TestPuzzleProgressModel:
    """测试 PuzzleProgress 模型"""
    
    def test_create_progress(self):
        """测试创建用户进度"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        progress = PuzzleProgress.objects.create(user=user)
        
        assert progress.user == user
        assert progress.total_completed == 0
        assert progress.ranking_points == 0
    
    def test_update_progress(self):
        """测试更新用户进度"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=3,
        )
        
        # 创建用户进度记录
        progress = PuzzleProgress.objects.create(user=user)
        
        # 创建通关记录
        PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            status=PuzzleAttemptStatus.SUCCESS,
            stars=3,
            points_earned=100,
        )
        
        # 更新进度
        progress.update_progress()
        
        assert progress.total_completed == 1
        assert progress.max_difficulty_passed == 3
        assert progress.stars_3 == 1


@pytest.mark.django_db
class TestPuzzleDifficulty:
    """测试难度等级"""
    
    def test_difficulty_choices(self):
        """测试难度选择"""
        assert PuzzleDifficulty.BEGINNER == 1
        assert PuzzleDifficulty.INTERMEDIATE == 3
        assert PuzzleDifficulty.MASTER == 10
    
    def test_difficulty_labels(self):
        """测试难度标签"""
        labels = dict(PuzzleDifficulty.choices)
        assert labels[1] == '入门 (1 星)'
        assert labels[5] == '进阶 (5 星)'
        assert labels[10] == '大师 (10 星)'
