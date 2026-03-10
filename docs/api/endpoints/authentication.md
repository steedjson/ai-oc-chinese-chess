# 认证 API 端点 (Authentication Endpoints)

**基础路径**: `/api/v1/auth/`

---

## 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/register/` | POST | ❌ | 用户注册 |
| `/login/` | POST | ❌ | 用户登录 |
| `/logout/` | POST | ✅ | 用户登出 |
| `/refresh/` | POST | ❌ | 刷新 Token |
| `/me/` | GET | ✅ | 获取当前用户信息 |

---

## 1. 用户注册

### POST `/api/v1/auth/register/`

创建新用户账号。

### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "username": "chess_player",
  "email": "player@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 验证规则 | 说明 |
|------|------|------|---------|------|
| username | string | 是 | 3-50 字符，字母数字下划线 | 用户名 |
| email | string | 是 | 有效邮箱格式 | 邮箱地址 |
| password | string | 是 | 最少 8 字符 | 密码 |
| password_confirm | string | 是 | 必须与 password 相同 | 确认密码 |

### 响应

**成功 (201 Created)**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

**失败 (400 Bad Request)**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": {
      "username": ["用户名已被使用"],
      "email": ["该邮箱已被注册"]
    }
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `USERNAME_TAKEN` | 400 | 用户名已被使用 |
| `EMAIL_REGISTERED` | 400 | 邮箱已被注册 |

---

## 2. 用户登录

### POST `/api/v1/auth/login/`

用户登录并获取访问令牌。

### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "username": "chess_player",
  "password": "SecurePass123!"
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200
  },
  "message": "登录成功"
}
```

**失败 (401 Unauthorized)**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

**账号封禁 (403 Forbidden)**:
```json
{
  "success": false,
  "error": {
    "code": "USER_BANNED",
    "message": "账号已被封禁"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `USER_BANNED` | 403 | 账号已被封禁 |
| `USER_INACTIVE` | 403 | 账号已被禁用 |
| `VALIDATION_ERROR` | 400 | 参数验证失败 |

---

## 3. 用户登出

### POST `/api/v1/auth/logout/`

用户登出，使当前 Token 失效（加入黑名单）。

### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**: (可选)
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `TOKEN_INVALID` | 401 | Token 无效或已过期 |

---

## 4. 刷新 Token

### POST `/api/v1/auth/refresh/`

使用 Refresh Token 获取新的 Access Token。

### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | Refresh Token |

### 响应

**成功 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 7200
  },
  "message": "Token 刷新成功"
}
```

**失败 (401 Unauthorized)**:
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Token 已过期或无效"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `TOKEN_REQUIRED` | 400 | Refresh Token 不能为空 |
| `TOKEN_INVALID` | 401 | Token 无效或已过期 |

---

## 5. 获取当前用户信息

### GET `/api/v1/auth/me/`

获取当前登录用户的详细信息。

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
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "first_name": "",
    "last_name": "",
    "avatar_url": "https://cdn.chinese-chess.com/avatars/default.png",
    "elo_rating": 1500,
    "status": "active",
    "is_verified": false,
    "is_staff": false,
    "is_superuser": false,
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-01-15T08:30:00Z",
    "last_login": "2026-03-06T09:00:00Z"
  }
}
```

### 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `TOKEN_INVALID` | 401 | Token 无效或已过期 |

---

## 认证流程示例

### 完整认证流程

```
┌─────────────┐
│   新用户    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ POST /register/ │
│ 获取 Tokens     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  使用 Access    │
│  Token 访问 API │
└──────┬──────────┘
       │
       │ Token 过期 (2 小时后)
       ▼
┌─────────────────┐
│ POST /refresh/  │
│ 刷新 Access     │
└──────┬──────────┘
       │
       │ Refresh Token 过期 (7 天后)
       ▼
┌─────────────────┐
│ POST /login/    │
│ 重新登录        │
└─────────────────┘
```

### cURL 示例

```bash
# 1. 注册
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# 2. 登录
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "password": "SecurePass123!"
  }'

# 3. 获取用户信息
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer <access_token>"

# 4. 刷新 Token
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'

# 5. 登出
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Token 说明

### JWT Token 结构

```
Header.Payload.Signature
```

#### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

#### Payload (Access Token)
```json
{
  "token_type": "access",
  "exp": 1709696400,
  "iat": 1709689200,
  "jti": "unique-token-id",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Token 有效期

| Token 类型 | 有效期 | 可配置 |
|-----------|--------|--------|
| Access Token | 2 小时 | ✅ |
| Refresh Token | 7 天 | ✅ |

### Token 安全

1. **存储**: 建议存储在 HttpOnly Cookie 或安全存储中
2. **传输**: 始终使用 HTTPS
3. **刷新**: Access Token 过期后立即刷新
4. **登出**: 将 Token 加入黑名单

---

## 相关文件

- **视图实现**: `authentication/views.py`
- **URL 路由**: `authentication/urls.py`
- **序列化器**: `users/serializers.py`
- **服务层**: `authentication/services.py`

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06
