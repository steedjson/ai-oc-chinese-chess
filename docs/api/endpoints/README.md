# API 端点文档索引

本目录包含 Chinese Chess API 各模块的详细端点文档。

**最后更新**: 2026-03-06  
**总端点数量**: 60+

---

## 📚 文档列表

### ✅ 认证模块
- **文件**: [authentication.md](./authentication.md)
- **基础路径**: `/api/v1/auth/`
- **端点数量**: 5
- **端点**:
  - `POST /register/` - 用户注册
  - `POST /login/` - 用户登录
  - `POST /logout/` - 用户登出
  - `POST /refresh/` - 刷新 Token
  - `GET /me/` - 获取当前用户信息

---

### ✅ 游戏对局模块
- **文件**: [games.md](./games.md)
- **基础路径**: `/api/v1/`
- **端点数量**: 11
- **端点**:
  - `GET /games/` - 获取对局列表
  - `POST /games/` - 创建新对局
  - `GET /games/{id}/` - 获取对局详情
  - `PUT /games/{id}/` - 更新对局
  - `DELETE /games/{id}/` - 取消对局
  - `POST /games/{id}/move/` - 提交走棋
  - `GET /games/{id}/moves/` - 获取走棋历史
  - `PUT /games/{id}/status/` - 更新对局状态
  - `GET /users/{id}/games/` - 获取用户对局
  - `GET /games/{id}/spectators/` - 获取观战者
  - `POST /chat/games/{id}/send/` - 发送聊天消息
  - `GET /chat/games/{id}/history/` - 获取聊天历史

---

### ✅ 每日挑战模块
- **文件**: [daily_challenge.md](./daily_challenge.md)
- **基础路径**: `/api/v1/daily-challenge/`
- **端点数量**: 12
- **端点**:
  - `GET /today/` - 获取今日挑战
  - `POST /today/attempt/` - 开始挑战
  - `POST /today/move/` - 提交走法
  - `POST /today/complete/` - 完成挑战
  - `GET /leaderboard/` - 获取排行榜
  - `GET /leaderboard/daily/` - 每日排行榜
  - `GET /leaderboard/weekly/` - 周排行榜
  - `GET /leaderboard/all-time/` - 总排行榜
  - `GET /leaderboard/user/{id}/` - 用户排名查询
  - `GET /streak/` - 用户连续打卡
  - `GET /history/` - 挑战历史
  - `POST /generate-tomorrow/` - 生成明日挑战（管理员）

---

### ✅ 健康检查模块
- **文件**: [health.md](./health.md)
- **基础路径**: `/api/health/`
- **端点数量**: 4
- **端点**:
  - `GET /` - 综合健康检查
  - `GET /db/` - 数据库状态
  - `GET /redis/` - Redis 状态
  - `GET /websocket/` - WebSocket 状态

---

### ✅ AI 引擎模块
- **文件**: [ai_engine.md](./ai_engine.md)
- **基础路径**: `/api/v1/ai/`
- **端点数量**: 10
- **端点**:
  - `GET /games/` - 获取 AI 对局列表
  - `POST /games/` - 创建 AI 对局
  - `GET /games/{id}/` - 获取 AI 对局详情
  - `PUT /games/{id}/` - 更新 AI 对局状态
  - `DELETE /games/{id}/` - 取消 AI 对局
  - `POST /games/{id}/move/` - 请求 AI 走棋
  - `POST /games/{id}/hint/` - 请求 AI 提示
  - `POST /games/{id}/analyze/` - 请求 AI 分析
  - `GET /difficulties/` - 获取难度列表
  - `GET /engines/status/` - 获取引擎状态

---

### ✅ 匹配系统模块
- **文件**: [matchmaking.md](./matchmaking.md)
- **基础路径**: `/api/v1/matchmaking/` 和 `/api/v1/ranking/`
- **端点数量**: 6
- **端点**:
  - `POST /start/` - 开始匹配
  - `POST /cancel/` - 取消匹配
  - `GET /status/` - 获取匹配状态
  - `GET /ranking/leaderboard/` - 天梯排行榜
  - `GET /ranking/user/{id}/` - 用户排名
  - `GET /ranking/user/` - 当前用户排名

---

### ✅ 用户模块
- **文件**: [users.md](./users.md)
- **基础路径**: `/api/v1/users/`
- **端点数量**: 8
- **端点**:
  - `GET /profile/` - 获取当前用户 Profile
  - `PUT /profile/` - 更新当前用户 Profile（全量）
  - `PATCH /profile/` - 更新当前用户 Profile（部分）
  - `GET /me/stats/` - 获取当前用户统计
  - `GET /{user_id}/` - 获取用户详情
  - `PUT /{user_id}/` - 更新用户信息（全量）
  - `PATCH /{user_id}/` - 更新用户信息（部分）
  - `PUT /{user_id}/password/` - 修改用户密码
  - `GET /{user_id}/stats/` - 获取用户统计
  - `GET /{user_id}/games/` - 获取用户对局历史

---

### ✅ 残局谜题模块
- **文件**: [puzzles.md](./puzzles.md)
- **基础路径**: `/api/v1/puzzles/`
- **端点数量**: 7
- **端点**:
  - `GET /` - 获取谜题列表
  - `GET /{puzzle_id}/` - 获取谜题详情
  - `POST /{puzzle_id}/attempt/` - 开始挑战
  - `POST /{puzzle_id}/attempts/{attempt_id}/move/` - 提交走法
  - `POST /{puzzle_id}/attempts/{attempt_id}/complete/` - 完成挑战
  - `GET /progress/` - 用户进度
  - `GET /leaderboard/` - 排行榜

---

## 📊 端点统计

| 模块 | 端点数量 | 公开端点 | 认证端点 |
|------|---------|---------|---------|
| 认证模块 | 5 | 3 | 2 |
| 用户模块 | 8 | 0 | 8 |
| 游戏对局模块 | 11 | 0 | 11 |
| 每日挑战模块 | 12 | 6 | 6 |
| AI 引擎模块 | 10 | 1 | 9 |
| 匹配系统模块 | 6 | 2 | 4 |
| 残局谜题模块 | 7 | 0 | 7 |
| 健康检查模块 | 4 | 4 | 0 |
| **总计** | **63** | **16** | **47** |

---

## 📖 文档结构

每个端点文档包含以下内容：

1. **端点概览表** - 快速查看所有端点
2. **详细端点说明** - 每个端点的完整文档
   - 请求方法
   - 请求路径
   - 认证要求
   - 请求参数
   - 请求示例
   - 响应示例（成功 + 错误）
   - 错误码说明
   - 字段说明
3. **数据模型** - 相关对象字段说明
4. **使用示例** - cURL、JavaScript、Python 等代码示例

---

## 🔗 相关文档

### 核心文档
- **完整 API 参考**: [../API-REFERENCE-COMPLETE.md](../API-REFERENCE-COMPLETE.md) - 完整 API 参考文档
- **错误码说明**: [../errors.md](../errors.md) - 完整错误码列表
- **WebSocket 文档**: [../websocket.md](../websocket.md) - 实时对战协议

### 项目文档
- **项目文档索引**: [../../README.md](../../README.md)
- **架构设计**: [../../architecture.md](../../architecture.md)
- **开发规范**: [../../DEVELOPMENT-CONSTRAINTS.md](../../DEVELOPMENT-CONSTRAINTS.md)

---

## 📝 更新日志

### 2026-03-06
- ✅ 新增：用户 API 端点文档（users.md）
- ✅ 新增：AI 引擎 API 端点文档（ai_engine.md）
- ✅ 新增：匹配系统 API 端点文档（matchmaking.md）
- ✅ 新增：残局谜题 API 端点文档（puzzles.md）
- ✅ 更新：完整 API 参考文档（API-REFERENCE-COMPLETE.md）
- ✅ 更新：端点文档索引（README.md）

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-06  
**维护者**: Chinese Chess Team
