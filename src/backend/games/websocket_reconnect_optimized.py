"""
WebSocket 断线重连优化服务

提供断线检测、自动重连（指数退避）、重连状态管理和历史记录功能。

优化内容：
1. 断线检测机制（心跳监测）
   - 可配置的心跳超时阈值
   - 心跳追踪和更新
   - 连接健康状态检查

2. 自动重连逻辑（指数退避）
   - 指数退避算法
   - 随机抖动避免并发重连
   - 最大重连次数限制
   - 可配置的重连参数

3. 重连状态提示
   - 实时状态广播
   - 详细的状态信息
   - 连接统计信息

4. 重连历史记录
   - 完整的重连记录
   - 限制历史记录数量
   - 支持查询和导出

5. 连接统计
   - 总连接数统计
   - 重连成功/失败统计
   - 连续成功次数统计

使用示例：
    # 在 Consumer 中使用
    class GameConsumer(BaseConsumer):
        async def connect(self):
            await super().connect()
            
            # 创建重连管理器
            self.reconnect_manager = ReconnectManager(
                self, 
                game_id=self.game_id, 
                user_id=self.user_id
            )
        
        async def disconnect(self, close_code):
            # 检测断线并启动重连
            if close_code != 1000:  # 非正常断开
                await self.reconnect_manager.start_reconnect()
            
            # 更新心跳
            self.reconnect_manager.update_heartbeat()
        
        async def receive(self, text_data):
            # 收到消息时更新心跳
            self.reconnect_manager.update_heartbeat()
            
            # 检查心跳是否超时
            if self.reconnect_manager.is_heartbeat_timeout(90):
                logger.warning("Heartbeat timeout detected")
                await self.reconnect_manager.start_reconnect()
"""
import asyncio
import logging
import time
import random
from typing import Dict, Optional, List, Any, Callable, Awaitable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ReconnectState(Enum):
    """
    重连状态枚举
    
    状态流转:
        CONNECTED -> DISCONNECTED -> RECONNECTING -> RECONNECTED -> CONNECTED
                                        |
                                        v
                                      FAILED
    """
    CONNECTED = "connected"          # 已连接
    DISCONNECTED = "disconnected"    # 已断开
    RECONNECTING = "reconnecting"    # 重连中
    RECONNECTED = "reconnected"      # 重连成功
    FAILED = "failed"                # 重连失败


@dataclass
class ReconnectRecord:
    """
    重连记录
    
    记录每次重连的详细信息，用于分析和调试
    """
    timestamp: str                              # 时间戳 (ISO 格式)
    state: str                                  # 重连状态
    attempt: int = 0                           # 重连尝试次数
    delay_ms: int = 0                          # 延迟时间 (毫秒)
    reason: str = ""                           # 重连原因
    duration_ms: int = 0                       # 重连耗时 (毫秒)
    user_id: str = ""                          # 用户 ID
    game_id: str = ""                          # 游戏 ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReconnectRecord':
        """从字典创建"""
        return cls(**data)


@dataclass
class ConnectionStats:
    """
    连接统计信息
    
    提供连接和重连的详细统计数据
    """
    total_connections: int = 0                 # 总连接次数
    total_reconnects: int = 0                  # 总重连次数
    successful_reconnects: int = 0             # 成功重连次数
    failed_reconnects: int = 0                 # 失败重连次数
    last_disconnect_time: Optional[str] = None # 最后断开时间
    last_reconnect_time: Optional[str] = None  # 最后重连时间
    current_streak: int = 0                    # 当前连续成功次数
    max_streak: int = 0                        # 最大连续成功次数
    avg_reconnect_time_ms: float = 0.0         # 平均重连耗时 (毫秒)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionStats':
        """从字典创建"""
        return cls(**data)


@dataclass
class ReconnectConfig:
    """
    重连配置
    
    可自定义重连行为参数
    """
    initial_delay_ms: int = 1000       # 初始延迟 1 秒
    max_delay_ms: int = 30000          # 最大延迟 30 秒
    multiplier: float = 2.0            # 指数退避乘数
    max_attempts: int = 10             # 最大重连次数
    jitter_ms: int = 500               # 随机抖动毫秒数
    heartbeat_timeout_seconds: int = 90  # 心跳超时阈值 (秒)
    max_history_size: int = 100        # 最大历史记录数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class ReconnectManager:
    """
    重连管理器
    
    管理单个 WebSocket 连接的重连逻辑
    
    功能:
    - 断线检测（心跳监测）
    - 自动重连（指数退避）
    - 重连状态管理
    - 重连历史记录
    - 连接统计
    
    使用示例:
        manager = ReconnectManager(
            consumer=websocket_consumer,
            game_id="game-123",
            user_id="user-456"
        )
        
        # 更新心跳
        manager.update_heartbeat()
        
        # 检查心跳超时
        if manager.is_heartbeat_timeout(90):
            await manager.start_reconnect()
        
        # 获取重连历史
        history = manager.get_reconnect_history(limit=10)
        
        # 获取统计信息
        stats = manager.get_stats()
    """
    
    def __init__(
        self, 
        consumer: Any, 
        game_id: str, 
        user_id: str,
        config: Optional[ReconnectConfig] = None
    ):
        """
        初始化重连管理器
        
        Args:
            consumer: WebSocket consumer 实例
            game_id: 游戏 ID
            user_id: 用户 ID
            config: 重连配置，使用默认配置如果未提供
        """
        self.consumer = consumer
        self.game_id = game_id
        self.user_id = user_id
        self.config = config or ReconnectConfig()
        
        self.state = ReconnectState.CONNECTED
        self.attempt = 0
        self.last_heartbeat = datetime.now(timezone.utc)
        self.reconnect_task: Optional[asyncio.Task] = None
        self.records: List[ReconnectRecord] = []
        self.stats = ConnectionStats()
        self._reconnect_start_time: Optional[float] = None
        self._reconnect_times: List[float] = []  # 用于计算平均重连时间
        
        # 回调函数
        self._on_state_change: Optional[Callable[[ReconnectState], Awaitable[None]]] = None
        self._on_reconnect_success: Optional[Callable[[], Awaitable[None]]] = None
        self._on_reconnect_failure: Optional[Callable[[], Awaitable[None]]] = None
    
    def _get_timestamp(self) -> str:
        """获取 ISO 格式时间戳"""
        return datetime.now(timezone.utc).isoformat()
    
    def _calculate_delay(self) -> int:
        """
        计算重连延迟（指数退避 + 随机抖动）
        
        算法:
            delay = min(
                initial_delay * (multiplier ^ attempt) + jitter,
                max_delay + jitter
            )
        
        Returns:
            延迟毫秒数
        """
        # 指数退避
        delay = self.config.initial_delay_ms * (self.config.multiplier ** self.attempt)
        
        # 限制最大延迟（包含抖动）
        max_delay_with_jitter = self.config.max_delay_ms + self.config.jitter_ms
        delay = min(delay, max_delay_with_jitter)
        
        # 添加随机抖动（避免多个连接同时重连）
        jitter = random.randint(0, self.config.jitter_ms)
        
        # 确保不超过绝对最大值
        return min(int(delay + jitter), self.config.max_delay_ms + self.config.jitter_ms)
    
    def set_state_change_callback(self, callback: Callable[[ReconnectState], Awaitable[None]]):
        """
        设置状态变化回调
        
        Args:
            callback: 状态变化时调用的异步函数
        """
        self._on_state_change = callback
    
    def set_reconnect_success_callback(self, callback: Callable[[], Awaitable[None]]):
        """
        设置重连成功回调
        
        Args:
            callback: 重连成功时调用的异步函数
        """
        self._on_reconnect_success = callback
    
    def set_reconnect_failure_callback(self, callback: Callable[[], Awaitable[None]]):
        """
        设置重连失败回调
        
        Args:
            callback: 重连失败时调用的异步函数
        """
        self._on_reconnect_failure = callback
    
    async def _notify_state_change(self, new_state: ReconnectState):
        """通知状态变化"""
        if self._on_state_change:
            try:
                await self._on_state_change(new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    async def start_reconnect(self) -> bool:
        """
        启动重连流程
        
        Returns:
            是否成功启动重连
        """
        if self.state == ReconnectState.RECONNECTING:
            logger.warning(f"Reconnect already in progress for user {self.user_id}")
            return False
        
        if self.attempt >= self.config.max_attempts:
            logger.warning(f"Max reconnect attempts reached for user {self.user_id}")
            self.state = ReconnectState.FAILED
            self._record_reconnect(
                ReconnectState.FAILED.value, 
                reason="Max attempts reached"
            )
            await self._notify_state_change(self.state)
            return False
        
        # 更新状态
        old_state = self.state
        self.state = ReconnectState.RECONNECTING
        self.attempt += 1
        self._reconnect_start_time = time.time()
        
        # 通知状态变化
        await self._notify_state_change(self.state)
        
        # 记录重连开始
        self._record_reconnect(
            ReconnectState.RECONNECTING.value, 
            attempt=self.attempt
        )
        
        # 广播重连状态
        await self._broadcast_reconnect_status()
        
        # 启动重连任务
        self.reconnect_task = asyncio.create_task(self._reconnect_loop())
        
        logger.info(
            f"Started reconnect attempt {self.attempt} for user {self.user_id} "
            f"in game {self.game_id}"
        )
        return True
    
    async def _reconnect_loop(self):
        """
        重连循环
        
        实现指数退避的重连逻辑，直到成功或达到最大尝试次数
        """
        try:
            while self.state == ReconnectState.RECONNECTING and self.attempt <= self.config.max_attempts:
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
                
                # 检查是否被取消
                if self.state != ReconnectState.RECONNECTING:
                    logger.info(f"Reconnect cancelled for user {self.user_id}")
                    return
                
                # 尝试重连
                success = await self._attempt_reconnect()
                
                if success:
                    await self._handle_reconnect_success()
                    return
                else:
                    await self._handle_reconnect_failure()
                        
        except asyncio.CancelledError:
            logger.info(f"Reconnect loop cancelled for user {self.user_id}")
            raise
        except Exception as e:
            logger.error(f"Error in reconnect loop for user {self.user_id}: {e}")
            self.state = ReconnectState.FAILED
            self._record_reconnect(ReconnectState.FAILED.value, reason=str(e))
            await self._broadcast_reconnect_status()
            await self._notify_state_change(self.state)
    
    async def _handle_reconnect_success(self):
        """处理重连成功"""
        self.state = ReconnectState.RECONNECTED
        self.attempt = 0  # 重置尝试次数
        
        # 更新统计
        self.stats.successful_reconnects += 1
        self.stats.current_streak += 1
        self.stats.max_streak = max(self.stats.max_streak, self.stats.current_streak)
        self.stats.last_reconnect_time = self._get_timestamp()
        
        # 记录重连时间用于计算平均值
        if self._reconnect_start_time:
            duration = (time.time() - self._reconnect_start_time) * 1000
            self._reconnect_times.append(duration)
            self._update_avg_reconnect_time()
        
        # 记录成功
        duration = int((time.time() - self._reconnect_start_time) * 1000) if self._reconnect_start_time else 0
        self._record_reconnect(
            ReconnectState.RECONNECTED.value,
            attempt=self.attempt,
            duration_ms=duration
        )
        
        # 广播重连成功
        await self._broadcast_reconnect_status()
        
        # 通知回调
        await self._notify_state_change(self.state)
        if self._on_reconnect_success:
            await self._on_reconnect_success()
        
        logger.info(f"Successfully reconnected for user {self.user_id}")
    
    async def _handle_reconnect_failure(self):
        """处理重连失败"""
        logger.warning(
            f"Reconnect attempt {self.attempt} failed for user {self.user_id}"
        )
        
        # 更新统计
        self.stats.failed_reconnects += 1
        self.stats.current_streak = 0
        
        # 继续下一次尝试
        if self.attempt < self.config.max_attempts:
            self.state = ReconnectState.RECONNECTING
        else:
            self.state = ReconnectState.FAILED
            self._record_reconnect(ReconnectState.FAILED.value, reason="All attempts failed")
            await self._broadcast_reconnect_status()
            await self._notify_state_change(self.state)
            
            if self._on_reconnect_failure:
                await self._on_reconnect_failure()
            
            logger.error(f"All reconnect attempts failed for user {self.user_id}")
    
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
            elif hasattr(self.consumer, 'reconnect'):
                await self.consumer.reconnect()
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
                    'max_attempts': self.config.max_attempts,
                    'next_delay_ms': self._calculate_delay() if self.state == ReconnectState.RECONNECTING else 0,
                    'stats': self.stats.to_dict(),
                    'config': self.config.to_dict()
                },
                'timestamp': self._get_timestamp()
            }
            
            # 发送给当前用户
            if hasattr(self.consumer, 'send') and self.consumer.channel_name:
                try:
                    await self.consumer.send(text_data=json.dumps(status_data))
                except Exception as e:
                    logger.warning(f"Failed to send status to user {self.user_id}: {e}")
            
            # 广播给房间内其他用户
            if hasattr(self.consumer, 'channel_layer') and hasattr(self.consumer, 'room_group_name'):
                try:
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
                    logger.warning(f"Failed to broadcast status: {e}")
        except Exception as e:
            logger.error(f"Error broadcasting reconnect status: {e}")
    
    def _record_reconnect(
        self, 
        state: str, 
        attempt: int = 0, 
        delay_ms: int = 0, 
        reason: str = "", 
        duration_ms: int = 0
    ):
        """
        记录重连事件
        
        Args:
            state: 重连状态
            attempt: 尝试次数
            delay_ms: 延迟时间
            reason: 原因
            duration_ms: 耗时
        """
        record = ReconnectRecord(
            timestamp=self._get_timestamp(),
            state=state,
            attempt=attempt,
            delay_ms=delay_ms,
            reason=reason,
            duration_ms=duration_ms,
            user_id=self.user_id,
            game_id=self.game_id
        )
        self.records.append(record)
        
        # 限制历史记录数量
        if len(self.records) > self.config.max_history_size:
            self.records = self.records[-self.config.max_history_size:]
    
    def _update_avg_reconnect_time(self):
        """更新平均重连时间"""
        if self._reconnect_times:
            self.stats.avg_reconnect_time_ms = sum(self._reconnect_times) / len(self._reconnect_times)
    
    def update_heartbeat(self):
        """
        更新心跳时间
        
        应该在收到任何 WebSocket 消息时调用
        """
        self.last_heartbeat = datetime.now(timezone.utc)
        
        # 如果之前是重连状态，现在心跳恢复，说明连接已恢复
        if self.state == ReconnectState.RECONNECTED:
            self.state = ReconnectState.CONNECTED
            self.stats.total_connections += 1
            self._notify_state_change(self.state)
    
    def is_heartbeat_timeout(self, timeout_seconds: Optional[int] = None) -> bool:
        """
        检查心跳是否超时
        
        Args:
            timeout_seconds: 超时阈值（秒），使用配置值如果未提供
            
        Returns:
            是否超时
        """
        timeout = timeout_seconds or self.config.heartbeat_timeout_seconds
        now = datetime.now(timezone.utc)
        delta = (now - self.last_heartbeat).total_seconds()
        return delta > timeout
    
    def get_connection_health(self) -> Dict[str, Any]:
        """
        获取连接健康状态
        
        Returns:
            健康状态信息
        """
        now = datetime.now(timezone.utc)
        time_since_heartbeat = (now - self.last_heartbeat).total_seconds()
        
        return {
            'is_healthy': not self.is_heartbeat_timeout(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'time_since_heartbeat_seconds': time_since_heartbeat,
            'timeout_threshold_seconds': self.config.heartbeat_timeout_seconds,
            'state': self.state.value,
            'attempt': self.attempt
        }
    
    def get_reconnect_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取重连历史记录
        
        Args:
            limit: 返回记录数量，使用配置值如果未提供
            
        Returns:
            重连记录列表
        """
        limit = limit or self.config.max_history_size
        return [record.to_dict() for record in self.records[-limit:]]
    
    def export_reconnect_history(self) -> str:
        """
        导出重连历史为 JSON
        
        Returns:
            JSON 字符串
        """
        return json.dumps([record.to_dict() for record in self.records], indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        stats_dict = self.stats.to_dict()
        stats_dict['total_records'] = len(self.records)
        return stats_dict
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = ConnectionStats()
        self._reconnect_times = []
    
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
    
    功能:
    - 集中管理所有重连管理器
    - 提供统一的 API 接口
    - 支持批量操作和清理
    
    使用示例:
        # 获取服务实例
        service = await ReconnectService.get_instance()
        
        # 创建管理器
        manager = service.create_manager(consumer, "game-123", "user-456")
        
        # 启动重连
        await service.start_reconnect("game-123", "user-456")
        
        # 更新心跳
        service.update_heartbeat("game-123", "user-456")
        
        # 获取统计
        stats = service.get_stats("game-123", "user-456")
        
        # 清理
        await service.cleanup()
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
    
    def create_manager(
        self, 
        consumer: Any, 
        game_id: str, 
        user_id: str,
        config: Optional[ReconnectConfig] = None
    ) -> ReconnectManager:
        """
        创建重连管理器
        
        Args:
            consumer: WebSocket consumer 实例
            game_id: 游戏 ID
            user_id: 用户 ID
            config: 重连配置
            
        Returns:
            新创建的重连管理器
        """
        key = self._make_key(game_id, user_id)
        
        # 如果已存在，先清理旧的
        if key in self._managers:
            old_manager = self._managers[key]
            old_manager.cancel()
        
        manager = ReconnectManager(consumer, game_id, user_id, config)
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
    
    def is_heartbeat_timeout(
        self, 
        game_id: str, 
        user_id: str, 
        timeout_seconds: Optional[int] = None
    ) -> bool:
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
    
    def get_connection_health(self, game_id: str, user_id: str) -> Dict[str, Any]:
        """
        获取连接健康状态
        
        Args:
            game_id: 游戏 ID
            user_id: 用户 ID
            
        Returns:
            健康状态信息
        """
        manager = self.get_manager(game_id, user_id)
        if not manager:
            return {'is_healthy': False, 'error': 'Manager not found'}
        
        return manager.get_connection_health()
    
    def get_reconnect_history(
        self, 
        game_id: str, 
        user_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
    
    def get_all_managers(self) -> Dict[str, ReconnectManager]:
        """
        获取所有管理器
        
        Returns:
            所有管理器的字典
        """
        return self._managers.copy()
    
    def get_active_reconnects(self) -> List[Dict[str, Any]]:
        """
        获取所有正在重连的连接
        
        Returns:
            正在重连的连接信息列表
        """
        active = []
        for key, manager in self._managers.items():
            if manager.state == ReconnectState.RECONNECTING:
                active.append({
                    'game_id': manager.game_id,
                    'user_id': manager.user_id,
                    'attempt': manager.attempt,
                    'max_attempts': manager.config.max_attempts
                })
        return active
    
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


# 便捷函数
async def init_reconnect_manager(
    consumer: Any, 
    game_id: str, 
    user_id: str,
    config: Optional[ReconnectConfig] = None
) -> ReconnectManager:
    """
    初始化重连管理器
    
    Args:
        consumer: WebSocket consumer 实例
        game_id: 游戏 ID
        user_id: 用户 ID
        config: 重连配置
        
    Returns:
        创建的重连管理器
    """
    service = await get_reconnect_service()
    return service.create_manager(consumer, game_id, user_id, config)


def check_heartbeat_timeout(
    game_id: str, 
    user_id: str, 
    timeout_seconds: int = 90
) -> bool:
    """
    检查心跳是否超时
    
    Args:
        game_id: 游戏 ID
        user_id: 用户 ID
        timeout_seconds: 超时阈值
        
    Returns:
        是否超时
    """
    if reconnect_service:
        return reconnect_service.is_heartbeat_timeout(game_id, user_id, timeout_seconds)
    return False
