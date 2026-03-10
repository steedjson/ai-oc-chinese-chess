# 🔄 中国象棋项目 - 并发执行分析报告

**文档版本**: v1.0  
**创建时间**: 2026-03-05 20:00  
**分析目标**: TODO-6.3 (残局挑战) 与 TODO-6.5 (聊天系统) 并发执行策略  
**分析师**: Subagent (Concurrency Analysis)

---

## 📋 执行摘要

### 关键发现

| 发现项 | 结论 | 影响 |
|--------|------|------|
| **任务独立性** | ✅ 高度独立 | 可安全并行开发 |
| **共享资源** | ⚠️ 共用 WebSocket 基础设施 | 需协调 Consumer 路由 |
| **数据库冲突** | ✅ 无表结构冲突 | 独立 Model，可并行迁移 |
| **代码冲突风险** | 🟢 低 | 不同 App 模块 |
| **推荐并发数** | 2-3 个并行任务 | 充分利用开发资源 |
| **预计节省时间** | ~40% | 并行 vs 串行 |

### 推荐策略

**🎯 并行执行** - 两个任务可以安全地同时进行，预计总耗时从 **12 小时** 降至 **7 小时**

---

## 1. 任务分解

### 1.1 TODO-6.3 残局挑战模式 (预计 8 小时)

```
TODO-6.3 残局挑战模式
├── 6.3.1 后端模型设计 (1.5h)
│   ├── Puzzle 模型 (残局题目)
│   ├── PuzzleAttempt 模型 (尝试记录)
│   └── 数据库迁移
│
├── 6.3.2 后端业务逻辑 (2h)
│   ├── PuzzleService (残局服务)
│   ├── 走棋验证逻辑 (与现有 engine 集成)
│   └── 完成判定算法
│
├── 6.3.3 REST API 开发 (1.5h)
│   ├── GET /api/puzzles/ - 获取残局列表
│   ├── GET /api/puzzles/:id/ - 获取残局详情
│   ├── POST /api/puzzles/:id/attempt/ - 提交走棋
│   └── GET /api/puzzles/history/ - 历史尝试
│
├── 6.3.4 前端开发 (2h)
│   ├── PuzzleList 组件
│   ├── PuzzleChallenge 组件 (棋盘 + 提示)
│   └── 结果反馈 UI
│
└── 6.3.5 测试 (1h)
    ├── 单元测试 (模型 + 服务)
    └── 集成测试 (API + 前端)
```

### 1.2 TODO-6.5 聊天系统 (预计 4 小时)

```
TODO-6.5 聊天系统
├── 6.5.1 后端模型设计 (0.5h)
│   ├── ChatMessage 模型
│   └── 数据库迁移
│
├── 6.5.2 REST API 开发 (1h)
│   ├── GET /api/games/:id/chat/ - 获取聊天记录
│   └── POST /api/games/:id/chat/ - 发送消息
│
├── 6.5.3 WebSocket Consumer (1h)
│   ├── ChatConsumer 或扩展现有 GameConsumer
│   ├── 消息广播逻辑
│   └── 权限验证
│
├── 6.5.4 前端开发 (1h)
│   ├── ChatPanel 组件
│   ├── MessageList 组件
│   └── 输入框 + 发送按钮
│
└── 6.5.5 测试 (0.5h)
    ├── 单元测试
    └── WebSocket 测试
```

---

## 2. 依赖关系分析

### 2.1 任务依赖图

```
                    ┌─────────────────┐
                    │   现有基础设施   │
                    │  (已完成)       │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────────┐    ┌────────────────┐
     │  games/engine  │    │  websocket/    │
     │  (规则引擎)    │    │  (WS 基础)      │
     └───────┬────────┘    └───────┬────────┘
             │                     │
             ▼                     ▼
     ┌────────────────┐    ┌────────────────┐
     │  TODO-6.3      │    │  TODO-6.5      │
     │  残局挑战      │    │  聊天系统      │
     │                │    │                │
     │  ┌──────────┐  │    │  ┌──────────┐  │
     │  │Puzzle    │  │    │  │ChatMessage│ │
     │  │Model     │  │    │  │Model     │ │
     │  └──────────┘  │    │  └──────────┘  │
     │  ┌──────────┐  │    │  ┌──────────┐  │
     │  │Puzzle    │  │    │  │Chat API  │  │
     │  │Service   │  │    │  └──────────┘  │
     │  └──────────┘  │    │  ┌──────────┐  │
     │  ┌──────────┐  │    │  │Chat WS   │  │
     │  │Puzzle    │  │    │  │Consumer  │  │
     │  │API       │  │    │  └──────────┘  │
     │  └──────────┘  │    │  ┌──────────┐  │
     │  ┌──────────┐  │    │  │Chat UI   │  │
     │  │Puzzle    │  │    │  │Component │  │
     │  │UI        │  │    │  └──────────┘  │
     │  └──────────┘  │    └────────────────┘
     └────────────────┘
```

### 2.2 依赖关系矩阵

| 依赖项 | TODO-6.3 | TODO-6.5 | 冲突风险 |
|--------|----------|----------|----------|
| **games/engine.py** | ✅ 强依赖 (走棋验证) | ❌ 无依赖 | - |
| **websocket 基础** | ⚠️ 弱依赖 (可复用) | ✅ 强依赖 (新建 Consumer) | 🟡 中 |
| **Game 模型** | ⚠️ 弱依赖 (可选关联) | ✅ 强依赖 (外键) | 🟢 低 |
| **数据库** | ✅ 独立表 | ✅ 独立表 | 🟢 低 |
| **前端棋盘组件** | ✅ 复用现有 | ❌ 无依赖 | - |
| **认证系统** | ✅ 复用现有 | ✅ 复用现有 | 🟢 低 |

### 2.3 共享资源识别

| 共享资源 | 使用方式 | 冲突风险 | 缓解措施 |
|----------|----------|----------|----------|
| **WebSocket 路由** | 6.3 可能复用 GameConsumer<br>6.5 需要 ChatConsumer | 🟡 中 | 提前规划路由结构 |
| **数据库连接池** | 两者都需要 DB 访问 | 🟢 低 | Django ORM 自动管理 |
| **Redis 缓存** | 可能都使用缓存 | 🟢 低 | Key 前缀区分 |
| **静态文件目录** | 前端资源存放 | 🟢 低 | 子目录隔离 |
| **API 版本前缀** | `/api/v1/` | 🟢 低 | 统一规范 |

---

## 3. 并发执行策略

### 3.1 可并行子任务

| 阶段 | TODO-6.3 子任务 | TODO-6.5 子任务 | 并行可行性 |
|------|----------------|----------------|------------|
| **阶段 1** | 6.3.1 模型设计 | 6.5.1 模型设计 | ✅ 完全可并行 |
| **阶段 2** | 6.3.2 业务逻辑 | 6.5.2 API 开发 | ✅ 完全可并行 |
| **阶段 3** | 6.3.3 API 开发 | 6.5.3 WebSocket | ✅ 可并行 (不同 Consumer) |
| **阶段 4** | 6.3.4 前端开发 | 6.5.4 前端开发 | ✅ 完全可并行 |
| **阶段 5** | 6.3.5 测试 | 6.5.5 测试 | ✅ 完全可并行 |

### 3.2 必须串行子任务

| 串行点 | 原因 | 建议顺序 |
|--------|------|----------|
| **数据库迁移执行** | 避免迁移冲突 | 先 6.3.1 → 后 6.5.1 (或反之) |
| **WebSocket 路由注册** | 避免路由冲突 | 协调后统一注册 |
| **集成测试** | 需要完整环境 | 所有开发完成后统一进行 |

### 3.3 推荐执行顺序

```
时间轴 (小时)
0───────1───────2───────3───────4───────5───────6───────7───────8

【TODO-6.3 残局挑战】
│
├─ 6.3.1 模型设计 (0-1.5h)
│
├─ 6.3.2 业务逻辑 (1.5-3.5h)
│
├─ 6.3.3 API 开发 (3.5-5h)
│
├─ 6.3.4 前端开发 (5-7h)
│
└─ 6.3.5 测试 (7-8h)


【TODO-6.5 聊天系统】
        │
        ├─ 6.5.1 模型设计 (1.5-2h)  ← 等待 6.3.1 迁移完成
        │
        ├─ 6.5.2 API 开发 (2-3h)
        │
        ├─ 6.5.3 WebSocket (3-4h)
        │
        ├─ 6.5.4 前端开发 (4-5h)
        │
        └─ 6.5.5 测试 (5-5.5h)


【集成测试】
                                        │
                                        └─ 统一集成测试 (5.5-7h)
```

### 3.4 最优并发数建议

| 场景 | 推荐并发数 | 说明 |
|------|------------|------|
| **单人开发** | 1-2 | 交替进行，避免上下文切换过多 |
| **双人开发** | 2 | 每人负责一个任务，完全并行 |
| **三人开发** | 2-3 | 2 人并行开发 + 1 人负责集成测试 |

**系统资源评估**:
- CPU: 开发任务主要为 I/O 密集型，2-3 并发不会造成瓶颈
- 内存: Django 开发服务器 + 前端 Dev Server ≈ 2-3GB，充足
- 数据库连接: SQLite (开发) 无限制，PostgreSQL 连接池默认 100+

---

## 4. 资源评估

### 4.1 任务类型分析

| 任务 | 类型 | CPU 密集 | I/O 密集 | 说明 |
|------|------|---------|---------|------|
| 模型设计 | 设计 | 🟢 低 | 🟡 中 | 主要是思考 + 写代码 |
| 业务逻辑 | 开发 | 🟡 中 | 🟢 低 | 算法实现 |
| API 开发 | 开发 | 🟢 低 | 🟡 中 | 数据库 I/O |
| WebSocket | 开发 | 🟢 低 | 🟠 高 | 实时通信 |
| 前端开发 | 开发 | 🟢 低 | 🟡 中 | 组件渲染 |
| 测试 | 测试 | 🟡 中 | 🟡 中 | 测试执行 |

### 4.2 数据库连接需求

| 模块 | 并发连接数 | 峰值预估 | 说明 |
|------|------------|---------|------|
| **残局挑战** | 1-2 | 5 | 主要是读操作 |
| **聊天系统** | 2-5 | 20+ | 高频写入 + 广播 |
| **现有系统** | 5-10 | 50 | 游戏对局 + 匹配 |
| **总计** | 8-17 | 75 | 安全范围内 |

### 4.3 内存占用预估

| 组件 | 基础占用 | 峰值占用 | 备注 |
|------|---------|---------|------|
| Django Dev Server | 300MB | 500MB | 含自动重载 |
| Frontend Dev Server | 200MB | 400MB | Vite |
| WebSocket Consumer | 50MB | 200MB | 按连接数 |
| 数据库 (SQLite) | 50MB | 100MB | 开发环境 |
| **总计** | **600MB** | **1.2GB** | 安全 |

---

## 5. 风险评估

### 5.1 风险矩阵

| 风险项 | 概率 | 影响 | 风险等级 | 缓解措施 |
|--------|------|------|----------|----------|
| **代码冲突** | 🟡 中 | 🟢 低 | 🟢 低 | 不同 App 目录，Git 分支管理 |
| **数据库迁移冲突** | 🟡 中 | 🟡 中 | 🟡 中 | 串行执行迁移，测试后合并 |
| **WebSocket 路由冲突** | 🟡 中 | 🟡 中 | 🟡 中 | 提前规划 URL 结构 |
| **端口/资源冲突** | 🟢 低 | 🟢 低 | 🟢 低 | Django 自动管理 |
| **测试环境不稳定** | 🟡 中 | 🟡 中 | 🟡 中 | 独立测试数据库 |
| **上下文切换成本** | 🟠 高 | 🟡 中 | 🟡 中 | 限制并发数，专注完成 |

### 5.2 关键风险详解

#### 风险 1: 数据库迁移冲突

**场景**: 两个任务同时创建迁移文件，可能导致迁移顺序问题

**缓解措施**:
```bash
# 1. 先完成一个任务的迁移
python manage.py makemigrations puzzles  # TODO-6.3
python manage.py migrate

# 2. 再完成另一个任务的迁移
python manage.py makemigrations chat  # TODO-6.5
python manage.py migrate

# 3. 或者合并迁移文件后统一执行
```

#### 风险 2: WebSocket 路由冲突

**场景**: 两个 Consumer 可能竞争相同的路由路径

**缓解措施**:
```python
# 明确的路由规划
websocket_urlpatterns = [
    # 游戏对局
    re_path(r'ws/game/(?P<game_id>[^/]+)/$', GameConsumer.as_asgi()),
    
    # 聊天 (独立路径)
    re_path(r'ws/chat/(?P<room_id>[^/]+)/$', ChatConsumer.as_asgi()),
    
    # 或者在游戏 WS 中支持聊天子通道
    re_path(r'ws/game/(?P<game_id>[^/]+)/chat/$', GameChatConsumer.as_asgi()),
]
```

#### 风险 3: 上下文切换成本

**场景**: 单人开发时频繁切换任务导致效率下降

**缓解措施**:
- 按阶段切换，而非按小时切换
- 完成一个里程碑后再切换
- 使用任务清单保持上下文

---

## 6. 时间对比

### 6.1 串行执行 (基准)

```
TODO-6.3 残局挑战: 8 小时
TODO-6.5 聊天系统: 4 小时
─────────────────────────────
总耗时: 12 小时
```

### 6.2 并行执行 (推荐)

```
时间轴:
0───────2───────4───────6───────8
│        │        │        │
│ 6.3.x  │ 6.3.x  │ 6.3.x  │ 6.3.5
│ 6.5.x  │ 6.5.x  │ 6.5.5  │
│        │        │        │
└────────┴────────┴────────┴──→
         并行开发    集成测试

总耗时: 7-8 小时 (节省 33-42%)
```

### 6.3 双人并行 (最优)

```
开发者 A: TODO-6.3 (8 小时)
开发者 B: TODO-6.5 (4 小时)
─────────────────────────────
总耗时: 8 小时 (墙钟时间)
人时：12 小时 (无节省，但交付更快)
```

---

## 7. 推荐行动方案

### 7.1 单人开发推荐

```
阶段 1 (0-2h):  TODO-6.3 模型 + 业务逻辑
阶段 2 (2-4h):  TODO-6.5 模型 + API
阶段 3 (4-6h):  TODO-6.3 API + 前端
阶段 4 (6-7h):  TODO-6.5 WebSocket + 前端
阶段 5 (7-8h):  统一集成测试
```

### 7.2 双人开发推荐

```
开发者 A:
├─ TODO-6.3 全流程 (8h)
│  └─ 负责：模型→服务→API→前端→测试

开发者 B:
├─ TODO-6.5 全流程 (4h)
└─ 协助集成测试 (1h)
```

### 7.3 关键检查点

| 时间点 | 检查项 | 决策点 |
|--------|--------|--------|
| **2h** | 模型设计完成 | 确认迁移无冲突 |
| **4h** | 核心逻辑完成 | 评估是否需要调整优先级 |
| **6h** | 前端开发完成 | 准备集成测试 |
| **8h** | 全部完成 | 验收 + 部署 |

---

## 8. 技术建议

### 8.1 代码组织

```
src/backend/
├── puzzles/              # TODO-6.3 残局挑战 (新建 App)
│   ├── models.py
│   ├── services.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── tests/
│
├── chat/                 # TODO-6.5 聊天系统 (新建 App)
│   ├── models.py
│   ├── consumers.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── tests/
│
└── games/                # 现有模块
    └── consumers.py      # 可能需要扩展支持聊天
```

### 8.2 WebSocket 架构建议

**方案 A: 独立 ChatConsumer** (推荐)
```python
# 优点：职责清晰，易于测试
# 缺点：需要管理两个连接

class ChatConsumer(AsyncWebsocketConsumer):
    """独立聊天 Consumer"""
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        await self.accept()
        await self.channel_layer.group_add(f'chat_{self.room_id}', self.channel_name)
```

**方案 B: 扩展 GameConsumer**
```python
# 优点：单连接，节省资源
# 缺点：Consumer 职责过重

class GameConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'move':
            await self.handle_move(data)
        elif data['type'] == 'chat':
            await self.handle_chat(data)  # 新增
```

### 8.3 数据库设计建议

```python
# puzzles/models.py
class Puzzle(models.Model):
    title = models.CharField(max_length=200)
    fen_start = models.TextField()  # 初始局面
    fen_solution = models.TextField()  # 正解局面
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES)
    move_count = models.IntegerField()  # 步数
    is_active = models.BooleanField(default=True)

class PuzzleAttempt(models.Model):
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    move_history = models.JSONField()
    is_solved = models.BooleanField(default=False)
    time_spent = models.IntegerField()  # 秒
    created_at = models.DateTimeField(auto_now_add=True)


# chat/models.py
class ChatMessage(models.Model):
    room = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
        ]
```

---

## 9. 结论

### 9.1 核心结论

✅ **TODO-6.3 和 TODO-6.5 可以安全并行开发**

- 任务独立性高，代码冲突风险低
- 共享资源可协调，无不可调和的依赖
- 预计节省时间 33-42% (串行 12h → 并行 7-8h)

### 9.2 关键建议

1. **数据库迁移串行执行** - 避免迁移冲突
2. **WebSocket 路由提前规划** - 避免路径冲突
3. **单人开发限制并发数** - 最多 2 个并行子任务
4. **双人开发完全并行** - 每人负责一个完整任务

### 9.3 下一步行动

1. 确认开发资源 (单人 or 双人)
2. 创建 Git 分支 (`feature/puzzle-challenge`, `feature/chat-system`)
3. 按本报告推荐的执行顺序开始开发
4. 完成每个阶段后进行代码审查

---

**报告完成时间**: 2026-03-05 20:00  
**下次更新**: 开发进度达到 50% 时
