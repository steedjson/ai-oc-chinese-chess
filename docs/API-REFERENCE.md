# 📡 中国象棋项目 - API 参考文档

**文档版本**: v1.0  
**创建时间**: 2026-03-10  
**最后更新**: 2026-03-10  
**基础路径**: `/api/v1`  
**API 端点总数**: 55+

---

## 📋 目录

1. [认证说明](#认证说明)
2. [API 端点总览表](#api 端点总览表)
3. [认证 API](#认证-api) - 5 个端点
4. [用户 API](#用户-api) - 8 个端点
5. [游戏 API](#游戏-api) - 8 个端点
6. [观战 API](#观战-api) - 6 个端点
7. [聊天 API](#聊天-api) - 4 个端点
8. [匹配 API](#匹配-api) - 3 个端点
9. [排行榜 API](#排行榜-api) - 3 个端点
10. [AI API](#ai-api) - 10 个端点
11. [残局 API](#残局-api) - 7 个端点
12. [健康检查 API](#健康检查-api) - 1 个端点
13. [WebSocket 协议](#websocket 协议)
14. [错误码说明](#错误码说明)
15. [请求/响应示例](#请求响应示例)

---

## 🔐 认证说明

### JWT Token 认证

本 API 使用 **JWT (JSON Web Token)** 进行认证。

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| **Access Token** | 2 小时 | 访问受保护资源 |
| **Refresh Token** | 7 天 | 刷新 Access Token |

### 认证流程

```
1. 用户登录/注册 → 获取 Access Token + Refresh Token
2. 访问受保护资源 → Header 携带 Access Token
3. Token 过期 → 使用 Refresh Token 刷新
4. 刷新失败 → 重新登录
```

### 请求头格式

所有需要认证的请求需包含以下 Header：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### curl 示例

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "SecurePass123"}'

# 使用 Token 访问受保护资源
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 📊 API 端点总览表

| 模块 | 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|------|
| **认证** | `/auth/register/` | POST | ❌ | 用户注册 |
| | `/auth/login/` | POST | ❌ | 用户登录 |
| | `/auth/logout/` | POST | ✅ | 用户登出 |
| | `/auth/refresh/` | POST | ❌ | 刷新 Token |
| | `/auth/me/` | GET | ✅ | 获取当前用户 |
| **用户** | `/users/profile/` | GET/PUT/PATCH | ✅ | 个人信息管理 |
| | `/users/me/stats/` | GET | ✅ | 个人统计 |
| | `/users/{id}/` | GET/PUT/PATCH | ✅ | 用户详情 |
| | `/users/{id}/password/` | PUT | ✅ | 修改密码 |
| | `/users/{id}/stats/` | GET | ✅ | 用户统计 |
| | `/users/{id}/games/` | GET | ✅ | 用户对局 |
| **游戏** | `/games/` | GET/POST | ✅ | 对局列表/创建 |
| | `/games/{id}/` | GET/DELETE | ✅ | 对局详情/取消 |
| | `/games/{id}/move/` | POST | ✅ | 提交走棋 |
| | `/games/{id}/moves/` | GET | ✅ | 走棋历史 |
| | `/games/{id}/status/` | PUT | ✅ | 更新状态 |
| **观战** | `/games/{id}/spectate/` | POST | ✅ | 加入观战 |
| | `/games/{id}/spectate/leave/` | POST | ✅ | 离开观战 |
| | `/games/{id}/spectators/` | GET | ✅ | 观战列表 |
| | `/games/{id}/spectators/kick/` | POST | ✅ | 踢出观战 |
| | `/spectator/active-games/` | GET | ✅ | 可观看对局 |
| **聊天** | `/chat/games/{id}/send/` | POST | ✅ | 发送消息 |
| | `/chat/games/{id}/history/` | GET | ✅ | 聊天历史 |
| | `/chat/messages/{id}/delete/` | DELETE | ✅ | 删除消息 |
| | `/chat/games/{id}/stats/` | GET | ✅ | 聊天统计 |
| **匹配** | `/matchmaking/start/` | POST | ✅ | 开始匹配 |
| | `/matchmaking/cancel/` | POST | ✅ | 取消匹配 |
| | `/matchmaking/status/` | GET | ✅ | 匹配状态 |
| **排行榜** | `/ranking/leaderboard/` | GET | ❌ | 天梯排名 |
| | `/ranking/user/{id}/` | GET | ❌ | 用户排名 |
| | `/ranking/user/` | GET | ✅ | 当前用户排名 |
| **AI** | `/ai/games/` | GET/POST | ✅ | AI 对局列表/创建 |
| | `/ai/games/{id}/` | GET/PUT/DELETE | ✅ | AI 对局管理 |
| | `/ai/games/{id}/move/` | POST | ✅ | AI 走棋 |
| | `/ai/games/{id}/hint/` | POST | ✅ | AI 提示 |
| | `/ai/games/{id}/analyze/` | POST | ✅ | AI 分析 |
| | `/ai/difficulties/` | GET | ❌ | 难度列表 |
| | `/ai/engines/status/` | GET | ✅ | 引擎状态 |
| **残局** | `/puzzles/` | GET | ✅ | 关卡列表 |
| | `/puzzles/{id}/` | GET | ✅ | 关卡详情 |
| | `/puzzles/{id}/attempt/` | POST | ✅ | 创建挑战 |
| | `/puzzles/{id}/attempts/{id}/move/` | POST | ✅ | 提交走法 |
| | `/puzzles/{id}/attempts/{id}/complete/` | POST | ✅ | 完成挑战 |
| | `/puzzles/progress/` | GET | ✅ | 用户进度 |
| | `/puzzles/leaderboard/` | GET | ✅ | 残局排行 |
| **健康** | `/health/` | GET | ❌ | 健康检查 |

---

## 🔑 认证 API

**基础路径**: `/api/v1/auth/`

### 1. 用户注册

**端点**: `POST /api/v1/auth/register/`

**权限**: 公开

**请求体**:
```json
{
  "username": "player1",
  "email": "player1@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "player1",
    "email": "player1@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com","password":"SecurePass123","password_confirm":"SecurePass123"}'
```

---

### 2. 用户登录

**端点**: `POST /api/v1/auth/login/`

**权限**: 公开

**请求体**:
```json
{
  "username": "player1",
  "password": "SecurePass123"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "player1",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "登录成功"
}
```

**错误响应** (401):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

---

### 3. 用户登出

**端点**: `POST /api/v1/auth/logout/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

### 4. 刷新 Token

**端点**: `POST /api/v1/auth/refresh/`

**权限**: 公开

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt_token",
    "expires_in": 7200
  },
  "message": "Token 刷新成功"
}
```

---

### 5. 获取当前用户信息

**端点**: `GET /api/v1/auth/me/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "player1",
    "email": "player1@example.com",
    "avatar": "url",
    "created_at": "2026-03-01T00:00:00Z",
    "last_login": "2026-03-10T12:00:00Z"
  }
}
```

---

## 👤 用户 API

**基础路径**: `/api/v1/users/`

### 1. 获取当前用户 Profile

**端点**: `GET /api/v1/users/profile/`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "player1",
    "email": "player1@example.com",
    "avatar": "url",
    "elo_rating": 1500,
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "2026-03-01T00:00:00Z"
  }
}
```

---

### 2. 更新当前用户信息

**端点**: `PUT /api/v1/users/profile/` 或 `PATCH /api/v1/users/profile/`

**请求体**:
```json
{
  "username": "new_username",
  "email": "new@example.com",
  "avatar": "https://example.com/avatar.jpg"
}
```

---

### 3. 获取当前用户统计

**端点**: `GET /api/v1/users/me/stats/`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "total_games": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 60.0,
    "current_rating": 1500,
    "highest_rating": 1550
  }
}
```

---

### 4-8. 其他用户端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/users/{user_id}/` | GET/PUT/PATCH | 获取/更新用户详情 |
| `/users/{user_id}/password/` | PUT | 修改密码 |
| `/users/{user_id}/stats/` | GET | 用户统计 |
| `/users/{user_id}/games/` | GET | 用户对局历史 |

---

## ♟️ 游戏 API

**基础路径**: `/api/v1/games/`

### 1. 获取游戏列表

**端点**: `GET /api/v1/games/games/`

**查询参数**:
- `status`: pending | playing | finished
- `game_type`: single | multiplayer | ai
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20)

**响应** (200):
```json
{
  "count": 50,
  "next": "/api/v1/games/games/?page=2",
  "previous": null,
  "results": [
    {
      "game_id": "uuid",
      "red_player": {"user_id": "uuid", "username": "player1"},
      "black_player": {"user_id": "uuid", "username": "player2"},
      "game_type": "multiplayer",
      "status": "playing",
      "created_at": "2026-03-10T10:00:00Z",
      "started_at": "2026-03-10T10:01:00Z"
    }
  ]
}
```

---

### 2. 创建游戏

**端点**: `POST /api/v1/games/games/`

**请求体**:
```json
{
  "game_type": "multiplayer",
  "black_player_id": "uuid",
  "time_control": {
    "initial_time": 600,
    "increment": 5
  }
}
```

**响应** (201):
```json
{
  "success": true,
  "data": {
    "game_id": "uuid",
    "red_player": {"user_id": "uuid", "username": "player1"},
    "black_player": {"user_id": "uuid", "username": "player2"},
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "move_count": 0,
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "created_at": "2026-03-10T12:00:00Z",
    "started_at": "2026-03-10T12:00:00Z"
  }
}
```

---

### 3. 获取游戏详情

**端点**: `GET /api/v1/games/games/{game_id}/`

**响应** (200):
```json
{
  "success": true,
  "data": {
    "game_id": "uuid",
    "red_player": {...},
    "black_player": {...},
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/...",
    "turn": "w",
    "move_count": 5,
    "red_time_remaining": 580,
    "black_time_remaining": 590,
    "winner": null,
    "created_at": "2026-03-10T12:00:00Z",
    "started_at": "2026-03-10T12:00:00Z",
    "finished_at": null
  }
}
```

---

### 4. 提交走棋

**端点**: `POST /api/v1/games/games/{game_id}/move/`

**请求体**:
```json
{
  "from_pos": "e2",
  "to_pos": "e4"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "move": {
    "move_id": "uuid",
    "move_number": 6,
    "piece": {"type": "pawn", "color": "red"},
    "from_pos": "e2",
    "to_pos": "e4",
    "is_capture": false,
    "is_check": false,
    "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/4P4/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "time_remaining": 580
  },
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/4P4/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
  "turn": "b"
}
```

**错误响应** (400):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_MOVE",
    "message": "无效走棋",
    "legal_moves": ["e4", "f4", "g4"]
  }
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:8000/api/v1/games/games/{game_id}/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"from_pos":"e2","to_pos":"e4"}'
```

---

### 5-8. 其他游戏端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/games/{id}/moves/` | GET | 获取走棋历史 |
| `/games/{id}/status/` | PUT | 更新游戏状态 |
| `/games/{id}/` | DELETE | 取消游戏 |
| `/users/{user_id}/games/` | GET | 获取用户对局 |

---

## 👁️ 观战 API

**基础路径**: `/api/v1/games/{game_id}` 和 `/api/v1/spectator`

### 1. 加入观战

**端点**: `POST /api/v1/games/{game_id}/spectate/`

**请求体**:
```json
{
  "is_anonymous": false
}
```

**响应** (201):
```json
{
  "success": true,
  "spectator": {
    "id": "uuid",
    "game_id": "uuid",
    "user_id": "uuid",
    "joined_at": "2026-03-10T12:00:00Z",
    "is_anonymous": false
  },
  "game_state": {
    "id": "uuid",
    "fen": "rnbakabnr/...",
    "turn": "w",
    "status": "playing",
    "move_count": 15
  },
  "message": "加入观战成功"
}
```

---

### 2-6. 其他观战端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/games/{id}/spectate/leave/` | POST | 离开观战 |
| `/games/{id}/spectators/` | GET | 获取观战列表 |
| `/games/{id}/spectators/kick/` | POST | 踢出观战者 |
| `/spectator/active-games/` | GET | 获取可观看的对局列表 |
| `/games/{id}/spectators/{spectator_id}/` | GET | 获取观战者详情 |

---

## 💬 聊天 API

**基础路径**: `/api/v1/chat`

### 1. 发送聊天消息

**端点**: `POST /api/v1/chat/games/{game_id}/send/`

**请求体**:
```json
{
  "content": "你好!",
  "message_type": "text",
  "room_type": "game"
}
```

**响应** (201):
```json
{
  "success": true,
  "message": {
    "id": "uuid",
    "sender": {"user_id": "uuid", "username": "player1"},
    "content": "你好!",
    "message_type": "text",
    "room_type": "game",
    "created_at": "2026-03-10T12:00:00Z",
    "is_deleted": false
  }
}
```

**错误响应** (429):
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "发送过于频繁"
  }
}
```

---

### 2-4. 其他聊天端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/chat/games/{id}/history/` | GET | 获取聊天历史 |
| `/chat/messages/{id}/delete/` | DELETE | 删除消息 |
| `/chat/games/{id}/stats/` | GET | 获取聊天统计 |

---

## 🎯 匹配 API

**基础路径**: `/api/v1/matchmaking`

### 1. 开始匹配

**端点**: `POST /api/v1/matchmaking/start/`

**请求体**:
```json
{
  "game_type": "ranked"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "加入匹配队列成功",
  "game_type": "ranked",
  "queue_position": 5,
  "estimated_wait_time": 30
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:8000/api/v1/matchmaking/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"game_type":"ranked"}'
```

---

### 2-3. 其他匹配端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/matchmaking/cancel/` | POST | 取消匹配 |
| `/matchmaking/status/` | GET | 获取匹配状态 |

---

## 🏆 排行榜 API

**基础路径**: `/api/v1/ranking`

### 1. 获取排行榜

**端点**: `GET /api/v1/ranking/leaderboard/`

**查询参数**:
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20, 最大 100)

**响应** (200):
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "user_id": "uuid",
      "username": "chess_master",
      "avatar": "url",
      "rating": 2200,
      "games_played": 500,
      "wins": 350,
      "losses": 120,
      "draws": 30,
      "win_rate": 70.0
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1000,
    "total_pages": 50
  }
}
```

---

### 2-3. 其他排行榜端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/ranking/user/{user_id}/` | GET | 获取用户排名 |
| `/ranking/user/` | GET | 获取当前用户排名 |

---

## 🤖 AI API

**基础路径**: `/api/v1/ai`

### 1. 获取 AI 对局列表

**端点**: `GET /api/v1/ai/games/`

**响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "player": {"user_id": "uuid", "username": "player1"},
      "ai_level": 5,
      "status": "playing",
      "fen_current": "...",
      "turn": "w",
      "created_at": "2026-03-10T10:00:00Z"
    }
  ]
}
```

---

### 2. 创建 AI 对局

**端点**: `POST /api/v1/ai/games/`

**请求体**:
```json
{
  "ai_level": 5,
  "time_control": {
    "initial_time": 600,
    "increment": 5
  },
  "player_color": "w"
}
```

**响应** (201):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "player": {...},
    "ai_level": 5,
    "status": "playing",
    "fen_current": "...",
    "created_at": "2026-03-10T12:00:00Z"
  },
  "message": "AI 对局创建成功"
}
```

---

### 3. 获取 AI 对局详情

**端点**: `GET /api/v1/ai/games/{game_id}/`

---

### 4. 请求 AI 走棋

**端点**: `POST /api/v1/ai/games/{game_id}/move/`

**请求体**:
```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "time_limit": 2000
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "from_pos": "b3",
    "to_pos": "e3",
    "piece": "C",
    "evaluation": 0.35,
    "depth": 12,
    "thinking_time": 1500
  }
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:8000/api/v1/ai/games/{game_id}/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"fen":"rnbakabnr/...","difficulty":5,"time_limit":2000}'
```

---

### 5. 请求 AI 提示

**端点**: `POST /api/v1/ai/games/{game_id}/hint/`

**请求体**:
```json
{
  "fen": "rnbakabnr/...",
  "difficulty": 5,
  "count": 3
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "hints": [
      {"from_pos": "b3", "to_pos": "e3", "evaluation": 0.35, "piece": "C"},
      {"from_pos": "h3", "to_pos": "e3", "evaluation": 0.28, "piece": "C"},
      {"from_pos": "b1", "to_pos": "c3", "evaluation": 0.15, "piece": "N"}
    ]
  }
}
```

---

### 6. 请求 AI 分析

**端点**: `POST /api/v1/ai/games/{game_id}/analyze/`

**请求体**:
```json
{
  "fen": "rnbakabnr/...",
  "depth": 15
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "evaluation": 0.3,
    "advantage": "red",
    "material_balance": 0,
    "position_features": {
      "red_king_safety": "good",
      "black_king_safety": "moderate",
      "center_control": "balanced"
    },
    "suggestions": [
      {"move": "h0h2", "reason": "出车控制边路"}
    ]
  }
}
```

---

### 7-10. 其他 AI 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/ai/difficulties/` | GET | 获取难度列表 |
| `/ai/engines/status/` | GET | 获取引擎状态 |

---

## 🧩 残局 API

**基础路径**: `/api/v1/puzzles`

### 1. 获取关卡列表

**端点**: `GET /api/v1/puzzles/`

**查询参数**:
- `difficulty`: 难度筛选 (1-10)
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20)

**响应** (200):
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "uuid",
        "title": "千里独行",
        "difficulty": 5,
        "category": "车兵类",
        "move_limit": 10,
        "time_limit": 300,
        "completed_count": 1500
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100
    }
  }
}
```

---

### 2-7. 其他残局端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/puzzles/{id}/` | GET | 关卡详情 |
| `/puzzles/{id}/attempt/` | POST | 创建挑战 |
| `/puzzles/{id}/attempts/{id}/move/` | POST | 提交走法 |
| `/puzzles/{id}/attempts/{id}/complete/` | POST | 完成挑战 |
| `/puzzles/progress/` | GET | 用户进度 |
| `/puzzles/leaderboard/` | GET | 残局排行榜 |

---

## 🏥 健康检查 API

**端点**: `GET /api/v1/health/`

**权限**: 公开

**响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-03-10T12:00:00Z",
  "version": "v1.0.0",
  "services": {
    "database": "ok",
    "cache": "ok",
    "ai_engine": "ok"
  }
}
```

**curl 示例**:
```bash
curl -X GET http://localhost:8000/api/v1/health/
```

---

## 🔌 WebSocket 协议

### 连接格式

```
ws://{host}/ws/{endpoint}/?token={access_token}
```

### WebSocket 端点

| 端点 | 用途 |
|------|------|
| `/ws/game/{game_id}/` | 游戏对弈 |
| `/ws/ai/game/{game_id}/` | AI 对弈 |
| `/ws/matchmaking/` | 匹配系统 |

### 通用消息格式

```json
{
  "type": "MESSAGE_TYPE",
  "payload": {},
  "timestamp": "2026-03-10T12:00:00Z"
}
```

### 心跳机制

**客户端发送**:
```json
{
  "type": "HEARTBEAT",
  "timestamp": "2026-03-10T12:00:00Z"
}
```

**服务器响应**:
```json
{
  "type": "HEARTBEAT",
  "payload": {
    "acknowledged": true,
    "timestamp": "2026-03-10T12:00:00Z"
  }
}
```

- **心跳间隔**: 30 秒
- **超时阈值**: 90 秒

### JavaScript 连接示例

```javascript
const token = 'eyJhbGciOiJIUzI1NiIs...';
const gameId = 'uuid';
const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}/?token=${token}`);

ws.onopen = () => {
  console.log('Connected');
  // 发送心跳
  setInterval(() => {
    ws.send(JSON.stringify({
      type: 'HEARTBEAT',
      timestamp: new Date().toISOString()
    }));
  }, 30000);
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// 发送走棋
ws.send(JSON.stringify({
  type: 'MOVE',
  payload: { from: 'e2', to: 'e4' }
}));
```

---

## ❌ 错误码说明

### 认证相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `TOKEN_REQUIRED` | 400 | Token 不能为空 |
| `TOKEN_INVALID` | 401 | Token 已过期或无效 |
| `USER_BANNED` | 403 | 账号已被封禁 |
| `USER_INACTIVE` | 403 | 账号已被禁用 |

### 验证相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `WRONG_OLD_PASSWORD` | 400 | 旧密码错误 |
| `SAME_PASSWORD` | 400 | 新密码不能与旧密码相同 |

### 用户相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `PERMISSION_DENIED` | 403 | 权限不足 |

### 游戏相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 游戏不存在 |
| `GAME_NOT_PLAYING` | 400 | 游戏未进行中 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 |
| `INVALID_MOVE` | 400 | 无效走棋 |
| `NO_PIECE` | 400 | 起始位置没有棋子 |

### 观战相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `GAME_FINISHED` | 400 | 游戏已结束 |
| `CANNOT_SPECTATE_PLAYERS` | 403 | 玩家不能观战自己的游戏 |
| `ALREADY_WATCHING` | 400 | 已在观战 |

### 聊天相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `ROOM_NOT_FOUND` | 404 | 房间不存在 |
| `EMPTY_CONTENT` | 400 | 消息内容不能为空 |
| `CONTENT_TOO_LONG` | 400 | 消息内容过长 |
| `RATE_LIMITED` | 429 | 发送过于频繁 |

### 匹配相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `NOT_IN_QUEUE` | 404 | 不在队列中 |
| `QUEUE_FULL` | 429 | 队列已满 |
| `ALREADY_IN_QUEUE` | 400 | 已在队列中 |

### AI 相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `INVALID_DIFFICULTY` | 400 | 难度等级无效 (必须 1-10) |
| `AI_ERROR` | 500 | AI 引擎错误 |

### 残局相关

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `PUZZLE_NOT_FOUND` | 404 | 关卡不存在 |
| `ATTEMPT_NOT_FOUND` | 404 | 挑战不存在 |
| `NOT_COMPLETE` | 400 | 挑战尚未完成 |

### 通用错误

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 请求方法不允许 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |

---

## 📝 请求/响应示例

### 完整登录流程

```bash
# 1. 用户注册
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com","password":"SecurePass123","password_confirm":"SecurePass123"}'

# 2. 用户登录
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"SecurePass123"}'

# 响应:
# {
#   "success": true,
#   "data": {
#     "user_id": "abc123",
#     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#     "expires_in": 7200
#   }
# }
```

### 创建多人对局

```bash
curl -X POST http://localhost:8000/api/v1/games/games/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "multiplayer",
    "black_player_id": "def456",
    "time_control": {"initial_time": 600, "increment": 5}
  }'
```

### 加入匹配队列

```bash
# 开始匹配
curl -X POST http://localhost:8000/api/v1/matchmaking/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"game_type":"ranked"}'

# 查询状态
curl -X GET "http://localhost:8000/api/v1/matchmaking/status/?game_type=ranked" \
  -H "Authorization: Bearer <access_token>"
```

### 刷新 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<your_refresh_token>"}'
```

---

## 📊 API 统计

| 模块 | 端点数量 | 认证要求 |
|------|---------|---------|
| 认证 API | 5 | 部分公开 |
| 用户 API | 8 | 已认证 |
| 游戏 API | 8 | 已认证 |
| 观战 API | 6 | 已认证 |
| 聊天 API | 4 | 已认证 |
| 匹配 API | 3 | 已认证 |
| 排行榜 API | 3 | 部分公开 |
| AI API | 10 | 部分公开 |
| 残局 API | 7 | 已认证 |
| 健康检查 | 1 | 公开 |
| **总计** | **55** | - |

---

## 📞 技术支持

- **文档版本**: v1.0
- **最后更新**: 2026-03-10
- **项目维护者**: 小屁孩（御姐模式）

---

**文档创建时间**: 2026-03-10
