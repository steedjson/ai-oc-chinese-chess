# AI 引擎 API 文档

## 基础信息

- **基础路径**: `/api/v1/ai/`
- **认证方式**: JWT Token (Authorization: Bearer <token>)

---

## 端点列表

### 1. AI 对局管理

#### 1.1 获取 AI 对局列表

- **URL**: `/api/v1/ai/games/`
- **方法**: `GET`
- **认证**: 需要
- **描述**: 获取当前用户的 AI 对局列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "player": "user_id",
      "ai_level": 5,
      "ai_side": "black",
      "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
      "fen_current": "...",
      "status": "playing",
      "winner": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 1.2 创建 AI 对局

- **URL**: `/api/v1/ai/games/`
- **方法**: `POST`
- **认证**: 需要
- **描述**: 创建新的 AI 对局

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ai_level | integer | 是 | AI 难度等级 (1-10) |
| ai_side | string | 否 | AI 执棋方 (red/black)，默认 black |
| fen_start | string | 否 | 初始 FEN，默认标准开局 |

**请求示例**:
```json
{
  "ai_level": 5,
  "ai_side": "black"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "ai_level": 5,
    "ai_side": "black",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "AI 对局创建成功"
}
```

#### 1.3 获取 AI 对局详情

- **URL**: `/api/v1/ai/games/{game_id}/`
- **方法**: `GET`
- **认证**: 需要
- **描述**: 获取指定 AI 对局的详细信息

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "player": "user_id",
    "ai_level": 5,
    "ai_side": "black",
    "fen_start": "...",
    "fen_current": "...",
    "status": "playing",
    "winner": null,
    "move_count": 10,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

#### 1.4 更新 AI 对局状态

- **URL**: `/api/v1/ai/games/{game_id}/`
- **方法**: `PUT`
- **认证**: 需要
- **描述**: 更新 AI 对局状态

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 对局状态 (pending/playing/finished/aborted) |
| winner | string | 否 | 获胜方 (red/black/draw) |

#### 1.5 取消 AI 对局

- **URL**: `/api/v1/ai/games/{game_id}/`
- **方法**: `DELETE`
- **认证**: 需要
- **描述**: 取消进行中的 AI 对局

**响应示例**:
```json
{
  "success": true,
  "message": "对局已取消"
}
```

---

### 2. AI 走棋

#### 2.1 请求 AI 走棋

- **URL**: `/api/v1/ai/games/{game_id}/move/`
- **方法**: `POST`
- **认证**: 需要
- **描述**: 请求 AI 计算并返回最佳走棋

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | 对局 ID |

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | 当前局面 FEN 字符串 |
| difficulty | integer | 否 | 难度等级 (1-10)，默认 5 |
| time_limit | integer | 否 | 思考时间限制（毫秒），默认 2000 |

**请求示例**:
```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "time_limit": 2000
}
```

**响应示例**:
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

---

### 3. AI 提示

#### 3.1 获取走棋提示

- **URL**: `/api/v1/ai/games/{game_id}/hint/`
- **方法**: `POST`
- **认证**: 需要
- **描述**: 获取 AI 推荐的候选走法

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | 当前局面 FEN 字符串 |
| difficulty | integer | 否 | 难度等级 (1-10)，默认 5 |
| count | integer | 否 | 提示数量 (1-5)，默认 3 |

**请求示例**:
```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "count": 3
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "hints": [
      {
        "from_pos": "b3",
        "to_pos": "e3",
        "evaluation": 0.35,
        "piece": "C"
      },
      {
        "from_pos": "h3",
        "to_pos": "e3",
        "evaluation": 0.28,
        "piece": "C"
      },
      {
        "from_pos": "b1",
        "to_pos": "c3",
        "evaluation": 0.15,
        "piece": "N"
      }
    ]
  }
}
```

---

### 4. AI 分析

#### 4.1 分析棋局

- **URL**: `/api/v1/ai/games/{game_id}/analyze/`
- **方法**: `POST`
- **认证**: 需要
- **描述**: 请求 AI 深度分析当前局面

**请求参数**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | 当前局面 FEN 字符串 |
| depth | integer | 否 | 搜索深度 (5-25)，默认 15 |

**请求示例**:
```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "depth": 15
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "score": 0.35,
    "score_text": "红方稍优",
    "best_move": "炮二平五",
    "depth": 15,
    "thinking_time": 2500,
    "lines": [
      {
        "moves": ["炮二平五", "马8进7", "马二进三", "车9平8"],
        "evaluation": 0.35
      }
    ]
  }
}
```

---

### 5. 难度配置

#### 5.1 获取难度列表

- **URL**: `/api/v1/ai/difficulties/`
- **方法**: `GET`
- **认证**: 不需要
- **描述**: 获取所有 AI 难度等级配置

**响应示例**:
```json
{
  "success": true,
  "data": {
    "difficulties": [
      {
        "level": 1,
        "name": "新手",
        "description": "500 Elo",
        "elo_estimate": 500,
        "skill_level": 1,
        "search_depth": 5,
        "think_time_ms": 500
      },
      {
        "level": 5,
        "name": "中级",
        "description": "1500 Elo",
        "elo_estimate": 1500,
        "skill_level": 10,
        "search_depth": 12,
        "think_time_ms": 2000
      },
      {
        "level": 10,
        "name": "大师",
        "description": "2500 Elo",
        "elo_estimate": 2500,
        "skill_level": 20,
        "search_depth": 20,
        "think_time_ms": 5000
      }
    ]
  }
}
```

---

### 6. 引擎状态

#### 6.1 获取引擎池状态

- **URL**: `/api/v1/ai/engines/status/`
- **方法**: `GET`
- **认证**: 需要
- **描述**: 获取 AI 引擎池的运行状态

**响应示例**:
```json
{
  "success": true,
  "data": {
    "pool_size": 5,
    "available": 3,
    "in_use": 2
  }
}
```

---

## WebSocket 端点

### AI 对弈房间

- **URL**: `ws://{host}/ws/ai/game/{game_id}/`
- **认证**: JWT Token (通过 URL 参数或 Header 传递)
- **描述**: AI 对弈实时通信

**连接示例**:
```
ws://localhost:8000/ws/ai/game/550e8400-e29b-41d4-a716-446655440000/?token=eyJhbG...
```

**消息类型**:

#### 客户端 → 服务器

| 消息类型 | 描述 |  payload |
|---------|------|----------|
| request_move | 请求 AI 走棋 | `{ "fen": "...", "difficulty": 5 }` |
| request_hint | 请求提示 | `{ "fen": "...", "count": 3 }` |
| request_analysis | 请求分析 | `{ "fen": "...", "depth": 15 }` |
| heartbeat | 心跳 | `{ "timestamp": 1234567890 }` |

#### 服务器 → 客户端

| 消息类型 | 描述 | payload |
|---------|------|---------|
| connected | 连接确认 | `{ "game_id": "..." }` |
| ai_thinking | AI 思考中 | `{ "progress": 50, "depth": 10 }` |
| ai_move | AI 走棋完成 | `{ "from_pos": "...", "to_pos": "..." }` |
| ai_hint | 提示返回 | `{ "hints": [...] }` |
| ai_analysis | 分析结果 | `{ "score": 0.35, "best_move": "..." }` |
| ai_error | AI 错误 | `{ "code": "...", "message": "..." }` |
| heartbeat_ack | 心跳确认 | `{ "timestamp": 1234567890 }` |

---

## 数据模型

### AIGame (AI 对局)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 对局唯一标识 |
| player | UUID | 玩家 ID |
| ai_level | integer | AI 难度等级 (1-10) |
| ai_side | string | AI 执棋方 (red/black) |
| fen_start | string | 初始 FEN |
| fen_current | string | 当前 FEN |
| status | string | 对局状态 |
| winner | string | 获胜方 |
| move_count | integer | 走棋数 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### AIMove (AI 走棋结果)

| 字段 | 类型 | 说明 |
|------|------|------|
| from_pos | string | 起始位置 (如 "b3") |
| to_pos | string | 目标位置 (如 "e3") |
| piece | string | 棋子类型 (如 "C" 表示炮) |
| evaluation | float | 局面评估分数 |
| depth | integer | 搜索深度 |
| thinking_time | integer | 思考时间（毫秒） |

### AIDifficulty (AI 难度配置)

| 字段 | 类型 | 说明 |
|------|------|------|
| level | integer | 难度等级 (1-10) |
| name | string | 难度名称 |
| description | string | 描述 |
| elo_estimate | integer | 预估 Elo 分数 |
| skill_level | integer | Stockfish skill level |
| search_depth | integer | 搜索深度 |
| think_time_ms | integer | 思考时间（毫秒） |

---

## 错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 参数验证失败 |
| INVALID_DIFFICULTY | 400 | 无效的难度等级 |
| GAME_NOT_FOUND | 404 | 对局不存在 |
| PERMISSION_DENIED | 403 | 无权访问此对局 |
| INVALID_STATUS | 400 | 无效的状态转换 |
| AI_ERROR | 500 | AI 引擎错误 |
| STATUS_ERROR | 500 | 获取状态失败 |
