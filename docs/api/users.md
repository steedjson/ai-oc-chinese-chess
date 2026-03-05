# 用户管理 API

## 基础路径
```
/api/v1/users/
```

---

## 端点列表

### 1. 获取用户详情

**GET** `/{user_id}/`

获取指定用户的详细信息。

#### 认证
- **类型**: JWT Bearer Token
- **权限**: 已认证用户（只能查看自己的信息，管理员可查看所有）

#### 路径参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_master",
    "email": "master@example.com",
    "first_name": "",
    "last_name": "",
    "avatar_url": null,
    "elo_rating": 1500,
    "status": "active",
    "is_verified": false,
    "profile": {
      "bio": "象棋爱好者",
      "location": "北京",
      "birthday": null,
      "gender": "male"
    },
    "stats": {
      "total_games": 100,
      "wins": 60,
      "losses": 30,
      "draws": 10,
      "win_rate": "60.00%",
      "favorite_opening": "中炮开局"
    },
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-03-20T14:22:00Z"
  }
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在"
  },
  "timestamp": "2024-03-20T14:22:00Z"
}
```

---

### 2. 更新用户信息（全量更新）

**PUT** `/{user_id}/`

使用 PUT 方法全量更新用户信息。

#### 认证
- **类型**: JWT Bearer Token
- **权限**: 只能更新自己的信息（管理员除外）

#### 路径参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 请求体
```json
{
  "username": "new_username",
  "email": "new_email@example.com",
  "first_name": "张",
  "last_name": "三",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

#### 字段说明
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 否 | 用户名（3-50字符） |
| email | string | 否 | 邮箱地址 |
| first_name | string | 否 | 名 |
| last_name | string | 否 | 姓 |
| avatar_url | string | 否 | 头像URL |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "new_username",
    "email": "new_email@example.com",
    "first_name": "张",
    "last_name": "三",
    "avatar_url": "https://example.com/avatar.jpg",
    "elo_rating": 1500,
    "status": "active",
    "is_verified": false,
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-03-20T14:25:00Z"
  },
  "message": "用户信息更新成功"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "无权修改其他用户信息"
  },
  "timestamp": "2024-03-20T14:22:00Z"
}
```

---

### 3. 更新用户信息（部分更新）

**PATCH** `/{user_id}/`

使用 PATCH 方法部分更新用户信息，只更新提供的字段。

#### 认证
- **类型**: JWT Bearer Token
- **权限**: 只能更新自己的信息（管理员除外）

#### 路径参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 请求体
```json
{
  "first_name": "李",
  "avatar_url": "https://example.com/new_avatar.jpg"
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "chess_master",
    "email": "master@example.com",
    "first_name": "李",
    "last_name": "",
    "avatar_url": "https://example.com/new_avatar.jpg",
    "elo_rating": 1500,
    "status": "active",
    "is_verified": false,
    "created_at": "2024-01-15T08:30:00Z",
    "updated_at": "2024-03-20T14:30:00Z"
  },
  "message": "用户信息更新成功"
}
```

---

### 4. 修改密码

**PUT** `/{user_id}/password/`

修改用户密码。

#### 认证
- **类型**: JWT Bearer Token
- **权限**: 只能修改自己的密码（管理员除外）

#### 路径参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 请求体
```json
{
  "old_password": "current_password123",
  "new_password": "new_secure_password456",
  "new_password_confirm": "new_secure_password456"
}
```

#### 字段说明
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码（需符合密码强度要求） |
| new_password_confirm | string | 是 | 确认新密码 |

#### 响应示例
```json
{
  "success": true,
  "message": "密码修改成功，请重新登录"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "WRONG_OLD_PASSWORD",
    "message": "旧密码错误"
  },
  "timestamp": "2024-03-20T14:22:00Z"
}
```

```json
{
  "success": false,
  "error": {
    "code": "SAME_PASSWORD",
    "message": "新密码不能与旧密码相同"
  },
  "timestamp": "2024-03-20T14:22:00Z"
}
```

---

## 数据模型

### UserSerializer

| 字段 | 类型 | 描述 |
|------|------|------|
| id | UUID | 用户唯一标识 |
| username | string | 用户名 |
| email | string | 邮箱地址 |
| first_name | string | 名 |
| last_name | string | 姓 |
| avatar_url | string/null | 头像URL |
| elo_rating | integer | Elo等级分（只读） |
| status | string | 账户状态：active/banned/suspended（只读） |
| is_verified | boolean | 是否验证（只读） |
| created_at | datetime | 创建时间（只读） |
| updated_at | datetime | 更新时间（只读） |

### UserProfileSerializer

| 字段 | 类型 | 描述 |
|------|------|------|
| bio | string | 个人简介 |
| location | string | 所在地 |
| birthday | date/null | 生日 |
| gender | string | 性别：male/female/other |

### UserStatsSerializer

| 字段 | 类型 | 描述 |
|------|------|------|
| total_games | integer | 总对局数 |
| wins | integer | 胜场数 |
| losses | integer | 负场数 |
| draws | integer | 平局数 |
| win_rate | string | 胜率百分比 |
| favorite_opening | string | 最常用开局 |

---

## 错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| USER_NOT_FOUND | 404 | 用户不存在 |
| PERMISSION_DENIED | 403 | 无权执行此操作 |
| WRONG_OLD_PASSWORD | 400 | 旧密码错误 |
| SAME_PASSWORD | 400 | 新密码与旧密码相同 |
| VALIDATION_ERROR | 400 | 参数验证失败 |
