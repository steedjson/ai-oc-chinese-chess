# 📚 中国象棋 - 完整 API 文档

**版本**: v1.0.0  
**创建时间**: 2026-03-11  
**最后更新**: 2026-03-11  
**基础 URL**: `http://localhost:8000/api/v1`

---

## 📑 目录

1. [认证 API](#1-认证-api)
2. [游戏 API](#2-游戏-api)
3. [AI 对弈 API](#3-ai 对弈-api)
4. [匹配系统 API](#4-匹配系统-api)
5. [好友对战 API](#5-好友对战-api)
6. [用户系统 API](#6-用户系统-api)
7. [聊天系统 API](#7-聊天系统-api)
8. [观战系统 API](#8-观战系统-api)
9. [残局挑战 API](#9-残局挑战-api)
10. [统计 API](#10-统计-api)
11. [WebSocket 事件](#11-websocket 事件)

---

## 1. 认证 API

### 1.1 用户注册

**POST** `/auth/register/`

**请求体**:
```json
{
  "username": "string (required, 3-150 chars)",
  "email": "string (required, email format)",
  "password": "string (required, min 8 chars)",
  "nickname": "string (optional)"
}
```

**响应** (201 Created):
```json
{
  "id": 1,
  "username": "player123",
  "email": "player@example.com",
  "nickname": "象棋大师",
  "created_at": "2026-03-11T00:00:00Z",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**错误响应**:
- 400 Bad Request - 用户名已存在/邮箱已注册/密码太短
- 422 Unprocessable Entity - 验证失败

---

### 1.2 用户登录

**POST** `/auth/login/`

**请求体**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**响应** (200 OK):
```json
{
  "user": {
    "id": 1,
    "username": "player123",
    "nickname": "象棋大师",
    "avatar": "https://...",
    "rating": 1500,
    "rank": "黄金"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 1.3 刷新 Token

**POST** `/auth/refresh/`

**请求体**:
```json
{
  "refresh_token": "string (required)"
}
```

**响应** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 2. 游戏 API

### 2.1 创建游戏

**POST** `/games/`

**认证**: Required  
**请求体**:
```json
{
  "game_type": "ai|match|friend|custom",
  "ai_difficulty": 5,  // 仅 AI 模式，1-10
  "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "time_control": {
    "mode": "untimed|clock",
    "red_time": 7200,  // 秒
    "black_time": 7200,
    "increment": 0
  }
}
```

**响应** (201 Created):
```json
{
  "id": 123,
  "game_type": "ai",
  "status": "waiting",
  "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "current_player": "red",
  "created_at": "2026-03-11T00:00:00Z",
  "players": {
    "red": {"id": 1, "username": "player123"},
    "black": null  // AI 或对手
  }
}
```

---

### 2.2 获取游戏详情

**GET** `/games/{game_id}/`

**认证**: Required  
**权限**: 游戏参与者或公开游戏

**响应** (200 OK):
```json
{
  "id": 123,
  "game_type": "ai",
  "status": "playing",
  "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "current_player": "red",
  "winner": null,
  "move_count": 15,
  "created_at": "2026-03-11T00:00:00Z",
  "updated_at": "2026-03-11T00:05:00Z",
  "players": {
    "red": {"id": 1, "username": "player123"},
    "black": {"id": null, "username": "AI (难度 5)"}
  },
  "time_remaining": {
    "red": 7150,
    "black": 7200
  }
}
```

---

### 2.3 执行走棋

**POST** `/games/{game_id}/move/`

**认证**: Required  
**请求体**:
```json
{
  "from": "e2",
  "to": "e4",
  "piece": "P"
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "move": {
    "id": 456,
    "from": "e2",
    "to": "e4",
    "piece": "P",
    "notation": "炮二平五",
    "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1"
  },
  "game_state": {
    "current_player": "black",
    "is_check": false,
    "is_checkmate": false,
    "move_count": 1
  }
}
```

**错误响应**:
- 400 Bad Request - 非法走棋
- 403 Forbidden - 不是你的回合
- 404 Not Found - 游戏不存在

---

### 2.4 获取走棋历史

**GET** `/games/{game_id}/moves/`

**响应** (200 OK):
```json
{
  "moves": [
    {
      "id": 1,
      "from": "e2",
      "to": "e4",
      "piece": "P",
      "notation": "炮二平五",
      "player": "red",
      "timestamp": "2026-03-11T00:01:00Z"
    },
    {
      "id": 2,
      "from": "e7",
      "to": "e5",
      "piece": "P",
      "notation": "炮 8 平 5",
      "player": "black",
      "timestamp": "2026-03-11T00:01:30Z"
    }
  ],
  "total": 2
}
```

---

### 2.5 认输

**POST** `/games/{game_id}/resign/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "success": true,
  "winner": "black",
  "game_status": "finished"
}
```

---

### 2.6 请求和棋

**POST** `/games/{game_id}/draw/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "success": true,
  "game_status": "finished",
  "result": "draw"
}
```

---

## 3. AI 对弈 API

### 3.1 请求 AI 走棋

**POST** `/games/{game_id}/ai/move/`

**认证**: Required  
**适用**: AI 对战模式

**响应** (200 OK):
```json
{
  "move": {
    "from": "c7",
    "to": "c5",
    "piece": "P",
    "notation": "卒 7 进 1"
  },
  "ai_info": {
    "difficulty": 5,
    "search_depth": 13,
    "evaluation": 0.3,
    "thinking_time_ms": 1250
  }
}
```

---

### 3.2 获取走棋建议

**POST** `/games/{game_id}/ai/hint/`

**认证**: Required  
**请求体**:
```json
{
  "count": 3  // 请求建议数量，默认 3
}
```

**响应** (200 OK):
```json
{
  "hints": [
    {
      "move": "e2e4",
      "notation": "炮二平五",
      "evaluation": 0.5,
      "confidence": 0.9
    },
    {
      "move": "c2c4",
      "notation": "兵七进一",
      "evaluation": 0.3,
      "confidence": 0.7
    }
  ]
}
```

---

### 3.3 局面分析

**POST** `/games/{game_id}/ai/analyze/`

**认证**: Required  
**请求体**:
```json
{
  "depth": 15  // 分析深度，默认 15
}
```

**响应** (200 OK):
```json
{
  "evaluation": 0.2,
  "advantage": "red",
  "best_line": ["e2e4", "e7e5", "h2c2"],
  "analysis": "红方略优，中路有攻势",
  "key_positions": [
    {"square": "e4", "importance": "high"},
    {"square": "c5", "importance": "medium"}
  ]
}
```

---

## 4. 匹配系统 API

### 4.1 加入匹配队列

**POST** `/matchmaking/join/`

**认证**: Required  
**请求体**:
```json
{
  "game_type": "online"  // 默认 online
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "queue_status": {
    "position": 3,
    "estimated_wait": 45,  // 秒
    "search_range": 100  // ELO 搜索范围
  }
}
```

---

### 4.2 取消匹配

**POST** `/matchmaking/leave/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "success": true,
  "message": "已退出匹配队列"
}
```

---

### 4.3 获取匹配状态

**GET** `/matchmaking/status/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "in_queue": true,
  "queue_status": {
    "position": 2,
    "estimated_wait": 30,
    "search_range": 150,
    "joined_at": "2026-03-11T00:00:00Z"
  }
}
```

---

## 5. 好友对战 API

### 5.1 创建房间

**POST** `/friend-rooms/`

**认证**: Required  
**请求体**:
```json
{
  "name": "好友切磋",
  "is_private": true,
  "password": "123456",  // 可选
  "time_control": {
    "mode": "clock",
    "red_time": 600,
    "black_time": 600
  }
}
```

**响应** (201 Created):
```json
{
  "id": "abc123",
  "name": "好友切磋",
  "creator": {"id": 1, "username": "player123"},
  "status": "waiting",
  "invite_link": "http://localhost:3000/friend-room/abc123",
  "created_at": "2026-03-11T00:00:00Z"
}
```

---

### 5.2 加入房间

**POST** `/friend-rooms/{room_id}/join/`

**认证**: Required  
**请求体**:
```json
{
  "password": "123456"  // 密码房间需要
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "room": {
    "id": "abc123",
    "name": "好友切磋",
    "players": [
      {"id": 1, "username": "player123", "side": "red"},
      {"id": 2, "username": "friend1", "side": "black"}
    ],
    "status": "ready"
  }
}
```

---

### 5.3 获取房间状态

**GET** `/friend-rooms/{room_id}/`

**响应** (200 OK):
```json
{
  "id": "abc123",
  "name": "好友切磋",
  "creator": {"id": 1, "username": "player123"},
  "status": "playing",
  "players": [
    {"id": 1, "username": "player123", "side": "red"},
    {"id": 2, "username": "friend1", "side": "black"}
  ],
  "game_id": 123,
  "spectators": 2
}
```

---

### 5.4 分享房间

**POST** `/friend-rooms/{room_id}/share/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "invite_link": "http://localhost:3000/friend-room/abc123",
  "share_text": "来和我下象棋！房间：好友切磋\n点击加入：http://localhost:3000/friend-room/abc123"
}
```

---

## 6. 用户系统 API

### 6.1 获取个人资料

**GET** `/users/profile/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "id": 1,
  "username": "player123",
  "nickname": "象棋大师",
  "avatar": "https://...",
  "bio": "热爱象棋",
  "rating": 1500,
  "rank": "黄金",
  "stats": {
    "total_games": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 0.60
  }
}
```

---

### 6.2 更新个人资料

**PUT** `/users/profile/`

**认证**: Required  
**请求体**:
```json
{
  "nickname": "新的昵称",
  "bio": "新的简介",
  "avatar": "https://..."  // 可选
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "username": "player123",
    "nickname": "新的昵称",
    "bio": "新的简介",
    ...
  }
}
```

---

### 6.3 获取用户战绩

**GET** `/users/{user_id}/stats/`

**响应** (200 OK):
```json
{
  "user": {"id": 1, "username": "player123"},
  "overall": {
    "total_games": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 0.60
  },
  "by_mode": {
    "ai": {"games": 50, "wins": 40},
    "match": {"games": 40, "wins": 15},
    "friend": {"games": 10, "wins": 5}
  },
  "rating_history": [
    {"date": "2026-03-01", "rating": 1450},
    {"date": "2026-03-11", "rating": 1500}
  ]
}
```

---

### 6.4 天梯排行榜

**GET** `/users/leaderboard/`

**查询参数**:
- `limit` (default: 100, max: 1000)
- `offset` (default: 0)
- `rank` (可选，过滤段位：bronze/silver/gold/platinum/diamond/master)

**响应** (200 OK):
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user": {"id": 99, "username": "grandmaster", "nickname": "特级大师"},
      "rating": 2800,
      "rank_title": "大师",
      "total_games": 500,
      "win_rate": 0.75
    },
    ...
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

---

## 7. 聊天系统 API

### 7.1 发送聊天消息

**WebSocket Event**: `chat.send`

**请求**:
```json
{
  "game_id": 123,
  "content": "你好！"
}
```

**响应**:
```json
{
  "message": {
    "id": 789,
    "game_id": 123,
    "sender": {"id": 1, "username": "player123"},
    "content": "你好！",
    "timestamp": "2026-03-11T00:05:00Z"
  }
}
```

---

### 7.2 发送表情

**WebSocket Event**: `chat.emote`

**请求**:
```json
{
  "game_id": 123,
  "emote_id": "smile"
}
```

**响应**:
```json
{
  "emote": {
    "id": 790,
    "game_id": 123,
    "sender": {"id": 1, "username": "player123"},
    "emote_id": "smile",
    "emote_url": "https://.../smile.png",
    "timestamp": "2026-03-11T00:05:00Z"
  }
}
```

---

## 8. 观战系统 API

### 8.1 加入观战

**WebSocket Event**: `spectator.join`

**请求**:
```json
{
  "game_id": 123
}
```

**响应**:
```json
{
  "success": true,
  "game": {
    "id": 123,
    "players": {
      "red": {"username": "player123"},
      "black": {"username": "player456"}
    },
    "status": "playing",
    "spectator_count": 5
  }
}
```

---

### 8.2 离开观战

**WebSocket Event**: `spectator.leave`

**请求**:
```json
{
  "game_id": 123
}
```

---

## 9. 残局挑战 API

### 9.1 获取残局列表

**GET** `/puzzles/`

**查询参数**:
- `difficulty` (可选：easy/medium/hard)
- `category` (可选：opening/middlegame/endgame)
- `limit` (default: 20)

**响应** (200 OK):
```json
{
  "puzzles": [
    {
      "id": 1,
      "title": "千里独行",
      "difficulty": "hard",
      "category": "endgame",
      "fen": "...",
      "solution_moves": 5,
      "success_rate": 0.25,
      "attempts": 1000
    },
    ...
  ],
  "total": 50
}
```

---

### 9.2 开始残局

**POST** `/puzzles/{puzzle_id}/start/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "success": true,
  "game_id": 456,
  "puzzle": {
    "id": 1,
    "title": "千里独行",
    "fen": "...",
    "player_side": "red"
  }
}
```

---

### 9.3 提交残局答案

**POST** `/puzzles/{puzzle_id}/submit/`

**认证**: Required  
**请求体**:
```json
{
  "moves": [
    {"from": "e2", "to": "e4"},
    {"from": "c7", "to": "c5"}
  ]
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "correct": true,
  "moves_count": 5,
  "time_taken": 120,  // 秒
  "rating_change": +10
}
```

---

## 10. 统计 API

### 10.1 获取平台统计

**GET** `/stats/platform/`

**响应** (200 OK):
```json
{
  "users": {
    "total": 10000,
    "active_today": 500,
    "active_week": 2000
  },
  "games": {
    "total": 50000,
    "today": 200,
    "ongoing": 50
  },
  "modes": {
    "ai": 30000,
    "match": 15000,
    "friend": 5000
  }
}
```

---

### 10.2 获取个人统计

**GET** `/stats/personal/`

**认证**: Required  
**响应** (200 OK):
```json
{
  "user": {"id": 1, "username": "player123"},
  "games": {
    "total": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5
  },
  "performance": {
    "avg_game_length": 45,  // 分钟
    "favorite_opening": "中炮局",
    "win_rate_by_mode": {
      "ai": 0.80,
      "match": 0.40,
      "friend": 0.50
    }
  },
  "progress": {
    "rating_change_30d": +50,
    "games_played_30d": 30
  }
}
```

---

## 11. WebSocket 事件

### 连接 URL

```
ws://localhost:8000/ws/
```

### 认证

连接时需在 query string 中提供 token：
```
ws://localhost:8000/ws/?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### 游戏事件

#### `game.move` - 走棋通知
```json
{
  "type": "game.move",
  "data": {
    "game_id": 123,
    "move": {
      "from": "e2",
      "to": "e4",
      "piece": "P",
      "notation": "炮二平五"
    },
    "player": "red",
    "fen_after": "..."
  }
}
```

#### `game.state` - 游戏状态更新
```json
{
  "type": "game.state",
  "data": {
    "game_id": 123,
    "status": "playing",
    "current_player": "black",
    "is_check": true,
    "is_checkmate": false,
    "move_count": 15
  }
}
```

#### `game.finish` - 游戏结束
```json
{
  "type": "game.finish",
  "data": {
    "game_id": 123,
    "winner": "red",
    "reason": "checkmate",
    "final_fen": "..."
  }
}
```

---

### 匹配事件

#### `matchmaking.found` - 匹配成功
```json
{
  "type": "matchmaking.found",
  "data": {
    "opponent": {"id": 2, "username": "player456", "rating": 1520},
    "game_id": 123,
    "your_side": "red"
  }
}
```

#### `matchmaking.status` - 匹配状态更新
```json
{
  "type": "matchmaking.status",
  "data": {
    "position": 2,
    "estimated_wait": 30,
    "search_range": 150
  }
}
```

---

### 聊天事件

#### `chat.message` - 聊天消息
```json
{
  "type": "chat.message",
  "data": {
    "game_id": 123,
    "sender": {"id": 1, "username": "player123"},
    "content": "你好！",
    "timestamp": "2026-03-11T00:05:00Z"
  }
}
```

#### `chat.emote` - 表情
```json
{
  "type": "chat.emote",
  "data": {
    "game_id": 123,
    "sender": {"id": 1, "username": "player123"},
    "emote_id": "smile",
    "emote_url": "https://.../smile.png"
  }
}
```

---

### 观战事件

#### `spectator.joined` - 观战者加入
```json
{
  "type": "spectator.joined",
  "data": {
    "game_id": 123,
    "spectator": {"id": 3, "username": "viewer1"}
  }
}
```

#### `spectator.left` - 观战者离开
```json
{
  "type": "spectator.left",
  "data": {
    "game_id": 123,
    "spectator": {"id": 3, "username": "viewer1"}
  }
}
```

---

## 错误码总览

| 错误码 | 说明 |
|--------|------|
| 400 Bad Request | 请求参数错误 |
| 401 Unauthorized | 未认证或 token 过期 |
| 403 Forbidden | 无权限访问 |
| 404 Not Found | 资源不存在 |
| 409 Conflict | 资源冲突（如已在队列中） |
| 422 Unprocessable Entity | 验证失败 |
| 429 Too Many Requests | 请求过于频繁 |
| 500 Internal Server Error | 服务器内部错误 |

---

## 限流策略

| 端点类型 | 限流 |
|----------|------|
| 认证 API | 10 次/分钟 |
| 游戏走棋 | 30 次/分钟 |
| 聊天消息 | 10 次/分钟 |
| 匹配操作 | 5 次/分钟 |
| 其他 API | 100 次/分钟 |

---

**文档维护**: 小屁孩（御姐模式）  
**最后更新**: 2026-03-11 00:22
