# 错误码说明

## 概述

系统使用统一的错误响应格式，所有错误响应都包含以下结构：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 错误码分类

### 1. 认证相关错误 (1xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `TOKEN_REQUIRED` | 400 | 缺少 Token |
| `TOKEN_INVALID` | 401 | Token 无效或已过期 |
| `USER_BANNED` | 403 | 账号已被封禁 |
| `USER_INACTIVE` | 403 | 账号已被禁用 |
| `AUTH_FAILED` | 401 | 认证失败（WebSocket） |
| `AUTH_FORBIDDEN` | 403 | 无权访问此资源（WebSocket） |

### 2. 验证相关错误 (2xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `WRONG_OLD_PASSWORD` | 400 | 旧密码错误 |
| `SAME_PASSWORD` | 400 | 新密码不能与旧密码相同 |
| `INVALID_JSON` | 400 | JSON 格式无效（WebSocket） |
| `INVALID_MOVE` | 400 | 无效走棋 |

### 3. 用户相关错误 (3xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `PERMISSION_DENIED` | 403 | 无权限执行此操作 |

### 4. 游戏相关错误 (4xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 |
| `GAME_NOT_PLAYING` | 400 | 游戏未进行中 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 |
| `NO_PIECE` | 400 | 起始位置没有棋子 |
| `MOVE_ERROR` | 500 | 走棋处理错误 |
| `INVALID_STATUS` | 400 | 无效的游戏状态 |

### 5. AI 引擎相关错误 (5xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `AI_ERROR` | 500 | AI 走棋失败 |
| `INVALID_DIFFICULTY` | 400 | 难度等级无效（必须在 1-10 之间） |
| `STATUS_ERROR` | 500 | 获取引擎状态失败 |

### 6. 匹配系统相关错误 (6xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `QUEUE_JOIN_FAILED` | 400 | 加入队列失败 |
| `QUEUE_JOIN_ERROR` | 500 | 加入队列时发生错误 |
| `QUEUE_LEAVE_FAILED` | 400 | 退出队列失败 |
| `QUEUE_LEAVE_ERROR` | 500 | 退出队列时发生错误 |

### 7. WebSocket 相关错误 (7xxx)

| 错误码 | 说明 |
|--------|------|
| `CONNECTION_ERROR` | 连接错误 |
| `INVALID_MESSAGE_TYPE` | 未知消息类型 |
| `INTERNAL_ERROR` | 内部服务器错误 |

### 8. 服务器错误 (9xxx)

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 |
| `PASSWORD_CHANGE_FAILED` | 400 | 密码修改失败 |

## HTTP 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容返回） |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## WebSocket 关闭代码

| 代码 | 说明 |
|------|------|
| 4001 | 认证失败（Token 无效或过期） |
| 4003 | 无权访问此资源 |
