# ♟️ 游戏对局系统 - 功能规划文档

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**优先级**：P0  
**状态**：待实现

---

## 1. 功能概述

### 1.1 功能描述

游戏对局系统是中国象棋平台的核心功能，负责管理棋局的创建、走棋、状态管理、胜负判定和棋谱记录。该系统需要支持单机 AI 对战、联网对战和好友对战三种模式，确保走棋规则的正确性和游戏状态的实时同步。

### 1.2 功能范围

**包含**：
- 创建对局（单机/联网/好友）
- 走棋规则验证（中国象棋规则）
- 游戏状态管理（FEN 格式）
- 胜负判定（将死、困毙、投降、超时）
- 棋谱记录（走棋历史、FEN 快照）
- 悔棋功能（单机模式）
- 游戏时间控制（计时器）

**不包含**（P1/P2）：
- 观战功能（P1）
- 断线重连（P1）
- 投降/求和（P1）
- 棋局分享（P1）
- 棋局分析（P2）

### 1.3 技术选型

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| **棋局表示** | FEN 格式 | 标准、简洁、易于传输 |
| **规则验证** | 自研规则引擎 | 完全可控、针对象棋优化 |
| **状态同步** | WebSocket | 实时、低延迟 |
| **棋谱存储** | PostgreSQL JSONB | 灵活、支持查询 |
| **游戏计时** | 前端 + 服务端双重计时 | 防止作弊、精确控制 |

---

## 2. 用户故事

### 2.1 核心用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|--------|
| **US-GAME-01** | 作为玩家，我希望创建单机对局并与 AI 对战，以便独自练习 | 支持 10 级难度选择，AI 响应时间<2 秒 | P0 |
| **US-GAME-02** | 作为玩家，我希望创建好友对局并邀请朋友，以便一起玩游戏 | 生成房间链接，好友可通过链接加入 | P0 |
| **US-GAME-03** | 作为玩家，我希望走棋时得到规则提示，以便避免无效走棋 | 非法走棋即时提示，显示合法走法范围 | P0 |
| **US-GAME-04** | 作为玩家，我希望查看对局历史记录，以便回顾我的走法 | 完整记录每步走棋，支持前后翻页 | P0 |
| **US-GAME-05** | 作为玩家，我希望在单机模式下悔棋，以便修正错误走法 | 支持最多 3 次悔棋，AI 也退回上一步 | P0 |
| **US-GAME-06** | 作为玩家，我希望对局自动保存，以便掉线后恢复 | 每步走棋自动保存，可随时恢复 | P0 |
| **US-GAME-07** | 作为玩家，我希望看到游戏时间，以便掌握对局节奏 | 显示双方剩余时间，超时判负 | P0 |
| **US-GAME-08** | 作为玩家，我希望游戏结束时看到结果和天梯分变化，以便了解我的表现 | 即时显示胜负和积分变化 | P0 |

### 2.2 用户旅程地图

```
单机对局流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 选择单机 │ →  │ 选择难度 │ →  │ 选择先手 │ →  │ 开始对局 │ →  │ 走棋对战 │ →  │ 游戏结束 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │                              │
                                    ▼                              ▼
                          初始化 FEN 位置                    判定胜负/和棋
                          启动 AI 引擎                       计算天梯分变化
                          启动计时器                       保存棋谱

联网对战流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 快速匹配 │ →  │ 匹配成功 │ →  │ 创建房间 │ →  │ 双方加入 │ →  │ 开始对局 │ →  │ 走棋对战 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │                                              │
                                    ▼                                              ▼
                          WebSocket 建立连接                                实时同步走棋
                          随机分配先后手                                  服务端验证走棋
```

---

## 3. API 设计

### 3.1 API 总览

#### 3.1.1 RESTful API

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/games/ | 创建对局 | 是 |
| GET | /api/games/ | 对局列表 | 是 |
| GET | /api/games/{id}/ | 对局详情 | 是 |
| GET | /api/games/{id}/state/ | 获取游戏状态 | 是 |
| GET | /api/games/history/ | 历史对局列表 | 是 |
| GET | /api/games/{id}/replay/ | 对局回放数据 | 是 |

#### 3.1.2 WebSocket API

| 消息类型 | 方向 | 描述 |
|---------|------|------|
| `join_game` | C→S | 加入游戏房间 |
| `make_move` | C→S | 执行走棋 |
| `resign` | C→S | 投降 |
| `offer_draw` | C→S | 提议和棋 |
| `accept_draw` | C→S | 接受和棋 |
| `game_state` | S→C | 游戏状态广播 |
| `move_made` | S→C | 走棋广播 |
| `move_invalid` | S→C | 走棋无效通知 |
| `game_end` | S→C | 游戏结束通知 |
| `chat_message` | 双向 | 聊天消息 |

---

### 3.2 API 详细设计

#### 3.2.1 创建对局

**请求**：
```http
POST /api/games/
Authorization: Bearer {token}
Content-Type: application/json

{
  "game_type": "single",  // single, online, friend
  "ai_level": 5,          // AI 难度 1-10（单机模式）
  "player_side": "red",   // red, black（单机模式）
  "time_control": {
    "base_time": 600,     // 基础时间（秒）
    "increment": 10       // 每步加时（秒）
  }
}
```

**成功响应**（201 Created）：
```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "single",
    "status": "playing",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "red",
    "red_player": {
      "user_id": 12345,
      "username": "player1"
    },
    "black_player": null,
    "ai_level": 5,
    "time_control": {
      "red_remaining": 600,
      "black_remaining": 600,
      "increment": 10
    },
    "created_at": "2026-03-03T09:00:00Z"
  }
}
```

**游戏类型说明**：
| 类型 | 描述 | 必填参数 |
|------|------|---------|
| `single` | 单机 AI 对战 | ai_level, player_side |
| `online` | 联网匹配对战 | time_control |
| `friend` | 好友对战 | time_control, room_password（可选） |

---

#### 3.2.2 获取对局详情

**请求**：
```http
GET /api/games/{game_id}/
Authorization: Bearer {token}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "game_type": "online",
    "status": "finished",
    "winner": "red",
    "win_reason": "checkmate",
    "fen_start": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "fen_current": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "move_count": 45,
    "duration": 1256,
    "red_player": {
      "user_id": 12345,
      "username": "player1",
      "rating_before": 1200,
      "rating_after": 1215,
      "rating_change": 15
    },
    "black_player": {
      "user_id": 67890,
      "username": "player2",
      "rating_before": 1180,
      "rating_after": 1165,
      "rating_change": -15
    },
    "is_rated": true,
    "created_at": "2026-03-03T09:00:00Z",
    "finished_at": "2026-03-03T09:20:56Z"
  }
}
```

---

#### 3.2.3 获取游戏状态（WebSocket）

**请求**：
```json
{
  "type": "get_state",
  "game_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应**：
```json
{
  "type": "game_state",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
    "turn": "red",
    "status": "playing",
    "move_count": 0,
    "time_control": {
      "red_remaining": 600,
      "black_remaining": 600,
      "increment": 10
    },
    "last_move": null,
    "players": {
      "red": { "user_id": 12345, "username": "player1", "online": true },
      "black": { "user_id": 67890, "username": "player2", "online": true }
    }
  }
}
```

---

#### 3.2.4 执行走棋（WebSocket）

**请求**：
```json
{
  "type": "make_move",
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "move": {
    "from": "e2",
    "to": "e4",
    "piece": "P"
  },
  "sequence": 1
}
```

**成功响应**：
```json
{
  "type": "move_made",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "move": {
      "from": "e2",
      "to": "e4",
      "piece": "P",
      "captured": null,
      "notation": "炮二平五"
    },
    "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "turn": "black",
    "move_count": 1,
    "time_remaining": 590,
    "timestamp": "2026-03-03T09:00:10Z"
  }
}
```

**失败响应**：
```json
{
  "type": "move_invalid",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "reason": "invalid_move",
    "message": "该棋子不能移动到此位置",
    "legal_moves": ["e2-e3", "e2-f2", "c1-c4"]
  }
}
```

---

#### 3.2.5 投降

**请求**：
```json
{
  "type": "resign",
  "game_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应**：
```json
{
  "type": "game_end",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "winner": "black",
    "reason": "resign",
    "rating_change": {
      "red": -10,
      "black": 10
    }
  }
}
```

---

#### 3.2.6 提议和棋

**请求**：
```json
{
  "type": "offer_draw",
  "game_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应**（对方接受）：
```json
{
  "type": "game_end",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "winner": "draw",
    "reason": "agreement",
    "rating_change": {
      "red": 0,
      "black": 0
    }
  }
}
```

---

### 3.3 走棋格式定义

#### 3.3.1 坐标系统

```
棋盘坐标系（红方视角）：
  a   b   c   d   e   f   g   h   i
9 +---+---+---+---+---+---+---+---+---+ 9
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
8 +---+---+---+---+---+---+---+---+---+ 8
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
7 +---+---+---+---+---+---+---+---+---+ 7
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
6 +---+---+---+---+---+---+---+---+---+ 6
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
5 +---+---+---+---+---+---+---+---+---+ 5
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
4 +---+---+---+---+---+---+---+---+---+ 4
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
3 +---+---+---+---+---+---+---+---+---+ 3
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
2 +---+---+---+---+---+---+---+---+---+ 2
  |   |   |   |   |   |   |   |   |   |
  +---+---+---+---+---+---+---+---+---+
  |   |   |   |   |   |   |   |   |   |
1 +---+---+---+---+---+---+---+---+---+ 1
  a   b   c   d   e   f   g   h   i

示例：
- "e2" 表示红方炮的初始位置
- "e4" 表示中线河界位置
```

#### 3.3.2 棋子代码

| 代码 | 红方 | 黑方 |
|------|------|------|
| K | 帅 | 将 |
| A | 仕 | 士 |
| B | 相 | 象 |
| N | 马 | 马 |
| R | 车 | 车 |
| C | 炮 | 炮 |
| P | 兵 | 卒 |

---

## 4. 数据库设计

### 4.1 对局表（games）

```sql
CREATE TABLE games (
    -- 主键
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 对局信息
    game_type       VARCHAR(20) NOT NULL,  -- 'single', 'online', 'friend'
    status          VARCHAR(20) NOT NULL,  -- 'waiting', 'playing', 'finished', 'aborted'
    
    -- 玩家信息
    red_player_id   BIGINT REFERENCES users(id),
    black_player_id BIGINT REFERENCES users(id),
    
    -- 游戏状态
    fen_start       TEXT NOT NULL,
    fen_current     TEXT NOT NULL,
    turn            VARCHAR(5) NOT NULL,   -- 'red', 'black'
    
    -- 结果信息
    winner          VARCHAR(10),           -- 'red', 'black', 'draw', NULL
    win_reason      VARCHAR(50),           -- 'checkmate', 'resign', 'timeout', 'agreement'
    
    -- 时间控制
    time_control_base     INTEGER DEFAULT 600,   -- 基础时间（秒）
    time_control_increment INTEGER DEFAULT 0,    -- 每步加时（秒）
    red_time_remaining    INTEGER,
    black_time_remaining  INTEGER,
    
    -- AI 配置（单机模式）
    ai_level        INTEGER,               -- 1-10
    ai_side         VARCHAR(5),            -- 'red', 'black'
    
    -- 统计信息
    move_count      INTEGER DEFAULT 0,
    duration        INTEGER,               -- 对局时长（秒）
    
    -- 评级信息
    is_rated        BOOLEAN DEFAULT TRUE,
    red_rating_before INTEGER,
    red_rating_after  INTEGER,
    black_rating_before INTEGER,
    black_rating_after  INTEGER,
    
    -- 房间信息（好友对战）
    room_id         UUID,
    
    -- 时间戳
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- 约束
    CONSTRAINT chk_game_type CHECK (game_type IN ('single', 'online', 'friend')),
    CONSTRAINT chk_status CHECK (status IN ('waiting', 'playing', 'finished', 'aborted')),
    CONSTRAINT chk_turn CHECK (turn IN ('red', 'black')),
    CONSTRAINT chk_winner CHECK (winner IS NULL OR winner IN ('red', 'black', 'draw')),
    CONSTRAINT chk_ai_level CHECK (ai_level IS NULL OR (ai_level BETWEEN 1 AND 10))
);

-- 索引
CREATE INDEX idx_games_red_player ON games(red_player_id);
CREATE INDEX idx_games_black_player ON games(black_player_id);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_created ON games(created_at DESC);
CREATE INDEX idx_games_finished ON games(finished_at DESC) WHERE status = 'finished';
CREATE INDEX idx_games_rated ON games(is_rated) WHERE is_rated = TRUE;
```

---

### 4.2 走棋记录表（game_moves）

```sql
CREATE TABLE game_moves (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    
    -- 外键
    game_id         UUID REFERENCES games(id) ON DELETE CASCADE NOT NULL,
    
    -- 走棋信息
    move_number     INTEGER NOT NULL,      -- 第几步
    piece           VARCHAR(1) NOT NULL,   -- 棋子类型
    from_pos        VARCHAR(2) NOT NULL,   -- 起始位置
    to_pos          VARCHAR(2) NOT NULL,   -- 目标位置
    captured        VARCHAR(1),            -- 被吃棋子
    is_check        BOOLEAN DEFAULT FALSE, -- 是否将军
    is_capture      BOOLEAN DEFAULT FALSE, -- 是否吃子
    
    -- 走棋描述
    notation        VARCHAR(10),           -- 中文记谱（如"炮二平五"）
    san             VARCHAR(10),           -- 标准代数记谱
    
    -- FEN 快照
    fen_after       TEXT NOT NULL,
    
    -- 时间信息
    time_remaining  INTEGER,               -- 走棋后剩余时间（秒）
    time_used       INTEGER,               -- 本步用时（秒）
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- 约束
    CONSTRAINT unique_move_per_game UNIQUE (game_id, move_number)
);

-- 索引
CREATE INDEX idx_game_moves_game ON game_moves(game_id, move_number);
CREATE INDEX idx_game_moves_piece ON game_moves(piece);
CREATE INDEX idx_game_moves_capture ON game_moves(is_capture) WHERE is_capture = TRUE;
```

---

### 4.3 游戏房间表（game_rooms）

```sql
CREATE TABLE game_rooms (
    -- 主键
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 房间信息
    name            VARCHAR(100) NOT NULL,
    owner_id        BIGINT REFERENCES users(id) NOT NULL,
    
    -- 房间状态
    status          VARCHAR(20) NOT NULL,  -- 'waiting', 'playing', 'finished'
    
    -- 游戏配置
    game_type       VARCHAR(20) NOT NULL,
    time_control_base     INTEGER DEFAULT 600,
    time_control_increment INTEGER DEFAULT 0,
    ai_level        INTEGER,
    
    -- 关联对局
    game_id         UUID REFERENCES games(id),
    
    -- 房间设置
    password        VARCHAR(100),          -- 房间密码（可选）
    max_spectators  INTEGER DEFAULT 0,     -- 最大观战人数
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_at       TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_room_status CHECK (status IN ('waiting', 'playing', 'finished'))
);

-- 索引
CREATE INDEX idx_rooms_owner ON game_rooms(owner_id);
CREATE INDEX idx_rooms_status ON game_rooms(status);
CREATE INDEX idx_rooms_created ON game_rooms(created_at DESC);
```

---

### 4.4 ER 图

```
┌─────────────────────────┐
│         users           │
├─────────────────────────┤
│ PK  id                  │
│     username            │
│     rating              │
└─────────────────────────┘
          │
          │ 1:N (red_player)
          │ 1:N (black_player)
          ▼
┌─────────────────────────┐
│         games           │
├─────────────────────────┤
│ PK  id (UUID)           │
│ FK  red_player_id       │
│ FK  black_player_id     │
│     game_type           │
│     status              │
│     fen_start           │
│     fen_current         │
│     turn                │
│     winner              │
│     win_reason          │
│     time_control_*      │
│     ai_level            │
│     move_count          │
│     duration            │
│     is_rated            │
│     rating_*            │
│     room_id             │
│     started_at          │
│     finished_at         │
│     created_at          │
│     updated_at          │
└─────────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────────┐
│       game_moves        │
├─────────────────────────┤
│ PK  id                  │
│ FK  game_id             │
│     move_number         │
│     piece               │
│     from_pos            │
│     to_pos              │
│     captured            │
│     is_check            │
│     is_capture          │
│     notation            │
│     fen_after           │
│     time_remaining      │
│     time_used           │
│     created_at          │
└─────────────────────────┘

┌─────────────────────────┐
│       game_rooms        │
├─────────────────────────┤
│ PK  id (UUID)           │
│ FK  owner_id            │
│     name                │
│     status              │
│     game_type           │
│     time_control_*      │
│ FK  game_id             │
│     password            │
│     created_at          │
│     closed_at           │
└─────────────────────────┘
```

---

## 5. 实现步骤（任务分解）

### 5.1 后端实现

#### 5.1.1 数据模型层（Day 1-2）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-01** | 创建 Game 模型（apps/games/models.py） | 3h | - |
| **GAME-BE-02** | 创建 GameMove 模型 | 2h | GAME-BE-01 |
| **GAME-BE-03** | 创建 GameRoom 模型 | 2h | GAME-BE-01 |
| **GAME-BE-04** | 编写数据库迁移并执行 | 1h | GAME-BE-01~03 |

---

#### 5.1.2 象棋规则引擎（Day 3-5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-05** | 创建 FEN 解析器（FENParser） | 3h | - |
| **GAME-BE-06** | 创建棋盘表示类（Board） | 4h | GAME-BE-05 |
| **GAME-BE-07** | 实现棋子移动规则验证 | 8h | GAME-BE-06 |
| **GAME-BE-08** | 实现将军检测 | 4h | GAME-BE-07 |
| **GAME-BE-09** | 实现将死/困毙检测 | 4h | GAME-BE-08 |
| **GAME-BE-10** | 实现合法走法生成器 | 4h | GAME-BE-07 |

**代码结构**：
```python
# apps/games/engine/board.py
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Move:
    from_pos: str
    to_pos: str
    piece: str
    captured: Optional[str] = None
    is_check: bool = False
    is_capture: bool = False

class Board:
    """象棋棋盘"""
    
    def __init__(self, fen: str = None):
        self.squares = {}  # 位置 -> 棋子
        self.turn = 'red'
        self.castling = '-'
        self.en_passant = '-'
        self.halfmove = 0
        self.fullmove = 1
        
        if fen:
            self.load_fen(fen or self.STARTING_FEN)
    
    def load_fen(self, fen: str):
        """加载 FEN 字符串"""
        parts = fen.split()
        self._parse_board(parts[0])
        self.turn = parts[1]
        # ...
    
    def to_fen(self) -> str:
        """生成 FEN 字符串"""
        board_str = self._board_to_fen()
        return f"{board_str} {self.turn} {self.castling} {self.en_passant} {self.halfmove} {self.fullmove}"
    
    def get_legal_moves(self) -> List[Move]:
        """获取所有合法走法"""
        moves = []
        for pos, piece in self.squares.items():
            if piece[0].lower() == self.turn[0]:  # 当前回合方
                piece_moves = self._get_piece_moves(pos, piece)
                for move in piece_moves:
                    if self._is_legal(move):  # 不走入将军
                        moves.append(move)
        return moves
    
    def make_move(self, move: Move) -> bool:
        """执行走棋"""
        if not self._is_legal(move):
            return False
        
        # 移动棋子
        captured = self.squares.get(move.to_pos)
        self.squares[move.to_pos] = self.squares[move.from_pos]
        del self.squares[move.from_pos]
        
        # 更新回合
        self.turn = 'black' if self.turn == 'red' else 'red'
        
        # 检查将军
        is_check = self._is_in_check(self.turn)
        
        return Move(
            from_pos=move.from_pos,
            to_pos=move.to_pos,
            piece=move.piece,
            captured=captured,
            is_check=is_check,
            is_capture=captured is not None
        )
    
    def _is_legal(self, move: Move) -> bool:
        """验证走棋是否合法（不走入将军）"""
        # 模拟走棋
        # 检查是否被将军
        # 恢复棋盘
        pass
    
    def _get_piece_moves(self, pos: str, piece: str) -> List[Move]:
        """获取棋子所有可能的走法"""
        piece_type = piece.upper()
        
        if piece_type == 'K':  # 将/帅
            return self._get_king_moves(pos, piece)
        elif piece_type == 'A':  # 士/仕
            return self._get_advisor_moves(pos, piece)
        elif piece_type == 'B':  # 象/相
            return self._get_bishop_moves(pos, piece)
        elif piece_type == 'N':  # 马
            return self._get_knight_moves(pos, piece)
        elif piece_type == 'R':  # 车
            return self._get_rook_moves(pos, piece)
        elif piece_type == 'C':  # 炮
            return self._get_cannon_moves(pos, piece)
        elif piece_type == 'P':  # 兵/卒
            return self._get_pawn_moves(pos, piece)
        
        return []
    
    def _is_in_check(self, color: str) -> bool:
        """检查是否被将军"""
        # 找到将/帅位置
        # 检查是否有敌方棋子可以攻击
        pass
    
    def is_checkmate(self) -> bool:
        """检查是否将死"""
        if not self._is_in_check(self.turn):
            return False
        return len(self.get_legal_moves()) == 0
    
    def is_stalemate(self) -> bool:
        """检查是否困毙"""
        if self._is_in_check(self.turn):
            return False
        return len(self.get_legal_moves()) == 0
```

---

#### 5.1.3 各棋子走法规则（Day 5-6）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-11** | 实现将/帅走法（九宫格内） | 2h | GAME-BE-06 |
| **GAME-BE-12** | 实现士/仕走法（九宫格斜线） | 2h | GAME-BE-06 |
| **GAME-BE-13** | 实现象/相走法（田字，不能过河） | 2h | GAME-BE-06 |
| **GAME-BE-14** | 实现马走法（日字，蹩马腿检测） | 3h | GAME-BE-06 |
| **GAME-BE-15** | 实现车走法（直线） | 2h | GAME-BE-06 |
| **GAME-BE-16** | 实现炮走法（直线，隔山打牛） | 3h | GAME-BE-06 |
| **GAME-BE-17** | 实现兵/卒走法（过河前后可横走） | 2h | GAME-BE-06 |

---

#### 5.1.4 服务层（Day 7-8）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-18** | 创建 GameService（对局 CRUD） | 4h | GAME-BE-01 |
| **GAME-BE-19** | 创建 MoveService（走棋处理） | 4h | GAME-BE-18 |
| **GAME-BE-20** | 创建 GameResultService（结果判定） | 3h | GAME-BE-18 |
| **GAME-BE-21** | 创建 TimerService（计时器） | 3h | GAME-BE-18 |
| **GAME-BE-22** | 实现中文记谱转换 | 2h | GAME-BE-05 |

**代码结构**：
```python
# apps/games/services.py
from django.db import transaction
from django.utils import timezone
from .models import Game, GameMove
from .engine.board import Board, Move

class GameService:
    @transaction.atomic
    def create_game(self, user, game_type: str, **kwargs) -> Game:
        """创建对局"""
        game = Game.objects.create(
            red_player_id=user.id if game_type == 'single' and kwargs.get('player_side') == 'red' else None,
            black_player_id=user.id if game_type == 'single' and kwargs.get('player_side') == 'black' else None,
            game_type=game_type,
            status='waiting',
            fen_start=Board.STARTING_FEN,
            fen_current=Board.STARTING_FEN,
            turn='red',
            time_control_base=kwargs.get('base_time', 600),
            time_control_increment=kwargs.get('increment', 0),
            red_time_remaining=kwargs.get('base_time', 600),
            black_time_remaining=kwargs.get('base_time', 600),
            ai_level=kwargs.get('ai_level'),
            ai_side=kwargs.get('player_side'),
        )
        
        if game_type == 'single':
            game.status = 'playing'
            game.started_at = timezone.now()
            game.save()
        
        return game
    
    @transaction.atomic
    def make_move(self, game_id: str, move_data: dict, user) -> Tuple[bool, dict]:
        """执行走棋"""
        game = Game.objects.select_for_update().get(id=game_id)
        
        # 验证游戏状态
        if game.status != 'playing':
            return False, {'error': '游戏未进行中'}
        
        # 验证是否是当前玩家的回合
        board = Board(game.fen_current)
        if not self._is_player_turn(game, user):
            return False, {'error': '不是你的回合'}
        
        # 验证走棋合法性
        move = Move(
            from_pos=move_data['from'],
            to_pos=move_data['to'],
            piece=board.get_piece(move_data['from'])
        )
        
        if not self._is_valid_move(board, move):
            return False, {'error': '无效走棋'}
        
        # 执行走棋
        board.make_move(move)
        
        # 创建走棋记录
        game_move = GameMove.objects.create(
            game_id=game_id,
            move_number=game.move_count + 1,
            piece=move.piece,
            from_pos=move.from_pos,
            to_pos=move.to_pos,
            captured=move.captured,
            is_check=board._is_in_check(board.turn),
            is_capture=move.captured is not None,
            notation=self._to_chinese_notation(move, board.turn),
            fen_after=board.to_fen(),
            time_remaining=self._get_time_remaining(game, board.turn)
        )
        
        # 更新游戏状态
        game.fen_current = board.to_fen()
        game.turn = board.turn
        game.move_count += 1
        game.save()
        
        # 检查游戏结束
        if board.is_checkmate():
            return self._end_game(game, winner=game.turn, reason='checkmate')
        elif board.is_stalemate():
            return self._end_game(game, winner='draw', reason='stalemate')
        
        return True, {
            'move': move_data,
            'fen': board.to_fen(),
            'turn': board.turn,
            'is_check': board._is_in_check(board.turn)
        }
```

---

#### 5.1.5 API 视图层（Day 9-10）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-23** | 创建 GameCreateView | 2h | GAME-BE-18 |
| **GAME-BE-24** | 创建 GameDetailView | 1h | GAME-BE-18 |
| **GAME-BE-25** | 创建 GameListView | 2h | GAME-BE-18 |
| **GAME-BE-26** | 创建 GameHistoryView | 2h | GAME-BE-18 |
| **GAME-BE-27** | 创建 MoveView（走棋 API） | 3h | GAME-BE-19 |
| **GAME-BE-28** | 创建 GameReplayView | 2h | GAME-BE-18 |

---

#### 5.1.6 WebSocket Consumer（Day 11-13）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-BE-29** | 创建 GameConsumer（WebSocket） | 6h | GAME-BE-19 |
| **GAME-BE-30** | 实现房间管理（加入/离开） | 3h | GAME-BE-29 |
| **GAME-BE-31** | 实现走棋广播 | 2h | GAME-BE-30 |
| **GAME-BE-32** | 实现游戏状态同步 | 3h | GAME-BE-30 |
| **GAME-BE-33** | 实现聊天功能 | 2h | GAME-BE-30 |
| **GAME-BE-34** | 实现心跳检测 | 2h | GAME-BE-29 |

**代码结构**：
```python
# apps/games/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """建立连接"""
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope['user']
        
        # 验证用户权限
        if not await self._can_join_game():
            await self.close()
            return
        
        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 发送当前游戏状态
        game_state = await self._get_game_state()
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'data': game_state
        }))
    
    async def disconnect(self, close_code):
        """断开连接"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # 更新玩家在线状态
        await self._update_player_online(False)
    
    async def receive(self, text_data):
        """接收客户端消息"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'make_move':
            await self._handle_move(data)
        elif message_type == 'resign':
            await self._handle_resign(data)
        elif message_type == 'offer_draw':
            await self._handle_draw_offer(data)
        elif message_type == 'accept_draw':
            await self._handle_draw_accept(data)
        elif message_type == 'chat':
            await self._handle_chat(data)
        elif message_type == 'heartbeat':
            await self._handle_heartbeat(data)
    
    async def _handle_move(self, data):
        """处理走棋"""
        game_id = data['game_id']
        move_data = data['move']
        
        # 服务端验证走棋
        success, result = await database_sync_to_async(
            game_service.make_move
        )(game_id, move_data, self.user)
        
        if success:
            # 广播走棋
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'move_made',
                    'data': result
                }
            )
        else:
            # 发送错误
            await self.send(text_data=json.dumps({
                'type': 'move_invalid',
                'data': result
            }))
    
    async def move_made(self, event):
        """广播走棋消息"""
        await self.send(text_data=json.dumps({
            'type': 'move_made',
            'data': event['data']
        }))
    
    async def game_end(self, event):
        """广播游戏结束"""
        await self.send(text_data=json.dumps({
            'type': 'game_end',
            'data': event['data']
        }))
```

---

### 5.2 前端实现

#### 5.2.1 棋盘组件（Day 14-16）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-FE-01** | 创建棋盘 SVG 组件（Board） | 6h | - |
| **GAME-FE-02** | 创建棋子组件（Piece） | 3h | GAME-FE-01 |
| **GAME-FE-03** | 实现走棋动画 | 4h | GAME-FE-02 |
| **GAME-FE-04** | 实现合法走法提示 | 3h | GAME-FE-01 |
| **GAME-FE-05** | 实现选中棋子高亮 | 2h | GAME-FE-02 |

**代码结构**：
```typescript
// src/components/board/Board.tsx
import React, { useMemo, useCallback } from 'react'
import { Piece } from './Piece'
import { parseFen, type BoardState } from '@/utils/fen'

interface BoardProps {
  fen: string
  onMove: (from: string, to: string) => void
  orientation?: 'red' | 'black'
  showHints?: boolean
  selectedPos?: string
  legalMoves?: string[]
}

export const Board: React.FC<BoardProps> = ({
  fen,
  onMove,
  orientation = 'red',
  showHints = true,
  selectedPos,
  legalMoves
}) => {
  const boardState = useMemo(() => parseFen(fen), [fen])
  
  const handleClick = useCallback((position: string) => {
    if (selectedPos) {
      // 已选中棋子，尝试移动
      if (legalMoves?.includes(position)) {
        onMove(selectedPos, position)
      } else {
        // 点击其他棋子，切换选中
      }
    } else {
      // 未选中，选择棋子
    }
  }, [selectedPos, legalMoves, onMove])
  
  return (
    <svg viewBox="0 0 450 500" className="board">
      {/* 棋盘网格 */}
      <g className="grid">
        {/* 横线 */}
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={`h-${i}`} x1="25" y1={25 + i * 50} x2="425" y2={25 + i * 50} />
        ))}
        {/* 竖线 */}
        {Array.from({ length: 9 }).map((_, i) => (
          <line key={`v-${i}`} x1={25 + i * 50} y1="25" x2={25 + i * 50} y2="475" />
        ))}
        {/* 九宫格、河界等 */}
      </g>
      
      {/* 棋子 */}
      {boardState.squares.map((piece, index) => (
        <Piece
          key={index}
          piece={piece}
          position={piece.position}
          isSelected={selectedPos === piece.position}
          onClick={() => handleClick(piece.position)}
        />
      ))}
      
      {/* 合法走法提示 */}
      {showHints && legalMoves?.map(pos => (
        <circle
          key={pos}
          cx={getX(pos)}
          cy={getY(pos)}
          r="10"
          fill="rgba(0, 255, 0, 0.3)"
        />
      ))}
    </svg>
  )
}
```

---

#### 5.2.2 游戏页面（Day 17-18）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-FE-06** | 创建游戏大厅页面 | 4h | - |
| **GAME-FE-07** | 创建对局页面（GamePage） | 6h | GAME-FE-01 |
| **GAME-FE-08** | 创建游戏信息面板 | 3h | GAME-FE-07 |
| **GAME-FE-09** | 创建计时器组件 | 3h | GAME-FE-07 |
| **GAME-FE-10** | 创建走棋历史记录面板 | 3h | GAME-FE-07 |
| **GAME-FE-11** | 创建游戏结束弹窗 | 2h | GAME-FE-07 |

---

#### 5.2.3 WebSocket 管理（Day 18-19）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-FE-12** | 创建 WebSocket Manager | 4h | - |
| **GAME-FE-13** | 实现自动重连 | 3h | GAME-FE-12 |
| **GAME-FE-14** | 实现心跳机制 | 2h | GAME-FE-12 |
| **GAME-FE-15** | 实现状态同步 | 3h | GAME-FE-12 |

---

### 5.3 测试实现

#### 5.3.1 后端测试（Day 20-21）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-TEST-01** | 编写 FEN 解析器测试 | 2h | GAME-BE-05 |
| **GAME-TEST-02** | 编写棋子走法测试 | 4h | GAME-BE-11~17 |
| **GAME-TEST-03** | 编写将军/将死检测测试 | 3h | GAME-BE-08~09 |
| **GAME-TEST-04** | 编写走棋 API 测试 | 3h | GAME-BE-27 |
| **GAME-TEST-05** | 编写游戏结束判定测试 | 2h | GAME-BE-20 |
| **GAME-TEST-06** | 编写 WebSocket 集成测试 | 4h | GAME-BE-29 |

---

#### 5.3.2 前端测试（Day 21-22）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **GAME-TEST-07** | 编写棋盘组件测试 | 3h | GAME-FE-01 |
| **GAME-TEST-08** | 编写走棋交互测试 | 3h | GAME-FE-07 |
| **GAME-TEST-09** | 编写 WebSocket 连接测试 | 2h | GAME-FE-12 |

---

### 5.4 任务时间线

```
Week 1-2: 后端核心
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│BE-01 │BE-05 │BE-07 │BE-11 │BE-14 │BE-18 │ 休息 │
│BE-04 │BE-06 │BE-08 │BE-12 │BE-15 │BE-19 │      │
│      │      │      │      │      │      │      │
│      │BE-09 │BE-13 │BE-16 │BE-17 │BE-20 │      │
│      │      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 3: 后端 API+WebSocket
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│BE-23 │BE-29 │BE-31 │BE-33 │FE-01 │FE-04 │ 休息 │
│BE-28 │BE-30 │BE-32 │BE-34 │FE-03 │FE-05 │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 4: 前端实现
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│FE-06 │FE-07 │FE-09 │FE-12 │FE-14 │TEST-1│ 休息 │
│      │FE-08 │FE-10 │FE-13 │FE-15 │TEST-6│      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 5: 测试与联调
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│TEST-7│TEST-9│ 联调 │ 联调 │ 修复 │ 验收 │ 休息 │
│      │      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

**总工时预估**：约 120 小时（3 周）

---

## 6. 测试计划

### 6.1 单元测试

#### 6.1.1 规则引擎测试

| 测试模块 | 测试用例 | 预期结果 |
|---------|---------|---------|
| **FENParser** | 解析初始 FEN | 正确解析所有棋子位置 |
| **FENParser** | 生成 FEN | 与输入 FEN 一致 |
| **Board** | 获取初始合法走法 | 红方有 20 种合法走法 |
| **Board** | 马走日字 | 返回正确的马走法 |
| **Board** | 蹩马腿检测 | 蹩腿时不能走 |
| **Board** | 象不过河 | 象不能走到对方半场 |
| **Board** | 将不出宫 | 将不能走出九宫格 |
| **MoveValidator** | 验证合法走棋 | 返回 true |
| **MoveValidator** | 验证非法走棋 | 返回 false |
| **CheckDetector** | 检测将军 | 正确识别将军状态 |
| **CheckmateDetector** | 检测将死 | 正确识别将死 |
| **CheckmateDetector** | 检测困毙 | 正确识别困毙 |

**测试代码示例**：
```python
# apps/games/tests/test_board.py
import pytest
from apps.games.engine.board import Board, Move

class TestBoard:
    def test_initial_legal_moves(self):
        board = Board()
        moves = board.get_legal_moves()
        
        # 红方初始有 20 种合法走法
        assert len(moves) == 20
    
    def test_knight_move(self):
        board = Board()
        # 移动马
        move = Move(from_pos='b1', to_pos='c3', piece='N')
        result = board.make_move(move)
        
        assert result is not None
    
    def test_knight_blocked(self):
        board = Board('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/1N2KABNR/9 w - - 0 1')
        # 马被蹩腿
        moves = board._get_knight_moves('b1', 'N')
        
        assert 'c3' not in [m.to_pos for m in moves]
    
    def test_elephant_crossing(self):
        board = Board()
        # 尝试让象过河
        moves = board._get_bishop_moves('c1', 'B')
        
        # 象不能过河
        assert all(not m.to_pos.endswith('6') for m in moves)
    
    def test_checkmate_detection(self):
        # 设置将死局面
        board = Board('3ak4/9/9/9/9/9/9/9/9/4K4 w - - 0 1')
        
        assert board.is_checkmate()
```

---

### 6.2 集成测试

| 测试场景 | 测试步骤 | 预期结果 |
|---------|---------|---------|
| **创建单机对局** | 调用创建 API | 返回游戏 ID，状态为 playing |
| **走棋流程** | 1. 创建对局<br>2. 执行走棋<br>3. 验证走棋记录 | 走棋成功，记录入库 |
| **非法走棋拦截** | 尝试走非法棋 | 返回错误，棋盘不变 |
| **游戏结束判定** | 1. 构造将死局面<br>2. 执行最后一步<br>3. 验证游戏状态 | 游戏结束，胜者正确 |
| **WebSocket 走棋** | 1. 建立 WS 连接<br>2. 发送走棋消息<br>3. 验证广播 | 双方收到走棋通知 |

---

## 7. 验收标准

### 7.1 功能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **AC-01** | 可以创建单机对局 | 调用创建 API | 返回 201，游戏状态正确 |
| **AC-02** | 可以创建好友对局 | 调用创建 API | 返回房间链接 |
| **AC-03** | 走棋规则正确 | 测试各棋子走法 | 符合中国象棋规则 |
| **AC-04** | 非法走棋被拦截 | 尝试非法走棋 | 返回错误提示 |
| **AC-05** | 将军检测正确 | 构造将军局面 | 正确识别将军 |
| **AC-06** | 将死检测正确 | 构造将死局面 | 游戏结束，胜者正确 |
| **AC-07** | 困毙检测正确 | 构造困毙局面 | 游戏结束，和棋 |
| **AC-08** | 走棋记录完整 | 查看历史记录 | 每步走棋都有记录 |
| **AC-09** | FEN 状态正确 | 对比 FEN 字符串 | 与实际棋盘一致 |
| **AC-10** | 计时器正常工作 | 进行对局 | 时间正确递减 |
| **AC-11** | 超时判负 | 时间耗尽 | 游戏结束，对方胜 |
| **AC-12** | WebSocket 实时同步 | 双方走棋 | 即时看到对方走棋 |
| **AC-13** | 断线检测 | 关闭连接 | 检测到掉线 |

---

### 7.2 性能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **PERF-01** | 走棋验证响应时间 | 压测 | P95 < 50ms |
| **PERF-02** | WebSocket 延迟 | 压测 | P95 < 30ms |
| **PERF-03** | 并发对局能力 | 压测 | 支持 100+ 同时对局 |
| **PERF-04** | 规则引擎性能 | 基准测试 | 生成合法走法<10ms |

---

## 8. 风险与应对

| 风险 ID | 风险描述 | 可能性 | 影响 | 应对措施 |
|--------|---------|--------|------|---------|
| **GAME-RISK-01** | 规则引擎实现复杂，bug 多 | 高 | 高 | 充分单元测试，逐步实现 |
| **GAME-RISK-02** | WebSocket 连接不稳定 | 中 | 高 | 实现重连机制，状态同步 |
| **GAME-RISK-03** | 走棋状态不一致 | 中 | 高 | 服务端权威验证，定期同步 |
| **GAME-RISK-04** | 性能瓶颈 | 中 | 中 | 优化规则引擎，缓存合法走法 |
| **GAME-RISK-05** | 计时器作弊 | 中 | 中 | 服务端计时，前端仅展示 |

---

## 附录

### A. FEN 格式说明

```
FEN (Forsyth-Edwards Notation) 格式：

棋盘位置 回合 王车易位 吃过路兵 50 步规则 回合数

示例（初始局面）：
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1

棋盘位置：
- r/n/b/a/k/a/b/n/r: 黑方棋子（小写）
- 9: 空行
- 1c5c1: 炮的位置
- p1p1p1p1p: 卒的位置
- 9: 河界
- 9: 河界
- P1P1P1P1P: 兵的位置
- 1C5C1: 炮的位置
- 9: 空行
- RNBAKABNR: 红方棋子（大写）

回合：
- w: 红方走棋（white，红方先手）
- b: 黑方走棋

王车易位：中国象棋无，固定为 -

吃过路兵：中国象棋无，固定为 -

50 步规则：自上次吃子或动兵以来的步数

回合数：当前是第几回合
```

---

### B. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | planner agent | 初始版本，完成游戏对局系统规划 |

---

**游戏对局系统规划完成！** ✅

下一步：规划 AI 对弈系统（ai-opponent-plan.md）
