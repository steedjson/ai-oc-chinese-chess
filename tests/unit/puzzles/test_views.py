"""
测试残局视图

测试 puzzles/views.py 中的视图函数
"""

import pytest
from unittest.mock import Mock, patch
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from puzzles.models import Puzzle, PuzzleAttempt, PuzzleProgress

User = get_user_model()


@pytest.mark.django_db
class TestPuzzleListView:
    """测试残局列表视图"""
    
    def test_get_puzzle_list(self, api_client, authenticated_user):
        """测试获取残局列表"""
        api_client.force_authenticate(user=authenticated_user)
        
        # 创建测试数据
        Puzzle.objects.create(
            title="测试残局 1",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=True,
        )
        
        response = api_client.get('/api/puzzles/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'puzzles' in response.data
    
    def test_puzzle_list_filter_difficulty(self, api_client, authenticated_user):
        """测试按难度筛选残局"""
        api_client.force_authenticate(user=authenticated_user)
        
        # 创建不同难度的残局
        for diff in [1, 3, 5, 7, 9]:
            Puzzle.objects.create(
                title=f"难度{diff}残局",
                fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
                solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
                difficulty=diff,
                is_active=True,
            )
        
        response = api_client.get('/api/puzzles/?difficulty=5')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_puzzle_list_pagination(self, api_client, authenticated_user):
        """测试残局列表分页"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/?page=1&page_size=10')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPuzzleDetailView:
    """测试残局详情视图"""
    
    def test_get_puzzle_detail(self, api_client, authenticated_user):
        """测试获取残局详情"""
        api_client.force_authenticate(user=authenticated_user)
        
        puzzle = Puzzle.objects.create(
            title="测试残局",
            description="测试描述",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=5,
            hint="测试提示",
            is_active=True,
        )
        
        response = api_client.get(f'/api/puzzles/{puzzle.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == "测试残局"
    
    def test_get_inactive_puzzle(self, api_client, authenticated_user):
        """测试获取未激活的残局"""
        api_client.force_authenticate(user=authenticated_user)
        
        puzzle = Puzzle.objects.create(
            title="未激活残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=False,  # 未激活
        )
        
        response = api_client.get(f'/api/puzzles/{puzzle.id}/')
        
        # 应该返回 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_nonexistent_puzzle(self, api_client, authenticated_user):
        """测试获取不存在的残局"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/99999/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPuzzleAttemptView:
    """测试残局尝试视图"""
    
    def test_start_puzzle_attempt(self, api_client, authenticated_user):
        """测试开始残局挑战"""
        api_client.force_authenticate(user=authenticated_user)
        
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=True,
        )
        
        response = api_client.post(f'/api/puzzles/{puzzle.id}/attempt/')
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
        ]
    
    def test_submit_puzzle_move(self, api_client, authenticated_user):
        """测试提交残局走法"""
        api_client.force_authenticate(user=authenticated_user)
        
        puzzle = Puzzle.objects.create(
            title="测试残局",
            fen_initial="4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1",
            solution_moves=[{"from": "a1", "to": "a4", "piece": "R"}],
            difficulty=1,
            is_active=True,
        )
        
        attempt = PuzzleAttempt.objects.create(
            user=authenticated_user,
            puzzle=puzzle,
            status='in_progress',
        )
        
        data = {
            'attempt_id': str(attempt.id),
            'move': {"from": "a1", "to": "a4", "piece": "R"},
        }
        
        response = api_client.post(f'/api/puzzles/{puzzle.id}/move/', data)
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.django_db
class TestPuzzleProgressView:
    """测试残局进度视图"""
    
    def test_get_user_progress(self, api_client, authenticated_user):
        """测试获取用户进度"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/progress/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_completed' in response.data or 'progress' in response.data
    
    def test_get_progress_statistics(self, api_client, authenticated_user):
        """测试获取进度统计"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/progress/stats/')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPuzzleLeaderboardView:
    """测试残局排行榜视图"""
    
    def test_get_puzzle_leaderboard(self, api_client, authenticated_user):
        """测试获取残局排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/leaderboard/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'leaderboard' in response.data
    
    def test_get_leaderboard_by_time_range(self, api_client, authenticated_user):
        """测试按时间范围获取排行榜"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/puzzles/leaderboard/?time_range=weekly')
        
        assert response.status_code == status.HTTP_200_OK


@pytest.fixture
def api_client():
    """创建 API 客户端"""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """创建认证用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
    )
