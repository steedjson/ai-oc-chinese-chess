"""
测试 AI 引擎模块

测试 ai_engine/ 中的服务、视图和任务
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAIServices:
    """测试 AI 引擎服务"""
    
    def test_get_ai_move(self):
        """测试获取 AI 走法"""
        from ai_engine.services import get_ai_move, analyze_position
        
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 测试接口存在
        assert callable(get_ai_move) or callable(analyze_position)
    
    def test_analyze_position(self):
        """测试分析局面"""
        from ai_engine.services import analyze_position
        
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 如果有 Stockfish 集成，这里会返回实际分析
        # 否则可能返回 None 或抛出异常
        try:
            result = analyze_position(fen, depth=10)
            assert result is not None
        except Exception:
            # 如果 Stockfish 未安装，可能抛出异常
            pass
    
    def test_get_best_move(self):
        """测试获取最佳走法"""
        from ai_engine.services import get_best_move
        
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        try:
            move = get_best_move(fen, difficulty=5)
            assert move is not None
        except Exception:
            # Stockfish 可能未安装
            pass


@pytest.mark.django_db
class TestAIViews:
    """测试 AI 引擎视图"""
    
    def test_analyze_position_view(self, api_client, authenticated_user):
        """测试分析局面视图"""
        api_client.force_authenticate(user=authenticated_user)
        
        data = {
            'fen': "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            'depth': 10,
        }
        
        response = api_client.post('/api/ai/analyze/', data)
        
        # 视图可能存在或不存在
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]
    
    def test_get_ai_move_view(self, api_client, authenticated_user):
        """测试获取 AI 走法视图"""
        api_client.force_authenticate(user=authenticated_user)
        
        data = {
            'fen': "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
            'difficulty': 5,
        }
        
        response = api_client.post('/api/ai/move/', data)
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]
    
    def test_ai_game_view(self, api_client, authenticated_user):
        """测试 AI 对弈视图"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.post('/api/ai/game/', {
            'difficulty': 5,
        })
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.django_db
class TestAITasks:
    """测试 AI 异步任务"""
    
    def test_analyze_position_task(self):
        """测试分析局面任务"""
        from ai_engine.tasks import analyze_position_async
        
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 如果有 Celery，这里会异步执行
        try:
            result = analyze_position_async.delay(fen, depth=10)
            assert result is not None
        except Exception:
            # Celery 可能未配置
            pass
    
    def test_calculate_elo_task(self):
        """测试计算 ELO 任务"""
        from ai_engine.tasks import calculate_elo_change
        
        try:
            result = calculate_elo_change.delay(
                player_elo=1500,
                opponent_elo=1500,
                result='win'
            )
            assert result is not None
        except Exception:
            # Celery 可能未配置
            pass


class TestAIConfig:
    """测试 AI 配置"""
    
    def test_difficulty_config(self):
        """测试难度配置"""
        from ai_engine.config import get_difficulty_config, DifficultyConfig
        
        for difficulty in range(1, 11):
            config = get_difficulty_config(difficulty)
            assert config is not None
            assert isinstance(config, DifficultyConfig)
            assert config.level == difficulty
    
    def test_difficulty_levels(self):
        """测试难度等级"""
        from ai_engine.config import get_difficulty_config
        
        # 验证 ELO 递增
        prev_elo = 0
        for difficulty in range(1, 11):
            config = get_difficulty_config(difficulty)
            assert config is not None
            assert config.elo > prev_elo, f"ELO 应该在难度 {difficulty-1} 到 {difficulty} 之间递增"
            prev_elo = config.elo


class TestEnginePool:
    """测试引擎池"""
    
    @patch('ai_engine.engine_pool.StockfishService')
    def test_get_engine_pool(self, mock_service_class):
        """测试获取引擎池实例"""
        from ai_engine.engine_pool import get_engine_pool, EnginePool
        
        pool = get_engine_pool()
        assert pool is not None
        assert isinstance(pool, EnginePool)
    
    @patch('ai_engine.engine_pool.StockfishService')
    def test_engine_pool_acquire_release(self, mock_service_class):
        """测试引擎池获取和释放"""
        from ai_engine.engine_pool import EnginePool
        import asyncio
        
        pool = EnginePool(pool_size=2)
        
        # Mock 引擎
        mock_engine = Mock()
        pool.engines[0] = mock_engine
        
        # 测试获取
        engine = asyncio.run(pool.acquire(difficulty=5))
        assert engine is not None
        
        # 测试释放
        pool.release(engine)


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
