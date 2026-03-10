# 每日挑战 API 端点 (Daily Challenge Endpoints)

**基础路径**: `/api/v1/daily-challenge/`

---

## 端点概览

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
| `/leaderboard/user/{id}/` | GET | ❌ | 用户排名查询 |
| `/streak/` | GET | ✅ | 用户连续打卡 |
| `/history/` | GET | ❌ | 挑战历史 |
| `/generate-tomorrow/` | POST | ✅(staff) | 生成明日挑战 |

---

## 1. 获取今日挑战

### GET `/api/v1/daily-challenge/today/`

获取今日挑战的详细信息。

### 请求

**Headers**:
```
# 可选认证
Authorization: Bearer <access_token>
```

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "challenge": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2026-03-06",
      "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
      "target_description": "红方先行，3 步内将死黑方",
      "difficulty": "medium",
      "stars": 3,
      "max_moves": 10,
      "time_limit": 300,
      "total_attempts": 1250,
      "unique_players": 890,
      "completion_rate": 0.35
    },
    "user_attempt": {
      "has_attempted": false
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

**已尝试用户响应**:
```json
{
  "success": true,
  "data": {
    "challenge": { ... },
    "user_attempt": {
      "has_attempted": true,
      "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
      "best_score": 850,
      "best_stars": 2,
      "status": "completed"
    }
  }
}
```

---

## 2. 开始挑战

### POST `/api/v1/daily-challenge/today/attempt/`

开始今日挑战，创建挑战尝试记录。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 响应

**成功 (201 Created)**:
```json
{
  "success": true,
  "data": {
    "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
    "challenge_id": "550e8400-e29b-41d4-a716-446655440000",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "started_at": "2026-03-06T09:00:00Z",
    "time_limit": 300,
    "max_moves": 10
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

**失败 (400 Bad Request)**:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_ATTEMPTED",
    "message": "您今日已经尝试过挑战"
  }
}
```

**失败 (404 Not Found)**:
```json
{
  "success": false,
  "error": {
    "code": "NO_CHALLENGE",
    "message": "今日挑战尚未发布"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `NO_CHALLENGE` | 404 | 今日挑战尚未发布 |
| `ALREADY_ATTEMPTED` | 400 | 今日已尝试过 |

---

## 3. 提交走法

### POST `/api/v1/daily-challenge/today/move/`

在挑战中提交一步走法。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
  "from": "e3",
  "to": "e4",
  "piece": "P"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| attempt_id | string | 是 | 挑战尝试 ID |
| from | string | 是 | 起始位置 |
| to | string | 是 | 目标位置 |
| piece | string | 否 | 棋子类型（可选） |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "move_number": 1,
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/4P4/P1P3P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "remaining_moves": 9,
    "remaining_time": 295,
    "is_check": false,
    "is_capture": false
  },
  "timestamp": "2026-03-06T09:01:00Z"
}
```

**失败 (400 Bad Request)**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_MOVE",
    "message": "无效的走法"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `MISSING_ATTEMPT_ID` | 400 | 缺少尝试 ID |
| `INVALID_MOVE` | 400 | 无效走法 |
| `ATTEMPT_NOT_FOUND` | 404 | 尝试记录不存在 |
| `ATTEMPT_COMPLETED` | 400 | 挑战已完成 |

---

## 4. 完成挑战

### POST `/api/v1/daily-challenge/today/complete/`

完成挑战并提交结果。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "success"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| attempt_id | string | 是 | - | 挑战尝试 ID |
| status | string | 否 | "success" | `success` 或 `failed` |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "attempt_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "completed",
    "score": 850,
    "stars_earned": 2,
    "moves_used": 8,
    "time_used": 180,
    "completed_at": "2026-03-06T09:03:00Z",
    "rank_change": "+5"
  },
  "timestamp": "2026-03-06T09:03:00Z"
}
```

### 评分规则

| 星级 | 条件 |
|------|------|
| ⭐⭐⭐ | 使用 ≤ 最优步数 +2，时间 ≤ 60 秒 |
| ⭐⭐ | 使用 ≤ 最优步数 +5，时间 ≤ 180 秒 |
| ⭐ | 完成挑战 |

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `MISSING_ATTEMPT_ID` | 400 | 缺少尝试 ID |
| `ATTEMPT_NOT_FOUND` | 404 | 尝试记录不存在 |
| `ATTEMPT_ALREADY_COMPLETED` | 400 | 挑战已完成 |

---

## 5. 获取排行榜

### GET `/api/v1/daily-challenge/leaderboard/`

获取挑战排行榜（支持日期过滤）。

### 请求

**Headers**:
```
# 可选认证（用于获取用户排名）
Authorization: Bearer <access_token>
```

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | today | 日期 (YYYY-MM-DD) |
| limit | integer | 100 | 返回数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "challenge_date": "2026-03-06",
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "username": "chess_master",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/1.png"
        },
        "score": 1000,
        "stars": 3,
        "moves_used": 5,
        "time_used": 45,
        "completed_at": "2026-03-06T00:30:00Z"
      },
      {
        "rank": 2,
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "username": "grandmaster",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/2.png"
        },
        "score": 980,
        "stars": 3,
        "moves_used": 5,
        "time_used": 52,
        "completed_at": "2026-03-06T01:15:00Z"
      }
    ],
    "user_rank": {
      "rank": 125,
      "score": 750,
      "stars": 2,
      "percentile": 85.5
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `INVALID_DATE` | 400 | 日期格式错误 |

---

## 6. 每日排行榜

### GET `/api/v1/daily-challenge/leaderboard/daily/`

获取指定日期的排行榜。

### 请求

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | today | 日期 (YYYY-MM-DD) |
| limit | integer | 100 | 返回数量 |

### 响应

同 [获取排行榜](#5-获取排行榜)

---

## 7. 周排行榜

### GET `/api/v1/daily-challenge/leaderboard/weekly/`

获取本周排行榜。

### 请求

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| week_start | string | Monday | 周起始日期 (YYYY-MM-DD) |
| limit | integer | 100 | 返回数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "week_start": "2026-03-02",
    "week_end": "2026-03-08",
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "username": "chess_master",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/1.png"
        },
        "total_score": 6500,
        "challenges_completed": 7,
        "average_stars": 2.8,
        "best_streak": 7
      }
    ],
    "user_rank": {
      "rank": 50,
      "total_score": 4200,
      "challenges_completed": 5,
      "percentile": 75.0
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 8. 总排行榜

### GET `/api/v1/daily-challenge/leaderboard/all-time/`

获取历史总排行榜。

### 请求

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 100 | 返回数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "username": "chess_master",
          "avatar_url": "https://cdn.chinese-chess.com/avatars/1.png"
        },
        "total_score": 250000,
        "challenges_completed": 365,
        "average_stars": 2.9,
        "longest_streak": 120
      }
    ],
    "user_rank": {
      "rank": 500,
      "total_score": 50000,
      "challenges_completed": 100,
      "percentile": 90.0
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 9. 用户排名查询

### GET `/api/v1/daily-challenge/leaderboard/user/{user_id}/`

查询指定用户的排名信息。

### 请求

**Path Parameters**:
| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户 ID |

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | all-time | `daily`, `weekly`, `all-time` |
| date | string | today | 日期（仅 daily 类型） |
| week_start | string | Monday | 周起始日期（仅 weekly 类型） |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "rank_type": "daily",
    "challenge_date": "2026-03-06",
    "rank": 125,
    "score": 750,
    "stars": 2,
    "percentile": 85.5
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

**无记录 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "rank_type": "daily",
    "challenge_date": "2026-03-06",
    "message": "该用户在今日挑战中没有记录"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `INVALID_DATE` | 400 | 日期格式错误 |

---

## 10. 用户连续打卡

### GET `/api/v1/daily-challenge/streak/`

获取用户的连续打卡记录和统计信息。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "streak": {
      "current_streak": 15,
      "longest_streak": 45,
      "last_completion_date": "2026-03-05"
    },
    "statistics": {
      "total_challenges": 120,
      "completed_challenges": 95,
      "completion_rate": 0.79,
      "total_score": 75000,
      "average_stars": 2.3,
      "three_star_count": 25,
      "two_star_count": 40,
      "one_star_count": 30
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 11. 挑战历史

### GET `/api/v1/daily-challenge/history/`

获取历史挑战列表。

### 请求

**Query Parameters**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | integer | 30 | 返回数量 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "date": "2026-03-05",
        "difficulty": "medium",
        "stars": 3,
        "target_description": "红方先行，3 步内将死黑方",
        "total_attempts": 1100,
        "unique_players": 850,
        "completion_rate": 0.38
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "date": "2026-03-04",
        "difficulty": "hard",
        "stars": 3,
        "target_description": "红方先行，5 步内将死黑方",
        "total_attempts": 980,
        "unique_players": 720,
        "completion_rate": 0.25
      }
    ]
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 12. 生成明日挑战

### POST `/api/v1/daily-challenge/generate-tomorrow/`

生成明日的挑战（管理员专用）。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
```

**认证要求**: 需要管理员权限 (is_staff=true)

### 响应

**成功 (201 Created)**:
```json
{
  "success": true,
  "data": {
    "challenge_id": "550e8400-e29b-41d4-a716-446655440002",
    "date": "2026-03-07",
    "difficulty": "medium",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "target_description": "红方先行，3 步内将死黑方",
    "max_moves": 10,
    "time_limit": 300
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

**失败 (403 Forbidden)**:
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "需要管理员权限"
  }
}
```

**失败 (500 Internal Server Error)**:
```json
{
  "success": false,
  "error": {
    "code": "GENERATION_ERROR",
    "message": "无法生成挑战：无合适的谜题"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `PERMISSION_DENIED` | 403 | 需要管理员权限 |
| `GENERATION_ERROR` | 500 | 生成失败 |
| `CHALLENGE_EXISTS` | 400 | 明日挑战已存在 |

---

## 数据模型

### DailyChallenge 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 挑战唯一标识 |
| date | date | 挑战日期 |
| fen | string | 初始局面 FEN |
| target_description | string | 目标描述 |
| difficulty | string | 难度：`easy`, `medium`, `hard` |
| stars | integer | 星级 (1-3) |
| max_moves | integer | 最大步数 |
| time_limit | integer | 时间限制（秒） |
| total_attempts | integer | 总尝试次数 |
| unique_players | integer | 独立玩家数 |
| completion_rate | float | 完成率 |
| is_active | boolean | 是否激活 |
| created_at | datetime | 创建时间 |

### ChallengeAttempt 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 尝试唯一标识 |
| user | UUID | 用户 ID |
| challenge | UUID | 挑战 ID |
| status | string | 状态：`in_progress`, `completed`, `failed` |
| score | integer | 得分 |
| stars_earned | integer | 获得星级 |
| moves_used | integer | 使用步数 |
| time_used | integer | 使用时间（秒） |
| attempted_at | datetime | 尝试时间 |
| completed_at | datetime | 完成时间 |

### ChallengeStreak 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 记录唯一标识 |
| user | UUID | 用户 ID |
| current_streak | integer | 当前连续天数 |
| longest_streak | integer | 最长连续天数 |
| last_completion_date | date | 最后完成日期 |
| total_completions | integer | 总完成次数 |

---

## 相关文件

- **视图实现**: `daily_challenge/views.py`
- **URL 路由**: `daily_challenge/urls.py`
- **模型**: `daily_challenge/models.py`
- **服务层**: `daily_challenge/services.py`

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06
