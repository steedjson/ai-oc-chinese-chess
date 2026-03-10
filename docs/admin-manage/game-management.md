# 游戏管理功能文档

## 概述

游戏管理功能为中国象棋项目管理端提供完整的对局管理能力，包括游戏对局查看、一键中止、异常预警和流水追踪。

## 功能模块

### 1. 游戏对局管理界面

**位置**: `src/frontend-admin/src/pages/Games/index.tsx`

**功能特性**:
- ✅ 显示当前所有游戏对局列表
- ✅ 显示对局详细信息（玩家、步数、时间等）
- ✅ 支持搜索和过滤（按玩家名称、游戏 ID、状态）
- ✅ 分页显示
- ✅ 实时统计数据（总对局数、对局中、等待中、异常对局）

**筛选条件**:
- 状态筛选：等待中、对局中、已结束、已中止
- 异常筛选：仅显示异常对局
- 关键词搜索：玩家名称、游戏 ID

**页面布局**:
```
┌─────────────────────────────────────────┐
│  游戏管理 (Title)                        │
├─────────────────────────────────────────┤
│  [总对局数] [对局中] [等待中] [异常对局]  │
├─────────────────────────────────────────┤
│  ⚠️ 发现 X 个异常对局 [查看异常对局]      │
├─────────────────────────────────────────┤
│  [搜索框] [状态筛选] [异常筛选] [操作按钮]│
├─────────────────────────────────────────┤
│  游戏列表表格                            │
│  - 游戏 ID | 红方 | 黑方 | 状态 | ...    │
│  - [详情] [日志] [中止] [标记异常]        │
└─────────────────────────────────────────┘
```

### 2. 一键中止对局功能

**后端 API**: `src/backend/games/management_api.py`

**接口**: `POST /management/games/{id}/abort/`

**请求参数**:
```json
{
  "reason": "管理员强制中止"
}
```

**功能特性**:
- ✅ 管理员可以强制中止任意对局
- ✅ 中止后自动通知双方玩家（待实现 WebSocket 通知）
- ✅ 记录中止原因和操作日志
- ✅ 需要二次确认，防止误操作
- ✅ 仅超级管理员可用

**权限控制**:
- 仅 `is_superuser` 用户可以访问
- 前端显示权限提示

**中止流程**:
```
1. 用户点击"中止"按钮
2. 弹出确认对话框，输入中止原因
3. 确认后发送 API 请求
4. 后端更新游戏状态为"aborted"
5. 记录操作日志
6. 通知双方玩家（待实现）
7. 刷新列表显示
```

### 3. 异常预警系统

**后端服务**: `src/backend/games/services/anomaly_detector.py`

**异常类型**:

#### 3.1 超时对局 (timeout)
- **检测条件**: 对局时间超过 2 小时且状态仍为"对局中"
- **严重程度**: high
- **处理方式**: 自动标记，提醒管理员处理

#### 3.2 可疑走棋 (suspicious_moves)
- **检测条件**: 连续 5 次以上走棋时间小于 2 秒
- **严重程度**: high
- **可能原因**: 使用 AI 作弊
- **处理方式**: 标记为异常，人工审查

#### 3.3 长时间无操作 (idle)
- **检测条件**: 超过 30 分钟无走棋记录
- **严重程度**: medium
- **处理方式**: 提醒管理员关注

**API 接口**: `GET /management/games/anomalies/`

**响应格式**:
```json
{
  "data": [
    {
      "game_id": "xxx",
      "game": {
        "id": "xxx",
        "red_player": "player1",
        "black_player": "player2",
        "status": "playing",
        "started_at": "2026-03-07T10:00:00Z"
      },
      "anomaly_type": "timeout",
      "severity": "high",
      "description": "对局时间过长，已持续 2.5 小时",
      "details": {
        "duration_hours": 2.5,
        "threshold_hours": 2
      },
      "detected_at": "2026-03-07T12:30:00Z"
    }
  ],
  "total": 1
}
```

**前端展示**:
- 统计卡片显示异常对局数量
- 异常预警 Alert 提示
- 状态列显示异常标记
- 支持一键筛选异常对局

### 4. 对局流水追踪

**模型**: `src/backend/games/models/game_log.py`

**日志类型**:
- `create`: 创建对局
- `start`: 开始对局
- `move`: 走棋
- `abort`: 中止对局
- `auto_abort`: 自动中止
- `finish`: 结束对局
- `mark_abnormal`: 标记异常
- `unmark_abnormal`: 取消异常标记
- `join`: 加入对局
- `leave`: 离开对局
- `spectator_join`: 观战者加入
- `spectator_leave`: 观战者离开
- `chat_message`: 聊天消息
- `other`: 其他操作

**日志字段**:
- `game`: 关联的游戏对局
- `operator`: 操作者
- `action`: 操作类型
- `details`: 操作详情（JSON）
- `severity`: 严重程度（info/warning/error/critical）
- `created_at`: 操作时间
- `ip_address`: IP 地址（审计用）
- `user_agent`: 用户代理

**API 接口**: `GET /management/games/{id}/logs/`

**查询参数**:
- `page`: 页码
- `page_size`: 每页数量
- `action`: 按操作类型过滤
- `severity`: 按严重程度过滤

**前端展示**:
- 点击"日志"按钮查看对局操作历史
- 支持分页浏览
- 显示操作者、时间、IP 等详细信息
- 支持导出 CSV（待实现）

## 技术实现

### 后端技术栈

- **框架**: Django REST Framework
- **权限**: IsSuperAdmin（自定义权限类）
- **模型**: Game, GameLog
- **服务**: AnomalyDetector

### 前端技术栈

- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design
- **状态管理**: TanStack Query (React Query)
- **路由**: React Router

### 数据库设计

#### GameLog 模型
```python
class GameLog(models.Model):
    game = models.ForeignKey('games.Game', on_delete=models.CASCADE)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
```

**索引**:
- `(game, -created_at)`: 快速查询游戏日志
- `(operator, -created_at)`: 快速查询用户操作
- `(action, -created_at)`: 快速查询操作类型

## API 文档

### 游戏管理 API

#### 获取游戏列表
```
GET /management/games/
```

**参数**:
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）
- `search`: 搜索关键词
- `status`: 状态过滤
- `abnormal`: 是否仅显示异常对局

**响应**:
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### 获取对局详情
```
GET /management/games/{id}/
```

#### 中止对局
```
POST /management/games/{id}/abort/
```

**请求体**:
```json
{
  "reason": "中止原因"
}
```

#### 获取异常对局
```
GET /management/games/anomalies/
```

#### 标记对局为异常
```
POST /management/games/{id}/mark_abnormal/
```

**请求体**:
```json
{
  "reason": "标记原因"
}
```

#### 获取对局日志
```
GET /management/games/{id}/logs/
```

**参数**:
- `page`: 页码
- `page_size`: 每页数量
- `action`: 操作类型
- `severity`: 严重程度

## 配置说明

### 异常检测配置

在 `src/backend/games/services/anomaly_detector.py` 中配置：

```python
class AnomalyDetector:
    MAX_GAME_DURATION_HOURS = 2  # 最大对局时长
    SUSPICIOUS_MOVE_TIME_SECONDS = 2  # 可疑走棋时间
    MIN_SUSPICIOUS_MOVES = 5  # 最少可疑走棋次数
```

### 权限配置

仅超级管理员可访问游戏管理功能：

```python
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser
```

## 待办事项

- [ ] 实现 WebSocket 通知（中止对局时通知玩家）
- [ ] 实现日志导出 CSV 功能
- [ ] 实现列表导出 Excel 功能
- [ ] 添加更多异常检测规则（如：胜率异常波动）
- [ ] 添加对局回放功能
- [ ] 添加批量操作功能

## 测试指南

详见：`docs/testing/game-management-test-report.md`

## 更新日志

### v1.0.0 (2026-03-07)
- ✅ 初始版本发布
- ✅ 游戏对局管理界面
- ✅ 一键中止对局功能
- ✅ 异常预警系统
- ✅ 对局流水追踪
