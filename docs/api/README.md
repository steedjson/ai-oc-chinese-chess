# 中国象棋 API 文档

**版本**: v1.1.0  
**最后更新**: 2026-03-11  
**基础路径**: `/api/v1`  
**总端点数量**: 73

---

## 📋 目录

### 核心文档
1. [认证流程](#认证流程)
2. [API 端点总览表](#api 端点总览表)
3. [错误码说明](#错误码说明)

### 模块文档
4. [认证 API](#认证-api) - 5 个端点
5. [用户 API](#用户-api) - 8 个端点
6. [游戏 API](#游戏-api) - 11 个端点
7. [观战 API](#观战-api) - 6 个端点
8. [聊天 API](#聊天-api) - 4 个端点
9. [匹配 API](#匹配-api) - 3 个端点
10. [排行榜 API](#排行榜-api) - 3 个端点
11. [AI API](#ai-api) - 10 个端点
12. [残局 API](#残局-api) - 7 个端点
13. [每日挑战 API](#每日挑战-api) - 12 个端点
14. [健康检查 API](#健康检查-api) - 4 个端点
15. [WebSocket 协议](#websocket-协议)

### 附录
16. [请求/响应示例](#请求响应示例)
17. [SDK 和代码示例](#sdk 和代码示例)

---

## 🔐 认证流程

### JWT Token 认证

本 API 使用 **JWT (JSON Web Token)** 进行认证。

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| **Access Token** | 2 小时 | 访问受保护资源 |
| **Refresh Token** | 7 天 | 刷新 Access Token |

### 认证流程

```
1. 用户登录/注册 → 获取 Access Token + Refresh Token
2. 访问受保护资源 → Header 携带 Access Token
3. Token 过期 → 使用 Refresh Token 刷新
4. 刷新失败 → 重新登录
```

### 请求头格式

所有需要认证的请求需包含以下 Header：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### curl 示例

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "SecurePass123"}'

# 使用 Token 访问受保护资源
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 📊 API 端点总览表

| 模块 | 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|------|
| **认证** | `/auth/register/` | POST | ❌ | 用户注册 |
| | `/auth/login/` | POST | ❌ | 用户登录 |
| | `/auth/logout/` | POST | ✅ | 用户登出 |
| | `/auth/refresh/` | POST | ❌ | 刷新 Token |
| | `/auth/me/` | GET | ✅ | 获取当前用户 |
| **用户** | `/users/profile/` | GET/PUT/PATCH | ✅ | 个人信息管理 |
| | `/users/me/stats/` | GET | ✅ | 个人统计 |
| | `/users/{id}/` | GET/PUT/PATCH | ✅ | 用户详情 |
| | `/users/{id}/password/` | PUT | ✅ | 修改密码 |
| | `/users/{id}/stats/` | GET | ✅ | 用户统计 |
| | `/users/{id}/games/` | GET | ✅ | 用户对局 |
| **游戏** | `/games/` | GET/POST | ✅ | 对局列表/创建 |
| | `/games/{id}/` | GET/DELETE | ✅ | 对局详情/取消 |
| | `/games/{id}/join/` | POST | ✅ | 加入对局 |
| | `/games/{id}/move/` | POST | ✅ | 提交走棋 |
| | `/games/{id}/moves/` | GET | ✅ | 走棋历史 |
| | `/games/{id}/status/` | PUT | ✅ | 更新状态 |
| | `/games/{id}/spectators/` | GET | ✅ | 观战者列表 |
| **观战** | `/games/{id}/spectate/` | POST | ✅ | 加入观战 |
| | `/games/{id}/spectate/leave/` | POST | ✅ | 离开观战 |
| | `/games/{id}/spectators/kick/` | POST | ✅ | 踢出观战 |
| | `/spectator/active-games/` | GET | ✅ | 可观看对局 |
| **聊天** | `/chat/games/{id}/send/` | POST | ✅ | 发送消息 |
| | `/chat/games/{id}/history/` | GET | ✅ | 聊天历史 |
| | `/chat/messages/{id}/delete/` | DELETE | ✅ | 删除消息 |
| | `/chat/games/{id}/stats/` | GET | ✅ | 聊天统计 |
| **匹配** | `/matchmaking/start/` | POST | ✅ | 开始匹配 |
| | `/matchmaking/cancel/` | POST | ✅ | 取消匹配 |
| | `/matchmaking/status/` | GET | ✅ | 匹配状态 |
| **排行榜** | `/ranking/leaderboard/` | GET | ❌ | 天梯排名 |
| | `/ranking/user/{id}/` | GET | ❌ | 用户排名 |
| | `/ranking/user/` | GET | ✅ | 当前用户排名 |
| **AI** | `/ai/games/` | GET/POST | ✅ | AI 对局列表/创建 |
| | `/ai/games/{id}/` | GET/PUT/DELETE | ✅ | AI 对局管理 |
| | `/ai/games/{id}/move/` | POST | ✅ | AI 走棋 |
| | `/ai/games/{id}/hint/` | POST | ✅ | AI 提示 |
| | `/ai/games/{id}/analyze/` | POST | ✅ | AI 分析 |
| | `/ai/difficulties/` | GET | ❌ | 难度列表 |
| | `/ai/engines/status/` | GET | ✅ | 引擎状态 |
| **残局** | `/puzzles/` | GET | ✅ | 关卡列表 |
| | `/puzzles/{id}/` | GET | ✅ | 关卡详情 |
| | `/puzzles/{id}/attempt/` | POST | ✅ | 创建挑战 |
| | `/puzzles/{id}/attempts/{id}/move/` | POST | ✅ | 提交走法 |
| | `/puzzles/{id}/attempts/{id}/complete/` | POST | ✅ | 完成挑战 |
| | `/puzzles/progress/` | GET | ✅ | 用户进度 |
| | `/puzzles/leaderboard/` | GET | ✅ | 残局排行 |
| **每日挑战** | `/daily-challenge/today/` | GET | ✅ | 今日挑战 |
| | `/daily-challenge/today/attempt/` | POST | ✅ | 开始挑战 |
| | `/daily-challenge/today/move/` | POST | ✅ | 提交走法 |
| | `/daily-challenge/today/complete/` | POST | ✅ | 完成挑战 |
| | `/daily-challenge/leaderboard/` | GET | ✅ | 挑战排行 |
| | `/daily-challenge/leaderboard/daily/` | GET | ✅ | 每日排行 |
| | `/daily-challenge/leaderboard/weekly/` | GET | ✅ | 周排行 |
| | `/daily-challenge/leaderboard/all-time/` | GET | ✅ | 总排行 |
| | `/daily-challenge/streak/` | GET | ✅ | 连胜记录 |
| | `/daily-challenge/history/` | GET | ✅ | 挑战历史 |
| **健康** | `/health/` | GET | ❌ | 综合健康检查 |
| | `/health/db/` | GET | ❌ | 数据库状态 |
| | `/health/redis/` | GET | ❌ | Redis 状态 |
| | `/health/websocket/` | GET | ❌ | WebSocket 状态 |

---

## 🔑 认证 API

**详细文档**: [endpoints/authentication.md](./endpoints/authentication.md)

**基础路径**: `/api/v1/auth/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/register/` | POST | ❌ | 用户注册 |
| `/login/` | POST | ❌ | 用户登录 |
| `/logout/` | POST | ✅ | 用户登出 |
| `/refresh/` | POST | ❌ | 刷新 Token |
| `/me/` | GET | ✅ | 获取当前用户 |

---

## 👤 用户 API

**详细文档**: [endpoints/users.md](./endpoints/users.md)

**基础路径**: `/api/v1/users/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/profile/` | GET/PUT/PATCH | ✅ | 个人信息管理 |
| `/me/stats/` | GET | ✅ | 个人统计 |
| `/{id}/` | GET/PUT/PATCH | ✅ | 用户详情 |
| `/{id}/password/` | PUT | ✅ | 修改密码 |
| `/{id}/stats/` | GET | ✅ | 用户统计 |
| `/{id}/games/` | GET | ✅ | 用户对局 |

---

## ♟️ 游戏 API

**详细文档**: [endpoints/games.md](./endpoints/games.md)

**基础路径**: `/api/v1/games/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET/POST | ✅ | 对局列表/创建 |
| `/{id}/` | GET/DELETE | ✅ | 对局详情/取消 |
| `/{id}/join/` | POST | ✅ | 加入对局 |
| `/{id}/move/` | POST | ✅ | 提交走棋 |
| `/{id}/moves/` | GET | ✅ | 走棋历史 |
| `/{id}/status/` | PUT | ✅ | 更新状态 |
| `/{id}/spectators/` | GET | ✅ | 观战者列表 |

---

## 👁️ 观战 API

**详细文档**: 详见游戏 API 文档

**基础路径**: `/api/v1/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/{id}/spectate/` | POST | ✅ | 加入观战 |
| `/games/{id}/spectate/leave/` | POST | ✅ | 离开观战 |
| `/games/{id}/spectators/kick/` | POST | ✅ | 踢出观战 |
| `/spectator/active-games/` | GET | ✅ | 可观看对局 |

---

## 💬 聊天 API

**详细文档**: 详见游戏 API 文档

**基础路径**: `/api/v1/chat/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/{id}/send/` | POST | ✅ | 发送消息 |
| `/games/{id}/history/` | GET | ✅ | 聊天历史 |
| `/messages/{id}/delete/` | DELETE | ✅ | 删除消息 |
| `/games/{id}/stats/` | GET | ✅ | 聊天统计 |

---

## 🎯 匹配 API

**详细文档**: [endpoints/matchmaking.md](./endpoints/matchmaking.md)

**基础路径**: `/api/v1/matchmaking/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/start/` | POST | ✅ | 开始匹配 |
| `/cancel/` | POST | ✅ | 取消匹配 |
| `/status/` | GET | ✅ | 匹配状态 |

---

## 🏆 排行榜 API

**详细文档**: [ranking-api.md](./ranking-api.md)

**基础路径**: `/api/v1/ranking/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/leaderboard/` | GET | ❌ | 天梯排名 |
| `/user/{id}/` | GET | ❌ | 用户排名 |
| `/user/` | GET | ✅ | 当前用户排名 |

---

## 🤖 AI API

**详细文档**: [endpoints/ai_engine.md](./endpoints/ai_engine.md)

**基础路径**: `/api/v1/ai/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/games/` | GET/POST | ✅ | AI 对局列表/创建 |
| `/games/{id}/` | GET/PUT/DELETE | ✅ | AI 对局管理 |
| `/games/{id}/move/` | POST | ✅ | AI 走棋 |
| `/games/{id}/hint/` | POST | ✅ | AI 提示 |
| `/games/{id}/analyze/` | POST | ✅ | AI 分析 |
| `/difficulties/` | GET | ❌ | 难度列表 |
| `/engines/status/` | GET | ✅ | 引擎状态 |

---

## 🧩 残局 API

**详细文档**: [endpoints/puzzles.md](./endpoints/puzzles.md)

**基础路径**: `/api/v1/puzzles/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | ✅ | 关卡列表 |
| `/{id}/` | GET | ✅ | 关卡详情 |
| `/{id}/attempt/` | POST | ✅ | 创建挑战 |
| `/{id}/attempts/{id}/move/` | POST | ✅ | 提交走法 |
| `/{id}/attempts/{id}/complete/` | POST | ✅ | 完成挑战 |
| `/progress/` | GET | ✅ | 用户进度 |
| `/leaderboard/` | GET | ✅ | 残局排行 |

---

## 📅 每日挑战 API

**详细文档**: [endpoints/daily_challenge.md](./endpoints/daily_challenge.md)

**基础路径**: `/api/v1/daily-challenge/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/today/` | GET | ✅ | 今日挑战 |
| `/today/attempt/` | POST | ✅ | 开始挑战 |
| `/today/move/` | POST | ✅ | 提交走法 |
| `/today/complete/` | POST | ✅ | 完成挑战 |
| `/leaderboard/` | GET | ✅ | 挑战排行 |
| `/leaderboard/daily/` | GET | ✅ | 每日排行 |
| `/leaderboard/weekly/` | GET | ✅ | 周排行 |
| `/leaderboard/all-time/` | GET | ✅ | 总排行 |
| `/streak/` | GET | ✅ | 连胜记录 |
| `/history/` | GET | ✅ | 挑战历史 |

---

## 🏥 健康检查 API

**详细文档**: [endpoints/health.md](./endpoints/health.md)

**基础路径**: `/api/health/`

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | ❌ | 综合健康检查 |
| `/db/` | GET | ❌ | 数据库状态 |
| `/redis/` | GET | ❌ | Redis 状态 |
| `/websocket/` | GET | ❌ | WebSocket 状态 |

---

## 🔌 WebSocket 协议

**详细文档**: [websocket.md](./websocket.md)

### 连接端点

```
wss://<host>/ws/game/<game_id>/
```

### 认证方式

WebSocket 连接需要在查询参数中传递 Token：

```
wss://<host>/ws/game/<game_id>/?token=<access_token>
```

### 消息格式

所有消息使用 JSON 格式：

```json
{
  "type": "message_type",
  "data": { ... }
}
```

### 客户端 → 服务端消息

| 类型 | 描述 | 数据格式 |
|------|------|---------|
| `join_game` | 加入游戏 | `{"game_id": "uuid"}` |
| `make_move` | 提交走棋 | `{"from": "e2", "to": "e4"}` |
| `chat_message` | 发送聊天 | `{"content": "消息内容"}` |
| `leave_game` | 离开游戏 | `{}` |
| `ping` | 心跳 | `{"timestamp": 1234567890}` |

### 服务端 → 客户端消息

| 类型 | 描述 | 数据格式 |
|------|------|---------|
| `game_state` | 游戏状态 | `{"fen": "...", "turn": "red"}` |
| `move_made` | 走棋通知 | `{"from": "e2", "to": "e4", "player": "red"}` |
| `chat_message` | 聊天消息 | `{"sender": "user1", "content": "..."}` |
| `game_over` | 游戏结束 | `{"winner": "red", "reason": "checkmate"}` |
| `error` | 错误消息 | `{"code": "ERROR_CODE", "message": "..."}` |
| `pong` | 心跳响应 | `{"timestamp": 1234567890}` |

---

## ❌ 错误码说明

**详细文档**: [errors.md](./errors.md)

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": { ... }
  },
  "timestamp": "2026-03-11T12:00:00Z"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `INVALID_CREDENTIALS` | 用户名或密码错误 | 检查凭证后重试 |
| `TOKEN_INVALID` | Token 无效或已过期 | 刷新 Token 或重新登录 |
| `VALIDATION_ERROR` | 参数验证失败 | 检查请求参数格式 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 检查资源 ID |
| `PERMISSION_DENIED` | 权限不足 | 检查用户权限 |
| `RATE_LIMIT_EXCEEDED` | 请求过于频繁 | 稍后重试 |

---

## 📝 请求/响应示例

### cURL 示例

```bash
# 用户注册
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "SecurePass123"
  }'

# 创建 AI 对局
curl -X POST http://localhost:8000/api/v1/ai/games/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"difficulty": 5}'

# 获取排行榜
curl -X GET http://localhost:8000/api/v1/ranking/leaderboard/ \
  -H "Authorization: Bearer <access_token>"
```

### JavaScript 示例

```javascript
// 使用 Fetch API
const response = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'player1',
    password: 'SecurePass123',
  }),
});

const data = await response.json();
console.log('Access Token:', data.access_token);
```

### Python 示例

```python
import requests

# 用户登录
response = requests.post('http://localhost:8000/api/v1/auth/login/', json={
    'username': 'player1',
    'password': 'SecurePass123'
})

token = response.json()['access_token']

# 创建 AI 对局
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8000/api/v1/ai/games/',
    headers=headers,
    json={'difficulty': 5}
)
```

---

## 📊 API 统计

### 端点分布

| 分类 | 数量 | 占比 |
|------|------|------|
| 认证 API | 5 | 6.8% |
| 用户 API | 8 | 11.0% |
| 游戏 API | 11 | 15.1% |
| 观战 API | 4 | 5.5% |
| 聊天 API | 4 | 5.5% |
| 匹配 API | 3 | 4.1% |
| 排行榜 API | 3 | 4.1% |
| AI API | 10 | 13.7% |
| 残局 API | 7 | 9.6% |
| 每日挑战 API | 12 | 16.4% |
| 健康检查 API | 4 | 5.5% |
| **总计** | **73** | **100%** |

### 认证要求

| 类型 | 数量 | 占比 |
|------|------|------|
| 公开端点 | 16 | 21.9% |
| 认证端点 | 57 | 78.1% |
| **总计** | **73** | **100%** |

### HTTP 方法分布

| 方法 | 数量 | 用途 |
|------|------|------|
| GET | 35 | 查询资源 |
| POST | 30 | 创建/操作资源 |
| PUT | 5 | 更新资源 |
| PATCH | 2 | 部分更新 |
| DELETE | 1 | 删除资源 |

---

## 🔗 相关文档

### 模块详细文档
- [认证端点](./endpoints/authentication.md)
- [用户端点](./endpoints/users.md)
- [游戏端点](./endpoints/games.md)
- [AI 引擎端点](./endpoints/ai_engine.md)
- [匹配系统端点](./endpoints/matchmaking.md)
- [残局端点](./endpoints/puzzles.md)
- [每日挑战端点](./endpoints/daily_challenge.md)
- [健康检查端点](./endpoints/health.md)

### 核心文档
- [错误码说明](./errors.md)
- [WebSocket 协议](./websocket.md)
- [排行榜 API](./ranking-api.md)
- [完整 API 参考](./API-REFERENCE-COMPLETE.md)

### 项目文档
- [项目总览](../README.md)
- [架构设计](../architecture.md)
- [开发规范](../DEVELOPMENT-CONSTRAINTS.md)

---

## 📝 更新日志

### v1.1.0 (2026-03-11)
- ✅ 更新：API 端点总览表（73 个端点）
- ✅ 新增：每日挑战 API 完整文档
- ✅ 更新：认证流程和示例代码
- ✅ 更新：WebSocket 协议说明

### v1.0.0 (2026-03-06)
- ✅ 初始版本发布
- ✅ 完成所有核心 API 文档
- ✅ 统一错误码说明

---

**最后更新**: 2026-03-11  
**文档版本**: v1.1.0  
**维护者**: 中国象棋项目组
