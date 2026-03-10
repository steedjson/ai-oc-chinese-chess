# WebSocket 断线重连优化使用指南

## 概述

WebSocket 断线重连优化模块提供了完整的断线检测、自动重连、状态管理和历史记录功能，确保中国象棋游戏的 WebSocket 连接稳定可靠。

## 核心功能

### 1. 断线检测机制（心跳监测）

- **心跳追踪**: 自动记录每次消息接收的时间
- **超时检测**: 可配置的心跳超时阈值（默认 90 秒）
- **健康检查**: 实时检查连接健康状态

### 2. 自动重连逻辑（指数退避）

- **指数退避算法**: 重连延迟按指数增长（1s → 2s → 4s → ...）
- **随机抖动**: 避免多个连接同时重连造成服务器压力
- **最大尝试次数**: 限制重连次数（默认 10 次）
- **最大延迟**: 限制最大重连延迟（默认 30 秒）

### 3. 重连状态提示

- **实时状态广播**: 向客户端和房间内其他用户广播重连状态
- **详细状态信息**: 包含当前尝试次数、下次延迟、统计信息等
- **状态回调**: 支持注册状态变化回调函数

### 4. 重连历史记录

- **完整记录**: 记录每次重连的详细信息
- **限制大小**: 自动限制历史记录数量（默认 100 条）
- **导出功能**: 支持导出为 JSON 格式

### 5. 连接统计

- **连接次数统计**: 总连接数、总重连数
- **成功率统计**: 成功/失败重连次数
- **连续成功**: 当前和最大连续成功次数
- **平均耗时**: 平均重连时间

## 快速开始

### 在 Consumer 中使用

```python
from games.websocket_reconnect_optimized import (
    ReconnectManager,
    ReconnectConfig,
    get_reconnect_service
)

class GameConsumer(BaseConsumer):
    """游戏 WebSocket Consumer"""
    
    async def connect(self):
        """建立连接"""
        await super().connect()
        
        # 创建重连管理器
        self.reconnect_manager = ReconnectManager(
            consumer=self,
            game_id=self.game_id,
            user_id=self.user_id
        )
        
        # 设置状态变化回调
        self.reconnect_manager.set_state_change_callback(
            self._on_reconnect_state_change
        )
        
        # 设置重连成功回调
        self.reconnect_manager.set_reconnect_success_callback(
            self._on_reconnect_success
        )
        
        # 设置重连失败回调
        self.reconnect_manager.set_reconnect_failure_callback(
            self._on_reconnect_failure
        )
        
        # 接受连接
        await self.accept()
        logger.info(f"WebSocket connected for user {self.user_id}")
    
    async def disconnect(self, close_code: int):
        """断开连接"""
        # 非正常断开时启动重连
        if close_code != 1000:  # 1000 是正常关闭
            logger.warning(
                f"Abnormal disconnection (code={close_code}) for user {self.user_id}"
            )
            # 注意：disconnect 时连接已关闭，重连由客户端发起
            
        # 清理重连管理器
        if hasattr(self, 'reconnect_manager'):
            service = await get_reconnect_service()
            service.remove_manager(self.game_id, self.user_id)
        
        await super().disconnect(close_code)
    
    async def receive(self, text_data: str):
        """接收消息"""
        try:
            # 更新心跳（重要！）
            if hasattr(self, 'reconnect_manager'):
                self.reconnect_manager.update_heartbeat()
            
            # 解析消息
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # 处理心跳消息
            if message_type == 'HEARTBEAT':
                await self._handle_heartbeat(data)
                return
            
            # 处理其他消息...
            
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
    
    async def _handle_heartbeat(self, data: Dict[str, Any]):
        """处理心跳消息"""
        # 更新心跳
        if hasattr(self, 'reconnect_manager'):
            self.reconnect_manager.update_heartbeat()
        
        # 回复心跳确认
        await self.send(text_data=json.dumps({
            'type': 'HEARTBEAT_ACK',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    async def _on_reconnect_state_change(self, state: ReconnectState):
        """状态变化回调"""
        logger.info(
            f"Reconnect state changed to {state.value} "
            f"for user {self.user_id}"
        )
        
        # 根据状态执行不同操作
        if state == ReconnectState.RECONNECTED:
            # 重连成功，同步游戏状态
            await self._sync_game_state()
        elif state == ReconnectState.FAILED:
            # 重连失败，通知用户
            await self._notify_reconnect_failed()
    
    async def _on_reconnect_success(self):
        """重连成功回调"""
        logger.info(f"Reconnect success for user {self.user_id}")
        # 同步游戏状态
        await self._sync_game_state()
    
    async def _on_reconnect_failure(self):
        """重连失败回调"""
        logger.warning(f"Reconnect failed for user {self.user_id}")
        # 通知用户重连失败
        await self._notify_reconnect_failed()
    
    async def _sync_game_state(self):
        """同步游戏状态"""
        # 发送最新的游戏状态给客户端
        pass
    
    async def _notify_reconnect_failed(self):
        """通知重连失败"""
        await self.send(text_data=json.dumps({
            'type': 'RECONNECT_FAILED',
            'payload': {
                'message': '重连失败，请刷新页面重试'
            }
        }))
```

### 在 Consumer 中使用重连服务

```python
from games.websocket_reconnect_optimized import (
    ReconnectService,
    ReconnectConfig
)

class GameConsumer(BaseConsumer):
    """使用重连服务的 Consumer"""
    
    async def connect(self):
        await super().connect()
        
        # 获取重连服务实例
        self.reconnect_service = await ReconnectService.get_instance()
        
        # 创建自定义配置
        config = ReconnectConfig(
            initial_delay_ms=1000,      # 初始延迟 1 秒
            max_delay_ms=30000,         # 最大延迟 30 秒
            multiplier=2.0,             # 指数乘数
            max_attempts=10,            # 最大尝试 10 次
            jitter_ms=500,              # 抖动 500ms
            heartbeat_timeout_seconds=90,  # 心跳超时 90 秒
            max_history_size=100        # 最多 100 条历史
        )
        
        # 创建管理器
        self.reconnect_manager = self.reconnect_service.create_manager(
            consumer=self,
            game_id=self.game_id,
            user_id=self.user_id,
            config=config
        )
        
        await self.accept()
    
    async def disconnect(self, close_code: int):
        # 移除管理器
        if hasattr(self, 'reconnect_service'):
            self.reconnect_service.remove_manager(
                self.game_id, 
                self.user_id
            )
        
        await super().disconnect(close_code)
```

## API 参考

### ReconnectManager

管理单个 WebSocket 连接的重连逻辑。

#### 初始化

```python
manager = ReconnectManager(
    consumer=websocket_consumer,  # WebSocket consumer 实例
    game_id="game-123",           # 游戏 ID
    user_id="user-456",           # 用户 ID
    config=None                   # 可选的自定义配置
)
```

#### 心跳管理

```python
# 更新心跳（每次收到消息时调用）
manager.update_heartbeat()

# 检查心跳是否超时
if manager.is_heartbeat_timeout(timeout_seconds=90):
    logger.warning("Heartbeat timeout!")

# 获取连接健康状态
health = manager.get_connection_health()
# 返回: {
#     'is_healthy': True,
#     'last_heartbeat': '2024-01-01T00:00:00Z',
#     'time_since_heartbeat_seconds': 30.5,
#     'timeout_threshold_seconds': 90,
#     'state': 'connected',
#     'attempt': 0
# }
```

#### 重连控制

```python
# 启动重连
success = await manager.start_reconnect()

# 取消重连
manager.cancel()

# 重置重连管理器
manager.reset()
```

#### 状态和统计

```python
# 获取当前状态
print(manager.state)  # ReconnectState.CONNECTED

# 获取重连历史
history = manager.get_reconnect_history(limit=10)
# 返回: [{'timestamp': '...', 'state': 'reconnecting', ...}, ...]

# 导出历史为 JSON
json_history = manager.export_reconnect_history()

# 获取统计信息
stats = manager.get_stats()
# 返回: {
#     'total_connections': 5,
#     'total_reconnects': 3,
#     'successful_reconnects': 3,
#     'failed_reconnects': 0,
#     'current_streak': 3,
#     'max_streak': 3,
#     'avg_reconnect_time_ms': 1500.5,
#     'total_records': 10
# }

# 重置统计
manager.reset_stats()
```

#### 回调函数

```python
# 设置状态变化回调
async def on_state_change(state: ReconnectState):
    print(f"State changed to {state.value}")

manager.set_state_change_callback(on_state_change)

# 设置重连成功回调
async def on_success():
    print("Reconnect successful!")

manager.set_reconnect_success_callback(on_success)

# 设置重连失败回调
async def on_failure():
    print("Reconnect failed!")

manager.set_reconnect_failure_callback(on_failure)
```

### ReconnectService

集中管理所有重连管理器的单例服务。

#### 获取实例

```python
service = await ReconnectService.get_instance()
```

#### 管理器管理

```python
# 创建管理器
manager = service.create_manager(
    consumer=consumer,
    game_id="game-123",
    user_id="user-456",
    config=None  # 可选配置
)

# 获取管理器
manager = service.get_manager("game-123", "user-456")

# 移除管理器
service.remove_manager("game-123", "user-456")

# 获取所有管理器
all_managers = service.get_all_managers()

# 获取正在重连的连接
active_reconnects = service.get_active_reconnects()
# 返回: [{'game_id': '...', 'user_id': '...', 'attempt': 1, ...}, ...]
```

#### 批量操作

```python
# 启动重连
success = await service.start_reconnect("game-123", "user-456")

# 更新心跳
service.update_heartbeat("game-123", "user-456")

# 检查心跳超时
is_timeout = service.is_heartbeat_timeout(
    "game-123", 
    "user-456", 
    timeout_seconds=90
)

# 获取健康状态
health = service.get_connection_health("game-123", "user-456")

# 获取重连历史
history = service.get_reconnect_history(
    "game-123", 
    "user-456", 
    limit=10
)

# 获取统计信息
stats = service.get_stats("game-123", "user-456")

# 清理所有管理器
await service.cleanup()
```

### ReconnectConfig

重连配置类。

```python
config = ReconnectConfig(
    initial_delay_ms=1000,        # 初始延迟（毫秒）
    max_delay_ms=30000,           # 最大延迟（毫秒）
    multiplier=2.0,               # 指数退避乘数
    max_attempts=10,              # 最大重连次数
    jitter_ms=500,                # 随机抖动（毫秒）
    heartbeat_timeout_seconds=90, # 心跳超时阈值（秒）
    max_history_size=100          # 最大历史记录数
)

# 转换为字典
config_dict = config.to_dict()
```

### ReconnectState

重连状态枚举。

```python
from games.websocket_reconnect_optimized import ReconnectState

# 状态值
ReconnectState.CONNECTED      # "connected" - 已连接
ReconnectState.DISCONNECTED   # "disconnected" - 已断开
ReconnectState.RECONNECTING   # "reconnecting" - 重连中
ReconnectState.RECONNECTED    # "reconnected" - 重连成功
ReconnectState.FAILED         # "failed" - 重连失败

# 获取状态值
state_value = ReconnectState.CONNECTED.value  # "connected"
```

## 配置选项

### 推荐配置

#### 生产环境

```python
config = ReconnectConfig(
    initial_delay_ms=1000,        # 1 秒初始延迟
    max_delay_ms=30000,           # 30 秒最大延迟
    multiplier=2.0,               # 指数增长
    max_attempts=10,              # 最多 10 次尝试
    jitter_ms=500,                # 500ms 抖动
    heartbeat_timeout_seconds=90, # 90 秒超时
    max_history_size=100          # 保留 100 条历史
)
```

#### 开发环境

```python
config = ReconnectConfig(
    initial_delay_ms=500,         # 更短的初始延迟
    max_delay_ms=10000,           # 更短的最大延迟
    multiplier=2.0,
    max_attempts=5,               # 更少的尝试次数
    jitter_ms=200,
    heartbeat_timeout_seconds=30, # 更短的超时（便于调试）
    max_history_size=50
)
```

#### 高稳定性环境

```python
config = ReconnectConfig(
    initial_delay_ms=2000,        # 更长的初始延迟（减少服务器压力）
    max_delay_ms=60000,           # 1 分钟最大延迟
    multiplier=1.5,               # 更温和的增长
    max_attempts=20,              # 更多的尝试次数
    jitter_ms=1000,
    heartbeat_timeout_seconds=120,# 更长的超时
    max_history_size=200
)
```

## 前端集成

### JavaScript 示例

```javascript
class WebSocketClient {
    constructor(gameId, userId, token) {
        this.gameId = gameId;
        this.userId = userId;
        this.token = token;
        this.ws = null;
        this.reconnectState = 'connected';
        this.reconnectAttempt = 0;
    }
    
    connect() {
        const wsUrl = `ws://localhost:8000/ws/game/${this.gameId}/?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectState = 'connected';
            this.reconnectAttempt = 0;
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // 处理重连状态
            if (data.type === 'RECONNECT_STATUS') {
                this.handleReconnectStatus(data.payload);
                return;
            }
            
            // 处理心跳确认
            if (data.type === 'HEARTBEAT_ACK') {
                console.log('Heartbeat acknowledged');
                return;
            }
            
            // 处理其他消息...
        };
        
        this.ws.onclose = (event) => {
            console.log(`WebSocket closed (code=${event.code})`);
            
            // 非正常关闭时尝试重连
            if (event.code !== 1000) {
                this.scheduleReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleReconnectStatus(payload) {
        const { state, attempt, max_attempts, next_delay_ms, stats } = payload;
        
        this.reconnectState = state;
        this.reconnectAttempt = attempt;
        
        console.log(`Reconnect status: ${state}, attempt: ${attempt}/${max_attempts}`);
        console.log(`Next delay: ${next_delay_ms}ms`);
        console.log(`Stats:`, stats);
        
        // 更新 UI
        this.updateReconnectUI(state, attempt, max_attempts);
    }
    
    scheduleReconnect() {
        // 指数退避重连
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempt), 30000);
        const jitter = Math.random() * 500;
        
        console.log(`Scheduling reconnect in ${delay + jitter}ms`);
        
        setTimeout(() => {
            if (this.reconnectAttempt < 10) {
                this.reconnectAttempt++;
                this.connect();
            } else {
                console.error('Max reconnect attempts reached');
                this.showReconnectFailed();
            }
        }, delay + jitter);
    }
    
    updateReconnectUI(state, attempt, maxAttempts) {
        // 更新 UI 显示重连状态
        const statusElement = document.getElementById('reconnect-status');
        if (statusElement) {
            statusElement.textContent = `重连中... (${attempt}/${maxAttempts})`;
            statusElement.className = `reconnect-${state}`;
        }
    }
    
    showReconnectFailed() {
        alert('重连失败，请刷新页面重试');
    }
    
    // 发送心跳
    sendHeartbeat() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'HEARTBEAT',
                timestamp: new Date().toISOString()
            }));
        }
    }
    
    // 定期发送心跳
    startHeartbeat(intervalMs = 30000) {
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, intervalMs);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
    }
}

// 使用示例
const client = new WebSocketClient('game-123', 'user-456', 'your-token');
client.connect();
client.startHeartbeat(30000);  // 每 30 秒发送一次心跳
```

## 监控和调试

### 日志记录

重连模块会记录详细的日志：

```python
# 配置日志
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('games.websocket_reconnect')

# 日志输出示例:
# INFO: ReconnectService initialized
# INFO: Created reconnect manager for game-123:user-456
# INFO: Started reconnect attempt 1 for user user-456 in game game-123
# INFO: Waiting 1000ms before reconnect attempt 1 for user user-456
# INFO: Successfully reconnected for user user-456
```

### 监控指标

```python
# 获取所有活跃的重连
service = await ReconnectService.get_instance()
active = service.get_active_reconnects()

# 监控重连成功率
for key, manager in service.get_all_managers().items():
    stats = manager.get_stats()
    success_rate = (
        stats['successful_reconnects'] / stats['total_reconnects'] * 100
        if stats['total_reconnects'] > 0 else 100
    )
    logger.info(f"{key}: 成功率 {success_rate:.2f}%")
```

### 调试技巧

1. **检查心跳状态**:
   ```python
   health = manager.get_connection_health()
   print(f"连接健康：{health['is_healthy']}")
   print(f"距上次心跳：{health['time_since_heartbeat_seconds']}秒")
   ```

2. **查看重连历史**:
   ```python
   history = manager.get_reconnect_history(limit=20)
   for record in history:
       print(f"{record['timestamp']}: {record['state']} "
             f"(attempt={record['attempt']}, delay={record['delay_ms']}ms)")
   ```

3. **导出历史分析**:
   ```python
   json_data = manager.export_reconnect_history()
   with open('reconnect_history.json', 'w') as f:
       f.write(json_data)
   ```

## 最佳实践

### 1. 心跳管理

- **定期发送心跳**: 客户端应每 30 秒发送一次心跳
- **收到消息时更新**: 每次收到消息时更新心跳
- **合理设置超时**: 超时时间应为心跳间隔的 2-3 倍

### 2. 重连策略

- **使用指数退避**: 避免频繁重连给服务器造成压力
- **添加随机抖动**: 避免多个客户端同时重连
- **限制最大次数**: 避免无限重连

### 3. 状态管理

- **及时清理**: 断开连接时清理重连管理器
- **状态同步**: 重连成功后同步最新状态
- **用户提示**: 及时向用户显示重连状态

### 4. 错误处理

- **捕获异常**: 重连逻辑中捕获所有异常
- **记录日志**: 详细记录重连过程
- **优雅降级**: 重连失败时提供友好的错误提示

## 常见问题

### Q: 重连一直失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. 服务器是否在线
3. Token 是否过期
4. 查看日志了解具体错误原因

### Q: 如何调整重连参数？

A: 创建自定义的 `ReconnectConfig`:
```python
config = ReconnectConfig(
    initial_delay_ms=2000,
    max_delay_ms=60000,
    max_attempts=20
)
manager = ReconnectManager(consumer, game_id, user_id, config)
```

### Q: 重连成功后需要做什么？

A: 重连成功后应该：
1. 同步最新的游戏状态
2. 恢复用户界面
3. 通知房间内其他用户

### Q: 如何监控重连性能？

A: 使用统计信息：
```python
stats = manager.get_stats()
print(f"成功率：{stats['successful_reconnects'] / stats['total_reconnects'] * 100:.2f}%")
print(f"平均重连时间：{stats['avg_reconnect_time_ms']:.2f}ms")
```

## 版本历史

### v1.0.0 (2024-01-01)

- 初始版本
- 实现断线检测机制
- 实现自动重连逻辑（指数退避）
- 实现重连状态管理
- 实现重连历史记录
- 实现连接统计

## 相关文件

- 实现代码：`src/backend/games/websocket_reconnect_optimized.py`
- 测试文件：`src/backend/tests/unit/games/test_websocket_reconnect.py`
- Consumer 基类：`src/backend/websocket/consumers.py`

## 联系支持

如有问题或建议，请联系开发团队。
