# 中国象棋 API 文档

**版本**: v1.0.0  
**最后更新**: 2026-03-06  
**基础路径**: `/api/v1`

---

## 📋 目录

1. [认证流程](#认证流程)
2. [认证 API](#认证-api) - 5 个端点
3. [用户 API](#用户-api) - 8 个端点
4. [游戏 API](#游戏-api) - 8 个端点
5. [观战 API](#观战-api) - 6 个端点
6. [聊天 API](#聊天-api) - 4 个端点
7. [匹配 API](#匹配-api) - 3 个端点
8. [排行榜 API](#排行榜-api) - 3 个端点
9. [AI API](#ai-api) - 10 个端点
10. [残局 API](#残局-api) - 7 个端点
11. [健康检查 API](#健康检查-api) - 1 个端点
12. [错误码说明](#错误码说明)
13. [API 使用示例](#api 使用示例)

---

## 🔐 认证流程

### JWT Token 认证

本 API 使用 JWT (JSON Web Token) 进行认证。认证流程如下:

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  客户端   │     │   API    │     │  受保护   │
│          │────▶│  认证端点  │────▶│  资源     │
│          │◀────│          │◀────│          │
└──────────┘     └──────────┘     └──────────┘
     │                  │
     │  1. 登录/注册     │
     │─────────────────▶│
     │                  │
     │  2. 返回 Tokens   │
     │  - access_token  │
     │  - refresh_token │
     │◀─────────────────│
     │                  │
     │  3. 请求资源     │
     │  (携带 access_token)│
     │─────────────────▶│
     │                  │
     │  4. 返回数据     │
     │◀─────────────────│
     │                  │
     │  5. Token 过期   │
     │─────────────────▶│
     │                  │
     │  6. 刷新 Token   │
     │  (携带 refresh_token)│
     │─────────────────▶│
     │                  │
     │  7. 新 access_token│
     │◀─────────────────│
```

### Token 说明

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| Access Token | 2 小时 | 访问受保护资源 |
| Refresh Token | 7 天 | 刷新 Access Token |

### 请求头格式

所有需要认证的请求需包含以下 Header:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## 🔑 认证 API

**基础路径**: `/api/v1/auth`

### 1. 用户注册

**端点**: `POST /api/v1/auth/register/`

**权限**: 公开 (无需认证)

**请求体**:
```json
{
  "username": "string (3-20 字符，必填)",
  "email": "string (邮箱格式，必填)",
  "password": "string (8-20 字符，必填)"
}
```

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "access_token": "jwt_token",
    "refresh_token": "jwt_token",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

**失败响应** (400):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "用户名已存在"
  }
}
```

**错误码**:
- `VALIDATION_ERROR`: 验证失败
- `USERNAME_EXISTS`: 用户名已存在
- `EMAIL_EXISTS`: 邮箱已存在

---

### 2. 用户登录

**端点**: `POST /api/v1/auth/login/`

**权限**: 公开

**请求体**:
```json
{
  "username": "string (必填)",
  "password": "string (必填)"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "access_token": "jwt_token",
    "refresh_token": "jwt_token",
    "expires_in": 7200
  },
  "message": "登录成功"
}
```

**失败响应** (401):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

**错误码**:
- `INVALID_CREDENTIALS`: 用户名或密码错误
- `USER_BANNED`: 账号已被封禁
- `USER_INACTIVE`: 账号已被禁用

---

### 3. 用户登出

**端点**: `POST /api/v1/auth/logout/`

**权限**: 已认证

**请求头**:
```http
Authorization: Bearer <access_token>
```

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
  "refresh_token": "jwt_token (必填)"
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

**失败响应** (401):
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Refresh Token 已过期或无效"
  }
}
```

---

### 5. 获取当前用户信息

**端点**: `GET /api/v1/auth/me/`

**权限**: 已认证

**请求头**:
```http
Authorization: Bearer <access_token>
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "avatar": "url",
    "created_at": "datetime",
    "last_login": "datetime"
  }
}
```

---

## 👤 用户 API

**基础路径**: `/api/v1/users`

### 1. 获取当前用户 Profile

**端点**: `GET /api/v1/users/profile/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "avatar": "url",
    "elo_rating": 1500,
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "datetime"
  }
}
```

---

### 2. 更新当前用户信息

**端点**: 
- `PUT /api/v1/users/profile/` (全量更新)
- `PATCH /api/v1/users/profile/` (部分更新)

**权限**: 已认证 (只能更新自己的信息)

**请求体**:
```json
{
  "username": "string (可选)",
  "email": "string (可选)",
  "avatar": "url (可选)"
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "avatar": "url"
  },
  "message": "用户信息更新成功"
}
```

---

### 3. 获取当前用户统计

**端点**: `GET /api/v1/users/me/stats/`

**权限**: 已认证

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

### 4. 获取用户详情

**端点**: `GET /api/v1/users/{user_id}/`

**权限**: 已认证

**路径参数**:
- `user_id`: 用户 ID

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "avatar": "url",
    "elo_rating": 1500,
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "datetime"
  }
}
```

**错误响应** (404):
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在"
  }
}
```

---

### 5. 更新用户信息

**端点**: 
- `PUT /api/v1/users/{user_id}/` (全量更新)
- `PATCH /api/v1/users/{user_id}/` (部分更新)

**权限**: 已认证 (只能更新自己的信息，管理员除外)

**请求体**:
```json
{
  "username": "string (可选)",
  "email": "string (可选)",
  "avatar": "url (可选)"
}
```

**错误码**:
- `USER_NOT_FOUND`: 用户不存在
- `PERMISSION_DENIED`: 无权修改其他用户信息
- `VALIDATION_ERROR`: 验证失败

---

### 6. 修改密码

**端点**: `PUT /api/v1/users/{user_id}/password/`

**权限**: 已认证 (只能修改自己的密码)

**请求体**:
```json
{
  "old_password": "string (必填)",
  "new_password": "string (必填，8-20 字符)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

**错误码**:
- `USER_NOT_FOUND`: 用户不存在
- `PERMISSION_DENIED`: 无权修改其他用户密码
- `WRONG_OLD_PASSWORD`: 旧密码错误
- `SAME_PASSWORD`: 新密码不能与旧密码相同
- `PASSWORD_CHANGE_FAILED`: 密码修改失败

---

### 7. 获取用户统计

**端点**: `GET /api/v1/users/{user_id}/stats/`

**权限**: 已认证

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

### 8. 获取用户对局历史

**端点**: `GET /api/v1/users/{user_id}/games/`

**权限**: 已认证

**查询参数**:
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
        "opponent": {
          "id": "uuid",
          "username": "string",
          "avatar_url": "url",
          "rating": 1500
        },
        "result": "win",
        "rating_change": 15,
        "is_red": true,
        "game_type": "multiplayer",
        "created_at": "datetime"
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

## ♟️ 游戏 API

**基础路径**: `/api/v1/games`

### 1. 获取游戏列表

**端点**: `GET /api/v1/games/games/`

**权限**: 已认证

**查询参数**:
- `status`: 游戏状态筛选 (pending, playing, finished)
- `game_type`: 游戏类型 (single, multiplayer, ai)
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
      "red_player": {
        "user_id": "uuid",
        "username": "string"
      },
      "black_player": {
        "user_id": "uuid",
        "username": "string"
      },
      "game_type": "multiplayer",
      "status": "playing",
      "created_at": "datetime",
      "started_at": "datetime"
    }
  ]
}
```

---

### 2. 创建游戏

**端点**: `POST /api/v1/games/games/`

**权限**: 已认证

**请求体**:
```json
{
  "game_type": "single | multiplayer | ai (必填)",
  "black_player_id": "uuid (多人模式必填)",
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
    "red_player": {
      "user_id": "uuid",
      "username": "string"
    },
    "black_player": {
      "user_id": "uuid",
      "username": "string"
    },
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "move_count": 0,
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "created_at": "datetime",
    "started_at": "datetime"
  }
}
```

---

### 3. 获取游戏详情

**端点**: `GET /api/v1/games/games/{game_id}/`

**权限**: 已认证 (参与者或观战者)

**响应** (200):
```json
{
  "success": true,
  "data": {
    "game_id": "uuid",
    "red_player": {
      "user_id": "uuid",
      "username": "string"
    },
    "black_player": {
      "user_id": "uuid",
      "username": "string"
    },
    "game_type": "multiplayer",
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "move_count": 5,
    "red_time_remaining": 580,
    "black_time_remaining": 590,
    "winner": null,
    "created_at": "datetime",
    "started_at": "datetime",
    "finished_at": null
  }
}
```

---

### 4. 提交走棋

**端点**: `POST /api/v1/games/games/{game_id}/move/`

**权限**: 已认证 (游戏参与者)

**请求体**:
```json
{
  "from_pos": "e0 (必填)",
  "to_pos": "e4 (必填)"
}
```

**成功响应** (200):
```json
{
  "success": true,
  "move": {
    "move_id": "uuid",
    "move_number": 6,
    "piece": {
      "type": "pawn",
      "color": "red"
    },
    "from_pos": "e0",
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

**错误码**:
- `GAME_NOT_FOUND`: 游戏不存在
- `GAME_NOT_PLAYING`: 游戏未进行中
- `NOT_YOUR_TURN`: 不是你的回合
- `INVALID_MOVE`: 无效走棋
- `NO_PIECE`: 起始位置没有棋子

---

### 5. 获取走棋历史

**端点**: `GET /api/v1/games/games/{game_id}/moves/`

**权限**: 已认证

**响应** (200):
```json
{
  "moves": [
    {
      "move_id": "uuid",
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

### 6. 更新游戏状态

**端点**: `PUT /api/v1/games/games/{game_id}/status/`

**权限**: 已认证 (管理员或参与者)

**请求体**:
```json
{
  "status": "pending | playing | red_win | black_win | draw | aborted (必填)"
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "game_id": "uuid",
    "status": "red_win",
    "winner": "red",
    "finished_at": "datetime",
    "duration": 1200
  }
}
```

---

### 7. 取消游戏

**端点**: `DELETE /api/v1/games/games/{game_id}/`

**权限**: 已认证 (游戏参与者)

**响应** (204): 无内容

**错误响应** (400):
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_CANCEL",
    "message": "无法取消已结束的游戏"
  }
}
```

---

### 8. 获取用户对局

**端点**: `GET /api/v1/games/users/{user_id}/games/`

**权限**: 已认证 (只能查看自己的对局，管理员除外)

**响应** (200):
```json
{
  "games": [
    {
      "game_id": "uuid",
      "opponent": {...},
      "result": "win",
      "created_at": "datetime"
    }
  ]
}
```

---

## 👁️ 观战 API

**基础路径**: `/api/v1/games/{game_id}` 和 `/api/v1/spectator`

### 1. 加入观战

**端点**: `POST /api/v1/games/{game_id}/spectate/`

**权限**: 已认证

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
    "joined_at": "datetime",
    "is_anonymous": false
  },
  "game_state": {
    "id": "uuid",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "status": "playing",
    "move_count": 15
  },
  "message": "加入观战成功"
}
```

**错误码**:
- `GAME_NOT_FOUND`: 游戏不存在
- `GAME_FINISHED`: 游戏已结束
- `CANNOT_SPECTATE_PLAYERS`: 玩家不能观战自己的游戏
- `ALREADY_WATCHING`: 已在观战

---

### 2. 离开观战

**端点**: `POST /api/v1/games/{game_id}/spectate/leave/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "duration": 120,
  "message": "离开观战成功"
}
```

---

### 3. 获取观战列表

**端点**: `GET /api/v1/games/{game_id}/spectators/`

**权限**: 已认证

**查询参数**:
- `limit`: 返回数量限制 (默认 50, 最大 100)

**响应** (200):
```json
{
  "count": 10,
  "spectators": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "username": "string",
      "joined_at": "datetime",
      "duration": 120,
      "is_anonymous": false
    }
  ]
}
```

---

### 4. 踢出观战者

**端点**: `POST /api/v1/games/{game_id}/spectators/kick/`

**权限**: 已认证 (游戏参与者或管理员)

**请求体**:
```json
{
  "spectator_id": "uuid (必填)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "已将 xxx 踢出观战"
}
```

---

### 5. 获取可观看的对局列表

**端点**: `GET /api/v1/spectator/active-games/`

**权限**: 已认证

**查询参数**:
- `limit`: 返回数量限制 (默认 20)

**响应** (200):
```json
{
  "count": 10,
  "games": [
    {
      "id": "uuid",
      "status": "playing",
      "move_count": 15,
      "spectator_count": 5,
      "red_player": {
        "id": "uuid",
        "username": "string",
        "rating": 1500
      },
      "black_player": {
        "id": "uuid",
        "username": "string",
        "rating": 1480
      },
      "time_control": {
        "base": 600,
        "increment": 5
      },
      "created_at": "datetime"
    }
  ]
}
```

---

### 6. 获取观战者详细信息

**端点**: `GET /api/v1/games/{game_id}/spectators/{spectator_id}/`

**权限**: 已认证 (只能查看自己的信息，或游戏参与者/管理员)

**响应** (200):
```json
{
  "id": "uuid",
  "game_id": "uuid",
  "user": {
    "id": "uuid",
    "username": "string"
  },
  "status": "watching",
  "joined_at": "datetime",
  "left_at": "datetime",
  "duration": 120,
  "is_anonymous": false
}
```

---

## 💬 聊天 API

**基础路径**: `/api/v1/chat`

### 1. 发送聊天消息

**端点**: `POST /api/v1/chat/games/{game_id}/send/`

**权限**: 已认证 (游戏参与者或观战者)

**请求体**:
```json
{
  "content": "string (必填，最大 500 字符)",
  "message_type": "text | emoji | system (必填)",
  "room_type": "game | spectator (必填)"
}
```

**成功响应** (201):
```json
{
  "success": true,
  "message": {
    "id": "uuid",
    "sender": {
      "user_id": "uuid",
      "username": "string"
    },
    "content": "你好!",
    "message_type": "text",
    "room_type": "game",
    "created_at": "datetime",
    "is_deleted": false
  }
}
```

**错误码**:
- `ROOM_NOT_FOUND`: 房间不存在
- `EMPTY_CONTENT`: 消息内容不能为空
- `CONTENT_TOO_LONG`: 消息内容过长
- `RATE_LIMITED`: 发送过于频繁
- `INVALID_EMOJI`: 无效的 emoji
- `PERMISSION_DENIED`: 无权发送系统消息

---

### 2. 获取聊天历史

**端点**: `GET /api/v1/chat/games/{game_id}/history/`

**权限**: 已认证 (游戏参与者或观战者)

**查询参数**:
- `room_type`: game | spectator (必填)
- `limit`: 返回数量 (默认 50, 最大 100)
- `page`: 页码
- `page_size`: 每页数量

**响应** (200):
```json
{
  "success": true,
  "messages": [
    {
      "id": "uuid",
      "sender": {
        "user_id": "uuid",
        "username": "string"
      },
      "content": "你好!",
      "message_type": "text",
      "room_type": "game",
      "created_at": "datetime",
      "is_deleted": false
    }
  ],
  "has_more": true
}
```

---

### 3. 删除聊天消息

**端点**: `DELETE /api/v1/chat/messages/{message_uuid}/delete/`

**权限**: 已认证 (消息发送者或管理员)

**响应** (200):
```json
{
  "success": true,
  "message": "消息已删除"
}
```

---

### 4. 获取聊天统计

**端点**: `GET /api/v1/chat/games/{game_id}/stats/`

**权限**: 已认证

**响应** (200):
```json
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

## 🎯 匹配 API

**基础路径**: `/api/v1/matchmaking`

### 1. 开始匹配

**端点**: `POST /api/v1/matchmaking/start/`

**权限**: 已认证

**请求体**:
```json
{
  "game_type": "ranked | casual (默认 ranked)"
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

**错误码**:
- `ALREADY_IN_QUEUE`: 已在队列中
- `QUEUE_FULL`: 队列已满

---

### 2. 取消匹配

**端点**: `POST /api/v1/matchmaking/cancel/`

**权限**: 已认证

**请求体**:
```json
{
  "game_type": "ranked | casual (默认 ranked)"
}
```

**响应** (200):
```json
{
  "success": true,
  "message": "已取消匹配"
}
```

**错误码**:
- `NOT_IN_QUEUE`: 不在队列中

---

### 3. 获取匹配状态

**端点**: `GET /api/v1/matchmaking/status/`

**权限**: 已认证

**查询参数**:
- `game_type`: ranked | casual (默认 ranked)

**响应** (200):
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

## 🏆 排行榜 API

**基础路径**: `/api/v1/ranking`

### 1. 获取排行榜

**端点**: `GET /api/v1/ranking/leaderboard/`

**权限**: 公开

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
      "username": "string",
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

### 2. 获取用户排名

**端点**: `GET /api/v1/ranking/user/{user_id}/`

**权限**: 公开

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
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

### 3. 获取当前用户排名

**端点**: `GET /api/v1/ranking/user/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
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

## 🤖 AI API

**基础路径**: `/api/v1/ai`

### 1. 获取 AI 对局列表

**端点**: `GET /api/v1/ai/games/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "player": {
        "user_id": "uuid",
        "username": "string"
      },
      "ai_level": 5,
      "status": "playing",
      "fen_current": "...",
      "turn": "w",
      "created_at": "datetime"
    }
  ]
}
```

---

### 2. 创建 AI 对局

**端点**: `POST /api/v1/ai/games/`

**权限**: 已认证

**请求体**:
```json
{
  "ai_level": 5 (1-10, 默认 5)",
  "time_control": {
    "initial_time": 600,
    "increment": 5
  },
  "player_color": "w | b (默认 w)"
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
    "created_at": "datetime"
  },
  "message": "AI 对局创建成功"
}
```

**错误码**:
- `INVALID_DIFFICULTY`: 难度等级必须在 1-10 之间
- `VALIDATION_ERROR`: 参数验证失败

---

### 3. 获取 AI 对局详情

**端点**: `GET /api/v1/ai/games/{game_id}/`

**权限**: 已认证 (只能查看自己的对局)

**响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "player": {...},
    "ai_level": 5,
    "status": "playing",
    "fen_current": "...",
    "turn": "w",
    "move_count": 10,
    "created_at": "datetime"
  }
}
```

---

### 4. 更新 AI 对局状态

**端点**: `PUT /api/v1/ai/games/{game_id}/`

**权限**: 已认证 (只能修改自己的对局)

**请求体**:
```json
{
  "status": "playing | finished | aborted (必填)",
  "winner": "w | b | draw (可选)"
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {...}
}
```

---

### 5. 取消 AI 对局

**端点**: `DELETE /api/v1/ai/games/{game_id}/`

**权限**: 已认证 (只能删除自己的对局)

**响应** (204): 无内容

**错误码**:
- `INVALID_STATUS`: 只能取消未开始或进行中的对局
- `PERMISSION_DENIED`: 无权删除此对局

---

### 6. 请求 AI 走棋

**端点**: `POST /api/v1/ai/games/{game_id}/move/`

**权限**: 已认证

**请求体**:
```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1 (必填)",
  "difficulty": 5 (1-10, 默认 5)",
  "time_limit": 2000 (毫秒，可选)
}
```

**响应** (200):
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

### 7. 请求 AI 提示

**端点**: `POST /api/v1/ai/games/{game_id}/hint/`

**权限**: 已认证

**请求体**:
```json
{
  "fen": "string (必填)",
  "difficulty": 5 (可选)",
  "count": 3 (返回提示数量，可选)
}
```

**响应** (200):
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

### 8. 请求 AI 分析

**端点**: `POST /api/v1/ai/games/{game_id}/analyze/`

**权限**: 已认证

**请求体**:
```json
{
  "fen": "string (必填)",
  "depth": 15 (分析深度，可选)
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
      {
        "move": "h0h2",
        "reason": "出车控制边路"
      }
    ]
  }
}
```

---

### 9. 获取难度列表

**端点**: `GET /api/v1/ai/difficulties/`

**权限**: 公开

**响应** (200):
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

### 10. 获取引擎状态

**端点**: `GET /api/v1/ai/engines/status/`

**权限**: 已认证

**响应** (200):
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

## 🧩 残局 API

**基础路径**: `/api/v1/puzzles`

### 1. 获取关卡列表

**端点**: `GET /api/v1/puzzles/`

**权限**: 已认证

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

### 2. 获取关卡详情

**端点**: `GET /api/v1/puzzles/{puzzle_id}/`

**权限**: 已认证

**响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
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

**错误码**:
- `PUZZLE_NOT_FOUND`: 关卡不存在

---

### 3. 创建挑战

**端点**: `POST /api/v1/puzzles/{puzzle_id}/attempt/`

**权限**: 已认证

**响应** (201):
```json
{
  "success": true,
  "data": {
    "attempt_id": "uuid",
    "puzzle_id": "uuid",
    "fen_current": "...",
    "status": "in_progress",
    "current_move_index": 0,
    "move_limit": 10,
    "time_limit": 300,
    "started_at": "datetime"
  }
}
```

---

### 4. 提交走法

**端点**: `POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/move/`

**权限**: 已认证

**请求体**:
```json
{
  "from": "e2",
  "to": "e4",
  "piece": "P"
}
```

**响应** (200):
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

### 5. 完成挑战

**端点**: `POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/complete/`

**权限**: 已认证

**响应** (200):
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

**错误码**:
- `ATTEMPT_NOT_FOUND`: 挑战不存在
- `NOT_COMPLETE`: 挑战尚未完成

---

### 6. 获取用户进度

**端点**: `GET /api/v1/puzzles/progress/`

**权限**: 已认证

**响应** (200):
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

### 7. 获取残局排行榜

**端点**: `GET /api/v1/puzzles/leaderboard/`

**权限**: 已认证

**查询参数**:
- `time_range`: daily | weekly | all (默认 all)
- `limit`: 返回数量 (默认 100)

**响应** (200):
```json
{
  "success": true,
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "user_id": "uuid",
        "username": "string",
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

## 🏥 健康检查 API

**基础路径**: `/api/v1/health`

### 1. 健康检查

**端点**: `GET /api/v1/health/`

**权限**: 公开

**响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T12:00:00Z",
  "version": "v1.0.0",
  "services": {
    "database": "ok",
    "cache": "ok",
    "ai_engine": "ok"
  }
}
```

---

## ❌ 错误码说明

### 认证相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `VALIDATION_ERROR` | 400 | 验证失败 |
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `USER_BANNED` | 403 | 账号已被封禁 |
| `USER_INACTIVE` | 403 | 账号已被禁用 |
| `TOKEN_REQUIRED` | 401 | Token 不能为空 |
| `TOKEN_INVALID` | 401 | Token 已过期或无效 |
| `TOKEN_EXPIRED` | 401 | Token 已过期 |
| `USERNAME_EXISTS` | 400 | 用户名已存在 |
| `EMAIL_EXISTS` | 400 | 邮箱已存在 |

### 用户相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `WRONG_OLD_PASSWORD` | 400 | 旧密码错误 |
| `SAME_PASSWORD` | 400 | 新密码不能与旧密码相同 |
| `PASSWORD_CHANGE_FAILED` | 400 | 密码修改失败 |

### 游戏相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `GAME_NOT_FOUND` | 404 | 游戏不存在 |
| `GAME_NOT_PLAYING` | 400 | 游戏未进行中 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 |
| `INVALID_MOVE` | 400 | 无效走棋 |
| `NO_PIECE` | 400 | 起始位置没有棋子 |
| `CANNOT_CANCEL` | 400 | 无法取消已结束的游戏 |

### 观战相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `GAME_FINISHED` | 400 | 游戏已结束 |
| `CANNOT_SPECTATE_PLAYERS` | 403 | 玩家不能观战自己的游戏 |
| `ALREADY_WATCHING` | 400 | 已在观战 |
| `NOT_WATCHING` | 404 | 未在观战 |

### 聊天相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `ROOM_NOT_FOUND` | 404 | 房间不存在 |
| `EMPTY_CONTENT` | 400 | 消息内容不能为空 |
| `CONTENT_TOO_LONG` | 400 | 消息内容过长 |
| `RATE_LIMITED` | 429 | 发送过于频繁 |
| `INVALID_EMOJI` | 400 | 无效的 emoji |

### 匹配相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `NOT_IN_QUEUE` | 404 | 不在队列中 |
| `QUEUE_FULL` | 429 | 队列已满 |
| `ALREADY_IN_QUEUE` | 400 | 已在队列中 |

### AI 相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_DIFFICULTY` | 400 | 难度等级无效 (必须 1-10) |
| `AI_ERROR` | 500 | AI 引擎错误 |
| `INVALID_STATUS` | 400 | 无效的状态 |
| `STATUS_ERROR` | 500 | 获取状态失败 |

### 残局相关

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `PUZZLE_NOT_FOUND` | 404 | 关卡不存在 |
| `ATTEMPT_NOT_FOUND` | 404 | 挑战不存在 |
| `NOT_COMPLETE` | 400 | 挑战尚未完成 |
| `NOT_FOUND` | 404 | 关卡或挑战不存在 |

### 通用错误

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 请求方法不允许 |
| `UNAUTHORIZED` | 401 | 未授权 |
| `FORBIDDEN` | 403 | 禁止访问 |

---

## 📝 API 使用示例

### 示例 1: 完整登录流程

```bash
# 1. 用户注册
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "SecurePass123"
  }'

# 2. 用户登录
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "SecurePass123"
  }'

# 响应示例:
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

### 示例 2: 创建多人对局

```bash
# 创建多人对局
curl -X POST http://localhost:8000/api/v1/games/games/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "multiplayer",
    "black_player_id": "def456",
    "time_control": {
      "initial_time": 600,
      "increment": 5
    }
  }'
```

### 示例 3: 提交走棋

```bash
# 提交走棋
curl -X POST http://localhost:8000/api/v1/games/games/<game_id>/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "from_pos": "h0",
    "to_pos": "h2"
  }'
```

### 示例 4: 加入匹配队列

```bash
# 加入排位匹配
curl -X POST http://localhost:8000/api/v1/matchmaking/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "ranked"
  }'

# 查询匹配状态
curl -X GET http://localhost:8000/api/v1/matchmaking/status/?game_type=ranked \
  -H "Authorization: Bearer <access_token>"
```

### 示例 5: 获取 AI 走棋建议

```bash
# 请求 AI 走棋
curl -X POST http://localhost:8000/api/v1/ai/games/<game_id>/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "difficulty": 5,
    "time_limit": 2000
  }'
```

### 示例 6: 开始残局挑战

```bash
# 创建挑战
curl -X POST http://localhost:8000/api/v1/puzzles/<puzzle_id>/attempt/ \
  -H "Authorization: Bearer <access_token>"

# 提交走法
curl -X POST http://localhost:8000/api/v1/puzzles/<puzzle_id>/attempts/<attempt_id>/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "from": "e2",
    "to": "e4",
    "piece": "P"
  }'
```

### 示例 7: 查看排行榜

```bash
# 获取天梯排行榜
curl -X GET "http://localhost:8000/api/v1/ranking/leaderboard/?page=1&page_size=20"

# 获取用户排名
curl -X GET http://localhost:8000/api/v1/ranking/user/<user_id>/
```

### 示例 8: 刷新 Token

```bash
# 刷新 Access Token
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<your_refresh_token>"
  }'
```

---

## 📊 API 端点统计

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

如有问题，请联系:
- Email: support@chinese-chess.com
- 文档版本：v1.0.0
- 最后更新：2026-03-06
