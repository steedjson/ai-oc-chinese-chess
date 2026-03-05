# ♟️ 中国象棋项目

**创建时间**：2026-03-02  
**项目类型**：益智类游戏  
**目标用户**：单机用户 + 网络用户  
**项目状态**：🔄 开发中

---

## 🎯 项目简介与目标

中国象棋是一款经典的双人策略棋类游戏，本项目旨在打造一个功能完善的在线象棋平台，支持：

- **单机模式**：人机对战，多难度等级 AI
- **联网对战**：实时匹配、好友对战、房间系统
- **棋局管理**：保存、回放、分享棋谱
- **排名系统**：天梯积分、胜率统计

### 核心目标
1. 提供流畅的游戏体验（低延迟、高并发）
2. 实现准确的象棋规则引擎
3. 支持多种游戏模式（单机/联网/好友）
4. 完善的用户系统和社交功能

---

## 🛠️ 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12.6 | 编程语言 |
| Django | 5.x | Web 框架 |
| Django REST Framework | 最新版 | API 开发 |
| Django Channels | 最新版 | WebSocket 实时通信 |
| PostgreSQL | 15 | 主数据库 |
| Redis | 7 | 缓存 + 消息队列 |
| Stockfish | 16 | AI 引擎 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI 框架 |
| TypeScript | - | 类型安全 |
| Vite | - | 构建工具 |
| Zustand | - | 状态管理 |

### 部署
| 技术 | 用途 |
|------|------|
| Docker | 容器化 |
| Docker Compose | 本地开发环境 |

---

## ✅ 已完成功能清单

### 阶段 1-4：基础架构 ✅
- [x] 需求分析文档
- [x] 架构设计文档
- [x] 技术选型评估
- [x] 功能规划文档

### 阶段 5.1：用户认证系统 ✅
- [x] JWT Token 认证
- [x] 用户注册/登录 API
- [x] Token 刷新机制
- [x] 密码加密存储
- [x] 用户资料管理

### 阶段 5.2：游戏对局系统 ✅
- [x] FEN 格式解析与生成
- [x] 象棋规则引擎（7种棋子走法）
- [x] Game / GameMove 数据模型
- [x] 游戏 CRUD API
- [x] 走棋验证与执行
- [x] 游戏状态管理
- [x] WebSocket Consumer 基础框架

### 测试覆盖
| 模块 | 测试数 | 通过率 |
|------|--------|--------|
| FEN 服务 | 12 | 100% ✅ |
| 规则引擎 | 27 | 74% 🔄 |
| API 集成 | 10 | 30% 🔄 |

---

## ⏳ 待完成功能清单

### 阶段 5.2 续：游戏对局系统优化
- [ ] 将死/困毙检测完善
- [ ] 计时器服务实现
- [ ] WebSocket 异步数据库访问修复
- [ ] 游戏结束判定逻辑

### 阶段 5.3：AI 对弈系统 ⏳
- [ ] Stockfish 引擎集成
- [ ] 多难度等级配置
- [ ] AI 走棋接口
- [ ] 引擎池管理

### 阶段 5.4：匹配系统 ⏳
- [ ] 匹配队列实现
- [ ] ELO 评分算法
- [ ] 实时匹配逻辑
- [ ] 好友对战邀请

### 阶段 6+：高级功能
- [ ] 棋谱导出（PGN 格式）
- [ ] 中文记谱转换
- [ ] 残局挑战模式
- [ ] 观战功能
- [ ] 聊天系统

---

## 📁 项目目录结构

```
projects/chinese-chess/
├── README.md                    # 本文件（项目总览）
├── docs/                        # 项目文档
│   ├── README.md                # 文档索引
│   ├── requirements.md          # 需求文档
│   ├── architecture.md          # 架构设计
│   ├── tech-stack-evaluation.md # 技术选型
│   ├── DEVELOPMENT-CONSTRAINTS.md # 开发规范
│   ├── SHARED-CONTEXT.md        # 共享上下文
│   ├── SETUP-GUIDE.md           # 环境搭建指南
│   ├── BUGFIX-REPORT.md         # Bug 修复报告
│   ├── TDD-IMPLEMENTATION-SUMMARY.md # TDD 总结
│   └── features/                # 功能规划
│       ├── user-auth-plan.md
│       ├── game-core-plan.md
│       ├── ai-opponent-plan.md
│       └── matchmaking-plan.md
├── src/
│   └── backend/                 # Django 后端
│       ├── config/              # 项目配置
│       │   ├── settings.py
│       │   ├── urls.py
│       │   └── asgi.py
│       ├── authentication/      # 认证系统
│       ├── users/               # 用户系统
│       ├── games/               # 游戏系统
│       │   ├── models.py        # Game, GameMove
│       │   ├── engine.py        # 规则引擎
│       │   ├── fen_service.py   # FEN 服务
│       │   ├── serializers.py   # 序列化器
│       │   ├── views.py         # API 视图
│       │   ├── urls.py          # URL 路由
│       │   └── consumers.py     # WebSocket
│       ├── matchmaking/         # 匹配系统
│       ├── ai_engine/           # AI 引擎
│       ├── websocket/           # WebSocket 配置
│       └── common/              # 公共模块
└── tests/                       # 测试文件
    ├── unit/                    # 单元测试
    │   ├── games/
    │   ├── users/
    │   ├── ai_engine/
    │   └── matchmaking/
    └── integration/             # 集成测试
        ├── auth/
        └── games/
```

---

## 🚀 快速启动指南

### 环境要求
- Python ≥ 3.11
- PostgreSQL 15
- Redis 7

### 1. 克隆并进入项目
```bash
cd projects/chinese-chess/
```

### 2. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r src/backend/requirements.txt
```

### 4. 配置数据库
编辑 `src/backend/config/settings.py`：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chinese_chess',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. 运行迁移
```bash
cd src/backend
python manage.py migrate
```

### 6. 启动开发服务器
```bash
python manage.py runserver
```

### 7. 启动 WebSocket 服务（需要 Redis）
```bash
# 终端 1：启动 Daphne
python -m daphne -b 0.0.0.0 -p 8001 config.asgi:application

# 或使用 runserver（Channels 会自动处理）
python manage.py runserver
```

---

## 📊 项目进度

| 阶段 | 内容 | 状态 | 完成度 |
|------|------|------|--------|
| 阶段 1 | 需求分析 | ✅ 完成 | 100% |
| 阶段 2 | 架构设计 | ✅ 完成 | 100% |
| 阶段 3 | 技术选型 | ✅ 完成 | 100% |
| 阶段 4 | 功能规划 | ✅ 完成 | 100% |
| 阶段 5.1 | 用户认证系统 | ✅ 完成 | 100% |
| 阶段 5.2 | 游戏对局系统 | 🔄 进行中 | 85% |
| 阶段 5.3 | AI 对弈系统 | ⏳ 待开始 | 0% |
| 阶段 5.4 | 匹配系统 | ⏳ 待开始 | 0% |
| 阶段 6 | 前端开发 | ⏳ 待开始 | 0% |
| 阶段 7 | 部署上线 | ⏳ 待开始 | 0% |

---

## 🔗 相关资源

### 项目文档
- [需求文档](docs/requirements.md)
- [架构设计](docs/architecture.md)
- [技术选型](docs/tech-stack-evaluation.md)
- [开发规范](docs/DEVELOPMENT-CONSTRAINTS.md)
- [环境搭建](docs/SETUP-GUIDE.md)

### 工作区文档
- [Django 最佳实践](../../docs/django/README.md)
- [Agent 配置](../../docs/agents/README.md)
- [OpenClaw 配置](../../docs/openclaw/README.md)

### Skills
- `chess-ai/` - 象棋 AI 决策
- `game-state/` - 游戏状态管理
- `websocket-realtime/` - WebSocket 实时对战
- `game-framework/` - 游戏框架

---

## 👥 维护者

- **小屁孩**（御姐模式）

---

**最后更新**：2026-03-04  
**文档版本**：v1.0
