#!/usr/bin/env python3
"""
WebSocket 重连功能快速验证脚本

不依赖 Django 环境，仅验证核心逻辑
"""
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# 添加路径
sys.path.insert(0, '/Users/changsailong/.openclaw/workspace/projects/chinese-chess/src/backend')

# 导入模块
from games.websocket_reconnect import (
    ReconnectManager,
    ReconnectService,
    ReconnectState,
    ReconnectRecord,
    ConnectionStats,
)


def test_reconnect_state():
    """测试重连状态枚举"""
    print("✓ Testing ReconnectState enum...")
    assert ReconnectState.CONNECTED.value == "connected"
    assert ReconnectState.RECONNECTING.value == "reconnecting"
    assert ReconnectState.FAILED.value == "failed"
    print("  ✓ All state values correct")


def test_reconnect_record():
    """测试重连记录"""
    print("✓ Testing ReconnectRecord...")
    record = ReconnectRecord(
        timestamp="2024-01-01T00:00:00Z",
        state="reconnecting",
        attempt=1,
        delay_ms=1000
    )
    assert record.state == "reconnecting"
    assert record.attempt == 1
    
    result = record.to_dict()
    assert 'timestamp' in result
    assert 'state' in result
    print("  ✓ Record creation and to_dict() work correctly")


def test_connection_stats():
    """测试连接统计"""
    print("✓ Testing ConnectionStats...")
    stats = ConnectionStats()
    assert stats.total_connections == 0
    assert stats.current_streak == 0
    
    stats.successful_reconnects = 3
    stats.current_streak = 2
    result = stats.to_dict()
    assert result['successful_reconnects'] == 3
    print("  ✓ Stats tracking works correctly")


def test_reconnect_manager_initialization():
    """测试重连管理器初始化"""
    print("✓ Testing ReconnectManager initialization...")
    mock_consumer = type('MockConsumer', (), {
        'send': asyncio.coroutine(lambda self, data: None),
        'channel_name': 'test',
        'channel_layer': type('MockLayer', (), {
            'group_send': asyncio.coroutine(lambda self, name, data: None)
        })(),
        'room_group_name': 'game_test',
        '_reconnect_channel': asyncio.coroutine(lambda self: True)
    })()
    
    manager = ReconnectManager(mock_consumer, "game-123", "user-456")
    assert manager.game_id == "game-123"
    assert manager.user_id == "user-456"
    assert manager.state == ReconnectState.CONNECTED
    assert manager.attempt == 0
    print("  ✓ Manager initializes with correct state")


def test_delay_calculation():
    """测试延迟计算（指数退避）"""
    print("✓ Testing delay calculation (exponential backoff)...")
    mock_consumer = type('MockConsumer', (), {
        'send': asyncio.coroutine(lambda self, data: None),
        'channel_name': 'test',
        'channel_layer': type('MockLayer', (), {
            'group_send': asyncio.coroutine(lambda self, name, data: None)
        })(),
        'room_group_name': 'game_test',
        '_reconnect_channel': asyncio.coroutine(lambda self: True)
    })()
    
    manager = ReconnectManager(mock_consumer, "game-123", "user-456")
    
    # 测试初始延迟
    manager.attempt = 0
    delay = manager._calculate_delay()
    assert 1000 <= delay <= 1500, f"Expected 1000-1500, got {delay}"
    print(f"  ✓ Attempt 1: {delay}ms (expected 1000-1500ms)")
    
    # 测试第二次延迟
    manager.attempt = 1
    delay = manager._calculate_delay()
    assert 2000 <= delay <= 2500, f"Expected 2000-2500, got {delay}"
    print(f"  ✓ Attempt 2: {delay}ms (expected 2000-2500ms)")
    
    # 测试最大延迟
    manager.attempt = 10
    delay = manager._calculate_delay()
    assert delay <= 30500, f"Expected <= 30500, got {delay}"
    print(f"  ✓ Attempt 11: {delay}ms (capped at ~30000ms + jitter)")


def test_heartbeat_timeout():
    """测试心跳超时检测"""
    print("✓ Testing heartbeat timeout detection...")
    mock_consumer = type('MockConsumer', (), {
        'send': asyncio.coroutine(lambda self, data: None),
        'channel_name': 'test',
        'channel_layer': type('MockLayer', (), {
            'group_send': asyncio.coroutine(lambda self, name, data: None)
        })(),
        'room_group_name': 'game_test',
        '_reconnect_channel': asyncio.coroutine(lambda self: True)
    })()
    
    manager = ReconnectManager(mock_consumer, "game-123", "user-456")
    
    # 更新心跳
    manager.update_heartbeat()
    assert not manager.is_heartbeat_timeout(90)
    print("  ✓ Recent heartbeat: no timeout")
    
    # 模拟旧心跳
    manager.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=100)
    assert manager.is_heartbeat_timeout(90)
    print("  ✓ Old heartbeat (100s): timeout detected")


async def test_reconnect_service_singleton():
    """测试重连服务单例模式"""
    print("✓ Testing ReconnectService singleton...")
    ReconnectService._instance = None
    
    service1 = await ReconnectService.get_instance()
    service2 = await ReconnectService.get_instance()
    
    assert service1 is service2
    print("  ✓ Singleton pattern works correctly")


async def test_manager_lifecycle():
    """测试管理器生命周期"""
    print("✓ Testing manager lifecycle...")
    ReconnectService._instance = None
    
    mock_consumer = type('MockConsumer', (), {
        'send': asyncio.coroutine(lambda self, data: None),
        'channel_name': 'test',
        'channel_layer': type('MockLayer', (), {
            'group_send': asyncio.coroutine(lambda self, name, data: None)
        })(),
        'room_group_name': 'game_test',
        '_reconnect_channel': asyncio.coroutine(lambda self: True)
    })()
    
    service = await ReconnectService.get_instance()
    
    # 创建管理器
    manager = service.create_manager(mock_consumer, "game-123", "user-456")
    assert service.get_manager("game-123", "user-456") is manager
    print("  ✓ Manager created and retrieved")
    
    # 移除管理器
    service.remove_manager("game-123", "user-456")
    assert service.get_manager("game-123", "user-456") is None
    print("  ✓ Manager removed successfully")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("WebSocket Reconnect - Quick Validation")
    print("="*60 + "\n")
    
    try:
        # 同步测试
        test_reconnect_state()
        test_reconnect_record()
        test_connection_stats()
        test_reconnect_manager_initialization()
        test_delay_calculation()
        test_heartbeat_timeout()
        
        # 异步测试
        await test_reconnect_service_singleton()
        await test_manager_lifecycle()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
