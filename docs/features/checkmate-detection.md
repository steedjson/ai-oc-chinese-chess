# 将死/困毙检测功能实现文档

## 概述

本功能实现中国象棋中的将死和困毙检测，是游戏核心逻辑的重要组成部分。

- **将死（Checkmate）**：将被将军且无法解救，游戏结束
- **困毙（Stalemate）**：未被将军但无合法走法，游戏结束

## 实现位置

```
projects/chinese-chess/src/backend/games/services/
├── __init__.py              # 服务模块初始化
├── checkmate_detector.py    # 将死检测器
├── stalemate_detector.py    # 困毙检测器
└── game_service.py          # 游戏服务（集成）
```

## 核心逻辑

### 1. 将死检测（CheckmateDetector）

**检测条件**：
1. 当前玩家被将军
2. 当前玩家没有任何合法走法可以解将

**API**：
```python
CheckmateDetector.check_checkmate(board: Board, current_player: str = None) -> bool
```

**参数**：
- `board`: 棋盘对象
- `current_player`: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn

**返回值**：
- `True`: 将死
- `False`: 未将死

**详细检测**：
```python
CheckmateDetector.check_checkmate_detailed(board: Board, current_player: str = None) -> dict
```

返回详细信息：
- `is_checkmate`: 是否将死
- `is_in_check`: 是否被将军
- `legal_moves_count`: 合法走法数量
- `reason`: 原因说明

**模式识别**（教学功能）：
```python
CheckmateDetector.get_checkmate_patterns(board: Board) -> list
```

识别典型将死模式：
- 重炮将死
- 马后炮将死
- 卧槽马将死
- 挂角马将死
- 铁门栓将死
- 大刀剜心将死

### 2. 困毙检测（StalemateDetector）

**检测条件**：
1. 当前玩家未被将军
2. 当前玩家没有任何合法走法

**API**：
```python
StalemateDetector.check_stalemate(board: Board, current_player: str = None) -> bool
```

**参数**：
- `board`: 棋盘对象
- `current_player`: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn

**返回值**：
- `True`: 困毙
- `False`: 未困毙

**详细检测**：
```python
StalemateDetector.check_stalemate_detailed(board: Board, current_player: str = None) -> dict
```

返回详细信息：
- `is_stalemate`: 是否困毙
- `is_in_check`: 是否被将军
- `legal_moves_count`: 合法走法数量
- `reason`: 原因说明

**原因分析**：
```python
StalemateDetector.analyze_stalemate_cause(board: Board, current_player: str = None) -> dict
```

分析困毙原因：
- 所有棋子都被阻塞
- 所有棋子移动都会导致被将军
- 特定棋子受限

### 3. 游戏服务集成（GameService）

**走棋处理**：
```python
GameService.make_move(game_id: int, move_data: Dict[str, str]) -> Dict[str, Any]
```

**流程**：
1. 加载游戏和棋盘
2. 执行走棋
3. 检查是否将死
4. 检查是否困毙
5. 更新游戏状态
6. 返回结果

**游戏状态检查**：
```python
GameService.check_game_status(game_id: int) -> Dict[str, Any]
```

**获取合法走法**：
```python
GameService.get_legal_moves(game_id: int) -> Dict[str, Any]
```

## 使用示例

### 基本使用

```python
from games.engine import Board
from games.services.checkmate_detector import CheckmateDetector
from games.services.stalemate_detector import StalemateDetector

# 加载棋盘
board = Board(fen="3ak4/9/9/9/9/9/9/9/4K4/4R4 w - - 0 1")

# 检查将死
is_checkmate = CheckmateDetector.check_checkmate(board, 'b')
if is_checkmate:
    print("黑方被将死！")

# 检查困毙
is_stalemate = StalemateDetector.check_stalemate(board, 'b')
if is_stalemate:
    print("黑方被困毙！")
```

### 详细检测

```python
# 获取详细将死信息
result = CheckmateDetector.check_checkmate_detailed(board, 'b')
print(f"是否将死：{result['is_checkmate']}")
print(f"是否被将军：{result['is_in_check']}")
print(f"合法走法数：{result['legal_moves_count']}")
print(f"原因：{result['reason']}")
```

### 游戏服务

```python
from games.services.game_service import GameService

game_service = GameService()

# 执行走棋
result = game_service.make_move(game_id=1, move_data={
    'from_pos': 'e2',
    'to_pos': 'e4',
    'piece': 'P'
})

if result['game_over']:
    if result['is_checkmate']:
        print(f"游戏结束，{result['winner']}获胜（将死）")
    elif result['is_stalemate']:
        print("游戏结束，平局（困毙）")
```

## 性能优化

### 1. 缓存机制

将死检测涉及大量计算，建议实现缓存：

```python
from functools import lru_cache

class CheckmateDetector:
    @staticmethod
    @lru_cache(maxsize=1024)
    def check_checkmate_cached(fen: str, current_player: str) -> bool:
        board = Board(fen=fen)
        return CheckmateDetector.check_checkmate(board, current_player)
```

### 2. 提前退出

- 如果未被将军，直接返回 False（不是将死）
- 如果找到一个合法走法，直接返回 False（不是将死）

### 3. 并行计算

对于复杂局面，可以并行检查不同棋子的走法。

## 测试覆盖

### 将死检测测试

- ✅ 基本将死场景（5 个典型棋局）
- ✅ 非将死场景（未被将军）
- ✅ 非将死场景（有合法走法）
- ✅ 详细检测功能
- ✅ 边界条件（空棋盘）

### 困毙检测测试

- ✅ 基本困毙场景（3 个典型棋局）
- ✅ 非困毙场景（被将军）
- ✅ 非困毙场景（有合法走法）
- ✅ 详细检测功能
- ✅ 原因分析功能
- ✅ 边界条件（空棋盘）

## 与现有代码集成

### 依赖关系

```
games/services/checkmate_detector.py
    └── 依赖：games/engine.py (Board 类)

games/services/stalemate_detector.py
    └── 依赖：games/engine.py (Board 类)

games/services/game_service.py
    ├── 依赖：games/models.py (Game, GameMove)
    ├── 依赖：games/engine.py (Board, Move)
    ├── 依赖：games/services/checkmate_detector.py
    └── 依赖：games/services/stalemate_detector.py
```

### 集成点

1. **consumers.py**: WebSocket 消费者中调用 `board.is_checkmate()` 和 `board.is_stalemate()`
2. **game_service.py**: 使用新的检测器服务
3. **views.py**: REST API 中可以调用游戏服务

## 后续改进

### 1. 模式识别增强

实现完整的将死模式识别：
- 重炮将死
- 马后炮将死
- 卧槽马将死
- 挂角马将死
- 铁门栓将死
- 大刀剜心将死
- 双车错将死
- 天地炮将死

### 2. 性能优化

- 实现 FEN 缓存
- 使用位棋盘优化
- 并行计算合法走法

### 3. 教学功能

- 提供解将建议
- 显示所有解将走法
- 将死模式教学

### 4. AI 集成

- 与 Stockfish 集成
- 将死谜题生成
- 将死训练模式

## 安全考虑

- ✅ 输入验证：所有走棋数据都经过验证
- ✅ 错误处理：完善的异常处理
- ✅ 日志记录：详细的日志记录
- ✅ 类型注解：完整的类型注解

## 变更记录

- **2026-03-07**: 初始实现
  - 创建 CheckmateDetector
  - 创建 StalemateDetector
  - 创建 GameService
  - 编写单元测试
  - 编写文档
