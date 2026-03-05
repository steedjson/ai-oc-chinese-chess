"""
AI Engine 单元测试 - 引擎池管理测试

测试引擎池的创建、获取、释放和健康检查
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from ai_engine.engine_pool import EnginePool


class TestEnginePool:
    """引擎池管理测试"""
    
    @patch('ai_engine.engine_pool.StockfishService')
    def test_pool_initialization(self, mock_service_class):
        """测试引擎池初始化"""
        pool = EnginePool(pool_size=4)
        
        assert pool.pool_size == 4
        assert len(pool.engines) == 4
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_engine(self, mock_service_class):
        """测试获取引擎"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        
        assert engine is not None
        assert pool.available.qsize() == 3
        assert len(pool.in_use) == 1
        engine.set_difficulty.assert_called_with(5)
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_release_engine(self, mock_service_class):
        """测试释放引擎"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        pool.release(engine)
        
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_multiple_engines(self, mock_service_class):
        """测试获取多个引擎"""
        pool = EnginePool(pool_size=4)
        
        engines = []
        for i in range(4):
            engine = await pool.acquire(difficulty=5)
            engines.append(engine)
        
        assert len(engines) == 4
        assert pool.available.qsize() == 0
        assert len(pool.in_use) == 4
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_when_pool_empty(self, mock_service_class):
        """测试引擎池为空时获取引擎（应该等待）"""
        pool = EnginePool(pool_size=2)
        
        # 获取所有引擎
        engine1 = await pool.acquire(difficulty=5)
        engine2 = await pool.acquire(difficulty=5)
        
        assert pool.available.qsize() == 0
        
        # 释放一个引擎
        pool.release(engine1)
        
        # 现在应该可以获取
        engine3 = await pool.acquire(difficulty=5)
        assert engine3 is not None
        assert pool.available.qsize() == 0
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_release_nonexistent_engine(self, mock_service_class):
        """测试释放不存在的引擎"""
        pool = EnginePool(pool_size=4)
        mock_engine = Mock()
        
        # 不应该抛出异常
        pool.release(mock_engine)
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check(self, mock_service_class):
        """测试健康检查"""
        pool = EnginePool(pool_size=4)
        
        # Mock 引擎的 get_best_move 方法
        for engine in pool.engines.values():
            engine.get_best_move = Mock(return_value="e2e4")
        
        await pool.health_check()
        
        # 所有引擎都应该被检查
        for engine in pool.engines.values():
            engine.get_best_move.assert_called()
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check_restart_failed_engine(self, mock_service_class):
        """测试健康检查重启失败的引擎"""
        pool = EnginePool(pool_size=4)
        
        # Mock 一个引擎失败
        failed_engine = pool.engines[0]
        failed_engine.get_best_move = Mock(side_effect=Exception("Engine crashed"))
        
        await pool.health_check()
        
        # 应该尝试重启失败的引擎
        mock_service_class.assert_called()
    
    @patch('ai_engine.engine_pool.StockfishService')
    def test_default_pool_size(self, mock_service_class):
        """测试默认引擎池大小"""
        pool = EnginePool()
        
        assert pool.pool_size == 4
        assert len(pool.engines) == 4
    
    @patch('ai_engine.engine_pool.StockfishService')
    def test_custom_pool_size(self, mock_service_class):
        """测试自定义引擎池大小"""
        pool = EnginePool(pool_size=8)
        
        assert pool.pool_size == 8
        assert len(pool.engines) == 8
    
    @patch('ai_engine.engine_pool.StockfishService')
    @pytest.mark.asyncio
    async def test_engine_pool_concurrent_access(self, mock_service_class):
        """测试引擎池并发访问"""
        pool = EnginePool(pool_size=4)
        
        async def acquire_and_release():
            engine = await pool.acquire(difficulty=5)
            await asyncio.sleep(0.01)  # 模拟使用
            pool.release(engine)
        
        # 并发执行 10 次获取和释放
        tasks = [acquire_and_release() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # 所有引擎都应该被释放回池中
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0


class TestEnginePoolSingleton:
    """引擎池单例模式测试"""
    
    def test_global_engine_pool_instance(self):
        """测试全局引擎池实例存在"""
        from ai_engine.engine_pool import engine_pool
        
        assert engine_pool is not None
        assert isinstance(engine_pool, EnginePool)
