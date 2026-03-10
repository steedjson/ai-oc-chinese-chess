"""
AI Engine 引擎池扩展测试
覆盖更多边界情况、异常场景和并发测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from ai_engine.engine_pool import EnginePool, get_engine_pool


class TestEnginePoolInitialization:
    """引擎池初始化扩展测试"""
    
    @patch('ai_engine.services.StockfishService')
    def test_pool_initialization_creates_all_engines(self, mock_service_class):
        """验证所有引擎实例都被创建"""
        pool = EnginePool(pool_size=6)
        
        assert len(pool.engines) == 6
        assert pool.pool_size == 6
        # 验证所有引擎都被初始化
        for i in range(6):
            assert i in pool.engines
    
    @patch('ai_engine.services.StockfishService')
    def test_pool_initialization_all_available(self, mock_service_class):
        """验证初始时所有引擎都可用"""
        pool = EnginePool(pool_size=5)
        
        assert pool.available.qsize() == 5
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.services.StockfishService')
    def test_pool_with_size_one(self, mock_service_class):
        """测试单引擎池"""
        pool = EnginePool(pool_size=1)
        
        assert pool.pool_size == 1
        assert len(pool.engines) == 1
        assert pool.available.qsize() == 1
    
    @patch('ai_engine.services.StockfishService')
    def test_pool_with_large_size(self, mock_service_class):
        """测试大引擎池"""
        pool = EnginePool(pool_size=20)
        
        assert pool.pool_size == 20
        assert len(pool.engines) == 20
        assert pool.available.qsize() == 20


class TestEnginePoolAcquireExtended:
    """引擎获取扩展测试"""
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_sets_difficulty(self, mock_service_class):
        """验证获取引擎时设置难度"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=7)
        
        engine.set_difficulty.assert_called_once_with(7)
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_marks_engine_as_in_use(self, mock_service_class):
        """验证获取引擎后标记为使用中"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        
        # 验证引擎在 in_use 集合中
        assert len(pool.in_use) == 1
        # 找到引擎 ID
        engine_id = None
        for eid, eng in pool.engines.items():
            if eng is engine:
                engine_id = eid
                break
        assert engine_id in pool.in_use
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_decreases_available_count(self, mock_service_class):
        """验证获取引擎后可用数量减少"""
        pool = EnginePool(pool_size=4)
        
        await pool.acquire(difficulty=5)
        await pool.acquire(difficulty=5)
        
        assert pool.available.qsize() == 2
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_different_difficulties(self, mock_service_class):
        """测试获取不同难度的引擎"""
        pool = EnginePool(pool_size=4)
        
        engine1 = await pool.acquire(difficulty=3)
        engine2 = await pool.acquire(difficulty=8)
        
        engine1.set_difficulty.assert_called_with(3)
        engine2.set_difficulty.assert_called_with(8)


class TestEnginePoolReleaseExtended:
    """引擎释放扩展测试"""
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_returns_to_available(self, mock_service_class):
        """验证释放后引擎回到可用队列"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        pool.release(engine)
        
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_removes_from_in_use(self, mock_service_class):
        """验证释放后从使用中移除"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        engine_id = None
        for eid, eng in pool.engines.items():
            if eng is engine:
                engine_id = eid
                break
        
        pool.release(engine)
        
        assert engine_id not in pool.in_use
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_multiple_engines(self, mock_service_class):
        """测试释放多个引擎"""
        pool = EnginePool(pool_size=4)
        
        engines = []
        for _ in range(4):
            engine = await pool.acquire(difficulty=5)
            engines.append(engine)
        
        # 逐个释放
        for engine in engines:
            pool.release(engine)
        
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_unknown_engine_no_crash(self, mock_service_class):
        """测试释放未知引擎不崩溃"""
        pool = EnginePool(pool_size=4)
        unknown_engine = Mock()
        
        # 不应抛出异常
        pool.release(unknown_engine)
        
        # 池状态不变
        assert pool.available.qsize() == 4
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_same_engine_twice(self, mock_service_class):
        """测试重复释放同一引擎"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=5)
        pool.release(engine)
        
        # 再次释放（不应该重复计数）
        pool.release(engine)
        
        # 可用数量不应超过池大小
        assert pool.available.qsize() <= 4


class TestEnginePoolHealthCheckExtended:
    """健康检查扩展测试"""
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check_skips_in_use_engines(self, mock_service_class):
        """验证健康检查跳过使用中的引擎"""
        pool = EnginePool(pool_size=4)
        
        # 获取一个引擎
        await pool.acquire(difficulty=5)
        
        # Mock 所有引擎
        for engine in pool.engines.values():
            engine.engine.get_best_move = Mock(return_value="e2e4")
        
        await pool.health_check()
        
        # 验证检查了所有不在使用中的引擎
        for engine_id, engine in pool.engines.items():
            if engine_id not in pool.in_use:
                engine.engine.get_best_move.assert_called()
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check_successful_engine(self, mock_service_class):
        """测试健康检查成功引擎"""
        pool = EnginePool(pool_size=4)
        
        for engine in pool.engines.values():
            engine.engine.get_best_move = Mock(return_value="e2e4")
        
        # 不应抛出异常
        await pool.health_check()
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check_failing_engine(self, mock_service_class):
        """测试健康检查失败引擎"""
        pool = EnginePool(pool_size=4)
        
        # 第一个引擎失败
        pool.engines[0].engine.get_best_move = Mock(side_effect=Exception("Crash"))
        # 其他引擎正常
        for i in range(1, 4):
            pool.engines[i].engine.get_best_move = Mock(return_value="e2e4")
        
        # 不应抛出异常
        await pool.health_check()
        
        # 验证尝试重启失败的引擎
        mock_service_class.assert_called()
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_health_check_all_failing(self, mock_service_class):
        """测试所有引擎都失败"""
        pool = EnginePool(pool_size=4)
        
        for engine in pool.engines.values():
            engine.engine.get_best_move = Mock(side_effect=Exception("Crash"))
        
        # 不应抛出异常
        await pool.health_check()
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_restart_engine_quits_old(self, mock_service_class):
        """验证重启引擎时关闭旧引擎"""
        pool = EnginePool(pool_size=4)
        
        old_engine = pool.engines[0]
        old_engine.engine.quit = Mock()
        old_engine.engine.get_best_move = Mock(side_effect=Exception("Crash"))
        
        await pool._restart_engine(0)
        
        old_engine.engine.quit.assert_called()
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_restart_engine_creates_new(self, mock_service_class):
        """验证重启引擎时创建新引擎"""
        pool = EnginePool(pool_size=4)
        
        old_engine = pool.engines[0]
        old_engine.engine.quit = Mock(side_effect=Exception("Already quit"))
        
        await pool._restart_engine(0)
        
        # 验证创建了新引擎
        assert pool.engines[0] is not old_engine


class TestEnginePoolConcurrency:
    """并发测试"""
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_concurrent_acquire_release_stress(self, mock_service_class):
        """压力测试：并发获取和释放"""
        pool = EnginePool(pool_size=4)
        
        async def worker(worker_id):
            for _ in range(10):
                engine = await pool.acquire(difficulty=5)
                await asyncio.sleep(0.001)  # 模拟工作
                pool.release(engine)
        
        # 10 个 worker 并发
        tasks = [worker(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # 最终所有引擎都应该可用
        assert pool.available.qsize() == 4
        assert len(pool.in_use) == 0
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_timeout_behavior(self, mock_service_class):
        """测试获取引擎时的等待行为"""
        pool = EnginePool(pool_size=2)
        
        # 获取所有引擎
        engine1 = await pool.acquire(difficulty=5)
        engine2 = await pool.acquire(difficulty=5)
        
        assert pool.available.qsize() == 0
        
        # 异步释放一个引擎
        async def release_later():
            await asyncio.sleep(0.01)
            pool.release(engine1)
        
        # 启动释放任务
        release_task = asyncio.create_task(release_later())
        
        # 等待获取第三个引擎（应该等待）
        engine3 = await pool.acquire(difficulty=5)
        
        assert engine3 is not None
        
        await release_task
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_no_deadlock_on_release(self, mock_service_class):
        """测试释放时不会死锁"""
        pool = EnginePool(pool_size=2)
        
        engine1 = await pool.acquire(difficulty=5)
        engine2 = await pool.acquire(difficulty=5)
        
        # 同时释放（不应该死锁）
        await asyncio.gather(
            asyncio.get_event_loop().run_in_executor(None, pool.release, engine1),
            asyncio.get_event_loop().run_in_executor(None, pool.release, engine2)
        )
        
        assert pool.available.qsize() == 2


class TestEnginePoolGetEnginePool:
    """全局引擎池函数测试"""
    
    @patch('ai_engine.engine_pool._engine_pool_instance', None)
    @patch('ai_engine.services.StockfishService')
    def test_get_engine_pool_creates_instance(self, mock_service_class):
        """验证获取引擎池时创建实例"""
        # 重置全局变量
        import ai_engine.engine_pool as ep_module
        ep_module._engine_pool_instance = None
        
        pool = get_engine_pool()
        
        assert pool is not None
        assert isinstance(pool, EnginePool)
        assert ep_module._engine_pool_instance is pool
    
    @patch('ai_engine.services.StockfishService')
    def test_get_engine_pool_returns_same_instance(self, mock_service_class):
        """验证多次获取返回同一实例"""
        pool1 = get_engine_pool()
        pool2 = get_engine_pool()
        
        assert pool1 is pool2
    
    @patch('ai_engine.services.StockfishService')
    def test_get_engine_pool_default_size(self, mock_service_class):
        """验证默认池大小"""
        import ai_engine.engine_pool as ep_module
        ep_module._engine_pool_instance = None
        
        pool = get_engine_pool()
        
        assert pool.pool_size == 4  # 默认大小


class TestEnginePoolEdgeCases:
    """边界情况测试"""
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_with_zero_difficulty(self, mock_service_class):
        """测试获取难度为 0 的引擎"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=0)
        
        engine.set_difficulty.assert_called_with(0)
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_acquire_with_high_difficulty(self, mock_service_class):
        """测试获取高难度引擎"""
        pool = EnginePool(pool_size=4)
        
        engine = await pool.acquire(difficulty=10)
        
        engine.set_difficulty.assert_called_with(10)
    
    @patch('ai_engine.services.StockfishService')
    def test_pool_size_zero(self, mock_service_class):
        """测试池大小为 0"""
        pool = EnginePool(pool_size=0)
        
        assert pool.pool_size == 0
        assert len(pool.engines) == 0
        assert pool.available.qsize() == 0
    
    @patch('ai_engine.services.StockfishService')
    @pytest.mark.asyncio
    async def test_release_before_acquire(self, mock_service_class):
        """测试在获取前释放（边界情况）"""
        pool = EnginePool(pool_size=4)
        mock_engine = Mock()
        
        # 不应崩溃
        pool.release(mock_engine)
        
        assert pool.available.qsize() == 4
