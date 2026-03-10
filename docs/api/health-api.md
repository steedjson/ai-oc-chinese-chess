# 健康检查 API 文档

提供系统各组件的健康状态检测，用于监控和运维。

## 概述

健康检查 API 提供以下功能：

- **综合健康检查**：检查所有核心组件的状态
- **数据库状态**：检查数据库连接和响应时间
- **Redis 状态**：检查 Redis 缓存服务连接
- **WebSocket 状态**：检查 WebSocket 通道层状态

所有端点都无需认证，方便监控系统调用。

## 端点列表

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health/` | GET | 综合健康检查 |
| `/api/health/db/` | GET | 数据库状态 |
| `/api/health/redis/` | GET | Redis 状态 |
| `/api/health/websocket/` | GET | WebSocket 状态 |

## API 详情

### 1. 综合健康检查

**端点**: `GET /api/health/`

检查所有核心组件的健康状态，返回综合评估结果。

#### 请求示例

```bash
curl -X GET http://localhost:8000/api/health/
```

#### 响应示例（健康）

```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T09:00:00.000000",
  "overall_healthy": true,
  "components": {
    "django": {
      "status": "healthy",
      "version": "5.0.0",
      "debug": true
    },
    "database": {
      "status": "healthy",
      "response_time_ms": 1.23,
      "timestamp": "2026-03-06T09:00:00.000000",
      "engine": "django.db.backends.sqlite3",
      "name": "/path/to/db.sqlite3",
      "version": "3.43.0"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.45,
      "timestamp": "2026-03-06T09:00:00.000000",
      "backend": "RedisCache",
      "location": "redis://localhost:6379/0",
      "redis_version": "7.2.0"
    },
    "websocket": {
      "status": "healthy",
      "response_time_ms": 0.89,
      "timestamp": "2026-03-06T09:00:00.000000",
      "backend": "RedisChannelLayer",
      "config": {
        "default": {
          "BACKEND": "channels_redis.core.RedisChannelLayer",
          "CONFIG": {
            "hosts": [["localhost", 6379]],
            "capacity": 1500,
            "expiry": 10
          }
        }
      }
    },
    "python": {
      "status": "healthy",
      "version": "3.12.0"
    },
    "system": {
      "status": "healthy",
      "timestamp": "2026-03-06T09:00:00.000000",
      "uptime_seconds": 1234567.89
    }
  }
}
```

#### 响应示例（不健康）

```json
{
  "status": "unhealthy",
  "timestamp": "2026-03-06T09:00:00.000000",
  "overall_healthy": false,
  "components": {
    "django": {
      "status": "healthy",
      "version": "5.0.0",
      "debug": true
    },
    "database": {
      "status": "unhealthy",
      "response_time_ms": 5000.12,
      "timestamp": "2026-03-06T09:00:00.000000",
      "error": "could not connect to server: Connection refused"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.45,
      "timestamp": "2026-03-06T09:00:00.000000",
      "backend": "RedisCache",
      "location": "redis://localhost:6379/0"
    },
    "websocket": {
      "status": "healthy",
      "response_time_ms": 0.89,
      "timestamp": "2026-03-06T09:00:00.000000",
      "backend": "RedisChannelLayer"
    },
    "python": {
      "status": "healthy",
      "version": "3.12.0"
    },
    "system": {
      "status": "healthy",
      "timestamp": "2026-03-06T09:00:00.000000",
      "uptime_seconds": 1234567.89
    }
  }
}
```

#### HTTP 状态码

- `200 OK`: 所有组件健康
- `503 Service Unavailable`: 至少一个组件不健康

---

### 2. 数据库状态

**端点**: `GET /api/health/db/`

检查数据库连接状态和响应时间。

#### 请求示例

```bash
curl -X GET http://localhost:8000/api/health/db/
```

#### 响应示例（健康）

```json
{
  "component": "database",
  "status": "healthy",
  "response_time_ms": 1.23,
  "timestamp": "2026-03-06T09:00:00.000000",
  "engine": "django.db.backends.sqlite3",
  "name": "/path/to/db.sqlite3",
  "version": "3.43.0"
}
```

#### 响应示例（不健康）

```json
{
  "component": "database",
  "status": "unhealthy",
  "error": "could not connect to server: Connection refused",
  "response_time_ms": 5000.12,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

#### HTTP 状态码

- `200 OK`: 数据库连接正常
- `503 Service Unavailable`: 数据库连接失败

---

### 3. Redis 状态

**端点**: `GET /api/health/redis/`

检查 Redis 缓存服务连接状态。

#### 请求示例

```bash
curl -X GET http://localhost:8000/api/health/redis/
```

#### 响应示例（健康）

```json
{
  "component": "redis",
  "status": "healthy",
  "response_time_ms": 2.45,
  "timestamp": "2026-03-06T09:00:00.000000",
  "backend": "RedisCache",
  "location": "redis://localhost:6379/0",
  "redis_version": "7.2.0"
}
```

#### 响应示例（不健康）

```json
{
  "component": "redis",
  "status": "unhealthy",
  "error": "Error connecting to Redis on localhost:6379. Connection refused.",
  "response_time_ms": 5000.34,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

#### HTTP 状态码

- `200 OK`: Redis 连接正常
- `503 Service Unavailable`: Redis 连接失败

---

### 4. WebSocket 状态

**端点**: `GET /api/health/websocket/`

检查 WebSocket 通道层状态。

#### 请求示例

```bash
curl -X GET http://localhost:8000/api/health/websocket/
```

#### 响应示例（Redis 模式 - 生产环境）

```json
{
  "component": "websocket",
  "status": "healthy",
  "response_time_ms": 0.89,
  "timestamp": "2026-03-06T09:00:00.000000",
  "backend": "RedisChannelLayer",
  "config": {
    "default": {
      "BACKEND": "channels_redis.core.RedisChannelLayer",
      "CONFIG": {
        "hosts": [["localhost", 6379]],
        "capacity": 1500,
        "expiry": 10
      }
    }
  }
}
```

#### 响应示例（内存模式 - 开发环境）

```json
{
  "component": "websocket",
  "status": "healthy",
  "response_time_ms": 0.12,
  "timestamp": "2026-03-06T09:00:00.000000",
  "backend": "InMemoryChannelLayer",
  "status": "development_mode",
  "note": "Using in-memory channel layer (development only)"
}
```

#### 响应示例（不健康）

```json
{
  "component": "websocket",
  "status": "unhealthy",
  "error": "Redis channel layer error: Connection refused",
  "response_time_ms": 5000.56,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

#### HTTP 状态码

- `200 OK`: WebSocket 通道层正常
- `503 Service Unavailable`: WebSocket 通道层异常

---

## 响应字段说明

### 通用字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `status` | string | 健康状态：`healthy` 或 `unhealthy` |
| `timestamp` | string | ISO 8601 格式的时间戳 |
| `response_time_ms` | number | 响应时间（毫秒） |
| `error` | string | 错误信息（仅当不健康时） |

### 组件特定字段

#### Django

| 字段 | 类型 | 描述 |
|------|------|------|
| `version` | string | Django 版本号 |
| `debug` | boolean | 是否开启调试模式 |

#### Database

| 字段 | 类型 | 描述 |
|------|------|------|
| `engine` | string | 数据库引擎 |
| `name` | string | 数据库名称/路径 |
| `version` | string | 数据库版本 |

#### Redis

| 字段 | 类型 | 描述 |
|------|------|------|
| `backend` | string | 缓存后端类名 |
| `location` | string | Redis 连接地址 |
| `redis_version` | string | Redis 服务器版本 |

#### WebSocket

| 字段 | 类型 | 描述 |
|------|------|------|
| `backend` | string | 通道层后端类名 |
| `config` | object | 通道层配置 |
| `note` | string | 附加说明（开发模式提示） |

---

## 使用场景

### 1. 负载均衡器健康检查

配置负载均衡器（如 Nginx、HAProxy）定期调用 `/api/health/` 端点，自动剔除不健康的实例。

```nginx
location /health {
    proxy_pass http://backend/api/health/;
    proxy_connect_timeout 5s;
    proxy_read_timeout 5s;
}
```

### 2. Kubernetes 存活探针

在 Kubernetes 部署配置中添加健康检查探针：

```yaml
livenessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/health/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### 3. 监控系统集成

使用 Prometheus、Grafana 等监控系统定期抓取健康状态：

```bash
# 使用 curl 定期检查
while true; do
  curl -s http://localhost:8000/api/health/ | jq '.status'
  sleep 30
done
```

### 4. 运维脚本

编写运维脚本检查服务状态：

```bash
#!/bin/bash

HEALTH_URL="http://localhost:8000/api/health/"
RESPONSE=$(curl -s -w "\n%{http_code}" $HEALTH_URL)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Health check failed with HTTP $HTTP_CODE"
  echo "$BODY" | jq '.components | to_entries[] | select(.value.status == "unhealthy")'
  exit 1
else
  echo "✅ All systems healthy"
  exit 0
fi
```

---

## 安全考虑

1. **无需认证**: 健康检查端点设计为无需认证，方便监控系统调用
2. **信息泄露**: 生产环境应限制访问来源（如仅允许内网访问）
3. **限流**: 建议对健康检查端点实施限流，防止滥用
4. **敏感信息**: 响应中不包含密码、密钥等敏感信息

### 生产环境配置建议

在 Nginx 中限制访问来源：

```nginx
location /api/health/ {
    # 仅允许内网访问
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    allow 127.0.0.1;
    deny all;
    
    proxy_pass http://backend;
}
```

---

## 故障排查

### 数据库连接失败

**症状**: `/api/health/db/` 返回 `503` 状态码

**可能原因**:
- 数据库服务未启动
- 数据库配置错误
- 网络连接问题

**解决方案**:
1. 检查数据库服务状态
2. 验证 `DATABASES` 配置
3. 检查防火墙规则

### Redis 连接失败

**症状**: `/api/health/redis/` 返回 `503` 状态码

**可能原因**:
- Redis 服务未启动
- Redis 配置错误
- 端口被占用

**解决方案**:
1. 启动 Redis: `redis-server`
2. 检查 `REDIS_URL` 配置
3. 验证端口 6379 是否可用

### WebSocket 通道层异常

**症状**: `/api/health/websocket/` 返回 `503` 状态码

**可能原因**:
- Channels 库未安装
- Redis 通道层配置错误
- Redis 不可用

**解决方案**:
1. 确认 `channels` 和 `channels-redis` 已安装
2. 检查 `CHANNEL_LAYERS` 配置
3. 验证 Redis 连接

---

## 相关文件

- 视图实现：`health/views.py`
- URL 路由：`health/urls.py`
- 主配置：`config/settings.py`
- 主路由：`config/urls.py`

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-06 | 初始版本 |
