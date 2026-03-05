# 中国象棋观战功能

**版本**: 1.0  
**实现日期**: 2026-03-05  
**状态**: ✅ 已完成

---

## 功能概述

观战功能允许用户实时观看其他玩家的象棋对局，包括：
- 加入/离开观战
- 实时棋盘状态同步
- 观战者列表管理
- 匿名观战支持
- 观战权限控制

---

## 数据模型

### Spectator 模型

位于：`src/backend/games/spectator.py`

```python
class Spectator(models.Model):
    id = UUIDField(primary_key=True)
    game = ForeignKey(Game)          # 关联的对局
    user = ForeignKey(User)          # 观战者
    status = CharField()             # watching/left/kicked
    joined_at = DateTimeField()      # 加入时间
    left_at = DateTimeField()        # 离开时间
    duration = IntegerField()        # 观战时长（秒）
    is_anonymous = BooleanField()    # 是否匿名
```

**状态枚举**：
- `watching` - 观战中
- `left` - 已离开
- `kicked` - 被踢出

**约束**：
- 同一用户不能重复观战同一局游戏（unique_together）
- 游戏参与者不能观战自己的游戏

---

## REST API

### 1. 加入观战

```http
POST /api/v1/games/:id/spectate/
Authorization: Bearer <token>

Request:
{
    "is_anonymous": false  // 可选
}

Response (201):
{
    "success": true,
    "spectator": {
        "id": "uuid",
        "game_id": "uuid",
        "user_id": "uuid",
        "joined_at": "ISO8601",
        "is_anonymous": false
    },
    "game_state": {
        "id": "uuid",
        "fen": "...",
        "turn": "w",
        "status": "playing",
        "move_count": 10,
        "red_player": {...},
        "black_player": {...}
    }
}
```

### 2. 离开观战

```http
POST /api/v1/games/:id/spectate/leave/
Authorization: Bearer <token>

Response (200):
{
    "success": true,
    "duration": 120
}
```

### 3. 获取观战列表

```http
GET /api/v1/games/:id/spectators/?limit=50
Authorization: Bearer <token>

Response (200):
{
    "count": 10,
    "spectators": [
        {
            "id": "uuid",
            "user_id": "uuid",
            "username": "xxx",
            "joined_at": "ISO8601",
            "duration": 120,
            "is_anonymous": false
        }
    ]
}
```

### 4. 踢出观战者

```http
POST /api/v1/games/:id/spectators/kick/
Authorization: Bearer <token>

Request:
{
    "spectator_id": "uuid"
}

Response (200):
{
    "success": true,
    "message": "已将 xxx 踢出观战"
}
```

**权限**：仅游戏创建者（红方）或管理员可用

### 5. 获取活跃游戏列表

```http
GET /api/v1/spectator/active-games/?limit=20
Authorization: Bearer <token>

Response (200):
{
    "count": 10,
    "games": [
        {
            "id": "uuid",
            "status": "playing",
            "move_count": 15,
            "spectator_count": 5,
            "red_player": {...},
            "black_player": {...}
        }
    ]
}
```

### 6. 获取观战者信息

```http
GET /api/v1/games/:game_id/spectators/:id/
Authorization: Bearer <token>

Response (200):
{
    "id": "uuid",
    "game_id": "uuid",
    "user": {
        "id": "uuid",
        "username": "xxx"
    },
    "status": "watching",
    "joined_at": "ISO8601",
    "duration": 120,
    "is_anonymous": false
}
```

---

## WebSocket

### 观战连接

```javascript
// 连接观战房间
const ws = new WebSocket(
    `ws://localhost:8000/ws/spectate/${game_id}/?token=${jwt_token}`
);

ws.onopen = () => {
    console.log('Connected to spectate room');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'GAME_STATE':
            // 初始游戏状态
            console.log('Current FEN:', data.payload.fen);
            break;
        
        case 'MOVE_MADE':
            // 玩家走棋通知
            console.log('Move:', data.payload.move);
            updateBoard(data.payload.fen);
            break;
        
        case 'GAME_OVER':
            // 游戏结束
            console.log('Winner:', data.payload.winner);
            break;
        
        case 'SPECTATOR_JOIN':
            // 新观战者加入
            console.log('New spectator:', data.payload.username);
            break;
        
        case 'SPECTATOR_LEAVE':
            // 观战者离开
            console.log('Spectator left:', data.payload.username);
            break;
        
        case 'HEARTBEAT':
            // 心跳响应
            break;
        
        case 'ERROR':
            // 错误
            console.error(data.payload.error);
            break;
    }
};

// 发送心跳
setInterval(() => {
    ws.send(JSON.stringify({type: 'HEARTBEAT'}));
}, 30000);
```

### 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `GAME_STATE` | 服务器→客户端 | 初始游戏状态 |
| `MOVE_MADE` | 服务器→客户端 | 玩家走棋通知 |
| `GAME_OVER` | 服务器→客户端 | 游戏结束 |
| `SPECTATOR_JOIN` | 服务器→客户端 | 新观战者加入 |
| `SPECTATOR_LEAVE` | 服务器→客户端 | 观战者离开 |
| `HEARTBEAT` | 双向 | 心跳 |
| `JOIN` | 客户端→服务器 | 加入观战 |
| `LEAVE` | 客户端→服务器 | 离开观战 |
| `ERROR` | 服务器→客户端 | 错误消息 |

---

## 权限控制

### 观战权限

1. **只能观战进行中的游戏**（status: playing/pending）
2. **游戏参与者不能观战**（红方或黑方玩家）
3. **需要认证**（JWT Token）

### 管理权限

1. **踢出观战者**：仅游戏创建者（红方）或管理员
2. **查看观战列表**：所有认证用户
3. **查看观战者信息**：仅自己、游戏参与者或管理员

---

## 实现文件

### 后端

| 文件 | 说明 |
|------|------|
| `src/backend/games/spectator.py` | 观战数据模型和管理器 |
| `src/backend/games/spectator_views.py` | 观战 API 视图 |
| `src/backend/games/spectator_consumer.py` | 观战 WebSocket Consumer |
| `src/backend/games/migrations/0002_spectator_model.py` | 数据库迁移 |
| `src/backend/games/urls.py` | URL 路由（已更新） |
| `src/backend/games/routing.py` | WebSocket 路由（已更新） |
| `src/backend/games/consumers.py` | GameConsumer（已更新通知观战者） |

### 测试

| 文件 | 说明 |
|------|------|
| `tests/unit/games/test_spectator.py` | 模型和管理器测试 |
| `tests/unit/games/test_spectator_views.py` | API 视图测试 |
| `tests/unit/games/test_spectator_basic.py` | 基础功能测试 |
| `tests/unit/websocket/test_spectator_consumer.py` | WebSocket Consumer 测试 |

---

## 使用示例

### Python 示例

```python
from games.spectator import SpectatorManager

# 加入观战
result = await SpectatorManager.join_spectate(
    game_id='uuid',
    user_id='uuid',
    is_anonymous=False
)

if result['success']:
    print(f"Joined spectate: {result['spectator'].id}")
else:
    print(f"Failed: {result['error']}")

# 离开观战
result = await SpectatorManager.leave_spectate(
    game_id='uuid',
    user_id='uuid'
)

# 获取观战列表
spectators = await SpectatorManager.get_spectators(game_id='uuid')

# 获取观战人数
count = await SpectatorManager.get_spectator_count(game_id='uuid')
```

### JavaScript 示例

```javascript
// 加入观战
const response = await fetch(`/api/v1/games/${gameId}/spectate/`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({is_anonymous: false})
});

const data = await response.json();
console.log('Spectator ID:', data.spectator.id);

// 获取观战列表
const spectatorsResponse = await fetch(`/api/v1/games/${gameId}/spectators/`);
const spectatorsData = await spectatorsResponse.json();
console.log('Spectators:', spectatorsData.spectators);
```

---

## 测试

### 运行测试

```bash
cd src/backend
python3 -m pytest ../../tests/unit/games/test_spectator_basic.py -v
```

### 测试覆盖

- ✅ Spectator 模型创建
- ✅ 加入观战（正常/异常场景）
- ✅ 离开观战
- ✅ 获取观战列表
- ✅ 观战人数统计
- ✅ 踢出观战者
- ✅ 权限控制
- ✅ API 端点
- ✅ WebSocket 消息处理

---

## 前端集成

### React 组件示例

```jsx
function SpectatorRoom({ gameId }) {
    const [spectators, setSpectators] = useState([]);
    const [gameState, setGameState] = useState(null);
    const ws = useRef(null);
    
    useEffect(() => {
        // 连接 WebSocket
        ws.current = new WebSocket(
            `ws://localhost:8000/ws/spectate/${gameId}/?token=${token}`
        );
        
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch(data.type) {
                case 'GAME_STATE':
                    setGameState(data.payload);
                    break;
                case 'MOVE_MADE':
                    updateBoard(data.payload.fen);
                    break;
                case 'SPECTATOR_LIST':
                    setSpectators(data.payload.spectators);
                    break;
            }
        };
        
        return () => ws.current?.close();
    }, [gameId]);
    
    return (
        <div>
            <ChessBoard fen={gameState?.fen} />
            <SpectatorList spectators={spectators} />
        </div>
    );
}
```

---

## 性能优化

1. **观战者数量限制**：默认 50 人
2. **不活跃清理**：30 分钟无活动自动离开
3. **匿名观战**：减少隐私暴露
4. **增量更新**：只推送变化的状态

---

## 安全考虑

1. **JWT 认证**：所有操作需要有效 token
2. **权限验证**：参与者不能观战，只有创建者可管理
3. **输入验证**：所有 API 参数严格验证
4. **速率限制**：防止滥用（待实现）

---

## 待扩展功能

- [ ] 观战聊天功能
- [ ] 观战者视角切换（红方/黑方/俯视）
- [ ] 观战录像回放
- [ ] 热门对局推荐
- [ ] 观战数据统计

---

## 变更日志

### v1.0 (2026-03-05)
- ✅ 初始实现
- ✅ 数据模型
- ✅ REST API
- ✅ WebSocket 支持
- ✅ 基础测试
