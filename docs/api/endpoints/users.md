# 用户 API 端点文档

**基础路径**: `/api/v1/users/`  
**最后更新**: 2026-03-06

---

## 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/profile/` | GET | ✅ | 获取当前用户 Profile |
| `/profile/` | PUT | ✅ | 更新当前用户 Profile（全量） |
| `/profile/` | PATCH | ✅ | 更新当前用户 Profile（部分） |
| `/me/stats/` | GET | ✅ | 获取当前用户统计 |
| `/{user_id}/` | GET | ✅ | 获取用户详情 |
| `/{user_id}/` | PUT | ✅ | 更新用户信息（全量） |
| `/{user_id}/` | PATCH | ✅ | 更新用户信息（部分） |
| `/{user_id}/password/` | PUT | ✅ | 修改用户密码 |
| `/{user_id}/stats/` | GET | ✅ | 获取用户统计 |
| `/{user_id}/games/` | GET | ✅ | 获取用户对局历史 |

---

## 详细端点说明

### GET /api/v1/users/profile/

**获取当前用户 Profile**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求头
```http
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
    "games_played": 100,
    "games_won": 60,
    "games_lost": 35,
    "games_drawn": 5,
    "win_rate": 0.6,
    "created_at": "2026-01-15T08:30:00Z"
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户唯一标识 |
| username | string | 用户名 |
| email | string | 邮箱地址 |
| avatar | string | 头像 URL |
| elo_rating | integer | ELO 等级分 |
| games_played | integer | 总对局数 |
| games_won | integer | 胜局数 |
| games_lost | integer | 负局数 |
| games_drawn | integer | 和局数 |
| win_rate | float | 胜率（0-1） |
| created_at | datetime | 注册时间 |

---

### PUT /api/v1/users/profile/

**更新当前用户信息（全量更新）**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能更新自己的信息

#### 请求头
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-20 字符） |
| email | string | 是 | 邮箱地址 |
| avatar | string | 否 | 头像 URL |

#### 请求示例

```json
{
  "username": "new_chess_player",
  "email": "new@example.com",
  "avatar": "https://example.com/new_avatar.png"
}
```

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

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 400 | USERNAME_EXISTS | 用户名已存在 |
| 400 | EMAIL_EXISTS | 邮箱已存在 |

---

### PATCH /api/v1/users/profile/

**更新当前用户信息（部分更新）**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求示例

```json
{
  "avatar": "https://example.com/new_avatar.png"
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
    "avatar": "https://example.com/new_avatar.png"
  },
  "message": "用户信息更新成功"
}
```

---

### GET /api/v1/users/me/stats/

**获取当前用户统计**

#### 认证要求
- 需要有效的 JWT Access Token

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total_games | integer | 总对局数 |
| wins | integer | 胜局数 |
| losses | integer | 负局数 |
| draws | integer | 和局数 |
| win_rate | float | 胜率（百分比） |
| current_rating | integer | 当前等级分 |
| highest_rating | integer | 最高等级分 |

---

### GET /api/v1/users/{user_id}/

**获取用户详情**

#### 认证要求
- 需要有效的 JWT Access Token

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

### PUT /api/v1/users/{user_id}/

**更新用户信息（全量更新）**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能更新自己的信息（管理员除外）

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱 |
| avatar | string | 否 | 头像 URL |

#### 错误响应

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 404 | USER_NOT_FOUND | 用户不存在 |
| 403 | PERMISSION_DENIED | 无权修改其他用户信息 |
| 400 | VALIDATION_ERROR | 参数验证失败 |

---

### PATCH /api/v1/users/{user_id}/

**更新用户信息（部分更新）**

#### 认证要求
- 需要有效的 JWT Access Token

#### 请求示例

```json
{
  "avatar": "https://example.com/new_avatar.png"
}
```

---

### PUT /api/v1/users/{user_id}/password/

**修改用户密码**

#### 认证要求
- 需要有效的 JWT Access Token
- 只能修改自己的密码（管理员除外）

#### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码（8-20 字符） |

#### 请求示例

```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

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
| 400 | PASSWORD_CHANGE_FAILED | 密码修改失败 |

---

### GET /api/v1/users/{user_id}/stats/

**获取用户统计**

#### 认证要求
- 需要有效的 JWT Access Token

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

#### 认证要求
- 需要有效的 JWT Access Token

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | UUID | 用户 ID |

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

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 对局 ID |
| opponent | object | 对手信息 |
| opponent.id | UUID | 对手用户 ID |
| opponent.username | string | 对手用户名 |
| opponent.avatar_url | string | 对手头像 URL |
| opponent.rating | integer | 对手等级分 |
| result | string | 对局结果（win/loss/draw） |
| rating_change | integer | 等级分变化 |
| is_red | boolean | 是否执红 |
| game_type | string | 游戏类型（single/multiplayer/ai） |
| created_at | datetime | 对局时间 |

#### 分页说明

| 字段 | 类型 | 说明 |
|------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total_count | integer | 总记录数 |
| total_pages | integer | 总页数 |
| has_next | boolean | 是否有下一页 |
| has_prev | boolean | 是否有上一页 |

---

## 代码示例

### cURL

#### 获取当前用户 Profile

```bash
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer <access_token>"
```

#### 更新用户信息

```bash
curl -X PATCH http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "avatar": "https://example.com/new_avatar.png"
  }'
```

#### 修改密码

```bash
curl -X PUT http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440000/password/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPass123!",
    "new_password": "NewPass456!"
  }'
```

#### 获取用户对局历史

```bash
curl -X GET "http://localhost:8000/api/v1/users/550e8400-e29b-41d4-a716-446655440000/games/?page=1&page_size=20" \
  -H "Authorization: Bearer <access_token>"
```

---

### JavaScript

```javascript
// 获取当前用户 Profile
async function getUserProfile(token) {
  const response = await fetch('http://localhost:8000/api/v1/users/profile/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data;
}

// 更新用户信息
async function updateUserProfile(token, updates) {
  const response = await fetch('http://localhost:8000/api/v1/users/profile/', {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });
  const data = await response.json();
  return data.data;
}

// 获取用户对局历史
async function getUserGames(token, userId, page = 1, pageSize = 20) {
  const response = await fetch(
    `http://localhost:8000/api/v1/users/${userId}/games/?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
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

def get_user_profile(token):
    """获取当前用户 Profile"""
    response = requests.get(
        f'{BASE_URL}/api/v1/users/profile/',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']

def update_user_profile(token, updates):
    """更新用户信息"""
    response = requests.patch(
        f'{BASE_URL}/api/v1/users/profile/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        json=updates
    )
    return response.json()['data']

def get_user_games(token, user_id, page=1, page_size=20):
    """获取用户对局历史"""
    response = requests.get(
        f'{BASE_URL}/api/v1/users/{user_id}/games/',
        params={'page': page, 'page_size': page_size},
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']
```

---

## 相关文档

- [认证 API](./authentication.md) - 用户注册、登录、Token 管理
- [游戏 API](./games.md) - 游戏对局相关 API
- [错误码说明](../errors.md) - 完整错误码列表

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
