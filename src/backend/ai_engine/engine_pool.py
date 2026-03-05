"""
AI Engine 引擎池管理模块

实现 Stockfish 引擎池，支持多实例并发
"""
import asyncio
from typing import Dict, Optional
from django.conf import settings

from .services import StockfishService


class EnginePool:
    """
    Stockfish 引擎池
    
    管理多个 Stockfish 引擎实例，支持并发获取和释放
    """
    
    def __init__(self, pool_size: int = 4):
        """
        初始化引擎池
        
        Args:
            pool_size: 引擎实例数量，默认为 4
        """
        self.pool_size = pool_size
        self.engines: Dict[int, StockfishService] = {}
        self.available: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self.in_use: set = set()
        
        # 初始化引擎实例
        for i in range(pool_size):
            engine = StockfishService(difficulty=5)  # 默认难度
            self.engines[i] = engine
        
        # 所有引擎初始可用
        for i in range(pool_size):
            self.available.put_nowait(i)
    
    async def acquire(self, difficulty: int = 5) -> StockfishService:
        """
        获取可用引擎
        
        Args:
            difficulty: 难度等级
        
        Returns:
            StockfishService: 引擎实例
        """
        # 等待可用引擎
        engine_id = await self.available.get()
        self.in_use.add(engine_id)
        
        # 设置难度
        engine = self.engines[engine_id]
        engine.set_difficulty(difficulty)
        
        return engine
    
    def release(self, engine: StockfishService):
        """
        释放引擎回池
        
        Args:
            engine: 引擎实例
        """
        # 找到引擎 ID
        for engine_id, eng in self.engines.items():
            if eng is engine:
                self.in_use.discard(engine_id)
                self.available.put_nowait(engine_id)
                break
    
    async def health_check(self):
        """健康检查，重启异常引擎"""
        for engine_id, engine in self.engines.items():
            if engine_id in self.in_use:
                continue
            
            try:
                # 简单测试
                engine.engine.get_best_move(time=100)
            except Exception as e:
                # 重启引擎
                await self._restart_engine(engine_id)
    
    async def _restart_engine(self, engine_id: int):
        """
        重启引擎实例
        
        Args:
            engine_id: 引擎 ID
        """
        try:
            self.engines[engine_id].engine.quit()
        except:
            pass
        
        self.engines[engine_id] = StockfishService(difficulty=5)


# 全局引擎池实例（延迟初始化）
_engine_pool_instance: Optional[EnginePool] = None


def get_engine_pool() -> EnginePool:
    """
    获取全局引擎池实例（懒加载）
    
    Returns:
        EnginePool: 引擎池实例
    """
    global _engine_pool_instance
    if _engine_pool_instance is None:
        _engine_pool_instance = EnginePool(pool_size=getattr(settings, 'AI_ENGINE_POOL_SIZE', 4))
    return _engine_pool_instance


# 为了兼容性保留 engine_pool 引用（懒加载）
engine_pool = None  # 使用时调用 get_engine_pool()
