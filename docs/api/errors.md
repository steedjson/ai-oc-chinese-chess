# API 错误码说明

**版本**: 1.0.0  
**最后更新**: 2026-03-06

---

## 概述

本 API 使用统一的错误响应格式，所有错误响应都包含以下结构：

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

---

## HTTP 状态码

### 成功状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 OK | 请求成功 | GET、PUT、PATCH 成功 |
| 201 Created | 创建成功 | POST 创建资源 |
| 204 No Content | 删除成功 | DELETE 成功（无内容返回） |

### 客户端错误状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 400 Bad Request | 请求参数错误 | 参数验证失败、JSON 格式错误 |
| 401 Unauthorized | 未认证 | Token 缺失、Token 过期 |
| 403 Forbidden | 无权限 | 权限不足、账号被封禁 |
| 404 Not Found | 资源不存在 | 用户、对局等资源不存在 |
| 409 Conflict | 资源冲突 | 用户名重复、邮箱重复 |
| 422 Unprocessable Entity | 请求语义错误 | 业务逻辑验证失败 |
| 429 Too Many Requests | 请求过于频繁 | 触发速率限制 |

### 服务端错误状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 500 Internal Server Error | 服务器内部错误 | 未处理的异常 |
| 502 Bad Gateway | 网关错误 | 上游服务不可用 |
| 503 Service Unavailable | 服务不可用 | 维护中、过载 |
| 504 Gateway Timeout | 网关超时 | 上游服务超时 |

---

## 错误码分类

### 1. 认证相关错误 (AUTH)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 | 检查凭证后重试 |
| `TOKEN_REQUIRED` | 400 | 缺少 Token | 在请求头中添加 Authorization |
| `TOKEN_INVALID` | 401 | Token 无效或已过期 | 刷新 Token 或重新登录 |
| `TOKEN_EXPIRED` | 401 | Token 已过期 | 使用 Refresh Token 刷新 |
| `USER_BANNED` | 403 | 账号已被封禁 | 联系客服申诉 |
| `USER_INACTIVE` | 403 | 账号已被禁用 | 检查邮箱验证状态 |
| `AUTH_FAILED` | 401 | 认证失败（WebSocket） | 检查 Token 有效性 |
| `AUTH_FORBIDDEN` | 403 | 无权访问此资源 | 检查用户权限 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 2. 验证相关错误 (VALIDATION)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `VALIDATION_ERROR` | 400 | 参数验证失败 | 检查请求参数格式 |
| `MISSING_FIELD` | 400 | 缺少必填字段 | 补充缺失字段 |
| `INVALID_FORMAT` | 400 | 字段格式错误 | 检查字段格式要求 |
| `INVALID_LENGTH` | 400 | 字段长度不符合要求 | 调整字段长度 |
| `INVALID_RANGE` | 400 | 字段值超出范围 | 检查有效范围 |
| `INVALID_CHOICE` | 400 | 字段值不在选项中 | 选择有效值 |
| `WRONG_OLD_PASSWORD` | 400 | 旧密码错误 | 检查旧密码 |
| `SAME_PASSWORD` | 400 | 新密码不能与旧密码相同 | 使用不同的密码 |
| `PASSWORD_TOO_WEAK` | 400 | 密码强度不足 | 使用更复杂的密码 |
| `INVALID_JSON` | 400 | JSON 格式无效 | 检查 JSON 语法 |
| `INVALID_MOVE` | 400 | 无效走棋 | 检查走棋规则 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": {
      "username": ["用户名长度必须在 3-50 字符之间"],
      "email": ["请输入有效的邮箱地址"]
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 3. 用户相关错误 (USER)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `USER_NOT_FOUND` | 404 | 用户不存在 | 检查用户 ID |
| `USERNAME_TAKEN` | 409 | 用户名已被使用 | 更换用户名 |
| `EMAIL_REGISTERED` | 409 | 邮箱已被注册 | 更换邮箱或使用其他账号 |
| `PERMISSION_DENIED` | 403 | 无权限执行此操作 | 检查用户权限 |
| `USER_NOT_AUTHORIZED` | 403 | 用户未授权 | 联系管理员授权 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 4. 游戏相关错误 (GAME)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `GAME_NOT_FOUND` | 404 | 对局不存在 | 检查对局 ID |
| `GAME_NOT_PLAYING` | 400 | 游戏未进行中 | 检查游戏状态 |
| `GAME_ALREADY_FINISHED` | 400 | 游戏已结束 | 无法对已结束的游戏进行操作 |
| `NOT_YOUR_TURN` | 400 | 不是你的回合 | 等待对手走棋 |
| `NO_PIECE` | 400 | 起始位置没有棋子 | 检查棋子位置 |
| `INVALID_MOVE` | 400 | 无效走棋 | 检查走棋规则，参考 legal_moves |
| `MOVE_ERROR` | 500 | 走棋处理错误 | 联系技术支持 |
| `INVALID_STATUS` | 400 | 无效的游戏状态 | 检查有效状态值 |
| `GAME_NOT_ACCESSIBLE` | 403 | 无权访问此对局 | 检查对局参与权限 |
| `SPECTATOR_NOT_ALLOWED` | 403 | 不允许观战 | 检查观战权限 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_MOVE",
    "message": "无效走棋",
    "details": {
      "legal_moves": ["e4", "f4", "g4"]
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 5. AI 引擎相关错误 (AI)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `AI_ERROR` | 500 | AI 走棋失败 | 重试或联系技术支持 |
| `INVALID_DIFFICULTY` | 400 | 难度等级无效 | 使用 1-10 之间的值 |
| `STATUS_ERROR` | 500 | 获取引擎状态失败 | 检查引擎服务状态 |
| `ENGINE_UNAVAILABLE` | 503 | AI 引擎不可用 | 稍后重试 |
| `TIMEOUT` | 504 | AI 计算超时 | 降低难度或重试 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_DIFFICULTY",
    "message": "难度等级必须在 1-10 之间"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 6. 匹配系统相关错误 (MATCHMAKING)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `QUEUE_JOIN_FAILED` | 400 | 加入队列失败 | 检查是否已在队列中 |
| `QUEUE_JOIN_ERROR` | 500 | 加入队列时发生错误 | 重试或联系技术支持 |
| `QUEUE_LEAVE_FAILED` | 400 | 退出队列失败 | 检查是否已在队列外 |
| `QUEUE_LEAVE_ERROR` | 500 | 退出队列时发生错误 | 重试或联系技术支持 |
| `ALREADY_IN_QUEUE` | 400 | 已在匹配队列中 | 先退出队列 |
| `NOT_IN_QUEUE` | 400 | 不在匹配队列中 | 先加入队列 |
| `MATCH_NOT_FOUND` | 404 | 匹配对局不存在 | 重新匹配 |
| `MATCH_DECLINED` | 400 | 匹配被拒绝 | 等待下一次匹配 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_IN_QUEUE",
    "message": "您已在匹配队列中"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 7. 每日挑战相关错误 (CHALLENGE)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `NO_CHALLENGE` | 404 | 今日挑战尚未发布 | 等待挑战发布 |
| `ALREADY_ATTEMPTED` | 400 | 今日已尝试过 | 明日再来 |
| `MISSING_ATTEMPT_ID` | 400 | 缺少尝试 ID | 检查请求参数 |
| `ATTEMPT_NOT_FOUND` | 404 | 尝试记录不存在 | 检查尝试 ID |
| `ATTEMPT_COMPLETED` | 400 | 挑战已完成 | 无法重复提交 |
| `INVALID_DATE` | 400 | 日期格式错误 | 使用 YYYY-MM-DD 格式 |
| `GENERATION_ERROR` | 500 | 生成挑战失败 | 联系技术支持 |
| `CHALLENGE_EXISTS` | 400 | 挑战已存在 | 无需重复生成 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_ATTEMPTED",
    "message": "您今日已经尝试过挑战"
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 8. WebSocket 相关错误 (WEBSOCKET)

| 错误码 | 说明 | 关闭代码 |
|--------|------|----------|
| `CONNECTION_ERROR` | 连接错误 | 1006 |
| `INVALID_MESSAGE_TYPE` | 未知消息类型 | 4000 |
| `INTERNAL_ERROR` | 内部服务器错误 | 1011 |
| `AUTH_FAILED` | 认证失败 | 4001 |
| `AUTH_FORBIDDEN` | 无权访问 | 4003 |
| `GAME_NOT_FOUND` | 对局不存在 | 4004 |
| `RATE_LIMITED` | 请求过于频繁 | 4029 |

**WebSocket 关闭代码说明**:

| 代码范围 | 说明 |
|----------|------|
| 1000-1999 | 标准 WebSocket 关闭代码 |
| 4000-4999 | 自定义应用关闭代码 |

**示例**:
```json
{
  "type": "error",
  "data": {
    "code": "AUTH_FAILED",
    "message": "Token 无效或已过期"
  }
}
```

---

### 9. 服务器错误 (SERVER)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `INTERNAL_SERVER_ERROR` | 500 | 服务器内部错误 | 联系技术支持 |
| `PASSWORD_CHANGE_FAILED` | 400 | 密码修改失败 | 检查密码要求 |
| `DATABASE_ERROR` | 500 | 数据库错误 | 联系技术支持 |
| `CACHE_ERROR` | 500 | 缓存服务错误 | 联系技术支持 |
| `EXTERNAL_SERVICE_ERROR` | 502 | 外部服务错误 | 稍后重试 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂时不可用 | 稍后重试 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "服务器内部错误，请稍后重试",
    "details": {
      "error_id": "ERR-20260306-001"
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

---

### 10. 速率限制错误 (RATE_LIMIT)

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| `RATE_LIMIT_EXCEEDED` | 429 | 请求过于频繁 | 等待后重试 |
| `QUOTA_EXCEEDED` | 429 | 配额已用尽 | 升级套餐或等待重置 |

**示例**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "details": {
      "retry_after": 60,
      "limit": 60,
      "window": "1m"
    }
  },
  "timestamp": "2026-03-06T09:00:00Z"
}
```

**响应头**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1709689260
Retry-After: 60
```

---

## 错误处理最佳实践

### 客户端错误处理

```javascript
// JavaScript 示例
async function apiCall(endpoint, options) {
  try {
    const response = await fetch(endpoint, options);
    const data = await response.json();
    
    if (!response.ok) {
      // 处理错误
      switch (data.error.code) {
        case 'TOKEN_EXPIRED':
          // 刷新 Token
          await refresh_token();
          return apiCall(endpoint, options);
        case 'RATE_LIMIT_EXCEEDED':
          // 等待后重试
          const retryAfter = data.error.details.retry_after;
          await sleep(retryAfter * 1000);
          return apiCall(endpoint, options);
        case 'INVALID_CREDENTIALS':
          // 提示用户重新登录
          showLoginPrompt();
          break;
        default:
          // 显示错误消息
          showError(data.error.message);
      }
      throw new Error(data.error.message);
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

### Python 示例

```python
import requests
from requests.exceptions import HTTPError

def api_call(endpoint, **kwargs):
    try:
        response = requests.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        error_data = e.response.json()
        error_code = error_data.get('error', {}).get('code')
        
        if error_code == 'TOKEN_EXPIRED':
            # 刷新 Token
            refresh_token()
            return api_call(endpoint, **kwargs)
        elif error_code == 'RATE_LIMIT_EXCEEDED':
            # 等待后重试
            retry_after = error_data.get('error', {}).get('details', {}).get('retry_after', 60)
            time.sleep(retry_after)
            return api_call(endpoint, **kwargs)
        else:
            # 抛出异常
            raise Exception(f"API Error: {error_code} - {error_data['error']['message']}")
```

---

## 错误码快速索引

### 按字母顺序

| 错误码 | 分类 | HTTP 状态码 |
|--------|------|-------------|
| `ALREADY_ATTEMPTED` | CHALLENGE | 400 |
| `ALREADY_IN_QUEUE` | MATCHMAKING | 400 |
| `AUTH_FAILED` | AUTH / WEBSOCKET | 401 |
| `AUTH_FORBIDDEN` | AUTH / WEBSOCKET | 403 |
| `CHALLENGE_EXISTS` | CHALLENGE | 400 |
| `DATABASE_ERROR` | SERVER | 500 |
| `EMAIL_REGISTERED` | USER | 409 |
| `EXTERNAL_SERVICE_ERROR` | SERVER | 502 |
| `GAME_ALREADY_FINISHED` | GAME | 400 |
| `GAME_NOT_ACCESSIBLE` | GAME | 403 |
| `GAME_NOT_FOUND` | GAME / WEBSOCKET | 404 |
| `GAME_NOT_PLAYING` | GAME | 400 |
| `GENERATION_ERROR` | CHALLENGE | 500 |
| `INTERNAL_SERVER_ERROR` | SERVER | 500 |
| `INVALID_CREDENTIALS` | AUTH | 401 |
| `INVALID_DATE` | CHALLENGE | 400 |
| `INVALID_DIFFICULTY` | AI | 400 |
| `INVALID_FORMAT` | VALIDATION | 400 |
| `INVALID_JSON` | VALIDATION | 400 |
| `INVALID_LENGTH` | VALIDATION | 400 |
| `INVALID_MOVE` | VALIDATION / GAME | 400 |
| `INVALID_STATUS` | GAME | 400 |
| `MATCH_DECLINED` | MATCHMAKING | 400 |
| `MATCH_NOT_FOUND` | MATCHMAKING | 404 |
| `MISSING_ATTEMPT_ID` | CHALLENGE | 400 |
| `MISSING_FIELD` | VALIDATION | 400 |
| `MOVE_ERROR` | GAME | 500 |
| `NO_CHALLENGE` | CHALLENGE | 404 |
| `NO_PIECE` | GAME | 400 |
| `NOT_IN_QUEUE` | MATCHMAKING | 400 |
| `NOT_YOUR_TURN` | GAME | 400 |
| `PASSWORD_TOO_WEAK` | VALIDATION | 400 |
| `PERMISSION_DENIED` | USER | 403 |
| `QUOTA_EXCEEDED` | RATE_LIMIT | 429 |
| `QUEUE_JOIN_ERROR` | MATCHMAKING | 500 |
| `QUEUE_JOIN_FAILED` | MATCHMAKING | 400 |
| `QUEUE_LEAVE_ERROR` | MATCHMAKING | 500 |
| `QUEUE_LEAVE_FAILED` | MATCHMAKING | 400 |
| `RATE_LIMIT_EXCEEDED` | RATE_LIMIT | 429 |
| `SAME_PASSWORD` | VALIDATION | 400 |
| `SERVICE_UNAVAILABLE` | SERVER | 503 |
| `SPECTATOR_NOT_ALLOWED` | GAME | 403 |
| `STATUS_ERROR` | AI | 500 |
| `TIMEOUT` | AI | 504 |
| `TOKEN_EXPIRED` | AUTH | 401 |
| `TOKEN_INVALID` | AUTH | 401 |
| `TOKEN_REQUIRED` | AUTH | 400 |
| `USER_BANNED` | AUTH | 403 |
| `USER_INACTIVE` | AUTH | 403 |
| `USER_NOT_AUTHORIZED` | USER | 403 |
| `USER_NOT_FOUND` | USER | 404 |
| `USERNAME_TAKEN` | USER | 409 |
| `VALIDATION_ERROR` | VALIDATION | 400 |
| `WRONG_OLD_PASSWORD` | VALIDATION | 400 |

---

## 相关文件

- **主 API 参考**: [API-REFERENCE.md](./API-REFERENCE.md)
- **端点文档**: [endpoints/](./endpoints/)

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06
