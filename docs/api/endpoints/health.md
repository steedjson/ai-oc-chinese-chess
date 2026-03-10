# 健康检查 API 端点 (Health Endpoints)

**基础路径**: `/api/health/`

---

## 端点概览

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/` | GET | ❌ | 综合健康检查 |
| `/db/` | GET | ❌ | 数据库状态 |
| `/redis/` | GET | ❌ | Redis 状态 |
| `/websocket/` | GET | ❌ | WebSocket 状态 |

---

## 1. 综合健康检查

### GET `/api/health/`

检查所有核心组件的健康状态，返回综合评估结果。

### 请求

无需认证，无需参数。

### 响应

**健康 (200 OK)**:
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

**不健康 (503 Service Unavailable)**:
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

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 所有组件健康 |
| 503 | 至少一个组件不健康 |

---

## 2. 数据库状态

### GET `/api/health/db/`

检查数据库连接状态和响应时间。

### 请求

无需认证，无需参数。

### 响应

**健康 (200 OK)**:
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

**不健康 (503 Service Unavailable)**:
```json
{
  "component": "database",
  "status": "unhealthy",
  "error": "could not connect to server: Connection refused",
  "response_time_ms": 5000.12,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 数据库连接正常 |
| 503 | 数据库连接失败 |

---

## 3. Redis 状态

### GET `/api/health/redis/`

检查 Redis 缓存服务连接状态。

### 请求

无需认证，无需参数。

### 响应

**健康 (200 OK)**:
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

**不健康 (503 Service Unavailable)**:
```json
{
  "component": "redis",
  "status": "unhealthy",
  "error": "Error connecting to Redis on localhost:6379. Connection refused.",
  "response_time_ms": 5000.34,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | Redis 连接正常 |
| 503 | Redis 连接失败 |

---

## 4. WebSocket 状态

### GET `/api/health/websocket/`

检查 WebSocket 通道层状态。

### 请求

无需认证，无需参数。

### 响应

**健康 - Redis 模式 (生产环境)**:
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

**健康 - 内存模式 (开发环境)**:
```json
{
  "component": "websocket",
  "status": "development_mode",
  "response_time_ms": 0.12,
  "timestamp": "2026-03-06T09:00:00.000000",
  "backend": "InMemoryChannelLayer",
  "note": "Using in-memory channel layer (development only)"
}
```

**不健康 (503 Service Unavailable)**:
```json
{
  "component": "websocket",
  "status": "unhealthy",
  "error": "Redis channel layer error: Connection refused",
  "response_time_ms": 5000.56,
  "timestamp": "2026-03-06T09:00:00.000000"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | WebSocket 通道层正常 |
| 503 | WebSocket 通道层异常 |

---

## 响应字段说明

### 通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 健康状态：`healthy`, `unhealthy`, `development_mode` |
| `timestamp` | string | ISO 8601 格式的时间戳 |
| `response_time_ms` | number | 响应时间（毫秒） |
| `error` | string | 错误信息（仅当不健康时） |
| `component` | string | 组件名称 |

### 组件特定字段

#### Django

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | Django 版本号 |
| `debug` | boolean | 是否开启调试模式 |

#### Database

| 字段 | 类型 | 说明 |
|------|------|------|
| `engine` | string | 数据库引擎 |
| `name` | string | 数据库名称/路径 |
| `version` | string | 数据库版本 |

#### Redis

| 字段 | 类型 | 说明 |
|------|------|------|
| `backend` | string | 缓存后端类名 |
| `location` | string | Redis 连接地址 |
| `redis_version` | string | Redis 服务器版本 |

#### WebSocket

| 字段 | 类型 | 说明 |
|------|------|------|
| `backend` | string | 通道层后端类名 |
| `config` | object | 通道层配置 |
| `note` | string | 附加说明（开发模式提示） |

#### Python

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | Python 版本号 |

#### System

| 字段 | 类型 | 说明 |
|------|------|------|
| `uptime_seconds` | number | 系统运行时间（秒） |

---

## 使用场景

### 1. 负载均衡器健康检查

配置 Nginx 负载均衡器：

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
}

server {
    location /health {
        proxy_pass http://backend/api/health/;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }
}
```

### 2. Kubernetes 探针配置

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: chinese-chess
spec:
  containers:
  - name: app
    image: chinese-chess:latest
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

### 3. Docker Compose 健康检查

```yaml
version: '3.8'
services:
  app:
    image: chinese-chess:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 4. Prometheus 监控

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chinese-chess'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/health/'
    scrape_interval: 30s
```

### 5. 运维脚本

```bash
#!/bin/bash

HEALTH_URL="http://localhost:8000/api/health/"

check_health() {
    response=$(curl -s -w "\n%{http_code}" $HEALTH_URL)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" != "200" ]; then
        echo "❌ Health check failed with HTTP $http_code"
        echo "$body" | jq '.components | to_entries[] | select(.value.status == "unhealthy")'
        return 1
    else
        echo "✅ All systems healthy"
        return 0
    fi
}

check_health
```

### 6. Grafana 面板

使用 Graphite 或 Prometheus 数据源创建健康状态面板：

```
# Prometheus Query
chinese_chess_health_status{component="database"}
chinese_chess_health_status{component="redis"}
chinese_chess_health_status{component="websocket"}
```

---

## 安全考虑

### 生产环境配置

1. **限制访问来源**:

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

2. **限流配置**:

```nginx
location /api/health/ {
    limit_req zone=health_limit burst=10 nodelay;
    proxy_pass http://backend;
}

# 在 http 块中定义
limit_req_zone $binary_remote_addr zone=health_limit:10m rate=1r/s;
```

3. **信息脱敏**:

生产环境建议隐藏敏感信息：

```python
# settings.py
HEALTH_CHECK_HIDE_DETAILS = True
```

---

## 故障排查

### 数据库连接失败

**症状**: `/api/health/db/` 返回 `503`

**可能原因**:
- 数据库服务未启动
- 数据库配置错误
- 网络连接问题

**解决方案**:
```bash
# 检查数据库服务
sudo systemctl status postgresql  # 或 mysql

# 测试连接
psql -h localhost -U username -d database_name

# 检查配置
cat config/settings.py | grep DATABASES
```

### Redis 连接失败

**症状**: `/api/health/redis/` 返回 `503`

**可能原因**:
- Redis 服务未启动
- Redis 配置错误
- 端口被占用

**解决方案**:
```bash
# 检查 Redis 服务
sudo systemctl status redis

# 测试连接
redis-cli ping

# 检查端口
netstat -tlnp | grep 6379
```

### WebSocket 通道层异常

**症状**: `/api/health/websocket/` 返回 `503`

**可能原因**:
- Channels 库未安装
- Redis 通道层配置错误
- Redis 不可用

**解决方案**:
```bash
# 检查 Channels 安装
pip show channels
pip show channels-redis

# 检查配置
cat config/settings.py | grep CHANNEL_LAYERS

# 重启 Daphne/ASGI 服务器
sudo systemctl restart daphne
```

---

## 相关文件

- **视图实现**: `health/views.py`
- **URL 路由**: `health/urls.py`
- **主配置**: `config/settings.py`

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06
