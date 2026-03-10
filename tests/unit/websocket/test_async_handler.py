"""
WebSocket 异步处理器单元测试

测试 websocket/async_handler.py 中的 AsyncHandler、QueuedMessage 和 MessagePriority

测试范围：
- 消息队列管理
- 消息优先级处理
- 消息确认机制
- 异步批量处理
- 自动重试
- 流量控制
- 性能统计
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from websocket.async_handler import (
    AsyncHandler,
    QueuedMessage,
    MessagePriority,
    MessageStats,
    get_async_handler,
    create_async_handler
)


# ==================== MessagePriority 枚举测试 ====================

class TestMessagePriority:
    """MessagePriority 枚举测试"""
    
    def test_priority_values(self):
        """测试优先级值"""
        assert MessagePriority.CRITICAL.value == 0
        assert MessagePriority.HIGH.value == 1
        assert MessagePriority.NORMAL.value == 2
        assert MessagePriority.LOW.value == 3
    
    def test_priority_ordering(self):
        """测试优先级顺序"""
        assert MessagePriority.CRITICAL < MessagePriority.HIGH
        assert MessagePriority.HIGH < MessagePriority.NORMAL
        assert MessagePriority.NORMAL < MessagePriority.LOW


# ==================== QueuedMessage 测试 ====================

class TestQueuedMessage:
    """QueuedMessage 测试"""
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = QueuedMessage(
            priority=MessagePriority.HIGH.value,
            timestamp=time.time(),
            message_id='test-123',
            message_type='MOVE',
            payload={'from': 'e2', 'to': 'e4'},
            room_id='game-456'
        )
        
        assert msg.priority == 1
        assert msg.message_id == 'test-123'
        assert msg.message_type == 'MOVE'
        assert msg.room_id == 'game-456'
        assert msg.retry_count == 0
        assert msg.max_retries == 3
        assert msg.acknowledged is False
        assert msg.ack_timeout == 5.0
    
    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-456',
            message_type='CHAT',
            payload={'content': 'Hello'},
            room_id='game-789'
        )
        
        result = msg.to_dict()
        
        assert isinstance(result, dict)
        assert result['message_id'] == 'test-456'
        assert result['message_type'] == 'CHAT'
        assert result['room_id'] == 'game-789'
        assert result['priority'] == 2
        assert 'created_at' in result
    
    def test_message_ordering(self):
        """测试消息排序（优先级高的在前）"""
        msg1 = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='msg-1',
            message_type='CHAT',
            payload={},
            room_id='room-1'
        )
        
        msg2 = QueuedMessage(
            priority=MessagePriority.HIGH.value,
            timestamp=time.time() + 1,
            message_id='msg-2',
            message_type='MOVE',
            payload={},
            room_id='room-1'
        )
        
        # 高优先级应该小于低优先级（在优先队列中排在前面）
        assert msg2 < msg1


# ==================== MessageStats 测试 ====================

class TestMessageStats:
    """MessageStats 测试"""
    
    def test_stats_creation(self):
        """测试统计创建"""
        stats = MessageStats(
            total_enqueued=100,
            total_dequeued=95,
            total_acknowledged=90,
            total_failed=5,
            total_retried=10,
            avg_processing_time_ms=15.5
        )
        
        assert stats.total_enqueued == 100
        assert stats.total_dequeued == 95
        assert stats.total_acknowledged == 90
        assert stats.total_failed == 5
        assert stats.avg_processing_time_ms == 15.5
    
    def test_stats_to_dict(self):
        """测试统计转字典"""
        stats = MessageStats(
            total_enqueued=50,
            total_dequeued=45,
            total_acknowledged=40
        )
        stats.last_processed_at = datetime.now(timezone.utc)
        
        result = stats.to_dict()
        
        assert isinstance(result, dict)
        assert result['total_enqueued'] == 50
        assert result['total_dequeued'] == 45
        assert result['total_acknowledged'] == 40
        assert 'avg_processing_time_ms' in result
        assert 'last_processed_at' in result
    
    def test_stats_default_values(self):
        """测试统计默认值"""
        stats = MessageStats()
        
        assert stats.total_enqueued == 0
        assert stats.total_dequeued == 0
        assert stats.total_acknowledged == 0
        assert stats.total_failed == 0
        assert stats.total_retried == 0
        assert stats.avg_processing_time_ms == 0.0
        assert stats.last_processed_at is None


# ==================== AsyncHandler 初始化测试 ====================

class TestAsyncHandlerInitialization:
    """AsyncHandler 初始化测试"""
    
    def test_handler_creation(self):
        """测试处理器创建"""
        handler = AsyncHandler()
        
        assert handler._running is False
        assert handler._processor_task is None
        assert handler._ack_checker_task is None
        assert len(handler._queues) == 0
        assert len(handler._pending_acks) == 0
        assert len(handler._handlers) == 0
    
    def test_handler_config_values(self):
        """测试处理器配置值"""
        handler = AsyncHandler()
        
        assert handler.MAX_QUEUE_SIZE == 1000
        assert handler.BATCH_SIZE == 10
        assert handler.PROCESSING_INTERVAL == 0.1
        assert handler.ACK_TIMEOUT == 5.0
        assert handler.MAX_RETRIES == 3


# ==================== AsyncHandler 注册处理器测试 ====================

class TestAsyncHandlerRegisterHandler:
    """AsyncHandler 注册处理器测试"""
    
    def test_register_handler(self):
        """测试注册处理器"""
        handler = AsyncHandler()
        
        async def mock_handler(payload):
            return True
        
        handler.register_handler('MOVE', mock_handler)
        
        assert 'MOVE' in handler._handlers
        assert handler._handlers['MOVE'] is mock_handler
    
    def test_register_multiple_handlers(self):
        """测试注册多个处理器"""
        handler = AsyncHandler()
        
        async def move_handler(payload):
            return True
        
        async def chat_handler(payload):
            return True
        
        handler.register_handler('MOVE', move_handler)
        handler.register_handler('CHAT', chat_handler)
        
        assert len(handler._handlers) == 2
        assert 'MOVE' in handler._handlers
        assert 'CHAT' in handler._handlers


# ==================== AsyncHandler 消息队列测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerMessageQueue:
    """AsyncHandler 消息队列测试"""
    
    async def test_enqueue_message(self):
        """测试 enqueue 消息"""
        handler = AsyncHandler()
        
        message_id = await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={'from': 'e2', 'to': 'e4'},
            priority=MessagePriority.HIGH
        )
        
        assert message_id != ''
        assert handler.get_queue_size('game-123') == 1
    
    async def test_enqueue_message_with_custom_id(self):
        """测试使用自定义 ID enqueue 消息"""
        handler = AsyncHandler()
        
        message_id = await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={},
            message_id='custom-id-123'
        )
        
        assert message_id == 'custom-id-123'
    
    async def test_enqueue_message_queue_full(self):
        """测试队列满时 enqueue 消息"""
        handler = AsyncHandler()
        handler.MAX_QUEUE_SIZE = 3
        
        # 填满队列
        for i in range(3):
            await handler.enqueue_message('game-123', 'MSG', {})
        
        # 再次 enqueue 应该失败
        message_id = await handler.enqueue_message('game-123', 'MSG', {})
        
        assert message_id == ''
        assert handler.get_queue_size('game-123') == 3
    
    async def test_dequeue_message(self):
        """测试 dequeue 消息"""
        handler = AsyncHandler()
        
        await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={'move': 'e2e4'},
            priority=MessagePriority.NORMAL,
            message_id='msg-1'
        )
        
        await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={'move': 'e7e5'},
            priority=MessagePriority.HIGH,
            message_id='msg-2'
        )
        
        # 高优先级应该先出队
        msg = await handler.dequeue_message('game-123')
        assert msg is not None
        assert msg.message_id == 'msg-2'  # 高优先级
        
        # 然后是普通优先级
        msg = await handler.dequeue_message('game-123')
        assert msg is not None
        assert msg.message_id == 'msg-1'
        
        # 队列为空
        msg = await handler.dequeue_message('game-123')
        assert msg is None
    
    async def test_dequeue_empty_queue(self):
        """测试从空队列 dequeue"""
        handler = AsyncHandler()
        
        msg = await handler.dequeue_message('non-existent-room')
        assert msg is None


# ==================== AsyncHandler 消息确认测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerAcknowledgement:
    """AsyncHandler 消息确认测试"""
    
    async def test_acknowledge_message(self):
        """测试确认消息"""
        handler = AsyncHandler()
        
        message_id = await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={}
        )
        
        # 模拟消息被处理并加入待确认列表
        handler._pending_acks[message_id] = MagicMock()
        
        await handler.acknowledge_message(message_id)
        
        assert message_id not in handler._pending_acks
        assert handler._stats.total_acknowledged == 1
    
    async def test_acknowledge_nonexistent_message(self):
        """测试确认不存在的消息"""
        handler = AsyncHandler()
        
        # 不应该抛出异常
        await handler.acknowledge_message('nonexistent-id')


# ==================== AsyncHandler 启动停止测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerStartStop:
    """AsyncHandler 启动停止测试"""
    
    async def test_start_handler(self):
        """测试启动处理器"""
        handler = AsyncHandler()
        
        await handler.start()
        
        assert handler._running is True
        assert handler._processor_task is not None
        assert handler._ack_checker_task is not None
        
        await handler.stop()
    
    async def test_stop_handler(self):
        """测试停止处理器"""
        handler = AsyncHandler()
        
        await handler.start()
        await handler.stop()
        
        assert handler._running is False
        assert handler._processor_task is None or handler._processor_task.done()
        assert handler._ack_checker_task is None or handler._ack_checker_task.done()
    
    async def test_start_already_running(self):
        """测试重复启动"""
        handler = AsyncHandler()
        
        await handler.start()
        
        # 再次启动不应该出错
        await handler.start()
        
        await handler.stop()
    
    async def test_stop_not_running(self):
        """测试停止未运行的处理器"""
        handler = AsyncHandler()
        
        # 不应该出错
        await handler.stop()


# ==================== AsyncHandler 消息处理测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerMessageProcessing:
    """AsyncHandler 消息处理测试"""
    
    async def test_process_message_success(self):
        """测试成功处理消息"""
        handler = AsyncHandler()
        
        call_count = 0
        
        async def mock_handler(payload):
            nonlocal call_count
            call_count += 1
            return True
        
        handler.register_handler('MOVE', mock_handler)
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={'move': 'e2e4'},
            room_id='game-123'
        )
        
        result = await handler._process_message(msg)
        
        assert result is True
        assert call_count == 1
    
    async def test_process_message_no_handler(self):
        """测试没有处理器时处理消息"""
        handler = AsyncHandler()
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='UNKNOWN',
            payload={},
            room_id='game-123'
        )
        
        # 没有处理器也应该返回 True（避免重试）
        result = await handler._process_message(msg)
        
        assert result is True
    
    async def test_process_message_failure(self):
        """测试处理消息失败"""
        handler = AsyncHandler()
        
        async def failing_handler(payload):
            return False
        
        handler.register_handler('MOVE', failing_handler)
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={},
            room_id='game-123'
        )
        
        result = await handler._process_message(msg)
        
        assert result is False
    
    async def test_process_message_exception(self):
        """测试处理消息抛出异常"""
        handler = AsyncHandler()
        
        async def error_handler(payload):
            raise Exception('Processing error')
        
        handler.register_handler('MOVE', error_handler)
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={},
            room_id='game-123'
        )
        
        result = await handler._process_message(msg)
        
        assert result is False


# ==================== AsyncHandler 重试机制测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerRetry:
    """AsyncHandler 重试机制测试"""
    
    async def test_retry_message(self):
        """测试消息重试"""
        handler = AsyncHandler()
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={},
            room_id='game-123',
            retry_count=0,
            max_retries=3
        )
        
        initial_queue_size = handler.get_queue_size('game-123')
        
        await handler._retry_or_fail_message(msg)
        
        assert msg.retry_count == 1
        assert handler.get_queue_size('game-123') == initial_queue_size + 1
    
    async def test_retry_message_max_retries(self):
        """测试达到最大重试次数"""
        handler = AsyncHandler()
        
        msg = QueuedMessage(
            priority=MessagePriority.NORMAL.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={},
            room_id='game-123',
            retry_count=2,
            max_retries=3
        )
        
        initial_failed_count = handler._stats.total_failed
        
        await handler._retry_or_fail_message(msg)
        
        assert msg.retry_count == 3
        assert handler._stats.total_failed == initial_failed_count + 1
    
    async def test_retry_decreases_priority(self):
        """测试重试降低优先级"""
        handler = AsyncHandler()
        
        msg = QueuedMessage(
            priority=MessagePriority.HIGH.value,
            timestamp=time.time(),
            message_id='test-msg',
            message_type='MOVE',
            payload={},
            room_id='game-123',
            retry_count=0,
            max_retries=3
        )
        
        await handler._retry_or_fail_message(msg)
        
        # 优先级应该降低
        assert msg.priority == MessagePriority.NORMAL.value


# ==================== AsyncHandler 统计测试 ====================

class TestAsyncHandlerStats:
    """AsyncHandler 统计测试"""
    
    def test_get_stats(self):
        """测试获取统计"""
        handler = AsyncHandler()
        
        handler._stats.total_enqueued = 100
        handler._stats.total_dequeued = 95
        handler._stats.total_acknowledged = 90
        
        stats = handler.get_stats()
        
        assert stats['total_enqueued'] == 100
        assert stats['total_dequeued'] == 95
        assert stats['total_acknowledged'] == 90
        assert 'total_rooms' in stats
        assert 'pending_acks' in stats
        assert 'total_queued' in stats
    
    def test_get_queue_size(self):
        """测试获取队列大小"""
        handler = AsyncHandler()
        
        # 未初始化的队列应该返回 0
        assert handler.get_queue_size('non-existent') == 0


# ==================== AsyncHandler 清理测试 ====================

class TestAsyncHandlerCleanup:
    """AsyncHandler 清理测试"""
    
    def test_clear_queue(self):
        """测试清空队列"""
        handler = AsyncHandler()
        
        # 添加一些消息
        asyncio.run(handler.enqueue_message('game-123', 'MSG', {}))
        asyncio.run(handler.enqueue_message('game-123', 'MSG', {}))
        
        handler.clear_queue('game-123')
        
        assert handler.get_queue_size('game-123') == 0
    
    def test_clear_all_queues(self):
        """测试清空所有队列"""
        handler = AsyncHandler()
        
        # 添加一些消息
        asyncio.run(handler.enqueue_message('game-1', 'MSG', {}))
        asyncio.run(handler.enqueue_message('game-2', 'MSG', {}))
        
        handler.clear_all_queues()
        
        assert handler.get_queue_size('game-1') == 0
        assert handler.get_queue_size('game-2') == 0
        assert handler.get_pending_ack_count() == 0


# ==================== 全局函数测试 ====================

class TestGlobalFunctions:
    """全局函数测试"""
    
    def test_get_async_handler(self):
        """测试获取异步处理器"""
        handler1 = get_async_handler()
        handler2 = get_async_handler()
        
        # 应该返回同一个实例（单例）
        assert handler1 is handler2
    
    @pytest.mark.asyncio
    async def test_create_async_handler(self):
        """测试创建并启动异步处理器"""
        handler = await create_async_handler()
        
        assert handler is not None
        assert handler._running is True
        
        await handler.stop()


# ==================== 集成测试 ====================

@pytest.mark.asyncio
class TestAsyncHandlerIntegration:
    """AsyncHandler 集成测试"""
    
    async def test_full_message_lifecycle(self):
        """测试完整消息生命周期"""
        handler = AsyncHandler()
        
        processed_messages = []
        
        async def mock_handler(payload):
            processed_messages.append(payload)
            return True
        
        handler.register_handler('MOVE', mock_handler)
        
        # 启动处理器
        await handler.start()
        
        # 发送消息
        await handler.enqueue_message(
            room_id='game-123',
            message_type='MOVE',
            payload={'move': 'e2e4'},
            priority=MessagePriority.HIGH
        )
        
        # 等待处理
        await asyncio.sleep(0.3)
        
        # 停止处理器
        await handler.stop()
        
        # 验证消息被处理
        assert len(processed_messages) >= 1
    
    async def test_priority_ordering_integration(self):
        """测试优先级排序集成"""
        handler = AsyncHandler()
        
        processed_order = []
        
        async def mock_handler(payload):
            processed_order.append(payload['priority'])
            return True
        
        handler.register_handler('MSG', mock_handler)
        
        # 按相反顺序添加消息
        await handler.enqueue_message('room', 'MSG', {'priority': 'low'}, MessagePriority.LOW)
        await handler.enqueue_message('room', 'MSG', {'priority': 'normal'}, MessagePriority.NORMAL)
        await handler.enqueue_message('room', 'MSG', {'priority': 'high'}, MessagePriority.HIGH)
        await handler.enqueue_message('room', 'MSG', {'priority': 'critical'}, MessagePriority.CRITICAL)
        
        # 启动并快速处理
        await handler.start()
        await asyncio.sleep(0.3)
        await handler.stop()
        
        # 验证处理顺序（高优先级先处理）
        # 注意：由于批量处理，可能不会完全按顺序，但高优先级应该在前
        assert processed_order[0] == 'critical' or processed_order[0] == 'high'
    
    async def test_concurrent_enqueue(self):
        """测试并发 enqueue"""
        handler = AsyncHandler()
        
        # 并发 enqueue 10 条消息
        tasks = [
            handler.enqueue_message('game-123', 'MSG', {'id': i})
            for i in range(10)
        ]
        
        await asyncio.gather(*tasks)
        
        assert handler.get_queue_size('game-123') == 10


# ==================== 边界情况测试 ====================

class TestAsyncHandlerEdgeCases:
    """AsyncHandler 边界情况测试"""
    
    def test_empty_payload(self):
        """测试空 payload"""
        handler = AsyncHandler()
        
        asyncio.run(handler.enqueue_message(
            room_id='game-123',
            message_type='MSG',
            payload={}
        ))
        
        assert handler.get_queue_size('game-123') == 1
    
    def test_large_payload(self):
        """测试大 payload"""
        handler = AsyncHandler()
        
        large_data = {'data': 'x' * 10000}
        
        asyncio.run(handler.enqueue_message(
            room_id='game-123',
            message_type='MSG',
            payload=large_data
        ))
        
        assert handler.get_queue_size('game-123') == 1
    
    def test_special_characters_in_message_id(self):
        """测试消息 ID 中的特殊字符"""
        handler = AsyncHandler()
        
        asyncio.run(handler.enqueue_message(
            room_id='game-123',
            message_type='MSG',
            payload={},
            message_id='special!@#$%^&*()_+-=[]{}|;:,.<>?'
        ))
        
        assert handler.get_queue_size('game-123') == 1
    
    def test_multiple_rooms(self):
        """测试多个房间"""
        handler = AsyncHandler()
        
        asyncio.run(handler.enqueue_message('room-1', 'MSG', {}))
        asyncio.run(handler.enqueue_message('room-2', 'MSG', {}))
        asyncio.run(handler.enqueue_message('room-3', 'MSG', {}))
        
        assert handler.get_queue_size('room-1') == 1
        assert handler.get_queue_size('room-2') == 1
        assert handler.get_queue_size('room-3') == 1
        assert handler.get_stats()['total_rooms'] == 3
