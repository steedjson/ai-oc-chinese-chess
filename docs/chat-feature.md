# 中国象棋聊天系统功能文档

**版本**: 1.0  
**创建日期**: 2026-03-05  
**状态**: ✅ 已完成

---

## 功能概述

聊天系统为中国象棋对局提供实时通信功能，支持：

- **对局内聊天**：游戏玩家之间的实时交流
- **观战聊天**：观战者之间的讨论交流
- **消息历史记录**：保存和查看历史消息
- **表情支持**：简单的表情符号发送
- **消息限流**：防止刷屏滥用

---

## 系统架构

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   前端      │         │   后端      │         │   数据库    │
│  (React)    │◄───────►│  (Django)   │◄───────►│ (PostgreSQL)│
│             │  WS/REST│             │  ORM    │             │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                        ┌─────────────┐
                        │   Redis     │
                        │ (Channel Layer)│
                        └─────────────┘
```

---

## 数据模型

### ChatMessage 模型

位于：`src/backend/games/chat.py`

```python
class ChatMessage(models.Model):
    id = BigAutoField                    # 主键
    message_uuid = UUIDField             # 消息唯一标识
    game = ForeignKey(Game)              # 关联对局
    sender = ForeignKey(User)            # 发送者（系统消息可为空）
    content = TextField                  # 消息内容
    message_type = CharField             # 消息类型（text/system/emoji）
    room_type = CharField                # 房间类型（game/spectator）
    is_deleted = BooleanField            # 软删除标记
    created_at = DateTimeField           # 创建时间
    updated_at = DateTimeField           # 更新时间
```

**消息类型枚举**：
- `text` - 文本消息
- `system` - 系统消息
- `emoji` - 表情消息

**房间类型枚举**：
- `game` - 对局房间（玩家聊天）
- `spectator` - 观战房间（观战者聊天）

**约束**：
- 消息内容最大长度：500 字符
- 消息限流：每条消息间隔至少 2 秒
- 软删除：删除消息时仅标记 `is_deleted=True`

---

## REST API

### 1. 发送聊天消息

```http
POST /api/v1/chat/games/{game_id}/send/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
    "content": "你好！",
    "message_type": "text",  // text, system, emoji
    "room_type": "game"      // game, spectator
}

Response (201):
{
    "success": true,
    "message": {
        "id": "uuid",
        "game_id": "uuid",
        "sender": {
            "id": "user_id",
            "username": "username"
        },
        "content": "你好！",
        "message_type": "text",
        "room_type": "game",
        "created_at": "2026-03-05T12:00:00"
    }
}
```

**错误响应**：
```json
{
    "success": false,
    "error": "消息内容不能为空"
}
```

### 2. 获取聊天历史

```http
GET /api/v1/chat/games/{game_id}/history/?limit=50&before=2026-03-05T12:00:00&room_type=game
Authorization: Bearer <token>

Query Parameters:
- limit: 返回数量限制（默认 50，最大 100）
- before: 分页游标（ISO8601 时间戳）
- room_type: 房间类型（game 或 spectator，默认 game）

Response (200):
{
    "success": true,
    "messages": [
        {
            "id": "uuid",
            "sender": {...},
            "content": "...",
            "message_type": "text",
            "created_at": "ISO8601"
        }
    ],
    "has_more": true
}
```

### 3. 删除聊天消息

```http
DELETE /api/v1/chat/messages/{message_uuid}/delete/
Authorization: Bearer <token>

Response (200):
{
    "success": true,
    "message": "消息已删除"
}
```

**权限**：只有消息发送者或管理员可删除

### 4. 获取聊天统计

```http
GET /api/v1/chat/games/{game_id}/stats/
Authorization: Bearer <token>

Response (200):
{
    "success": true,
    "stats": {
        "total_messages": 100,
        "game_messages": 80,
        "spectator_messages": 20
    }
}
```

---

## WebSocket 接口

### 连接聊天房间

```javascript
// 对局聊天
const ws = new WebSocket(
    `ws://localhost:8000/ws/chat/game/${game_id}/?token=${jwt_token}`
);

// 观战聊天
const ws = new WebSocket(
    `ws://localhost:8000/ws/chat/spectator/${game_id}/?token=${jwt_token}`
);
```

### 消息类型

#### 客户端 → 服务端

**发送聊天消息**：
```javascript
ws.send(JSON.stringify({
    type: 'CHAT_MESSAGE',
    content: '你好！',
    message_type: 'text'  // text, emoji
}));
```

**获取历史消息**：
```javascript
ws.send(JSON.stringify({
    type: 'GET_HISTORY',
    limit: 50,
    before: '2026-03-05T12:00:00'
}));
```

**删除消息**：
```javascript
ws.send(JSON.stringify({
    type: 'DELETE_MESSAGE',
    message_id: 'uuid'
}));
```

**心跳**：
```javascript
ws.send(JSON.stringify({
    type: 'HEARTBEAT'
}));
```

#### 服务端 → 客户端

**欢迎消息**：
```javascript
{
    type: 'WELCOME',
    payload: {
        room_type: 'game',
        game_id: 'uuid',
        username: 'username',
        timestamp: 'ISO8601'
    }
}
```

**聊天消息广播**：
```javascript
{
    type: 'CHAT_MESSAGE',
    payload: {
        success: true,
        message: {
            id: 'uuid',
            sender: {...},
            content: '...',
            message_type: 'text',
            created_at: 'ISO8601'
        }
    }
}
```

**历史消息**：
```javascript
{
    type: 'CHAT_HISTORY',
    payload: {
        success: true,
        messages: [...],
        room_type: 'game'
    }
}
```

**系统消息**：
```javascript
{
    type: 'SYSTEM_MESSAGE',
    payload: {
        content: '游戏开始',
        message_type: 'system'
    }
}
```

**消息删除通知**：
```javascript
{
    type: 'MESSAGE_DELETED',
    payload: {
        success: true,
        message_id: 'uuid'
    }
}
```

**心跳响应**：
```javascript
{
    type: 'HEARTBEAT',
    payload: {
        acknowledged: true,
        timestamp: 'ISO8601'
    }
}
```

**错误消息**：
```javascript
{
    type: 'ERROR',
    payload: {
        success: false,
        error: {
            code: 'RATE_LIMITED',
            message: '发送频率过快，请等待 1.5 秒'
        }
    }
}
```

### 错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| `EMPTY_MESSAGE` | 消息内容为空 | 提示用户输入内容 |
| `MESSAGE_TOO_LONG` | 消息超长 | 限制在 500 字符内 |
| `RATE_LIMITED` | 发送频率过快 | 等待后重试 |
| `INVALID_EMOJI` | 不支持的表情 | 使用允许的表情 |
| `INVALID_MESSAGE_TYPE` | 无效的消息类型 | 使用 text/emoji |
| `INVALID_ROOM_TYPE` | 无效的房间类型 | 使用 game/spectator |
| `NO_PERMISSION` | 无权限 | 检查用户权限 |
| `NOT_PARTICIPANT` | 非游戏参与者 | 只能观战或加入其他游戏 |
| `NOT_SPECTATOR` | 非观战者 | 加入观战或离开 |
| `GAME_NOT_FOUND` | 游戏不存在 | 检查游戏 ID |
| `DELETE_FAILED` | 删除失败 | 检查权限 |

---

## 权限控制

### 对局聊天（room_type=game）

| 操作 | 游戏参与者 | 观战者 | 管理员 |
|------|-----------|--------|--------|
| 发送消息 | ✅ | ❌ | ✅ |
| 查看历史 | ✅ | ❌ | ✅ |
| 删除自己消息 | ✅ | ❌ | ✅ |
| 删除他人消息 | ❌ | ❌ | ✅ |

### 观战聊天（room_type=spectator）

| 操作 | 游戏参与者 | 观战者 | 管理员 |
|------|-----------|--------|--------|
| 发送消息 | ❌ | ✅ | ✅ |
| 查看历史 | ❌ | ✅ | ✅ |
| 删除自己消息 | ❌ | ✅ | ✅ |
| 删除他人消息 | ❌ | ❌ | ✅ |

---

## 功能特性

### 1. 消息限流

防止用户刷屏：

- **限流间隔**：2 秒
- **限流范围**：每个用户每个房间独立计算
- **错误提示**：返回剩余等待时间

```python
# 限流检查逻辑
if time_since_last_message < 2 seconds:
    return error("发送频率过快，请等待 X 秒")
```

### 2. 表情支持

支持常用表情符号：

```python
ALLOWED_EMOJIS = [
    '😀', '😂', '😍', '🥰', '😎', '🤔', '👍', '👎',
    '❤️', '🔥', '✨', '🎉', '🏆', '♟️', '🎯', '💪',
    '😅', '😭', '😱', '🙏', '💯', '🚀', '⭐', '🌟',
]
```

### 3. 消息历史分页

支持游标分页：

```javascript
// 第一次请求
GET /api/v1/chat/games/{game_id}/history/?limit=50

// 加载更多
GET /api/v1/chat/games/{game_id}/history/?limit=50&before=2026-03-05T12:00:00
```

### 4. 软删除

消息删除采用软删除：

- 标记 `is_deleted=True`
- 查询时自动过滤已删除消息
- 保留数据可追溯

### 5. 实时广播

使用 Django Channels 实现实时消息广播：

```python
# 广播消息到房间
await channel_layer.group_send(
    f'chat_{room_type}_{game_id}',
    {'type': 'chat_message', 'message': message_data}
)
```

---

## 前端集成示例

### React 组件

```jsx
import { useState, useEffect, useRef } from 'react';

function ChatRoom({ gameId, roomType = 'game' }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const ws = useRef(null);
    
    useEffect(() => {
        // 连接 WebSocket
        const token = localStorage.getItem('token');
        ws.current = new WebSocket(
            `ws://localhost:8000/ws/chat/${roomType}/${gameId}/?token=${token}`
        );
        
        ws.current.onopen = () => {
            console.log('Chat connected');
        };
        
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch(data.type) {
                case 'WELCOME':
                    console.log('Welcome to chat');
                    break;
                    
                case 'CHAT_HISTORY':
                    setMessages(data.payload.messages);
                    break;
                    
                case 'CHAT_MESSAGE':
                    setMessages(prev => [...prev, data.payload.message]);
                    break;
                    
                case 'MESSAGE_DELETED':
                    setMessages(prev => prev.filter(
                        m => m.id !== data.payload.message_id
                    ));
                    break;
            }
        };
        
        return () => ws.current?.close();
    }, [gameId, roomType]);
    
    const sendMessage = () => {
        if (!input.trim()) return;
        
        ws.current.send(JSON.stringify({
            type: 'CHAT_MESSAGE',
            content: input,
            message_type: 'text'
        }));
        
        setInput('');
    };
    
    const sendEmoji = (emoji) => {
        ws.current.send(JSON.stringify({
            type: 'CHAT_MESSAGE',
            content: emoji,
            message_type: 'emoji'
        }));
    };
    
    return (
        <div className="chat-room">
            <div className="message-list">
                {messages.map(msg => (
                    <div key={msg.id} className={`message ${msg.message_type}`}>
                        <span className="sender">{msg.sender?.username || 'System'}</span>
                        <span className="content">{msg.content}</span>
                    </div>
                ))}
            </div>
            
            <div className="input-area">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="输入消息..."
                />
                <button onClick={sendMessage}>发送</button>
                <div className="emoji-picker">
                    {['😀', '😂', '👍', '❤️', '🔥'].map(emoji => (
                        <button key={emoji} onClick={() => sendEmoji(emoji)}>
                            {emoji}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
```

---

## 测试

### 运行测试

```bash
cd src/backend

# 运行模型测试
python3 -m pytest ../../tests/unit/games/test_chat.py -v

# 运行 API 测试
python3 -m pytest ../../tests/unit/games/test_chat_views.py -v

# 运行 WebSocket 测试
python3 -m pytest ../../tests/unit/games/test_chat_consumer.py -v

# 运行所有聊天相关测试
python3 -m pytest ../../tests/unit/games/test_chat*.py -v
```

### 测试覆盖

- ✅ ChatMessage 模型创建
- ✅ 消息类型（text/system/emoji）
- ✅ 房间类型（game/spectator）
- ✅ 消息限流
- ✅ 表情验证
- ✅ 消息历史分页
- ✅ 软删除
- ✅ 权限控制
- ✅ API 端点
- ✅ WebSocket 连接
- ✅ WebSocket 消息处理
- ✅ WebSocket 广播

---

## 性能优化

### 1. 数据库索引

```python
indexes = [
    Index(fields=['game', 'room_type', '-created_at']),
    Index(fields=['sender', '-created_at']),
    Index(fields=['message_uuid']),
    Index(fields=['is_deleted', '-created_at']),
]
```

### 2. 消息清理

定期清理旧消息（可选）：

```python
# 清理 7 天前的消息
ChatMessageManager.cleanup_old_messages(game_id, days=7)
```

### 3. 连接数限制

- 每个房间默认最大连接数：100
- 可通过配置调整

---

## 安全考虑

### 1. 认证授权

- 所有操作需要 JWT Token 认证
- 房间访问权限验证
- 消息删除权限验证

### 2. 输入验证

- 消息内容长度限制（500 字符）
- 消息类型白名单
- 表情符号白名单
- SQL 注入防护（Django ORM）

### 3. 限流防护

- 每用户每房间 2 秒限流
- 防止消息洪水攻击

### 4. 内容审核

- 敏感词过滤（待实现）
- 举报功能（待实现）

---

## 待扩展功能

- [ ] 敏感词过滤
- [ ] 消息举报功能
- [ ] 用户禁言功能
- [ ] 消息搜索功能
- [ ] 富文本支持（图片/链接）
- [ ] 消息已读状态
- [ ] @提及功能
- [ ] 聊天表情包

---

## 变更日志

### v1.0 (2026-03-05)
- ✅ 初始实现
- ✅ ChatMessage 模型
- ✅ REST API（发送/获取/删除/统计）
- ✅ WebSocket Consumer（实时通信）
- ✅ 消息限流
- ✅ 表情支持
- ✅ 权限控制
- ✅ 单元测试（Model/API/WebSocket）
- ✅ 功能文档

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `src/backend/games/chat.py` | 数据模型和管理器 |
| `src/backend/games/chat_views.py` | REST API 视图 |
| `src/backend/games/chat_consumer.py` | WebSocket Consumer |
| `src/backend/games/migrations/0003_chat_message.py` | 数据库迁移 |
| `src/backend/games/urls.py` | URL 路由（已更新） |
| `src/backend/games/routing.py` | WebSocket 路由（已更新） |
| `tests/unit/games/test_chat.py` | 模型测试 |
| `tests/unit/games/test_chat_views.py` | API 测试 |
| `tests/unit/games/test_chat_consumer.py` | WebSocket 测试 |

---

**TODO-6.5 聊天系统功能** ✅ 完成
