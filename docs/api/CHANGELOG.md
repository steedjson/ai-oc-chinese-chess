# API 变更日志

**项目**: 中国象棋平台  
**版本**: v1.0.0  
**最后更新**: 2026-03-11

---

## [v1.0.0] - 2026-03-11

### 🎉 正式发布

这是中国象棋平台的第一个正式版本，包含完整的游戏功能、API 和 WebSocket 支持。

### ✨ 新增功能

#### 认证 API (`/api/v1/auth`)
- `POST /api/v1/auth/register/` - 用户注册
- `POST /api/v1/auth/login/` - 用户登录
- `POST /api/v1/auth/logout/` - 用户登出
- `POST /api/v1/auth/refresh/` - 刷新 Token
- `GET /api/v1/auth/me/` - 获取当前用户信息

#### 用户 API (`/api/v1/users`)
- `GET /api/v1/users/profile/` - 获取当前用户 Profile
- `PUT /api/v1/users/profile/` - 更新当前用户信息
- `PATCH /api/v1/users/profile/` - 部分更新用户信息
- `GET /api/v1/users/me/stats/` - 获取当前用户统计
- `GET /api/v1/users/{user_id}/` - 获取用户详情
- `PUT /api/v1/users/{user_id}/` - 更新用户信息
- `PUT /api/v1/users/{user_id}/password/` - 修改密码
- `GET /api/v1/users/{user_id}/stats/` - 获取用户统计
- `GET /api/v1/users/{user_id}/games/` - 获取用户对局历史

#### 游戏 API (`/api/v1/games`)
- `GET /api/v1/games/games/` - 获取游戏列表
- `POST /api/v1/games/games/` - 创建游戏
- `GET /api/v1/games/games/{game_id}/` - 获取游戏详情
- `POST /api/v1/games/games/{game_id}/move/` - 提交走棋
- `GET /api/v1/games/games/{game_id}/moves/` - 获取走棋历史
- `PUT /api/v1/games/games/{game_id}/status/` - 更新游戏状态
- `DELETE /api/v1/games/games/{game_id}/` - 取消游戏
- `GET /api/v1/games/users/{user_id}/games/` - 获取用户对局

#### 观战 API (`/api/v1/games`, `/api/v1/spectator`)
- `POST /api/v1/games/{game_id}/spectate/` - 加入观战
- `POST /api/v1/games/{game_id}/spectate/leave/` - 离开观战
- `GET /api/v1/games/{game_id}/spectators/` - 获取观战列表
- `POST /api/v1/games/{game_id}/spectators/kick/` - 踢出观战者
- `GET /api/v1/spectator/active-games/` - 获取可观看的对局
- `GET /api/v1/games/{game_id}/spectators/{spectator_id}/` - 获取观战者详情

#### 聊天 API (`/api/v1/chat`)
- `POST /api/v1/chat/games/{game_id}/send/` - 发送聊天消息
- `GET /api/v1/chat/games/{game_id}/history/` - 获取聊天历史
- `DELETE /api/v1/chat/messages/{message_uuid}/delete/` - 删除聊天消息
- `GET /api/v1/chat/games/{game_id}/stats/` - 获取聊天统计

#### 匹配 API (`/api/v1/matchmaking`)
- `POST /api/v1/matchmaking/start/` - 开始匹配
- `POST /api/v1/matchmaking/cancel/` - 取消匹配
- `GET /api/v1/matchmaking/status/` - 获取匹配状态

#### 排行榜 API (`/api/v1/ranking`)
- `GET /api/v1/ranking/leaderboard/` - 获取排行榜
- `GET /api/v1/ranking/user/{user_id}/` - 获取用户排名
- `GET /api/v1/ranking/user/` - 获取当前用户排名

#### AI API (`/api/v1/ai`)
- `GET /api/v1/ai/games/` - 获取 AI 对局列表
- `POST /api/v1/ai/games/` - 创建 AI 对局
- `GET /api/v1/ai/games/{game_id}/` - 获取 AI 对局详情
- `PUT /api/v1/ai/games/{game_id}/` - 更新 AI 对局状态
- `DELETE /api/v1/ai/games/{game_id}/` - 取消 AI 对局
- `POST /api/v1/ai/games/{game_id}/move/` - 请求 AI 走棋
- `POST /api/v1/ai/games/{game_id}/hint/` - 请求 AI 提示
- `POST /api/v1/ai/games/{game_id}/analyze/` - 请求 AI 分析
- `GET /api/v1/ai/difficulties/` - 获取难度列表
- `GET /api/v1/ai/engines/status/` - 获取引擎状态

#### 残局 API (`/api/v1/puzzles`)
- `GET /api/v1/puzzles/` - 获取关卡列表
- `GET /api/v1/puzzles/{puzzle_id}/` - 获取关卡详情
- `POST /api/v1/puzzles/{puzzle_id}/attempt/` - 创建挑战
- `POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/move/` - 提交走法
- `POST /api/v1/puzzles/{puzzle_id}/attempts/{attempt_id}/complete/` - 完成挑战
- `GET /api/v1/puzzles/progress/` - 获取用户进度
- `GET /api/v1/puzzles/leaderboard/` - 获取残局排行榜

#### 健康检查 API (`/api/v1/health`)
- `GET /api/v1/health/` - 健康检查

### 🔌 WebSocket 端点

#### 游戏对弈
- `/ws/game/{game_id}/` - 实时游戏对弈

#### AI 对弈
- `/ws/ai/game/{game_id}/` - 实时 AI 对弈

#### 匹配系统
- `/ws/matchmaking/` - 匹配队列实时更新

#### 观战系统
- `/ws/game/{game_id}/` - 观战模式

#### 聊天系统
- `/ws/chat/game/{game_id}/` - 对局内聊天
- `/ws/chat/spectator/{game_id}/` - 观战聊天

### 🔐 认证方式

本 API 使用 JWT (JSON Web Token) 进行认证：

**Token 类型**:
- `Access Token`: 有效期 2 小时，用于访问受保护资源
- `Refresh Token`: 有效期 7 天，用于刷新 Access Token

**请求头格式**:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**认证流程**:
1. 客户端调用登录/注册接口获取 Tokens
2. 在后续请求中携带 `Authorization: Bearer <access_token>`
3. Access Token 过期后使用 Refresh Token 刷新

### ❌ 错误码

标准化的错误码体系，涵盖：
- 认证相关错误 (VALIDATION_ERROR, TOKEN_INVALID, 等)
- 用户相关错误 (USER_NOT_FOUND, PERMISSION_DENIED, 等)
- 游戏相关错误 (GAME_NOT_FOUND, INVALID_MOVE, 等)
- 观战相关错误 (GAME_FINISHED, ALREADY_WATCHING, 等)
- 聊天相关错误 (RATE_LIMITED, CONTENT_TOO_LONG, 等)
- 匹配相关错误 (NOT_IN_QUEUE, QUEUE_FULL, 等)
- AI 相关错误 (INVALID_DIFFICULTY, AI_ERROR, 等)
- 残局相关错误 (PUZZLE_NOT_FOUND, ATTEMPT_NOT_FOUND, 等)
- 通用错误 (SERVER_ERROR, NOT_FOUND, 等)

详见: [错误码说明](error-codes.md)

### 📊 API 统计

**总端点数**: 55 个 REST API + 5 个 WebSocket 端点

**按模块分类**:
- 认证 API: 5 个端点
- 用户 API: 8 个端点
- 游戏 API: 8 个端点
- 观战 API: 6 个端点
- 聊天 API: 4 个端点
- 匹配 API: 3 个端点
- 排行榜 API: 3 个端点
- AI API: 10 个端点
- 残局 API: 7 个端点
- 健康检查: 1 个端点

**文档完整性**: 100%

---

## [v0.9.0-beta] - 2026-03-06

### ✨ 新增功能

#### 观战功能
- 实时观战对局
- 观战者列表
- 踢出观战者功能
- 观战聊天

#### 聊天系统
- 对局内聊天
- 观战聊天
- 24 种表情支持
- 消息限流（2秒间隔）

#### 棋盘动画
- 走棋动画
- 吃子特效
- 将军提示
- 胜利高亮

### 🔧 问题修复

- 修复个人中心 Mock 数据问题
- 优化 WebSocket 断线重连
- 添加后端服务状态检测

---

## [v0.8.0-beta] - 2026-03-05

### ✨ 新增功能

#### 游戏核心系统
- 完整的象棋规则引擎
- FEN 格式支持
- 走棋验证
- 将军检测
- 走棋历史记录

#### AI 对弈系统
- Stockfish 16 引擎集成
- 10 个难度等级
- AI 走棋建议
- AI 局势分析

#### 匹配系统
- ELO 积分系统
- 快速匹配
- 天梯排行榜
- 好友对战

### 🔧 问题修复

- 修复 WebSocket 路由问题
- 修复数据库异步访问问题
- 优化 Token 刷新机制

---

## [v0.7.0-beta] - 2026-03-04

### ✨ 新增功能

#### 用户认证系统
- 用户注册/登录
- JWT Token 认证
- 用户 Profile 管理
- 密码修改

#### 游戏对局 API
- 创建对局
- 提交走棋
- 获取对局详情
- 对局状态管理

### 🔧 问题修复

- 修复跨域问题
- 优化数据库查询
- 添加请求限流

---

## [v0.6.0-alpha] - 2026-03-03

### ✨ 初始版本

- 基础项目架构
- Django REST Framework 配置
- PostgreSQL 数据库
- Redis 缓存
- WebSocket 支持 (Django Channels)

---

## 版本命名规则

- **主版本号**: 重大架构变更或不兼容的 API 变更
- **次版本号**: 新增功能、向后兼容的 API 变更
- **修订号**: Bug 修复、文档更新
- **后缀**:
  - `alpha`: 内部测试版本
  - `beta`: 公开测试版本
  - `rc`: 候选发布版本
  - 无后缀: 正式发布版本

---

## 即将推出

### v1.1.0 (计划中)

- 🎮 每日挑战系统
- 🏆 锦标赛模式
- 📊 深度数据分析
- 🎨 更多棋盘主题

### v1.2.0 (计划中)

- 🤝 团队对战
- 📱 移动端 App
- 🎬 对局回放视频
- 🌐 多语言支持

---

## API 策略

### 兼容性承诺

- v1.x 版本将保持向后兼容
- 弃用的 API 将至少保留 2 个次版本
- 重大变更将在主版本号变更时进行

### 废弃策略

1. 在文档中标记为 `Deprecated`
2. 在响应头中添加 `Warning: Deprecated` 头
3. 发布替代 API
4. 至少 2 个次版本后移除

### 通知渠道

- API 变更日志 (本文件)
- 邮件通知（订阅用户）
- 开发者文档更新
- GitHub Release Notes

---

**维护者**: 小屁孩（御姐模式）  
**最后更新**: 2026-03-11