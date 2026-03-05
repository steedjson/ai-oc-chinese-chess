# 中国象棋 - 后端联调测试报告

**测试日期**: 2026-03-03  
**测试人员**: OpenClaw 助手  
**项目位置**: `/Users/changsailong/.openclaw/workspace/projects/chinese-chess/`

---

## 测试概述

本次测试验证了中国象棋项目前后端的集成情况，包括后端 API 服务、前端连接、WebSocket 通信和完整用户流程。

---

## 1. 后端服务启动测试

### 1.1 环境检查

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Python 版本 | ⚠️ 警告 | Python 3.9.6（项目要求 3.11+） |
| 虚拟环境 | ❌ 未使用 | 依赖安装在全局环境 |
| Django | ✅ 已安装 | 4.2.28 |
| DRF | ✅ 已安装 | 3.16.1 |
| Channels | ✅ 已安装 | 4.3.2 |
| Daphne | ✅ 已安装 | 4.2.1 |

### 1.2 数据库检查

| 检查项 | 状态 | 详情 |
|--------|------|------|
| SQLite 数据库 | ✅ 存在 | `db.sqlite3` |
| 数据库迁移 | ✅ 完成 | 所有迁移已应用 |

**发现的问題**:
- `users` 应用缺少迁移文件，已创建 `users/migrations/0001_initial.py`
- `AIGame` 模型的 `player_id` 字段类型与用户模型不匹配（UUID vs 整数），已修复为外键

### 1.3 后端服务启动

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 使用 runserver 启动 | ✅ 成功 | HTTP 服务正常 |
| 使用 Daphne 启动 | ✅ 成功 | HTTP + WebSocket 支持 |
| 端口占用 | ✅ 无问题 | 8000 端口可用 |

**启动日志**:
```
2026-03-03 17:10:26,541 INFO     Starting server at tcp:port=8000:interface=127.0.0.1
2026-03-03 17:10:26,541 INFO     HTTP/2 support not enabled
2026-03-03 17:10:26,542 INFO     Listening on TCP address 127.0.0.1:8000
```

---

## 2. API 接口测试

### 2.1 健康检查

| 端点 | 状态 | 响应 |
|------|------|------|
| `/api/v1/health` | ❌ 404 | 端点未实现 |

**建议**: 添加健康检查端点用于监控。

### 2.2 用户认证 API

| 端点 | 方法 | 状态 | 详情 |
|------|------|------|------|
| `/api/v1/auth/register/` | POST | ✅ 201 | 注册成功 |
| `/api/v1/auth/login/` | POST | ✅ 200 | 登录成功 |

**注册请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user1","email":"test1@example.com","password":"Test@123456","password_confirm":"Test@123456"}'
```

**注册响应**:
```json
{
    "success": true,
    "data": {
        "user_id": "1",
        "username": "test_user1",
        "email": "test1@example.com",
        "access_token": "eyJhbGci...",
        "refresh_token": "eyJhbGci...",
        "expires_in": 7200
    },
    "message": "注册成功"
}
```

**注意**: 注册需要 `password_confirm` 字段，与测试计划中的示例不同。

### 2.3 游戏 API

| 端点 | 方法 | 状态 | 详情 |
|------|------|------|------|
| `/api/v1/games/` | POST | ✅ 201 | 创建游戏成功 |

**创建游戏响应**:
```json
{
    "id": "dfa28915-7587-4b39-8e95-4c0ce9706d01",
    "game_type": "single",
    "status": "playing",
    "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    ...
}
```

### 2.4 AI 对弈 API

| 端点 | 方法 | 状态 | 详情 |
|------|------|------|------|
| `/api/v1/ai/games/` | POST | ✅ 201 | 创建 AI 对局成功 |

**修复的问题**:
- `AIGame` 模型的 `player_id` 字段从 UUID 改为外键关联用户
- `AIGameCreateSerializer` 更新为自动从 request 获取玩家
- 视图代码更新为使用 `player` 而非 `player_id`

**创建 AI 对局请求**:
```bash
curl -X POST http://localhost:8000/api/v1/ai/games/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"ai_level": 5, "ai_side": "black", "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"}'
```

### 2.5 匹配系统 API

| 端点 | 状态 | 详情 |
|------|------|------|
| `/api/v1/matchmaking/queue` | ❌ 未实现 | URL 路由未配置 |

**建议**: 
- 创建 `matchmaking/urls.py`
- 在 `config/urls.py` 中注册匹配系统路由

---

## 3. 前端连接测试

### 3.1 前端配置

已更新 `.env.development`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
VITE_USE_MOCK=false
VITE_TEST_USERNAME=test_user1
VITE_TEST_PASSWORD=Test@123456
```

### 3.2 前端开发服务器

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 启动命令 | ✅ 成功 | `npm run dev` |
| 访问地址 | ✅ 正常 | http://localhost:3000/ |
| Vite 版本 | ✅ | v7.3.1 |

### 3.3 页面连接测试

由于浏览器工具配置问题，无法进行完整的 UI 测试。建议手动测试以下页面：
- [ ] 登录页面
- [ ] AI 对战页面
- [ ] 匹配对战页面
- [ ] 用户中心
- [ ] 排行榜

---

## 4. WebSocket 连接测试

### 4.1 WebSocket 路由配置

**修复的问题**:
- `config/asgi.py` 修改为在 `get_asgi_application()` 之后导入 WebSocket 路由
- 解决了 `AppRegistryNotReady` 错误

**WebSocket 端点**:
- `ws://localhost:8000/ws/game/{game_id}/` - 游戏房间
- `ws://localhost:8000/ws/ai/game/{game_id}/` - AI 对弈

### 4.2 WebSocket 连接测试

| 测试项 | 状态 | 详情 |
|--------|------|------|
| 无 Token 连接 | ⚠️ 403 | 预期行为（需要认证） |
| 带 Token 连接 | ⚠️ 403 | 认证逻辑需调试 |

**发现的问题**:
- WebSocket 认证返回错误 "0"，可能是 `TokenService.verify_token` 或 `_get_user_by_id` 的问题
- 需要进一步调试消费者中的认证逻辑

**建议修复**:
1. 在 `TokenService.verify_token` 中添加详细日志
2. 检查 `_get_user_by_id` 返回的用户数据格式
3. 确保消费者正确处理用户字典 vs 用户对象

---

## 5. 完整流程测试

### 5.1 AI 对弈流程

| 步骤 | 状态 | 详情 |
|------|------|------|
| 1. 用户注册/登录 | ✅ 通过 | API 正常 |
| 2. 创建 AI 对局 | ✅ 通过 | API 正常 |
| 3. 选择难度 | ✅ 通过 | 参数验证正常 |
| 4. 玩家走棋 | ⬜ 未测试 | 需要 WebSocket |
| 5. AI 响应走棋 | ⬜ 未测试 | 需要 AI 引擎 |
| 6. 游戏结束判定 | ⬜ 未测试 | 需要完整流程 |

### 5.2 匹配对战流程

| 步骤 | 状态 | 详情 |
|------|------|------|
| 1. 用户登录 | ✅ 通过 | API 正常 |
| 2. 加入匹配队列 | ❌ 未实现 | 路由缺失 |
| 3. 匹配成功通知 | ⬜ 未测试 | - |
| 4. 创建游戏房间 | ✅ 通过 | API 正常 |
| 5-7. 对战流程 | ⬜ 未测试 | 需要 WebSocket |

---

## 6. 验证标准汇总

| 标准 | 状态 | 备注 |
|------|------|------|
| 后端服务启动成功 | ✅ | Daphne ASGI 服务器 |
| 数据库迁移完成 | ✅ | 所有迁移已应用 |
| 健康检查通过 | ❌ | 端点未实现 |
| 用户注册/登录 API | ✅ | 功能正常 |
| 游戏 API 正常 | ✅ | 功能正常 |
| AI 对弈 API 正常 | ✅ | 功能正常（已修复） |
| 匹配系统 API 正常 | ❌ | 路由未配置 |
| 前端连接成功 | ✅ | 开发服务器启动 |
| WebSocket 连接成功 | ⚠️ | 认证需调试 |
| 完整流程测试通过 | ⬜ | 部分未测试 |

---

## 7. 发现的问题与修复建议

### 7.1 已修复的问题

1. **users 应用缺少迁移**
   - 问题：数据库中没有 users 表
   - 修复：运行 `python3 manage.py makemigrations users` 创建迁移

2. **AIGame 模型 player_id 类型不匹配**
   - 问题：用户模型使用整数 ID，AIGame 使用 UUID
   - 修复：将 `player_id` 改为外键关联 `users.User`

3. **ASGI 应用加载顺序错误**
   - 问题：`AppRegistryNotReady` 错误
   - 修复：在 `get_asgi_application()` 之后导入 WebSocket 路由

### 7.2 待修复的问题

1. **WebSocket 认证失败**
   - 现象：带 Token 连接仍返回 403
   - 可能原因：`TokenService.verify_token` 或 `_get_user_by_id` 问题
   - 建议：添加详细日志，检查 Token 验证流程

2. **匹配系统路由缺失**
   - 问题：`/api/v1/matchmaking/` 未配置
   - 建议：创建 `matchmaking/urls.py` 并注册路由

3. **健康检查端点缺失**
   - 问题：`/api/v1/health` 返回 404
   - 建议：添加简单健康检查视图

4. **Python 版本不匹配**
   - 问题：系统 Python 3.9.6，项目要求 3.11+
   - 建议：使用 pyenv 或创建虚拟环境

5. **缺少虚拟环境**
   - 问题：依赖安装在全局环境
   - 建议：创建项目专用虚拟环境

---

## 8. 测试账号

已创建测试账号并保存到 `.env.development`:

```env
VITE_TEST_USERNAME=test_user1
VITE_TEST_PASSWORD=Test@123456
```

**账号信息**:
- 用户名：`test_user1`
- 邮箱：`test1@example.com`
- 用户 ID：`1`

---

## 9. 后续工作建议

### 高优先级

1. **修复 WebSocket 认证**
   - 调试 `TokenService.verify_token` 
   - 检查消费者中的用户数据格式

2. **配置匹配系统路由**
   - 创建 `matchmaking/urls.py`
   - 在 `config/urls.py` 中注册

3. **添加健康检查端点**
   - 实现 `/api/v1/health` 
   - 返回服务状态信息

### 中优先级

4. **创建虚拟环境**
   ```bash
   cd projects/chinese-chess/src/backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **完善 API 文档**
   - 使用 Swagger/OpenAPI
   - 添加 API 使用示例

### 低优先级

6. **升级 Python 版本**
   - 使用 pyenv 安装 Python 3.11+
   - 更新项目文档

7. **添加端到端测试**
   - 使用 Playwright 测试前端
   - 使用 pytest 测试后端

---

## 10. 测试结论

**总体评估**: ⚠️ 部分通过

后端核心 API（用户认证、游戏创建、AI 对局）功能正常，但存在以下问题需要修复：

1. WebSocket 认证逻辑需调试
2. 匹配系统路由未配置
3. 缺少健康检查端点
4. 项目环境配置需优化（虚拟环境、Python 版本）

**建议**: 优先修复 WebSocket 认证问题，然后完成匹配系统路由配置，最后进行完整的端到端测试。

---

**报告生成时间**: 2026-03-03 17:15 GMT+8  
**测试工具**: OpenClaw + curl + Python websockets
