# 残局谜题 API 端点文档

**基础路径**: `/api/v1/puzzles/`  
**最后更新**: 2026-03-06

---

## 端点概览

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

## 详细端点说明

### GET /api/v1/puzzles/

**获取谜题列表**

#### 认证要求
- 需要有效的 JWT Access Token

#### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| difficulty | integer | - | 难度筛选（1-10） |
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
        "title": "千里独行",
        "difficulty": 5,
        "category": "车兵类",
        "move_limit": 10,
        "time_limit": 300,
        "completed_count": 1500,
        "description": "红方先行，巧妙运兵，千里独行"
      },
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "title": "双车错",
        "difficulty": 3,
        "category": "车类",
        "move_limit": 6,
        "time_limit": 180,
        "completed_count": 2500,
        "description": "红方先行，双车配合制胜"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 谜题 ID |
| title | string | 谜题名称 |
| difficulty | integer | 难度等级（1-10） |
| category | string | 分类（车兵类/马类/炮类等） |
| move_limit | integer | 步数限制 |
| time_limit | integer | 时间限制（秒） |
| completed_count | integer | 完成次数 |
| description | string | 谜题描述 |

#### 分页说明

| 字段 | 类型 | 说明 |
|------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total | integer | 总记录数 |
| total_pages | integer | 总页数 |

---

### GET /api/v1/puzzles/{puzzle_id}/

**获取谜题详情**

#### 认证要求
- 需要有效的 JWT Access Token

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| puzzle_id | UUID | 谜题 ID |

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "千里独行",
    "difficulty": 5,
    "category": "车兵类",
    "description": "红方先行，巧妙运兵，千里独行",
    "fen_initial": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "move_limit": 10,
    "time_limit": 300,
    "completed_count": 1500,
    "user_completed": false,
    "solution_preview": "兵五进一，将 6 进 1，兵五平四..."
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 谜题 ID |
| title | string | 谜题名称 |
| difficulty | integer | 难度等级 |
| category | string | 分类 |
| description | string | 详细描述 |
| fen_initial | string | 初始 FEN 字符串 |
| move_limit | integer | 步数限制 |
| time_limit | integer | 时间限制（秒） |
| completed_count | integer | 完成次数 |
| user_completed | boolean | 用户是否已完成 |
| solution_preview | string | 解答预览（仅提示） |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | PUZZLE_NOT_FOUND | 关卡不存在 |

---

### POST /api/v1/puzzles/{puzzle_id}/attempt/

**开始挑战**

#### 认证要求
- 需要有效的 JWT Access Token

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| puzzle_id | UUID | 谜题 ID |

#### 成功响应 (201 Created)

```json
{
  "success": true,
  "data": {
    "attempt_id": "550e8400-e29b-41d4-a716-446655440000",
    "puzzle_id": "550e8400-e29b-41d4-a716-446655440000",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "status": "in_progress",
    "current_move_index": 0,
    "move_limit": 10,
    "time_limit": 300,
    "started_at": "2026-03-06T09:00:00Z"
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| attempt_id | UUID | 挑战 ID |
| puzzle_id | UUID | 谜题 ID |
| fen_current | string | 当前 FEN 字符串 |
| status | string | 挑战状态（in_progress/success/failed） |
| current_move_index | integer | 当前步数索引 |
| move_limit | integer | 步数限制 |
| time_limit | integer | 时间限制（秒） |
| started_at | datetime | 开始时间 |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | PUZZLE_NOT_FOUND | 关卡不存在 |

---

### POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/move/

**提交走法**

#### 认证要求
- 需要有效的 JWT Access Token

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| puzzle_id | UUID | 谜题 ID |
| attempt_id | UUID | 挑战 ID |

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| from | string | 是 | 起始位置（如 "e2"） |
| to | string | 是 | 目标位置（如 "e4"） |
| piece | string | 是 | 棋子类型（如 "P"） |

#### 请求示例

```json
{
  "from": "e2",
  "to": "e4",
  "piece": "P"
}
```

#### 成功响应 - 正确走法 (200 OK)

```json
{
  "success": true,
  "data": {
    "correct": true,
    "message": "正确！",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/4P4/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "current_move_index": 1,
    "remaining_moves": 9,
    "is_complete": false
  }
}
```

#### 成功响应 - 错误走法 (200 OK)

```json
{
  "success": false,
  "data": {
    "correct": false,
    "message": "这步棋不正确，请重新思考",
    "fen_current": "...",
    "remaining_moves": 10,
    "is_complete": false
  }
}
```

#### 完成挑战响应

```json
{
  "success": true,
  "data": {
    "correct": true,
    "message": "恭喜！挑战成功！",
    "fen_current": "...",
    "current_move_index": 10,
    "remaining_moves": 0,
    "is_complete": true,
    "stars": 3,
    "points_earned": 100
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| correct | boolean | 走法是否正确 |
| message | string | 提示信息 |
| fen_current | string | 当前 FEN 字符串 |
| current_move_index | integer | 当前步数索引 |
| remaining_moves | integer | 剩余步数 |
| is_complete | boolean | 是否完成挑战 |
| stars | integer | 获得星级（1-3） |
| points_earned | integer | 获得积分 |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | NOT_FOUND | 关卡或挑战不存在 |

---

### POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/complete/

**完成挑战**

#### 认证要求
- 需要有效的 JWT Access Token

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| puzzle_id | UUID | 谜题 ID |
| attempt_id | UUID | 挑战 ID |

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 完成状态（success/failed） |
| stars | integer | 获得星级（1-3） |
| points_earned | integer | 获得积分 |
| moves_used | integer | 使用步数 |
| time_used | integer | 使用时间（秒） |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | ATTEMPT_NOT_FOUND | 挑战不存在 |
| 400 | NOT_COMPLETE | 挑战尚未完成 |

---

### GET /api/v1/puzzles/progress/

**用户进度**

#### 认证要求
- 需要有效的 JWT Access Token

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
    },
    "category_stats": {
      "车兵类": 20,
      "马类": 15,
      "炮类": 10,
      "车类": 5
    }
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total_completed | integer | 总完成数 |
| total_attempts | integer | 总尝试数 |
| completion_rate | float | 完成率（百分比） |
| total_points | integer | 总积分 |
| best_stars | integer | 总星级 |
| difficulty_stats | object | 难度统计 |
| difficulty_stats.easy | integer | 简单难度完成数 |
| difficulty_stats.medium | integer | 中等难度完成数 |
| difficulty_stats.hard | integer | 困难难度完成数 |
| category_stats | object | 分类统计 |

---

### GET /api/v1/puzzles/leaderboard/

**排行榜**

#### 认证要求
- 需要有效的 JWT Access Token

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
        "username": "puzzle_master",
        "ranking_points": 10000,
        "total_completed": 200,
        "best_stars": 180,
        "completion_rate": 95.0
      },
      {
        "rank": 2,
        "user_id": "660e8400-e29b-41d4-a716-446655440001",
        "username": "chess_genius",
        "ranking_points": 9500,
        "total_completed": 190,
        "best_stars": 170,
        "completion_rate": 90.0
      }
    ],
    "user_rank": {
      "rank": 50,
      "ranking_points": 5000,
      "total_completed": 50,
      "best_stars": 45
    }
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | integer | 排名 |
| user_id | UUID | 用户 ID |
| username | string | 用户名 |
| ranking_points | integer | 排名积分 |
| total_completed | integer | 总完成数 |
| best_stars | integer | 总星级 |
| completion_rate | float | 完成率 |

#### 用户排名

| 字段 | 类型 | 说明 |
|------|------|------|
| rank | integer | 用户排名 |
| ranking_points | integer | 用户积分 |
| total_completed | integer | 用户完成数 |
| best_stars | integer | 用户星级 |

---

## 代码示例

### cURL

#### 获取谜题列表

```bash
curl -X GET "http://localhost:8000/api/v1/puzzles/?difficulty=5&page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

#### 获取谜题详情

```bash
curl -X GET http://localhost:8000/api/v1/puzzles/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer <access_token>"
```

#### 开始挑战

```bash
curl -X POST http://localhost:8000/api/v1/puzzles/550e8400-e29b-41d4-a716-446655440000/attempt/ \
  -H "Authorization: Bearer <access_token>"
```

#### 提交走法

```bash
curl -X POST http://localhost:8000/api/v1/puzzles/550e8400-e29b-41d4-a716-446655440000/attempts/550e8400-e29b-41d4-a716-446655440000/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "from": "e2",
    "to": "e4",
    "piece": "P"
  }'
```

#### 获取用户进度

```bash
curl -X GET http://localhost:8000/api/v1/puzzles/progress/ \
  -H "Authorization: Bearer <access_token>"
```

#### 获取排行榜

```bash
curl -X GET "http://localhost:8000/api/v1/puzzles/leaderboard/?time_range=all&limit=100" \
  -H "Authorization: Bearer <access_token>"
```

---

### JavaScript

```javascript
// 获取谜题列表
async function getPuzzles(token, difficulty = null, page = 1, pageSize = 20) {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (difficulty) params.append('difficulty', difficulty);
  
  const response = await fetch(
    `http://localhost:8000/api/v1/puzzles/?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  const data = await response.json();
  return data.data;
}

// 开始挑战
async function startPuzzleAttempt(token, puzzleId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/puzzles/${puzzleId}/attempt/`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  const data = await response.json();
  return data.data;
}

// 提交走法
async function submitPuzzleMove(token, puzzleId, attemptId, move) {
  const response = await fetch(
    `http://localhost:8000/api/v1/puzzles/${puzzleId}/attempts/${attemptId}/move/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(move)
    }
  );
  const data = await response.json();
  return data.data;
}

// 获取用户进度
async function getPuzzleProgress(token) {
  const response = await fetch(
    'http://localhost:8000/api/v1/puzzles/progress/',
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  const data = await response.json();
  return data.data;
}
```

---

### Python

```python
import requests

BASE_URL = 'http://localhost:8000'

def get_puzzles(token, difficulty=None, page=1, page_size=20):
    """获取谜题列表"""
    params = {'page': page, 'page_size': page_size}
    if difficulty:
        params['difficulty'] = difficulty
    
    response = requests.get(
        f'{BASE_URL}/api/v1/puzzles/',
        params=params,
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']

def start_puzzle_attempt(token, puzzle_id):
    """开始挑战"""
    response = requests.post(
        f'{BASE_URL}/api/v1/puzzles/{puzzle_id}/attempt/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']

def submit_puzzle_move(token, puzzle_id, attempt_id, move):
    """提交走法"""
    response = requests.post(
        f'{BASE_URL}/api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/move/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json=move
    )
    return response.json()['data']

def get_puzzle_progress(token):
    """获取用户进度"""
    response = requests.get(
        f'{BASE_URL}/api/v1/puzzles/progress/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']

def get_puzzle_leaderboard(token, time_range='all', limit=100):
    """获取排行榜"""
    response = requests.get(
        f'{BASE_URL}/api/v1/puzzles/leaderboard/',
        params={'time_range': time_range, 'limit': limit},
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']
```

---

## 谜题分类

### 按难度分类

| 等级 | 名称 | 适合人群 |
|------|------|---------|
| 1-2 | 简单 | 新手入门 |
| 3-4 | 中等 | 有一定基础 |
| 5-6 | 困难 | 熟练玩家 |
| 7-8 | 专家 | 高水平玩家 |
| 9-10 | 大师 | 顶级高手 |

### 按棋子分类

| 分类 | 说明 |
|------|------|
| 车兵类 | 车和兵的配合战术 |
| 马类 | 马的战术运用 |
| 炮类 | 炮的战术运用 |
| 车类 | 车的单独战术 |
| 综合类 | 多种棋子配合 |

---

## 评分规则

### 星级评定

| 星级 | 条件 |
|------|------|
| ⭐⭐⭐ (3 星) | 在规定步数内完成 |
| ⭐⭐ (2 星) | 超出规定步数 1-3 步 |
| ⭐ (1 星) | 超出规定步数 4 步以上 |

### 积分计算

```
基础积分 = 难度等级 × 10
时间奖励 = (时间限制 - 使用时间) / 10
步数奖励 = (步数限制 - 使用步数) × 2
总积分 = 基础积分 + 时间奖励 + 步数奖励
```

---

## 相关文档

- [每日挑战 API](./daily_challenge.md) - 每日挑战相关 API
- [错误码说明](../errors.md) - 完整错误码列表

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
