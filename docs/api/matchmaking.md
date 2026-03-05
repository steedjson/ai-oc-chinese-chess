# 匹配系统 API

## 基础路径
```
/api/v1/matchmaking/
```

---

## REST API 端点

### 开始匹配

**POST** `/api/v1/matchmaking/start/`

加入匹配队列，寻找对手。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |
| Content-Type | application/json |

#### 请求体
```json
{
  "game_type": "ranked"  // 可选，默认为 "ranked" (ranked/casual)
}
```

#### 响应

**成功 (200 OK)**
```json
{
  "success": true,
  "message": "加入匹配队列成功",
  "game_type": "ranked",
  "queue_position": 5,
  "estimated_wait_time": 30
}
```

**失败 (400 Bad Request)**
```json
{
  "success": false,
  "error": "已在队列中或加入失败"
}
```

**失败 (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "服务器错误信息"
}
```

---

### 取消匹配

**POST** `/api/v1/matchmaking/cancel/`

退出匹配队列。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |
| Content-Type | application/json |

#### 请求体
```json
{
  "game_type": "ranked"  // 可选，默认为 "ranked"
}
```

#### 响应

**成功 (200 OK)**
```json
{
  "success": true,
  "message": "已取消匹配"
}
```

**失败 (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "服务器错误信息"
}
```

---

### 获取匹配状态

**GET** `/api/v1/matchmaking/status/?game_type=ranked`

查询当前用户在匹配队列中的状态。

#### 请求头
| 字段 | 值 |
|------|-----|
| Authorization | Bearer {access_token} |

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| game_type | string | 否 | 游戏类型 (ranked/casual)，默认 ranked |

#### 响应

**成功 (200 OK)**
```json
{
  "success": true,
  "in_queue": true,
  "queue_position": 3,
  "estimated_wait_time": 25,
  "total_in_queue": 15
}
```

**不在队列中**
```json
{
  "success": true,
  "in_queue": false,
  "queue_position": null,
  "estimated_wait_time": null,
  "total_in_queue": 12
}
```

---

## WebSocket 端点

### 匹配队列连接

**WebSocket URL**: `ws://{host}/ws/matchmaking/?token={access_token}`

提供实时匹配进度通知和匹配成功推送。

#### 连接认证
通过 URL 查询参数传递 JWT Token：
```
?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 客户端消息类型

##### 1. 加入队列
```json
{
  "type": "JOIN_QUEUE",
  "payload": {
    "game_type": "ranked"
  }
}
```

##### 2. 退出队列
```json
{
  "type": "LEAVE_QUEUE"
}
```

##### 3. 获取状态
```json
{
  "type": "GET_STATUS"
}
```

##### 4. 心跳
```json
{
  "type": "HEARTBEAT",
  "payload": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 服务端消息类型

##### 连接确认
```json
{
  "type": "connected",
  "payload": {
    "status": "connected",
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 加入队列成功
```json
{
  "type": "queue_joined",
  "payload": {
    "success": true,
    "game_type": "ranked",
    "rating": 1500,
    "queue_position": 5,
    "estimated_wait_time": 30
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 退出队列成功
```json
{
  "type": "queue_left",
  "payload": {
    "success": true
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 队列状态更新
```json
{
  "type": "queue_status",
  "payload": {
    "total_in_queue": 15,
    "your_position": 3,
    "estimated_wait_time": 25,
    "in_queue": true
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 匹配成功
```json
{
  "type": "match_found",
  "payload": {
    "success": true,
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "opponent": {
      "user_id": "123e4567-e89b-12d3-a456-426614174001",
      "username": "player2",
      "rating": 1520
    },
    "game_type": "ranked",
    "side": "red"  // red/black
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 心跳响应
```json
{
  "type": "HEARTBEAT",
  "payload": {
    "acknowledged": true,
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

##### 错误消息
```json
{
  "type": "ERROR",
  "payload": {
    "success": false,
    "error": {
      "code": "QUEUE_JOIN_FAILED",
      "message": "Failed to join queue"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 错误码说明

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| QUEUE_JOIN_FAILED | 400 | 加入队列失败 |
| QUEUE_LEAVE_FAILED | 400 | 退出队列失败（可能不在队列中） |
| STATUS_ERROR | 500 | 获取状态失败 |
| INVALID_MESSAGE_TYPE | 400 | 无效的消息类型 |
| INVALID_JSON | 400 | JSON 格式错误 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 匹配算法说明

### Elo 等级分匹配
- 初始搜索范围：±100 分
- 等待时间每增加 10 秒，搜索范围扩大 50 分
- 最大搜索范围：±500 分

### 预估等待时间计算
基于以下因素：
- 当前队列人数
- 相近分数段玩家数量
- 历史平均匹配时间

### 匹配流程
1. 用户加入队列，记录 Elo 分数和时间
2. 系统定期执行匹配算法
3. 找到合适对手后，双方收到 `match_found` 消息
4. 创建游戏房间，双方自动加入
