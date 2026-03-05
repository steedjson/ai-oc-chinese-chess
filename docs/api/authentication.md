# 认证 API (Authentication API)

## 基础路径
`/api/v1/auth/`

---

## 端点列表

### 1. 用户注册

**POST** `/api/v1/auth/register/`

#### 描述
创建新用户账号。

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50字符） |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |
| password_confirm | string | 是 | 确认密码 |

#### 请求示例
```json
{
  "username": "chess_player",
  "email": "player@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!"
}
```

#### 成功响应 (201 Created)
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "注册成功"
}
```

#### 错误响应
| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 400 | USERNAME_TAKEN | 用户名已被使用 |
| 400 | EMAIL_REGISTERED | 邮箱已被注册 |

---

### 2. 用户登录

**POST** `/api/v1/auth/login/`

#### 描述
用户登录并获取访问令牌。

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 请求示例
```json
{
  "username": "chess_player",
  "password": "SecurePass123!"
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
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "登录成功"
}
```

#### 错误响应
| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 401 | INVALID_CREDENTIALS | 用户名或密码错误 |
| 403 | USER_BANNED | 账号已被封禁 |
| 403 | USER_INACTIVE | 账号已被禁用 |
| 400 | VALIDATION_ERROR | 参数验证失败 |

---

### 3. 用户登出

**POST** `/api/v1/auth/logout/`

#### 描述
用户登出，使当前 Token 失效。

#### 认证要求
需要有效的 JWT Access Token。

#### 请求头
```
Authorization: Bearer <access_token>
```

#### 成功响应 (200 OK)
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

### 4. 刷新 Token

**POST** `/api/v1/auth/refresh/`

#### 描述
使用 Refresh Token 获取新的 Access Token。

#### 请求参数
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | Refresh Token |

#### 请求示例
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### 成功响应 (200 OK)
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  },
  "message": "Token 刷新成功"
}
```

#### 错误响应
| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | TOKEN_REQUIRED | Refresh Token 不能为空 |
| 401 | TOKEN_INVALID | Token 无效或已过期 |

---

### 5. 获取当前用户信息

**GET** `/api/v1/auth/me/`

#### 描述
获取当前登录用户的详细信息。

#### 认证要求
需要有效的 JWT Access Token。

#### 请求头
```
Authorization: Bearer <access_token>
```

#### 成功响应 (200 OK)
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_player",
    "email": "player@example.com",
    "first_name": "",
    "last_name": "",
    "avatar_url": null,
    "elo_rating": 1500,
    "status": "active",
    "is_verified": false,
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-01-15T08:30:00Z"
  }
}
```

---

## 认证流程

### 标准认证流程

```
┌─────────┐     POST /auth/register      ┌─────────┐
│  Client │ ───────────────────────────> │ Server  │
│         │                              │         │
│         │ <─────────────────────────── │         │
│         │   {access_token, refresh_token}        │
└─────────┘                              └─────────┘
       │
       │ 后续请求
       ▼
┌─────────────┐
Authorization: Bearer <access_token>
└─────────────┘
       │
       │ Token 过期
       ▼
┌─────────┐     POST /auth/refresh       ┌─────────┐
│  Client │ ───────────────────────────> │ Server  │
│         │   {refresh_token}            │         │
│         │ <─────────────────────────── │         │
│         │   {new_access_token}         │         │
└─────────┘                              └─────────┘
```

### Token 有效期
- **Access Token**: 2 小时 (7200 秒)
- **Refresh Token**: 7 天

---

## 错误码说明

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| VALIDATION_ERROR | 参数验证失败 | 400 |
| INVALID_CREDENTIALS | 用户名或密码错误 | 401 |
| USER_BANNED | 账号已被封禁 | 403 |
| USER_INACTIVE | 账号已被禁用 | 403 |
| TOKEN_REQUIRED | Token 不能为空 | 400 |
| TOKEN_INVALID | Token 无效或已过期 | 401 |
