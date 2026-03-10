# Chinese Chess API 完整参考文档

**版本**: 1.0.0  
**最后更新**: 2026-03-06  
**基础 URL**: `http://localhost:8000`

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [认证模块](#认证模块)
4. [用户模块](#用户模块)
5. [游戏对局模块](#游戏对局模块)
6. [每日挑战模块](#每日挑战模块)
7. [AI 引擎模块](#ai 引擎模块)
8. [匹配系统模块](#匹配系统模块)
9. [残局谜题模块](#残局谜题模块)
10. [健康检查模块](#健康检查模块)
11. [错误码说明](#错误码说明)
12. [WebSocket 协议](#websocket 协议)

---

## 概述

Chinese Chess API 提供中国象棋游戏的完整后端功能，包括用户认证、游戏对局、AI 引擎、匹配系统、每日挑战、残局谜题等功能。

### 基础路径

| 环境 | URL |
|------|-----|
| 开发 | `http://localhost:8000` |
| 生产 | `https://api.chinese-chess.com` |

### API 版本

当前 API 版本为 **v1**，所有端点都以 `/api/v1/` 为前缀（健康检查端点除外）。

### 数据格式

- **请求格式**: `application/json`
- **响应格式**: `application/json`
- **字符编码**: `UTF-8`

### 响应格式

所有 API 响应遵循统一格式：

#### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2026-03-06T09:00:00Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": { ... }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 快速开始

### 1. 用户注册

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "chess_player",
    "email": "player@example.com",
    "password": "SecurePass123!"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

### 2. 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "chess_player",
    "password": "SecurePass123!"
  }'
```

### 3. 创建 AI 对局

```bash
curl -X POST http://localhost:8000/api/v1/ai/games/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "ai_level": 5,
    "time_control": {
      "initial_time": 600,
      "increment": 5
    },
    "player_color": "w"
  }'
```

### 4. 提交走棋

```bash
curl -X POST http://localhost:8000/api/v1/games/<game_id>/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "from_pos": "e3",
    "to_pos": "e4"
  }'
```

---

## 认证模块

**基础路径**: `/api/v1/auth/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/register/` | POST | ❌ | 用户注册 |
| `/login/` | POST | ❌ | 用户登录 |
| `/logout/` | POST | ✅ | 用户登出 |
| `/refresh/` | POST | ❌ | 刷新 Token |
| `/me/` | GET | ✅ | 获取当前用户 |

---

### POST /api/v1/auth/register/

**用户注册**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-20 字符） |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码（8-20 字符） |

#### 请求示例

```json
{
  "username": "chess_player",
  "email": "player@example.com",
  "password": "SecurePass123!"
}
```

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 400 | USERNAME_EXISTS | 用户名已存在 |
| 400 | EMAIL_EXISTS | 邮箱已存在 |

```json
{
  "success": false,
  "error": {
    "code": "USERNAME_EXISTS",
    "message": "用户名已存在"
  }
}
```

---

### POST /api/v1/auth/login/

**用户登录**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 请求示例

```json
{
  "username": "chess_player",
  "password": "SecurePass123!"
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "登录成功"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 401 | INVALID_CREDENTIALS | 用户名或密码错误 |
| 403 | USER_BANNED | 账号已被封禁 |
| 403 | USER_INACTIVE | 账号已被禁用 |

---

### POST /api/v1/auth/logout/

**用户登出**

#### 认证要求

需要有效的 JWT Access Token

#### 请求头

```
Authorization: Bearer <access_token>
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "登出成功"
}
```

---

### POST /api/v1/auth/refresh/

**刷新 Token**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | Refresh Token |

#### 请求示例

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "Token 刷新成功"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | TOKEN_REQUIRED | Refresh Token 不能为空 |
| 401 | TOKEN_INVALID | Token 已过期或无效 |

---

### GET /api/v1/auth/me/

**获取当前用户信息**

#### 认证要求

需要有效的 JWT Access Token

#### 请求头

```
Authorization: Bearer <access_token>
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "avatar": "https://example.com/avatar.png",
    "elo_rating": 1500,
    "created_at": "2026-01-15T08:30:00Z",
    "last_login": "2026-03-06T09:00:00Z"
  }
}
```

---

## 用户模块

**基础路径**: `/api/v1/users/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/profile/` | GET/PUT/PATCH | ✅ | 当前用户 Profile |
| `/me/stats/` | GET | ✅ | 当前用户统计 |
| `/{user_id}/` | GET/PUT/PATCH | ✅ | 用户详情 |
| `/{user_id}/password/` | PUT | ✅ | 修改密码 |
| `/{user_id}/stats/` | GET | ✅ | 用户统计 |
| `/{user_id}/games/` | GET | ✅ | 用户对局历史 |

---

### GET /api/v1/users/profile/

**获取当前用户 Profile**

#### 认证要求

需要有效的 JWT Access Token

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "avatar": "https://example.com/avatar.png",
    "elo_rating": 1500,
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "2026-01-15T08:30:00Z"
  }
}
```

---

### PUT /api/v1/users/profile/

**更新当前用户信息（全量更新）**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱 |
| avatar | string | 否 | 头像 URL |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "new_chess_player",
    "email": "new@example.com",
    "avatar": "https://example.com/new_avatar.png"
  },
  "message": "用户信息更新成功"
}
```

---

### PATCH /api/v1/users/profile/

**更新当前用户信息（部分更新）**

#### 请求示例

```json
{
  "avatar": "https://example.com/new_avatar.png"
}
```

---

### GET /api/v1/users/me/stats/

**获取当前用户统计**

#### 成功响应 (200 OK)

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

### GET /api/v1/users/{user_id}/

**获取用户详情**

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户 ID |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "avatar": "https://example.com/avatar.png",
    "elo_rating": 1500,
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "2026-01-15T08:30:00Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | USER_NOT_FOUND | 用户不存在 |

---

### PUT /api/v1/users/{user_id}/password/

**修改用户密码**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码（8-20 字符） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | USER_NOT_FOUND | 用户不存在 |
| 403 | PERMISSION_DENIED | 无权修改其他用户密码 |
| 400 | WRONG_OLD_PASSWORD | 旧密码错误 |
| 400 | SAME_PASSWORD | 新密码不能与旧密码相同 |

---

### GET /api/v1/users/{user_id}/stats/

**获取用户统计**

#### 成功响应 (200 OK)

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

### GET /api/v1/users/{user_id}/games/

**获取用户对局历史**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量（最大 100） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "opponent": {
          "id": "660e8400-e29b-41d4-a716-446655440001",
          "username": "opponent1",
          "avatar_url": "https://example.com/avatar.png",
          "rating": 1480
        },
        "result": "win",
        "rating_change": 15,
        "is_red": true,
        "game_type": "multiplayer",
        "created_at": "2026-03-06T08:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## 游戏对局模块

**基础路径**: `/api/v1/games/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/` | GET | ✅ | 获取对局列表 |
| `/games/` | POST | ✅ | 创建新对局 |
| `/games/{game_id}/` | GET | ✅ | 获取对局详情 |
| `/games/{game_id}/move/` | POST | ✅ | 提交走棋 |
| `/games/{game_id}/moves/` | GET | ✅ | 获取走棋历史 |
| `/games/{game_id}/status/` | PUT | ✅ | 更新对局状态 |
| `/games/{game_id}/` | DELETE | ✅ | 取消对局 |
| `/games/{game_id}/spectators/` | GET | ✅ | 获取观战者 |
| `/users/{user_id}/games/` | GET | ✅ | 获取用户对局 |

---

### GET /api/v1/games/games/

**获取对局列表**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | string | - | 游戏状态筛选（pending, playing, finished） |
| game_type | string | - | 游戏类型（single, multiplayer, ai） |
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量 |

#### 成功响应 (200 OK)

```json
{
  "count": 50,
  "next": "/api/v1/games/games/?page=2",
  "previous": null,
  "results": [
    {
      "game_id": "550e8400-e29b-41d4-a716-446655440000",
      "red_player": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "player1"
      },
      "black_player": {
        "user_id": "660e8400-e29b-41d4-a716-446655440001",
        "username": "player2"
      },
      "game_type": "multiplayer",
      "status": "playing",
      "created_at": "2026-03-06T08:00:00Z",
      "started_at": "2026-03-06T08:01:00Z"
    }
  ]
}
```

---

### POST /api/v1/games/games/

**创建新对局**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 是 | 游戏类型（single, multiplayer, ai） |
| black_player_id | UUID | 条件必填 | 多人模式时必填 |
| time_control | object | 否 | 时间控制 |
| time_control.initial_time | integer | 否 | 初始时间（秒），默认 600 |
| time_control.increment | integer | 否 | 每步加秒，默认 5 |

#### 请求示例

```json
{
  "game_type": "multiplayer",
  "black_player_id": "660e8400-e29b-41d4-a716-446655440001",
  "time_control": {
    "initial_time": 600,
    "increment": 5
  }
}
```

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "red_player": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player1"
    },
    "black_player": {
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "player2"
    },
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "move_count": 0,
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "created_at": "2026-03-06T09:00:00Z",
    "started_at": "2026-03-06T09:00:00Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |

---

### GET /api/v1/games/games/{game_id}/

**获取对局详情**

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "red_player": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player1"
    },
    "black_player": {
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "player2"
    },
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "move_count": 5,
    "red_time_remaining": 580,
    "black_time_remaining": 590,
    "winner": null,
    "created_at": "2026-03-06T09:00:00Z",
    "started_at": "2026-03-06T09:00:00Z",
    "finished_at": null
  }
}
```

---

### POST /api/v1/games/games/{game_id}/move/

**提交走棋**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from_pos | string | 是 | 起始位置（如 "e3"） |
| to_pos | string | 是 | 目标位置（如 "e4"） |

#### 请求示例

```json
{
  "from_pos": "e3",
  "to_pos": "e4"
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "move": {
    "move_id": "550e8400-e29b-41d4-a716-446655440000",
    "move_number": 6,
    "piece": {
      "type": "pawn",
      "color": "red"
    },
    "from_pos": "e3",
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

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | GAME_NOT_FOUND | 游戏不存在 |
| 400 | GAME_NOT_PLAYING | 游戏未进行中 |
| 400 | NOT_YOUR_TURN | 不是你的回合 |
| 400 | INVALID_MOVE | 无效走棋 |
| 400 | NO_PIECE | 起始位置没有棋子 |

---

### GET /api/v1/games/games/{game_id}/moves/

**获取走棋历史**

#### 成功响应 (200 OK)

```json
{
  "moves": [
    {
      "move_id": "550e8400-e29b-41d4-a716-446655440000",
      "move_number": 1,
      "piece": {
        "type": "cannon",
        "color": "red"
      },
      "from_pos": "h0",
      "to_pos": "h2",
      "is_capture": false,
      "is_check": false,
      "fen_after": "...",
      "time_remaining": 595
    }
  ]
}
```

---

### PUT /api/v1/games/games/{game_id}/status/

**更新对局状态**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态 |

**有效状态值**: `pending`, `playing`, `red_win`, `black_win`, `draw`, `aborted`

#### 请求示例

```json
{
  "status": "red_win"
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "red_win",
    "winner": "red",
    "finished_at": "2026-03-06T10:00:00Z",
    "duration": 1200
  }
}
```

---

### DELETE /api/v1/games/games/{game_id}/

**取消对局**

#### 成功响应 (204 No Content)

无内容返回

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | CANNOT_CANCEL | 无法取消已结束的游戏 |

---

### GET /api/v1/games/games/{game_id}/spectators/

**获取观战者列表**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 50 | 返回数量限制（最大 100） |

#### 成功响应 (200 OK)

```json
{
  "count": 10,
  "spectators": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "spectator1",
      "joined_at": "2026-03-06T09:00:00Z",
      "duration": 120,
      "is_anonymous": false
    }
  ]
}
```

---

### GET /api/v1/games/users/{user_id}/games/

**获取用户对局**

#### 成功响应 (200 OK)

```json
{
  "games": [
    {
      "game_id": "550e8400-e29b-41d4-a716-446655440000",
      "opponent": {...},
      "result": "win",
      "created_at": "2026-03-06T08:00:00Z"
    }
  ]
}
```

---

## 每日挑战模块

**基础路径**: `/api/v1/daily-challenge/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/today/` | GET | ❌ | 获取今日挑战 |
| `/today/attempt/` | POST | ✅ | 开始挑战 |
| `/today/move/` | POST | ✅ | 提交走法 |
| `/today/complete/` | POST | ✅ | 完成挑战 |
| `/leaderboard/` | GET | ❌ | 获取排行榜 |
| `/leaderboard/daily/` | GET | ❌ | 每日排行榜 |
| `/leaderboard/weekly/` | GET | ❌ | 周排行榜 |
| `/leaderboard/all-time/` | GET | ❌ | 总排行榜 |
| `/leaderboard/user/{id}/` | GET | ❌ | 用户排名 |
| `/streak/` | GET | ✅ | 用户连续打卡 |
| `/history/` | GET | ❌ | 挑战历史 |
| `/generate-tomorrow/` | POST | ✅(staff) | 生成明日挑战 |

---

### GET /api/v1/daily-challenge/today/

**获取今日挑战**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "challenge": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2026-03-06",
      "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
      "target_description": "红方先行，三步杀",
      "difficulty": 5,
      "stars": 3,
      "max_moves": 10,
      "time_limit": 300,
      "total_attempts": 1500,
      "unique_players": 800,
      "completion_rate": 0.35
    },
    "user_attempt": {
      "has_attempted": false
    }
  }
}
```

---

### POST /api/v1/daily-challenge/today/attempt/

**开始挑战**

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "attempt_id": "550e8400-e29b-41d4-a716-446655440000",
    "challenge_id": "550e8400-e29b-41d4-a716-446655440000",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "started_at": "2026-03-06T09:00:00Z",
    "time_limit": 300,
    "max_moves": 10
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | NO_CHALLENGE | 今日挑战尚未发布 |
| 400 | ALREADY_ATTEMPTED | 今日已尝试过 |

---

### POST /api/v1/daily-challenge/today/move/

**提交走法**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| attempt_id | string | 是 | 尝试 ID |
| from | string | 是 | 起始位置 |
| to | string | 是 | 目标位置 |
| piece | string | 是 | 棋子类型 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "correct": true,
    "message": "正确！",
    "fen_current": "...",
    "current_move_index": 1,
    "remaining_moves": 9,
    "is_complete": false
  }
}
```

---

### POST /api/v1/daily-challenge/today/complete/

**完成挑战**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| attempt_id | string | 是 | 尝试 ID |
| status | string | 否 | 状态（success/failed，默认 success） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "status": "success",
    "stars": 3,
    "points_earned": 100,
    "moves_used": 8,
    "time_used": 120
  }
}
```

---

### GET /api/v1/daily-challenge/leaderboard/

**获取排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | today | 日期（YYYY-MM-DD） |
| limit | integer | 100 | 返回数量 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "challenge_date": "2026-03-06",
    "leaderboard": [
      {
        "rank": 1,
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "player1",
        "score": 100,
        "stars_earned": 3,
        "time_used": 120,
        "moves_used": 8
      }
    ],
    "user_rank": {
      "rank": 50,
      "score": 80,
      "stars_earned": 2
    }
  }
}
```

---

### GET /api/v1/daily-challenge/leaderboard/daily/

**每日排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | today | 日期（YYYY-MM-DD） |
| limit | integer | 100 | 返回数量 |

---

### GET /api/v1/daily-challenge/leaderboard/weekly/

**周排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| week_start | string | 本周一 | 周起始日期（YYYY-MM-DD） |
| limit | integer | 100 | 返回数量 |

---

### GET /api/v1/daily-challenge/leaderboard/all-time/

**总排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 100 | 返回数量 |

---

### GET /api/v1/daily-challenge/leaderboard/user/{user_id}/

**用户排名查询**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | all-time | 排行榜类型（daily/weekly/all-time） |
| date | string | today | 日期（仅 daily 类型） |
| week_start | string | 本周一 | 周起始日期（仅 weekly 类型） |

---

### GET /api/v1/daily-challenge/streak/

**用户连续打卡**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "streak": {
      "current_streak": 7,
      "longest_streak": 15,
      "last_completion_date": "2026-03-05"
    },
    "statistics": {
      "total_completed": 50,
      "total_attempts": 60,
      "completion_rate": 83.3,
      "total_points": 5000,
      "best_stars": 150,
      "difficulty_stats": {
        "easy": 30,
        "medium": 15,
        "hard": 5
      }
    }
  }
}
```

---

### GET /api/v1/daily-challenge/history/

**挑战历史**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 30 | 返回数量 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "date": "2026-03-05",
        "difficulty": 5,
        "stars": 3,
        "target_description": "红方先行，三步杀",
        "total_attempts": 1500,
        "unique_players": 800,
        "completion_rate": 0.35
      }
    ]
  }
}
```

---

### POST /api/v1/daily-challenge/generate-tomorrow/

**生成明日挑战（管理员专用）**

#### 认证要求

需要管理员权限（is_staff=true）

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "challenge_id": "550e8400-e29b-41d4-a716-446655440000",
    "date": "2026-03-07",
    "difficulty": 5
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 403 | PERMISSION_DENIED | 需要管理员权限 |
| 500 | GENERATION_ERROR | 生成挑战失败 |

---

## AI 引擎模块

**基础路径**: `/api/v1/ai/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/` | GET | ✅ | 获取 AI 对局列表 |
| `/games/` | POST | ✅ | 创建 AI 对局 |
| `/games/{game_id}/` | GET | ✅ | 获取 AI 对局详情 |
| `/games/{game_id}/` | PUT | ✅ | 更新 AI 对局状态 |
| `/games/{game_id}/` | DELETE | ✅ | 取消 AI 对局 |
| `/games/{game_id}/move/` | POST | ✅ | 请求 AI 走棋 |
| `/games/{game_id}/hint/` | POST | ✅ | 请求 AI 提示 |
| `/games/{game_id}/analyze/` | POST | ✅ | 请求 AI 分析 |
| `/difficulties/` | GET | ❌ | 获取难度列表 |
| `/engines/status/` | GET | ✅ | 获取引擎状态 |

---

### GET /api/v1/ai/games/

**获取 AI 对局列表**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "player": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "player1"
      },
      "ai_level": 5,
      "status": "playing",
      "fen_current": "...",
      "turn": "w",
      "created_at": "2026-03-06T09:00:00Z"
    }
  ]
}
```

---

### POST /api/v1/ai/games/

**创建 AI 对局**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ai_level | integer | 是 | AI 难度等级（1-10） |
| time_control | object | 否 | 时间控制 |
| time_control.initial_time | integer | 否 | 初始时间（秒） |
| time_control.increment | integer | 否 | 每步加秒 |
| player_color | string | 否 | 玩家颜色（w/b，默认 w） |

#### 请求示例

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

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "player": {...},
    "ai_level": 5,
    "status": "playing",
    "fen_current": "...",
    "created_at": "2026-03-06T09:00:00Z"
  },
  "message": "AI 对局创建成功"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | INVALID_DIFFICULTY | 难度等级必须在 1-10 之间 |
| 400 | VALIDATION_ERROR | 参数验证失败 |

---

### GET /api/v1/ai/games/{game_id}/

**获取 AI 对局详情**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "player": {...},
    "ai_level": 5,
    "status": "playing",
    "fen_current": "...",
    "turn": "w",
    "move_count": 10,
    "created_at": "2026-03-06T09:00:00Z"
  }
}
```

---

### PUT /api/v1/ai/games/{game_id}/

**更新 AI 对局状态**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 状态（playing/finished/aborted） |
| winner | string | 否 | 获胜方（w/b/draw） |

---

### DELETE /api/v1/ai/games/{game_id}/

**取消 AI 对局**

#### 成功响应 (204 No Content)

无内容返回

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | INVALID_STATUS | 只能取消未开始或进行中的对局 |
| 403 | PERMISSION_DENIED | 无权删除此对局 |

---

### POST /api/v1/ai/games/{game_id}/move/

**请求 AI 走棋**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | FEN 字符串 |
| difficulty | integer | 否 | 难度等级（1-10，默认 5） |
| time_limit | integer | 否 | 时间限制（毫秒，默认 2000） |

#### 请求示例

```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "time_limit": 2000
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "from_pos": "h0",
    "to_pos": "h2",
    "piece": "cannon",
    "evaluation": 0.5,
    "depth": 8,
    "thinking_time": 950
  }
}
```

---

### POST /api/v1/ai/games/{game_id}/hint/

**请求 AI 提示**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | FEN 字符串 |
| difficulty | integer | 否 | 难度等级（默认 5） |
| count | integer | 否 | 返回提示数量（默认 3） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "hints": [
      {
        "from_pos": "h0",
        "to_pos": "h2",
        "evaluation": 0.5,
        "depth": 8
      }
    ]
  }
}
```

---

### POST /api/v1/ai/games/{game_id}/analyze/

**请求 AI 分析**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | FEN 字符串 |
| depth | integer | 否 | 分析深度（默认 15） |

#### 成功响应 (200 OK)

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
      {
        "move": "h0h2",
        "reason": "出车控制边路"
      }
    ]
  }
}
```

---

### GET /api/v1/ai/difficulties/

**获取难度列表**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "difficulties": [
      {
        "level": 1,
        "name": "入门",
        "description": "800 Elo",
        "elo_estimate": 800,
        "skill_level": 0,
        "search_depth": 1,
        "think_time_ms": 500
      },
      {
        "level": 5,
        "name": "中级",
        "description": "1500 Elo",
        "elo_estimate": 1500,
        "skill_level": 5,
        "search_depth": 8,
        "think_time_ms": 2000
      },
      {
        "level": 10,
        "name": "大师",
        "description": "2800 Elo",
        "elo_estimate": 2800,
        "skill_level": 10,
        "search_depth": 15,
        "think_time_ms": 5000
      }
    ]
  }
}
```

---

### GET /api/v1/ai/engines/status/

**获取引擎状态**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "pool_size": 10,
    "available": 8,
    "in_use": 2
  }
}
```

---

## 匹配系统模块

**基础路径**: `/api/v1/matchmaking/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/start/` | POST | ✅ | 开始匹配 |
| `/cancel/` | POST | ✅ | 取消匹配 |
| `/status/` | GET | ✅ | 获取匹配状态 |

---

### POST /api/v1/matchmaking/start/

**开始匹配**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 否 | 游戏类型（ranked/casual，默认 ranked） |

#### 请求示例

```json
{
  "game_type": "ranked"
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "加入匹配队列成功",
  "game_type": "ranked",
  "queue_position": 5,
  "estimated_wait_time": 30
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | ALREADY_IN_QUEUE | 已在队列中 |
| 429 | QUEUE_FULL | 队列已满 |

---

### POST /api/v1/matchmaking/cancel/

**取消匹配**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 否 | 游戏类型（ranked/casual，默认 ranked） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "已取消匹配"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | NOT_IN_QUEUE | 不在队列中 |

---

### GET /api/v1/matchmaking/status/

**获取匹配状态**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| game_type | string | ranked | 游戏类型 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "in_queue": true,
  "queue_position": 5,
  "estimated_wait_time": 30,
  "total_in_queue": 50
}
```

---

### GET /api/v1/ranking/leaderboard/

**获取排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量（最大 100） |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player1",
      "avatar": "https://example.com/avatar.png",
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

### GET /api/v1/ranking/user/{user_id}/

**获取用户排名**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "player1",
    "rating": 1500,
    "rank": 125,
    "games_played": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 60.0,
    "highest_rating": 1550,
    "rating_change_24h": 15
  }
}
```

---

### GET /api/v1/ranking/user/

**获取当前用户排名**

#### 认证要求

需要有效的 JWT Access Token

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "player1",
    "rating": 1500,
    "rank": 125,
    "games_played": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 60.0
  }
}
```

---

## 残局谜题模块

**基础路径**: `/api/v1/puzzles/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | ✅ | 获取谜题列表 |
| `/{puzzle_id}/` | GET | ✅ | 获取谜题详情 |
| `/{puzzle_id}/attempt/` | POST | ✅ | 开始挑战 |
| `/{puzzle_id}/attempts/{attempt_id}/move/` | POST | ✅ | 提交走法 |
| `/{puzzle_id}/attempts/{attempt_id}/complete/` | POST | ✅ | 完成挑战 |
| `/progress/` | GET | ✅ | 用户进度 |
| `/leaderboard/` | GET | ✅ | 排行榜 |

---

### GET /api/v1/puzzles/

**获取谜题列表**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| difficulty | integer | - | 难度筛选（1-10） |
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
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

### GET /api/v1/puzzles/{puzzle_id}/

**获取谜题详情**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "千里独行",
    "difficulty": 5,
    "category": "车兵类",
    "description": "红方先行，一步杀",
    "fen_initial": "...",
    "move_limit": 10,
    "time_limit": 300,
    "completed_count": 1500,
    "user_completed": false
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | PUZZLE_NOT_FOUND | 关卡不存在 |

---

### POST /api/v1/puzzles/{puzzle_id}/attempt/

**开始挑战**

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "attempt_id": "550e8400-e29b-41d4-a716-446655440000",
    "puzzle_id": "550e8400-e29b-41d4-a716-446655440000",
    "fen_current": "...",
    "status": "in_progress",
    "current_move_index": 0,
    "move_limit": 10,
    "time_limit": 300,
    "started_at": "2026-03-06T09:00:00Z"
  }
}
```

---

### POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/move/

**提交走法**

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | string | 是 | 起始位置 |
| to | string | 是 | 目标位置 |
| piece | string | 是 | 棋子类型 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "correct": true,
    "message": "正确！",
    "fen_current": "...",
    "current_move_index": 1,
    "remaining_moves": 9,
    "is_complete": false
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | NOT_FOUND | 关卡或挑战不存在 |

---

### POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/complete/

**完成挑战**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "status": "success",
    "stars": 3,
    "points_earned": 100,
    "moves_used": 8,
    "time_used": 120
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | ATTEMPT_NOT_FOUND | 挑战不存在 |
| 400 | NOT_COMPLETE | 挑战尚未完成 |

---

### GET /api/v1/puzzles/progress/

**用户进度**

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "total_completed": 50,
    "total_attempts": 80,
    "completion_rate": 62.5,
    "total_points": 5000,
    "best_stars": 150,
    "difficulty_stats": {
      "easy": 30,
      "medium": 15,
      "hard": 5
    }
  }
}
```

---

### GET /api/v1/puzzles/leaderboard/

**排行榜**

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| time_range | string | all | 时间范围（daily/weekly/all） |
| limit | integer | 100 | 返回数量 |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "player1",
        "ranking_points": 10000,
        "total_completed": 200,
        "best_stars": 180
      }
    ],
    "user_rank": {
      "rank": 50,
      "ranking_points": 5000,
      "total_completed": 50
    }
  }
}
```

---

## 健康检查模块

**基础路径**: `/api/health/`

### 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | ❌ | 综合健康检查 |
| `/db/` | GET | ❌ | 数据库状态 |
| `/redis/` | GET | ❌ | Redis 状态 |
| `/websocket/` | GET | ❌ | WebSocket 状态 |

---

### GET /api/health/

**综合健康检查**

#### 成功响应 (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T12:00:00Z",
  "version": "v1.0.0",
  "components": {
    "django": {
      "status": "healthy",
      "version": "5.0",
      "debug": false
    },
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2,
      "engine": "django.db.backends.sqlite3",
      "name": "/path/to/db.sqlite3"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "backend": "RedisCache",
      "location": "redis://localhost:6379/0"
    },
    "websocket": {
      "status": "healthy",
      "backend": "RedisChannelLayer"
    },
    "python": {
      "status": "healthy",
      "version": "3.9.0"
    },
    "system": {
      "status": "healthy",
      "timestamp": "2026-03-06T12:00:00Z",
      "uptime_seconds": 86400
    }
  },
  "overall_healthy": true
}
```

---

### GET /api/health/db/

**数据库健康检查**

#### 成功响应 (200 OK)

```json
{
  "component": "database",
  "status": "healthy",
  "response_time_ms": 5.2,
  "timestamp": "2026-03-06T12:00:00Z",
  "engine": "django.db.backends.sqlite3",
  "name": "/path/to/db.sqlite3",
  "version": "3.39.0"
}
```

---

### GET /api/health/redis/

**Redis 健康检查**

#### 成功响应 (200 OK)

```json
{
  "component": "redis",
  "status": "healthy",
  "response_time_ms": 2.1,
  "timestamp": "2026-03-06T12:00:00Z",
  "backend": "RedisCache",
  "location": "redis://localhost:6379/0",
  "redis_version": "7.0.0"
}
```

---

### GET /api/health/websocket/

**WebSocket 健康检查**

#### 成功响应 (200 OK)

```json
{
  "component": "websocket",
  "status": "healthy",
  "response_time_ms": 3.5,
  "timestamp": "2026-03-06T12:00:00Z",
  "backend": "RedisChannelLayer",
  "config": {
    "type": "channels.layers.RedisChannelLayer",
    "config": {
      "hosts": ["redis://localhost:6379/0"]
    }
  }
}
```

---

## 错误码说明

详见：[errors.md](./errors.md)

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": { ... }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

### 常见错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| VALIDATION_ERROR | 400 | 参数验证失败 |
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| TOKEN_REQUIRED | 400 | Token 不能为空 |
| TOKEN_INVALID | 401 | Token 已过期或无效 |
| USER_NOT_FOUND | 404 | 用户不存在 |
| PERMISSION_DENIED | 403 | 权限不足 |
| GAME_NOT_FOUND | 404 | 游戏不存在 |
| INVALID_MOVE | 400 | 无效走棋 |
| NOT_YOUR_TURN | 400 | 不是你的回合 |

---

## WebSocket 协议

详见：[websocket.md](./websocket.md)

### 连接端点

```
ws://localhost:8000/ws/game/{game_id}/
```

### 认证方式

在连接 URL 中添加 Token：

```
ws://localhost:8000/ws/game/{game_id}/?token=<access_token>
```

### 消息类型

#### 客户端 → 服务器

| 类型 | 描述 | 数据格式 |
|------|------|----------|
| `move` | 提交走棋 | `{"from_pos": "e3", "to_pos": "e4"}` |
| `chat_message` | 发送聊天 | `{"content": "你好!", "type": "text"}` |

#### 服务器 → 客户端

| 类型 | 描述 | 数据格式 |
|------|------|----------|
| `move_result` | 走棋结果 | `{"success": true, "move": {...}, "fen": "..."}` |
| `opponent_move` | 对手走棋 | `{"move": {...}}` |
| `game_state` | 游戏状态 | `{"fen": "...", "turn": "w", "status": "playing"}` |
| `chat_message` | 聊天消息 | `{"sender": "player1", "content": "你好!", "type": "text"}` |
| `spectator_join` | 观战者加入 | `{"username": "spectator1"}` |
| `spectator_leave` | 观战者离开 | `{"username": "spectator1"}` |

---

## API 端点统计

| 模块 | 端点数量 | 认证要求 |
|------|---------|---------|
| 认证 API | 5 | 部分公开 |
| 用户 API | 8 | 已认证 |
| 游戏 API | 9 | 已认证 |
| 每日挑战 API | 12 | 部分公开 |
| AI 引擎 API | 10 | 部分公开 |
| 匹配系统 API | 5 | 部分公开 |
| 残局谜题 API | 7 | 已认证 |
| 健康检查 API | 4 | 公开 |
| **总计** | **60** | - |

---

## 支持

### 问题反馈

- **GitHub Issues**: https://github.com/chinese-chess/api/issues
- **文档问题**: 请在 Issue 中标记 `documentation` 标签

### 联系方式

- **技术支持**: support@chinese-chess.com
- **商务合作**: business@chinese-chess.com

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
