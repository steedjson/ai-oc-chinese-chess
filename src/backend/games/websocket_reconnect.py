"""
WebSocket 断线重连服务

提供断线检测、自动重连（指数退避）、重连状态管理和历史记录功能。

功能：
- 断线检测机制
- 自动重连逻辑（指数退避算法）
- 重连状态管理
- 重连历史记录
- 重连状态广播
"""
import asyncio
import logging
import time
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ReconnectState(Enum):
    """重连状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    RECONNECTED = "reconnected"
    FAILED = "failed"


@dataclass
class ReconnectRecord:
    """重连记录"""
    timestamp: str
    state: str
    attempt: int = 0
    delay_ms: int = 0
    reason: str = ""
    duration_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ConnectionStats:
    """连接统计信息"""
    total_connections: int = 0
    total_reconnects: int = 0
    successful_reconnects: int = 0
    failed_reconnects: int = 0
    last_disconnect_time: Optional[str] = None
    last_reconnect_time: Optional[str] = None
    current_streak: int = 0  # 当前连续重连成功次数
    max_streak: int = 0  # 最大连续重连成功次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class ReconnectManager:
    """
    重连管理器
    
    管理单个 WebSocket 连接的重连逻辑
    """
    
    # 重连配置
    INITIAL_DELAY_MS = 1000  # 初始延迟 1 秒
    MAX_DELAY_MS = 30000  # 最大延迟 30 秒
    MULTIPLIER = 2.0  # 指数退避乘数
    MAX_ATTEMPTS = 10  # 最大重连次数
    JITTER_MS = 500  # 随机抖动毫秒数
    
    def __init__(self, consumer: Any, game_id: str, user_id: str):
        """
        初始化重连管理器
        
        Args:
            consumer: WebSocket consumer 实例
            game_id: 游戏 ID
            user_id: 用户 ID
        """
        self.consumer = consumer
        self.game_id = game_id
        self.user_id = user_id
        
        self.state = ReconnectState.CONNECTED
        self.attempt = 0
        self.last_heartbeat = datetime.now(timezone.utc)
        self.reconnect_task: Optional[asyncio.Task] = None
        self.records: List[ReconnectRecord] = []
        self.stats = ConnectionStats()
        self._reconnect_start_time: Optional[float] = None
        
    def _get_timestamp(self) -> str:
        """获取 ISO 格式时间戳"""
        return datetime.now(timezone.utc).isoformat()
    
    def _calculate_delay(self) -> int:
        """
        计算重连延迟（指数退避 + 随机抖动）
        
        Returns:
            延迟毫秒数
        """
        import random
        
        # 指数退避
        delay = self.INITIAL_DELAY_MS * (self.MULTIPLIER ** self.attempt)
        
        # 限制最大延迟（包含抖动）
        max_delay_with_jitter = self.MAX_DELAY_MS + self.JITTER_MS
        delay = min(delay, max_delay_with_jitter)
        
        # 添加随机抖动（避免多个连接同时重连）
        jitter = random.randint(0, self.JITTER_MS)
        
        # 确保不超过绝对最大值
        return min(int(delay + jitter), self.MAX_DELAY_MS + self.JITTER_MS)
    
    async def start_reconnect(self) -> bool:
        """
        启动重连流程
        
        Returns:
            是否成功启动重连
        """
        if self.state == ReconnectState.RECONNECTING:
            logger.warning(f"Reconnect already in progress for user {self.user_id}")
            return False
        
        if self.attempt >= self.MAX_ATTEMPTS:
            logger.warning(f"Max reconnect attempts reached for user {self.user_id}")
            self.state = ReconnectState.FAILED
            self._record_reconnect(ReconnectState.FAILED.value, reason="Max attempts reached")
            return False
        
        self.state = ReconnectState.RECONNECTING
        self.attempt += 1
        self._reconnect_start_time = time.time()
        
        # 记录重连开始
        self._record_reconnect(ReconnectState.RECONNECTING.value, attempt=self.attempt)
        
        # 广播重连状态
        await self._broadcast_reconnect_status()
        
        # 启动重连任务
        self.reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        logger.info(f"Started reconnect attempt {self.attempt} for user {self.user_id} in game {self.game_id}")
        return True
    
    async def _reconnect_loop(self):
        """重连循环"""
        try:
            while self.state == ReconnectState.RECONNECTING and self.attempt <= self.MAX_ATTEMPTS:
                delay = self._calculate_delay()
                
                # 记录延迟信息
                if self.records:
                    self.records[-1].delay_ms = delay
                
                logger.info(
                    f"Waiting {delay}ms before reconnect attempt {self.attempt} "
                    f"for user {self.user_id}"
                )
                
                # 等待延迟
                await asyncio.sleep(delay / 1000.0)
                
                # 尝试重连
                success = await self._attempt_reconnect()
                
                if success:
                    self.state = ReconnectState.RECONNECTED
                    self.attempt = 0  # 重置尝试次数
                    
                    # 更新统计
                    self.stats.successful_reconnects += 1
                    self.stats.current_streak += 1
                    self.stats.max_streak = max(self.stats.max_streak, self.stats.current_streak)
                    self.stats.last_reconnect_time = self._get_timestamp()
                    
                    # 记录成功
                    duration = int((time.time() - self._reconnect_start_time) * 1000) if self._reconnect_start_time else 0
                    self._record_reconnect(
                        ReconnectState.RECONNECTED.value,
                        attempt=self.attempt,
                        duration_ms=duration
                    )
                    
                    # 广播重连成功
                    await self._broadcast_reconnect_status()
                    
                    logger.info(f"Successfully reconnected for user {self.user_id}")
                    return
                else:
                    logger.warning(
                        f"Reconnect attempt {self.attempt} failed for user {self.user_id}"
                    )
                    
                    # 更新统计
                    self.stats.failed_reconnects += 1
                    self.stats.current_streak = 0
                    
                    # 继续下一次尝试
                    if self.attempt < self.MAX_ATTEMPTS:
                        self.state = ReconnectState.RECONNECTING
                    else:
                        self.state = ReconnectState.FAILED
                        self._record_reconnect(ReconnectState.FAILED.value, reason="All attempts failed")
                        await self._broadcast_reconnect_status()
                        logger.error(f"All reconnect attempts failed for user {self.user_id}")
                        return
                        
        except asyncio.CancelledError:
            logger.info(f"Reconnect loop cancelled for user {self.user_id}")
            raise
        except Exception as e:
            logger.error(f"Error in reconnect loop for user {self.user_id}: {e}")
            self.state = ReconnectState.FAILED
            self._record_reconnect(ReconnectState.FAILED.value, reason=str(e))
            await self._broadcast_reconnect_status()
    
    async def _attempt_reconnect(self) -> bool:
        """
        尝试重连
        
        Returns:
            是否成功
        """
        try:
            # 调用 consumer 的重连方法
            if hasattr(self.consumer, '_reconnect_channel'):
                await self.consumer._reconnect_channel()
                return True
            return False
        except Exception as e:
            logger.error(f"Reconnect attempt failed for user {self.user_id}: {e}")
            return False
    
    async def _broadcast_reconnect_status(self):
        """广播重连状态"""
        try:
            status_data = {
                'type': 'RECONNECT_STATUS',
                'payload': {
                    'state': self.state.value,
                    'attempt': self.attempt,
                    'max_attempts': self.MAX_ATTEMPTS,
                    'next_delay_ms': self._calculate_delay() if self.state == ReconnectState.RECONNECTING else 0,
                    'stats': self.stats.to_dict()
                },
                'timestamp': self._get_timestamp()
            }
            
            # 发送给当前用户
            if hasattr(self.consumer, 'send') and self.consumer.channel_name:
                await self.consumer.send(text_data=json.dumps(status_data))
            
            # 广播给房间内其他用户
            if hasattr(self.consumer, 'channel_layer') and hasattr(self.consumer, 'room_group_name'):
                await self.consumer.channel_layer.group_send(
                    self.consumer.room_group_name,
                    {
                        'type': 'reconnect_status',
                        'data': {
                            'user_id': self.user_id,
                            'state': self.state.value,
                            'attempt': self.attempt
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error broadcasting reconnect status: {e}")
    
    def _record_reconnect(self, state: str, attempt: int = 0, delay_ms: int = 0, 
                          reason: str = "", duration_ms: int = 0):
        """记录重连事件"""
        record = ReconnectRecord(
            timestamp=self._get_timestamp(),
            state=state,
            attempt=attempt,
            delay_ms=delay_ms,
            reason=reason,
            duration_ms=duration_ms
        )
        self.records.append(record)
        
        # 限制历史记录数量
        if len(self.records) > 100:
            self.records = self.records[-100:]
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now(timezone.utc)
        
        # 如果之前是重连状态，现在心跳恢复，说明连接已恢复
        if self.state == ReconnectState.RECONNECTED:
            self.state = ReconnectState.CONNECTED
            self.stats.total_connections += 1
    
    def is_heartbeat_timeout(self, timeout_seconds: int = 90) -> bool:
        """
        检查心跳是否超时
        
        Args:
            timeout_seconds: 超时阈值（秒）
            
        Returns:
            是否超时
        """
        now = datetime.now(timezone.utc)
        delta = (now - self.last_heartbeat).total_seconds()
        return delta > timeout_seconds
    
    def get_reconnect_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取重连历史记录
        
        Args:
            limit: 返回记录数量
            
        Returns:
            重连记录列表
        """
        return [record.to_dict() for record in self.records[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        stats_dict = self.stats.to_dict()
        stats_dict['total_records'] = len(self.records)
        return stats_dict
    
    def cancel(self):
        """取消重连"""
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()
            logger.info(f"Cancelled reconnect for user {self.user_id}")
    
    def reset(self):
        """重置重连管理器"""
        self.cancel()
        self.state = ReconnectState.CONNECTED
        self.attempt = 0
        self._reconnect_start_time = None


class ReconnectService:
    """
    重连服务（单例）
    
    管理所有 WebSocket 连接的重连管理器
    """
    
    _instance: Optional['ReconnectService'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'ReconnectService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._managers: Dict[str, ReconnectManager] = {}  # key: "{game_id}:{user_id}"
        self._initialized = True
        logger.info("ReconnectService initialized")
    
    @classmethod
    async def get_instance(cls) -> 'ReconnectService':
        """获取单例实例"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def _make_key(self, game_id: str, user_id: str) -> str:
        """生成管理器键"""
        return f"{game_id}:{user_id}"
    
    def get_manager(self, game_id: str, user_id: str) -> Optional[ReconnectManager]:
        """
        获取重连管理器
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            重连管理器，不存在返回 None
        """
        key = self._make_key(game_id, user_id)
        return self._managers.get(key)
    
    def create_manager(self, consumer: Any, game_id: str, user_id: str) -> ReconnectManager:
        """
        创建重连管理器
        
        Args:
            consumer: WebSocket consumer 实例
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            新创建的重连管理器
        """
        key = self._make_key(game_id, user_id)
        
        # 如果已存在，先清理旧的
        if key in self._managers:
            old_manager = self._managers[key]
            old_manager.cancel()
        
        manager = ReconnectManager(consumer, game_id, user_id)
        self._managers[key] = manager
        manager.stats.total_connections = 1
        
        logger.info(f"Created reconnect manager for {key}")
        return manager
    
    def remove_manager(self, game_id: str, user_id: str):
        """
        移除重连管理器
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
        """
        key = self._make_key(game_id, user_id)
        if key in self._managers:
            manager = self._managers[key]
            manager.cancel()
            del self._managers[key]
            logger.info(f"Removed reconnect manager for {key}")
    
    async def start_reconnect(self, game_id: str, user_id: str) -> bool:
        """
        启动重连
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            是否成功启动
        """
        manager = self.get_manager(game_id, user_id)
        if not manager:
            logger.warning(f"No reconnect manager found for {game_id}:{user_id}")
            return False
        
        return await manager.start_reconnect()
    
    def update_heartbeat(self, game_id: str, user_id: str):
        """
        更新心跳
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
        """
        manager = self.get_manager(game_id, user_id)
        if manager:
            manager.update_heartbeat()
    
    def is_heartbeat_timeout(self, game_id: str, user_id: str, timeout_seconds: int = 90) -> bool:
        """
        检查心跳是否超时
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            timeout_seconds: 超时阈值
            
        Returns:
            是否超时
        """
        manager = self.get_manager(game_id, user_id)
        if not manager:
            return False
        
        return manager.is_heartbeat_timeout(timeout_seconds)
    
    def get_reconnect_history(self, game_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取重连历史
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            limit: 记录数量
            
        Returns:
            重连历史记录
        """
        manager = self.get_manager(game_id, user_id)
        if not manager:
            return []
        
        return manager.get_reconnect_history(limit)
    
    def get_stats(self, game_id: str, user_id: str) -> Dict[str, Any]:
        """
        获取连接统计
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            统计信息
        """
        manager = self.get_manager(game_id, user_id)
        if not manager:
            return {}
        
        return manager.get_stats()
    
    async def cleanup(self):
        """清理所有重连管理器"""
        logger.info(f"Cleaning up {len(self._managers)} reconnect managers")
        for key, manager in list(self._managers.items()):
            manager.cancel()
        self._managers.clear()


# 全局服务实例
reconnect_service: Optional[ReconnectService] = None


async def get_reconnect_service() -> ReconnectService:
    """获取重连服务实例"""
    global reconnect_service
    if reconnect_service is None:
        reconnect_service = await ReconnectService.get_instance()
    return reconnect_service
