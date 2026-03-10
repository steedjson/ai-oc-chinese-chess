# Chinese Chess API 参考文档

**版本**: 1.0.0  
**最后更新**: 2026-03-06  
**基础 URL**: `http://localhost:8000`

---

## 目录

1. [概述](#概述)
2. [认证](#认证)
3. [API 端点](#api-端点)
4. [错误处理](#错误处理)
5. [速率限制](#速率限制)
6. [版本控制](#版本控制)

---

## 概述

Chinese Chess API 提供中国象棋游戏的完整后端功能，包括用户认证、游戏对局、AI 引擎、匹配系统、每日挑战等功能。

### 基础路径

| 环境 | URL |
|------|-----|
| 开发 | `http://localhost:8000` |
| 生产 | `https://api.chinese-chess.com` |

### API 版本

当前 API 版本为 **v1**，所有端点都以 `/api/v1/` 为前缀（健康检查端点除外）。

### 数据格式

- **请求格式**: `application/json`
- **响应格式**: `application/json`
- **字符编码**: `UTF-8`

### 响应格式

所有 API 响应遵循统一格式：

#### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2026-03-06T09:00:00Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

## 认证

### JWT Token 认证

本 API 使用 JWT (JSON Web Token) 进行认证。

#### Token 类型

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| Access Token | 2 小时 | 访问受保护的资源 |
| Refresh Token | 7 天 | 刷新 Access Token |

#### 使用方式

在请求头中添加 `Authorization` 字段：

```
Authorization: Bearer <access_token>
```

### 认证流程

```
1. 用户注册/登录 → 获取 Access Token + Refresh Token
2. 使用 Access Token 访问受保护资源
3. Access Token 过期 → 使用 Refresh Token 刷新
4. Refresh Token 过期 → 重新登录
```

### 认证端点

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/auth/register/` | POST | ❌ | 用户注册 |
| `/api/v1/auth/login/` | POST | ❌ | 用户登录 |
| `/api/v1/auth/logout/` | POST | ✅ | 用户登出 |
| `/api/v1/auth/refresh/` | POST | ❌ | 刷新 Token |
| `/api/v1/auth/me/` | GET | ✅ | 获取当前用户信息 |

详细文档：[authentication.md](./authentication.md)

---

## API 端点

### 认证模块 (Authentication)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/auth/register/` | POST | ❌ | 用户注册 |
| `/api/v1/auth/login/` | POST | ❌ | 用户登录 |
| `/api/v1/auth/logout/` | POST | ✅ | 用户登出 |
| `/api/v1/auth/refresh/` | POST | ❌ | 刷新 Token |
| `/api/v1/auth/me/` | GET | ✅ | 获取当前用户 |

📄 详细文档：[端点文档 - 认证](./endpoints/authentication.md)

---

### 游戏对局模块 (Games)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/games/` | GET | ✅ | 获取对局列表 |
| `/api/v1/games/` | POST | ✅ | 创建新对局 |
| `/api/v1/games/{id}/` | GET | ✅ | 获取对局详情 |
| `/api/v1/games/{id}/` | PUT | ✅ | 更新对局 |
| `/api/v1/games/{id}/` | DELETE | ✅ | 取消对局 |
| `/api/v1/games/{id}/move/` | POST | ✅ | 提交走棋 |
| `/api/v1/games/{id}/moves/` | GET | ✅ | 获取走棋历史 |
| `/api/v1/games/{id}/status/` | PUT | ✅ | 更新对局状态 |
| `/api/v1/users/{id}/games/` | GET | ✅ | 获取用户对局 |
| `/api/v1/games/{id}/spectators/` | GET | ✅ | 获取观战者 |
| `/api/v1/chat/games/{id}/send/` | POST | ✅ | 发送聊天消息 |
| `/api/v1/chat/games/{id}/history/` | GET | ✅ | 获取聊天历史 |

📄 详细文档：[端点文档 - 游戏](./endpoints/games.md)

---

### 每日挑战模块 (Daily Challenge)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/daily-challenge/today/` | GET | ❌ | 获取今日挑战 |
| `/api/v1/daily-challenge/today/attempt/` | POST | ✅ | 开始挑战 |
| `/api/v1/daily-challenge/today/move/` | POST | ✅ | 提交走法 |
| `/api/v1/daily-challenge/today/complete/` | POST | ✅ | 完成挑战 |
| `/api/v1/daily-challenge/leaderboard/` | GET | ❌ | 获取排行榜 |
| `/api/v1/daily-challenge/leaderboard/daily/` | GET | ❌ | 每日排行榜 |
| `/api/v1/daily-challenge/leaderboard/weekly/` | GET | ❌ | 周排行榜 |
| `/api/v1/daily-challenge/leaderboard/all-time/` | GET | ❌ | 总排行榜 |
| `/api/v1/daily-challenge/leaderboard/user/{id}/` | GET | ❌ | 用户排名 |
| `/api/v1/daily-challenge/streak/` | GET | ✅ | 用户连续打卡 |
| `/api/v1/daily-challenge/history/` | GET | ❌ | 挑战历史 |
| `/api/v1/daily-challenge/generate-tomorrow/` | POST | ✅(staff) | 生成明日挑战 |

📄 详细文档：[端点文档 - 每日挑战](./endpoints/daily_challenge.md)

---

### 健康检查模块 (Health)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/health/` | GET | ❌ | 综合健康检查 |
| `/api/health/db/` | GET | ❌ | 数据库状态 |
| `/api/health/redis/` | GET | ❌ | Redis 状态 |
| `/api/health/websocket/` | GET | ❌ | WebSocket 状态 |

📄 详细文档：[端点文档 - 健康检查](./endpoints/health.md)

---

### AI 引擎模块 (AI Engine)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/ai/move/` | POST | ✅ | AI 走棋 |
| `/api/v1/ai/analyze/` | POST | ✅ | 局面分析 |
| `/api/v1/ai/status/` | GET | ❌ | 引擎状态 |

📄 详细文档：[端点文档 - AI 引擎](./endpoints/ai_engine.md)

---

### 匹配系统模块 (Matchmaking)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/matchmaking/queue/` | POST | ✅ | 加入匹配队列 |
| `/api/v1/matchmaking/queue/` | DELETE | ✅ | 退出匹配队列 |
| `/api/v1/matchmaking/status/` | GET | ✅ | 匹配状态 |
| `/api/v1/ranking/leaderboard/` | GET | ❌ | 天梯排行榜 |
| `/api/v1/ranking/player/{id}/` | GET | ❌ | 玩家天梯信息 |

📄 详细文档：[端点文档 - 匹配系统](./endpoints/matchmaking.md)

---

### 用户模块 (Users)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/users/{id}/` | GET | ✅ | 获取用户信息 |
| `/api/v1/users/{id}/` | PUT | ✅ | 更新用户信息 |
| `/api/v1/users/{id}/avatar/` | PUT | ✅ | 更新头像 |
| `/api/v1/users/{id}/password/` | PUT | ✅ | 修改密码 |
| `/api/v1/users/{id}/stats/` | GET | ✅ | 用户统计 |

📄 详细文档：[端点文档 - 用户](./endpoints/users.md)

---

### 残局谜题模块 (Puzzles)

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/puzzles/` | GET | ✅ | 获取谜题列表 |
| `/api/v1/puzzles/{id}/` | GET | ✅ | 获取谜题详情 |
| `/api/v1/puzzles/{id}/attempt/` | POST | ✅ | 开始谜题 |
| `/api/v1/puzzles/{id}/solution/` | GET | ✅ | 获取解答 |

📄 详细文档：[端点文档 - 残局谜题](./endpoints/puzzles.md)

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": { ... }  // 可选的详细信息
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

### 错误码分类

| 分类 | 错误码前缀 | 说明 |
|------|-----------|------|
| 认证错误 | 1xxx | 认证、Token 相关 |
| 验证错误 | 2xxx | 参数验证相关 |
| 用户错误 | 3xxx | 用户操作相关 |
| 游戏错误 | 4xxx | 游戏对局相关 |
| AI 错误 | 5xxx | AI 引擎相关 |
| 匹配错误 | 6xxx | 匹配系统相关 |
| WebSocket 错误 | 7xxx | WebSocket 连接相关 |
| 服务器错误 | 9xxx | 服务器内部错误 |

### 常见错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `TOKEN_REQUIRED` | 400 | 缺少 Token |
| `TOKEN_INVALID` | 401 | Token 无效或已过期 |
| `USER_BANNED` | 403 | 账号已被封禁 |
| `USER_INACTIVE` | 403 | 账号已被禁用 |
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `PERMISSION_DENIED` | 403 | 无权限 |
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `INVALID_MOVE` | 400 | 无效走棋 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 |

📄 完整错误码文档：[errors.md](./errors.md)

---

## 速率限制

### 默认限制

| 端点类型 | 限制 | 时间窗口 |
|---------|------|---------|
| 认证端点 | 10 次/分钟 | 滑动窗口 |
| 游戏端点 | 100 次/分钟 | 滑动窗口 |
| 其他端点 | 60 次/分钟 | 滑动窗口 |
| 健康检查 | 30 次/分钟 | 滑动窗口 |

### 速率限制响应

当超过速率限制时，返回 `429 Too Many Requests`：

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "retry_after": 60
  }
}
```

响应头中包含速率限制信息：

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709689260
Retry-After: 60
```

---

## 版本控制

### URL 版本控制

API 版本通过 URL 路径控制：

```
/api/v1/...
/api/v2/...  (未来版本)
```

### 版本兼容性

- **v1**: 当前稳定版本
- 破坏性变更将引入新版本
- 旧版本将在新版本发布后维护 6 个月

### 版本迁移

当新版本发布时，将提供：
- 迁移指南
- 废弃通知（至少提前 3 个月）
- 兼容层（如适用）

---

## WebSocket API

### 连接端点

```
ws://localhost:8000/ws/game/{game_id}/
```

### 认证

在连接 URL 中添加 Token：

```
ws://localhost:8000/ws/game/{game_id}/?token=<access_token>
```

### 消息格式

#### 客户端 → 服务器

```json
{
  "type": "move",
  "data": {
    "from_pos": "e3",
    "to_pos": "e4"
  }
}
```

#### 服务器 → 客户端

```json
{
  "type": "move_result",
  "data": {
    "success": true,
    "move": { ... },
    "fen": "..."
  }
}
```

### 消息类型

| 类型 | 方向 | 描述 |
|------|------|------|
| `move` | C→S | 提交走棋 |
| `move_result` | S→C | 走棋结果 |
| `opponent_move` | S→C | 对手走棋 |
| `game_state` | S→C | 游戏状态更新 |
| `chat_message` | C→S / S→C | 聊天消息 |
| `spectator_join` | S→C | 观战者加入 |
| `spectator_leave` | S→C | 观战者离开 |

📄 完整 WebSocket 文档：[websocket.md](./websocket.md)

---

## SDK 和示例代码

### cURL 示例

#### 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "SecurePass123!"
  }'
```

#### 创建对局

```bash
curl -X POST http://localhost:8000/api/v1/games/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "game_type": "single",
    "ai_level": 5
  }'
```

#### 提交走棋

```bash
curl -X POST http://localhost:8000/api/v1/games/{game_id}/move/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "from_pos": "e3",
    "to_pos": "e4"
  }'
```

### JavaScript 示例

```javascript
// 登录
const login = async (username, password) => {
  const response = await fetch('/api/v1/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  return data.data.access_token;
};

// 创建对局
const createGame = async (token) => {
  const response = await fetch('/api/v1/games/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ game_type: 'single', ai_level: 5 })
  });
  return await response.json();
};
```

### Python 示例

```python
import requests

BASE_URL = 'http://localhost:8000'

def login(username, password):
    response = requests.post(
        f'{BASE_URL}/api/v1/auth/login/',
        json={'username': username, 'password': password}
    )
    return response.json()['data']['access_token']

def create_game(token):
    response = requests.post(
        f'{BASE_URL}/api/v1/games/',
        headers={'Authorization': f'Bearer {token}'},
        json={'game_type': 'single', 'ai_level': 5}
    )
    return response.json()
```

---

## 支持

### 问题反馈

- **GitHub Issues**: https://github.com/chinese-chess/api/issues
- **文档问题**: 请在 Issue 中标记 `documentation` 标签

### 联系方式

- **技术支持**: support@chinese-chess.com
- **商务合作**: business@chinese-chess.com

### 更新日志

查看 [CHANGELOG.md](./CHANGELOG.md) 获取最新版本变更。

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
