# WebSocket 统一配置中心

**版本**: 1.0.0  
**创建时间**: 2026-03-03  
**状态**: ✅ 已完成

---

## 📋 概述

WebSocket 统一配置中心为中国象棋项目提供统一的 WebSocket 路由、配置、中间件和基础 Consumer 类，便于维护和扩展。

### 背景

当前项目有多个 WebSocket 模块：
- 游戏对弈：`/ws/game/{game_id}/`
- AI 对弈：`/ws/ai/game/{game_id}/`
- 匹配系统：`/ws/matchmaking/`

统一配置中心将这些模块的路由和配置集中管理，提供：
- 统一认证中间件（JWT Token 验证）
- 统一权限控制
- 统一心跳和超时配置
- 统一日志和监控
- 可复用的基础 Consumer 类

---

## 🏗️ 模块结构

```
src/backend/websocket/
├── __init__.py          # 模块导出
├── config.py            # WebSocket 配置（心跳、超时、认证、日志等）
├── middleware.py        # WebSocket 中间件（JWT 认证、权限、日志、性能监控）
├── consumers.py         # 基础 Consumer 类（复用逻辑）
└── routing.py           # 统一 WebSocket 路由配置
```

---

## 🚀 核心功能

### 1. WebSocket 路由配置

**文件**: `websocket/routing.py`

统一管理所有 WebSocket 路由：

```python
from websocket.routing import websocket_urlpatterns

# 在 config/asgi.py 中使用
application = ProtocolTypeRouter({
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

**路由列表**：

| 路由 | 说明 | 参数 | 认证 |
|------|------|------|------|
| `/ws/game/{game_id}/` | 游戏对弈 | game_id | ✅ |
| `/ws/ai/game/{game_id}/` | AI 对弈 | game_id | ✅ |
| `/ws/matchmaking/` | 匹配系统 | 无 | ✅ |

### 2. 统一认证中间件

**文件**: `websocket/middleware.py`

提供 JWT Token 验证、用户信息注入、连接权限控制：

```python
from websocket.middleware import JWTAuthMiddleware

class GameConsumer(BaseConsumer):
    async def connect(self):
        # 使用统一认证中间件
        user = await JWTAuthMiddleware().authenticate(self.scope)
        if not user:
            await self.close(code=4001, reason='Invalid token')
            return
        
        self.user = user
        # 继续连接逻辑...
```

**认证方式**：
- URL 参数：`?token=eyJhbG...`
- Header: `Authorization: Bearer eyJhbG...`

### 3. 心跳和超时配置

**文件**: `websocket/config.py`

统一配置心跳和超时参数：

```python
from websocket.config import WebSocketConfig

config = WebSocketConfig()

# 心跳配置
config.HEARTBEAT_INTERVAL = 30  # 30 秒
config.TIMEOUT_THRESHOLD = 90   # 90 秒超时
config.MAX_MISSED_HEARTBEATS = 3

# 超时配置
config.CONNECT_TIMEOUT = 30
config.MESSAGE_TIMEOUT = 10

# 重连配置
config.ALLOW_RECONNECT = True
config.MAX_RECONNECT_ATTEMPTS = 5
```

**心跳机制**：
- 客户端每 30 秒发送一次心跳
- 90 秒无心跳判定掉线
- 支持断线重连（指数退避）

### 4. 日志和监控

**文件**: `websocket/middleware.py`

提供统一的日志记录和性能监控：

```python
from websocket.middleware import LoggingMiddleware, PerformanceMonitorMiddleware

logging = LoggingMiddleware()
perf_monitor = PerformanceMonitorMiddleware()

# 记录连接日志
logging.log_connection(user, game_id, 'game')

# 记录消息日志
logging.log_message('MOVE', 'inbound', user_id, game_id)

# 性能监控
with perf_monitor.measure('process_move'):
    # 执行操作
    pass
```

**日志类型**：
- 连接日志（LOG_CONNECTIONS）
- 消息日志（LOG_MESSAGES）
- 错误日志（LOG_ERRORS）
- 性能日志（LOG_PERFORMANCE）

### 5. 基础 Consumer 类

**文件**: `websocket/consumers.py`

提供可复用的 Consumer 基类：

```python
from websocket.consumers import BaseConsumer

class GameConsumer(BaseConsumer):
    async def connect(self):
        # 使用父类的认证方法
        authenticated = await self.authenticate()
        if not authenticated:
            return
        
        self.resource_id = self.scope['url_route']['kwargs']['game_id']
        self.resource_type = 'game'
        
        await super().connect()
    
    async def receive(self, text_data):
        # 使用父类的消息处理方法
        await super().receive(text_data)
        
        # 处理具体消息类型
        data = json.loads(text_data)
        if data['type'] == 'MOVE':
            await self.handle_move(data)
```

**提供功能**：
- 心跳追踪和管理
- 统一认证处理
- 统一错误处理
- 统一日志记录
- 性能监控
- 消息格式化

---

## 📖 使用示例

### 创建新的 WebSocket Consumer

```python
from websocket.consumers import BaseConsumer
from websocket.middleware import PermissionMiddleware
import json

class ChatConsumer(BaseConsumer):
    """聊天室 Consumer"""
    
    async def connect(self):
        # 认证
        authenticated = await self.authenticate()
        if not authenticated:
            return
        
        # 设置资源信息
        self.resource_id = self.scope['url_route']['kwargs']['room_id']
        self.resource_type = 'chat'
        
        # 加入房间组
        self.room_group_name = f'chat_{self.resource_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        await super().connect()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await super().disconnect(close_code)
    
    async def receive(self, text_data):
        await super().receive(text_data)
        
        data = json.loads(text_data)
        
        if data['type'] == 'CHAT':
            await self.handle_chat(data)
    
    async def handle_chat(self, data):
        """处理聊天消息"""
        message = data['payload'].get('message')
        
        # 广播消息
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data': {
                    'user_id': self.user['id'],
                    'username': self.user['username'],
                    'message': message
                }
            }
        )
    
    async def chat_message(self, event):
        """广播聊天消息"""
        await self.send(text_data=self._format_message(
            'CHAT_MESSAGE',
            event['data']
        ))
```

### 添加新路由

在 `websocket/routing.py` 中添加：

```python
from .consumers import ChatConsumer

websocket_urlpatterns = [
    # ... 现有路由
    
    # 聊天室
    re_path(
        r'ws/chat/(?P<room_id>[^/]+)/$',
        ChatConsumer.as_asgi(),
        name='ws-chat'
    ),
]

# 添加路由配置
ROUTE_CONFIG['chat'] = {
    'pattern': r'ws/chat/(?P<room_id>[^/]+)/$',
    'consumer': 'websocket.consumers.ChatConsumer',
    'description': '聊天室',
    'auth_required': True,
    'parameters': ['room_id'],
}
```

---

## 🧪 测试

### 运行单元测试

```bash
cd src/backend
PYTHONPATH=. python3 -m pytest ../../tests/unit/websocket/test_config.py -v
```

### 运行集成测试

```bash
cd src/backend
PYTHONPATH=. python3 -m pytest ../../tests/integration/websocket/test_websocket_config.py -v
```

### 测试覆盖率

```bash
cd src/backend
PYTHONPATH=. python3 -m pytest ../../tests/unit/websocket/ --cov=websocket --cov-report=html
```

---

## 📊 配置选项

### WebSocketConfig 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `HEARTBEAT_INTERVAL` | 30 | 心跳间隔（秒） |
| `TIMEOUT_THRESHOLD` | 90 | 超时阈值（秒） |
| `MAX_MISSED_HEARTBEATS` | 3 | 最大丢失心跳次数 |
| `CONNECT_TIMEOUT` | 30 | 连接超时（秒） |
| `MESSAGE_TIMEOUT` | 10 | 消息处理超时（秒） |
| `JWT_ALGORITHM` | 'HS256' | JWT 算法 |
| `LOG_CONNECTIONS` | True | 记录连接日志 |
| `LOG_MESSAGES` | True | 记录消息日志 |
| `LOG_ERRORS` | True | 记录错误日志 |
| `LOG_PERFORMANCE` | True | 记录性能日志 |
| `MAX_CONNECTIONS_PER_USER` | 3 | 单用户最大连接数 |
| `MAX_GLOBAL_CONNECTIONS` | 10000 | 全局最大连接数 |
| `MAX_MESSAGE_SIZE` | 65536 | 最大消息大小（字节） |

---

## 🔧 更新各模块引用

### games/consumers.py

已更新为使用统一配置：

```python
from websocket.consumers import BaseConsumer
from websocket.middleware import JWTAuthMiddleware

class GameConsumer(BaseConsumer):
    # ... 使用统一配置
```

### ai_engine/consumers.py

已更新为使用统一配置：

```python
from websocket.consumers import BaseConsumer

class AIGameConsumer(BaseConsumer):
    # ... 使用统一配置
```

### matchmaking/consumers.py

已创建并使用统一配置：

```python
from websocket.consumers import BaseConsumer

class MatchmakingConsumer(BaseConsumer):
    # ... 使用统一配置
```

---

## 📝 开发规范

### 1. 所有 Consumer 必须继承 BaseConsumer

```python
# ✅ 正确
from websocket.consumers import BaseConsumer

class MyConsumer(BaseConsumer):
    pass

# ❌ 错误
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    pass
```

### 2. 使用统一认证中间件

```python
# ✅ 正确
authenticated = await self.authenticate()
if not authenticated:
    return

# ❌ 错误（重复实现认证逻辑）
token = self._extract_token()
user = self._verify_token(token)
```

### 3. 使用统一日志记录

```python
# ✅ 正确
self.logging_middleware.log_connection(user, resource_id, 'game')

# ❌ 错误（直接使用 print）
print(f"User {user} connected")
```

### 4. 遵循消息格式规范

```python
# ✅ 正确
await self.send(text_data=self._format_message('MY_TYPE', {'key': 'value'}))

# ❌ 错误（手动拼接 JSON）
await self.send(text_data=json.dumps({'type': 'MY_TYPE', 'data': {...}}))
```

---

## 🚨 错误码规范

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| `4001` | Invalid or expired token | 重新登录 |
| `4002` | Authentication failed | 检查认证信息 |
| `4003` | Not authorized | 检查权限 |
| `INVALID_JSON` | Invalid JSON format | 检查消息格式 |
| `INVALID_MESSAGE_TYPE` | Unknown message type | 检查消息类型 |
| `INTERNAL_ERROR` | Internal server error | 联系管理员 |

---

## 📈 性能优化建议

### 1. 使用连接池

```python
# 在 settings.py 中配置
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

### 2. 启用消息压缩

```python
# 对于大消息，使用压缩
import gzip
compressed = gzip.compress(json.dumps(data).encode())
await self.send(bytes_data=compressed)
```

### 3. 限制广播频率

```python
# 使用节流
from datetime import datetime, timedelta

last_broadcast = None

async def broadcast_update(self):
    global last_broadcast
    now = datetime.now()
    
    if last_broadcast and (now - last_broadcast).total_seconds() < 1:
        return  # 限制每秒最多一次广播
    
    last_broadcast = now
    # 执行广播...
```

---

## 🔒 安全建议

### 1. 始终验证 Token

```python
# ✅ 正确
authenticated = await self.authenticate()
if not authenticated:
    await self.close(code=4001)
    return

# ❌ 错误（跳过认证）
async def connect(self):
    await self.accept()  # 危险！
```

### 2. 检查资源权限

```python
# ✅ 正确
if not self.check_permission(game_data):
    await self.close(code=4003)
    return

# ❌ 错误（不检查权限）
async def connect(self):
    await self.accept()  # 任何人都可以加入
```

### 3. 限制消息大小

```python
# 在 config.py 中配置
config.MAX_MESSAGE_SIZE = 65536  # 64KB

# 在 receive 中检查
if len(text_data) > self.config.MAX_MESSAGE_SIZE:
    await self._send_error('MESSAGE_TOO_LARGE', 'Message exceeds size limit')
    return
```

---

## 📚 相关文档

- [DEVELOPMENT-CONSTRAINTS.md](./DEVELOPMENT-CONSTRAINTS.md) - 开发约束规范
- [SHARED-CONTEXT.md](./SHARED-CONTEXT.md) - 共享上下文
- [architecture.md](./architecture.md) - 系统架构设计

---

## ✅ 验收标准

- [x] 创建统一路由配置（routing.py）
- [x] 创建统一配置文件（config.py）
- [x] 创建统一中间件（middleware.py）
- [x] 创建基础 Consumer 类（consumers.py）
- [x] 实现 JWT 认证中间件
- [x] 实现权限检查中间件
- [x] 实现心跳和超时配置
- [x] 实现日志和监控
- [x] 更新 games/consumers.py 引用统一配置
- [x] 更新 ai_engine/consumers.py 引用统一配置
- [x] 创建 matchmaking/consumers.py 引用统一配置
- [x] 编写单元测试（16 个测试全部通过）
- [x] 编写集成测试
- [x] 编写使用文档

---

**WebSocket 统一配置中心已完成** ✅
