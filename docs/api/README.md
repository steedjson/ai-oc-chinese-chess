# 中国象棋 API 文档

## 📚 文档导航

本文档包含中国象棋项目的完整 API 接口说明。

### 文档列表

| 文档 | 描述 |
|------|------|
| [认证 API](./authentication.md) | 用户注册、登录、Token 刷新等认证相关接口 |
| [用户 API](./users.md) | 用户信息管理、密码修改等接口 |
| [游戏 API](./games.md) | 对局创建、走棋、状态管理等接口 |
| [AI 引擎 API](./ai-engine.md) | AI 对弈、提示、分析等接口 |
| [匹配系统 API](./matchmaking.md) | 在线匹配队列相关接口 |
| [WebSocket 协议](./websocket.md) | 实时通信协议说明 |
| [错误码说明](./error-codes.md) | 统一错误码定义 |

---

## 🔧 API 基础信息

### 基础路径

```
http://localhost:8000/api/v1/
```

### 请求格式

- **Content-Type**: `application/json`
- **字符编码**: UTF-8

### 响应格式

所有 API 返回统一的 JSON 格式：

```json
{
  "success": true|false,
  "data": { ... },           // 成功时返回的数据
  "error": {                  // 失败时返回的错误信息
    "code": "ERROR_CODE",
    "message": "错误描述"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 认证方式

API 使用 JWT Token 进行认证，在请求头中添加：

```
Authorization: Bearer <access_token>
```

或使用 URL 参数（仅 WebSocket）：

```
?token=<access_token>
```

### Token 获取

通过登录接口获取：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

响应示例：

```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "your_username",
    "email": "user@example.com",
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "expires_in": 7200
  }
}
```

---

## 📁 模块路由总览

### 主路由配置 (`config/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/', include('games.urls')),
    path('api/v1/ai/', include('ai_engine.urls')),
    path('api/v1/matchmaking/', include('matchmaking.urls')),
    path('api/v1/health/', include('common.health_urls')),
]
```

### 各模块端点速查

#### 认证模块 (`/api/v1/auth/`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/register/` | 用户注册 |
| POST | `/login/` | 用户登录 |
| POST | `/logout/` | 用户登出 |
| POST | `/refresh/` | 刷新 Access Token |
| GET | `/me/` | 获取当前用户信息 |

#### 用户模块 (`/api/v1/users/`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/<int:pk>/` | 获取用户详情 |
| PUT/PATCH | `/<int:pk>/` | 更新用户信息 |
| PUT | `/<int:pk>/password/` | 修改密码 |

#### 游戏模块 (`/api/v1/`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/games/` | 获取对局列表 |
| POST | `/games/` | 创建新对局 |
| GET | `/games/<id>/` | 获取对局详情 |
| DELETE | `/games/<id>/` | 取消对局 |
| GET | `/games/<id>/moves/` | 获取走棋历史 |
| POST | `/games/<id>/move/` | 提交走棋 |
| PUT | `/games/<id>/status/` | 更新对局状态 |
| GET | `/users/<user_id>/games/` | 获取用户对局列表 |

#### AI 引擎模块 (`/api/v1/ai/`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/games/` | 获取 AI 对局列表 |
| POST | `/games/` | 创建 AI 对局 |
| GET | `/games/<game_id>/` | 获取 AI 对局详情 |
| PUT | `/games/<game_id>/` | 更新对局状态 |
| DELETE | `/games/<game_id>/` | 取消 AI 对局 |
| POST | `/games/<game_id>/move/` | 请求 AI 走棋 |
| POST | `/games/<game_id>/hint/` | 请求 AI 提示 |
| POST | `/games/<game_id>/analyze/` | 请求 AI 分析 |
| GET | `/difficulties/` | 获取难度等级列表 |
| GET | `/engines/status/` | 获取引擎池状态 |

#### 匹配系统模块 (`/api/v1/matchmaking/`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/start/` | 开始匹配 |
| POST | `/cancel/` | 取消匹配 |
| GET | `/status/` | 获取匹配状态 |

---

## 🔌 WebSocket 端点

### 连接地址

```
ws://localhost:8000/ws/<endpoint>/?token=<jwt_token>
```

### 可用端点

| 端点 | 描述 |
|------|------|
| `/ws/game/<game_id>/` | 游戏对弈房间 |
| `/ws/ai/game/<game_id>/` | AI 对弈房间 |
| `/ws/matchmaking/` | 匹配队列 |

详细协议说明请查看 [WebSocket 协议文档](./websocket.md)。

---

## ⚠️ 错误处理

### HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 错误码列表

详见 [错误码说明文档](./error-codes.md)。

---

## 📝 版本信息

- **API 版本**: v1
- **最后更新**: 2024-03-04
- **文档维护**: doc-updater agent
