"""
残局服务扩展测试
覆盖更多边界情况和异常场景
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress, PuzzleAttemptStatus
from puzzles.services import PuzzleService, PuzzleAttemptService, PuzzleProgressService

User = get_user_model()


@pytest.mark.django_db
class TestPuzzleServiceExtended:
    """PuzzleService 扩展测试"""
    
    def test_get_puzzle_list_with_difficulty_filter(self):
        """测试按难度筛选关卡"""
        # 创建不同难度的关卡
        for diff in range(1, 6):
            Puzzle.objects.create(
                title=f"难度{diff}残局",
                fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
                solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
                difficulty=diff,
            )
        
        # 筛选难度 3 的关卡
        result = PuzzleService.get_puzzle_list(difficulty=3, page=1, page_size=10)
        
        assert len(result['results']) == 1
        assert result['results'][0]['difficulty'] == 3
        assert result['pagination']['total_count'] == 1
    
    def test_get_puzzle_list_pagination(self):
        """测试分页功能"""
        # 创建 25 个关卡
        for i in range(25):
            Puzzle.objects.create(
                title=f"测试残局{i}",
                fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
                solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
                difficulty=1,
            )
        
        # 第一页
        result_page1 = PuzzleService.get_puzzle_list(page=1, page_size=10)
        assert len(result_page1['results']) == 10
        assert result_page1['pagination']['page'] == 1
        assert result_page1['pagination']['total_pages'] == 3
        assert result_page1['pagination']['has_next'] is True
        assert result_page1['pagination']['has_prev'] is False
        
        # 第二页
        result_page2 = PuzzleService.get_puzzle_list(page=2, page_size=10)
        assert len(result_page2['results']) == 10
        assert result_page2['pagination']['page'] == 2
        assert result_page2['pagination']['has_next'] is True
        assert result_page2['pagination']['has_prev'] is True
        
        # 第三页
        result_page3 = PuzzleService.get_puzzle_list(page=3, page_size=10)
        assert len(result_page3['results']) == 5
        assert result_page3['pagination']['page'] == 3
        assert result_page3['pagination']['has_next'] is False
        assert result_page3['pagination']['has_prev'] is True
    
    def test_get_puzzle_list_only_active(self):
        """测试只返回启用的关卡"""
        Puzzle.objects.create(
            title="启用的残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=True,
        )
        Puzzle.objects.create(
            title="禁用的残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=False,
        )
        
        result = PuzzleService.get_puzzle_list(page=1, page_size=10)
        
        assert len(result['results']) == 1
        assert result['results'][0]['title'] == "启用的残局"
    
    def test_get_puzzle_detail_not_found(self):
        """测试获取不存在的关卡详情"""
        import uuid
        non_existent_id = str(uuid.uuid4())
        
        result = PuzzleService.get_puzzle_detail(non_existent_id)
        
        assert result is None
    
    def test_get_puzzle_detail_inactive(self):
        """测试获取已禁用关卡详情"""
        puzzle = Puzzle.objects.create(
            title="禁用的残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=False,
        )
        
        result = PuzzleService.get_puzzle_detail(str(puzzle.id))
        
        assert result is None
    
    def test_verify_move_already_complete(self):
        """测试已完成关卡的走法验证"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        # 创建一个已完成的挑战
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            current_move_index=1,  # 已完成所有步骤
        )
        
        move_data = {"from": "a1", "to": "a4", "piece": "R"}
        is_correct, message = PuzzleService.verify_move(puzzle, attempt, move_data)
        
        assert is_correct is False
        assert "已完成" in message
    
    def test_get_hint_no_hint(self):
        """测试没有提示的情况"""
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            hint="",  # 空提示
        )
        
        hint = PuzzleService.get_hint(puzzle)
        
        assert hint is None
    
    def test_get_puzzle_detail_statistics(self):
        """测试关卡详情包含统计信息"""
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=3,
            total_attempts=100,
            total_completions=50,
        )
        
        result = PuzzleService.get_puzzle_detail(str(puzzle.id))
        
        assert result is not None
        assert result['total_attempts'] == 100
        assert result['total_completions'] == 50


@pytest.mark.django_db
class TestPuzzleAttemptServiceExtended:
    """PuzzleAttemptService 扩展测试"""
    
    def test_create_attempt_puzzle_not_found(self):
        """测试创建挑战时关卡不存在"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        import uuid
        non_existent_id = str(uuid.uuid4())
        
        attempt = PuzzleAttemptService.create_attempt(user, non_existent_id)
        
        assert attempt is None
    
    def test_create_attempt_puzzle_inactive(self):
        """测试创建挑战时关卡已禁用"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=False,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        
        assert attempt is None
    
    def test_create_attempt_existing_in_progress(self):
        """测试已存在进行中的挑战时返回现有挑战"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        # 创建一个进行中的挑战
        existing = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            status=PuzzleAttemptStatus.IN_PROGRESS,
            fen_current=puzzle.fen_initial,
        )
        
        # 再次创建挑战
        new_attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        
        assert new_attempt is not None
        assert new_attempt.id == existing.id
    
    def test_update_attempt_wrong_move(self):
        """测试更新挑战时走法错误"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        move_data = {"from": "a1", "to": "a5", "piece": "R"}  # 错误走法
        
        result = PuzzleAttemptService.update_attempt(attempt, move_data, is_correct=False)
        
        assert result['is_complete'] is False
        assert result['current_move_index'] == 0  # 索引未增加
        assert result['moves_used'] == 1  # 步数增加
        assert attempt.move_history[0]['correct'] is False
    
    def test_calculate_stars_boundary_3_stars(self):
        """测试 3 星级边界条件"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}] * 10,  # 10 步最优解
            difficulty=1,
        )
        
        # 12 步 = 10 * 1.2，刚好 3 星
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            moves_used=12,
        )
        
        stars = PuzzleAttemptService.calculate_stars(attempt)
        assert stars == 3
    
    def test_calculate_stars_boundary_2_stars(self):
        """测试 2 星级边界条件"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}] * 10,  # 10 步最优解
            difficulty=1,
        )
        
        # 13 步 > 10 * 1.2，但 <= 10 * 1.5，2 星
        attempt = PuzzleAttempt.objects.create(
            user=user,
            puzzle=puzzle,
            moves_used=13,
        )
        
        stars = PuzzleAttemptService.calculate_stars(attempt)
        assert stars == 2
        
        # 15 步 = 10 * 1.5，刚好 2 星
        attempt.moves_used = 15
        stars = PuzzleAttemptService.calculate_stars(attempt)
        assert stars == 2
    
    def test_calculate_points_different_difficulties(self):
        """测试不同难度的积分计算"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        # 难度 1
        puzzle1 = Puzzle.objects.create(
            title="难度 1 残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        attempt1 = PuzzleAttempt.objects.create(user=user, puzzle=puzzle1, moves_used=1)
        points1 = PuzzleAttemptService.calculate_points(attempt1, stars=3)
        
        # 难度 5
        puzzle5 = Puzzle.objects.create(
            title="难度 5 残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=5,
        )
        attempt5 = PuzzleAttempt.objects.create(user=user, puzzle=puzzle5, moves_used=1)
        points5 = PuzzleAttemptService.calculate_points(attempt5, stars=3)
        
        # 难度 10
        puzzle10 = Puzzle.objects.create(
            title="难度 10 残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=10,
        )
        attempt10 = PuzzleAttempt.objects.create(user=user, puzzle=puzzle10, moves_used=1)
        points10 = PuzzleAttemptService.calculate_points(attempt10, stars=3)
        
        # 难度越高积分越多
        assert points1 < points5 < points10
    
    def test_calculate_points_different_stars(self):
        """测试不同星级的积分计算"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=5,
        )
        
        attempt = PuzzleAttempt.objects.create(user=user, puzzle=puzzle, moves_used=1)
        
        points_1star = PuzzleAttemptService.calculate_points(attempt, stars=1)
        points_2star = PuzzleAttemptService.calculate_points(attempt, stars=2)
        points_3star = PuzzleAttemptService.calculate_points(attempt, stars=3)
        
        # 星级越高积分越多
        assert points_1star < points_2star < points_3star
    
    def test_abandon_attempt(self):
        """测试放弃挑战"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        
        PuzzleAttemptService.abandon_attempt(attempt)
        
        attempt.refresh_from_db()
        assert attempt.status == PuzzleAttemptStatus.ABANDONED
    
    def test_update_attempt_completes_puzzle_statistics(self):
        """测试完成挑战后更新关卡统计"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            total_attempts=0,
            total_completions=0,
        )
        
        attempt = PuzzleAttemptService.create_attempt(user, str(puzzle.id))
        move_data = {"from": "a1", "to": "a4", "piece": "R"}
        PuzzleAttemptService.update_attempt(attempt, move_data, is_correct=True)
        
        puzzle.refresh_from_db()
        assert puzzle.total_attempts == 1
        assert puzzle.total_completions == 1


@pytest.mark.django_db
class TestPuzzleProgressServiceExtended:
    """PuzzleProgressService 扩展测试"""
    
    def test_update_progress_calculates_all_stats(self):
        """测试更新进度时计算所有统计"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        # 创建不同难度的关卡并完成
        for diff in range(1, 6):
            puzzle = Puzzle.objects.create(
                title=f"难度{diff}残局",
                fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
                solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
                difficulty=diff,
            )
            attempt = PuzzleAttempt.objects.create(
                user=user,
                puzzle=puzzle,
                status=PuzzleAttemptStatus.SUCCESS,
                stars=3,
            )
        
        progress = PuzzleProgressService.update_progress(user)
        
        assert progress.total_completed == 5
        assert progress.max_difficulty_passed == 5
        assert progress.stars_3 == 5
        assert progress.total_stars == 15  # 5 * 3
    
    def test_get_leaderboard(self):
        """测试获取排行榜"""
        # 创建多个用户和进度
        for i in range(5):
            user = User.objects.create_user(username=f'user{i}', email=f'user{i}@example.com', password='password')
            progress = PuzzleProgress.objects.create(
                user=user,
                ranking_points=(i + 1) * 100,
                total_completed=i + 1,
            )
        
        leaderboard = PuzzleProgressService.get_leaderboard(limit=10)
        
        assert len(leaderboard) == 5
        # 按积分降序排列
        assert leaderboard[0]['ranking_points'] > leaderboard[1]['ranking_points']
        assert leaderboard[0]['rank'] == 1
    
    def test_get_leaderboard_limit(self):
        """测试排行榜数量限制"""
        # 创建 10 个用户
        for i in range(10):
            user = User.objects.create_user(username=f'user{i}', email=f'user{i}@example.com', password='password')
            PuzzleProgress.objects.create(
                user=user,
                ranking_points=i * 100,
                total_completed=i,
            )
        
        leaderboard = PuzzleProgressService.get_leaderboard(limit=5)
        
        assert len(leaderboard) == 5
    
    def test_add_ranking_points_multiple_times(self):
        """测试多次添加排名积分"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        PuzzleProgressService.add_ranking_points(user, 100)
        PuzzleProgressService.add_ranking_points(user, 50)
        PuzzleProgressService.add_ranking_points(user, 25)
        
        progress = PuzzleProgress.objects.get(user=user)
        assert progress.ranking_points == 175
    
    def test_get_user_statistics_with_no_attempts(self):
        """测试无挑战记录时的用户统计"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        stats = PuzzleProgressService.get_user_statistics(user)
        
        assert stats['total_completed'] == 0
        assert stats['total_attempts'] == 0
        assert stats['completion_rate'] == 0
    
    def test_get_user_statistics_with_attempts(self):
        """测试有挑战记录时的用户统计"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        
        # 创建 10 次挑战，5 次成功
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        for i in range(10):
            status = PuzzleAttemptStatus.SUCCESS if i < 5 else PuzzleAttemptStatus.FAILED
            PuzzleAttempt.objects.create(
                user=user,
                puzzle=puzzle,
                status=status,
            )
        
        # 更新进度后再获取统计
        PuzzleProgressService.update_progress(user)
        stats = PuzzleProgressService.get_user_statistics(user)
        
        assert stats['total_completed'] == 5
        assert stats['total_attempts'] == 10
        assert stats['completion_rate'] == 50.0
    
    def test_update_progress_with_mixed_star_ratings(self):
        """测试混合星级评定的进度更新"""
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
        )
        
        # 创建不同星级的完成记录
        for stars in [1, 1, 2, 2, 2, 3, 3, 3, 3]:
            PuzzleAttempt.objects.create(
                user=user,
                puzzle=puzzle,
                status=PuzzleAttemptStatus.SUCCESS,
                stars=stars,
            )
        
        progress = PuzzleProgressService.update_progress(user)
        
        assert progress.stars_1 == 2
        assert progress.stars_2 == 3
        assert progress.stars_3 == 4
        assert progress.total_stars == 2*1 + 3*2 + 4*3  # 20
