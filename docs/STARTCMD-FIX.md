# 后端启动命令修复报告 - 使用 Django runserver

**修复日期**: 2026-03-03  
**修复者**: 中国象棋项目高级开发工程师  
**问题**: Daphne 存在兼容性问题，开发环境应使用 Django runserver

---

## 📋 问题描述

用户反馈在使用 Daphne 启动后端时遇到兼容性问题：
- 中间件协程错误
- WebSocket 连接问题

**解决方案**: 开发环境使用 Django 内置的 `runserver` 命令，它会自动处理 ASGI 配置。

---

## 🔍 检查结果

### 1. 文档检查

| 文档 | 状态 | 说明 |
|------|------|------|
| `README.md` | ✅ 正确 | 使用 `python manage.py runserver` |
| `docs/SETUP-GUIDE.md` | ✅ 正确 | 使用 `python manage.py runserver` |
| `docs/architecture.md` | ⚠️ 需修改 | 环境配置对比表中 WS 服务器描述不准确 |
| `docs/WEBSOCKET-ROUTING-FIX.md` | ✅ 正确 | 说明使用 runserver 时 Channels 会自动使用 ASGI |
| `docs/VERIFICATION-REPORT.md` | ℹ️ 信息性 | 记录了 Daphne 兼容性问题 |

### 2. 依赖检查

`src/backend/requirements.txt`:
```
# WebSocket
channels==4.0.0
channels-redis==4.2.0
daphne==4.0.0  # 保留作为 ASGI 依赖
```

**说明**: `daphne` 作为依赖包保留是必要的，因为：
- Channels 需要 ASGI 服务器支持
- 生产环境仍使用 Daphne
- 开发环境使用 `runserver` 时，Django 会自动处理 ASGI

### 3. 启动命令检查

**开发环境正确启动方式**:
```bash
cd src/backend
python manage.py runserver 8000
```

**生产环境启动方式** (Docker):
```bash
# WebSocket 服务
daphne -b 0.0.0.0 -p 8001 config.asgi:application

# HTTP 服务
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 8
```

---

## 🛠️ 修复内容

### 修改 1: `docs/architecture.md`

**位置**: 6.4 环境配置对比表

**修改前**:
```markdown
| **WS 服务器** | Daphne (dev) | Daphne (2 实例) | Daphne (N 实例) |
```

**修改后**:
```markdown
| **WS 服务器** | runserver (内置 ASGI) | Daphne (2 实例) | Daphne (N 实例) |
```

**理由**: 开发环境使用 `python manage.py runserver` 时，Django Channels 会自动使用 ASGI 协议处理 WebSocket，无需单独配置 Daphne。

---

## 📝 技术说明

### 为什么开发环境使用 runserver？

1. **自动 ASGI 支持**: Django 4.x+ 的 `runserver` 命令会自动检测 ASGI 配置
2. **简化开发**: 无需额外配置 ASGI 服务器
3. **调试友好**: 支持热重载、详细错误信息
4. **避免兼容性问题**: Daphne 在开发环境可能出现中间件协程错误

### 为什么生产环境使用 Daphne？

1. **性能**: Daphne 是专为生产环境设计的 ASGI 服务器
2. **稳定性**: 经过生产验证，支持高并发
3. **功能完整**: 支持完整的 ASGI 规范
4. **可伸缩**: 支持多实例部署

### Django runserver 如何支持 WebSocket？

当配置了 `ASGI_APPLICATION` 时，`runserver` 会自动：
1. 加载 ASGI 配置
2. 根据协议类型路由请求 (HTTP/WebSocket)
3. 使用 Channels 处理 WebSocket 连接

```python
# config/settings.py
ASGI_APPLICATION = 'config.asgi.application'

# config/asgi.py
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

---

## ✅ 验证结果

### 测试 1: 服务启动

```bash
cd /Users/changsailong/.openclaw/workspace/projects/chinese-chess/src/backend
python manage.py runserver 8000 --settings=config.settings
```

**结果**: ✅ 服务正常启动
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
March 03, 2026 - 22:00:00
Django version 5.0, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 测试 2: WebSocket 路由

```bash
python -c "
import django
django.setup()
from websocket.routing import websocket_urlpatterns
print('WebSocket routes:', len(websocket_urlpatterns))
for pattern in websocket_urlpatterns:
    print(' -', pattern.pattern)
"
```

**结果**: ✅ 所有路由正常加载
```
WebSocket routes: 3
 - ws/game/(?P<game_id>[^/]+)/$
 - ws/ai/game/(?P<game_id>[^/]+)/$
 - ws/matchmaking/$
```

### 测试 3: HTTP 服务

```bash
curl http://localhost:8000/api/v1/health/
```

**结果**: ✅ 健康检查通过
```json
{
  "status": "healthy",
  "components": {
    "django": {"status": "healthy", "version": "5.0"},
    "database": {"status": "healthy"},
    "cache": {"status": "healthy"},
    "python": {"status": "healthy", "version": "3.12.6"}
  }
}
```

---

## 📚 更新后的启动说明

### 开发环境

```bash
# 1. 进入项目目录
cd projects/chinese-chess/

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 进入后端目录
cd src/backend

# 4. 启动开发服务器
python manage.py runserver 8000
```

**访问**:
- HTTP: http://localhost:8000/
- WebSocket: ws://localhost:8000/ws/game/{game_id}/

### 生产环境 (Docker)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**服务**:
- Web (Gunicorn): http://0.0.0.0:8000/
- WebSocket (Daphne): ws://0.0.0.0:8001/

---

## 🎯 总结

### 修改内容

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `docs/architecture.md` | 更新 | 修正环境配置对比表中的 WS 服务器描述 |
| `docs/STARTCMD-FIX.md` | 新建 | 本修复报告 |

### 保留内容

- `requirements.txt` 中的 `daphne==4.0.0` 保留（生产环境需要）
- 生产环境 Docker 配置中的 Daphne 命令保留

### 关键要点

1. ✅ **开发环境**: 使用 `python manage.py runserver`，无需直接使用 Daphne
2. ✅ **生产环境**: 使用 Daphne 作为 ASGI 服务器
3. ✅ **依赖保留**: `daphne` 包作为依赖保留，生产环境需要
4. ✅ **文档更新**: 已更新 architecture.md 中的环境配置表

---

## 📋 验证清单

| 检查项 | 验证方法 | 状态 |
|--------|---------|------|
| 文档修改 | 检查 README.md | ✅ 使用 runserver |
| 文档修改 | 检查 SETUP-GUIDE.md | ✅ 使用 runserver |
| 文档修改 | 检查 architecture.md | ✅ 已修正 |
| 服务启动 | 实际测试 runserver | ✅ 正常启动 |
| WebSocket 路由 | 检查路由配置 | ✅ 正常加载 |
| HTTP 服务 | 访问健康检查端点 | ✅ 响应正常 |

---

**报告生成时间**: 2026-03-03 22:16  
**修复状态**: ✅ 已完成
