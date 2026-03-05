# 📋 中国象棋项目 - 开发约束规范

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**状态**：✅ 生效中  
**适用范围**：所有并行开发的 Agent

---

## ⚠️ 重要说明

**所有参与本项目开发的 Agent 必须严格遵守本规范**，以确保多 Agent 并行开发时的一致性。

**启动任务时必须引用**：
```
参考 docs/DEVELOPMENT-CONSTRAINTS.md 和 docs/SHARED-CONTEXT.md
```

---

## 1. 命名规范

### 1.1 变量/字段命名

| 类型 | 规范 | 示例 |
|------|------|------|
| **变量/字段** | camelCase | `userId`, `createdAt`, `gameStatus` |
| **常量** | UPPER_SNAKE_CASE | `MAX_PLAYERS`, `DEFAULT_ELO` |
| **类名** | PascalCase | `UserService`, `GameRepository` |
| **数据库表** | snake_case 复数 | `users`, `games`, `match_history` |
| **数据库字段** | snake_case | `user_id`, `created_at`, `game_status` |
| **API 路径** | kebab-case 复数 | `/api/users`, `/api/game-moves` |
| **文件/目录** | kebab-case | `user-auth-plan.md`, `game-core/` |

### 1.2 统一字段命名

| 含义 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 主键 | `id` | UUID | 所有表统一使用 UUID |
| 用户 ID | `userId` / `user_id` | UUID | JS 用 camelCase，DB 用 snake_case |
| 游戏 ID | `gameId` / `game_id` | UUID | 同上 |
| 创建时间 | `createdAt` / `created_at` | datetime | ISO 8601 格式 |
| 更新时间 | `updatedAt` / `updated_at` | datetime | ISO 8601 格式 |
| 删除时间 | `deletedAt` / `deleted_at` | datetime | 软删除用 |
| 状态 | `status` | string/enum | 统一用枚举值 |

---

## 2. API 设计规范

### 2.1 RESTful 规范

```
基础路径：/api/v1/

资源路径：
- /api/v1/users          # 用户资源
- /api/v1/games          # 游戏资源
- /api/v1/matches        # 匹配资源
- /api/v1/boards         # 棋盘资源
- /api/v1/rankings       # 排名资源
- /api/v1/tutorials      # 教程资源
- /api/v1/social         # 社交资源
- /api/v1/admin          # 管理资源
```

### 2.2 HTTP 方法

| 方法 | 用途 | 示例 |
|------|------|------|
| `GET` | 查询资源 | `GET /api/v1/users/:id` |
| `POST` | 创建资源 | `POST /api/v1/users` |
| `PUT` | 全量更新 | `PUT /api/v1/users/:id` |
| `PATCH` | 部分更新 | `PATCH /api/v1/users/:id` |
| `DELETE` | 删除资源 | `DELETE /api/v1/users/:id` |

### 2.3 响应格式

**成功响应**：
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2026-03-03T10:00:00Z"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "用户不存在",
    "details": { "userId": "xxx" }
  },
  "timestamp": "2026-03-03T10:00:00Z"
}
```

**分页响应**：
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  },
  "timestamp": "2026-03-03T10:00:00Z"
}
```

### 2.4 状态码规范

| 状态码 | 用途 |
|--------|------|
| `200` | 成功 |
| `201` | 创建成功 |
| `204` | 删除成功（无内容） |
| `400` | 请求参数错误 |
| `401` | 未认证 |
| `403` | 无权限 |
| `404` | 资源不存在 |
| `409` | 资源冲突 |
| `422` | 验证失败 |
| `429` | 请求限流 |
| `500` | 服务器错误 |

### 2.5 错误码规范

```
格式：{MODULE}_{ERROR_TYPE}

模块前缀：
- AUTH_      # 认证模块
- USER_      # 用户模块
- GAME_      # 游戏模块
- MATCH_     # 匹配模块
- BOARD_     # 棋盘模块
- RANK_      # 排名模块
- TUTORIAL_  # 教程模块
- SOCIAL_    # 社交模块
- ADMIN_     # 管理模块
```

---

## 3. 数据库设计规范

### 3.1 表命名

```
规则：复数形式 + snake_case

示例：
- users          # 用户表
- games          # 游戏对局表
- game_moves     # 走棋记录表
- match_queues   # 匹配队列表
- rankings       # 排名表
- tutorials      # 教程表
- user_achievements  # 用户成就表
```

### 3.2 字段规范

**所有表必须包含**：
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
deleted_at      TIMESTAMP WITH TIME ZONE NULL  -- 软删除
```

**外键命名**：
```sql
{table}_id    -- 例如：user_id, game_id
```

**布尔字段**：
```sql
is_active     BOOLEAN DEFAULT true
is_verified   BOOLEAN DEFAULT false
```

### 3.3 索引规范

```sql
-- 外键字段必须加索引
CREATE INDEX idx_games_white_player ON games(white_player_id);

-- 查询频繁字段加索引
CREATE INDEX idx_games_status ON games(status);

-- 组合索引（按查询顺序）
CREATE INDEX idx_games_status_created ON games(status, created_at);

-- 唯一索引
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
```

### 3.4 枚举值规范

**游戏状态**：
```python
class GameStatus(models.TextChoices):
    PENDING = 'pending', '等待开始'
    PLAYING = 'playing', '进行中'
    WHITE_WIN = 'white_win', '红方胜'
    BLACK_WIN = 'black_win', '黑方胜'
    DRAW = 'draw', '和棋'
    ABORTED = 'aborted', '已取消'
```

**用户状态**：
```python
class UserStatus(models.TextChoices):
    ACTIVE = 'active', '活跃'
    INACTIVE = 'inactive', '不活跃'
    BANNED = 'banned', '已封禁'
```

---

## 4. WebSocket 规范

### 4.1 连接路径

```
基础路径：/ws/

路由：
- /ws/game/{game_id}/        # 游戏房间
- /ws/chat/{room_id}/        # 聊天室
- /ws/matchmaking/           # 匹配队列
```

### 4.2 消息格式

**客户端 → 服务端**：
```json
{
  "type": "MOVE",
  "payload": {
    "from": "e2",
    "to": "e4",
    "promotion": "queen"
  },
  "timestamp": "2026-03-03T10:00:00Z"
}
```

**服务端 → 客户端**：
```json
{
  "type": "MOVE_RESULT",
  "payload": {
    "success": true,
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "lastMove": { "from": "e2", "to": "e4" }
  },
  "timestamp": "2026-03-03T10:00:00Z"
}
```

### 4.3 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `JOIN` | C→S | 加入房间 |
| `LEAVE` | C→S | 离开房间 |
| `MOVE` | C→S | 走棋 |
| `CHAT` | C→S | 聊天消息 |
| `HEARTBEAT` | 双向 | 心跳 |
| `JOIN_RESULT` | S→C | 加入结果 |
| `MOVE_RESULT` | S→C | 走棋结果 |
| `GAME_STATE` | S→C | 游戏状态 |
| `ERROR` | S→C | 错误消息 |

---

## 5. 安全规范

### 5.1 认证授权

- **JWT Token**：所有 API 必须验证 JWT
- **Token 有效期**：Access Token 24h，Refresh Token 7d
- **密码加密**：bcrypt，cost=12
- **敏感操作**：需要二次验证

### 5.2 输入验证

```python
# 必须验证所有用户输入
from rest_framework import serializers

class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128)
    username = serializers.CharField(min_length=3, max_length=50)
```

### 5.3 SQL 注入防护

- ✅ 使用 Django ORM
- ✅ 参数化查询
- ❌ 禁止字符串拼接 SQL

### 5.4 XSS 防护

- ✅ 前端转义所有用户输入
- ✅ 使用 Content-Security-Policy
- ❌ 禁止 dangerouslySetInnerHTML

---

## 6. 测试规范

### 6.1 测试文件命名

```
规则：{文件名}.test.{扩展名}

示例：
- user.service.test.ts
- auth.api.test.ts
- game.repository.test.py
```

### 6.2 测试目录结构

```
tests/
├── unit/           # 单元测试
├── integration/    # 集成测试
├── e2e/           # 端到端测试
└── fixtures/      # 测试数据
```

### 6.3 测试覆盖率要求

| 模块 | 覆盖率要求 |
|------|-----------|
| 核心业务逻辑 | ≥90% |
| API 接口 | ≥80% |
| 工具函数 | ≥95% |
| UI 组件 | ≥70% |

---

## 7. 文档规范

### 7.1 功能规划文档结构

```markdown
# 功能名称

## 1. 功能概述
## 2. 用户故事
## 3. API 设计
## 4. 数据库设计
## 5. 实现步骤
## 6. 测试计划
## 7. 验收标准
```

### 7.2 代码注释规范

```python
# 函数必须有文档字符串
def create_game(white_player_id: UUID, black_player_id: UUID) -> Game:
    """
    创建新游戏对局
    
    Args:
        white_player_id: 红方玩家 ID
        black_player_id: 黑方玩家 ID
    
    Returns:
        Game: 创建的游戏对象
    
    Raises:
        ValidationError: 玩家 ID 无效
        GameExistsError: 游戏已存在
    """
    pass
```

---

## 8. Git 规范

### 8.1 分支命名

```
main              # 主分支
develop           # 开发分支
feature/{name}    # 功能分支
bugfix/{name}     # 修复分支
release/{version} # 发布分支
```

### 8.2 Commit 信息格式

```
<type>(<scope>): <subject>

type: feat|fix|docs|style|refactor|test|chore
scope: auth|game|match|board|user|admin
subject: 简短描述

示例：
feat(game): 实现走棋规则验证
fix(auth): 修复 JWT 过期时间计算错误
```

---

## 9. 性能规范

### 9.1 API 响应时间

| 类型 | 要求 |
|------|------|
| 简单查询 | <100ms |
| 复杂查询 | <500ms |
| 写操作 | <200ms |
| WebSocket 延迟 | <50ms |

### 9.2 缓存策略

```python
# 必须缓存的数据
- 用户信息：TTL 5min
- 游戏状态：TTL 30min
- 排名列表：TTL 1min
- 配置信息：TTL 1h
```

---

## 10. 日志规范

### 10.1 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 正常流程 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

### 10.2 日志格式

```json
{
  "timestamp": "2026-03-03T10:00:00Z",
  "level": "INFO",
  "module": "game.service",
  "action": "create_game",
  "userId": "xxx",
  "gameId": "yyy",
  "message": "游戏创建成功",
  "duration": 45
}
```

---

## 📝 更新记录

| 版本 | 日期 | 更新内容 | 更新者 |
|------|------|---------|--------|
| v1.0 | 2026-03-03 | 初始版本 | planner agent |

---

**所有 Agent 必须遵守本规范，违反规范的代码/文档将被要求返工！**
