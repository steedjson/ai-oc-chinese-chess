"""
WebSocket 断线重连测试

测试重连服务的各项功能：
- 断线检测
- 自动重连（指数退避）
- 重连状态管理
- 重连历史记录
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from games.websocket_reconnect import (
    ReconnectManager,
    ReconnectService,
    ReconnectState,
    ReconnectRecord,
    ConnectionStats,
)


class TestReconnectState:
    """测试重连状态枚举"""
    
    def test_reconnect_state_values(self):
        """测试重连状态值"""
        assert ReconnectState.CONNECTED.value == "connected"
        assert ReconnectState.DISCONNECTED.value == "disconnected"
        assert ReconnectState.RECONNECTING.value == "reconnecting"
        assert ReconnectState.RECONNECTED.value == "reconnected"
        assert ReconnectState.FAILED.value == "failed"


class TestReconnectRecord:
    """测试重连记录"""
    
    def test_reconnect_record_creation(self):
        """测试重连记录创建"""
        record = ReconnectRecord(
            timestamp="2024-01-01T00:00:00Z",
            state="reconnecting",
            attempt=1,
            delay_ms=1000,
            reason="Connection lost",
            duration_ms=0
        )
        
        assert record.timestamp == "2024-01-01T00:00:00Z"
        assert record.state == "reconnecting"
        assert record.attempt == 1
        assert record.delay_ms == 1000
    
    def test_reconnect_record_to_dict(self):
        """测试重连记录转换为字典"""
        record = ReconnectRecord(
            timestamp="2024-01-01T00:00:00Z",
            state="reconnected",
            attempt=1
        )
        
        result = record.to_dict()
        
        assert result['timestamp'] == "2024-01-01T00:00:00Z"
        assert result['state'] == "reconnected"
        assert result['attempt'] == 1


class TestConnectionStats:
    """测试连接统计"""
    
    def test_connection_stats_default(self):
        """测试连接统计默认值"""
        stats = ConnectionStats()
        
        assert stats.total_connections == 0
        assert stats.total_reconnects == 0
        assert stats.successful_reconnects == 0
        assert stats.failed_reconnects == 0
        assert stats.current_streak == 0
        assert stats.max_streak == 0
    
    def test_connection_stats_to_dict(self):
        """测试连接统计转换为字典"""
        stats = ConnectionStats(
            total_connections=5,
            successful_reconnects=3,
            current_streak=2,
            max_streak=3
        )
        
        result = stats.to_dict()
        
        assert result['total_connections'] == 5
        assert result['successful_reconnects'] == 3
        assert result['current_streak'] == 2
        assert result['max_streak'] == 3


class TestReconnectManager:
    """测试重连管理器"""
    
    @pytest.fixture
    def mock_consumer(self):
        """模拟 Consumer"""
        consumer = Mock()
        consumer.send = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()
        consumer.room_group_name = "game_test"
        consumer._reconnect_channel = AsyncMock(return_value=True)
        return consumer
    
    @pytest.fixture
    def reconnect_manager(self, mock_consumer):
        """创建重连管理器"""
        return ReconnectManager(mock_consumer, "game-123", "user-456")
    
    def test_initial_state(self, reconnect_manager):
        """测试初始状态"""
        assert reconnect_manager.state == ReconnectState.CONNECTED
        assert reconnect_manager.attempt == 0
        assert reconnect_manager.game_id == "game-123"
        assert reconnect_manager.user_id == "user-456"
    
    def test_calculate_delay_initial(self, reconnect_manager):
        """测试初始延迟计算"""
        delay = reconnect_manager._calculate_delay()
        
        # 初始延迟应该在 1000-1500ms 之间（含抖动）
        assert 1000 <= delay <= 1500
    
    def test_calculate_delay_exponential(self, reconnect_manager):
        """测试指数退避延迟计算"""
        reconnect_manager.attempt = 1
        delay = reconnect_manager._calculate_delay()
        
        # 第二次尝试延迟应该在 2000-2500ms 之间
        assert 2000 <= delay <= 2500
        
        reconnect_manager.attempt = 2
        delay = reconnect_manager._calculate_delay()
        
        # 第三次尝试延迟应该在 4000-4500ms 之间
        assert 4000 <= delay <= 4500
    
    def test_calculate_delay_max(self, reconnect_manager):
        """测试最大延迟限制"""
        reconnect_manager.attempt = 10
        delay = reconnect_manager._calculate_delay()
        
        # 延迟不应超过最大值 30000ms
        assert delay <= 30000
    
    def test_update_heartbeat(self, reconnect_manager):
        """测试心跳更新"""
        old_heartbeat = reconnect_manager.last_heartbeat
        asyncio.sleep(0.1)
        
        reconnect_manager.update_heartbeat()
        
        assert reconnect_manager.last_heartbeat > old_heartbeat
    
    def test_is_heartbeat_timeout_false(self, reconnect_manager):
        """测试心跳未超时"""
        reconnect_manager.update_heartbeat()
        
        # 刚更新心跳，不应超时
        assert not reconnect_manager.is_heartbeat_timeout(90)
    
    def test_is_heartbeat_timeout_true(self, reconnect_manager):
        """测试心跳超时"""
        # 设置一个很久以前的心跳时间
        reconnect_manager.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=100)
        
        # 应该超时
        assert reconnect_manager.is_heartbeat_timeout(90)
    
    def test_get_reconnect_history_empty(self, reconnect_manager):
        """测试获取空的重连历史"""
        history = reconnect_manager.get_reconnect_history()
        
        assert history == []
    
    def test_get_stats(self, reconnect_manager):
        """测试获取统计信息"""
        stats = reconnect_manager.get_stats()
        
        assert 'total_connections' in stats
        assert 'total_reconnects' in stats
        assert 'total_records' in stats
    
    @pytest.mark.asyncio
    async def test_start_reconnect_success(self, reconnect_manager, mock_consumer):
        """测试成功重连"""
        # Mock 重连方法
        mock_consumer._reconnect_channel = AsyncMock(return_value=True)
        
        # 启动重连
        result = await reconnect_manager.start_reconnect()
        
        assert result is True
        assert reconnect_manager.state == ReconnectState.RECONNECTING
        
        # 等待重连完成
        await asyncio.sleep(0.1)
        
        # 验证状态更新
        assert reconnect_manager.attempt >= 1
    
    @pytest.mark.asyncio
    async def test_start_reconnect_already_in_progress(self, reconnect_manager):
        """测试重连已在进行中"""
        reconnect_manager.state = ReconnectState.RECONNECTING
        
        result = await reconnect_manager.start_reconnect()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_start_reconnect_max_attempts(self, reconnect_manager):
        """测试达到最大重连次数"""
        reconnect_manager.attempt = ReconnectManager.MAX_ATTEMPTS
        
        result = await reconnect_manager.start_reconnect()
        
        assert result is False
        assert reconnect_manager.state == ReconnectState.FAILED
    
    @pytest.mark.asyncio
    async def test_reconnect_loop_success(self, reconnect_manager, mock_consumer):
        """测试重连循环成功"""
        mock_consumer._reconnect_channel = AsyncMock(return_value=True)
        
        # 启动重连
        await reconnect_manager.start_reconnect()
        
        # 等待重连完成
        await asyncio.sleep(0.5)
        
        # 验证成功重连
        assert reconnect_manager.state == ReconnectState.RECONNECTED
        assert reconnect_manager.attempt == 0
        assert reconnect_manager.stats.successful_reconnects >= 1
    
    @pytest.mark.asyncio
    async def test_reconnect_loop_failure(self, mock_consumer):
        """测试重连循环失败"""
        # Mock 重连方法总是失败
        mock_consumer._reconnect_channel = AsyncMock(return_value=False)
        
        manager = ReconnectManager(mock_consumer, "game-123", "user-456")
        manager.MAX_ATTEMPTS = 2  # 减少测试时间
        
        # 启动重连
        await manager.start_reconnect()
        
        # 等待所有尝试完成
        await asyncio.sleep(3)  # 等待两次尝试
        
        # 验证失败
        assert manager.state == ReconnectState.FAILED
        assert manager.stats.failed_reconnects >= 1
    
    def test_cancel_reconnect(self, reconnect_manager):
        """测试取消重连"""
        # 启动重连任务
        reconnect_manager.reconnect_task = asyncio.create_task(asyncio.sleep(10))
        
        # 取消
        reconnect_manager.cancel()
        
        # 验证任务已取消
        assert reconnect_manager.reconnect_task.cancelled() or reconnect_manager.reconnect_task.done()
    
    def test_reset(self, reconnect_manager):
        """测试重置重连管理器"""
        reconnect_manager.state = ReconnectState.FAILED
        reconnect_manager.attempt = 5
        
        reconnect_manager.reset()
        
        assert reconnect_manager.state == ReconnectState.CONNECTED
        assert reconnect_manager.attempt == 0


class TestReconnectService:
    """测试重连服务"""
    
    @pytest.fixture
    def mock_consumer(self):
        """模拟 Consumer"""
        consumer = Mock()
        consumer.send = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()
        consumer.room_group_name = "game_test"
        consumer._reconnect_channel = AsyncMock(return_value=True)
        return consumer
    
    @pytest.fixture(autouse=True)
    def reset_service(self):
        """重置服务单例"""
        ReconnectService._instance = None
        yield
        ReconnectService._instance = None
    
    def test_singleton_instance(self):
        """测试单例模式"""
        service1 = ReconnectService()
        service2 = ReconnectService()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_get_instance(self):
        """测试获取实例"""
        service = await ReconnectService.get_instance()
        
        assert service is not None
        assert isinstance(service, ReconnectService)
    
    def test_create_manager(self, mock_consumer):
        """测试创建管理器"""
        service = ReconnectService()
        
        manager = service.create_manager(mock_consumer, "game-123", "user-456")
        
        assert manager is not None
        assert manager.game_id == "game-123"
        assert manager.user_id == "user-456"
    
    def test_get_manager(self, mock_consumer):
        """测试获取管理器"""
        service = ReconnectService()
        
        # 先创建
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 再获取
        manager = service.get_manager("game-123", "user-456")
        
        assert manager is not None
    
    def test_get_manager_not_exists(self):
        """测试获取不存在的管理器"""
        service = ReconnectService()
        
        manager = service.get_manager("nonexistent", "nonexistent")
        
        assert manager is None
    
    def test_remove_manager(self, mock_consumer):
        """测试移除管理器"""
        service = ReconnectService()
        
        # 创建
        manager = service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 移除
        service.remove_manager("game-123", "user-456")
        
        # 验证已移除
        assert service.get_manager("game-123", "user-456") is None
    
    @pytest.mark.asyncio
    async def test_start_reconnect(self, mock_consumer):
        """测试启动重连"""
        service = ReconnectService()
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        result = await service.start_reconnect("game-123", "user-456")
        
        assert result is True
    
    def test_update_heartbeat(self, mock_consumer):
        """测试更新心跳"""
        service = ReconnectService()
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 不应该抛出异常
        service.update_heartbeat("game-123", "user-456")
    
    def test_is_heartbeat_timeout(self, mock_consumer):
        """测试心跳超时检查"""
        service = ReconnectService()
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 刚创建，不应超时
        assert not service.is_heartbeat_timeout("game-123", "user-456", 90)
    
    def test_get_reconnect_history(self, mock_consumer):
        """测试获取重连历史"""
        service = ReconnectService()
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        history = service.get_reconnect_history("game-123", "user-456", limit=5)
        
        assert isinstance(history, list)
    
    def test_get_stats(self, mock_consumer):
        """测试获取统计信息"""
        service = ReconnectService()
        service.create_manager(mock_consumer, "game-123", "user-456")
        
        stats = service.get_stats("game-123", "user-456")
        
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_consumer):
        """测试清理"""
        service = ReconnectService()
        
        # 创建多个管理器
        service.create_manager(mock_consumer, "game-1", "user-1")
        service.create_manager(mock_consumer, "game-2", "user-2")
        
        # 清理
        await service.cleanup()
        
        # 验证已清理
        assert len(service._managers) == 0


class TestReconnectIntegration:
    """集成测试"""
    
    @pytest.fixture
    def mock_consumer(self):
        """模拟 Consumer"""
        consumer = Mock()
        consumer.send = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()
        consumer.room_group_name = "game_test"
        consumer._reconnect_channel = AsyncMock(return_value=True)
        return consumer
    
    @pytest.mark.asyncio
    async def test_full_reconnect_cycle(self, mock_consumer):
        """测试完整重连周期"""
        # 创建服务和管理器
        service = ReconnectService()
        manager = service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 初始状态
        assert manager.state == ReconnectState.CONNECTED
        
        # 模拟心跳超时
        manager.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=100)
        
        # 启动重连
        result = await manager.start_reconnect()
        assert result is True
        
        # 等待重连完成
        await asyncio.sleep(0.5)
        
        # 验证重连成功
        assert manager.state == ReconnectState.RECONNECTED
        
        # 更新心跳，恢复正常状态
        manager.update_heartbeat()
        assert manager.state == ReconnectState.CONNECTED
        
        # 验证历史记录
        history = manager.get_reconnect_history()
        assert len(history) > 0
        
        # 验证统计
        stats = manager.get_stats()
        assert stats['successful_reconnects'] >= 1
    
    @pytest.mark.asyncio
    async def test_multiple_reconnect_attempts(self, mock_consumer):
        """测试多次重连尝试"""
        service = ReconnectService()
        manager = service.create_manager(mock_consumer, "game-123", "user-456")
        
        # 模拟多次连接 - 断开 - 重连
        for i in range(3):
            # 启动重连
            await manager.start_reconnect()
            await asyncio.sleep(0.3)
            
            # 验证成功
            assert manager.state == ReconnectState.RECONNECTED
            
            # 重置
            manager.update_heartbeat()
            manager.state = ReconnectState.CONNECTED
        
        # 验证统计
        stats = manager.get_stats()
        assert stats['successful_reconnects'] >= 3
        assert stats['current_streak'] >= 3
