# 游戏对局 API

## 基础路径
```
/api/v1/
```

## 端点列表

### 1. 获取对局列表

**GET** `/games/`

获取当前用户参与的所有对局列表。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 响应
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "game_type": "single",
      "status": "playing",
      "red_player": "user-uuid-1",
      "black_player": null,
      "red_player_username": "player1",
      "black_player_username": null,
      "winner": null,
      "move_count": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### 2. 创建新对局

**POST** `/games/`

创建新的游戏对局。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |
| Content-Type | application/json |

#### 请求体
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

#### 参数说明
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 是 | 游戏类型：`single` (单机), `online` (在线对战) |
| ai_level | integer | 否 | AI 难度等级 (1-10)，默认 5 |
| time_control_base | integer | 否 | 基础时间（秒），默认 600 |
| time_control_increment | integer | 否 | 每步加秒，默认 5 |
| is_rated | boolean | 否 | 是否计分，默认 true |
| player_side | string | 否 | 玩家选择方：`red` 或 `black`，默认 `red` |

#### 响应
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "playing",
    "red_player": "user-uuid-1",
    "black_player": null,
    "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "ai_level": 5,
    "ai_side": "black",
    "move_count": 0,
    "is_rated": true,
    "started_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "moves": []
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### 3. 获取对局详情

**GET** `/games/{game_id}/`

获取指定对局的详细信息。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 响应
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "playing",
    "red_player": "user-uuid-1",
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
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "ai_level": 5,
    "ai_side": "black",
    "move_count": 0,
    "duration": 0,
    "is_rated": true,
    "started_at": "2024-01-15T10:30:00Z",
    "finished_at": null,
    "created_at": "2024-01-15T10:30:00Z",
    "moves": []
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### 4. 提交走棋

**POST** `/games/{game_id}/move/`

在指定对局中提交一步走棋。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |
| Content-Type | application/json |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 请求体
```json
{
  "from_pos": "e3",
  "to_pos": "e4"
}
```

#### 参数说明
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from_pos | string | 是 | 起始位置，如 "e3" |
| to_pos | string | 是 | 目标位置，如 "e4" |

#### 响应
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
    "created_at": "2024-01-15T10:31:00Z"
  },
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
  "turn": "b"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "INVALID_MOVE",
    "message": "无效走棋",
    "legal_moves": ["e4", "f4", "g4"]
  },
  "timestamp": "2024-01-15T10:31:00Z"
}
```

---

### 5. 获取走棋历史

**GET** `/games/{game_id}/moves/`

获取指定对局的所有走棋记录。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 响应
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
      "created_at": "2024-01-15T10:31:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### 6. 更新对局状态

**PUT** `/games/{game_id}/status/`

更新对局的状态（用于认输、和棋等）。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |
| Content-Type | application/json |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 请求体
```json
{
  "status": "red_win"
}
```

#### 参数说明
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态：`pending`, `playing`, `red_win`, `black_win`, `draw`, `aborted` |

#### 响应
返回更新后的对局详情（同获取对局详情响应）。

---

### 7. 取消对局

**DELETE** `/games/{game_id}/`

取消未开始或进行中的对局。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

#### 响应
- 成功：HTTP 204 No Content
- 失败：返回错误信息

---

### 8. 获取用户对局列表

**GET** `/users/{user_id}/games/`

获取指定用户的对局列表（仅管理员或本人可查看）。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户 ID |

#### 响应
```json
{
  "success": true,
  "games": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "game_type": "single",
      "status": "playing",
      "red_player": "user-uuid-1",
      "black_player": null,
      "red_player_username": "player1",
      "black_player_username": null,
      "winner": null,
      "move_count": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

## 数据模型

### Game 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 对局唯一标识 |
| game_type | string | 游戏类型：single, online |
| status | string | 状态：pending, playing, red_win, black_win, draw, aborted |
| red_player | UUID | 红方玩家 ID |
| black_player | UUID | 黑方玩家 ID |
| fen_start | string | 初始 FEN |
| fen_current | string | 当前 FEN |
| turn | string | 当前回合：w(红), b(黑) |
| winner | string | 获胜方：red, black, draw |
| win_reason | string | 获胜原因 |
| time_control_base | integer | 基础时间（秒） |
| time_control_increment | integer | 每步加秒 |
| red_time_remaining | integer | 红方剩余时间 |
| black_time_remaining | integer | 黑方剩余时间 |
| ai_level | integer | AI 难度等级 |
| ai_side | string | AI 执方：red, black |
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
