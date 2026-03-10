# WebSocket 断线重连优化

## 概述

本文档描述了中国象棋游戏 WebSocket 连接的断线重连优化实现。通过实现自动断线检测、指数退避重连、状态管理和历史记录功能，提升了用户体验和系统稳定性。

## 问题背景

在实时对战游戏中，WebSocket 连接可能因以下原因中断：

- 网络波动
- 服务器重启
- 客户端切换网络（WiFi ↔ 4G/5G）
- 设备休眠
- 长时间无活动

原有实现缺乏完善的断线重连机制，导致用户掉线后需要手动刷新页面重新连接，影响游戏体验。

## 解决方案

### 核心功能

1. **断线检测机制**
   - 心跳监测（30 秒间隔）
   - 超时判定（90 秒无心跳）
   - 后台心跳监测任务

2. **自动重连逻辑**
   - 指数退避算法
   - 随机抖动避免并发风暴
   - 最大重连次数限制

3. **重连状态管理**
   - 5 种状态：CONNECTED, DISCONNECTED, RECONNECTING, RECONNECTED, FAILED
   - 状态广播给房间内其他用户
   - 前端实时显示重连状态

4. **重连历史记录**
   - 记录每次重连事件
   - 统计连接质量指标
   - 支持查询历史数据

### 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      GameConsumer                        │
│  ┌─────────────────┐    ┌──────────────────────────┐   │
│  │ heartbeat_task  │    │  reconnect_manager       │   │
│  │ (后台监测)      │───▶│  (ReconnectManager)      │   │
│  └─────────────────┘    └──────────────────────────┘   │
│                            │                             │
│                            ▼                             │
│                   ┌─────────────────┐                   │
│                   │ ReconnectService│                   │
│                   │ (单例，管理所有) │                   │
│                   └─────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## 实现细节

### 1. 指数退避算法

```python
# 重连配置
INITIAL_DELAY_MS = 1000      # 初始延迟 1 秒
MAX_DELAY_MS = 30000         # 最大延迟 30 秒
MULTIPLIER = 2.0             # 指数乘数
MAX_ATTEMPTS = 10            # 最大尝试次数
JITTER_MS = 500              # 随机抖动

# 计算公式
delay = INITIAL_DELAY_MS * (MULTIPLIER ** attempt)
delay = min(delay, MAX_DELAY_MS)
delay += random(0, JITTER_MS)
```

**重连延迟示例：**

| 尝试次数 | 基础延迟 | + 随机抖动 | 总延迟范围 |
|---------|---------|-----------|-----------|
| 1       | 1000ms  | 0-500ms   | 1000-1500ms |
| 2       | 2000ms  | 0-500ms   | 2000-2500ms |
| 3       | 4000ms  | 0-500ms   | 4000-4500ms |
| 4       | 8000ms  | 0-500ms   | 8000-8500ms |
| 5       | 16000ms | 0-500ms   | 16000-16500ms |
| 6+      | 30000ms | 0-500ms   | 30000-30500ms |

### 2. 心跳监测

```python
# 后台监测任务
async def _heartbeat_monitor(self):
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)  # 30 秒
        
        if reconnect_manager.is_heartbeat_timeout(TIMEOUT_THRESHOLD):
            # 启动自动重连
            await reconnect_service.start_reconnect(game_id, user_id)
```

### 3. 状态管理

```python
class ReconnectState(Enum):
    CONNECTED = "connected"      # 连接正常
    DISCONNECTED = "disconnected" # 已断开
    RECONNECTING = "reconnecting" # 重连中
    RECONNECTED = "reconnected"   # 重连成功
    FAILED = "failed"            # 重连失败
```

### 4. 消息协议

#### 客户端 → 服务端

**请求重连：**
```json
{
  "type": "RECONNECT_REQUEST",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**获取重连历史：**
```json
{
  "type": "GET_RECONNECT_HISTORY",
  "payload": {
    "limit": 10
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 服务端 → 客户端

**重连状态广播：**
```json
{
  "type": "RECONNECT_STATUS",
  "payload": {
    "state": "reconnecting",
    "attempt": 2,
    "max_attempts": 10,
    "next_delay_ms": 2350,
    "stats": {
      "total_connections": 5,
      "successful_reconnects": 3,
      "current_streak": 2
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**重连历史响应：**
```json
{
  "type": "RECONNECT_HISTORY",
  "payload": {
    "history": [
      {
        "timestamp": "2024-01-01T11:55:00Z",
        "state": "reconnected",
        "attempt": 1,
        "delay_ms": 1200,
        "duration_ms": 1500
      }
    ],
    "stats": {
      "total_connections": 5,
      "total_reconnects": 3,
      "successful_reconnects": 3,
      "failed_reconnects": 0
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 文件结构

```
projects/chinese-chess/src/backend/
├── games/
│   ├── consumers.py              # WebSocket Consumer（集成重连）
│   └── websocket_reconnect.py    # 重连服务（核心实现）
├── tests/unit/games/
│   └── test_websocket_reconnect.py  # 单元测试
└── docs/websocket/
    └── reconnect-optimization.md    # 本文档
```

## 使用方法

### 后端集成

1. **Consumer 初始化重连管理器**

```python
from games.websocket_reconnect import get_reconnect_service

async def connect(self):
    # ... 认证逻辑 ...
    
    # 初始化重连管理器
    reconnect_service = await get_reconnect_service()
    self.reconnect_manager = reconnect_service.create_manager(
        self, self.game_id, str(user['id'])
    )
    
    # 启动心跳监测
    self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
```

2. **处理心跳**

```python
async def _handle_heartbeat(self, data):
    self.last_heartbeat = timezone.now()
    
    if self.reconnect_manager and self.user:
        self.reconnect_manager.update_heartbeat()
    
    # ... 响应心跳 ...
```

3. **清理资源**

```python
async def disconnect(self, close_code):
    # 取消心跳任务
    if self.heartbeat_task:
        self.heartbeat_task.cancel()
    
    # 清理重连管理器
    if self.reconnect_manager:
        self.reconnect_manager.cancel()
        reconnect_service.remove_manager(self.game_id, str(self.user['id']))
    
    # ... 其他清理逻辑 ...
```

### 前端使用

1. **监听重连状态**

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'RECONNECT_STATUS') {
    const { state, attempt, next_delay_ms } = data.payload;
    
    switch (state) {
      case 'reconnecting':
        showReconnectToast(`正在重连... (尝试 ${attempt}/10, ${next_delay_ms}ms 后)`);
        break;
      case 'reconnected':
        showSuccessToast('重连成功！');
        break;
      case 'failed':
        showErrorToast('重连失败，请刷新页面');
        break;
    }
  }
};
```

2. **主动请求重连**

```javascript
// 检测到网络断开时
function onNetworkDisconnect() {
  ws.send(JSON.stringify({
    type: 'RECONNECT_REQUEST',
    timestamp: new Date().toISOString()
  }));
}
```

3. **查看重连历史**

```javascript
// 请求重连历史
function getReconnectHistory() {
  ws.send(JSON.stringify({
    type: 'GET_RECONNECT_HISTORY',
    payload: { limit: 10 },
    timestamp: new Date().toISOString()
  }));
}

// 接收历史数据
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'RECONNECT_HISTORY') {
    displayReconnectHistory(data.payload.history);
  }
};
```

## 配置参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `HEARTBEAT_INTERVAL` | 30 秒 | 心跳发送间隔 |
| `TIMEOUT_THRESHOLD` | 90 秒 | 心跳超时阈值 |
| `INITIAL_DELAY_MS` | 1000ms | 初始重连延迟 |
| `MAX_DELAY_MS` | 30000ms | 最大重连延迟 |
| `MULTIPLIER` | 2.0 | 指数退避乘数 |
| `MAX_ATTEMPTS` | 10 | 最大重连次数 |
| `JITTER_MS` | 500ms | 随机抖动范围 |

## 测试

### 运行单元测试

```bash
cd projects/chinese-chess/src/backend
pytest tests/unit/games/test_websocket_reconnect.py -v
```

### 测试场景

1. **正常连接**
   - 验证初始状态为 CONNECTED
   - 心跳正常更新

2. **心跳超时自动重连**
   - 模拟 90 秒无心跳
   - 验证自动触发重连
   - 验证状态广播

3. **重连成功**
   - 验证重连后状态恢复 CONNECTED
   - 验证统计信息更新

4. **重连失败**
   - 模拟连续失败
   - 验证达到最大次数后状态为 FAILED

5. **并发重连**
   - 多个用户同时掉线
   - 验证随机抖动避免并发风暴

## 性能影响

- **内存占用**: 每个连接约增加 5-10KB（重连管理器和历史记录）
- **CPU 占用**: 心跳监测任务每 30 秒唤醒一次，影响可忽略
- **网络流量**: 重连状态广播增加少量流量（每次约 200-500 bytes）

## 监控与告警

### 关键指标

1. **重连成功率**
   ```
   重连成功率 = successful_reconnects / total_reconnects * 100%
   告警阈值：< 80%
   ```

2. **平均重连时间**
   ```
   平均重连时间 = Σ(duration_ms) / successful_reconnects
   告警阈值：> 5000ms
   ```

3. **连续失败次数**
   ```
   告警阈值：current_streak < 0 且 failed_reconnects > 5
   ```

### 日志记录

```python
# 关键日志
logger.info(f"Started reconnect attempt {attempt} for user {user_id}")
logger.warning(f"Heartbeat timeout detected for user {user_id}")
logger.error(f"All reconnect attempts failed for user {user_id}")
```

## 未来优化

1. **持久化重连历史**
   - 将重连记录存入数据库
   - 支持长期趋势分析

2. **智能重连策略**
   - 根据网络质量动态调整参数
   - 学习用户网络模式

3. **断线续传**
   - 保存断线前的游戏状态
   - 重连后快速同步

4. **多路径重连**
   - 同时尝试多个连接路径
   - 选择最优连接

## 参考资料

- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Exponential Backoff Pattern](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

## 变更日志

### v1.0.0 (2024-03-06)

- ✅ 实现断线检测机制
- ✅ 实现指数退避重连
- ✅ 实现重连状态管理
- ✅ 实现重连历史记录
- ✅ 编写单元测试
- ✅ 编写文档
