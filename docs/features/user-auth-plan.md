# 🔐 用户认证系统 - 功能规划文档

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**优先级**：P0  
**状态**：待实现

---

## 1. 功能概述

### 1.1 功能描述

用户认证系统是整个中国象棋平台的基础设施，提供用户注册、登录、身份验证、密码管理和用户信息管理等功能。该系统采用 JWT Token 认证机制，确保 API 调用的安全性和无状态性。

### 1.2 功能范围

**包含**：
- 用户注册（邮箱/用户名）
- 用户登录（账号密码）
- JWT Token 认证（Access Token + Refresh Token）
- 密码加密存储（bcrypt）
- 用户信息管理（查看/编辑）
- Token 刷新机制
- 用户登出

**不包含**（P1/P2）：
- 密码找回（P1）
- 邮箱验证（P1）
- 第三方登录（微信/QQ）（P2）
- 账号注销（P2）
- 双因素认证（P2）

### 1.3 技术选型

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| **认证机制** | JWT (JSON Web Token) | 无状态、跨域支持、生态成熟 |
| **密码加密** | bcrypt | 安全、不可逆、抗彩虹表 |
| **Token 存储** | HttpOnly Cookie + localStorage | 安全 + 灵活 |
| **有效期** | Access Token: 2h, Refresh Token: 7d | 平衡安全与体验 |

---

## 2. 用户故事

### 2.1 核心用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|--------|
| **US-AUTH-01** | 作为新用户，我希望通过邮箱或用户名快速注册账号，以便开始游戏 | 注册流程≤3 步，1 分钟内完成，用户名唯一性校验 | P0 |
| **US-AUTH-02** | 作为已注册用户，我希望使用账号密码登录，以便访问我的个人数据 | 登录响应时间<500ms，支持记住登录状态 | P0 |
| **US-AUTH-03** | 作为登录用户，我希望在 Token 过期后自动刷新，以便无感知继续使用 | 刷新过程用户无感知，刷新失败时提示重新登录 | P0 |
| **US-AUTH-04** | 作为用户，我希望查看和编辑我的个人资料（昵称、头像），以便展示个性 | 支持上传头像（≤2MB），昵称可修改（1-20 字符） | P0 |
| **US-AUTH-05** | 作为用户，我希望修改我的密码，以便保障账号安全 | 需验证旧密码，新密码强度校验（≥8 位，含字母 + 数字） | P0 |

### 2.2 用户旅程地图

```
新用户注册流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 访问首页 │ →  │ 点击注册 │ →  │ 填写信息 │ →  │ 提交验证 │ →  │ 注册成功 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │
                                    ▼
                          输入：用户名、邮箱、密码
                          验证：唯一性、格式、强度

用户登录流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 访问首页 │ →  │ 点击登录 │ →  │ 输入凭证 │ →  │ 验证通过 │ →  │ 进入大厅 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │
                                    ▼
                          颁发：Access Token + Refresh Token
                          存储：HttpOnly Cookie + 内存

Token 刷新流程：
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ API 调用 401  │ →  │ 使用 Refresh  │ →  │ 获取新 Token  │ →  │ 重试原请求  │
│ Token 过期    │    │ Token 刷新    │    │ 对           │    │ 成功         │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. API 设计

### 3.1 API 总览

| 方法 | 路径 | 描述 | 认证 | 限流 |
|------|------|------|------|------|
| POST | /api/auth/register/ | 用户注册 | 否 | 5 次/分钟/IP |
| POST | /api/auth/login/ | 用户登录 | 否 | 10 次/分钟/IP |
| POST | /api/auth/logout/ | 用户登出 | 是 | - |
| POST | /api/auth/refresh/ | 刷新 Token | 是（Refresh Token） | - |
| GET | /api/auth/profile/ | 获取个人信息 | 是 | - |
| PUT | /api/auth/profile/ | 更新个人信息 | 是 | - |
| POST | /api/auth/change-password/ | 修改密码 | 是 | 3 次/小时 |
| POST | /api/auth/verify-username/ | 验证用户名可用性 | 否 | 10 次/分钟 |
| POST | /api/auth/verify-email/ | 验证邮箱可用性 | 否 | 10 次/分钟 |

---

### 3.2 API 详细设计

#### 3.2.1 用户注册

**请求**：
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "player123",
  "email": "player123@example.com",
  "password": "SecurePass123",
  "nickname": "象棋高手"
}
```

**成功响应**（201 Created）：
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "username": "player123",
    "email": "player123@example.com",
    "nickname": "象棋高手",
    "avatar_url": null,
    "rating": 1200,
    "created_at": "2026-03-03T09:00:00Z",
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 7200
    }
  },
  "message": "注册成功"
}
```

**错误响应**（400 Bad Request）：
```json
{
  "success": false,
  "error": {
    "code": "USERNAME_EXISTS",
    "message": "用户名已存在",
    "details": {
      "field": "username",
      "value": "player123"
    }
  }
}
```

**错误码**：
| 错误码 | HTTP 状态码 | 含义 |
|--------|-----------|------|
| USERNAME_EXISTS | 400 | 用户名已存在 |
| EMAIL_EXISTS | 400 | 邮箱已被注册 |
| WEAK_PASSWORD | 400 | 密码强度不足 |
| INVALID_EMAIL | 400 | 邮箱格式无效 |
| INVALID_USERNAME | 400 | 用户名格式无效（3-20 位字母数字下划线） |

---

#### 3.2.2 用户登录

**请求**：
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "player123",
  "password": "SecurePass123",
  "remember_me": true
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "username": "player123",
    "nickname": "象棋高手",
    "avatar_url": "https://cdn.example.com/avatars/12345.jpg",
    "rating": 1200,
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 7200
    }
  },
  "message": "登录成功"
}
```

**错误响应**（401 Unauthorized）：
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

**错误码**：
| 错误码 | HTTP 状态码 | 含义 |
|--------|-----------|------|
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| USER_BANNED | 403 | 账号已被封禁 |
| USER_INACTIVE | 403 | 账号未激活 |

---

#### 3.2.3 刷新 Token

**请求**：
```http
POST /api/auth/refresh/
Content-Type: application/json
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**成功响应**（200 OK）：
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

**错误响应**（401 Unauthorized）：
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Refresh Token 已过期，请重新登录"
  }
}
```

---

#### 3.2.4 获取个人信息

**请求**：
```http
GET /api/auth/profile/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "username": "player123",
    "email": "player123@example.com",
    "nickname": "象棋高手",
    "avatar_url": "https://cdn.example.com/avatars/12345.jpg",
    "rating": 1200,
    "total_games": 156,
    "wins": 89,
    "losses": 52,
    "draws": 15,
    "win_rate": 57.05,
    "created_at": "2026-03-03T09:00:00Z",
    "last_login": "2026-03-03T12:00:00Z"
  }
}
```

---

#### 3.2.5 更新个人信息

**请求**：
```http
PUT /api/auth/profile/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "nickname": "新的昵称",
  "avatar_url": "https://cdn.example.com/avatars/new.jpg"
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "user_id": 12345,
    "username": "player123",
    "nickname": "新的昵称",
    "avatar_url": "https://cdn.example.com/avatars/new.jpg"
  },
  "message": "个人信息更新成功"
}
```

**错误码**：
| 错误码 | HTTP 状态码 | 含义 |
|--------|-----------|------|
| INVALID_NICKNAME | 400 | 昵称格式无效（1-20 字符） |
| NICKNAME_EXISTS | 409 | 昵称已被使用 |

---

#### 3.2.6 修改密码

**请求**：
```http
POST /api/auth/change-password/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "old_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

**错误码**：
| 错误码 | HTTP 状态码 | 含义 |
|--------|-----------|------|
| WRONG_OLD_PASSWORD | 400 | 旧密码错误 |
| WEAK_PASSWORD | 400 | 新密码强度不足 |
| SAME_PASSWORD | 400 | 新密码与旧密码相同 |

---

## 4. 数据库设计

### 4.1 用户表（users）

```sql
CREATE TABLE users (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    
    -- 基本信息
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    nickname        VARCHAR(50) NOT NULL,
    avatar_url      VARCHAR(500),
    
    -- 游戏数据
    rating          INTEGER DEFAULT 1200 NOT NULL,  -- 天梯分
    total_games     INTEGER DEFAULT 0 NOT NULL,
    wins            INTEGER DEFAULT 0 NOT NULL,
    losses          INTEGER DEFAULT 0 NOT NULL,
    draws           INTEGER DEFAULT 0 NOT NULL,
    
    -- 账号状态
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    is_banned       BOOLEAN DEFAULT FALSE NOT NULL,
    ban_reason      TEXT,
    banned_at       TIMESTAMP,
    banned_by       BIGINT REFERENCES users(id),
    
    -- 时间戳
    last_login      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- 约束
    CONSTRAINT chk_rating CHECK (rating >= 0),
    CONSTRAINT chk_games CHECK (total_games = wins + losses + draws),
    CONSTRAINT chk_username_length CHECK (length(username) BETWEEN 3 AND 50),
    CONSTRAINT chk_nickname_length CHECK (length(nickname) BETWEEN 1 AND 50)
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_rating ON users(rating DESC);
CREATE INDEX idx_users_created ON users(created_at DESC);
CREATE INDEX idx_users_active ON users(id) WHERE is_active = TRUE;
```

---

### 4.2 Token 黑名单表（token_blacklist）

用于存储已登出的 Access Token，防止登出后继续使用。

```sql
CREATE TABLE token_blacklist (
    id              BIGSERIAL PRIMARY KEY,
    token_jti       VARCHAR(255) UNIQUE NOT NULL,  -- JWT ID
    user_id         BIGINT REFERENCES users(id) NOT NULL,
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 索引
CREATE INDEX idx_token_blacklist_jti ON token_blacklist(token_jti);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);

-- 定期清理过期 Token（Celery Beat 任务）
```

---

### 4.3 用户登录日志表（user_login_logs）

记录用户登录历史，用于安全审计。

```sql
CREATE TABLE user_login_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id) NOT NULL,
    login_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address      INET NOT NULL,
    user_agent      TEXT,
    login_status    VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'banned'
    failure_reason  VARCHAR(100)
);

-- 索引
CREATE INDEX idx_login_logs_user ON user_login_logs(user_id, login_time DESC);
CREATE INDEX idx_login_logs_time ON user_login_logs(login_time DESC);
CREATE INDEX idx_login_logs_ip ON user_login_logs(ip_address);
```

---

### 4.4 ER 图

```
┌─────────────────────────┐
│         users           │
├─────────────────────────┤
│ PK  id                  │
│     username            │
│     email               │
│     password_hash       │
│     nickname            │
│     avatar_url          │
│     rating              │
│     total_games         │
│     wins/losses/draws   │
│     is_active           │
│     is_banned           │
│     last_login          │
│     created_at          │
│     updated_at          │
└─────────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────────┐
│    token_blacklist      │
├─────────────────────────┤
│ PK  id                  │
│     token_jti           │
│ FK  user_id             │
│     expires_at          │
│     created_at          │
└─────────────────────────┘

          │
          │ 1:N
          ▼
┌─────────────────────────┐
│   user_login_logs       │
├─────────────────────────┤
│ PK  id                  │
│ FK  user_id             │
│     login_time          │
│     ip_address          │
│     user_agent          │
│     login_status        │
│     failure_reason      │
└─────────────────────────┘
```

---

## 5. 实现步骤（任务分解）

### 5.1 后端实现

#### 5.1.1 数据模型层（Day 1）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-01** | 创建 User 模型（apps/users/models.py） | 2h | - |
| **AUTH-BE-02** | 创建 TokenBlacklist 模型 | 1h | AUTH-BE-01 |
| **AUTH-BE-03** | 创建 UserLoginLog 模型 | 1h | - |
| **AUTH-BE-04** | 编写数据库迁移文件并执行迁移 | 1h | AUTH-BE-01~03 |

**代码结构**：
```python
# apps/users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        # 实现用户创建逻辑
        pass
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        # 实现超级用户创建逻辑
        pass

class User(AbstractBaseUser):
    # 字段定义
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    # ... 其他字段
    
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
```

---

#### 5.1.2 序列化器层（Day 1）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-05** | 创建 UserSerializer（用户数据序列化） | 2h | AUTH-BE-01 |
| **AUTH-BE-06** | 创建 RegisterSerializer（注册数据验证） | 2h | AUTH-BE-05 |
| **AUTH-BE-07** | 创建 LoginSerializer（登录数据验证） | 1h | AUTH-BE-05 |
| **AUTH-BE-08** | 创建 ChangePasswordSerializer | 1h | AUTH-BE-05 |

**代码结构**：
```python
# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'nickname')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "密码不匹配"})
        return attrs
```

---

#### 5.1.3 服务层（Day 2）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-09** | 创建 UserService（用户 CRUD 操作） | 3h | AUTH-BE-01 |
| **AUTH-BE-10** | 创建 AuthService（认证逻辑） | 3h | AUTH-BE-09 |
| **AUTH-BE-11** | 创建 TokenService（JWT Token 管理） | 2h | AUTH-BE-10 |
| **AUTH-BE-12** | 实现密码强度验证函数 | 1h | - |

**代码结构**：
```python
# apps/users/services.py
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import jwt
from datetime import datetime, timedelta

User = get_user_model()

class TokenService:
    @staticmethod
    def generate_tokens(user: User) -> dict:
        """生成 Access Token 和 Refresh Token"""
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=2),
            'type': 'access'
        }
        refresh_payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=7),
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 7200
        }
    
    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> dict:
        """验证 Token 有效性"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != token_type:
                raise jwt.InvalidTokenError('Token 类型不匹配')
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError('Token 已过期')
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f'无效 Token: {str(e)}')
```

---

#### 5.1.4 API 视图层（Day 2-3）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-13** | 创建 RegisterView（用户注册） | 2h | AUTH-BE-06, AUTH-BE-10 |
| **AUTH-BE-14** | 创建 LoginView（用户登录） | 2h | AUTH-BE-07, AUTH-BE-10 |
| **AUTH-BE-15** | 创建 LogoutView（用户登出） | 1h | AUTH-BE-11 |
| **AUTH-BE-16** | 创建 RefreshTokenView（刷新 Token） | 2h | AUTH-BE-11 |
| **AUTH-BE-17** | 创建 ProfileView（获取/更新个人信息） | 2h | AUTH-BE-05 |
| **AUTH-BE-18** | 创建 ChangePasswordView | 1h | AUTH-BE-08 |
| **AUTH-BE-19** | 创建 UsernameVerifyView / EmailVerifyView | 1h | AUTH-BE-01 |

**代码结构**：
```python
# apps/users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .services import AuthService, TokenService

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = AuthService.register_user(serializer.validated_data)
        tokens = TokenService.generate_tokens(user)
        
        return Response({
            'success': True,
            'data': {
                'user_id': user.id,
                'username': user.username,
                'tokens': tokens
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = AuthService.authenticate_user(
            serializer.validated_data['username'],
            serializer.validated_data['password']
        )
        
        if user.is_banned:
            return Response({
                'success': False,
                'error': {'code': 'USER_BANNED', 'message': '账号已被封禁'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        tokens = TokenService.generate_tokens(user)
        AuthService.update_last_login(user, request)
        
        return Response({
            'success': True,
            'data': {
                'user_id': user.id,
                'tokens': tokens
            }
        })
```

---

#### 5.1.5 认证权限类（Day 3）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-20** | 创建 JWTAuthentication 自定义认证类 | 2h | AUTH-BE-11 |
| **AUTH-BE-21** | 创建 IsAuthenticatedOrReadOnly 权限类 | 1h | AUTH-BE-20 |
| **AUTH-BE-22** | 配置 DRF 认证和权限设置 | 1h | AUTH-BE-20 |

---

#### 5.1.6 中间件和限流（Day 3）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-BE-23** | 创建登录限流类（基于 IP） | 2h | - |
| **AUTH-BE-24** | 创建 Token 刷新中间件 | 1h | AUTH-BE-11 |
| **AUTH-BE-25** | 配置 DRF 限流设置 | 1h | AUTH-BE-23 |

---

### 5.2 前端实现

#### 5.2.1 状态管理（Day 4）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-FE-01** | 创建 Auth Store（Zustand） | 2h | - |
| **AUTH-FE-02** | 实现 Token 自动刷新逻辑 | 2h | AUTH-FE-01 |
| **AUTH-FE-03** | 创建 Axios 拦截器（Token 注入） | 1h | AUTH-FE-01 |

**代码结构**：
```typescript
// src/stores/authStore.ts
import { create } from 'zustand'
import { axiosInstance } from '@/services/api'

interface AuthState {
  user: UserInfo | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshTokens: () => Promise<void>
  updateProfile: (data: Partial<UserInfo>) => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  
  login: async (username, password) => {
    const response = await axiosInstance.post('/api/auth/login/', {
      username,
      password,
    })
    
    const { access_token, refresh_token } = response.data.data.tokens
    set({
      accessToken: access_token,
      refreshToken: refresh_token,
      isAuthenticated: true,
    })
    
    // 存储 Refresh Token 到 HttpOnly Cookie
    document.cookie = `refresh_token=${refresh_token}; path=/; max-age=604800; secure; samesite=strict`
  },
  
  logout: async () => {
    await axiosInstance.post('/api/auth/logout/')
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    })
    document.cookie = 'refresh_token=; path=/; max-age=0'
  },
}))
```

---

#### 5.2.2 页面组件（Day 4-5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-FE-04** | 创建注册页面（RegisterPage） | 3h | AUTH-FE-01 |
| **AUTH-FE-05** | 创建登录页面（LoginPage） | 3h | AUTH-FE-01 |
| **AUTH-FE-06** | 创建个人中心页面（ProfilePage） | 3h | AUTH-FE-01 |
| **AUTH-FE-07** | 创建修改密码页面（ChangePasswordPage） | 2h | AUTH-FE-01 |
| **AUTH-FE-08** | 创建头像上传组件（AvatarUploader） | 2h | AUTH-FE-06 |

---

#### 5.2.3 表单验证（Day 5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-FE-09** | 创建注册表单验证（username/email/password） | 2h | AUTH-FE-04 |
| **AUTH-FE-10** | 创建密码强度指示器组件 | 2h | AUTH-FE-09 |
| **AUTH-FE-11** | 创建用户名/邮箱可用性实时校验 | 2h | AUTH-FE-09 |

---

#### 5.2.4 路由保护（Day 5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-FE-12** | 创建 AuthGuard 路由守卫组件 | 2h | AUTH-FE-01 |
| **AUTH-FE-13** | 创建 GuestGuard（已登录用户不可访问登录/注册页） | 1h | AUTH-FE-01 |
| **AUTH-FE-14** | 配置受保护路由 | 1h | AUTH-FE-12 |

**代码结构**：
```typescript
// src/components/AuthGuard.tsx
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface AuthGuardProps {
  children: React.ReactNode
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  return <>{children}</>
}

// 路由配置
const routes = [
  {
    path: '/profile',
    element: (
      <AuthGuard>
        <ProfilePage />
      </AuthGuard>
    ),
  },
  {
    path: '/login',
    element: (
      <GuestGuard>
        <LoginPage />
      </GuestGuard>
    ),
  },
]
```

---

### 5.3 测试实现

#### 5.3.1 后端测试（Day 6）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-TEST-01** | 编写注册 API 单元测试 | 2h | AUTH-BE-13 |
| **AUTH-TEST-02** | 编写登录 API 单元测试 | 2h | AUTH-BE-14 |
| **AUTH-TEST-03** | 编写 Token 刷新测试 | 1h | AUTH-BE-16 |
| **AUTH-TEST-04** | 编写个人信息 API 测试 | 2h | AUTH-BE-17 |
| **AUTH-TEST-05** | 编写密码修改 API 测试 | 1h | AUTH-BE-18 |
| **AUTH-TEST-06** | 编写集成测试（完整认证流程） | 2h | AUTH-TEST-01~05 |

---

#### 5.3.2 前端测试（Day 6）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AUTH-TEST-07** | 编写登录表单组件测试 | 2h | AUTH-FE-05 |
| **AUTH-TEST-08** | 编写注册表单组件测试 | 2h | AUTH-FE-04 |
| **AUTH-TEST-09** | 编写 AuthGuard 路由守卫测试 | 1h | AUTH-FE-12 |

---

### 5.4 任务时间线

```
Week 1:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│BE-01 │BE-09 │BE-13 │BE-20 │FE-01 │TEST-1│ 休息 │
│BE-04 │BE-12 │BE-19 │BE-25 │FE-03 │TEST-6│      │
│      │      │      │      │      │      │      │
│BE-05 │BE-10 │BE-14 │FE-04 │FE-06 │TEST-7│      │
│BE-08 │BE-11 │BE-18 │FE-08 │FE-11 │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 2:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│FE-02 │FE-05 │FE-07 │FE-12 │TEST-2│ 联调 │ 休息 │
│      │      │      │      │TEST-4│ 测试 │      │
│      │      │      │      │      │      │      │
│      │      │      │      │TEST-5│      │      │
│      │      │      │      │TEST-8│      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

**总工时预估**：约 60 小时（1.5 周）

---

## 6. 测试计划

### 6.1 单元测试

#### 6.1.1 后端单元测试

| 测试模块 | 测试用例 | 预期结果 |
|---------|---------|---------|
| **TokenService** | 生成 Token | 返回有效的 JWT Token |
| **TokenService** | 验证有效 Token | 返回解析后的 payload |
| **TokenService** | 验证过期 Token | 抛出 ExpiredSignatureError |
| **TokenService** | 验证伪造 Token | 抛出 InvalidTokenError |
| **UserService** | 创建用户 | 用户成功创建，密码已加密 |
| **UserService** | 创建重复用户名 | 抛出 IntegrityError |
| **UserService** | 更新用户信息 | 用户信息成功更新 |
| **AuthService** | 认证成功 | 返回用户对象 |
| **AuthService** | 认证失败（错误密码） | 返回 None |
| **AuthService** | 认证失败（账号封禁） | 抛出 UserBannedError |

**测试代码示例**：
```python
# apps/users/tests/test_services.py
import pytest
from django.contrib.auth import get_user_model
from apps.users.services import TokenService, AuthService
from rest_framework.exceptions import ValidationError

User = get_user_model()

@pytest.mark.django_db
class TestTokenService:
    def test_generate_tokens(self, user):
        tokens = TokenService.generate_tokens(user)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['expires_in'] == 7200
        
        # 验证 Token 可解析
        payload = TokenService.verify_token(tokens['access_token'])
        assert payload['user_id'] == user.id
    
    def test_verify_expired_token(self):
        expired_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9...'
        
        with pytest.raises(jwt.InvalidTokenError, match='Token 已过期'):
            TokenService.verify_token(expired_token)

@pytest.mark.django_db
class TestAuthService:
    def test_register_user(self):
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123',
            'nickname': '测试用户'
        }
        
        user = AuthService.register_user(user_data)
        
        assert user.username == user_data['username']
        assert user.email == user_data['email']
        assert user.check_password(user_data['password'])
    
    def test_register_duplicate_username(self, user):
        user_data = {
            'username': user.username,
            'email': 'other@example.com',
            'password': 'SecurePass123',
            'nickname': '测试用户'
        }
        
        with pytest.raises(ValidationError):
            AuthService.register_user(user_data)
```

---

### 6.2 集成测试

#### 6.2.1 API 集成测试

| 测试场景 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| **完整注册登录流程** | 1. 注册新用户<br>2. 使用凭证登录<br>3. 获取个人信息<br>4. 修改个人信息<br>5. 修改密码<br>6. 使用新密码登录 | 所有步骤成功 |
| **Token 刷新流程** | 1. 登录获取 Token<br>2. 等待 Access Token 过期<br>3. 调用刷新接口<br>4. 使用新 Token 访问 API | 刷新成功，API 访问正常 |
| **登出流程** | 1. 登录<br>2. 登出<br>3. 使用旧 Token 访问 API<br>4. Token 应失效 | 登出后 Token 失效 |
| **账号封禁流程** | 1. 管理员封禁用户<br>2. 用户尝试登录<br>3. 应返回 USER_BANNED 错误 | 登录失败，提示封禁 |

**测试代码示例**：
```python
# apps/users/tests/test_integration.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
class TestAuthIntegration:
    def test_full_registration_login_flow(self):
        client = APIClient()
        
        # 1. 注册
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
            'nickname': '新用户'
        }
        response = client.post(reverse('auth:register'), register_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        access_token = response.data['data']['tokens']['access_token']
        
        # 2. 获取个人信息
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = client.get(reverse('auth:profile'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'newuser'
        
        # 3. 更新个人信息
        response = client.patch(reverse('auth:profile'), {
            'nickname': '新昵称'
        })
        assert response.status_code == status.HTTP_200_OK
        
        # 4. 修改密码
        response = client.post(reverse('auth:change-password'), {
            'old_password': 'SecurePass123',
            'new_password': 'NewSecurePass456'
        })
        assert response.status_code == status.HTTP_200_OK
        
        # 5. 使用新密码登录
        login_response = client.post(reverse('auth:login'), {
            'username': 'newuser',
            'password': 'NewSecurePass456'
        })
        assert login_response.status_code == status.HTTP_200_OK
```

---

### 6.3 前端 E2E 测试

| 测试场景 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| **注册流程 E2E** | 1. 访问注册页<br>2. 填写表单<br>3. 提交<br>4. 验证跳转到登录页 | 注册成功，跳转正确 |
| **登录流程 E2E** | 1. 访问登录页<br>2. 输入凭证<br>3. 提交<br>4. 验证跳转到大厅 | 登录成功，跳转正确 |
| **Token 过期处理 E2E** | 1. 登录<br>2. 模拟 Token 过期<br>3. 访问受保护页面<br>4. 验证自动刷新 | 无感知刷新，页面正常加载 |
| **路由守卫 E2E** | 1. 未登录状态<br>2. 访问受保护页面<br>3. 验证重定向到登录页 | 重定向正确 |

**测试代码示例**（Playwright）：
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('用户认证流程', () => {
  test('完整注册登录流程', async ({ page }) => {
    // 1. 注册
    await page.goto('/register')
    await page.fill('[name="username"]', 'e2etest')
    await page.fill('[name="email"]', 'e2etest@example.com')
    await page.fill('[name="password"]', 'SecurePass123')
    await page.fill('[name="password_confirm"]', 'SecurePass123')
    await page.fill('[name="nickname"]', 'E2E 测试用户')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/login')
    
    // 2. 登录
    await page.fill('[name="username"]', 'e2etest')
    await page.fill('[name="password"]', 'SecurePass123')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/lobby')
    
    // 3. 验证个人信息
    await page.click('[data-testid="profile-link"]')
    await expect(page.locator('[data-testid="username"]')).toHaveText('e2etest')
  })
})
```

---

### 6.4 性能测试

| 测试项目 | 目标值 | 测试工具 |
|---------|-------|---------|
| **登录 API 响应时间** | P95 < 200ms | Locust |
| **注册 API 响应时间** | P95 < 300ms | Locust |
| **Token 刷新响应时间** | P95 < 100ms | Locust |
| **并发登录能力** | 100 用户/秒 | Locust |
| **密码加密耗时** | < 100ms | pytest-benchmark |

---

## 7. 验收标准

### 7.1 功能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **AC-01** | 用户可以成功注册 | 执行注册流程 | 返回 201，用户数据入库 |
| **AC-02** | 用户名/邮箱唯一性 | 尝试注册重复用户名/邮箱 | 返回 400，提示已存在 |
| **AC-03** | 密码强度验证 | 尝试使用弱密码注册 | 返回 400，提示强度不足 |
| **AC-04** | 用户可以成功登录 | 使用正确凭证登录 | 返回 200，颁发 Token |
| **AC-05** | 错误凭证登录失败 | 使用错误密码登录 | 返回 401，提示凭证错误 |
| **AC-06** | Token 认证有效 | 使用有效 Token 访问 API | 返回 200，数据正常 |
| **AC-07** | Token 过期处理 | 使用过期 Token 访问 API | 返回 401，提示过期 |
| **AC-08** | Token 刷新成功 | 调用刷新接口 | 返回 200，新 Token 有效 |
| **AC-09** | 个人信息可查询 | 调用获取个人信息接口 | 返回完整用户数据 |
| **AC-10** | 个人信息可更新 | 调用更新接口 | 返回 200，数据已更新 |
| **AC-11** | 密码可修改 | 调用修改密码接口 | 返回 200，新密码生效 |
| **AC-12** | 旧密码验证 | 使用错误旧密码修改 | 返回 400，提示错误 |
| **AC-13** | 登出后 Token 失效 | 登出后使用旧 Token 访问 | 返回 401 |
| **AC-14** | 封禁用户无法登录 | 封禁用户尝试登录 | 返回 403，提示封禁 |

---

### 7.2 安全验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **SEC-01** | 密码加密存储 | 检查数据库 | 密码为 bcrypt 哈希，非明文 |
| **SEC-02** | SQL 注入防护 | 尝试注入攻击 | 请求被拦截，无数据泄露 |
| **SEC-03** | XSS 防护 | 尝试注入脚本 | 输入被转义，脚本不执行 |
| **SEC-04** | CSRF 防护 | 尝试跨站请求 | 请求被拒绝 |
| **SEC-05** | 限流生效 | 高频请求登录接口 | 触发限流，返回 429 |
| **SEC-06** | Token 安全存储 | 检查前端存储 | Refresh Token 在 HttpOnly Cookie |
| **SEC-07** | HTTPS 强制 | HTTP 请求重定向 | 自动跳转到 HTTPS |
| **SEC-08** | 密码不泄露 | 错误响应检查 | 错误信息不包含敏感数据 |

---

### 7.3 性能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **PERF-01** | 登录响应时间 | Locust 压测 | P95 < 200ms |
| **PERF-02** | 注册响应时间 | Locust 压测 | P95 < 300ms |
| **PERF-03** | Token 刷新时间 | Locust 压测 | P95 < 100ms |
| **PERF-04** | 并发登录能力 | Locust 压测 | 支持 100 用户/秒 |
| **PERF-05** | 数据库查询性能 | EXPLAIN 分析 | 关键查询使用索引 |

---

### 7.4 兼容性验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **COMP-01** | Chrome 浏览器 | 手动测试 | 功能正常 |
| **COMP-02** | Firefox 浏览器 | 手动测试 | 功能正常 |
| **COMP-03** | Safari 浏览器 | 手动测试 | 功能正常 |
| **COMP-04** | Edge 浏览器 | 手动测试 | 功能正常 |
| **COMP-05** | 移动端响应式 | 手动测试 | 布局正常，操作流畅 |

---

## 8. 风险与应对

| 风险 ID | 风险描述 | 可能性 | 影响 | 应对措施 |
|--------|---------|--------|------|---------|
| **AUTH-RISK-01** | JWT Secret 泄露 | 低 | 高 | 使用环境变量存储，定期轮换 |
| **AUTH-RISK-02** | Token 被截获 | 中 | 高 | 强制 HTTPS，Token 短期有效 |
| **AUTH-RISK-03** | 暴力破解密码 | 中 | 中 | 登录限流，密码强度要求 |
| **AUTH-RISK-04** | 彩虹表攻击 | 低 | 中 | 使用 bcrypt+salt，不可逆加密 |
| **AUTH-RISK-05** | Session 固定攻击 | 低 | 中 | 登录后生成新 Token |
| **AUTH-RISK-06** | 用户枚举攻击 | 中 | 低 | 统一错误提示（不区分用户名/密码错误） |

---

## 9. 后续扩展（P1/P2）

### 9.1 P1 功能

- **邮箱验证**：注册后发送验证邮件
- **密码找回**：通过邮箱重置密码
- **记住登录状态**：长期 Token（30 天）
- **登录设备管理**：查看和管理登录设备

### 9.2 P2 功能

- **第三方登录**：微信、QQ、Google 登录
- **双因素认证**：短信/邮箱验证码
- **账号注销**：用户申请注销账号
- **登录通知**：新设备登录时邮件通知

---

## 附录

### A. 环境变量配置

```bash
# .env
# JWT 配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_LIFETIME_HOURS=2
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ALGORITHM=HS256

# 密码配置
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGIT=true
PASSWORD_REQUIRE_SPECIAL=false

# 限流配置
LOGIN_RATE_LIMIT=10/minute
REGISTER_RATE_LIMIT=5/minute
```

---

### B. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | planner agent | 初始版本，完成用户认证系统规划 |

---

**用户认证系统规划完成！** ✅

下一步：规划游戏对局系统（game-core-plan.md）
