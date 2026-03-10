# 测试覆盖率分析报告

**生成时间**: 2026-03-06  
**当前覆盖率**: 47%  
**目标覆盖率**: 80%+  
**差距**: 33%

---

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 总语句数 | 7005 |
| 未覆盖语句 | 3719 |
| 当前覆盖率 | 47% |
| 目标覆盖率 | 80% |
| 需覆盖语句 | ~1881 |

---

## 🔴 0% 覆盖率文件（优先级：最高）

这些文件完全没有测试覆盖，需要添加完整测试。

| 文件 | 语句数 | 模块 | 说明 |
|------|--------|------|------|
| games/ranking_services.py | 199 | games | 排行榜核心服务 |
| games/websocket_reconnect_optimized.py | 343 | games | WebSocket 断线重连优化 |
| tests/unit/games/test_websocket_reconnect.py | 255 | tests | 测试文件（本身需要执行） |
| ai_engine/tasks.py | 62 | ai_engine | Celery 异步任务 |
| verify_reconnect.py | 111 | root | 验证脚本 |
| test_websocket.py | 135 | root | 测试脚本 |
| games/ranking_models.py | 136 | games | 排行榜模型 |
| common/health.py | 42 | common | 健康检查 |
| daily_challenge/management/commands/generate_daily_challenge.py | 29 | daily_challenge | 管理命令 |
| manage.py | 11 | root | Django 管理脚本 |
| config/asgi.py | 9 | config | ASGI 配置 |
| config/wsgi.py | 4 | config | WSGI 配置 |
| common/health_urls.py | 3 | common | 健康检查 URL |

**小计**: 1339 语句

---

## 🟠 低覆盖率文件（<30%，优先级：高）

| 文件 | 覆盖率 | 语句数 | 未覆盖 | 模块 |
|------|--------|--------|--------|------|
| games/consumers.py | 15% | 324 | 275 | games |
| matchmaking/consumers.py | 19% | 174 | 141 | matchmaking |
| games/chat_consumer.py | 24% | 227 | 172 | games |
| games/spectator_consumer.py | 23% | 192 | 147 | games |
| health/views.py | 22% | 140 | 109 | health |
| ai_engine/consumers.py | 27% | 74 | 54 | ai_engine |
| users/views.py | 25% | 143 | 107 | users |
| matchmaking/views.py | 29% | 75 | 53 | matchmaking |
| games/spectator_views.py | 30% | 88 | 62 | games |
| ai_engine/views.py | 30% | 122 | 85 | ai_engine |
| games/websocket_reconnect.py | 30% | 243 | 169 | games |
| websocket/middleware.py | 32% | 174 | 119 | websocket |
| matchmaking/__init__.py | 33% | 15 | 10 | matchmaking |

**小计**: 1991 语句

---

## 🟡 中等覆盖率文件（30%-60%，优先级：中）

| 文件 | 覆盖率 | 语句数 | 未覆盖 | 模块 |
|------|--------|--------|--------|------|
| games/spectator.py | 46% | 168 | 90 | games |
| ai_engine/engine_pool.py | 40% | 47 | 28 | ai_engine |
| puzzles/views.py | 40% | 85 | 51 | puzzles |
| games/views.py | 55% | 105 | 47 | games |
| games/chat.py | 58% | 182 | 77 | games |
| matchmaking/algorithm.py | 58% | 160 | 68 | matchmaking |
| authentication/services.py | 56% | 73 | 32 | authentication |
| matchmaking/elo.py | 52% | 121 | 58 | matchmaking |
| websocket/consumers.py | 50% | 117 | 59 | websocket |
| daily_challenge/views.py | 60% | 180 | 72 | daily_challenge |

**小计**: 1233 语句

---

## 📋 测试编写计划

### 第一阶段：0% 覆盖率核心模块（目标：+15%）

1. **games/ranking_services.py** (199 语句)
   - 测试排行榜核心服务
   - 测试缓存服务
   - 测试排行榜统计

2. **ai_engine/tasks.py** (62 语句)
   - 测试 Celery 异步任务
   - Mock Stockfish 服务

3. **games/ranking_models.py** (136 语句)
   - 测试模型方法
   - 测试模型管理器

### 第二阶段：WebSocket 消费者（目标：+10%）

4. **games/consumers.py** (324 语句)
   - 测试游戏连接
   - 测试走棋逻辑
   - 测试游戏状态同步

5. **games/chat_consumer.py** (227 语句)
   - 测试聊天连接
   - 测试消息发送/接收

6. **games/spectator_consumer.py** (192 语句)
   - 测试观战连接
   - 测试观战功能

### 第三阶段：Views 和 API（目标：+8%）

7. **ai_engine/views.py** (122 语句)
8. **users/views.py** (143 语句)
9. **health/views.py** (140 语句)
10. **daily_challenge/views.py** (180 语句)

### 第四阶段：其他模块（目标：+5%）

11. **matchmaking/** 相关模块
12. **websocket/** 相关模块
13. **puzzles/views.py**

---

## 🎯 覆盖率提升路径

| 阶段 | 目标覆盖率 | 重点模块 |
|------|------------|----------|
| 当前 | 47% | - |
| 第一阶段后 | 62% | ranking_services, tasks, ranking_models |
| 第二阶段后 | 72% | consumers |
| 第三阶段后 | 80% | views |
| 第四阶段后 | 85% | 其他模块 |

---

## 📝 备注

- 部分文件（如 manage.py, config/asgi.py）为配置文件，测试优先级较低
- 优先测试业务逻辑复杂、使用频率高的模块
- 对于依赖外部服务（如 Stockfish）的代码，使用 Mock 进行测试
