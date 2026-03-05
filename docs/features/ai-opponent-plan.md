# 🤖 AI 对弈系统 - 功能规划文档

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**优先级**：P0  
**状态**：待实现

---

## 1. 功能概述

### 1.1 功能描述

AI 对弈系统是中国象棋平台的单机模式核心功能，通过集成 Stockfish 象棋引擎，提供从入门到大师级的 10 级难度 AI 对战。该系统需要实现 AI 走棋接口、思考时间控制、难度等级映射和走棋提示功能，为用户提供优质的单机对弈体验。

### 1.2 功能范围

**包含**：
- Stockfish 引擎集成
- 10 级难度设计（入门到大师）
- AI 走棋接口（同步/异步）
- 思考时间控制
- 走棋提示功能（单机模式）
- AI 棋力限制（难度映射）
- 引擎池管理（多实例）

**不包含**（P1/P2）：
- AI 棋局分析（P1）
- 残局挑战（P1）
- AI 走棋解释（P2）
- 棋力评估报告（P2）

### 1.3 技术选型

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| **AI 引擎** | Stockfish 16 | 开源最强象棋引擎 |
| **Python 封装** | python-stockfish | 成熟的 UCI 协议封装 |
| **调用方式** | Celery 异步任务 | 避免阻塞主线程 |
| **引擎管理** | 引擎池模式 | 多实例并行，提高并发 |
| **难度控制** | Skill Level + 深度 + 时间 | 多维度控制棋力 |

---

## 2. 用户故事

### 2.1 核心用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|--------|
| **US-AI-01** | 作为新手玩家，我希望选择低难度 AI 练习，以便学习基础走法 | 难度 1-3 级，AI 响应时间<1 秒，有意放水 | P0 |
| **US-AI-02** | 作为中级玩家，我希望选择中等难度 AI 对战，以便提升棋力 | 难度 4-7 级，AI 响应时间<2 秒，棋力相当 | P0 |
| **US-AI-03** | 作为高级玩家，我希望挑战高难度 AI，以便测试水平 | 难度 8-10 级，AI 深度思考，棋力强劲 | P0 |
| **US-AI-04** | 作为玩家，我希望 AI 走棋速度合理，以便有思考时间 | 根据难度调整思考时间，不会过快或过慢 | P0 |
| **US-AI-05** | 作为玩家，我希望在困惑时获得 AI 提示，以便学习更好走法 | 提示响应时间<3 秒，提供 3 个候选走法 | P0 |
| **US-AI-06** | 作为玩家，我希望选择执红或执黑，以便决定先手 | 支持选择先手，AI 后手应对正确 | P0 |
| **US-AI-07** | 作为玩家，我希望 AI 有意料之外的走法，以便增加趣味性 | AI 走法有一定随机性，不完全可预测 | P0 |

### 2.2 用户旅程地图

```
单机 AI 对战流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 选择单机 │ →  │ 选择难度 │ →  │ 选择先手 │ →  │ 开始对局 │ →  │ 人机对战 │ →  │ 游戏结束 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │                              │
                                    ▼                              ▼
                          初始化游戏                         玩家走棋
                          启动 AI 引擎（异步）                  AI 思考并回应
                          加载难度配置                       显示提示（可选）
```

---

## 3. API 设计

### 3.1 API 总览

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/ai/move/ | 获取 AI 走棋 | 是 |
| POST | /api/ai/hint/ | 获取走棋提示 | 是 |
| POST | /api/ai/evaluate/ | 评估当前局面 | 是 |
| GET | /api/ai/difficulties/ | 获取难度列表 | 否 |

### 3.2 WebSocket 消息

| 消息类型 | 方向 | 描述 |
|---------|------|------|
| `ai_thinking` | S→C | AI 思考中通知 |
| `ai_move` | S→C | AI 走棋完成 |
| `ai_hint` | S→C | AI 提示返回 |

---

### 3.3 API 详细设计

#### 3.3.1 获取 AI 走棋

**请求**：
```http
POST /api/ai/move/
Authorization: Bearer {token}
Content-Type: application/json

{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "time_limit": 2000
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "move": {
      "from": "c1",
      "to": "c4",
      "piece": "C",
      "notation": "炮八进四"
    },
    "fen_after": "rnbakabnr/9/1c5c1/p1p1p1p1p/2C6/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",
    "evaluation": {
      "score": 0.35,
      "depth": 15,
      "time_ms": 1850
    },
    "thinking_time": 1850
  }
}
```

**评估分数说明**：
- 正分：红方优势
- 负分：黑方优势
- 0：均势

---

#### 3.3.2 获取走棋提示

**请求**：
```http
POST /api/ai/hint/
Authorization: Bearer {token}
Content-Type: application/json

{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "difficulty": 5,
  "count": 3
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "hints": [
      {
        "move": {
          "from": "c1",
          "to": "c4",
          "piece": "C",
          "notation": "炮八进四"
        },
        "evaluation": 0.35,
        "rank": 1
      },
      {
        "move": {
          "from": "h2",
          "to": "h5",
          "piece": "C",
          "notation": "炮二进四"
        },
        "evaluation": 0.28,
        "rank": 2
      },
      {
        "move": {
          "from": "b1",
          "to": "c3",
          "piece": "N",
          "notation": "马八进七"
        },
        "evaluation": 0.22,
        "rank": 3
      }
    ],
    "thinking_time": 2100
  }
}
```

---

#### 3.3.3 评估局面

**请求**：
```http
POST /api/ai/evaluate/
Authorization: Bearer {token}
Content-Type: application/json

{
  "fen": "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",
  "depth": 15
}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "evaluation": {
      "score": 0.35,
      "score_text": "红方稍优",
      "depth": 15,
      "best_move": {
        "from": "c1",
        "to": "c4",
        "piece": "C",
        "notation": "炮八进四"
      }
    },
    "thinking_time": 1500
  }
}
```

**分数对照表**：
| 分数范围 | 优势描述 |
|---------|---------|
| > 2.0 | 一方胜势 |
| 1.0 ~ 2.0 | 一方明显优势 |
| 0.5 ~ 1.0 | 一方稍优 |
| -0.5 ~ 0.5 | 均势 |
| -1.0 ~ -0.5 | 一方稍劣 |
| -2.0 ~ -1.0 | 一方明显劣势 |
| < -2.0 | 一方败势 |

---

#### 3.3.4 获取难度列表

**请求**：
```http
GET /api/ai/difficulties/
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "difficulties": [
      {
        "level": 1,
        "name": "入门",
        "description": "适合完全新手，AI 会犯明显错误",
        "elo_estimate": 400,
        "think_time": "0.5 秒"
      },
      {
        "level": 2,
        "name": "新手",
        "description": "适合刚学规则的玩家",
        "elo_estimate": 600,
        "think_time": "0.5 秒"
      },
      {
        "level": 3,
        "name": "初级",
        "description": "适合有一定基础的玩家",
        "elo_estimate": 800,
        "think_time": "1.0 秒"
      },
      {
        "level": 4,
        "name": "入门",
        "description": "适合初学者",
        "elo_estimate": 1000,
        "think_time": "1.0 秒"
      },
      {
        "level": 5,
        "name": "中级",
        "description": "适合普通玩家",
        "elo_estimate": 1200,
        "think_time": "1.5 秒"
      },
      {
        "level": 6,
        "name": "中级",
        "description": "适合有一定经验的玩家",
        "elo_estimate": 1400,
        "think_time": "1.5 秒"
      },
      {
        "level": 7,
        "name": "高级",
        "description": "适合高手",
        "elo_estimate": 1600,
        "think_time": "2.0 秒"
      },
      {
        "level": 8,
        "name": "高级",
        "description": "适合资深玩家",
        "elo_estimate": 1800,
        "think_time": "2.0 秒"
      },
      {
        "level": 9,
        "name": "大师",
        "description": "专业棋手水平",
        "elo_estimate": 2000,
        "think_time": "3.0 秒"
      },
      {
        "level": 10,
        "name": "大师",
        "description": "顶级棋手水平",
        "elo_estimate": 2200,
        "think_time": "5.0 秒"
      }
    ]
  }
}
```

---

## 4. 数据库设计

### 4.1 AI 对局配置表（ai_configs）

```sql
CREATE TABLE ai_configs (
    -- 主键
    id              SERIAL PRIMARY KEY,
    
    -- 难度配置
    difficulty_level INTEGER UNIQUE NOT NULL,  -- 1-10
    name            VARCHAR(50) NOT NULL,
    description     TEXT,
    
    -- Stockfish 参数
    skill_level     INTEGER NOT NULL,           -- 0-20
    search_depth    INTEGER NOT NULL,           -- 搜索深度
    think_time_ms   INTEGER NOT NULL,           -- 思考时间（毫秒）
    move_overhead   INTEGER DEFAULT 100,        -- 移动开销（毫秒）
    threads         INTEGER DEFAULT 2,          -- 线程数
    hash_mb         INTEGER DEFAULT 128,        -- 哈希表大小（MB）
    
    -- 棋力评估
    elo_estimate    INTEGER NOT NULL,
    
    -- 启用状态
    is_active       BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- 约束
    CONSTRAINT chk_difficulty_level CHECK (difficulty_level BETWEEN 1 AND 10),
    CONSTRAINT chk_skill_level CHECK (skill_level BETWEEN 0 AND 20),
    CONSTRAINT chk_search_depth CHECK (search_depth BETWEEN 5 AND 25)
);

-- 初始数据
INSERT INTO ai_configs (difficulty_level, name, description, skill_level, search_depth, think_time_ms, elo_estimate) VALUES
(1, '入门', '适合完全新手，AI 会犯明显错误', 0, 5, 500, 400),
(2, '新手', '适合刚学规则的玩家', 2, 7, 500, 600),
(3, '初级', '适合有一定基础的玩家', 4, 9, 1000, 800),
(4, '入门', '适合初学者', 6, 11, 1000, 1000),
(5, '中级', '适合普通玩家', 8, 13, 1500, 1200),
(6, '中级', '适合有一定经验的玩家', 10, 15, 1500, 1400),
(7, '高级', '适合高手', 12, 17, 2000, 1600),
(8, '高级', '适合资深玩家', 14, 19, 2000, 1800),
(9, '大师', '专业棋手水平', 16, 21, 3000, 2000),
(10, '大师', '顶级棋手水平', 20, 25, 5000, 2200);

-- 索引
CREATE INDEX idx_ai_configs_level ON ai_configs(difficulty_level);
CREATE INDEX idx_ai_configs_active ON ai_configs(is_active) WHERE is_active = TRUE;
```

---

### 4.2 AI 对局记录表（ai_game_records）

用于分析 AI 对局数据，优化 AI 行为。

```sql
CREATE TABLE ai_game_records (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    
    -- 外键
    game_id         UUID REFERENCES games(id) ON DELETE CASCADE NOT NULL,
    
    -- AI 信息
    ai_level        INTEGER NOT NULL,
    ai_side         VARCHAR(5) NOT NULL,       -- 'red', 'black'
    
    -- 对局统计
    total_moves     INTEGER NOT NULL,
    ai_wins         INTEGER NOT NULL,
    ai_losses       INTEGER NOT NULL,
    ai_draws        INTEGER NOT NULL,
    
    -- 性能指标
    avg_think_time  INTEGER,                   -- 平均思考时间（毫秒）
    max_think_time  INTEGER,                   -- 最大思考时间（毫秒）
    avg_depth       INTEGER,                   -- 平均搜索深度
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 索引
CREATE INDEX idx_ai_records_game ON ai_game_records(game_id);
CREATE INDEX idx_ai_records_level ON ai_game_records(ai_level);
CREATE INDEX idx_ai_records_created ON ai_game_records(created_at DESC);
```

---

## 5. 实现步骤（任务分解）

### 5.1 后端实现

#### 5.1.1 Stockfish 引擎集成（Day 1-3）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-BE-01** | 安装 Stockfish 16 引擎 | 1h | - |
| **AI-BE-02** | 安装 python-stockfish 库 | 0.5h | AI-BE-01 |
| **AI-BE-03** | 创建 StockfishService 封装类 | 4h | AI-BE-02 |
| **AI-BE-04** | 实现基础走棋接口 | 3h | AI-BE-03 |
| **AI-BE-05** | 实现局面评估接口 | 2h | AI-BE-03 |
| **AI-BE-06** | 实现多 PV 分析（获取多个候选走法） | 3h | AI-BE-03 |

**代码结构**：
```python
# apps/ai/services/stockfish_service.py
from stockfish import Stockfish
from typing import List, Optional, Dict
from dataclasses import dataclass
from django.conf import settings

@dataclass
class AIMove:
    from_pos: str
    to_pos: str
    piece: str
    evaluation: float
    depth: int
    thinking_time: int
    notation: str = ""

class StockfishService:
    """Stockfish 引擎服务"""
    
    def __init__(self, difficulty: int = 5):
        """
        初始化 Stockfish 引擎
        
        Args:
            difficulty: 难度等级 1-10
        """
        config = self._get_difficulty_config(difficulty)
        
        self.engine = Stockfish(
            path=settings.STOCKFISH_PATH,
            depth=config['depth'],
            parameters={
                "Skill Level": config['skill_level'],
                "Move Overhead": config['move_overhead'],
                "Threads": config['threads'],
                "Hash": config['hash'],
                "UCI_LimitStrength": True,
                "UCI_Elo": config['elo'],
            }
        )
        
        self.config = config
    
    def _get_difficulty_config(self, difficulty: int) -> dict:
        """获取难度配置"""
        configs = {
            1: {'skill_level': 0, 'depth': 5, 'think_time': 500, 'elo': 400, 'move_overhead': 100, 'threads': 1, 'hash': 64},
            2: {'skill_level': 2, 'depth': 7, 'think_time': 500, 'elo': 600, 'move_overhead': 100, 'threads': 1, 'hash': 64},
            3: {'skill_level': 4, 'depth': 9, 'think_time': 1000, 'elo': 800, 'move_overhead': 100, 'threads': 2, 'hash': 128},
            4: {'skill_level': 6, 'depth': 11, 'think_time': 1000, 'elo': 1000, 'move_overhead': 100, 'threads': 2, 'hash': 128},
            5: {'skill_level': 8, 'depth': 13, 'think_time': 1500, 'elo': 1200, 'move_overhead': 100, 'threads': 2, 'hash': 128},
            6: {'skill_level': 10, 'depth': 15, 'think_time': 1500, 'elo': 1400, 'move_overhead': 100, 'threads': 2, 'hash': 128},
            7: {'skill_level': 12, 'depth': 17, 'think_time': 2000, 'elo': 1600, 'move_overhead': 100, 'threads': 2, 'hash': 256},
            8: {'skill_level': 14, 'depth': 19, 'think_time': 2000, 'elo': 1800, 'move_overhead': 100, 'threads': 2, 'hash': 256},
            9: {'skill_level': 16, 'depth': 21, 'think_time': 3000, 'elo': 2000, 'move_overhead': 100, 'threads': 4, 'hash': 512},
            10: {'skill_level': 20, 'depth': 25, 'think_time': 5000, 'elo': 2200, 'move_overhead': 100, 'threads': 4, 'hash': 512},
        }
        return configs.get(difficulty, configs[5])
    
    def get_best_move(self, fen: str, time_limit: int = None) -> AIMove:
        """
        获取最佳走棋
        
        Args:
            fen: 棋局 FEN 字符串
            time_limit: 思考时间限制（毫秒）
        
        Returns:
            AIMove: AI 走棋结果
        """
        import time
        start_time = time.time()
        
        # 设置局面
        self.engine.set_fen_position(fen)
        
        # 获取最佳走棋
        if time_limit:
            best_move = self.engine.get_best_move(time=time_limit)
        else:
            best_move = self.engine.get_best_move(time=self.config['think_time'])
        
        thinking_time = int((time.time() - start_time) * 1000)
        
        # 解析走棋
        from_pos, to_pos = self._parse_move(best_move)
        
        # 获取评估分数
        evaluation = self._get_evaluation()
        
        return AIMove(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=self._get_piece_at(from_pos, fen),
            evaluation=evaluation,
            depth=self.engine.get_current_depth(),
            thinking_time=thinking_time
        )
    
    def get_top_moves(self, fen: str, count: int = 3) -> List[Dict]:
        """
        获取多个候选走法（用于提示）
        
        Args:
            fen: 棋局 FEN 字符串
            count: 返回走法数量
        
        Returns:
            List[Dict]: 候选走法列表
        """
        self.engine.set_fen_position(fen)
        
        # 使用 MultiPV 获取多个走法
        self.engine.set_skill_level(self.config['skill_level'])
        self.engine.set_depth(self.config['depth'])
        
        # 获取顶级走法
        top_moves = []
        info = self.engine.get_stockfish_major_info()
        
        for i in range(min(count, len(info))):
            move_info = info[i]
            from_pos, to_pos = self._parse_move(move_info['move'])
            
            top_moves.append({
                'from': from_pos,
                'to': to_pos,
                'evaluation': move_info.get('score', 0),
                'depth': move_info.get('depth', 0),
            })
        
        return top_moves
    
    def evaluate_position(self, fen: str, depth: int = None) -> Dict:
        """
        评估当前局面
        
        Args:
            fen: 棋局 FEN 字符串
            depth: 搜索深度
        
        Returns:
            Dict: 评估结果
        """
        self.engine.set_fen_position(fen)
        
        if depth:
            self.engine.set_depth(depth)
        
        evaluation = self._get_evaluation()
        best_move = self.engine.get_best_move()
        
        return {
            'score': evaluation,
            'score_text': self._evaluation_to_text(evaluation),
            'best_move': best_move,
            'depth': self.engine.get_current_depth()
        }
    
    def _get_evaluation(self) -> float:
        """获取局面评估分数"""
        eval_info = self.engine.get_evaluation()
        
        # Stockfish 返回 {'type': 'cp', 'value': 35} 或 {'type': 'mate', 'value': 3}
        if eval_info['type'] == 'cp':
            # 百分比分，转换为小数
            return eval_info['value'] / 100.0
        elif eval_info['type'] == 'mate':
            # 将死，返回极大值
            return 100.0 if eval_info['value'] > 0 else -100.0
        
        return 0.0
    
    def _evaluation_to_text(self, score: float) -> str:
        """将评估分数转换为文字描述"""
        if score > 2.0:
            return "红方胜势"
        elif score > 1.0:
            return "红方明显优势"
        elif score > 0.5:
            return "红方稍优"
        elif score > -0.5:
            return "均势"
        elif score > -1.0:
            return "黑方稍优"
        elif score > -2.0:
            return "黑方明显优势"
        else:
            return "黑方胜势"
    
    def _parse_move(self, move_str: str) -> tuple:
        """解析 UCI 格式走棋"""
        # UCI 格式：e2e4, e7e5, b1c3
        from_pos = move_str[:2]
        to_pos = move_str[2:4]
        return from_pos, to_pos
    
    def _get_piece_at(self, pos: str, fen: str) -> str:
        """获取指定位置的棋子"""
        # 解析 FEN 获取棋子
        pass
    
    def set_difficulty(self, difficulty: int):
        """动态调整难度"""
        config = self._get_difficulty_config(difficulty)
        self.engine.set_skill_level(config['skill_level'])
        self.engine.set_depth(config['depth'])
        self.config = config
```

---

#### 5.1.2 引擎池管理（Day 4-5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-BE-07** | 创建 EnginePool 类 | 4h | AI-BE-03 |
| **AI-BE-08** | 实现引擎实例管理 | 3h | AI-BE-07 |
| **AI-BE-09** | 实现引擎健康检查 | 2h | AI-BE-08 |
| **AI-BE-10** | 实现引擎自动重启 | 2h | AI-BE-09 |

**代码结构**：
```python
# apps/ai/services/engine_pool.py
import asyncio
from typing import Optional, Dict
from .stockfish_service import StockfishService

class EnginePool:
    """Stockfish 引擎池"""
    
    def __init__(self, pool_size: int = 4):
        """
        初始化引擎池
        
        Args:
            pool_size: 引擎实例数量
        """
        self.pool_size = pool_size
        self.engines: Dict[int, StockfishService] = {}
        self.available = asyncio.Queue(maxsize=pool_size)
        self.in_use = set()
        
        # 初始化引擎实例
        for i in range(pool_size):
            engine = StockfishService(difficulty=5)  # 默认难度
            self.engines[i] = engine
        
        # 所有引擎初始可用
        for i in range(pool_size):
            self.available.put_nowait(i)
    
    async def acquire(self, difficulty: int = 5) -> StockfishService:
        """
        获取可用引擎
        
        Args:
            difficulty: 难度等级
        
        Returns:
            StockfishService: 引擎实例
        """
        # 等待可用引擎
        engine_id = await self.available.get()
        self.in_use.add(engine_id)
        
        # 设置难度
        engine = self.engines[engine_id]
        engine.set_difficulty(difficulty)
        
        return engine
    
    def release(self, engine: StockfishService):
        """
        释放引擎回池
        
        Args:
            engine: 引擎实例
        """
        # 找到引擎 ID
        for engine_id, eng in self.engines.items():
            if eng is engine:
                self.in_use.discard(engine_id)
                self.available.put_nowait(engine_id)
                break
    
    async def health_check(self):
        """健康检查，重启异常引擎"""
        for engine_id, engine in self.engines.items():
            if engine_id in self.in_use:
                continue
            
            try:
                # 简单测试
                engine.engine.get_best_move(time=100)
            except Exception as e:
                # 重启引擎
                await self._restart_engine(engine_id)
    
    async def _restart_engine(self, engine_id: int):
        """重启引擎实例"""
        try:
            self.engines[engine_id].engine.quit()
        except:
            pass
        
        self.engines[engine_id] = StockfishService(difficulty=5)
```

---

#### 5.1.3 Celery 异步任务（Day 5-6）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-BE-11** | 创建 AI 走棋 Celery 任务 | 3h | AI-BE-03 |
| **AI-BE-12** | 创建 AI 提示 Celery 任务 | 2h | AI-BE-03 |
| **AI-BE-13** | 创建 AI 评估 Celery 任务 | 2h | AI-BE-03 |
| **AI-BE-14** | 实现任务超时处理 | 2h | AI-BE-11 |
| **AI-BE-15** | 实现任务进度通知 | 2h | AI-BE-11 |

**代码结构**：
```python
# apps/ai/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services.stockfish_service import StockfishService
from .services.engine_pool import engine_pool

@shared_task(queue='ai', bind=True, time_limit=30)
def get_ai_move(self, fen: str, difficulty: int = 5, time_limit: int = 2000, game_id: str = None):
    """
    获取 AI 走棋（异步任务）
    
    Args:
        fen: 棋局 FEN 字符串
        difficulty: 难度等级
        time_limit: 思考时间限制（毫秒）
        game_id: 游戏 ID（用于进度通知）
    
    Returns:
        dict: AI 走棋结果
    """
    engine = None
    try:
        # 从池中获取引擎
        engine = engine_pool.acquire_sync(difficulty)
        
        # 发送思考中通知
        if game_id:
            self._send_notification(game_id, 'ai_thinking', {
                'difficulty': difficulty,
                'estimated_time': time_limit
            })
        
        # 获取走棋
        move = engine.get_best_move(fen, time_limit)
        
        result = {
            'move': {
                'from': move.from_pos,
                'to': move.to_pos,
                'piece': move.piece,
            },
            'evaluation': move.evaluation,
            'depth': move.depth,
            'thinking_time': move.thinking_time
        }
        
        return result
    
    except Exception as e:
        # 记录错误
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    finally:
        if engine:
            engine_pool.release(engine)
    
    def _send_notification(self, game_id: str, event_type: str, data: dict):
        """发送 WebSocket 通知"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'game_{game_id}',
            {
                'type': event_type,
                'data': data
            }
        )

@shared_task(queue='ai', bind=True, time_limit=30)
def get_ai_hint(self, fen: str, difficulty: int = 5, count: int = 3):
    """
    获取 AI 走棋提示
    
    Args:
        fen: 棋局 FEN 字符串
        difficulty: 难度等级
        count: 提示数量
    
    Returns:
        dict: 提示列表
    """
    engine = StockfishService(difficulty=difficulty)
    
    try:
        top_moves = engine.get_top_moves(fen, count)
        
        return {
            'hints': top_moves,
            'thinking_time': sum(m.get('time', 0) for m in top_moves)
        }
    finally:
        engine.engine.quit()

@shared_task(queue='ai', bind=True, time_limit=30)
def evaluate_position(self, fen: str, depth: int = 15):
    """
    评估棋局
    
    Args:
        fen: 棋局 FEN 字符串
        depth: 搜索深度
    
    Returns:
        dict: 评估结果
    """
    engine = StockfishService(difficulty=5)
    
    try:
        evaluation = engine.evaluate_position(fen, depth)
        return evaluation
    finally:
        engine.engine.quit()
```

---

#### 5.1.4 API 视图层（Day 7-8）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-BE-16** | 创建 AIMoveView | 2h | AI-BE-11 |
| **AI-BE-17** | 创建 AIHintView | 2h | AI-BE-12 |
| **AI-BE-18** | 创建 AIEvaluateView | 2h | AI-BE-13 |
| **AI-BE-19** | 创建 AIDifficultyListView | 1h | - |
| **AI-BE-20** | 实现异步任务轮询接口 | 2h | AI-BE-11 |

**代码结构**：
```python
# apps/ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from django.http import JsonResponse
from .tasks import get_ai_move, get_ai_hint, evaluate_position
from .models import AIConfig

class AIMoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """获取 AI 走棋"""
        fen = request.data.get('fen')
        difficulty = request.data.get('difficulty', 5)
        time_limit = request.data.get('time_limit', 2000)
        game_id = request.data.get('game_id')
        
        if not fen:
            return Response({
                'success': False,
                'error': {'code': 'MISSING_FEN', 'message': '缺少 FEN 参数'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步执行
        task = get_ai_move.delay(fen, difficulty, time_limit, game_id)
        
        # 返回任务 ID，前端轮询结果
        return Response({
            'success': True,
            'data': {
                'task_id': task.id,
                'status': 'pending'
            }
        })

class AIMoveResultView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, task_id):
        """获取 AI 走棋结果（轮询）"""
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return Response({
                'success': True,
                'data': {'status': 'pending'}
            })
        elif task_result.state == 'STARTED':
            return Response({
                'success': True,
                'data': {'status': 'processing'}
            })
        elif task_result.state == 'SUCCESS':
            return Response({
                'success': True,
                'data': {
                    'status': 'completed',
                    'result': task_result.result
                }
            })
        elif task_result.state == 'FAILURE':
            return Response({
                'success': False,
                'error': {'code': 'AI_ERROR', 'message': str(task_result.result)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': {'status': task_result.state}
        })

class AIHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """获取 AI 提示"""
        fen = request.data.get('fen')
        difficulty = request.data.get('difficulty', 5)
        count = request.data.get('count', 3)
        
        if not fen:
            return Response({
                'success': False,
                'error': {'code': 'MISSING_FEN', 'message': '缺少 FEN 参数'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = get_ai_hint.delay(fen, difficulty, count)
        
        return Response({
            'success': True,
            'data': {'task_id': task.id}
        })

class AIEvaluateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """评估局面"""
        fen = request.data.get('fen')
        depth = request.data.get('depth', 15)
        
        if not fen:
            return Response({
                'success': False,
                'error': {'code': 'MISSING_FEN', 'message': '缺少 FEN 参数'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task = evaluate_position.delay(fen, depth)
        
        return Response({
            'success': True,
            'data': {'task_id': task.id}
        })

class AIDifficultyListView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """获取难度列表"""
        configs = AIConfig.objects.filter(is_active=True).order_by('difficulty_level')
        
        difficulties = [
            {
                'level': config.difficulty_level,
                'name': config.name,
                'description': config.description,
                'elo_estimate': config.elo_estimate,
                'think_time': f"{config.think_time_ms / 1000:.1f}秒"
            }
            for config in configs
        ]
        
        return Response({
            'success': True,
            'data': {'difficulties': difficulties}
        })
```

---

### 5.2 前端实现

#### 5.2.1 AI 服务层（Day 9）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-FE-01** | 创建 AI API 服务 | 3h | - |
| **AI-FE-02** | 实现任务轮询逻辑 | 2h | AI-FE-01 |
| **AI-FE-03** | 实现 AI 思考状态管理 | 2h | AI-FE-01 |

**代码结构**：
```typescript
// src/services/aiService.ts
import axios from 'axios'

const aiApi = axios.create({
  baseURL: '/api/ai',
})

export interface AIMove {
  from: string
  to: string
  piece: string
  evaluation: number
  depth: number
  thinking_time: number
}

export interface AIHint {
  from: string
  to: string
  evaluation: number
  rank: number
}

export interface AITaskResult {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result?: AIMove | AIHint[]
  error?: string
}

class AIService {
  /**
   * 获取 AI 走棋
   */
  async getAIMove(fen: string, difficulty: number, timeLimit: number = 2000, gameId?: string): Promise<string> {
    const response = await aiApi.post('/move/', {
      fen,
      difficulty,
      time_limit: timeLimit,
      game_id: gameId
    })
    
    return response.data.data.task_id
  }
  
  /**
   * 轮询 AI 走棋结果
   */
  async pollAIMoveResult(taskId: string, maxAttempts: number = 30): Promise<AIMove> {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await aiApi.get(`/move/${taskId}/`)
      const result: AITaskResult = response.data.data
      
      if (result.status === 'completed' && result.result) {
        return result.result as AIMove
      } else if (result.status === 'failed') {
        throw new Error(result.error || 'AI 走棋失败')
      }
      
      // 等待 500ms 后重试
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    throw new Error('AI 走棋超时')
  }
  
  /**
   * 获取 AI 走棋（带轮询）
   */
  async getAIMoveWithPoll(fen: string, difficulty: number, timeLimit: number = 2000): Promise<AIMove> {
    const taskId = await this.getAIMove(fen, difficulty, timeLimit)
    return await this.pollAIMoveResult(taskId)
  }
  
  /**
   * 获取 AI 提示
   */
  async getAIHint(fen: string, difficulty: number, count: number = 3): Promise<AIHint[]> {
    const response = await aiApi.post('/hint/', {
      fen,
      difficulty,
      count
    })
    
    const taskId = response.data.data.task_id
    return await this.pollHintResult(taskId)
  }
  
  /**
   * 轮询提示结果
   */
  async pollHintResult(taskId: string, maxAttempts: number = 30): Promise<AIHint[]> {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await aiApi.get(`/hint/${taskId}/`)
      const result: AITaskResult = response.data.data
      
      if (result.status === 'completed' && result.result) {
        return result.result as AIHint[]
      } else if (result.status === 'failed') {
        throw new Error(result.error || '获取提示失败')
      }
      
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    throw new Error('获取提示超时')
  }
  
  /**
   * 获取难度列表
   */
  async getDifficulties() {
    const response = await aiApi.get('/difficulties/')
    return response.data.data.difficulties
  }
}

export const aiService = new AIService()
```

---

#### 5.2.2 AI 对战页面（Day 10-11）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-FE-04** | 创建难度选择组件 | 3h | - |
| **AI-FE-05** | 创建 AI 思考动画组件 | 3h | - |
| **AI-FE-06** | 集成 AI 走棋到游戏页面 | 4h | AI-FE-01 |
| **AI-FE-07** | 实现提示功能 UI | 3h | AI-FE-01 |

---

### 5.3 测试实现

#### 5.3.1 后端测试（Day 12）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-TEST-01** | 编写 Stockfish 服务测试 | 3h | AI-BE-03 |
| **AI-TEST-02** | 编写引擎池测试 | 2h | AI-BE-07 |
| **AI-TEST-03** | 编写 Celery 任务测试 | 2h | AI-BE-11 |
| **AI-TEST-04** | 编写 API 接口测试 | 2h | AI-BE-16 |

---

#### 5.3.2 前端测试（Day 12-13）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **AI-TEST-05** | 编写 AI 服务测试 | 2h | AI-FE-01 |
| **AI-TEST-06** | 编写难度选择组件测试 | 2h | AI-FE-04 |

---

### 5.4 任务时间线

```
Week 1: 后端核心
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│AI-01 │AI-03 │AI-05 │AI-07 │AI-09 │AI-11 │ 休息 │
│AI-02 │AI-04 │AI-06 │AI-08 │AI-10 │AI-12 │      │
│      │      │      │      │      │      │      │
│      │      │      │      │      │AI-13 │      │
│      │      │      │      │      │AI-14 │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 2: 后端 API+ 前端
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│AI-16 │AI-FE1│AI-FE3│AI-FE5│AI-FE7│TEST-1│ 休息 │
│AI-20 │AI-FE2│AI-FE4│AI-FE6│      │TEST-4│      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 3: 测试与联调
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│TEST-5│ 联调 │ 联调 │ 修复 │ 验收 │ 休息 │ 休息 │
│      │      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

**总工时预估**：约 80 小时（2 周）

---

## 6. 测试计划

### 6.1 单元测试

| 测试模块 | 测试用例 | 预期结果 |
|---------|---------|---------|
| **StockfishService** | 初始化引擎 | 成功加载 Stockfish |
| **StockfishService** | 获取初始局面走棋 | 返回有效走棋 |
| **StockfishService** | 不同难度走棋质量 | 高难度走棋更强 |
| **StockfishService** | 思考时间控制 | 在规定时间内返回 |
| **StockfishService** | 局面评估 | 返回合理分数 |
| **EnginePool** | 获取引擎 | 返回可用引擎 |
| **EnginePool** | 引擎释放 | 引擎回到池中 |
| **EnginePool** | 并发获取 | 多个请求正常处理 |
| **AI Tasks** | 走棋任务执行 | 返回正确走棋 |
| **AI Tasks** | 任务超时处理 | 超时后正确失败 |
| **AI Tasks** | 提示任务 | 返回多个候选走法 |

**测试代码示例**：
```python
# apps/ai/tests/test_stockfish.py
import pytest
from apps.ai.services.stockfish_service import StockfishService

class TestStockfishService:
    def test_get_best_move_initial(self):
        service = StockfishService(difficulty=5)
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        move = service.get_best_move(fen)
        
        assert move.from_pos is not None
        assert move.to_pos is not None
        assert move.thinking_time < 2000
    
    def test_difficulty_levels(self):
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 低难度
        low_service = StockfishService(difficulty=1)
        low_move = low_service.get_best_move(fen)
        
        # 高难度
        high_service = StockfishService(difficulty=10)
        high_move = high_service.get_best_move(fen)
        
        # 高难度思考更深
        assert high_move.depth >= low_move.depth
    
    def test_evaluation(self):
        service = StockfishService(difficulty=5)
        
        # 均势局面
        fen_equal = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        eval_equal = service.evaluate_position(fen_equal)
        
        assert -0.5 < eval_equal['score'] < 0.5
```

---

## 7. 验收标准

### 7.1 功能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **AC-01** | 可以选择 10 级难度 | 调用难度列表 API | 返回 10 个难度等级 |
| **AC-02** | AI 走棋符合规则 | 验证 AI 走棋 | 所有走棋合法 |
| **AC-03** | 难度 1-3 有意放水 | 对局测试 | AI 会犯明显错误 |
| **AC-04** | 难度 8-10 棋力强劲 | 对局测试 | 普通玩家难以战胜 |
| **AC-05** | 思考时间符合配置 | 计时测试 | 各难度时间符合设定 |
| **AC-06** | 走棋提示功能正常 | 调用提示 API | 返回 3 个候选走法 |
| **AC-07** | 局面评估准确 | 对比人工评估 | 评估结果合理 |
| **AC-08** | 支持执红/执黑选择 | 创建对局测试 | AI 正确应对先后手 |
| **AC-09** | 引擎池正常工作 | 并发测试 | 多局游戏同时运行 |
| **AC-10** | 任务超时正确处理 | 模拟超时 | 返回错误，不卡死 |

---

### 7.2 性能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **PERF-01** | 难度 1-5 响应时间 | 压测 | P95 < 1.5 秒 |
| **PERF-02** | 难度 6-10 响应时间 | 压测 | P95 < 5 秒 |
| **PERF-03** | 提示功能响应时间 | 压测 | P95 < 3 秒 |
| **PERF-04** | 并发 AI 对局能力 | 压测 | 支持 20+ 同时对局 |
| **PERF-05** | 引擎池利用率 | 监控 | > 80% |

---

## 8. 风险与应对

| 风险 ID | 风险描述 | 可能性 | 影响 | 应对措施 |
|--------|---------|--------|------|---------|
| **AI-RISK-01** | Stockfish 安装失败 | 中 | 高 | 提供 Docker 镜像，预装引擎 |
| **AI-RISK-02** | 引擎响应慢 | 中 | 中 | 设置超时，异步执行 |
| **AI-RISK-03** | 引擎崩溃 | 低 | 高 | 引擎池健康检查，自动重启 |
| **AI-RISK-04** | 高难度 AI 太强 | 低 | 中 | 调整 Skill Level 和 UCI_Elo |
| **AI-RISK-05** | 低难度 AI 太弱 | 中 | 中 | 增加随机性，模拟人类错误 |
| **AI-RISK-06** | 资源占用高 | 中 | 中 | 限制引擎线程数和哈希大小 |

---

## 9. 后续扩展（P1/P2）

### 9.1 P1 功能

- **AI 棋局分析**：对局结束后 AI 分析关键走法
- **残局挑战**：预设残局，AI 作为防守方
- **走棋解释**：AI 解释为什么走这步棋
- **棋力评估**：根据对局评估玩家棋力

### 9.2 P2 功能

- **AI 语音解说**：实时语音解说对局
- **自定义 AI 风格**：激进/保守等风格选择
- **历史名手模拟**：模拟历史名手走棋风格
- **AI 让子功能**：AI 让先、让子

---

## 附录

### A. Stockfish 安装指南

**macOS**：
```bash
brew install stockfish
# 路径：/opt/homebrew/bin/stockfish
```

**Linux (Ubuntu)**：
```bash
sudo apt-get install stockfish
# 路径：/usr/games/stockfish
```

**Windows**：
```bash
# 从 https://stockfishchess.org/download/ 下载
# 或使用 choco
choco install stockfish
```

**Docker**：
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y stockfish

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
```

---

### B. 环境变量配置

```bash
# .env
# Stockfish 路径
STOCKFISH_PATH=/usr/games/stockfish

# AI 配置
AI_ENGINE_POOL_SIZE=4
AI_DEFAULT_DIFFICULTY=5
AI_MAX_THINK_TIME=10000

# Celery 配置
CELERY_AI_QUEUE_CONCURRENCY=4
CELERY_AI_TASK_TIME_LIMIT=30
```

---

### C. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | planner agent | 初始版本，完成 AI 对弈系统规划 |

---

**AI 对弈系统规划完成！** ✅

下一步：规划匹配系统（matchmaking-plan.md）
