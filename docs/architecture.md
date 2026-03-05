# 🏗️ 中国象棋项目 - 系统架构设计文档

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**最后更新**：2026-03-03  
**状态**：初稿  
**作者**：architect agent

---

## 1. 系统整体架构图（分层架构）

### 1.1 分层架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           客户端层 (Client Layer)                        │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │   用户端 (Web/Mobile)│  │   后台管理端 (Web)   │  │  移动端响应式    │ │
│  │   React + Vite      │  │   React + Vite      │  │  适配           │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           网关层 (Gateway Layer)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Nginx 反向代理 + 负载均衡                      │   │
│  │         SSL 终止 / 静态资源缓存 / 请求路由 / 限流                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────┐           ┌─────────────────────────────────┐
│     API 服务层           │           │      WebSocket 服务层            │
│   (RESTful API)         │           │    (Django Channels)            │
│  ┌───────────────────┐  │           │  ┌───────────────────────────┐  │
│  │  Django REST API  │  │           │  │  Channels Router          │  │
│  │  - 用户认证        │  │           │  │  - 游戏房间 Consumer       │  │
│  │  - 棋局管理        │  │           │  │  - 聊天 Consumer          │  │
│  │  - 排名查询        │  │           │  │  - 匹配 Consumer          │  │
│  │  - 数据统计        │  │           │  └───────────────────────────┘  │
│  └───────────────────┘  │           └─────────────────────────────────┘
└─────────────────────────┘                          │
                    │                                │
                    └───────────────┬────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         业务逻辑层 (Business Logic Layer)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ 用户服务     │  │ 游戏服务     │  │ 匹配服务     │  │  AI 引擎服务   │  │
│  │ UserService │  │ GameService │  │MatchService │  │ StockfishSvc  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ 棋局服务     │  │ 排名服务     │  │ 教程服务     │  │  社交服务      │  │
│  │BoardService │  │RankService  │  │TutorialSvc  │  │  SocialSvc    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据访问层 (Data Access Layer)                   │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │   ORM (Django)      │  │   Redis Client      │  │  File Storage   │ │
│  │   - Django ORM      │  │   - Cache           │  │  - 棋局文件      │ │
│  │   - 参数化查询       │  │   - Session         │  │  - 头像文件      │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          存储层 (Storage Layer)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ PostgreSQL  │  │   Redis     │  │  MinIO/S3   │  │  本地文件系统  │  │
│  │ 主数据库      │  │ 缓存/队列    │  │ 对象存储     │  │  - 日志文件    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 架构设计原则

| 原则 | 描述 | 实现方式 |
|------|------|---------|
| **分层解耦** | 各层职责清晰，层间依赖单向 | 严格遵循分层架构，禁止跨层调用 |
| **高内聚低耦合** | 模块内部高度聚合，模块间松耦合 | 基于领域驱动设计 (DDD) 划分模块 |
| **单一职责** | 每个模块/服务只负责一个职责 | 细化服务粒度，避免上帝类 |
| **可扩展性** | 支持水平扩展和性能优化 | 无状态服务设计，支持容器化部署 |
| **高可用性** | 关键组件冗余，故障自动恢复 | 数据库主从、Redis 哨兵、服务健康检查 |
| **安全性** | 数据加密、访问控制、审计日志 | HTTPS、JWT、RBAC、SQL 注入防护 |

---

## 2. 技术架构设计

### 2.1 前端技术栈

#### 2.1.1 用户端 (User Frontend)

| 技术 | 选型 | 理由 |
|------|------|------|
| **框架** | React 18 + TypeScript | 生态丰富、类型安全、组件化 |
| **构建工具** | Vite | 快速开发、热更新、生产优化 |
| **状态管理** | Zustand | 轻量、简洁、TypeScript 友好 |
| **路由** | React Router v6 | 官方推荐、支持嵌套路由 |
| **UI 组件库** | Ant Design / MUI | 组件丰富、文档完善 |
| **样式方案** | Tailwind CSS + CSS Modules | 原子化 CSS、局部作用域 |
| **HTTP 客户端** | Axios + React Query | 请求拦截、缓存、重试机制 |
| **WebSocket 客户端** | native WebSocket + 重连机制 | 轻量、可控性强 |
| **棋盘渲染** | SVG + CSS Animation | 矢量图清晰、动画流畅 |
| **响应式适配** | CSS Grid + Media Queries | 移动端优先、自适应布局 |

#### 2.1.2 后台管理端 (Admin Frontend)

| 技术 | 选型 | 理由 |
|------|------|------|
| **框架** | React 18 + TypeScript | 与用户端技术栈统一 |
| **构建工具** | Vite | 快速开发、代码复用 |
| **状态管理** | Zustand | 轻量简洁 |
| **UI 组件库** | Ant Design Pro | 企业级后台模板、组件丰富 |
| **图表库** | ECharts / Recharts | 数据可视化、图表丰富 |
| **表格组件** | Ant Design Table | 分页、排序、筛选 |

### 2.2 后端技术栈

| 组件 | 技术选型 | 版本 | 理由 |
|------|---------|------|------|
| **Web 框架** | Django | 5.x | 成熟稳定、生态完善、自带 Admin |
| **API 框架** | Django REST Framework | 3.14+ | 序列化、认证、权限完善 |
| **WebSocket** | Django Channels | 4.x | 与 Django 深度集成、异步支持 |
| **ASGI 服务器** | Daphne / Uvicorn | 最新 | 异步高性能 |
| **WSGI 服务器** | Gunicorn | 最新 | 同步请求处理 |
| **任务队列** | Celery + Redis | 5.x | 异步任务、定时任务 |
| **AI 引擎** | Stockfish 16 | 最新 | 开源最强象棋引擎 |
| **Python 版本** | Python | 3.11+ | 性能优化、类型提示 |

### 2.3 数据库设计

#### 2.3.1 数据库选型

| 数据库 | 用途 | 选型理由 |
|--------|------|---------|
| **PostgreSQL** | 主数据库 | ACID 事务、JSON 支持、扩展性强 |
| **Redis** | 缓存 + 消息队列 | 高性能、数据结构丰富、发布订阅 |
| **SQLite** | 开发环境 | 零配置、轻量、便于测试 |

#### 2.3.2 核心数据表设计

```sql
-- 用户表
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500),
    nickname        VARCHAR(50),
    rating          INTEGER DEFAULT 1200,  -- 天梯分
    total_games     INTEGER DEFAULT 0,
    wins            INTEGER DEFAULT 0,
    losses          INTEGER DEFAULT 0,
    draws           INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    is_banned       BOOLEAN DEFAULT FALSE,
    ban_reason      TEXT,
    last_login      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对局表
CREATE TABLE games (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    red_player_id   BIGINT REFERENCES users(id),
    black_player_id BIGINT REFERENCES users(id),
    game_type       VARCHAR(20) NOT NULL,  -- 'single', 'online', 'friend'
    status          VARCHAR(20) NOT NULL,  -- 'playing', 'finished', 'aborted'
    winner          VARCHAR(10),           -- 'red', 'black', 'draw'
    fen_start       TEXT NOT NULL,
    fen_current     TEXT NOT NULL,
    move_history    JSONB NOT NULL,        -- 走棋历史记录
    duration        INTEGER,               -- 对局时长 (秒)
    ai_level        INTEGER,               -- AI 难度 (1-10)
    is_rated        BOOLEAN DEFAULT TRUE,  -- 是否计入天梯
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at     TIMESTAMP
);

-- 房间表
CREATE TABLE rooms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    owner_id        BIGINT REFERENCES users(id),
    status          VARCHAR(20) NOT NULL,  -- 'waiting', 'playing', 'finished'
    max_players     INTEGER DEFAULT 2,
    password        VARCHAR(100),          -- 房间密码
    game_id         UUID REFERENCES games(id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at       TIMESTAMP
);

-- 匹配队列表 (Redis 实现，此处为逻辑结构)
-- MATCH_QUEUE: sorted set (rating as score, user_id as member)

-- 成就表
CREATE TABLE achievements (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    description     TEXT NOT NULL,
    icon_url        VARCHAR(500),
    requirement     JSONB NOT NULL         -- 解锁条件
);

-- 用户成就关联表
CREATE TABLE user_achievements (
    user_id         BIGINT REFERENCES users(id),
    achievement_id  INTEGER REFERENCES achievements(id),
    unlocked_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id)
);

-- 棋谱表
CREATE TABLE game_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id         UUID REFERENCES games(id),
    owner_id        BIGINT REFERENCES users(id),
    title           VARCHAR(200),
    description     TEXT,
    fen_start       TEXT NOT NULL,
    move_history    JSONB NOT NULL,
    is_public       BOOLEAN DEFAULT FALSE,
    view_count      INTEGER DEFAULT 0,
    like_count      INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 教程表
CREATE TABLE tutorials (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    type            VARCHAR(20) NOT NULL,  -- 'beginner', 'puzzle', 'spectrum'
    difficulty      INTEGER NOT NULL,      -- 1-10
    fen_puzzle      TEXT,
    solution        JSONB,                 -- 正解走法
    content         JSONB,                 -- 教程内容
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 好友关系表
CREATE TABLE friendships (
    user_id         BIGINT REFERENCES users(id),
    friend_id       BIGINT REFERENCES users(id),
    status          VARCHAR(20) NOT NULL,  -- 'pending', 'accepted', 'blocked'
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, friend_id)
);

-- 聊天记录表
CREATE TABLE chat_messages (
    id              BIGSERIAL PRIMARY KEY,
    room_id         UUID REFERENCES rooms(id),
    sender_id       BIGINT REFERENCES users(id),
    content         TEXT NOT NULL,
    message_type    VARCHAR(20) DEFAULT 'text',  -- 'text', 'system'
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计
CREATE INDEX idx_users_rating ON users(rating DESC);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_games_players ON games(red_player_id, black_player_id);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_created ON games(created_at DESC);
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_game_records_public ON game_records(is_public, created_at DESC);
CREATE INDEX idx_friendships_user ON friendships(user_id, status);
```

### 2.4 缓存设计

#### 2.4.1 Redis 缓存策略

| 缓存类型 | Key 格式 | TTL | 用途 |
|---------|---------|-----|------|
| **用户 Session** | `session:{session_id}` | 7d | 用户登录状态 |
| **用户信息** | `user:{user_id}` | 1h | 用户基础信息缓存 |
| **天梯排名** | `leaderboard:daily` | 1h | 日排行榜缓存 |
| **天梯排名** | `leaderboard:weekly` | 6h | 周排行榜缓存 |
| **天梯排名** | `leaderboard:monthly` | 24h | 月排行榜缓存 |
| **匹配队列** | `match:queue:{rating_range}` | - | 匹配队列 (Sorted Set) |
| **房间信息** | `room:{room_id}` | 2h | 房间状态缓存 |
| **在线用户** | `online:users` | - | 在线用户集合 (Set) |
| **游戏状态** | `game:{game_id}:state` | 30m | 游戏实时状态 |
| **API 响应** | `api:{endpoint}:{params_hash}` | 5m | 热点 API 缓存 |
| **用户成就** | `user:{user_id}:achievements` | 24h | 用户成就缓存 |
| **限流计数** | `ratelimit:{user_ip}:{endpoint}` | 1m | API 限流计数 |

#### 2.4.2 缓存更新策略

```python
# 缓存模式：Cache-Aside (Lazy Loading)
def get_user_info(user_id):
    # 1. 先查缓存
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # 2. 缓存未命中，查数据库
    user = User.objects.get(id=user_id)
    
    # 3. 写入缓存
    redis.setex(f"user:{user_id}", 3600, json.dumps(user.data))
    
    return user.data

# 缓存失效：主动失效 + 过期失效
def update_user_rating(user_id, new_rating):
    # 1. 更新数据库
    User.objects.filter(id=user_id).update(rating=new_rating)
    
    # 2. 删除缓存 (主动失效)
    redis.delete(f"user:{user_id}")
    
    # 3. 更新排行榜 (异步)
    update_leaderboard.delay(user_id, new_rating)
```

### 2.5 消息队列设计

#### 2.5.1 Celery 任务队列

| 队列名称 | 用途 | 优先级 |
|---------|------|--------|
| **default** | 默认队列，普通异步任务 | 中 |
| **email** | 邮件发送任务 | 低 |
| **game** | 游戏相关异步任务 | 高 |
| **analytics** | 数据统计分析任务 | 低 |
| **ai** | AI 引擎计算任务 | 中 |

#### 2.5.2 典型异步任务

```python
# 任务示例
@app.task(queue='email')
def send_welcome_email(user_id):
    """发送欢迎邮件"""
    user = User.objects.get(id=user_id)
    # 发送邮件逻辑...

@app.task(queue='game')
def calculate_rating_change(game_id):
    """计算天梯分变化"""
    game = Game.objects.get(id=game_id)
    # Elo 算法计算...
    # 更新用户天梯分...

@app.task(queue='analytics')
def daily_statistics():
    """每日统计任务"""
    # 计算 DAU、MAU、对局数等...

@app.task(queue='ai')
def analyze_game_position(fen, depth=10):
    """AI 分析棋局"""
    # 调用 Stockfish 分析...
    return analysis_result
```

---

## 3. 模块划分和职责定义

### 3.1 模块总览

```
src/
├── backend/                      # Django 后端
│   ├── apps/
│   │   ├── users/               # 用户模块
│   │   ├── games/               # 游戏对局模块
│   │   ├── matchmaking/         # 匹配模块
│   │   ├── boards/              # 棋局模块
│   │   ├── rankings/            # 排名模块
│   │   ├── tutorials/           # 教程模块
│   │   ├── social/              # 社交模块
│   │   └── admin_panel/         # 后台管理模块
│   ├── core/                    # 核心模块
│   │   ├── authentication/      # 认证授权
│   │   ├── permissions/         # 权限控制
│   │   └── middleware/          # 中间件
│   ├── common/                  # 公共模块
│   │   ├── utils/               # 工具函数
│   │   ├── exceptions/          # 异常定义
│   │   └── responses/           # 响应封装
│   ├── ai/                      # AI 引擎模块
│   │   ├── stockfish/           # Stockfish 集成
│   │   └── evaluator/           # 棋局评估
│   └── channels/                # WebSocket 模块
│       ├── consumers/           # Consumer 定义
│       ├── routing/             # 路由配置
│       └── middleware/          # WS 中间件
│
├── frontend-user/               # 用户端前端
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   ├── pages/               # 页面组件
│   │   ├── features/            # 功能模块
│   │   │   ├── auth/            # 认证功能
│   │   │   ├── game/            # 游戏功能
│   │   │   ├── matchmaking/     # 匹配功能
│   │   │   ├── board/           # 棋盘组件
│   │   │   ├── ranking/         # 排名功能
│   │   │   └── social/          # 社交功能
│   │   ├── hooks/               # 自定义 Hooks
│   │   ├── stores/              # 状态管理
│   │   ├── services/            # API 服务
│   │   └── utils/               # 工具函数
│   └── public/                  # 静态资源
│
└── frontend-admin/              # 管理端前端
    ├── src/
    │   ├── components/          # 管理组件
    │   ├── pages/               # 管理页面
    │   │   ├── users/           # 用户管理
    │   │   ├── games/           # 棋局管理
    │   │   ├── matching/        # 匹配管理
    │   │   ├── statistics/      # 数据统计
    │   │   └── settings/        # 系统配置
    │   ├── services/            # API 服务
    │   └── utils/               # 工具函数
    └── public/                  # 静态资源
```

### 3.2 后端模块职责

#### 3.2.1 用户模块 (users)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 用户数据模型 | User、UserProfile 模型定义 |
| **serializers.py** | 数据序列化 | 用户数据序列化/反序列化 |
| **views.py** | API 视图 | 注册、登录、个人信息 CRUD |
| **services.py** | 业务逻辑 | 用户创建、认证、密码管理 |
| **permissions.py** | 权限控制 | 用户权限验证 |
| **signals.py** | 信号处理 | 用户创建后初始化 |

**核心接口**：
- `POST /api/users/register/` - 用户注册
- `POST /api/users/login/` - 用户登录
- `GET /api/users/profile/` - 获取个人信息
- `PUT /api/users/profile/` - 更新个人信息
- `POST /api/users/change-password/` - 修改密码

#### 3.2.2 游戏对局模块 (games)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 对局数据模型 | Game、GameMove 模型定义 |
| **serializers.py** | 数据序列化 | 对局数据序列化 |
| **views.py** | API 视图 | 对局 CRUD、历史记录 |
| **services.py** | 业务逻辑 | 对局创建、状态管理、结果判定 |
| **validators.py** | 走棋验证 | 象棋规则验证、走棋合法性 |
| **engine.py** | 游戏引擎 | 棋盘状态管理、FEN 解析 |

**核心接口**：
- `POST /api/games/` - 创建对局
- `GET /api/games/{id}/` - 获取对局详情
- `POST /api/games/{id}/move/` - 执行走棋
- `POST /api/games/{id}/resign/` - 投降
- `GET /api/games/history/` - 历史对局列表

#### 3.2.3 匹配模块 (matchmaking)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 匹配数据模型 | MatchQueue、MatchResult 模型 |
| **services.py** | 匹配逻辑 | Elo 匹配算法、队列管理 |
| **tasks.py** | 异步任务 | 匹配超时处理、结果通知 |
| **consumer.py** | WebSocket | 匹配状态推送 |

**匹配算法**：
```python
def find_opponent(user_rating, queue_timeout=180):
    """
    基于 Elo 的匹配算法
    - 初始搜索范围：±100 分
    - 每 30 秒扩大 50 分
    - 最大搜索范围：±300 分
    """
    rating_range = 100
    elapsed = 0
    
    while elapsed < queue_timeout:
        # 在 rating_range 内搜索对手
        opponents = find_in_range(user_rating - rating_range, user_rating + rating_range)
        
        if opponents:
            return select_best_match(opponents)
        
        # 扩大搜索范围
        rating_range = min(rating_range + 50, 300)
        elapsed += 30
        await asyncio.sleep(30)
    
    return None  # 匹配超时
```

#### 3.2.4 棋局模块 (boards)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 棋谱数据模型 | GameRecord、BoardAnalysis 模型 |
| **services.py** | 业务逻辑 | 棋局保存、回放、分享 |
| **fen.py** | FEN 处理 | FEN 解析、生成、验证 |
| **pgn.py** | PGN 处理 | PGN 导入导出 |

**FEN 格式支持**：
```python
class FENParser:
    """FEN 格式解析器"""
    
    @staticmethod
    def parse(fen: str) -> dict:
        """解析 FEN 字符串为棋局状态"""
        parts = fen.split()
        return {
            'board': parse_board(parts[0]),
            'turn': parts[1],  # 'w' or 'b'
            'castling': parts[2],
            'en_passant': parts[3],
            'halfmove': int(parts[4]),
            'fullmove': int(parts[5])
        }
    
    @staticmethod
    def generate(board_state: dict) -> str:
        """从棋局状态生成 FEN 字符串"""
        # ...
```

#### 3.2.5 排名模块 (rankings)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 排名数据模型 | Leaderboard、RatingHistory 模型 |
| **services.py** | 业务逻辑 | Elo 计算、排名更新 |
| **tasks.py** | 异步任务 | 定时排名计算、历史归档 |

**Elo 算法实现**：
```python
def calculate_elo_change(player_rating: int, opponent_rating: int, 
                         result: str, k_factor: int = 32) -> int:
    """
    计算 Elo 积分变化
    result: 'win', 'loss', 'draw'
    """
    # 计算期望得分
    expected = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
    
    # 实际得分
    actual = {'win': 1, 'draw': 0.5, 'loss': 0}[result]
    
    # 积分变化
    change = round(k_factor * (actual - expected))
    return change
```

#### 3.2.6 教程模块 (tutorials)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 教程数据模型 | Tutorial、Puzzle、Progress 模型 |
| **services.py** | 业务逻辑 | 教程内容管理、进度跟踪 |
| **validators.py** | 答案验证 | 残局正解验证 |

#### 3.2.7 社交模块 (social)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **models.py** | 社交数据模型 | Friendship、Message、Notification 模型 |
| **services.py** | 业务逻辑 | 好友管理、消息推送、通知 |
| **consumer.py** | WebSocket | 实时消息推送 |

#### 3.2.8 后台管理模块 (admin_panel)

| 组件 | 职责 | 关键功能 |
|------|------|---------|
| **views.py** | 管理 API | 用户管理、棋局审核、数据统计 |
| **permissions.py** | 权限控制 | 管理员权限验证 |
| **serializers.py** | 数据序列化 | 管理数据序列化 |

### 3.3 AI 引擎模块 (ai)

#### 3.3.1 Stockfish 集成

```python
class StockfishEngine:
    """Stockfish 引擎封装"""
    
    def __init__(self, skill_level: int = 10):
        """
        初始化引擎
        skill_level: 1-10，难度等级
        """
        self.engine = stockfish.Stockfish(
            path="/usr/games/stockfish",
            depth=15,
            parameters={
                "Skill Level": skill_level,
                "Move Overhead": 100,
                "Threads": 2,
                "Hash": 128,
            }
        )
    
    def get_best_move(self, fen: str, think_time: float = 2.0) -> str:
        """获取最佳走法"""
        self.engine.set_fen_position(fen)
        return self.engine.get_best_move(time=think_time * 1000)
    
    def evaluate_position(self, fen: str) -> dict:
        """评估棋局"""
        self.engine.set_fen_position(fen)
        return {
            'score': self.engine.get_evaluation(),
            'best_move': self.engine.get_best_move(),
            'top_moves': self.engine.get_top_moves(3)
        }
    
    def get_hint(self, fen: str, count: int = 3) -> list:
        """获取走棋提示"""
        self.engine.set_fen_position(fen)
        return self.engine.get_top_moves(count)
```

#### 3.3.2 难度等级映射

| 难度等级 | Skill Level | 思考时间 | Elo 预估 |
|---------|-------------|---------|---------|
| 1 (入门) | 0 | 0.5s | 400 |
| 2 (新手) | 2 | 0.5s | 600 |
| 3 (初级) | 4 | 1.0s | 800 |
| 4 (入门) | 6 | 1.0s | 1000 |
| 5 (中级) | 8 | 1.5s | 1200 |
| 6 (中级) | 10 | 1.5s | 1400 |
| 7 (高级) | 12 | 2.0s | 1600 |
| 8 (高级) | 14 | 2.0s | 1800 |
| 9 (大师) | 16 | 3.0s | 2000+ |
| 10 (大师) | 20 | 5.0s | 2200+ |

### 3.4 WebSocket 模块 (channels)

#### 3.4.1 Consumer 设计

```python
# consumers/game_consumer.py
class GameConsumer(AsyncWebsocketConsumer):
    """游戏对局 WebSocket Consumer"""
    
    async def connect(self):
        """连接建立"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'
        
        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 发送当前游戏状态
        game_state = await self.get_game_state()
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': game_state
        }))
    
    async def disconnect(self, close_code):
        """连接断开"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """接收客户端消息"""
        data = json.loads(text_data)
        
        if data['type'] == 'move':
            await self.handle_move(data['move'])
        elif data['type'] == 'chat':
            await self.handle_chat(data['message'])
        elif data['type'] == 'resign':
            await self.handle_resign()
        elif data['type'] == 'offer_draw':
            await self.handle_draw_offer()
    
    async def game_move(self, event):
        """广播走棋消息"""
        await self.send(text_data=json.dumps({
            'type': 'move',
            'data': event['data']
        }))
    
    async def game_chat(self, event):
        """广播聊天消息"""
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'data': event['data']
        }))
    
    async def game_state_update(self, event):
        """广播游戏状态更新"""
        await self.send(text_data=json.dumps({
            'type': 'state_update',
            'data': event['data']
        }))
```

#### 3.4.2 路由配置

```python
# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<room_id>[^/]+)/$', consumers.GameConsumer.as_asgi()),
    re_path(r'ws/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]
```

---

## 4. 数据流设计

### 4.1 用户请求流程 (RESTful API)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  客户端   │     │  Nginx   │     │  Django  │     │  Service │     │ Database │
│          │     │          │     │   View   │     │  Layer   │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1.HTTP 请求     │                │                │                │
     │ (带 JWT Token) │                │                │                │
     ├───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2.转发请求      │                │                │
     │                │ (含用户信息)    │                │                │
     │                ├───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3.认证中间件     │                │
     │                │                │ 验证 JWT Token  │                │
     │                │                ├───────────────>│                │
     │                │                │                │                │
     │                │                │ 4.权限验证      │                │
     │                │                │ 调用 Service    │                │
     │                │                ├───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 5.业务逻辑处理   │
     │                │                │                │ 数据库操作      │
     │                │                │                ├───────────────>│
     │                │                │                │                │
     │                │                │                │ 6.返回结果      │
     │                │                │                <───────────────┤
     │                │                │                │                │
     │                │                │ 7.序列化响应    │                │
     │                │                <───────────────┤                │
     │                │                │                │                │
     │                │ 8.返回 HTTP 响应 │                │                │
     │                <───────────────┤                │                │
     │                │                │                │                │
     │ 9.返回响应数据  │                │                │                │
     <────────────────┤                │                │                │
     │                │                │                │                │
```

### 4.2 游戏对弈流程 (WebSocket)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  红方     │     │  Channels│     │  Game    │     │  黑方     │     │ Database │
│  Client  │     │  Server  │     │  Service │     │  Client  │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1.建立 WS 连接   │                │                │                │
     ├───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2.加入房间组    │                │                │
     │                ├───────────────>│                │                │
     │                │                │                │                │
     │ 3.发送走棋消息  │                │                │                │
     │ {type: 'move'} │                │                │                │
     ├───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 4.验证走棋      │                │                │
     │                ├───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 5.更新游戏状态  │                │
     │                │                ├───────────────>│                │
     │                │                │                │                │
     │                │ 6.广播走棋      │                │                │
     │                │ 到房间组        │                │                │
     │                ├───────────────────────────────>│                │
     │                │                │                │                │
     │ 7.接收走棋更新  │                │                │ 7.接收走棋更新  │
     <────────────────┤                │                <────────────────┤
     │                │                │                │                │
     │                │                │ 8.检查游戏结束  │                │
     │                │                ├───────────────>│                │
     │                │                │                │                │
     │                │                │ 9.保存对局结果  │                │
     │                │                ├───────────────────────────────>│
     │                │                │                │                │
     │                │ 10.广播游戏结束 │                │                │
     │                <────────────────┤                │                │
     │                │                │                │                │
     │ 11.接收结束消息 │                │                │ 11.接收结束消息 │
     <────────────────┤                │                <────────────────┤
```

### 4.3 实时通信流程

#### 4.3.1 消息类型定义

```typescript
// WebSocket 消息类型
interface WebSocketMessage {
  type: MessageType;
  data: any;
}

type MessageType = 
  | 'connect'           // 连接确认
  | 'game_state'        // 游戏状态
  | 'move'              // 走棋
  | 'move_invalid'      // 走棋无效
  | 'chat'              // 聊天消息
  | 'player_join'       // 玩家加入
  | 'player_leave'      // 玩家离开
  | 'game_start'        // 游戏开始
  | 'game_end'          // 游戏结束
  | 'offer_draw'        // 提议和棋
  | 'accept_draw'       // 接受和棋
  | 'resign'            // 投降
  | 'timeout'           // 超时
  | 'error'             // 错误消息
  | 'reconnect'         // 重连
  | 'heartbeat'         // 心跳
```

#### 4.3.2 心跳机制

```python
# 客户端心跳
class HeartbeatManager:
    """心跳管理"""
    
    HEARTBEAT_INTERVAL = 30  # 30 秒
    TIMEOUT_THRESHOLD = 90   # 90 秒无心跳判定掉线
    
    async def start_heartbeat(self):
        """启动心跳"""
        while self.is_connected:
            await self.send(json.dumps({'type': 'heartbeat'}))
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
    
    async def check_timeout(self):
        """检查超时"""
        last_heartbeat = await self.get_last_heartbeat_time()
        if time.time() - last_heartbeat > self.TIMEOUT_THRESHOLD:
            await self.handle_timeout()
```

#### 4.3.3 断线重连机制

```typescript
// 前端重连逻辑
class WebSocketManager {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 秒

  connect() {
    this.ws = new WebSocket(url);
    
    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => this.connect(), delay);
      }
    };
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // 发送重连消息，请求同步状态
      this.send({ type: 'reconnect', gameId: this.currentGameId });
    };
  }
}
```

### 4.4 匹配流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  玩家 A   │     │  Channels│     │  Match   │     │  玩家 B   │     │ Database │
│          │     │  Server  │     │  Service │     │          │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1.请求匹配      │                │                │                │
     │ (rating: 1200) │                │                │                │
     ├───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2.加入匹配队列  │                │                │
     │                │ Redis SortedSet │                │                │
     │                ├───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3.搜索对手      │                │
     │                │                │ (±100 分范围)   │                │
     │                │                ├───────────────>│                │
     │                │                │                │                │
     │                │                │ 4.找到玩家 B     │                │
     │                │                │ (rating: 1180)  │                │
     │                │                │                │                │
     │ 5.匹配成功通知  │                │                │ 5.匹配成功通知  │
     │                ├───────────────────────────────>│                │
     │ <──────────────┤                │                <────────────────┤
     │                │                │                │                │
     │ 6.确认匹配      │                │                │ 6.确认匹配      │
     ├───────────────>│                │                ├───────────────>│
     │                │                │                │                │
     │                │ 7.创建游戏房间  │                │                │
     │                ├───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 8.创建游戏记录  │                │
     │                │                ├───────────────────────────────>│
     │                │                │                │                │
     │ 9.返回房间信息  │                │                │ 9.返回房间信息  │
     │ (room_id)      │                │                │ (room_id)      │
     <────────────────┤                │                <────────────────┤
     │                │                │                │                │
     │ 10.加入房间 WS  │                │                │ 10.加入房间 WS  │
     ├───────────────────────────────>│                │                │
     │                │                │                ├───────────────>│
```

---

## 5. 接口设计规范

### 5.1 RESTful API 规范

#### 5.1.1 URL 设计规范

```
# 资源命名
/api/users/              # 用户列表
/api/users/{id}/         # 单个用户
/api/users/{id}/games/   # 用户的对局列表

# 动作使用 HTTP 方法，不使用动词
GET    /api/games/       # 获取对局列表
POST   /api/games/       # 创建对局
GET    /api/games/{id}/  # 获取对局详情
PUT    /api/games/{id}/  # 更新对局
DELETE /api/games/{id}/  # 删除对局

# 子资源
/api/games/{id}/moves/   # 对局的走棋记录
/api/users/{id}/friends/ # 用户的好友列表
```

#### 5.1.2 请求响应格式

**请求格式**：
```http
POST /api/users/login/
Content-Type: application/json
Authorization: Bearer {token}

{
  "username": "player1",
  "password": "secure_password"
}
```

**成功响应**：
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "username": "player1",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2026-03-04T09:00:00Z"
  },
  "message": "登录成功"
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误",
    "details": {
      "field": "password",
      "reason": "密码长度不足"
    }
  }
}
```

#### 5.1.3 状态码规范

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 OK | 成功 | GET/PUT 成功 |
| 201 Created | 已创建 | POST 成功创建资源 |
| 204 No Content | 无内容 | DELETE 成功 |
| 400 Bad Request | 请求错误 | 参数验证失败 |
| 401 Unauthorized | 未授权 | 未登录或 Token 过期 |
| 403 Forbidden | 禁止访问 | 权限不足 |
| 404 Not Found | 未找到 | 资源不存在 |
| 409 Conflict | 冲突 | 资源已存在/状态冲突 |
| 422 Unprocessable | 无法处理 | 业务逻辑错误 |
| 429 Too Many Requests | 请求过多 | 触发限流 |
| 500 Internal Server Error | 服务器错误 | 系统异常 |

#### 5.1.4 分页规范

```http
GET /api/games/?page=1&page_size=20&ordering=-created_at
```

**响应**：
```json
{
  "success": true,
  "data": {
    "results": [...],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 156,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### 5.1.5 核心 API 列表

**用户认证**：
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/users/register/ | 用户注册 | 否 |
| POST | /api/users/login/ | 用户登录 | 否 |
| POST | /api/users/logout/ | 用户登出 | 是 |
| POST | /api/users/refresh-token/ | 刷新 Token | 是 |
| GET | /api/users/profile/ | 获取个人信息 | 是 |
| PUT | /api/users/profile/ | 更新个人信息 | 是 |
| POST | /api/users/change-password/ | 修改密码 | 是 |

**游戏对局**：
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/games/ | 创建对局 | 是 |
| GET | /api/games/ | 对局列表 | 是 |
| GET | /api/games/{id}/ | 对局详情 | 是 |
| POST | /api/games/{id}/move/ | 执行走棋 | 是 |
| POST | /api/games/{id}/resign/ | 投降 | 是 |
| POST | /api/games/{id}/draw/ | 提议和棋 | 是 |
| GET | /api/games/history/ | 历史对局 | 是 |
| GET | /api/games/{id}/replay/ | 对局回放 | 是 |

**匹配系统**：
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/matchmaking/quick/ | 快速匹配 | 是 |
| POST | /api/matchmaking/cancel/ | 取消匹配 | 是 |
| GET | /api/matchmaking/status/ | 匹配状态 | 是 |

**排名系统**：
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | /api/rankings/leaderboard/ | 天梯排名 | 否 |
| GET | /api/rankings/user/{id}/ | 用户排名 | 否 |
| GET | /api/rankings/history/ | 排名历史 | 是 |

**社交功能**：
| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | /api/social/friends/ | 好友列表 | 是 |
| POST | /api/social/friends/request/ | 发送好友申请 | 是 |
| POST | /api/social/friends/accept/ | 接受好友申请 | 是 |
| DELETE | /api/social/friends/{id}/ | 删除好友 | 是 |

### 5.2 WebSocket 接口规范

#### 5.2.1 连接建立

```javascript
// 连接 URL
const wsUrl = `wss://api.example.com/ws/game/${roomId}/?token=${jwtToken}`;

// 建立连接
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onclose = (event) => {
  console.log('WebSocket closed', event.code, event.reason);
};

ws.onerror = (error) => {
  console.error('WebSocket error', error);
};
```

#### 5.2.2 消息格式

**客户端 → 服务端**：
```typescript
// 走棋消息
interface MoveMessage {
  type: 'move';
  data: {
    from: string;  // 起始位置，如 "e2"
    to: string;    // 目标位置，如 "e4"
    promotion?: string;  // 升变棋子（可选）
  };
}

// 聊天消息
interface ChatMessage {
  type: 'chat';
  data: {
    content: string;
  };
}

// 投降
interface ResignMessage {
  type: 'resign';
}

// 提议和棋
interface DrawOfferMessage {
  type: 'offer_draw';
}

// 接受和棋
interface AcceptDrawMessage {
  type: 'accept_draw';
}

// 心跳
interface HeartbeatMessage {
  type: 'heartbeat';
  timestamp: number;
}
```

**服务端 → 客户端**：
```typescript
// 游戏状态
interface GameStateMessage {
  type: 'game_state';
  data: {
    gameId: string;
    fen: string;
    turn: 'red' | 'black';
    players: {
      red: { id: number; username: string };
      black: { id: number; username: string };
    };
    status: 'waiting' | 'playing' | 'finished';
  };
}

// 走棋广播
interface MoveBroadcastMessage {
  type: 'move';
  data: {
    from: string;
    to: string;
    piece: string;
    captured?: string;
    fen: string;
    timestamp: number;
  };
}

// 走棋无效
interface MoveInvalidMessage {
  type: 'move_invalid';
  data: {
    reason: string;
  };
}

// 游戏结束
interface GameEndMessage {
  type: 'game_end';
  data: {
    winner: 'red' | 'black' | 'draw';
    reason: 'checkmate' | 'resign' | 'draw' | 'timeout';
    ratingChange: {
      red: number;
      black: number;
    };
  };
}

// 错误消息
interface ErrorMessage {
  type: 'error';
  data: {
    code: string;
    message: string;
  };
}
```

#### 5.2.3 错误码定义

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| WS_001 | 无效 Token | 重新登录 |
| WS_002 | 房间不存在 | 返回大厅 |
| WS_003 | 房间已满 | 提示用户 |
| WS_004 | 非回合内 | 等待对方走棋 |
| WS_005 | 无效走棋 | 提示合法走法 |
| WS_006 | 游戏已结束 | 返回结果页面 |
| WS_007 | 连接超时 | 自动重连 |
| WS_008 | 重复连接 | 踢出旧连接 |

---

## 6. 部署架构

### 6.1 开发环境

```
┌─────────────────────────────────────────────────────────────┐
│                     开发环境 (Development)                   │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Frontend  │  │   Backend   │  │     Database        │ │
│  │  Dev Server │  │  Runserver  │  │    PostgreSQL       │ │
│  │  (Vite)     │  │  (Debug)    │  │    (Docker)         │ │
│  │  :3000      │  │  :8000      │  │    :5432            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │    Redis    │  │  Stockfish  │                          │
│  │  (Docker)   │  │  (Local)    │                          │
│  │  :6379      │  │             │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**开发环境配置**：
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chinese_chess_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.dev
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    volumes:
      - ./src/backend:/app
    depends_on:
      - postgres
      - redis
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://dev:dev_password@postgres:5432/chinese_chess_dev
      - REDIS_URL=redis://redis:6379/0

  frontend-user:
    build:
      context: ./src/frontend-user
      dockerfile: Dockerfile.dev
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "3000:3000"
    volumes:
      - ./src/frontend-user:/app

  frontend-admin:
    build:
      context: ./src/frontend-admin
      dockerfile: Dockerfile.dev
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "3001:3001"
    volumes:
      - ./src/frontend-admin:/app

volumes:
  postgres_dev_data:
  redis_dev_data:
```

### 6.2 测试环境

```
┌─────────────────────────────────────────────────────────────┐
│                      测试环境 (Staging)                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Nginx (SSL)                      │   │
│  │                  staging.example.com                │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Frontend   │  │   Backend   │  │     Database        │ │
│  │  (Static)   │  │  Gunicorn   │  │    PostgreSQL       │ │
│  │             │  │  (4 workers)│  │    (Docker)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Redis    │  │   Celery    │  │    Stockfish        │ │
│  │  (Sentinel) │  │  Worker     │  │    (Docker)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**测试环境特点**：
- 与生产环境配置一致
- 用于集成测试、性能测试
- 数据定期清理
- 自动化 CI/CD 部署

### 6.3 生产环境

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        生产环境 (Production)                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         CDN (静态资源)                           │   │
│  │                   Cloudflare / 阿里云 CDN                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    负载均衡 (Load Balancer)                      │   │
│  │                  AWS ALB / Nginx + Keepalived                   │   │
│  └─────────────────────────┬───────────────────────────────────────┘   │
│                            │                                            │
│           ┌────────────────┼────────────────┐                          │
│           ▼                ▼                ▼                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │   Web 1     │  │   Web 2     │  │   Web N     │  (自动伸缩)         │
│  │  Gunicorn   │  │  Gunicorn   │  │  Gunicorn   │                    │
│  │  (8 workers)│  │  (8 workers)│  │  (8 workers)│                    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                    │
│         │                │                │                             │
│         └────────────────┼────────────────┘                             │
│                          │                                              │
│           ┌──────────────┼──────────────┐                              │
│           ▼              ▼              ▼                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐            │
│  │  Channels 1 │  │  Channels 2 │  │  Channels N         │            │
│  │   Daphne    │  │   Daphne    │  │   Daphne            │            │
│  └─────────────┘  └─────────────┘  └─────────────────────┘            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        数据层                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │ PostgreSQL  │  │   Redis     │  │       MinIO/S3          │  │   │
│  │  │ 主从复制     │  │   集群       │  │     对象存储             │  │   │
│  │  │ (1 主 2 从)   │  │  (3 节点)    │  │                       │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        任务队列                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │  Celery 1   │  │  Celery 2   │  │    Celery Beat          │  │   │
│  │  │  Worker     │  │  Worker     │  │   (定时任务)             │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**生产环境配置**：
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/app/static
    depends_on:
      - web
      - channels

  web:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 8
    volumes:
      - static_volume:/app/static
    environment:
      - DEBUG=False
      - DATABASE_URL=postgres://user:password@postgres:5432/chinese_chess
      - REDIS_URL=redis://redis-cluster:6379/0
    depends_on:
      - postgres
      - redis

  channels:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: daphne -b 0.0.0.0 -p 8001 config.asgi:application
    environment:
      - DATABASE_URL=postgres://user:password@postgres:5432/chinese_chess
      - REDIS_URL=redis://redis-cluster:6379/0
    depends_on:
      - postgres
      - redis

  celery-worker:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: celery -A config worker --loglevel=info --queues=default,email,game,analytics,ai
    environment:
      - DATABASE_URL=postgres://user:password@postgres:5432/chinese_chess
      - REDIS_URL=redis://redis-cluster:6379/0
    depends_on:
      - postgres
      - redis

  celery-beat:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: celery -A config beat --loglevel=info
    environment:
      - DATABASE_URL=postgres://user:password@postgres:5432/chinese_chess
      - REDIS_URL=redis://redis-cluster:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: chinese_chess
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

### 6.4 环境配置对比

| 配置项 | 开发环境 | 测试环境 | 生产环境 |
|--------|---------|---------|---------|
| **DEBUG** | True | False | False |
| **数据库** | PostgreSQL (Docker) | PostgreSQL (Docker) | PostgreSQL (主从) |
| **缓存** | Redis (单机) | Redis (Sentinel) | Redis (集群) |
| **Web 服务器** | runserver | Gunicorn (4 workers) | Gunicorn (8 workers × N) |
| **WS 服务器** | runserver (内置 ASGI) | Daphne (2 实例) | Daphne (N 实例) |
| **Celery** | 单 Worker | 2 Workers | 多 Workers + Beat |
| **Stockfish** | 本地安装 | Docker | Docker (多实例) |
| **SSL** | 无 | 自签名证书 | 正式 SSL 证书 |
| **监控** | 无 | 基础监控 | 完整监控 (Prometheus) |
| **日志** | 控制台 | 文件 | ELK 集中日志 |

---

## 7. 扩展性设计

### 7.1 水平扩展策略

#### 7.1.1 无状态服务设计

```python
# 所有服务设计为无状态，支持水平扩展

# ✅ 正确：无状态服务
class GameService:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client
        # 不保存任何实例状态
    
    def make_move(self, game_id, move):
        # 所有状态存储在数据库/Redis
        game = self.db.query(Game).get(game_id)
        # ...

# ❌ 错误：有状态服务
class GameService:
    def __init__(self):
        self.local_cache = {}  # 本地缓存导致扩展问题
```

#### 7.1.2 数据库水平扩展

**读写分离**：
```python
# 数据库路由配置
class DatabaseRouter:
    def db_for_read(self, model, hint):
        # 读操作走从库
        return 'replica'
    
    def db_for_write(self, model, hint):
        # 写操作走主库
        return 'default'

# Django 配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'postgres-master',
        # ...
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'postgres-replica-1',
        # ...
    }
}
```

**分库分表**（未来扩展）：
```python
# 按用户 ID 分片
def get_user_db(user_id):
    shard = user_id % 4  # 4 个分片
    return f'user_db_{shard}'

# 按时间分表（对局记录）
def get_game_table(game_date):
    month = game_date.strftime('%Y%m')
    return f'games_{month}'
```

#### 7.1.3 Redis 集群

```python
# Redis 集群配置
REDIS_CLUSTER = {
    'startup_nodes': [
        {'host': 'redis-1', 'port': 6379},
        {'host': 'redis-2', 'port': 6379},
        {'host': 'redis-3', 'port': 6379},
    ],
    'password': 'redis_password',
}

# 使用 redis-py-cluster
from redis.cluster import RedisCluster
rc = RedisCluster(**REDIS_CLUSTER)
```

### 7.2 性能优化

#### 7.2.1 数据库优化

**索引优化**：
```sql
-- 高频查询字段建立索引
CREATE INDEX idx_users_rating_active ON users(rating DESC) WHERE is_active = true;
CREATE INDEX idx_games_status_created ON games(status, created_at DESC);
CREATE INDEX idx_games_players_idx ON games(red_player_id) INCLUDE (black_player_id, status);

-- 复合索引
CREATE INDEX idx_leaderboard_composite ON users(rating DESC, total_games DESC) WHERE is_active = true;

-- 部分索引（只索引活跃用户）
CREATE INDEX idx_active_users_online ON users(id) WHERE is_active = true AND last_login > NOW() - INTERVAL '5 minutes';
```

**查询优化**：
```python
# ✅ 使用 select_related 和 prefetch_related
games = Game.objects.select_related('red_player', 'black_player')\
    .prefetch_related('moves')\
    .filter(status='playing')

# ✅ 只查询需要的字段
users = User.objects.only('id', 'username', 'avatar_url')

# ✅ 使用 annotate 进行聚合
leaderboard = User.objects.annotate(
    win_rate=ExpressionWrapper(F('wins') * 100.0 / F('total_games'), output_field=FloatField())
).order_by('-rating')[:100]

# ❌ 避免 N+1 查询
for game in games:
    print(game.red_player.username)  # 每次循环都会查询数据库
```

#### 7.2.2 缓存优化

**多级缓存策略**：
```python
class CacheManager:
    """多级缓存管理"""
    
    def __init__(self):
        self.local_cache = {}  # L1: 进程内缓存
        self.redis = redis_client  # L2: 分布式缓存
        self.db = db_session  # L3: 数据库
    
    def get(self, key, ttl=3600):
        # L1 缓存命中
        if key in self.local_cache:
            cached = self.local_cache[key]
            if cached['expires'] > time.time():
                return cached['data']
        
        # L2 缓存命中
        cached = self.redis.get(key)
        if cached:
            data = json.loads(cached)
            self.local_cache[key] = {'data': data, 'expires': time.time() + 60}  # L1 缓存 60 秒
            return data
        
        # L3 数据库查询
        data = self._query_db(key)
        
        # 写入 L2 缓存
        self.redis.setex(key, ttl, json.dumps(data))
        
        # 写入 L1 缓存
        self.local_cache[key] = {'data': data, 'expires': time.time() + 60}
        
        return data
```

**热点数据预加载**：
```python
@app.task(queue='analytics')
def preload_hot_data():
    """预加载热点数据到缓存"""
    # 预加载天梯前 100 名
    top_players = User.objects.order_by('-rating')[:100]
    for player in top_players:
        redis.setex(f"user:{player.id}", 3600, json.dumps(player.data))
    
    # 预加载热门棋局
    hot_games = Game.objects.filter(is_public=True).order_by('-view_count')[:50]
    for game in hot_games:
        redis.setex(f"game:{game.id}", 7200, json.dumps(game.data))
```

#### 7.2.3 WebSocket 性能优化

**连接池管理**：
```python
# Channels 配置
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis-1", 6379), ("redis-2", 6379), ("redis-3", 6379)],
            "capacity": 1500,  # 每个通道容量
            "expiry": 10,  # 消息过期时间
        },
    },
}
```

**消息压缩**：
```python
import gzip
import json

class CompressedConsumer(AsyncWebsocketConsumer):
    async def send_compressed(self, data):
        """发送压缩消息"""
        json_data = json.dumps(data)
        compressed = gzip.compress(json_data.encode())
        
        # 如果压缩后更小，发送压缩数据
        if len(compressed) < len(json_data):
            await self.send(bytes_data=compressed)
        else:
            await self.send(text_data=json_data)
```

### 7.3 容器化与编排

#### 7.3.1 Docker 优化

```dockerfile
# 多阶段构建优化
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

# 非 root 用户运行
RUN useradd -m appuser
USER appuser

CMD ["gunicorn", "config.wsgi:application"]
```

#### 7.3.2 Kubernetes 部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chinese-chess-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: chinese-chess-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chinese-chess-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 7.4 监控与告警

#### 7.4.1 监控指标

| 指标类型 | 指标名称 | 告警阈值 |
|---------|---------|---------|
| **API 性能** | API 响应时间 P95 | > 200ms |
| **API 性能** | API 错误率 | > 1% |
| **WebSocket** | WS 连接数 | > 10000 |
| **WebSocket** | WS 消息延迟 P95 | > 50ms |
| **数据库** | 查询响应时间 P95 | > 100ms |
| **数据库** | 连接池使用率 | > 80% |
| **缓存** | Redis 内存使用率 | > 80% |
| **缓存** | 缓存命中率 | < 70% |
| **系统** | CPU 使用率 | > 80% |
| **系统** | 内存使用率 | > 85% |
| **业务** | 匹配等待时间 | > 3 分钟 |
| **业务** | 对局异常率 | > 5% |

#### 7.4.2 日志收集

```python
# 结构化日志配置
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chinese_chess/app.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}

# 使用示例
import logging
logger = logging.getLogger(__name__)

logger.info("Game created", extra={
    'game_id': game_id,
    'red_player': red_player_id,
    'black_player': black_player_id
})
```

---

## 附录

### A. 技术选型决策记录

| 决策 | 选项 A | 选项 B | 选择 | 理由 |
|------|-------|-------|------|------|
| **前端框架** | React | Vue | React | 生态更丰富、TypeScript 支持更好 |
| **后端框架** | Django | FastAPI | Django | 自带 Admin、ORM 成熟、Channels 集成 |
| **数据库** | PostgreSQL | MySQL | PostgreSQL | JSON 支持更好、扩展性更强 |
| **缓存** | Redis | Memcached | Redis | 数据结构丰富、支持发布订阅 |
| **任务队列** | Celery | RQ | Celery | 功能更完善、生态更好 |
| **AI 引擎** | Stockfish | GNU Chess | Stockfish | 开源最强、可配置难度 |

### B. 架构图例说明

- **实线箭头**：同步调用
- **虚线箭头**：异步消息
- **圆柱体**：数据存储
- **矩形**：服务/组件
- **圆角矩形**：外部系统

### C. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | architect agent | 初始版本，完成系统架构设计 |

---

**阶段 2 完成** ✅

下一步：进入**阶段 3 详细设计**，进行数据库设计、API 详细设计、前端组件设计等。
