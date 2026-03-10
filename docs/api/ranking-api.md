# 中国象棋排行榜 API 文档

## 概述

排行榜系统提供每日、每周和总榜三种排行榜类型，支持缓存机制以提高查询性能。

### 特性

- ✅ **三种排行榜类型**: 每日榜、每周榜、总榜
- ✅ **缓存机制**: 自动缓存排行榜数据，1 小时有效期
- ✅ **用户排名查询**: 支持查询指定用户在各类排行榜中的排名
- ✅ **百分位显示**: 显示用户在所有玩家中的百分位排名
- ✅ **管理端点**: 支持管理员刷新和清理缓存

### 基础 URL

```
/api/ranking/
```

---

## API 端点

### 1. 每日排行榜

#### 请求

```http
GET /api/ranking/daily/
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| date | string | 否 | 今天 | 日期，格式：YYYY-MM-DD |
| limit | integer | 否 | 100 | 返回数量，最大 500 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "ranking_type": "daily",
    "date": "2026-03-06",
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "uuid-string",
          "username": "player1",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "total_score": 1500,
        "games_played": 15,
        "wins": 12,
        "losses": 2,
        "draws": 1,
        "highest_score": 150,
        "avg_score": 100.0
      }
    ],
    "user_rank": {
      "rank": 5,
      "total_score": 800,
      "games_played": 8,
      "wins": 5,
      "total_players": 100,
      "percentile": 95.0
    },
    "from_cache": true
  }
}
```

#### 错误响应

**无效日期格式**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_DATE",
    "message": "日期格式错误，请使用 YYYY-MM-DD 格式"
  }
}
```

---

### 2. 每周排行榜

#### 请求

```http
GET /api/ranking/weekly/
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| week_start | string | 否 | 本周一 | 周起始日期，格式：YYYY-MM-DD |
| limit | integer | 否 | 100 | 返回数量，最大 500 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "ranking_type": "weekly",
    "week_start": "2026-03-02",
    "week_end": "2026-03-08",
    "week_number": 10,
    "year": 2026,
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "uuid-string",
          "username": "player1",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "total_score": 5000,
        "games_played": 50,
        "wins": 40,
        "losses": 8,
        "draws": 2,
        "highest_score": 150,
        "avg_score": 100.0
      }
    ],
    "user_rank": {
      "rank": 10,
      "total_score": 2000,
      "games_played": 20,
      "wins": 15,
      "total_players": 200,
      "percentile": 95.0
    },
    "from_cache": true
  }
}
```

---

### 3. 总排行榜

#### 请求

```http
GET /api/ranking/all-time/
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 100 | 返回数量，最大 500 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "ranking_type": "all_time",
    "leaderboard": [
      {
        "rank": 1,
        "user": {
          "id": "uuid-string",
          "username": "chess_master",
          "avatar_url": "https://example.com/avatar.jpg"
        },
        "total_score": 50000,
        "games_played": 500,
        "wins": 400,
        "losses": 80,
        "draws": 20,
        "highest_score": 200,
        "avg_score": 100.0,
        "longest_win_streak": 25
      }
    ],
    "user_rank": {
      "rank": 50,
      "total_score": 10000,
      "games_played": 100,
      "wins": 70,
      "longest_win_streak": 10,
      "total_players": 1000,
      "percentile": 95.0
    },
    "from_cache": true
  }
}
```

---

### 4. 用户排名查询

#### 请求

```http
GET /api/ranking/user/<user_id>/
```

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 UUID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| type | string | 否 | all-time | 排行榜类型：daily/weekly/all-time |
| date | string | 否 | 今天 | 日期（仅 daily 类型需要） |
| week_start | string | 否 | 本周一 | 周起始日期（仅 weekly 类型需要） |

#### 响应示例（总榜）

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "username": "player1",
    "rank_type": "all_time",
    "rank": 50,
    "total_score": 10000,
    "games_played": 100,
    "wins": 70,
    "longest_win_streak": 10,
    "total_players": 1000,
    "percentile": 95.0
  }
}
```

#### 响应示例（无记录）

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "username": "newplayer",
    "rank_type": "daily",
    "date": "2026-03-06",
    "message": "该用户在今日没有游戏记录",
    "rank": null
  }
}
```

#### 错误响应

**用户不存在**

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

### 5. 用户排行榜统计

#### 请求

```http
GET /api/ranking/user/<user_id>/stats/
```

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 UUID |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "username": "player1",
    "statistics": {
      "total_games": 100,
      "total_wins": 70,
      "total_losses": 25,
      "total_draws": 5,
      "total_score": 10000,
      "highest_score": 200,
      "average_score": 100.0,
      "current_win_streak": 3,
      "longest_win_streak": 10
    },
    "current_ranks": {
      "daily": {
        "rank": 5,
        "total_score": 500,
        "games_played": 5,
        "wins": 4,
        "total_players": 100,
        "percentile": 95.0
      },
      "weekly": {
        "rank": 20,
        "total_score": 2000,
        "games_played": 20,
        "wins": 15,
        "total_players": 200,
        "percentile": 90.0
      },
      "all_time": {
        "rank": 50,
        "total_score": 10000,
        "games_played": 100,
        "wins": 70,
        "longest_win_streak": 10,
        "total_players": 1000,
        "percentile": 95.0
      }
    }
  }
}
```

---

### 6. 我的排行榜

#### 请求

```http
GET /api/ranking/my/
```

**需要认证**

#### 响应示例

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "username": "current_user",
    "statistics": {
      "total_games": 100,
      "total_wins": 70,
      "total_losses": 25,
      "total_draws": 5,
      "total_score": 10000,
      "highest_score": 200,
      "average_score": 100.0,
      "current_win_streak": 3,
      "longest_win_streak": 10
    },
    "ranks": {
      "daily": {
        "rank": 5,
        "total_score": 500,
        "games_played": 5,
        "wins": 4,
        "total_players": 100,
        "percentile": 95.0
      },
      "weekly": {
        "rank": 20,
        "total_score": 2000,
        "games_played": 20,
        "wins": 15,
        "total_players": 200,
        "percentile": 90.0
      },
      "all_time": {
        "rank": 50,
        "total_score": 10000,
        "games_played": 100,
        "wins": 70,
        "longest_win_streak": 10,
        "total_players": 1000,
        "percentile": 95.0
      }
    }
  }
}
```

#### 错误响应

**未认证**

```http
HTTP 401 Unauthorized
```

---

## 管理端点

### 7. 刷新排行榜缓存

#### 请求

```http
POST /api/ranking/admin/refresh-cache/
```

**需要管理员权限**

#### 请求体

```json
{
  "type": "all"
}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| type | string | 否 | all | 缓存类型：daily/weekly/all-time/all |

#### 响应示例

```json
{
  "success": true,
  "message": "排行榜缓存已刷新"
}
```

---

### 8. 清理过期缓存

#### 请求

```http
POST /api/ranking/admin/cleanup-cache/
```

**需要管理员权限**

#### 响应示例

```json
{
  "success": true,
  "message": "过期缓存已清理"
}
```

---

## 数据模型

### 排行榜条目结构

```typescript
interface LeaderboardEntry {
  rank: number;              // 排名
  user: {
    id: string;              // 用户 UUID
    username: string;        // 用户名
    avatar_url?: string;     // 头像 URL
  };
  total_score: number;       // 总得分
  games_played: number;      // 游戏场次
  wins: number;              // 胜场
  losses: number;            // 负场
  draws: number;             // 和棋
  highest_score: number;     // 最高单局得分
  avg_score: number;         // 平均得分
  longest_win_streak?: number; // 最长连胜（仅总榜）
}
```

### 用户排名结构

```typescript
interface UserRank {
  rank: number;              // 排名
  total_score: number;       // 总得分
  games_played: number;      // 游戏场次
  wins: number;              // 胜场
  total_players: number;     // 总玩家数
  percentile: number;        // 百分位
  longest_win_streak?: number; // 最长连胜（仅总榜）
}
```

---

## 缓存机制

### 缓存策略

- **缓存有效期**: 1 小时
- **自动刷新**: 缓存过期后自动重新计算
- **手动刷新**: 管理员可通过 API 刷新缓存
- **失效机制**: 游戏结束后自动使相关缓存失效

### 缓存状态

响应中的 `from_cache` 字段表示数据来源：

- `true`: 数据来自缓存
- `false`: 数据为实时计算

---

## 排名计算规则

### 得分规则

- **胜利**: +100 分
- **和棋**: +50 分
- **失败**: +0 分

### 排名排序

1. 总得分（降序）
2. 胜场数（降序）
3. 平均得分（降序）

### 百分位计算

```
percentile = (总玩家数 - 排名 + 1) / 总玩家数 × 100
```

---

## 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| INVALID_DATE | 400 | 日期格式错误 |
| USER_NOT_FOUND | 404 | 用户不存在 |
| REFRESH_ERROR | 500 | 刷新缓存失败 |
| CLEANUP_ERROR | 500 | 清理缓存失败 |

---

## 使用示例

### JavaScript/TypeScript

```typescript
// 获取每日排行榜
async function getDailyLeaderboard(date?: string, limit = 100) {
  const params = new URLSearchParams();
  if (date) params.append('date', date);
  params.append('limit', limit.toString());
  
  const response = await fetch(`/api/ranking/daily/?${params}`);
  const data = await response.json();
  
  if (data.success) {
    return data.data.leaderboard;
  }
  throw new Error(data.error.message);
}

// 获取用户排名
async function getUserRank(userId: string, type = 'all-time') {
  const response = await fetch(`/api/ranking/user/${userId}/?type=${type}`);
  const data = await response.json();
  
  if (data.success) {
    return data.data;
  }
  throw new Error(data.error.message);
}

// 获取我的排名
async function getMyRanking() {
  const response = await fetch('/api/ranking/my/');
  const data = await response.json();
  
  if (data.success) {
    return data.data;
  }
  throw new Error(data.error.message);
}
```

### Python

```python
import requests

# 获取每日排行榜
def get_daily_leaderboard(date=None, limit=100):
    params = {'limit': limit}
    if date:
        params['date'] = date
    
    response = requests.get('/api/ranking/daily/', params=params)
    data = response.json()
    
    if data['success']:
        return data['data']['leaderboard']
    raise Exception(data['error']['message'])

# 获取用户排名
def get_user_rank(user_id, rank_type='all-time'):
    response = requests.get(
        f'/api/ranking/user/{user_id}/',
        params={'type': rank_type}
    )
    data = response.json()
    
    if data['success']:
        return data['data']
    raise Exception(data['error']['message'])
```

---

## 注意事项

1. **限流**: 所有端点都有速率限制，请避免频繁请求
2. **缓存**: 建议使用缓存数据以减少服务器负载
3. **认证**: 部分端点需要用户认证
4. **权限**: 管理端点需要管理员权限
5. **数据更新**: 游戏结束后排行榜数据可能不会立即更新（缓存原因）

---

## 相关文件

- 模型：`src/backend/games/ranking_models.py`
- 服务：`src/backend/games/ranking_services.py`
- 视图：`src/backend/games/ranking_views.py`
