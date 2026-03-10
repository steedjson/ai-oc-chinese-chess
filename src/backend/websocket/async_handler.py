"""
WebSocket 异步处理器

提供优化的异步消息处理功能：
- 消息队列管理
- 消息优先级处理
- 消息确认机制
- 异步批量处理
- 流量控制

使用示例：
    async_handler = AsyncHandler()
    await async_handler.enqueue_message('game-123', message, priority='high')
    await async_handler.process_queue()
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime, timezone
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class MessagePriority(IntEnum):
    """消息优先级枚举（数值越小优先级越高）"""
    CRITICAL = 0  # 关键消息（游戏结束、断线重连）
    HIGH = 1      # 高优先级（走棋、玩家加入/离开）
    NORMAL = 2    # 普通消息（聊天、状态更新）
    LOW = 3       # 低优先级（日志、统计）


@dataclass(order=True)
class QueuedMessage:
    """队列消息"""
    priority: int
    timestamp: float = field(compare=False)
    message_id: str = field(compare=False)
    message_type: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)
    room_id: str = field(compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)
    acknowledged: bool = field(default=False, compare=False)
    ack_timeout: float = field(default=5.0, compare=False)  # 确认超时（秒）
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), compare=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type,
            'payload': self.payload,
            'room_id': self.room_id,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'acknowledged': self.acknowledged,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class MessageStats:
    """消息统计"""
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_acknowledged: int = 0
    total_failed: int = 0
    total_retried: int = 0
    avg_processing_time_ms: float = 0.0
    last_processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_enqueued': self.total_enqueued,
            'total_dequeued': self.total_dequeued,
            'total_acknowledged': self.total_acknowledged,
            'total_failed': self.total_failed,
            'total_retried': self.total_retried,
            'avg_processing_time_ms': round(self.avg_processing_time_ms, 2),
            'last_processed_at': self.last_processed_at.isoformat() if self.last_processed_at else None
        }


class AsyncHandler:
    """
    异步消息处理器
    
    功能：
    - 消息队列管理（按优先级排序）
    - 异步批量处理
    - 消息确认机制
    - 自动重试
    - 流量控制
    - 性能统计
    """
    
    # 配置常量
    MAX_QUEUE_SIZE = 1000  # 最大队列大小
    BATCH_SIZE = 10  # 批量处理大小
    PROCESSING_INTERVAL = 0.1  # 处理间隔（秒）
    ACK_TIMEOUT = 5.0  # 确认超时（秒）
    MAX_RETRIES = 3  # 最大重试次数
    
    def __init__(self):
        """初始化异步处理器"""
        # 消息队列：room_id -> priority queue
        self._queues: Dict[str, List[QueuedMessage]] = defaultdict(list)
        
        # 待确认消息：message_id -> QueuedMessage
        self._pending_acks: Dict[str, QueuedMessage] = {}
        
        # 消息处理器：message_type -> handler function
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[bool]]] = {}
        
        # 统计信息
        self._stats = MessageStats()
        self._processing_times: List[float] = []
        
        # 控制标志
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._ack_checker_task: Optional[asyncio.Task] = None
        
        # 锁
        self._queue_lock = asyncio.Lock()
        self._stats_lock = asyncio.Lock()
        
        logger.info("AsyncHandler initialized")
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], Awaitable[bool]]):
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 异步处理函数，返回 bool 表示是否成功
        """
        self._handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def start(self):
        """启动异步处理器"""
        if self._running:
            logger.warning("AsyncHandler already running")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        self._ack_checker_task = asyncio.create_task(self._ack_check_loop())
        
        logger.info("AsyncHandler started")
    
    async def stop(self):
        """停止异步处理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消任务
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self._ack_checker_task and not self._ack_checker_task.done():
            self._ack_checker_task.cancel()
            try:
                await self._ack_checker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("AsyncHandler stopped")
    
    async def enqueue_message(
        self,
        room_id: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        message_id: Optional[str] = None
    ) -> str:
        """
         enqueue 消息到队列
        
        Args:
            room_id: 房间 ID
            message_type: 消息类型
            payload: 消息负载
            priority: 优先级
            message_id: 消息 ID（可选，自动生成）
        
        Returns:
            消息 ID
        """
        async with self._queue_lock:
            # 检查队列大小
            if len(self._queues[room_id]) >= self.MAX_QUEUE_SIZE:
                logger.warning(f"Queue full for room {room_id}, dropping message")
                async with self._stats_lock:
                    self._stats.total_failed += 1
                return ""
            
            # 生成消息 ID
            if not message_id:
                message_id = f"{room_id}_{int(time.time() * 1000)}_{len(self._queues[room_id])}"
            
            # 创建队列消息
            queued_msg = QueuedMessage(
                priority=priority.value,
                timestamp=time.time(),
                message_id=message_id,
                message_type=message_type,
                payload=payload,
                room_id=room_id
            )
            
            # 加入优先队列
            heapq.heappush(self._queues[room_id], queued_msg)
            
            async with self._stats_lock:
                self._stats.total_enqueued += 1
            
            logger.debug(f"Enqueued message {message_id} to room {room_id} with priority {priority.name}")
            return message_id
    
    async def dequeue_message(self, room_id: str) -> Optional[QueuedMessage]:
        """
        从队列取出消息
        
        Args:
            room_id: 房间 ID
        
        Returns:
            队列消息，队列为空返回 None
        """
        async with self._queue_lock:
            if not self._queues[room_id]:
                return None
            
            msg = heapq.heappop(self._queues[room_id])
            
            async with self._stats_lock:
                self._stats.total_dequeued += 1
            
            return msg
    
    async def acknowledge_message(self, message_id: str):
        """
        确认消息已处理
        
        Args:
            message_id: 消息 ID
        """
        async with self._queue_lock:
            if message_id in self._pending_acks:
                del self._pending_acks[message_id]
                
                async with self._stats_lock:
                    self._stats.total_acknowledged += 1
                
                logger.debug(f"Message {message_id} acknowledged")
    
    async def _process_loop(self):
        """消息处理循环"""
        try:
            while self._running:
                await self._process_batch()
                await asyncio.sleep(self.PROCESSING_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Process loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in process loop: {e}")
    
    async def _process_batch(self):
        """批量处理消息"""
        start_time = time.time()
        processed_count = 0
        
        # 获取所有有消息的房间
        async with self._queue_lock:
            rooms_with_messages = [
                room_id for room_id, queue in self._queues.items() 
                if queue
            ]
        
        # 轮询处理每个房间的消息
        for room_id in rooms_with_messages:
            if processed_count >= self.BATCH_SIZE:
                break
            
            msg = await self.dequeue_message(room_id)
            if not msg:
                continue
            
            # 处理消息
            success = await self._process_message(msg)
            
            if success:
                # 加入待确认列表
                self._pending_acks[msg.message_id] = msg
                processed_count += 1
            else:
                # 处理失败，尝试重试
                await self._retry_or_fail_message(msg)
        
        # 更新平均处理时间
        if processed_count > 0:
            processing_time = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time)
            
            # 保留最近 100 次记录
            if len(self._processing_times) > 100:
                self._processing_times = self._processing_times[-100:]
            
            async with self._stats_lock:
                self._stats.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                self._stats.last_processed_at = datetime.now(timezone.utc)
    
    async def _process_message(self, msg: QueuedMessage) -> bool:
        """
        处理单条消息
        
        Args:
            msg: 队列消息
        
        Returns:
            是否成功
        """
        try:
            # 查找处理器
            handler = self._handlers.get(msg.message_type)
            
            if not handler:
                logger.warning(f"No handler for message type: {msg.message_type}")
                return True  # 没有处理器也视为成功（避免重复尝试）
            
            # 调用处理器
            success = await handler(msg.payload)
            
            if success:
                logger.debug(f"Processed message {msg.message_id} successfully")
            else:
                logger.warning(f"Handler returned false for message {msg.message_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing message {msg.message_id}: {e}")
            return False
    
    async def _retry_or_fail_message(self, msg: QueuedMessage):
        """
        重试或失败消息
        
        Args:
            msg: 队列消息
        """
        msg.retry_count += 1
        
        async with self._stats_lock:
            self._stats.total_retried += 1
        
        if msg.retry_count >= msg.max_retries:
            # 达到最大重试次数，标记为失败
            async with self._stats_lock:
                self._stats.total_failed += 1
            
            logger.error(f"Message {msg.message_id} failed after {msg.retry_count} retries")
        else:
            # 重新加入队列（降低优先级）
            msg.priority = min(msg.priority + 1, MessagePriority.LOW.value)
            msg.timestamp = time.time()
            
            async with self._queue_lock:
                heapq.heappush(self._queues[msg.room_id], msg)
            
            logger.info(f"Retrying message {msg.message_id} (attempt {msg.retry_count}/{msg.max_retries})")
    
    async def _ack_check_loop(self):
        """确认检查循环"""
        try:
            while self._running:
                await self._check_ack_timeouts()
                await asyncio.sleep(1.0)  # 每秒检查一次
        except asyncio.CancelledError:
            logger.info("Ack checker loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in ack check loop: {e}")
    
    async def _check_ack_timeouts(self):
        """检查确认超时"""
        current_time = time.time()
        timed_out_messages = []
        
        async with self._queue_lock:
            for message_id, msg in list(self._pending_acks.items()):
                if current_time - msg.timestamp > msg.ack_timeout:
                    timed_out_messages.append(message_id)
        
        # 处理超时消息
        for message_id in timed_out_messages:
            async with self._queue_lock:
                msg = self._pending_acks.pop(message_id, None)
            
            if msg:
                logger.warning(f"Message {message_id} acknowledgement timed out")
                await self._retry_or_fail_message(msg)
    
    def get_queue_size(self, room_id: str) -> int:
        """
        获取队列大小
        
        Args:
            room_id: 房间 ID
        
        Returns:
            队列中的消息数量
        """
        return len(self._queues.get(room_id, []))
    
    def get_pending_ack_count(self) -> int:
        """
        获取待确认消息数量
        
        Returns:
            待确认消息数量
        """
        return len(self._pending_acks)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        stats_dict = self._stats.to_dict()
        stats_dict['total_rooms'] = len(self._queues)
        stats_dict['pending_acks'] = len(self._pending_acks)
        stats_dict['total_queued'] = sum(len(q) for q in self._queues.values())
        return stats_dict
    
    def clear_queue(self, room_id: str):
        """
        清空房间队列
        
        Args:
            room_id: 房间 ID
        """
        if room_id in self._queues:
            self._queues[room_id].clear()
            logger.info(f"Cleared queue for room {room_id}")
    
    def clear_all_queues(self):
        """清空所有队列"""
        self._queues.clear()
        self._pending_acks.clear()
        logger.info("Cleared all queues")


# 全局异步处理器实例
_async_handler: Optional[AsyncHandler] = None


def get_async_handler() -> AsyncHandler:
    """获取全局异步处理器实例"""
    global _async_handler
    if _async_handler is None:
        _async_handler = AsyncHandler()
    return _async_handler


async def create_async_handler() -> AsyncHandler:
    """创建并启动异步处理器"""
    handler = get_async_handler()
    await handler.start()
    return handler
