# 游戏对局 API 端点 (Games Endpoints)

**基础路径**: `/api/v1/`

---

## 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/` | GET | ✅ | 获取对局列表 |
| `/games/` | POST | ✅ | 创建新对局 |
| `/games/{id}/` | GET | ✅ | 获取对局详情 |
| `/games/{id}/` | PUT | ✅ | 更新对局 |
| `/games/{id}/` | DELETE | ✅ | 取消对局 |
| `/games/{id}/move/` | POST | ✅ | 提交走棋 |
| `/games/{id}/moves/` | GET | ✅ | 获取走棋历史 |
| `/games/{id}/status/` | PUT | ✅ | 更新对局状态 |
| `/users/{id}/games/` | GET | ✅ | 获取用户对局 |
| `/games/{id}/spectators/` | GET | ✅ | 获取观战者 |
| `/chat/games/{id}/send/` | POST | ✅ | 发送聊天消息 |
| `/chat/games/{id}/history/` | GET | ✅ | 获取聊天历史 |

---

## 1. 获取对局列表

### GET `/api/v1/games/`

获取当前用户参与的所有对局列表（支持分页和过滤）。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量 |
| status | string | - | 状态过滤：`pending`, `playing`, `finished` |
| game_type | string | - | 类型过滤：`single`, `online` |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "count": 25,
    "next": "http://localhost:8000/api/v1/games/?page=2",
    "previous": null,
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "game_type": "single",
        "status": "playing",
        "red_player": "550e8400-e29b-41d4-a716-446655440001",
        "black_player": null,
        "red_player_username": "player1",
        "black_player_username": null,
        "winner": null,
        "move_count": 5,
        "created_at": "2026-03-06T09:00:00Z",
        "started_at": "2026-03-06T09:01:00Z"
      }
    ]
  },
  "timestamp": "2026-03-06T09:30:00Z"
}
```

---

## 2. 创建新对局

### POST `/api/v1/games/`

创建新的游戏对局。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "game_type": "single",
  "ai_level": 5,
  "time_control_base": 600,
  "time_control_increment": 5,
  "is_rated": true,
  "player_side": "red"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| game_type | string | 是 | - | `single` (单机) 或 `online` (在线对战) |
| ai_level | integer | 否 | 5 | AI 难度等级 (1-10) |
| time_control_base | integer | 否 | 600 | 基础时间（秒） |
| time_control_increment | integer | 否 | 5 | 每步加秒 |
| is_rated | boolean | 否 | true | 是否计分 |
| player_side | string | 否 | "red" | 玩家选择方：`red` 或 `black` |

### 响应

**成功 (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "playing",
    "red_player": "550e8400-e29b-41d4-a716-446655440001",
    "black_player": null,
    "red_player_username": "player1",
    "black_player_username": null,
    "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "ai_level": 5,
    "ai_side": "black",
    "move_count": 0,
    "is_rated": true,
    "time_control_base": 600,
    "time_control_increment": 5,
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "started_at": "2026-03-06T09:00:00Z",
    "created_at": "2026-03-06T09:00:00Z",
    "moves": []
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `INVALID_DIFFICULTY` | 400 | AI 难度等级无效 |

---

## 3. 获取对局详情

### GET `/api/v1/games/{game_id}/`

获取指定对局的详细信息。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "playing",
    "red_player": "550e8400-e29b-41d4-a716-446655440001",
    "black_player": null,
    "red_player_username": "player1",
    "black_player_username": null,
    "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "winner": null,
    "win_reason": null,
    "time_control_base": 600,
    "time_control_increment": 5,
    "red_time_remaining": 595,
    "black_time_remaining": 600,
    "ai_level": 5,
    "ai_side": "black",
    "move_count": 1,
    "duration": 30,
    "is_rated": true,
    "started_at": "2026-03-06T09:00:00Z",
    "finished_at": null,
    "created_at": "2026-03-06T09:00:00Z",
    "moves": [
      {
        "id": 1,
        "move_number": 1,
        "piece": "P",
        "from_pos": "e3",
        "to_pos": "e4",
        "captured": null,
        "is_check": false,
        "is_capture": false,
        "notation": "兵五进一",
        "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
        "time_remaining": 595,
        "created_at": "2026-03-06T09:01:00Z"
      }
    ]
  },
  "timestamp": "2026-03-06T09:01:30Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `PERMISSION_DENIED` | 403 | 无权查看此对局 |

---

## 4. 提交走棋

### POST `/api/v1/games/{game_id}/move/`

在指定对局中提交一步走棋。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**Body**:
```json
{
  "from_pos": "e3",
  "to_pos": "e4"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from_pos | string | 是 | 起始位置（棋盘坐标，如 "e3"） |
| to_pos | string | 是 | 目标位置（棋盘坐标，如 "e4"） |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "move": {
    "id": 1,
    "move_number": 1,
    "piece": "P",
    "from_pos": "e3",
    "to_pos": "e4",
    "captured": null,
    "is_check": false,
    "is_capture": false,
    "notation": "兵五进一",
    "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "time_remaining": 595,
    "created_at": "2026-03-06T09:01:00Z"
  },
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
  "turn": "b"
}
```

**失败 (400 Bad Request)**:
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

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `GAME_NOT_PLAYING` | 400 | 游戏未进行中 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 |
| `NO_PIECE` | 400 | 起始位置没有棋子 |
| `INVALID_MOVE` | 400 | 无效走棋 |

---

## 5. 获取走棋历史

### GET `/api/v1/games/{game_id}/moves/`

获取指定对局的所有走棋记录。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "moves": [
    {
      "id": 1,
      "move_number": 1,
      "piece": "P",
      "from_pos": "e3",
      "to_pos": "e4",
      "captured": null,
      "is_check": false,
      "is_capture": false,
      "notation": "兵五进一",
      "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
      "time_remaining": 595,
      "created_at": "2026-03-06T09:01:00Z"
    },
    {
      "id": 2,
      "move_number": 2,
      "piece": "p",
      "from_pos": "e7",
      "to_pos": "e5",
      "captured": null,
      "is_check": false,
      "is_capture": false,
      "notation": "卒 5 进 1",
      "fen_after": "rnbakabnr/9/1c5c1/p1p1p2pp/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR w - - 0 2",
      "time_remaining": 590,
      "created_at": "2026-03-06T09:02:00Z"
    }
  ],
  "timestamp": "2026-03-06T09:02:30Z"
}
```

---

## 6. 更新对局状态

### PUT `/api/v1/games/{game_id}/status/`

更新对局的状态（用于认输、和棋等）。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**Body**:
```json
{
  "status": "red_win"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态 |

**有效状态值**:
- `pending`: 等待开始
- `playing`: 进行中
- `red_win`: 红方获胜
- `black_win`: 黑方获胜
- `draw`: 和棋
- `aborted`: 已取消

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "red_win",
    "red_player": "550e8400-e29b-41d4-a716-446655440001",
    "black_player": null,
    "winner": "red",
    "win_reason": "opponent_resigned",
    "finished_at": "2026-03-06T09:30:00Z",
    "duration": 1800,
    ...
  },
  "timestamp": "2026-03-06T09:30:00Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `INVALID_STATUS` | 400 | 无效的状态 |
| `PERMISSION_DENIED` | 403 | 无权修改此对局 |

---

## 7. 取消对局

### DELETE `/api/v1/games/{game_id}/`

取消未开始或进行中的对局。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

### 响应

**成功 (204 No Content)**:
```
HTTP/1.1 204 No Content
```

**失败 (400 Bad Request)**:
```json
{
  "success": false,
  "error": {
    "code": "GAME_ALREADY_FINISHED",
    "message": "无法取消已结束的游戏"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `GAME_ALREADY_FINISHED` | 400 | 游戏已结束，无法取消 |
| `PERMISSION_DENIED` | 403 | 无权取消此对局 |

---

## 8. 获取用户对局列表

### GET `/api/v1/users/{user_id}/games/`

获取指定用户的对局列表。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户 ID |

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "games": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "game_type": "single",
      "status": "playing",
      "red_player": "550e8400-e29b-41d4-a716-446655440001",
      "black_player": null,
      "red_player_username": "player1",
      "black_player_username": null,
      "winner": null,
      "move_count": 5,
      "created_at": "2026-03-06T09:00:00Z"
    }
  ],
  "timestamp": "2026-03-06T09:30:00Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `PERMISSION_DENIED` | 403 | 无权查看他人对局 |

---

## 9. 获取观战者

### GET `/api/v1/games/{game_id}/spectators/`

获取指定对局的观战者列表。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "spectators": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "username": "spectator1",
        "avatar_url": "https://cdn.chinese-chess.com/avatars/default.png",
        "joined_at": "2026-03-06T09:05:00Z"
      }
    ],
    "count": 1
  },
  "timestamp": "2026-03-06T09:10:00Z"
}
```

---

## 10. 发送聊天消息

### POST `/api/v1/chat/games/{game_id}/send/`

在对局聊天室中发送消息。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**Body**:
```json
{
  "content": "好棋！"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 消息内容（最多 500 字符） |

### 响应

**成功 (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "sender": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "username": "player1",
      "avatar_url": "https://cdn.chinese-chess.com/avatars/default.png"
    },
    "content": "好棋！",
    "created_at": "2026-03-06T09:05:00Z"
  },
  "timestamp": "2026-03-06T09:05:00Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `MESSAGE_TOO_LONG` | 400 | 消息内容过长 |

---

## 11. 获取聊天历史

### GET `/api/v1/chat/games/{game_id}/history/`

获取对局聊天历史。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 50 | 返回消息数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
      {
        "id": 1,
        "sender": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "username": "player1",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/default.png"
        },
        "content": "你好！",
        "created_at": "2026-03-06T09:01:00Z"
      },
      {
        "id": 2,
        "sender": {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "username": "player2",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/default.png"
        },
        "content": "好棋！",
        "created_at": "2026-03-06T09:05:00Z"
      }
    ]
  },
  "timestamp": "2026-03-06T09:10:00Z"
}
```

---

## 数据模型

### Game 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 对局唯一标识 |
| game_type | string | 游戏类型：`single`, `online` |
| status | string | 状态：`pending`, `playing`, `red_win`, `black_win`, `draw`, `aborted` |
| red_player | UUID | 红方玩家 ID |
| black_player | UUID | 黑方玩家 ID |
| fen_start | string | 初始 FEN |
| fen_current | string | 当前 FEN |
| turn | string | 当前回合：`w`(红), `b`(黑) |
| winner | string | 获胜方：`red`, `black`, `draw` |
| win_reason | string | 获胜原因 |
| time_control_base | integer | 基础时间（秒） |
| time_control_increment | integer | 每步加秒 |
| red_time_remaining | integer | 红方剩余时间 |
| black_time_remaining | integer | 黑方剩余时间 |
| ai_level | integer | AI 难度等级 |
| ai_side | string | AI 执方：`red`, `black` |
| move_count | integer | 已走步数 |
| duration | integer | 对局持续时间（秒） |
| is_rated | boolean | 是否计分 |
| started_at | datetime | 开始时间 |
| finished_at | datetime | 结束时间 |
| created_at | datetime | 创建时间 |

### GameMove 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 走棋记录 ID |
| move_number | integer | 步数序号 |
| piece | string | 棋子类型 |
| from_pos | string | 起始位置 |
| to_pos | string | 目标位置 |
| captured | string | 被吃掉的棋子 |
| is_check | boolean | 是否将军 |
| is_capture | boolean | 是否吃子 |
| notation | string | 中文记谱 |
| fen_after | string | 走棋后 FEN |
| time_remaining | integer | 剩余时间 |
| created_at | datetime | 走棋时间 |

---

## 相关文件

- **视图实现**: `games/views.py`
- **URL 路由**: `games/urls.py`
- **模型**: `games/models.py`
- **序列化器**: `games/serializers.py`

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06
