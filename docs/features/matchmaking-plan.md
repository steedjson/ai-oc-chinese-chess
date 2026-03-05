# 🎯 匹配系统 - 功能规划文档

**文档版本**：v1.0  
**创建时间**：2026-03-03  
**优先级**：P0  
**状态**：待实现

---

## 1. 功能概述

### 1.1 功能描述

匹配系统是联网对战的核心功能，负责根据玩家天梯分（Elo 等级分）自动匹配实力相当的对手。该系统需要实现匹配队列管理、Elo 匹配算法、动态搜索范围调整和超时处理机制，确保玩家能够快速找到合适的对手进行公平对战。

### 1.2 功能范围

**包含**：
- Elo 等级分系统
- 匹配队列管理（Redis Sorted Set）
- 匹配算法（基于分差搜索）
- 动态搜索范围调整
- 匹配超时处理
- 匹配取消功能
- 匹配成功通知（WebSocket）

**不包含**（P1/P2）：
- 分段匹配（按段位）（P1）
- 组队匹配（P1）
- 匹配偏好设置（P1）
- 匹配质量评估（P2）

### 1.3 技术选型

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| **队列存储** | Redis Sorted Set | 按分数排序，高效范围查询 |
| **匹配算法** | 自定义 Elo 匹配 | 灵活控制匹配逻辑 |
| **实时通知** | WebSocket (Channels) | 即时推送匹配结果 |
| **超时处理** | Celery Beat | 定时检查超时请求 |
| **分布式锁** | Redis Lock | 防止重复匹配 |

---

## 2. 用户故事

### 2.1 核心用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|--------|
| **US-MM-01** | 作为玩家，我希望点击快速匹配后快速找到对手，以便开始对战 | 匹配等待时间<3 分钟，对手天梯分差距<200 | P0 |
| **US-MM-02** | 作为玩家，我希望匹配到实力相当的对手，以便公平对战 | 初始搜索范围±100 分，动态扩大 | P0 |
| **US-MM-03** | 作为玩家，我希望在匹配等待时看到当前队列状态，以便了解等待时间 | 显示当前队列人数和预估等待时间 | P0 |
| **US-MM-04** | 作为玩家，我希望在匹配时间过长时取消匹配，以便选择其他模式 | 随时可以取消匹配，立即生效 | P0 |
| **US-MM-05** | 作为玩家，我希望匹配成功后自动创建房间，以便快速开始游戏 | 匹配成功后自动跳转游戏页面 | P0 |
| **US-MM-06** | 作为玩家，我希望匹配超时后收到提示，以便选择其他操作 | 超时后提示并推荐 AI 对战 | P0 |

### 2.2 用户旅程地图

```
快速匹配流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 点击匹配 │ →  │ 加入队列 │ →  │ 等待匹配 │ →  │ 匹配成功 │ →  │ 创建房间 │ →  │ 开始对局 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                    │                              │
                                    ▼                              ▼
                              显示队列状态                     WebSocket 通知
                              动态搜索对手                     自动加入房间
                              
匹配超时流程：
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 等待匹配 │ →  │ 超时检测 │ →  │ 发送通知 │ →  │ 推荐 AI  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

## 3. API 设计

### 3.1 API 总览

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/matchmaking/quick/ | 快速匹配 | 是 |
| POST | /api/matchmaking/cancel/ | 取消匹配 | 是 |
| GET | /api/matchmaking/status/ | 匹配状态 | 是 |
| GET | /api/matchmaking/queue-info/ | 队列信息 | 是 |

### 3.2 WebSocket 消息

| 消息类型 | 方向 | 描述 |
|---------|------|------|
| `matchmaking_join` | C→S | 加入匹配队列 |
| `matchmaking_cancel` | C→S | 取消匹配 |
| `match_found` | S→C | 匹配成功通知 |
| `matchmaking_timeout` | S→C | 匹配超时通知 |
| `queue_update` | S→C | 队列状态更新 |

---

### 3.3 API 详细设计

#### 3.3.1 快速匹配

**请求**：
```http
POST /api/matchmaking/quick/
Authorization: Bearer {token}
Content-Type: application/json

{
  "game_type": "online",
  "time_control": {
    "base_time": 600,
    "increment": 10
  }
}
```

**成功响应**（202 Accepted）：
```json
{
  "success": true,
  "data": {
    "queue_id": "queue_12345",
    "status": "searching",
    "user_rating": 1200,
    "search_range": 100,
    "queue_position": 5,
    "estimated_wait": 30,
    "joined_at": "2026-03-03T09:00:00Z"
  },
  "message": "已加入匹配队列，正在搜索对手..."
}
```

**错误响应**（400 Bad Request）：
```json
{
  "success": false,
  "error": {
    "code": "ALREADY_IN_QUEUE",
    "message": "你已在匹配队列中"
  }
}
```

---

#### 3.3.2 取消匹配

**请求**：
```http
POST /api/matchmaking/cancel/
Authorization: Bearer {token}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "message": "已取消匹配"
}
```

**错误响应**（400 Bad Request）：
```json
{
  "success": false,
  "error": {
    "code": "NOT_IN_QUEUE",
    "message": "你不在匹配队列中"
  }
}
```

---

#### 3.3.3 匹配状态

**请求**：
```http
GET /api/matchmaking/status/
Authorization: Bearer {token}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "in_queue": true,
    "queue_id": "queue_12345",
    "status": "searching",
    "user_rating": 1200,
    "search_range": 150,
    "queue_position": 3,
    "wait_time": 45,
    "joined_at": "2026-03-03T09:00:00Z",
    "expires_at": "2026-03-03T09:03:00Z"
  }
}
```

**不在队列时**：
```json
{
  "success": true,
  "data": {
    "in_queue": false
  }
}
```

---

#### 3.3.4 队列信息

**请求**：
```http
GET /api/matchmaking/queue-info/
Authorization: Bearer {token}
```

**成功响应**（200 OK）：
```json
{
  "success": true,
  "data": {
    "total_players": 25,
    "rating_ranges": [
      {"range": "0-800", "players": 3},
      {"range": "800-1000", "players": 5},
      {"range": "1000-1200", "players": 8},
      {"range": "1200-1400", "players": 6},
      {"range": "1400-1600", "players": 2},
      {"range": "1600+", "players": 1}
    ],
    "avg_wait_time": 45,
    "your_rating": 1200,
    "your_range_players": 8
  }
}
```

---

### 3.4 WebSocket 详细设计

#### 3.4.1 加入匹配队列

**请求**：
```json
{
  "type": "matchmaking_join",
  "data": {
    "game_type": "online",
    "time_control": {
      "base_time": 600,
      "increment": 10
    }
  }
}
```

**响应**：
```json
{
  "type": "matchmaking_joined",
  "data": {
    "queue_id": "queue_12345",
    "status": "searching",
    "user_rating": 1200,
    "search_range": 100
  }
}
```

---

#### 3.4.2 匹配成功通知

**响应**（推送）：
```json
{
  "type": "match_found",
  "data": {
    "game_id": "550e8400-e29b-41d4-a716-446655440000",
    "room_id": "room_abc123",
    "opponent": {
      "user_id": 67890,
      "username": "opponent123",
      "rating": 1185
    },
    "your_side": "red",
    "room_url": "/game/550e8400-e29b-41d4-a716-446655440000/",
    "ws_url": "ws://api.example.com/ws/game/550e8400-e29b-41d4-a716-446655440000/"
  }
}
```

---

#### 3.4.3 匹配超时通知

**响应**（推送）：
```json
{
  "type": "matchmaking_timeout",
  "data": {
    "message": "匹配超时，未找到合适对手",
    "wait_time": 180,
    "suggestions": [
      {"type": "ai", "text": "试试 AI 对战"},
      {"type": "friend", "text": "邀请好友对战"}
    ]
  }
}
```

---

## 4. 数据库设计

### 4.1 匹配队列表（Redis）

使用 Redis Sorted Set 实现匹配队列，按天梯分排序。

```
# Key 格式
MATCH_QUEUE:{game_type}  # 例如：MATCH_QUEUE:online

# 数据结构：Sorted Set
# Member: user_id
# Score: rating (天梯分)

# 示例
ZADD MATCH_QUEUE:online 1200 12345  # 用户 12345，天梯分 1200
ZADD MATCH_QUEUE:online 1180 67890  # 用户 67890，天梯分 1180

# 查询指定分数范围的对手
ZRANGEBYSCORE MATCH_QUEUE:online 1100 1300  # 查询 1100-1300 分的玩家
```

**用户元数据（Hash）**：
```
# Key 格式
MATCH_USER:{user_id}

# 数据结构：Hash
HSET MATCH_USER:12345 rating 1200 joined_at 1709424000 search_range 100 game_type online
```

---

### 4.2 匹配记录表（matchmaking_records）

记录匹配历史，用于分析和优化。

```sql
CREATE TABLE matchmaking_records (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    
    -- 用户信息
    user_id         BIGINT REFERENCES users(id) NOT NULL,
    user_rating     INTEGER NOT NULL,
    
    -- 对手信息
    opponent_id     BIGINT REFERENCES users(id),
    opponent_rating INTEGER,
    
    -- 匹配信息
    game_type       VARCHAR(20) NOT NULL,
    search_range_initial INTEGER NOT NULL,     -- 初始搜索范围
    search_range_final   INTEGER,              -- 最终搜索范围
    rating_diff     INTEGER,                        -- 分差
    
    -- 时间信息
    queue_time      INTEGER NOT NULL,           -- 排队时长（秒）
    timeout         BOOLEAN DEFAULT FALSE,      -- 是否超时
    
    -- 结果信息
    game_id         UUID,
    match_success   BOOLEAN NOT NULL,
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 索引
CREATE INDEX idx_match_records_user ON matchmaking_records(user_id, created_at DESC);
CREATE INDEX idx_match_records_success ON matchmaking_records(match_success);
CREATE INDEX idx_match_records_queue_time ON matchmaking_records(queue_time);
```

---

### 4.3 匹配配置表（matchmaking_configs）

配置匹配算法参数。

```sql
CREATE TABLE matchmaking_configs (
    -- 主键
    id              SERIAL PRIMARY KEY,
    
    -- 配置信息
    config_key      VARCHAR(100) UNIQUE NOT NULL,
    config_value    JSONB NOT NULL,
    description     TEXT,
    
    -- 启用状态
    is_active       BOOLEAN DEFAULT TRUE,
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 初始配置
INSERT INTO matchmaking_configs (config_key, config_value, description) VALUES
('search_range', '{"initial": 100, "expansion": 50, "max": 300}', '搜索范围配置（初始/扩展/最大）'),
('timeout', '{"warning": 120, "max": 180}', '超时配置（警告/最大，秒）'),
('expansion_interval', '{"seconds": 30}', '扩大搜索范围间隔（秒）');

-- 索引
CREATE INDEX idx_match_configs_key ON matchmaking_configs(config_key);
```

---

## 5. 实现步骤（任务分解）

### 5.1 后端实现

#### 5.1.1 数据模型层（Day 1）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-BE-01** | 创建 MatchmakingRecord 模型 | 2h | - |
| **MM-BE-02** | 创建 MatchmakingConfig 模型 | 1h | MM-BE-01 |
| **MM-BE-03** | 编写数据库迁移并执行 | 1h | MM-BE-01~02 |

---

#### 5.1.2 Redis 队列管理（Day 2-3）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-BE-04** | 创建 MatchmakingQueue 类 | 4h | - |
| **MM-BE-05** | 实现加入队列 | 2h | MM-BE-04 |
| **MM-BE-06** | 实现离开队列 | 2h | MM-BE-04 |
| **MM-BE-07** | 实现搜索对手 | 4h | MM-BE-04 |
| **MM-BE-08** | 实现队列状态查询 | 2h | MM-BE-04 |

**代码结构**：
```python
# apps/matchmaking/services/queue.py
import redis
import json
from typing import Optional, List, Dict
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone
import time

@dataclass
class QueueUser:
    user_id: int
    rating: int
    joined_at: float
    search_range: int
    game_type: str

class MatchmakingQueue:
    """匹配队列管理"""
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.queue_prefix = "MATCH_QUEUE"
        self.user_prefix = "MATCH_USER"
        self.lock_prefix = "MATCH_LOCK"
    
    def join_queue(self, user_id: int, rating: int, game_type: str = "online") -> bool:
        """
        加入匹配队列
        
        Args:
            user_id: 用户 ID
            rating: 天梯分
            game_type: 游戏类型
        
        Returns:
            bool: 是否成功加入
        """
        # 检查是否已在队列中
        if self.is_in_queue(user_id, game_type):
            return False
        
        # 使用分布式锁防止并发
        lock_key = f"{self.lock_prefix}:{user_id}:{game_type}"
        if not self.redis.set(lock_key, "1", nx=True, ex=10):
            return False
        
        try:
            queue_key = f"{self.queue_prefix}:{game_type}"
            user_key = f"{self.user_prefix}:{user_id}"
            
            # 添加到 Sorted Set（分数=天梯分）
            self.redis.zadd(queue_key, {user_id: rating})
            
            # 存储用户元数据
            user_data = {
                'user_id': user_id,
                'rating': rating,
                'joined_at': time.time(),
                'search_range': 100,  # 初始搜索范围
                'game_type': game_type
            }
            self.redis.hset(user_key, mapping=user_data)
            self.redis.expire(user_key, 300)  # 5 分钟过期
            
            return True
        finally:
            self.redis.delete(lock_key)
    
    def leave_queue(self, user_id: int, game_type: str = "online") -> bool:
        """离开匹配队列"""
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 从队列移除
        removed = self.redis.zrem(queue_key, user_id)
        
        # 删除用户数据
        self.redis.delete(user_key)
        
        return removed > 0
    
    def is_in_queue(self, user_id: int, game_type: str = "online") -> bool:
        """检查用户是否在队列中"""
        queue_key = f"{self.queue_prefix}:{game_type}"
        return self.redis.zrank(queue_key, user_id) is not None
    
    def search_opponent(self, user_id: int, game_type: str = "online") -> Optional[int]:
        """
        搜索对手
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        
        Returns:
            Optional[int]: 对手用户 ID，未找到返回 None
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 获取用户信息
        user_data = self.redis.hgetall(user_key)
        if not user_data:
            return None
        
        rating = int(user_data[b'rating'])
        search_range = int(user_data[b'search_range'])
        
        # 搜索范围内的对手（排除自己）
        min_rating = rating - search_range
        max_rating = rating + search_range
        
        opponents = self.redis.zrangebyscore(
            queue_key, min_rating, max_rating,
            start=0, num=10  # 最多返回 10 个候选
        )
        
        # 过滤自己
        opponents = [int(op) for op in opponents if int(op) != user_id]
        
        if opponents:
            # 选择最接近的对手
            return opponents[0]
        
        return None
    
    def expand_search_range(self, user_id: int, game_type: str = "online", expansion: int = 50, max_range: int = 300) -> int:
        """
        扩大搜索范围
        
        Args:
            user_id: 用户 ID
            expansion: 扩展值
            max_range: 最大范围
        
        Returns:
            int: 新的搜索范围
        """
        user_key = f"{self.user_prefix}:{user_id}"
        
        current_range = int(self.redis.hget(user_key, 'search_range') or 100)
        new_range = min(current_range + expansion, max_range)
        
        self.redis.hset(user_key, 'search_range', new_range)
        
        return new_range
    
    def get_queue_position(self, user_id: int, game_type: str = "online") -> Dict:
        """
        获取队列位置信息
        
        Returns:
            Dict: 队列信息
        """
        queue_key = f"{self.queue_prefix}:{game_type}"
        user_key = f"{self.user_prefix}:{user_id}"
        
        # 用户排名
        rank = self.redis.zrank(queue_key, user_id)
        
        # 队列总人数
        total = self.redis.zcard(queue_key)
        
        # 用户信息
        user_data = self.redis.hgetall(user_key)
        
        return {
            'position': rank + 1 if rank is not None else 0,
            'total': total,
            'search_range': int(user_data.get(b'search_range', 100)),
            'wait_time': time.time() - float(user_data.get(b'joined_at', time.time()))
        }
    
    def get_queue_stats(self, game_type: str = "online") -> Dict:
        """获取队列统计信息"""
        queue_key = f"{self.queue_prefix}:{game_type}"
        
        # 所有玩家及分数
        all_players = self.redis.zrange(queue_key, 0, -1, withscores=True)
        
        # 按分数段统计
        ranges = [
            (0, 800, "0-800"),
            (800, 1000, "800-1000"),
            (1000, 1200, "1000-1200"),
            (1200, 1400, "1200-1400"),
            (1400, 1600, "1400-1600"),
            (1600, 99999, "1600+")
        ]
        
        stats = []
        for min_r, max_r, label in ranges:
            count = self.redis.zcount(queue_key, min_r, max_r)
            stats.append({'range': label, 'players': count})
        
        return {
            'total_players': len(all_players),
            'rating_ranges': stats,
            'avg_wait_time': self._calculate_avg_wait_time(game_type)
        }
    
    def _calculate_avg_wait_time(self, game_type: str) -> int:
        """计算平均等待时间"""
        # 从历史记录中计算
        pass
```

---

#### 5.1.3 匹配算法（Day 4-5）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-BE-09** | 实现基础匹配算法 | 4h | MM-BE-07 |
| **MM-BE-10** | 实现动态范围调整 | 3h | MM-BE-09 |
| **MM-BE-11** | 实现匹配超时检测 | 3h | MM-BE-09 |
| **MM-BE-12** | 实现匹配确认机制 | 3h | MM-BE-09 |

**代码结构**：
```python
# apps/matchmaking/services/matcher.py
from typing import Optional, Tuple
from django.utils import timezone
from datetime import timedelta
import asyncio

class Matchmaker:
    """匹配器"""
    
    def __init__(self):
        self.queue = MatchmakingQueue()
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载匹配配置"""
        return {
            'initial_range': 100,
            'expansion': 50,
            'max_range': 300,
            'expansion_interval': 30,  # 秒
            'timeout': 180,  # 秒
            'warning_timeout': 120  # 秒
        }
    
    async def matchmaking_loop(self, user_id: int, game_type: str = "online"):
        """
        匹配循环（异步）
        
        Args:
            user_id: 用户 ID
            game_type: 游戏类型
        """
        start_time = timezone.now()
        timeout = timedelta(seconds=self.config['timeout'])
        
        while True:
            # 检查是否超时
            elapsed = timezone.now() - start_time
            if elapsed > timeout:
                await self._handle_timeout(user_id, game_type)
                return
            
            # 检查用户是否还在队列
            if not self.queue.is_in_queue(user_id, game_type):
                return
            
            # 搜索对手
            opponent_id = self.queue.search_opponent(user_id, game_type)
            
            if opponent_id:
                # 尝试匹配
                success = await self._try_match(user_id, opponent_id, game_type)
                if success:
                    return
            
            # 扩大搜索范围
            current_range = self.queue.expand_search_range(
                user_id, game_type,
                expansion=self.config['expansion'],
                max_range=self.config['max_range']
            )
            
            # 发送队列更新通知
            await self._send_queue_update(user_id, {
                'search_range': current_range,
                'wait_time': elapsed.total_seconds()
            })
            
            # 警告超时
            if elapsed.total_seconds() > self.config['warning_timeout']:
                await self._send_timeout_warning(user_id)
            
            # 等待下次搜索
            await asyncio.sleep(self.config['expansion_interval'])
    
    async def _try_match(self, user_id: int, opponent_id: int, game_type: str) -> bool:
        """
        尝试匹配两个玩家
        
        Args:
            user_id: 用户 ID
            opponent_id: 对手用户 ID
            game_type: 游戏类型
        
        Returns:
            bool: 是否匹配成功
        """
        # 使用分布式锁防止重复匹配
        lock_key = f"match_lock:{min(user_id, opponent_id)}:{max(user_id, opponent_id)}"
        
        if not self.queue.redis.set(lock_key, "1", nx=True, ex=30):
            return False  # 已被其他进程处理
        
        try:
            # 检查对手是否还在队列
            if not self.queue.is_in_queue(opponent_id, game_type):
                return False
            
            # 双方确认匹配
            user_confirmed = await self._request_match_confirmation(user_id, opponent_id)
            opponent_confirmed = await self._request_match_confirmation(opponent_id, user_id)
            
            if user_confirmed and opponent_confirmed:
                # 创建游戏
                game_id = await self._create_game(user_id, opponent_id, game_type)
                
                # 从队列移除
                self.queue.leave_queue(user_id, game_type)
                self.queue.leave_queue(opponent_id, game_type)
                
                # 发送匹配成功通知
                await self._send_match_success(user_id, opponent_id, game_id)
                await self._send_match_success(opponent_id, user_id, game_id)
                
                # 记录匹配
                await self._record_match(user_id, opponent_id, game_id)
                
                return True
            
            return False
        finally:
            self.queue.redis.delete(lock_key)
    
    async def _request_match_confirmation(self, user_id: int, opponent_id: int) -> bool:
        """请求匹配确认（WebSocket 推送）"""
        # 通过 WebSocket 发送确认请求
        # 前端自动确认（P0），后续可扩展为手动确认
        return True
    
    async def _create_game(self, user_id: int, opponent_id: int, game_type: str) -> str:
        """创建游戏对局"""
        from apps.games.services import GameService
        
        game_service = GameService()
        game = game_service.create_game(
            game_type=game_type,
            red_player_id=user_id,
            black_player_id=opponent_id,
            is_rated=True
        )
        
        return str(game.id)
    
    async def _handle_timeout(self, user_id: int, game_type: str):
        """处理超时"""
        # 从队列移除
        self.queue.leave_queue(user_id, game_type)
        
        # 发送超时通知
        await self._send_timeout_notification(user_id)
    
    async def _send_match_success(self, user_id: int, opponent_id: int, game_id: str):
        """发送匹配成功通知"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'match_found',
                'data': {
                    'game_id': game_id,
                    'opponent_id': opponent_id,
                }
            }
        )
    
    async def _send_queue_update(self, user_id: int, data: dict):
        """发送队列更新通知"""
        pass
    
    async def _send_timeout_warning(self, user_id: int):
        """发送超时警告"""
        pass
    
    async def _send_timeout_notification(self, user_id: int):
        """发送超时通知"""
        pass
    
    async def _record_match(self, user_id: int, opponent_id: int, game_id: str):
        """记录匹配历史"""
        pass
```

---

#### 5.1.4 API 视图层（Day 6-7）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-BE-13** | 创建 QuickMatchView | 2h | MM-BE-04 |
| **MM-BE-14** | 创建 CancelMatchView | 1h | MM-BE-04 |
| **MM-BE-15** | 创建 MatchStatusView | 2h | MM-BE-04 |
| **MM-BE-16** | 创建 QueueInfoView | 2h | MM-BE-04 |
| **MM-BE-17** | 实现匹配结果轮询接口 | 2h | MM-BE-12 |

**代码结构**：
```python
# apps/matchmaking/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from .services.queue import MatchmakingQueue
from .services.matcher import Matchmaker
import asyncio

class QuickMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """快速匹配"""
        user = request.user
        game_type = request.data.get('game_type', 'online')
        time_control = request.data.get('time_control', {})
        
        queue = MatchmakingQueue()
        
        # 检查是否已在队列
        if queue.is_in_queue(user.id, game_type):
            return Response({
                'success': False,
                'error': {'code': 'ALREADY_IN_QUEUE', 'message': '你已在匹配队列中'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 加入队列
        success = queue.join_queue(user.id, user.rating, game_type)
        
        if not success:
            return Response({
                'success': False,
                'error': {'code': 'QUEUE_ERROR', 'message': '加入队列失败'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 获取队列信息
        queue_info = queue.get_queue_position(user.id, game_type)
        
        # 异步启动匹配循环
        matchmaker = Matchmaker()
        asyncio.create_task(matchmaker.matchmaking_loop(user.id, game_type))
        
        return Response({
            'success': True,
            'data': {
                'queue_id': f'queue_{user.id}',
                'status': 'searching',
                'user_rating': user.rating,
                'search_range': queue_info['search_range'],
                'queue_position': queue_info['position'],
                'estimated_wait': 30
            },
            'message': '已加入匹配队列，正在搜索对手...'
        }, status=status.HTTP_202_ACCEPTED)

class CancelMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """取消匹配"""
        user = request.user
        game_type = request.data.get('game_type', 'online')
        
        queue = MatchmakingQueue()
        
        if not queue.is_in_queue(user.id, game_type):
            return Response({
                'success': False,
                'error': {'code': 'NOT_IN_QUEUE', 'message': '你不在匹配队列中'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queue.leave_queue(user.id, game_type)
        
        return Response({
            'success': True,
            'message': '已取消匹配'
        })

class MatchStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """匹配状态"""
        user = request.user
        game_type = request.data.get('game_type', 'online')
        
        queue = MatchmakingQueue()
        
        if not queue.is_in_queue(user.id, game_type):
            return Response({
                'success': True,
                'data': {'in_queue': False}
            })
        
        queue_info = queue.get_queue_position(user.id, game_type)
        
        return Response({
            'success': True,
            'data': {
                'in_queue': True,
                'queue_id': f'queue_{user.id}',
                'status': 'searching',
                'user_rating': user.rating,
                'search_range': queue_info['search_range'],
                'queue_position': queue_info['position'],
                'wait_time': int(queue_info['wait_time']),
            }
        })

class QueueInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """队列信息"""
        game_type = request.query_params.get('game_type', 'online')
        
        queue = MatchmakingQueue()
        stats = queue.get_queue_stats(game_type)
        
        user = request.user
        user_data = queue.queue.redis.hgetall(f"MATCH_USER:{user.id}")
        
        stats['your_rating'] = user.rating
        stats['your_range_players'] = stats['rating_ranges'][3]['players']  # 1200-1400 分段
        
        return Response({
            'success': True,
            'data': stats
        })
```

---

#### 5.1.5 WebSocket Consumer（Day 8-9）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-BE-18** | 创建 MatchmakingConsumer | 4h | MM-BE-04 |
| **MM-BE-19** | 实现加入/取消匹配 | 2h | MM-BE-18 |
| **MM-BE-20** | 实现匹配成功推送 | 2h | MM-BE-18 |
| **MM-BE-21** | 实现队列状态推送 | 2h | MM-BE-18 |

**代码结构**：
```python
# apps/matchmaking/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .services.queue import MatchmakingQueue
from .services.matcher import Matchmaker
import asyncio

class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """建立连接"""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # 加入用户频道
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """断开连接"""
        # 注意：断开连接不自动取消匹配
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """接收消息"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'matchmaking_join':
            await self._handle_join(data)
        elif message_type == 'matchmaking_cancel':
            await self._handle_cancel(data)
    
    async def _handle_join(self, data):
        """处理加入匹配"""
        game_type = data.get('data', {}).get('game_type', 'online')
        
        queue = MatchmakingQueue()
        
        if queue.is_in_queue(self.user.id, game_type):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'data': {'code': 'ALREADY_IN_QUEUE', 'message': '已在队列中'}
            }))
            return
        
        success = queue.join_queue(self.user.id, self.user.rating, game_type)
        
        if success:
            # 启动匹配循环
            matchmaker = Matchmaker()
            asyncio.create_task(matchmaker.matchmaking_loop(self.user.id, game_type))
            
            await self.send(text_data=json.dumps({
                'type': 'matchmaking_joined',
                'data': {
                    'queue_id': f'queue_{self.user.id}',
                    'status': 'searching',
                    'user_rating': self.user.rating,
                    'search_range': 100
                }
            }))
    
    async def _handle_cancel(self, data):
        """处理取消匹配"""
        game_type = data.get('data', {}).get('game_type', 'online')
        
        queue = MatchmakingQueue()
        queue.leave_queue(self.user.id, game_type)
        
        await self.send(text_data=json.dumps({
            'type': 'matchmaking_cancelled',
            'data': {'message': '已取消匹配'}
        }))
    
    async def match_found(self, event):
        """接收匹配成功通知"""
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'data': event['data']
        }))
    
    async def queue_update(self, event):
        """接收队列更新通知"""
        await self.send(text_data=json.dumps({
            'type': 'queue_update',
            'data': event['data']
        }))
    
    async def matchmaking_timeout(self, event):
        """接收超时通知"""
        await self.send(text_data=json.dumps({
            'type': 'matchmaking_timeout',
            'data': event['data']
        }))
```

---

### 5.2 前端实现

#### 5.2.1 匹配服务层（Day 10）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-FE-01** | 创建匹配 API 服务 | 3h | - |
| **MM-FE-02** | 创建 WebSocket 管理器 | 3h | MM-FE-01 |
| **MM-FE-03** | 实现匹配状态管理 | 2h | MM-FE-01 |

**代码结构**：
```typescript
// src/services/matchmakingService.ts
import axios from 'axios'

const matchApi = axios.create({
  baseURL: '/api/matchmaking',
})

export interface MatchStatus {
  in_queue: boolean
  queue_id?: string
  status?: 'searching' | 'matched' | 'timeout'
  user_rating?: number
  search_range?: number
  queue_position?: number
  wait_time?: number
}

export interface MatchResult {
  game_id: string
  room_id: string
  opponent: {
    user_id: number
    username: string
    rating: number
  }
  your_side: 'red' | 'black'
  room_url: string
  ws_url: string
}

class MatchmakingService {
  private ws: WebSocket | null = null
  private statusListeners: ((status: MatchStatus) => void)[] = []
  private matchFoundListeners: ((result: MatchResult) => void)[] = []
  
  /**
   * 快速匹配
   */
  async quickMatch(gameType: string = 'online', timeControl?: { base_time: number; increment: number }) {
    const response = await matchApi.post('/quick/', {
      game_type: gameType,
      time_control: timeControl
    })
    
    return response.data.data
  }
  
  /**
   * 取消匹配
   */
  async cancelMatch(gameType: string = 'online') {
    const response = await matchApi.post('/cancel/', {
      game_type: gameType
    })
    
    return response.data
  }
  
  /**
   * 获取匹配状态
   */
  async getStatus(): Promise<MatchStatus> {
    const response = await matchApi.get('/status/')
    return response.data.data
  }
  
  /**
   * 获取队列信息
   */
  async getQueueInfo() {
    const response = await matchApi.get('/queue-info/')
    return response.data.data
  }
  
  /**
   * 连接 WebSocket
   */
  connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws/matchmaking/`
    this.ws = new WebSocket(wsUrl)
    
    this.ws.onopen = () => {
      console.log('Matchmaking WebSocket connected')
    }
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'match_found':
          this.matchFoundListeners.forEach(cb => cb(data.data))
          break
        case 'queue_update':
          this.statusListeners.forEach(cb => cb(data.data))
          break
        case 'matchmaking_timeout':
          // 处理超时
          break
      }
    }
    
    this.ws.onclose = () => {
      console.log('Matchmaking WebSocket disconnected')
      // 重连逻辑
      setTimeout(() => this.connectWebSocket(), 5000)
    }
  }
  
  /**
   * 订阅状态更新
   */
  onStatusUpdate(callback: (status: MatchStatus) => void) {
    this.statusListeners.push(callback)
  }
  
  /**
   * 订阅匹配成功
   */
  onMatchFound(callback: (result: MatchResult) => void) {
    this.matchFoundListeners.push(callback)
  }
  
  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

export const matchmakingService = new MatchmakingService()
```

---

#### 5.2.2 匹配页面（Day 11-12）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-FE-04** | 创建匹配大厅页面 | 4h | - |
| **MM-FE-05** | 创建队列状态组件 | 3h | MM-FE-01 |
| **MM-FE-06** | 创建匹配成功弹窗 | 3h | MM-FE-01 |
| **MM-FE-07** | 实现倒计时显示 | 2h | MM-FE-05 |

---

### 5.3 测试实现

#### 5.3.1 后端测试（Day 13）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-TEST-01** | 编写队列管理测试 | 3h | MM-BE-04 |
| **MM-TEST-02** | 编写匹配算法测试 | 3h | MM-BE-09 |
| **MM-TEST-03** | 编写 API 接口测试 | 2h | MM-BE-13 |
| **MM-TEST-04** | 编写 WebSocket 测试 | 2h | MM-BE-18 |

---

#### 5.3.2 前端测试（Day 13-14）

| 任务 ID | 任务描述 | 预计工时 | 依赖 |
|--------|---------|---------|------|
| **MM-TEST-05** | 编写匹配服务测试 | 2h | MM-FE-01 |
| **MM-TEST-06** | 编写匹配页面测试 | 2h | MM-FE-04 |

---

### 5.4 任务时间线

```
Week 1: 后端核心
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│MM-01 │MM-04 │MM-07 │MM-09 │MM-11 │MM-13 │ 休息 │
│MM-03 │MM-06 │MM-08 │MM-10 │MM-12 │MM-17 │      │
│      │      │      │      │      │      │      │
│      │      │      │      │      │MM-16 │      │
│      │      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 2: 后端 WebSocket+ 前端
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│MM-18 │MM-FE1│MM-FE3│MM-FE5│MM-FE7│TEST-1│ 休息 │
│MM-21 │MM-FE2│MM-FE4│MM-FE6│      │TEST-4│      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Week 3: 测试与联调
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │
├──────┼──────┼──────┼──────┼──────┼──────┼──────┤
│TEST-5│ 联调 │ 联调 │ 修复 │ 验收 │ 休息 │ 休息 │
│      │      │      │      │      │      │      │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘
```

**总工时预估**：约 90 小时（2 周）

---

## 6. 测试计划

### 6.1 单元测试

| 测试模块 | 测试用例 | 预期结果 |
|---------|---------|---------|
| **MatchmakingQueue** | 加入队列 | 成功加入，返回 true |
| **MatchmakingQueue** | 重复加入 | 返回 false |
| **MatchmakingQueue** | 离开队列 | 成功移除 |
| **MatchmakingQueue** | 搜索对手（范围内） | 返回对手 ID |
| **MatchmakingQueue** | 搜索对手（无） | 返回 None |
| **MatchmakingQueue** | 扩大搜索范围 | 范围正确扩大 |
| **Matchmaker** | 匹配成功 | 创建游戏，双方通知 |
| **Matchmaker** | 匹配超时 | 超时通知，移出队列 |
| **Matchmaker** | 动态范围调整 | 范围逐步扩大 |

**测试代码示例**：
```python
# apps/matchmaking/tests/test_queue.py
import pytest
from apps.matchmaking.services.queue import MatchmakingQueue

@pytest.mark.django_db
class TestMatchmakingQueue:
    def test_join_queue(self, user):
        queue = MatchmakingQueue()
        
        success = queue.join_queue(user.id, user.rating, 'online')
        
        assert success is True
        assert queue.is_in_queue(user.id, 'online') is True
    
    def test_duplicate_join(self, user):
        queue = MatchmakingQueue()
        
        queue.join_queue(user.id, user.rating, 'online')
        success = queue.join_queue(user.id, user.rating, 'online')
        
        assert success is False
    
    def test_leave_queue(self, user):
        queue = MatchmakingQueue()
        
        queue.join_queue(user.id, user.rating, 'online')
        success = queue.leave_queue(user.id, 'online')
        
        assert success is True
        assert queue.is_in_queue(user.id, 'online') is False
    
    def test_search_opponent(self, user, opponent_user):
        queue = MatchmakingQueue()
        
        # 两个用户分数接近
        queue.join_queue(user.id, 1200, 'online')
        queue.join_queue(opponent_user.id, 1180, 'online')
        
        found = queue.search_opponent(user.id, 'online')
        
        assert found == opponent_user.id
    
    def test_expand_search_range(self, user):
        queue = MatchmakingQueue()
        queue.join_queue(user.id, 1200, 'online')
        
        new_range = queue.expand_search_range(user.id, 'online', expansion=50, max_range=300)
        
        assert new_range == 150
```

---

## 7. 验收标准

### 7.1 功能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **AC-01** | 可以加入匹配队列 | 调用快速匹配 API | 返回 202，队列状态正确 |
| **AC-02** | 重复加入被拒绝 | 再次调用快速匹配 | 返回 400，提示已在队列 |
| **AC-03** | 可以取消匹配 | 调用取消 API | 返回 200，移出队列 |
| **AC-04** | 匹配到实力相当对手 | 模拟多用户匹配 | 对手分差<200 |
| **AC-05** | 动态扩大搜索范围 | 等待匹配 | 搜索范围逐步扩大 |
| **AC-06** | 匹配超时处理 | 等待 3 分钟 | 超时通知，移出队列 |
| **AC-07** | 匹配成功通知 | 模拟匹配成功 | WebSocket 推送正确 |
| **AC-08** | 自动创建游戏 | 匹配成功后 | 游戏记录创建 |
| **AC-09** | 队列状态查询 | 调用状态 API | 返回正确队列信息 |
| **AC-10** | 队列统计信息 | 调用队列信息 API | 返回各分段人数 |

---

### 7.2 性能验收

| ID | 验收项 | 验收方法 | 通过标准 |
|----|--------|---------|---------|
| **PERF-01** | 加入队列响应时间 | 压测 | P95 < 100ms |
| **PERF-02** | 搜索对手耗时 | 压测 | P95 < 50ms |
| **PERF-03** | 匹配通知延迟 | 压测 | P95 < 100ms |
| **PERF-04** | 并发匹配能力 | 压测 | 支持 100+ 并发匹配 |
| **PERF-05** | Redis 队列性能 | 监控 | 操作延迟<10ms |

---

## 8. 风险与应对

| 风险 ID | 风险描述 | 可能性 | 影响 | 应对措施 |
|--------|---------|--------|------|---------|
| **MM-RISK-01** | 匹配时间过长 | 中 | 高 | 动态扩大范围，超时推荐 AI |
| **MM-RISK-02** | 匹配质量差（分差大） | 中 | 中 | 设置最大分差限制 |
| **MM-RISK-03** | 重复匹配（并发） | 低 | 高 | 分布式锁防止 |
| **MM-RISK-04** | Redis 单点故障 | 低 | 高 | Redis Sentinel 高可用 |
| **MM-RISK-05** | WebSocket 断连 | 中 | 中 | 断连不影响匹配，API 轮询备用 |
| **MM-RISK-06** | 匹配作弊（小号） | 中 | 中 | 账号活跃度检测，限制新号 |

---

## 9. 后续扩展（P1/P2）

### 9.1 P1 功能

- **分段匹配**：按段位（青铜/白银/黄金）匹配
- **组队匹配**：2v2、3v3 组队对战
- **匹配偏好**：偏好先手/后手、时间控制
- **匹配质量评估**：匹配后评价对手质量

### 9.2 P2 功能

- **跨服匹配**：多服务器匹配
- **匹配保护**：连败后匹配保护机制
- **好友优先**：好友在线时优先匹配
- **匹配预测**：AI 预测匹配等待时间

---

## 附录

### A. Elo 等级分计算公式

```python
def calculate_elo_change(player_rating: int, opponent_rating: int, 
                         result: str, k_factor: int = 32) -> int:
    """
    计算 Elo 积分变化
    
    Args:
        player_rating: 玩家当前积分
        opponent_rating: 对手积分
        result: 'win', 'loss', 'draw'
        k_factor: K 因子（决定变化幅度）
    
    Returns:
        int: 积分变化（正数增加，负数减少）
    """
    # 计算期望得分
    expected = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
    
    # 实际得分
    actual = {'win': 1, 'draw': 0.5, 'loss': 0}[result]
    
    # 积分变化
    change = round(k_factor * (actual - expected))
    
    return change

# 示例
# 1200 分玩家战胜 1200 分对手
change = calculate_elo_change(1200, 1200, 'win')  # +16

# 1200 分玩家战胜 1400 分对手
change = calculate_elo_change(1200, 1400, 'win')  # +24

# 1200 分玩家输给 1000 分对手
change = calculate_elo_change(1200, 1000, 'loss')  # -24
```

---

### B. 环境变量配置

```bash
# .env
# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 匹配配置
MATCHMAKING_INITIAL_RANGE=100
MATCHMAKING_EXPANSION=50
MATCHMAKING_MAX_RANGE=300
MATCHMAKING_TIMEOUT=180
MATCHMAKING_EXPANSION_INTERVAL=30

# Elo 配置
ELO_K_FACTOR=32
ELO_INITIAL_RATING=1200
ELO_MIN_RATING=0
ELO_MAX_RATING=3000
```

---

### C. 文档历史

| 版本 | 日期 | 作者 | 变更描述 |
|------|------|------|---------|
| v1.0 | 2026-03-03 | planner agent | 初始版本，完成匹配系统规划 |

---

**匹配系统规划完成！** ✅

---

## 总结

四个 P0 优先级核心功能规划文档已全部完成：

1. ✅ **用户认证系统** (`user-auth-plan.md`) - 33KB
2. ✅ **游戏对局系统** (`game-core-plan.md`) - 38KB
3. ✅ **AI 对弈系统** (`ai-opponent-plan.md`) - 37KB
4. ✅ **匹配系统** (`matchmaking-plan.md`) - 35KB

所有文档均包含：
- 功能概述
- 用户故事
- API 设计
- 数据库设计
- 实现步骤（任务分解）
- 测试计划
- 验收标准

下一步：进入**阶段 5 实现**，按照规划文档开始编码实现。
