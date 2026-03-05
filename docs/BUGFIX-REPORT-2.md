# Bug Fix Report #2 - WebSocket Consumer 和匹配系统修复

**日期**: 2026-03-03  
**修复人**: OpenClaw 助手  
**项目**: 中国象棋  
**优先级**: ⭐⭐⭐⭐⭐

---

## 问题 1: WebSocket Consumer close() 参数错误

### 问题描述
`AsyncWebsocketConsumer.close()` 不支持 `reason` 参数，导致 TypeError。

**错误信息**:
```
TypeError: AsyncWebsocketConsumer.close() got an unexpected keyword argument 'reason'
```

### 根本原因
Django Channels 的 `AsyncWebsocketConsumer.close()` 方法只支持 `code` 参数，不支持 `reason` 参数。

**Django Channels close() 正确用法**:
```python
# ❌ 错误写法
await self.close(reason='code')
await self.close(code=4001, reason='message')

# ✅ 正确写法
await self.close(code=4001)  # 只支持 code 参数
# 或者先发送错误消息再关闭
await self.send(text_data=json.dumps({'error': 'message'}))
await self.close()
```

### 修复文件

#### 1. `src/backend/websocket/consumers.py` (第 258 行)

**修复前**:
```python
async def _send_connection_error(self, message: str):
    """发送连接错误并关闭"""
    await self.close(code=4001, reason=message)
```

**修复后**:
```python
async def _send_connection_error(self, message: str):
    """发送连接错误并关闭"""
    await self.send(text_data=json.dumps({
        'type': 'ERROR',
        'payload': {
            'success': False,
            'error': {
                'code': 'CONNECTION_ERROR',
                'message': message
            }
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }))
    await self.close(code=4001)
```

#### 2. `src/backend/games/consumers.py` (第 61、69 行)

**修复前**:
```python
# 验证用户身份
user = await self._authenticate_connection()
if not user:
    await self.close(code=4001, reason='Invalid or expired token')
    return

# 验证用户是否有权加入游戏
can_join = await self._can_join_game()
if not can_join:
    await self.close(code=4003, reason='Not authorized to join this game')
    return
```

**修复后**:
```python
# 验证用户身份
user = await self._authenticate_connection()
if not user:
    await self.send(text_data=json.dumps({
        'type': 'ERROR',
        'payload': {
            'success': False,
            'error': {
                'code': 'AUTH_FAILED',
                'message': 'Invalid or expired token'
            }
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }))
    await self.close(code=4001)
    return

# 验证用户是否有权加入游戏
can_join = await self._can_join_game()
if not can_join:
    await self.send(text_data=json.dumps({
        'type': 'ERROR',
        'payload': {
            'success': False,
            'error': {
                'code': 'AUTH_FORBIDDEN',
                'message': 'Not authorized to join this game'
            }
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }))
    await self.close(code=4003)
    return
```

#### 3. `src/backend/websocket/middleware.py` (文档注释更新)

更新了文档字符串中的示例代码，使其符合 Django Channels 的正确用法：

**修复前**:
```python
await self.close(code=4001, reason='Invalid token')
await self.close(code=4003, reason='Not authorized')
await self.close(code=4001, reason='Invalid or expired token')
```

**修复后**:
```python
await self.close(code=4001)  # Django Channels 只支持 code 参数
await self.close(code=4003)  # Django Channels 只支持 code 参数
await self.close(code=4001)  # Django Channels 只支持 code 参数
```

### 验证方法
1. 启动 WebSocket 服务
2. 使用无效 token 连接 WebSocket
3. 验证不再报 TypeError
4. 验证客户端收到错误消息

---

## 问题 2: QueueUser 参数不匹配

### 问题描述
`QueueUser.__init__()` 参数在不同文件中不一致，导致 TypeError。

**错误信息**:
```
TypeError: QueueUser.__init__() missing required arguments: ...
```

### 根本原因
`QueueUser` 在 `queue.py` 中定义为 dataclass，需要 5 个参数：
- `user_id: str`
- `rating: int`
- `joined_at: float`
- `search_range: int`
- `game_type: str`

但在 `consumers.py` 和 `views.py` 中使用了错误的参数（如 `username`），且缺少必需参数。

### QueueUser 正确定义

**`src/backend/matchmaking/queue.py`**:
```python
@dataclass
class QueueUser:
    """队列中的用户信息"""
    user_id: str
    rating: int
    joined_at: float
    search_range: int
    game_type: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueueUser':
        """从字典创建"""
        return cls(
            user_id=data.get('user_id', ''),
            rating=int(data.get('rating', 1500)),
            joined_at=float(data.get('joined_at', time.time())),
            search_range=int(data.get('search_range', INITIAL_SEARCH_RANGE)),
            game_type=data.get('game_type', 'online')
        )
```

### 修复文件

#### 1. `src/backend/matchmaking/consumers.py`

**修复前**:
```python
# 创建队列用户
queue_user = QueueUser(
    user_id=self.user['id'],
    username=self.user['username'],  # ❌ 不存在的参数
    game_type=game_type
)

# 获取用户 Elo（从数据库）
user_elo = await self._get_user_elo()
queue_user.rating = user_elo  # ❌ 事后赋值，不是构造函数参数
```

**修复后**:
```python
import time

# 获取用户 Elo（从数据库）
user_elo = await self._get_user_elo()

# 创建队列用户 - 使用 QueueUser 定义的正确参数
queue_user = QueueUser(
    user_id=self.user['id'],
    rating=user_elo,
    joined_at=time.time(),
    search_range=100,  # INITIAL_SEARCH_RANGE
    game_type=game_type
)
```

#### 2. `src/backend/matchmaking/consumers.py` - `_add_to_queue` 方法

**修复前**:
```python
async def _add_to_queue(self, queue_user: QueueUser) -> bool:
    try:
        # ❌ add_user 方法不存在
        self.queue.add_user(queue_user)
        await self._save_queue_record(queue_user)
        return True
    except Exception as e:
        logger.error(f"Error adding to queue: {e}")
        return False
```

**修复后**:
```python
async def _add_to_queue(self, queue_user: QueueUser) -> bool:
    try:
        # ✅ 使用正确的 join_queue 方法
        success = self.queue.join_queue(
            user_id=queue_user.user_id,
            rating=queue_user.rating,
            game_type=queue_user.game_type
        )
        
        if success:
            await self._save_queue_record(queue_user)
        
        return success
    except Exception as e:
        logger.error(f"Error adding to queue: {e}")
        return False
```

#### 3. `src/backend/matchmaking/consumers.py` - `_remove_from_queue` 方法

**修复前**:
```python
async def _remove_from_queue(self) -> bool:
    try:
        if not self.user_queue_data:
            return False
        
        # ❌ remove_user 方法不存在
        self.queue.remove_user(self.user['id'])
        await self._update_queue_record_status('cancelled')
        return True
    except Exception as e:
        logger.error(f"Error removing from queue: {e}")
        return False
```

**修复后**:
```python
async def _remove_from_queue(self) -> bool:
    try:
        if not self.user_queue_data:
            return False
        
        # ✅ 使用正确的 leave_queue 方法
        success = self.queue.leave_queue(
            user_id=self.user['id'],
            game_type=self.user_queue_data.game_type
        )
        
        if success:
            await self._update_queue_record_status('cancelled')
        
        return success
    except Exception as e:
        logger.error(f"Error removing from queue: {e}")
        return False
```

#### 4. `src/backend/matchmaking/consumers.py` - `_get_queue_position` 方法

**修复前**:
```python
async def _get_queue_position(self) -> int:
    try:
        # ❌ 缺少 game_type 参数
        return self.queue.get_queue_position(self.user['id'])
    except Exception:
        return -1
```

**修复后**:
```python
async def _get_queue_position(self) -> int:
    try:
        game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
        queue_info = self.queue.get_queue_position(self.user['id'], game_type)
        return queue_info.get('position', -1)
    except Exception:
        return -1
```

#### 5. `src/backend/matchmaking/consumers.py` - `_estimate_wait_time` 方法

**修复前**:
```python
async def _estimate_wait_time(self) -> int:
    try:
        # ❌ estimate_wait_time 方法不存在
        return self.queue.estimate_wait_time(self.user['id'])
    except Exception:
        return -1
```

**修复后**:
```python
async def _estimate_wait_time(self) -> int:
    try:
        game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
        queue_info = self.queue.get_queue_position(self.user['id'], game_type)
        return int(queue_info.get('wait_time', 0))
    except Exception:
        return -1
```

#### 6. `src/backend/matchmaking/consumers.py` - `_get_queue_status` 方法

**修复前**:
```python
async def _get_queue_status(self) -> Dict[str, Any]:
    try:
        # ❌ get_queue_size 方法不存在
        total_in_queue = self.queue.get_queue_size()
        position = await self._get_queue_position()
        estimated_wait = await self._estimate_wait_time()
        
        return {
            'total_in_queue': total_in_queue,
            'your_position': position if self.user_queue_data else None,
            'estimated_wait_time': estimated_wait if self.user_queue_data else None,
            'in_queue': self.user_queue_data is not None
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {}
```

**修复后**:
```python
async def _get_queue_status(self) -> Dict[str, Any]:
    try:
        game_type = self.user_queue_data.game_type if self.user_queue_data else 'ranked'
        stats = self.queue.get_queue_stats(game_type)
        position = await self._get_queue_position()
        estimated_wait = await self._estimate_wait_time()
        
        return {
            'total_in_queue': stats.get('total_players', 0),
            'your_position': position if self.user_queue_data else None,
            'estimated_wait_time': estimated_wait if self.user_queue_data else None,
            'in_queue': self.user_queue_data is not None
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {}
```

#### 7. `src/backend/matchmaking/views.py` - StartMatchmakingView

**修复前**:
```python
def post(self, request):
    try:
        game_type = request.data.get('game_type', 'ranked')
        user = request.user
        
        # ❌ 参数错误
        queue_user = QueueUser(
            user_id=str(user.id),
            username=user.username,  # 不存在的参数
            game_type=game_type
        )
        
        queue = MatchmakingQueue()
        queue.add_user(queue_user)  # ❌ 方法不存在
        
        return Response({
            'success': True,
            'message': '加入匹配队列成功',
            'game_type': game_type,
            'queue_position': queue.get_queue_position(str(user.id)),
            'estimated_wait_time': queue.estimate_wait_time(str(user.id))
        }, status=status.HTTP_200_OK)
```

**修复后**:
```python
def post(self, request):
    try:
        import time
        game_type = request.data.get('game_type', 'ranked')
        user = request.user
        
        # ✅ 使用正确的参数
        queue_user = QueueUser(
            user_id=str(user.id),
            rating=getattr(user, 'elo_rating', 1500),
            joined_at=time.time(),
            search_range=100,
            game_type=game_type
        )
        
        queue = MatchmakingQueue()
        success = queue.join_queue(
            user_id=str(user.id),
            rating=getattr(user, 'elo_rating', 1500),
            game_type=game_type
        )
        
        if not success:
            return Response({
                'success': False,
                'error': '已在队列中或加入失败'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取队列信息
        queue_info = queue.get_queue_position(str(user.id), game_type)
        estimated_wait = queue_info.get('wait_time', 0)
        
        return Response({
            'success': True,
            'message': '加入匹配队列成功',
            'game_type': game_type,
            'queue_position': queue_info.get('position', 0),
            'estimated_wait_time': int(estimated_wait)
        }, status=status.HTTP_200_OK)
```

#### 8. `src/backend/matchmaking/views.py` - CancelMatchmakingView

**修复前**:
```python
def post(self, request):
    try:
        user = request.user
        queue = MatchmakingQueue()
        queue.remove_user(str(user.id))  # ❌ 方法不存在
```

**修复后**:
```python
def post(self, request):
    try:
        user = request.user
        game_type = request.data.get('game_type', 'ranked')
        queue = MatchmakingQueue()
        queue.leave_queue(str(user.id), game_type)  # ✅ 正确方法
```

#### 9. `src/backend/matchmaking/views.py` - MatchStatusView

**修复前**:
```python
def get(self, request):
    try:
        user = request.user
        queue = MatchmakingQueue()
        
        return Response({
            'success': True,
            'in_queue': queue.is_user_in_queue(str(user.id)),  # ❌ 方法名错误
            'queue_position': queue.get_queue_position(str(user.id)),  # ❌ 缺少 game_type
            'estimated_wait_time': queue.estimate_wait_time(str(user.id)),  # ❌ 方法不存在
            'total_in_queue': queue.get_queue_size()  # ❌ 方法不存在
        }, status=status.HTTP_200_OK)
```

**修复后**:
```python
def get(self, request):
    try:
        user = request.user
        game_type = request.query_params.get('game_type', 'ranked')
        queue = MatchmakingQueue()
        
        in_queue = queue.is_in_queue(str(user.id), game_type)
        queue_info = queue.get_queue_position(str(user.id), game_type) if in_queue else {}
        stats = queue.get_queue_stats(game_type)
        
        return Response({
            'success': True,
            'in_queue': in_queue,
            'queue_position': queue_info.get('position', 0) if in_queue else None,
            'estimated_wait_time': int(queue_info.get('wait_time', 0)) if in_queue else None,
            'total_in_queue': stats.get('total_players', 0)
        }, status=status.HTTP_200_OK)
```

### 验证方法
1. 启动 Django 服务
2. 调用 `/api/matchmaking/start/` API
3. 验证不再报参数错误
4. 验证用户成功加入队列
5. 调用 `/api/matchmaking/cancel/` API
6. 验证用户成功退出队列
7. 调用 `/api/matchmaking/status/` API
8. 验证返回正确的队列状态

---

## 修复总结

### 修复的文件列表
| 文件 | 问题类型 | 修复内容 |
|------|---------|---------|
| `websocket/consumers.py` | WebSocket close | 移除 reason 参数 |
| `games/consumers.py` | WebSocket close | 移除 reason 参数，先发送错误消息 |
| `websocket/middleware.py` | 文档注释 | 更新示例代码 |
| `matchmaking/consumers.py` | QueueUser 参数 | 修正构造函数参数和方法调用 |
| `matchmaking/views.py` | QueueUser 参数 | 修正构造函数参数和方法调用 |

### 修复的方法列表
- `AsyncWebsocketConsumer.close()` - 5 处
- `QueueUser.__init__()` - 2 处
- `MatchmakingQueue.join_queue()` - 2 处
- `MatchmakingQueue.leave_queue()` - 2 处
- `MatchmakingQueue.get_queue_position()` - 3 处
- `MatchmakingQueue.get_queue_stats()` - 2 处
- `MatchmakingQueue.is_in_queue()` - 1 处

### 剩余问题
无。所有发现的问题已修复。

---

## 测试建议

### WebSocket close 测试
```bash
# 1. 使用无效 token 连接 WebSocket
wscat -c "ws://localhost:8000/ws/game/test-game-id/?token=invalid_token"

# 预期结果：
# - 收到 ERROR 消息
# - 连接关闭，不再报 TypeError
```

### 匹配系统测试
```bash
# 1. 开始匹配
curl -X POST http://localhost:8000/api/matchmaking/start/ \
  -H "Authorization: Bearer <valid_token>" \
  -H "Content-Type: application/json" \
  -d '{"game_type": "ranked"}'

# 预期结果：
# - 返回 200 OK
# - 包含 queue_position 和 estimated_wait_time

# 2. 查询匹配状态
curl http://localhost:8000/api/matchmaking/status/?game_type=ranked \
  -H "Authorization: Bearer <valid_token>"

# 预期结果：
# - 返回 200 OK
# - in_queue: true

# 3. 取消匹配
curl -X POST http://localhost:8000/api/matchmaking/cancel/ \
  -H "Authorization: Bearer <valid_token>" \
  -H "Content-Type: application/json" \
  -d '{"game_type": "ranked"}'

# 预期结果：
# - 返回 200 OK
# - 成功退出队列
```

---

## 结论

本次修复解决了两个关键的后端问题：

1. **WebSocket Consumer close() 参数错误** - 所有使用 `close(reason=...)` 的地方已修改为正确的 Django Channels 用法
2. **QueueUser 参数不匹配** - 统一了 `QueueUser` 的构造函数参数，修复了所有调用处的方法名和参数

修复后，WebSocket 连接和匹配系统应该能够正常工作，不再报 TypeError。

**修复完成时间**: 2026-03-03 20:38 GMT+8
