# 匹配系统 API 端点文档

**基础路径**: `/api/v1/matchmaking/` 和 `/api/v1/ranking/`  
**最后更新**: 2026-03-06

---

## 端点概览

### 匹配队列

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/start/` | POST | ✅ | 开始匹配 |
| `/cancel/` | POST | ✅ | 取消匹配 |
| `/status/` | GET | ✅ | 获取匹配状态 |

### 排行榜

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/ranking/leaderboard/` | GET | ❌ | 天梯排行榜 |
| `/ranking/user/{user_id}/` | GET | ❌ | 用户排名 |
| `/ranking/user/` | GET | ✅ | 当前用户排名 |

---

## 详细端点说明

### POST /api/v1/matchmaking/start/

**开始匹配**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 否 | 游戏类型（ranked/casual，默认 ranked） |

**有效游戏类型**:
- `ranked` - 排位赛（影响天梯分）
- `casual` - 休闲赛（不影响天梯分）

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| message | string | 提示信息 |
| game_type | string | 匹配类型 |
| queue_position | integer | 队列中的位置 |
| estimated_wait_time | integer | 预计等待时间（秒） |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | ALREADY_IN_QUEUE | 已在队列中 |
| 429 | QUEUE_FULL | 队列已满 |

```json
{
  "success": false,
  "error": {
    "code": "ALREADY_IN_QUEUE",
    "message": "您已在匹配队列中"
  }
}
```

---

### POST /api/v1/matchmaking/cancel/

**取消匹配**

#### 认证要求
- 需要有效的 JWT Access Token

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

#### 认证要求
- 需要有效的 JWT Access Token

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| game_type | string | ranked | 游戏类型（ranked/casual） |

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| in_queue | boolean | 是否在队列中 |
| queue_position | integer | 队列位置（如果在队列中） |
| estimated_wait_time | integer | 预计等待时间（秒） |
| total_in_queue | integer | 队列总人数 |

#### 不在队列中的响应

```json
{
  "success": true,
  "in_queue": false,
  "queue_position": null,
  "estimated_wait_time": null,
  "total_in_queue": 50
}
```

---

### GET /api/v1/ranking/leaderboard/

**天梯排行榜**

#### 认证要求
- 无需认证（公开端点）

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
      "username": "grandmaster1",
      "avatar": "https://example.com/avatar1.png",
      "rating": 2200,
      "games_played": 500,
      "wins": 350,
      "losses": 120,
      "draws": 30,
      "win_rate": 70.0
    },
    {
      "rank": 2,
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "chess_master",
      "avatar": "https://example.com/avatar2.png",
      "rating": 2150,
      "games_played": 450,
      "wins": 300,
      "losses": 130,
      "draws": 20,
      "win_rate": 66.7
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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | integer | 排名 |
| user_id | UUID | 用户 ID |
| username | string | 用户名 |
| avatar | string | 头像 URL |
| rating | integer | 天梯分（ELO） |
| games_played | integer | 总对局数 |
| wins | integer | 胜局数 |
| losses | integer | 负局数 |
| draws | integer | 和局数 |
| win_rate | float | 胜率（百分比） |

#### 分页说明

| 字段 | 类型 | 说明 |
|------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total | integer | 总记录数 |
| total_pages | integer | 总页数 |

---

### GET /api/v1/ranking/user/{user_id}/

**用户排名**

#### 认证要求
- 无需认证（公开端点）

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
    "rating": 1500,
    "rank": 125,
    "games_played": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 60.0,
    "highest_rating": 1550,
    "rating_change_24h": 15,
    "rating_change_7d": 50,
    "rating_change_30d": 100
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户 ID |
| username | string | 用户名 |
| rating | integer | 当前天梯分 |
| rank | integer | 当前排名 |
| games_played | integer | 总对局数 |
| wins | integer | 胜局数 |
| losses | integer | 负局数 |
| draws | integer | 和局数 |
| win_rate | float | 胜率（百分比） |
| highest_rating | integer | 最高天梯分 |
| rating_change_24h | integer | 24 小时内天梯分变化 |
| rating_change_7d | integer | 7 天内天梯分变化 |
| rating_change_30d | integer | 30 天内天梯分变化 |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | USER_NOT_FOUND | 用户不存在 |

---

### GET /api/v1/ranking/user/

**当前用户排名**

#### 认证要求
- 需要有效的 JWT Access Token

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "rating": 1500,
    "rank": 125,
    "games_played": 100,
    "wins": 60,
    "losses": 35,
    "draws": 5,
    "win_rate": 60.0,
    "highest_rating": 1550,
    "rating_change_24h": 15,
    "rating_change_7d": 50,
    "rating_change_30d": 100
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 401 | UNAUTHORIZED | 未认证 |

---

## 代码示例

### cURL

#### 开始匹配

```bash
curl -X POST http://localhost:8000/api/v1/matchmaking/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "ranked"
  }'
```

#### 取消匹配

```bash
curl -X POST http://localhost:8000/api/v1/matchmaking/cancel/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "ranked"
  }'
```

#### 获取匹配状态

```bash
curl -X GET "http://localhost:8000/api/v1/matchmaking/status/?game_type=ranked" \
  -H "Authorization: Bearer <access_token>"
```

#### 获取排行榜

```bash
curl -X GET "http://localhost:8000/api/v1/ranking/leaderboard/?page=1&page_size=20"
```

#### 获取用户排名

```bash
curl -X GET http://localhost:8000/api/v1/ranking/user/550e8400-e29b-41d4-a716-446655440000/
```

#### 获取当前用户排名

```bash
curl -X GET http://localhost:8000/api/v1/ranking/user/ \
  -H "Authorization: Bearer <access_token>"
```

---

### JavaScript

```javascript
// 开始匹配
async function startMatchmaking(token, gameType = 'ranked') {
  const response = await fetch('http://localhost:8000/api/v1/matchmaking/start/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ game_type: gameType })
  });
  const data = await response.json();
  return data;
}

// 取消匹配
async function cancelMatchmaking(token, gameType = 'ranked') {
  const response = await fetch('http://localhost:8000/api/v1/matchmaking/cancel/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ game_type: gameType })
  });
  const data = await response.json();
  return data;
}

// 获取匹配状态
async function getMatchStatus(token, gameType = 'ranked') {
  const response = await fetch(
    `http://localhost:8000/api/v1/matchmaking/status/?game_type=${gameType}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  const data = await response.json();
  return data;
}

// 获取排行榜
async function getLeaderboard(page = 1, pageSize = 20) {
  const response = await fetch(
    `http://localhost:8000/api/v1/ranking/leaderboard/?page=${page}&page_size=${pageSize}`
  );
  const data = await response.json();
  return data;
}

// 获取用户排名
async function getUserRank(token, userId = null) {
  const url = userId 
    ? `http://localhost:8000/api/v1/ranking/user/${userId}/`
    : 'http://localhost:8000/api/v1/ranking/user/';
  
  const response = await fetch(url, {
    headers: userId ? {} : { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data;
}
```

---

### Python

```python
import requests

BASE_URL = 'http://localhost:8000'

def start_matchmaking(token, game_type='ranked'):
    """开始匹配"""
    response = requests.post(
        f'{BASE_URL}/api/v1/matchmaking/start/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={'game_type': game_type}
    )
    return response.json()

def cancel_matchmaking(token, game_type='ranked'):
    """取消匹配"""
    response = requests.post(
        f'{BASE_URL}/api/v1/matchmaking/cancel/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json={'game_type': game_type}
    )
    return response.json()

def get_match_status(token, game_type='ranked'):
    """获取匹配状态"""
    response = requests.get(
        f'{BASE_URL}/api/v1/matchmaking/status/',
        params={'game_type': game_type},
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()

def get_leaderboard(page=1, page_size=20):
    """获取排行榜"""
    response = requests.get(
        f'{BASE_URL}/api/v1/ranking/leaderboard/',
        params={'page': page, 'page_size': page_size}
    )
    return response.json()

def get_user_rank(token, user_id=None):
    """获取用户排名"""
    if user_id:
        url = f'{BASE_URL}/api/v1/ranking/user/{user_id}/'
        headers = {}
    else:
        url = f'{BASE_URL}/api/v1/ranking/user/'
        headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers)
    return response.json()
```

---

## 匹配机制说明

### ELO 评分系统

本游戏使用 ELO 评分系统进行天梯排名：

- **初始分数**: 1500 分
- **分数范围**: 理论上无上限，最低 0 分
- **匹配范围**: 优先匹配分数相近的玩家（±100 分）

### 积分计算

胜利/失败的积分变化取决于双方分数差：

| 情况 | 胜方获得 | 负方失去 |
|------|---------|---------|
| 胜方分数低 | +20~25 | -20~25 |
| 双方分数相近 | +15~20 | -15~20 |
| 胜方分数高 | +5~10 | -5~10 |

### 匹配队列

1. **加入队列**: 调用 `POST /matchmaking/start/`
2. **匹配中**: 定期调用 `GET /matchmaking/status/` 查询状态
3. **匹配成功**: WebSocket 收到匹配成功通知
4. **取消匹配**: 调用 `POST /matchmaking/cancel/`

### 队列搜索范围

系统会动态扩大搜索范围以加快匹配：

- **初始范围**: ±100 分
- **每 30 秒**: 扩大 ±50 分
- **最大范围**: ±300 分

---

## 排行榜说明

### 排名规则

1. **主要排序**: 天梯分（rating）降序
2. **次要排序**: 胜率（win_rate）降序
3. **第三排序**: 总对局数（games_played）降序

### 分页限制

- **默认每页**: 20 条
- **最大每页**: 100 条
- **总记录数**: 无限制

---

## 相关文档

- [游戏 API](./games.md) - 游戏对局相关 API
- [WebSocket 文档](../websocket.md) - 实时对战协议
- [错误码说明](../errors.md) - 完整错误码列表

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
