# ♟️ 好友对战功能 - 实现规格文档

**文档版本**: v1.0  
**创建时间**: 2026-03-10 19:15  
**优先级**: P3  
**状态**: 🔄 实施中  
**预计工时**: 2-3 小时

---

## 1. 功能概述

### 1.1 功能描述

好友对战功能允许玩家创建私人房间并邀请好友进行对战，不消耗天梯分，适合朋友间娱乐练习。

### 1.2 现有基础

**已有实现**：
- ✅ `game_type` 字段支持 `'friend'` 选项
- ✅ Game 模型支持好友对战类型
- ✅ 匹配算法中有好友对战入口

**需要实现**：
- ⏳ 创建好友对战房间 API
- ⏳ 生成房间邀请码/链接
- ⏳ 好友加入房间 API
- ⏳ 房间状态管理
- ⏳ 前端创建/加入房间界面

---

## 2. 用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|--------|
| **US-FM-01** | 作为玩家，我希望创建好友对战房间，以便邀请朋友玩游戏 | 点击创建后生成房间号和邀请链接 | P0 |
| **US-FM-02** | 作为玩家，我希望通过房间号加入好友房间 | 输入房间号可快速加入 | P0 |
| **US-FM-03** | 作为玩家，我希望通过链接直接加入房间 | 点击链接自动跳转并加入 | P0 |
| **US-FM-04** | 作为房主，我希望查看房间状态 | 显示等待中/对局中/已结束 | P0 |
| **US-FM-05** | 作为房主，我希望开始游戏 | 好友加入后可点击开始 | P1 |
| **US-FM-06** | 作为玩家，我希望分享房间给好友 | 支持复制链接、分享图片 | P2 |

---

## 3. API 设计

### 3.1 创建好友房间

**端点**: `POST /api/games/friend/create/`

**请求**:
```json
{
  "time_control": 600,
  "is_rated": false
}
```

**响应**:
```json
{
  "id": "abc123",
  "room_code": "CHESS2026",
  "invite_link": "https://xxx.com/games/friend/join/CHESS2026",
  "status": "waiting",
  "creator": "player1",
  "created_at": "2026-03-10T19:15:00Z"
}
```

### 3.2 加入好友房间

**端点**: `POST /api/games/friend/join/`

**请求**:
```json
{
  "room_code": "CHESS2026"
}
```

**响应**:
```json
{
  "game_id": "abc123",
  "status": "playing",
  "red_player": "player1",
  "black_player": "player2"
}
```

### 3.3 获取房间状态

**端点**: `GET /api/games/friend/{room_code}/`

**响应**:
```json
{
  "room_code": "CHESS2026",
  "status": "waiting",
  "creator": "player1",
  "joined_player": null,
  "created_at": "2026-03-10T19:15:00Z"
}
```

---

## 4. 数据模型

### 4.1 FriendRoom 模型

```python
class FriendRoom(models.Model):
    room_code = models.CharField(max_length=10, unique=True)  # 房间号
    game = models.OneToOneField(Game, on_delete=models.CASCADE)  # 关联游戏
    creator = models.ForeignKey(User, on_delete=models.CASCADE)  # 创建者
    status = models.CharField(max_length=20, choices=[
        ('waiting', '等待中'),
        ('playing', '对局中'),
        ('finished', '已结束'),
    ])
    expires_at = models.DateTimeField()  # 过期时间（24 小时）
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 5. 实现任务

### 5.1 后端任务

| ID | 任务 | 预计工时 | 优先级 |
|----|------|---------|--------|
| BE-FM-01 | 创建 FriendRoom 模型 | 30min | P0 |
| BE-FM-02 | 实现创建房间 API | 45min | P0 |
| BE-FM-03 | 实现加入房间 API | 45min | P0 |
| BE-FM-04 | 实现房间状态 API | 30min | P0 |
| BE-FM-05 | 房间过期清理任务 | 30min | P1 |

### 5.2 前端任务

| ID | 任务 | 预计工时 | 优先级 |
|----|------|---------|--------|
| FE-FM-01 | 创建房间页面 | 45min | P0 |
| FE-FM-02 | 加入房间页面 | 30min | P0 |
| FE-FM-03 | 房间状态显示组件 | 30min | P0 |
| FE-FM-04 | 分享功能 | 30min | P2 |

---

## 6. 验收标准

- [ ] 可以创建好友对战房间
- [ ] 房间号唯一且易读（如 CHESS2026）
- [ ] 可以通过房间号加入房间
- [ ] 可以通过链接直接加入
- [ ] 房间状态正确显示
- [ ] 房间 24 小时后自动过期
- [ ] 好友对战不影响天梯分

---

**下一步**: 开始实施 BE-FM-01 创建 FriendRoom 模型
