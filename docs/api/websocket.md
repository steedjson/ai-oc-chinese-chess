# WebSocket API 文档

## 概述

WebSocket 端点用于实时通信，支持游戏对弈、AI 对弈和匹配系统。

**基础 URL**: `ws://localhost:8000/ws/`

**认证方式**: JWT Token（通过 URL 参数传递）
```
ws://localhost:8000/ws/game/{game_id}/?token=eyJhbG...
```

---

## 通用消息格式

### 消息结构
```json
{
  "type": "MESSAGE_TYPE",
  "payload": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误消息格式
```json
{
  "type": "ERROR",
  "payload": {
    "success": false,
    "error": {
      "code": "ERROR_CODE",
      "message": "错误描述"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 心跳机制

所有 WebSocket 连接都支持心跳检测：

**客户端发送:**
```json
{
  "type": "HEARTBEAT",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**服务器响应:**
```json
{
  "type": "HEARTBEAT",
  "payload": {
    "acknowledged": true,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

- 心跳间隔: 30 秒
- 超时阈值: 90 秒无心跳判定为掉线

---

## 1. 游戏对弈 WebSocket

### 连接端点
```
/ws/game/{game_id}/
```

### 消息类型

#### 1.1 JOIN - 加入游戏房间
**客户端发送:**
```json
{
  "type": "JOIN",
  "payload": {}
}
```

**服务器响应:**
```json
{
  "type": "JOIN_RESULT",
  "payload": {
    "success": true,
    "game_state": {
      "game_id": "uuid",
      "fen": "rnbakabnr/...",
      "turn": "w",
      "status": "playing",
      "players": {
        "red": {"user_id": "uuid", "online": true},
        "black": {"user_id": "uuid", "online": true}
      }
    }
  }
}
```

#### 1.2 MOVE - 提交走棋
**客户端发送:**
```json
{
  "type": "MOVE",
  "payload": {
    "from": "e2",
    "to": "e4"
  }
}
```

**服务器广播 (MOVE_RESULT):**
```json
{
  "type": "MOVE_RESULT",
  "payload": {
    "success": true,
    "move": {
      "from": "e2",
      "to": "e4",
      "piece": "P",
      "captured": null,
      "notation": "炮二平五"
    },
    "fen": "rnbakabnr/...",
    "turn": "b",
    "is_check": false,
    "is_checkmate": false,
    "is_stalemate": false
  }
}
```

#### 1.3 GAME_STATE - 游戏状态更新
**服务器主动推送:**
```json
{
  "type": "GAME_STATE",
  "payload": {
    "game_id": "uuid",
    "fen": "rnbakabnr/...",
    "turn": "w",
    "status": "playing",
    "players": {
      "red": {"user_id": "uuid", "online": true},
      "black": {"user_id": "uuid", "online": false}
    }
  }
}
```

#### 1.4 GAME_OVER - 游戏结束
**服务器主动推送:**
```json
{
  "type": "GAME_OVER",
  "payload": {
    "winner": "red",
    "reason": "checkmate",
    "rating_change": {
      "red": 15,
      "black": -15
    }
  }
}
```

#### 1.5 PLAYER_JOIN / PLAYER_LEAVE - 玩家进出通知
```json
{
  "type": "PLAYER_JOIN",
  "payload": {
    "user_id": "uuid",
    "username": "player_name"
  }
}
```

### 错误码
| 错误码 | 描述 |
|--------|------|
| AUTH_FAILED | 认证失败，Token 无效或过期 |
| AUTH_FORBIDDEN | 无权加入此游戏 |
| INVALID_MESSAGE_TYPE | 未知的消息类型 |
| INVALID_JSON | JSON 格式错误 |
| INVALID_MOVE | 无效的走棋 |
| NOT_YOUR_TURN | 不是你的回合 |
| NO_PIECE | 起始位置没有棋子 |
| GAME_NOT_PLAYING | 游戏未进行中 |
| GAME_NOT_FOUND | 游戏不存在 |
| MOVE_ERROR | 走棋处理错误 |

---

## 2. AI 对弈 WebSocket

### 连接端点
```
/ws/ai/game/{game_id}/
```

### 消息类型

#### 2.1 request_move - 请求 AI 走棋
**客户端发送:**
```json
{
  "type": "request_move",
  "payload": {
    "fen": "rnbakabnr/...",
    "difficulty": 5
  }
}
```

**服务器响应:**
```json
{
  "type": "move_requested",
  "payload": {
    "status": "processing"
  }
}
```

**AI 走棋完成推送:**
```json
{
  "type": "ai_move",
  "payload": {
    "from_pos": "e7",
    "to_pos": "e6",
    "piece": "p",
    "evaluation": -0.5,
    "depth": 15,
    "thinking_time": 1200
  }
}
```

#### 2.2 request_hint - 请求 AI 提示
**客户端发送:**
```json
{
  "type": "request_hint",
  "payload": {
    "fen": "rnbakabnr/...",
    "count": 3
  }
}
```

**服务器推送:**
```json
{
  "type": "ai_hint",
  "payload": {
    "hints": [
      {"move": "e2e4", "score": 0.8},
      {"move": "d2d4", "score": 0.6},
      {"move": "g1f3", "score": 0.4}
    ]
  }
}
```

#### 2.3 request_analysis - 请求 AI 分析
**客户端发送:**
```json
{
  "type": "request_analysis",
  "payload": {
    "fen": "rnbakabnr/...",
    "depth": 15
  }
}
```

**服务器推送:**
```json
{
  "type": "ai_analysis",
  "payload": {
    "score": 0.5,
    "score_text": "红方优势",
    "best_move": "e2e4",
    "depth": 15,
    "thinking_time": 2000
  }
}
```

#### 2.4 ai_thinking - AI 思考中通知
```json
{
  "type": "ai_thinking",
  "payload": {
    "progress": 50,
    "depth": 10,
    "nodes": 100000
  }
}
```

### 错误码
| 错误码 | 描述 |
|--------|------|
| INVALID_JSON | 无效的 JSON 格式 |
| PERMISSION_DENIED | 无权访问此对局 |

---

## 3. 匹配系统 WebSocket

### 连接端点
```
/ws/matchmaking/
```

### 消息类型

#### 3.1 JOIN_QUEUE - 加入匹配队列
**客户端发送:**
```json
{
  "type": "JOIN_QUEUE",
  "payload": {
    "game_type": "ranked"
  }
}
```

**服务器响应:**
```json
{
  "type": "queue_joined",
  "payload": {
    "success": true,
    "game_type": "ranked",
    "rating": 1500,
    "queue_position": 5,
    "estimated_wait_time": 60
  }
}
```

#### 3.2 LEAVE_QUEUE - 退出匹配队列
**客户端发送:**
```json
{
  "type": "LEAVE_QUEUE",
  "payload": {}
}
```

**服务器响应:**
```json
{
  "type": "queue_left",
  "payload": {
    "success": true
  }
}
```

#### 3.3 GET_STATUS - 获取队列状态
**客户端发送:**
```json
{
  "type": "GET_STATUS",
  "payload": {}
}
```

**服务器响应:**
```json
{
  "type": "queue_status",
  "payload": {
    "total_in_queue": 20,
    "your_position": 5,
    "estimated_wait_time": 60,
    "in_queue": true
  }
}
```

#### 3.4 MATCH_FOUND - 匹配成功
**服务器主动推送:**
```json
{
  "type": "match_found",
  "payload": {
    "success": true,
    "game_id": "uuid",
    "opponent": {
      "user_id": "uuid",
      "username": "opponent_name",
      "rating": 1520
    },
    "game_type": "ranked",
    "your_side": "red"
  }
}
```

### 错误码
| 错误码 | 描述 |
|--------|------|
| QUEUE_JOIN_FAILED | 加入队列失败 |
| QUEUE_JOIN_ERROR | 加入队列时发生错误 |
| QUEUE_LEAVE_FAILED | 不在队列中 |
| QUEUE_LEAVE_ERROR | 退出队列时发生错误 |
| STATUS_ERROR | 获取状态失败 |

---

## 连接关闭代码

| 代码 | 含义 |
|------|------|
| 1000 | 正常关闭 |
| 4001 | 认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 4005 | 服务器错误 |
| 4006 | 连接超时 |

---

## 使用示例

### JavaScript 客户端示例

```javascript
// 连接游戏房间
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
const gameId = '550e8400-e29b-41d4-a716-446655440000';
const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}/?token=${token}`);

// 连接建立
ws.onopen = () => {
  console.log('Connected to game room');
  
  // 发送心跳
  setInterval(() => {
    ws.send(JSON.stringify({
      type: 'HEARTBEAT',
      timestamp: new Date().toISOString()
    }));
  }, 30000);
};

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'GAME_STATE':
      console.log('Game state:', data.payload);
      break;
    case 'MOVE_RESULT':
      console.log('Move result:', data.payload);
      break;
    case 'GAME_OVER':
      console.log('Game over:', data.payload);
      break;
    case 'ERROR':
      console.error('Error:', data.payload.error);
      break;
  }
};

// 发送走棋
function makeMove(from, to) {
  ws.send(JSON.stringify({
    type: 'MOVE',
    payload: { from, to }
  }));
}

// 连接关闭
ws.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
};
```

---

## 注意事项

1. **Token 有效期**: Access Token 默认 2 小时有效，过期后需要刷新
2. **重连机制**: 客户端应实现自动重连逻辑
3. **并发限制**: 同一用户同一时间只能在一个游戏房间中
4. **消息大小**: 单条消息建议不超过 64KB
