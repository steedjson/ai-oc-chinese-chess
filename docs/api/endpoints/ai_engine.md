# AI 引擎 API 端点文档

**基础路径**: `/api/v1/ai/`  
**最后更新**: 2026-03-06

---

## 端点概览

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

## 详细端点说明

### GET /api/v1/ai/games/

**获取 AI 对局列表**

#### 认证要求
- 需要有效的 JWT Access Token

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
      "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
      "turn": "w",
      "created_at": "2026-03-06T09:00:00Z"
    }
  ]
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | AI 对局 ID |
| player | object | 玩家信息 |
| player.user_id | UUID | 玩家用户 ID |
| player.username | string | 玩家用户名 |
| ai_level | integer | AI 难度等级（1-10） |
| status | string | 对局状态（pending/playing/finished/aborted） |
| fen_current | string | 当前 FEN 字符串 |
| turn | string | 当前回合（w=红，b=黑） |
| created_at | datetime | 创建时间 |

---

### POST /api/v1/ai/games/

**创建 AI 对局**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ai_level | integer | 是 | AI 难度等级（1-10） |
| time_control | object | 否 | 时间控制配置 |
| time_control.initial_time | integer | 否 | 初始时间（秒），默认 600 |
| time_control.increment | integer | 否 | 每步加秒（秒），默认 5 |
| player_color | string | 否 | 玩家颜色（w=红，b=黑），默认 w |

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
    "player": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player1"
    },
    "ai_level": 5,
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "ai_side": "b",
    "red_time_remaining": 600,
    "black_time_remaining": 600,
    "move_count": 0,
    "created_at": "2026-03-06T09:00:00Z",
    "started_at": "2026-03-06T09:00:00Z"
  },
  "message": "AI 对局创建成功"
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | INVALID_DIFFICULTY | 难度等级必须在 1-10 之间 |
| 400 | VALIDATION_ERROR | 参数验证失败 |

```json
{
  "success": false,
  "error": {
    "code": "INVALID_DIFFICULTY",
    "message": "难度等级必须在 1-10 之间"
  }
}
```

---

### GET /api/v1/ai/games/{game_id}/

**获取 AI 对局详情**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能查看自己的对局

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| game_id | UUID | AI 对局 ID |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "player": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "player1"
    },
    "ai_level": 5,
    "status": "playing",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "w",
    "ai_side": "b",
    "move_count": 10,
    "red_time_remaining": 580,
    "black_time_remaining": 590,
    "winner": null,
    "created_at": "2026-03-06T09:00:00Z",
    "started_at": "2026-03-06T09:00:00Z",
    "finished_at": null
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | GAME_NOT_FOUND | 对局不存在 |
| 403 | PERMISSION_DENIED | 无权查看此对局 |

---

### PUT /api/v1/ai/games/{game_id}/

**更新 AI 对局状态**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能修改自己的对局

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 新状态 |
| winner | string | 否 | 获胜方（w/b/draw） |

**有效状态值**: `pending`, `playing`, `finished`, `aborted`  
**有效获胜方**: `w`（红）, `b`（黑）, `draw`（和棋）

#### 请求示例

```json
{
  "status": "finished",
  "winner": "w"
}
```

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "player": {...},
    "ai_level": 5,
    "status": "finished",
    "winner": "w",
    "finished_at": "2026-03-06T10:00:00Z"
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 403 | PERMISSION_DENIED | 无权修改此对局 |
| 400 | INVALID_STATUS | 无效的状态 |

---

### DELETE /api/v1/ai/games/{game_id}/

**取消 AI 对局**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能删除自己的对局

#### 成功响应 (204 No Content)

无内容返回

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 403 | PERMISSION_DENIED | 无权删除此对局 |
| 400 | INVALID_STATUS | 只能取消未开始或进行中的对局 |

---

### POST /api/v1/ai/games/{game_id}/move/

**请求 AI 走棋**

#### 认证要求
- 需要有效的 JWT Access Token

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| from_pos | string | 起始位置（如 "h0"） |
| to_pos | string | 目标位置（如 "h2"） |
| piece | string | 棋子类型（如 "cannon"） |
| evaluation | float | 局面评估（正数=红优，负数=黑优） |
| depth | integer | 搜索深度 |
| thinking_time | integer | 思考时间（毫秒） |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 500 | AI_ERROR | AI 走棋失败 |

---

### POST /api/v1/ai/games/{game_id}/hint/

**请求 AI 提示**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | FEN 字符串 |
| difficulty | integer | 否 | 难度等级（1-10，默认 5） |
| count | integer | 否 | 返回提示数量（默认 3） |

#### 请求示例

```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "count": 3
}
```

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
      },
      {
        "from_pos": "e3",
        "to_pos": "e4",
        "evaluation": 0.3,
        "depth": 8
      }
    ]
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 500 | AI_ERROR | 获取提示失败 |

---

### POST /api/v1/ai/games/{game_id}/analyze/

**请求 AI 分析**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fen | string | 是 | FEN 字符串 |
| depth | integer | 否 | 分析深度（默认 15） |

#### 请求示例

```json
{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "depth": 15
}
```

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
      },
      {
        "move": "e3e4",
        "reason": "挺兵控制中心"
      }
    ]
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| evaluation | float | 局面评估 |
| advantage | string | 优势方（red/black/balanced） |
| material_balance | integer | 子力平衡（正数=红优） |
| position_features | object | 局面特征 |
| position_features.red_king_safety | string | 红方王安全（good/moderate/poor） |
| position_features.black_king_safety | string | 黑方王安全 |
| position_features.center_control | string | 中心控制（balanced/red/black） |
| suggestions | array | 建议走法列表 |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 500 | AI_ERROR | 分析失败 |

---

### GET /api/v1/ai/difficulties/

**获取难度列表**

#### 认证要求
- 无需认证（公开端点）

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
        "level": 2,
        "name": "新手",
        "description": "1000 Elo",
        "elo_estimate": 1000,
        "skill_level": 2,
        "search_depth": 3,
        "think_time_ms": 1000
      },
      {
        "level": 3,
        "name": "初级",
        "description": "1200 Elo",
        "elo_estimate": 1200,
        "skill_level": 3,
        "search_depth": 5,
        "think_time_ms": 1500
      },
      {
        "level": 4,
        "name": "中级",
        "description": "1400 Elo",
        "elo_estimate": 1400,
        "skill_level": 4,
        "search_depth": 7,
        "think_time_ms": 1800
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
        "level": 6,
        "name": "中高级",
        "description": "1700 Elo",
        "elo_estimate": 1700,
        "skill_level": 6,
        "search_depth": 10,
        "think_time_ms": 2500
      },
      {
        "level": 7,
        "name": "高级",
        "description": "1900 Elo",
        "elo_estimate": 1900,
        "skill_level": 7,
        "search_depth": 12,
        "think_time_ms": 3000
      },
      {
        "level": 8,
        "name": "专家",
        "description": "2200 Elo",
        "elo_estimate": 2200,
        "skill_level": 8,
        "search_depth": 13,
        "think_time_ms": 3500
      },
      {
        "level": 9,
        "name": "大师",
        "description": "2500 Elo",
        "elo_estimate": 2500,
        "skill_level": 9,
        "search_depth": 14,
        "think_time_ms": 4500
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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| level | integer | 难度等级（1-10） |
| name | string | 难度名称 |
| description | string | 难度描述 |
| elo_estimate | integer | 预估 ELO 等级分 |
| skill_level | integer | Stockfish 技能等级（0-20） |
| search_depth | integer | 搜索深度 |
| think_time_ms | integer | 思考时间（毫秒） |

---

### GET /api/v1/ai/engines/status/

**获取引擎状态**

#### 认证要求
- 需要有效的 JWT Access Token

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| pool_size | integer | 引擎池总大小 |
| available | integer | 可用引擎数量 |
| in_use | integer | 正在使用的引擎数量 |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 500 | STATUS_ERROR | 获取状态失败 |

---

## 代码示例

### cURL

#### 创建 AI 对局

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

#### 请求 AI 走棋

```bash
curl -X POST http://localhost:8000/api/v1/ai/games/550e8400-e29b-41d4-a716-446655440000/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "difficulty": 5,
    "time_limit": 2000
  }'
```

#### 获取难度列表

```bash
curl -X GET http://localhost:8000/api/v1/ai/difficulties/
```

---

### JavaScript

```javascript
// 创建 AI 对局
async function createAIGame(token, aiLevel = 5, playerColor = 'w') {
  const response = await fetch('http://localhost:8000/api/v1/ai/games/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ai_level: aiLevel,
      time_control: {
        initial_time: 600,
        increment: 5
      },
      player_color: playerColor
    })
  });
  const data = await response.json();
  return data.data;
}

// 请求 AI 走棋
async function requestAIMove(token, gameId, fen, difficulty = 5) {
  const response = await fetch(
    `http://localhost:8000/api/v1/ai/games/${gameId}/move/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fen: fen,
        difficulty: difficulty,
        time_limit: 2000
      })
    }
  );
  const data = await response.json();
  return data.data;
}

// 获取难度列表
async function getDifficulties() {
  const response = await fetch('http://localhost:8000/api/v1/ai/difficulties/');
  const data = await response.json();
  return data.data.difficulties;
}
```

---

### Python

```python
import requests

BASE_URL = 'http://localhost:8000'

def create_ai_game(token, ai_level=5, player_color='w'):
    """创建 AI 对局"""
    response = requests.post(
        f'{BASE_URL}/api/v1/ai/games/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'ai_level': ai_level,
            'time_control': {
                'initial_time': 600,
                'increment': 5
            },
            'player_color': player_color
        }
    )
    return response.json()['data']

def request_ai_move(token, game_id, fen, difficulty=5, time_limit=2000):
    """请求 AI 走棋"""
    response = requests.post(
        f'{BASE_URL}/api/v1/ai/games/{game_id}/move/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={
            'fen': fen,
            'difficulty': difficulty,
            'time_limit': time_limit
        }
    )
    return response.json()['data']

def get_difficulties():
    """获取难度列表"""
    response = requests.get(f'{BASE_URL}/api/v1/ai/difficulties/')
    return response.json()['data']['difficulties']

def get_engine_status(token):
    """获取引擎状态"""
    response = requests.get(
        f'{BASE_URL}/api/v1/ai/engines/status/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']
```

---

## 难度等级说明

| 等级 | 名称 | ELO 预估 | 适合人群 |
|------|------|---------|---------|
| 1 | 入门 | 800 | 完全新手，刚学规则 |
| 2 | 新手 | 1000 | 了解基本规则 |
| 3 | 初级 | 1200 | 掌握基本战术 |
| 4 | 中级 | 1400 | 有一定实战经验 |
| 5 | 中级 | 1500 | 普通玩家水平 |
| 6 | 中高级 | 1700 | 熟练玩家 |
| 7 | 高级 | 1900 | 高水平玩家 |
| 8 | 专家 | 2200 | 接近大师水平 |
| 9 | 大师 | 2500 | 大师级水平 |
| 10 | 大师 | 2800 | 顶级大师水平 |

---

## 相关文档

- [游戏 API](./games.md) - 游戏对局相关 API
- [错误码说明](../errors.md) - 完整错误码列表
- [WebSocket 文档](../websocket.md) - 实时对战协议

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
