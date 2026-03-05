# 📚 中国象棋项目 - 共享上下文

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**状态**：🔄 更新中  
**维护者**：所有参与开发的 Agent

---

## ⚠️ 使用说明

**所有 Agent 在开始任务前必须阅读此文档**，避免重复定义和冲突。

**任务完成后必须更新此文档**，记录新增的内容。

**更新格式**：
```markdown
## 更新时间：2026-03-03 10:00
- 添加：XXX
- 修改：XXX
- 删除：XXX
```

---

## 📋 文档状态总览

| 文档 | 状态 | 最后更新 | 负责人 |
|------|------|---------|--------|
| docs/requirements.md | ✅ 完成 | 2026-03-03 09:09 | planner agent |
| docs/architecture.md | ✅ 完成 | 2026-03-03 09:22 | architect agent |
| docs/tech-stack-evaluation.md | ✅ 完成 | 2026-03-03 09:31 | architect agent |
| docs/features/user-auth-plan.md | ✅ 完成 | 2026-03-03 09:40 | planner agent |
| docs/features/game-core-plan.md | ✅ 完成 | 2026-03-03 10:01 | planner agent |
| docs/features/ai-opponent-plan.md | ✅ 完成 | 2026-03-03 11:50 | planner agent |
| docs/features/matchmaking-plan.md | ✅ 完成 | 2026-03-03 13:25 | planner agent |

---

## 📝 更新日志

### 2026-03-03 13:27 - 5.4 匹配系统完成更新
- 添加：5.4 匹配系统完整 API（7 个接口）
- 添加：5.4 数据库表（match_queues, match_history, player_ranks, seasons）
- 添加：Elo 等级分系统详情（玩家段位系统）
- 添加：匹配算法说明
- 标记：阶段 5 核心后端全部完成

### 2026-03-03 12:45 - 阶段 5.3/5.4 完成更新
- 添加：5.3 AI 对弈系统 API 和模型
- 添加：5.4 匹配系统 API 和模型
- 添加：Elo 系统说明（AI 难度 vs 玩家等级分）

### 2026-03-03 09:55 - 初始版本
- 创建共享上下文文档
- 记录已完成的需求/架构/技术选型文档
- 记录 user-auth-plan.md 已定义的 API 和数据库表
- 标记待定义的 API 和数据库表

---

## 🔐 已定义的 API

### 用户认证模块 (user-auth-plan.md)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/auth/register` | 用户注册 | ✅ 已定义 |
| `POST` | `/api/v1/auth/login` | 用户登录 | ✅ 已定义 |
| `POST` | `/api/v1/auth/logout` | 用户登出 | ✅ 已定义 |
| `POST` | `/api/v1/auth/refresh` | 刷新 Token | ✅ 已定义 |
| `GET` | `/api/v1/auth/me` | 获取当前用户信息 | ✅ 已定义 |
| `PUT` | `/api/v1/users/:id` | 更新用户信息 | ✅ 已定义 |
| `PUT` | `/api/v1/users/:id/password` | 修改密码 | ✅ 已定义 |

---

## 🗄️ 已定义的数据库表

### users (用户表)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(512) NULL,
    elo_rating      INTEGER DEFAULT 1500,
    status          VARCHAR(20) DEFAULT 'active',
    is_verified     BOOLEAN DEFAULT false,
    last_login_at   TIMESTAMP WITH TIME ZONE NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at      TIMESTAMP WITH TIME ZONE NULL
);

-- 索引
CREATE UNIQUE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_elo ON users(elo_rating DESC);
CREATE INDEX idx_users_status ON users(status);
```

### user_profiles (用户档案表)

```sql
CREATE TABLE user_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bio             TEXT NULL,
    location        VARCHAR(100) NULL,
    birthday        DATE NULL,
    gender          VARCHAR(20) NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE UNIQUE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### user_stats (用户统计表)

```sql
CREATE TABLE user_stats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_games     INTEGER DEFAULT 0,
    wins            INTEGER DEFAULT 0,
    losses          INTEGER DEFAULT 0,
    draws           INTEGER DEFAULT 0,
    win_rate        DECIMAL(5,2) DEFAULT 0,
    favorite_opening VARCHAR(100) NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE UNIQUE INDEX idx_user_stats_user_id ON user_stats(user_id);
```

---

## 🔌 已定义的 WebSocket 事件

### 认证模块

| 事件类型 | 方向 | 说明 | 状态 |
|---------|------|------|------|
| `AUTH_REQUEST` | C→S | 客户端认证请求 | ✅ 已定义 |
| `AUTH_RESPONSE` | S→C | 服务端认证响应 | ✅ 已定义 |
| `TOKEN_REFRESH` | C→S | Token 刷新请求 | ✅ 已定义 |

---

## 🎯 待定义的 API

### 游戏对局模块 (game-core-plan.md)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/games` | 创建新对局 | ⏳ 待定义 |
| `GET` | `/api/v1/games/:id` | 获取对局详情 | ⏳ 待定义 |
| `GET` | `/api/v1/games/:id/moves` | 获取走棋历史 | ⏳ 待定义 |
| `POST` | `/api/v1/games/:id/moves` | 提交走棋 | ⏳ 待定义 |
| `PUT` | `/api/v1/games/:id/status` | 更新对局状态 | ⏳ 待定义 |
| `DELETE` | `/api/v1/games/:id` | 取消对局 | ⏳ 待定义 |
| `GET` | `/api/v1/users/:id/games` | 获取用户对局列表 | ⏳ 待定义 |

### AI 对弈模块 (ai-opponent-plan.md)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/ai/games` | 创建 AI 对局 | ⏳ 待定义 |
| `PUT` | `/api/v1/ai/games/:id/difficulty` | 设置 AI 难度 | ⏳ 待定义 |
| `POST` | `/api/v1/ai/games/:id/hint` | 请求 AI 提示 | ⏳ 待定义 |
| `POST` | `/api/v1/ai/games/:id/analyze` | 请求棋局分析 | ⏳ 待定义 |

### 匹配系统模块 (matchmaking-plan.md)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/matchmaking/queue` | 加入匹配队列 | ⏳ 待定义 |
| `DELETE` | `/api/v1/matchmaking/queue` | 退出匹配队列 | ⏳ 待定义 |
| `GET` | `/api/v1/matchmaking/status` | 获取匹配状态 | ⏳ 待定义 |
| `GET` | `/api/v1/matchmaking/estimate` | 获取预估等待时间 | ⏳ 待定义 |

---

## 🗄️ 待定义的数据库表

### 游戏对局模块

```sql
-- 待定义：games, game_moves, game_players
```

### AI 对弈模块

```sql
-- 待定义：ai_games, ai_difficulty_levels
```

### 匹配系统模块

```sql
-- 待定义：match_queues, match_history
```

---

## 🔐 已定义的 API（阶段 5.3/5.4 新增）

### AI 对弈模块 (ai-opponent-plan.md) - ✅ 已完成

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/ai/games` | 创建 AI 对局 | ✅ 已实现 |
| `GET` | `/api/v1/ai/games/:id` | 获取 AI 对局详情 | ✅ 已实现 |
| `PUT` | `/api/v1/ai/games/:id/difficulty` | 设置 AI 难度 | ✅ 已实现 |
| `POST` | `/api/v1/ai/games/:id/move` | 请求 AI 走棋 | ✅ 已实现 |
| `POST` | `/api/v1/ai/games/:id/hint` | 请求走棋提示 | ✅ 已实现 |
| `POST` | `/api/v1/ai/games/:id/analyze` | 请求棋局分析 | ✅ 已实现 |
| `GET` | `/api/v1/ai/engines/status` | 获取引擎状态 | ✅ 已实现 |

### 匹配系统模块 (matchmaking-plan.md) - 🔄 进行中

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| `POST` | `/api/v1/matchmaking/queue` | 加入匹配队列 | 🔄 实现中 |
| `DELETE` | `/api/v1/matchmaking/queue` | 退出匹配队列 | 🔄 实现中 |
| `GET` | `/api/v1/matchmaking/status` | 获取匹配状态 | 🔄 实现中 |
| `GET` | `/api/v1/matchmaking/estimate` | 获取预估等待时间 | 🔄 实现中 |
| `GET` | `/api/v1/matchmaking/history` | 获取匹配历史 | 🔄 实现中 |
| `GET` | `/api/v1/rankings/leaderboard` | 获取排行榜 | 🔄 实现中 |
| `GET` | `/api/v1/rankings/:user_id` | 获取用户段位 | 🔄 实现中 |

---

## 🗄️ 已定义的数据库表（阶段 5.3/5.4 新增）

### AI 对弈模块

```sql
-- AI 对局表
CREATE TABLE ai_games (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    difficulty_id   UUID NOT NULL REFERENCES ai_difficulties(id),
    game_id         UUID NOT NULL REFERENCES games(id),
    status          VARCHAR(20) DEFAULT 'playing',
    analysis_result JSONB NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI 难度配置表
CREATE TABLE ai_difficulties (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level           INTEGER NOT NULL UNIQUE,  -- 1-10
    name            VARCHAR(50) NOT NULL,     -- 入门/新手/.../大师
    elo_estimate    INTEGER NOT NULL,         -- 400-2200
    skill_level     INTEGER NOT NULL,         -- Stockfish skill level 0-20
    search_depth    INTEGER NOT NULL,
    think_time_ms   INTEGER NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 匹配系统模块

```sql
-- 玩家段位表
CREATE TABLE player_ranks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL UNIQUE REFERENCES users(id),
    rating          INTEGER NOT NULL DEFAULT 1500,  -- Elo 分数
    rank            VARCHAR(20) NOT NULL DEFAULT 'bronze',  -- 段位
    season          INTEGER NOT NULL,
    games_played    INTEGER DEFAULT 0,
    wins            INTEGER DEFAULT 0,
    losses          INTEGER DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 匹配历史表
CREATE TABLE match_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    white_player_id UUID NOT NULL REFERENCES users(id),
    black_player_id UUID NOT NULL REFERENCES users(id),
    game_id         UUID NOT NULL REFERENCES games(id),
    white_rating_before INTEGER NOT NULL,
    black_rating_before INTEGER NOT NULL,
    white_rating_after  INTEGER NOT NULL,
    black_rating_after  INTEGER NOT NULL,
    result          VARCHAR(20) NOT NULL,  -- white_win/black_win/draw
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 📦 已定义的枚举值

### UserStatus

```python
class UserStatus(models.TextChoices):
    ACTIVE = 'active', '活跃'
    INACTIVE = 'inactive', '不活跃'
    BANNED = 'banned', '已封禁'
```

### GameStatus

```python
class GameStatus(models.TextChoices):
    PENDING = 'pending', '等待开始'
    PLAYING = 'playing', '进行中'
    WHITE_WIN = 'white_win', '红方胜'
    BLACK_WIN = 'black_win', '黑方胜'
    DRAW = 'draw', '和棋'
    ABORTED = 'aborted', '已取消'
```

### AIGameStatus

```python
class AIGameStatus(models.TextChoices):
    WAITING = 'waiting', '等待开始'
    PLAYING = 'playing', '进行中'
    FINISHED = 'finished', '已结束'
    ANALYZING = 'analyzing', '分析中'
```

### RankSegment (玩家段位)

```python
class RankSegment(models.TextChoices):
    BRONZE = 'bronze', '青铜'      # 0-1000
    SILVER = 'silver', '白银'      # 1001-1200
    GOLD = 'gold', '黄金'          # 1201-1400
    PLATINUM = 'platinum', '铂金'  # 1401-1600
    DIAMOND = 'diamond', '钻石'    # 1601-1800
    MASTER = 'master', '大师'      # 1801+
```

---

## 🔑 已定义的错误码

### 认证模块 (AUTH_*)

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `AUTH_INVALID_CREDENTIALS` | 401 | 账号或密码错误 |
| `AUTH_TOKEN_EXPIRED` | 401 | Token 已过期 |
| `AUTH_TOKEN_INVALID` | 401 | Token 无效 |
| `AUTH_USER_NOT_FOUND` | 404 | 用户不存在 |
| `AUTH_EMAIL_EXISTS` | 409 | 邮箱已被注册 |
| `AUTH_USERNAME_EXISTS` | 409 | 用户名已被注册 |

### 用户模块 (USER_*)

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `USER_NOT_FOUND` | 404 | 用户不存在 |
| `USER_INVALID_ID` | 400 | 用户 ID 无效 |
| `USER_UPDATE_FAILED` | 500 | 用户信息更新失败 |

---

## 📝 更新日志

### 2026-03-03 12:33 - 匹配系统核心功能实现完成
- **添加**: 匹配系统核心模块（TDD 方法）
  - Elo 等级分系统（K 因子、预期胜率、分数更新）
  - 匹配队列管理（Redis Sorted Set 实现）
  - 匹配算法（动态搜索范围、防止重复匹配）
  - Django 模型（MatchQueue, MatchHistory, PlayerRank, Season）
  - 段位系统（青铜/白银/黄金/铂金/钻石/大师）
  - 等级分排行榜（Redis 实现）
- **添加**: 匹配系统数据库模型
  - `match_queues` - 匹配队列表
  - `match_history` - 匹配历史表
  - `player_ranks` - 玩家段位表
  - `seasons` - 赛季配置表
- **添加**: 匹配系统配置
  - `MATCHMAKING_TIMEOUT = 180` - 3 分钟超时
  - `MATCHMAKING_INITIAL_RANGE = 100` - 初始搜索范围
  - `MATCHMAKING_EXPANSION = 50` - 每次扩大范围
  - `MATCHMAKING_MAX_RANGE = 300` - 最大搜索范围
  - `MATCHMAKING_EXPANSION_INTERVAL = 30` - 扩大间隔
- **更新**: `docs/features/matchmaking-plan.md` 核心功能状态为 ✅ 完成
- **测试**: 88 个单元测试，100% 通过
- **待完成**: API 接口、WebSocket 支持、集成测试

### 2026-03-03 12:00 - AI 对弈系统实现完成
- **添加**: AI 对弈模块完整实现（TDD 方法）
  - Stockfish 16 引擎集成
  - 10 级难度设计（400-2200 Elo）
  - AI 服务模块（AIService, EnginePool, GameAnalyzer）
  - API 接口（/api/v1/ai/*）
  - Django 模型（AIDifficulty, AIGame, AIAnalysis）
  - WebSocket 支持（/ws/ai/game/{game_id}/）
  - Celery 异步任务
- **添加**: AI 引擎 API 接口
  - `POST /api/v1/ai/games/` - 创建 AI 对局
  - `GET /api/v1/ai/games/:id/` - 获取 AI 对局详情
  - `POST /api/v1/ai/games/:id/move/` - 请求 AI 走棋
  - `POST /api/v1/ai/games/:id/hint/` - 请求走棋提示
  - `POST /api/v1/ai/games/:id/analyze/` - 请求棋局分析
  - `GET /api/v1/ai/difficulties/` - 获取难度列表
  - `GET /api/v1/ai/engines/status/` - 获取引擎状态
- **添加**: AI 数据库模型
  - `ai_difficulties` - 难度配置表
  - `ai_games` - AI 对局记录表
  - `ai_analyses` - 棋局分析结果表
- **添加**: AI WebSocket 事件
  - `ai_thinking` - AI 思考中通知
  - `ai_move` - AI 走棋完成
  - `ai_hint` - AI 提示返回
  - `ai_analysis` - 分析结果推送
- **更新**: `docs/features/ai-opponent-plan.md` 状态为 ✅ 完成
- **测试**: 47 个单元测试（24 个已验证通过）

### 2026-03-03 09:55 - 初始版本
- 创建共享上下文文档
- 记录已完成的需求/架构/技术选型文档
- 记录 user-auth-plan.md 已定义的 API 和数据库表
- 标记待定义的 API 和数据库表

---

## 🚨 冲突检测

**当前无冲突**

如发现冲突，请立即在下方记录：

```markdown
### 冲突记录

**发现时间**：2026-03-03 XX:XX
**冲突内容**：XXX
**涉及文档**：XXX
**解决方案**：XXX
**解决者**：XXX
```

---

---

## 🧠 Elo 系统说明

### AI Elo vs 玩家 Elo

| 对比 | AI Elo（难度） | 玩家 Elo（等级分） |
|------|---------------|------------------|
| **用途** | AI 难度配置 | 玩家实力评估 |
| **位置** | `ai_engine/config.py` | `matchmaking/elo.py` |
| **类型** | 固定值 | 动态计算 |
| **范围** | 400-2200（10 级） | 0-3000（动态） |
| **更新** | 不变 | 每局后更新 |
| **公式** | 无 | Elo 标准公式 |

### AI 难度等级（固定）

| 等级 | Elo | 名称 |
|------|-----|------|
| 1 | 400 | 入门 |
| 2 | 600 | 新手 |
| 3 | 800 | 初级 |
| 4 | 1000 | 业余 |
| 5 | 1200 | 中级 |
| 6 | 1400 | 进阶 |
| 7 | 1600 | 高级 |
| 8 | 1800 | 专家 |
| 9 | 2000 | 大师 |
| 10 | 2200 | 特级大师 |

### 玩家段位系统（动态）

| 段位 | Elo 范围 |
|------|---------|
| 青铜 | 0-1000 |
| 白银 | 1001-1200 |
| 黄金 | 1201-1400 |
| 铂金 | 1401-1600 |
| 钻石 | 1601-1800 |
| 大师 | 1801+ |

### Elo 计算公式

```python
# 预期胜率
E = 1 / (1 + 10^((R_opponent - R_player) / 400))

# 分数变化
ΔR = K * (S - E)
其中:
    K = 32（K 因子）
    S = 实际得分（1=胜，0.5=和，0=负）
    E = 预期得分
```

---

**所有 Agent 请注意：开始任务前请先阅读此文档，完成后请更新此文档！**
