# ♟️ 中国象棋项目文档库

**更新时间**：2026-03-03  
**项目状态**：🔄 开发中  
**维护者**：小屁孩（御姐模式）

---

## 📁 文档结构

```
projects/chinese-chess/docs/
├── README.md                    # 本文件（索引）
├── requirements.md              # 需求文档（阶段 1）
├── architecture.md              # 架构设计（阶段 2）
├── tech-stack-evaluation.md     # 技术选型（阶段 3）
├── DEVELOPMENT-CONSTRAINTS.md   # 开发约束规范
├── SHARED-CONTEXT.md            # 共享上下文
├── SETUP-GUIDE.md               # 开发环境搭建指南
├── BUGFIX-REPORT.md             # Bug 修复报告（2026-03-03）
├── features/                    # 功能规划文档
│   ├── user-auth-plan.md        # 用户认证系统
│   ├── game-core-plan.md        # 游戏对局系统
│   ├── ai-opponent-plan.md      # AI 对弈系统
│   └── matchmaking-plan.md      # 匹配系统
└── TDD-IMPLEMENTATION-SUMMARY.md # TDD 实现总结
```

---

## 📊 项目进度

| 阶段 | 内容 | 状态 | 文档 |
|------|------|------|------|
| 阶段 1 | 需求分析 | ✅ 完成 | requirements.md |
| 阶段 2 | 架构设计 | ✅ 完成 | architecture.md |
| 阶段 3 | 技术选型 | ✅ 完成 | tech-stack-evaluation.md |
| 阶段 4 | 功能规划 | ✅ 完成 | features/*.md |
| 阶段 5.1 | 用户认证系统 | ✅ 完成 | TDD 实现 |
| 阶段 5.2 | 游戏对局系统 | ✅ 完成 | TDD 实现 |
| 阶段 5.3 | AI 对弈系统 | ⏳ 待开始 | - |
| 阶段 5.4 | 匹配系统 | ⏳ 待开始 | - |

---

## 🎯 快速导航

### 需求文档
→ [requirements.md](requirements.md) - 项目背景、用户群体、功能列表

### 架构设计
→ [architecture.md](architecture.md) - 系统架构、技术架构、数据库设计

### 技术选型
→ [tech-stack-evaluation.md](tech-stack-evaluation.md) - 技术栈评估与决策

### 开发规范
→ [DEVELOPMENT-CONSTRAINTS.md](DEVELOPMENT-CONSTRAINTS.md) - 命名/API/数据库/安全规范

### 共享上下文
→ [SHARED-CONTEXT.md](SHARED-CONTEXT.md) - 已定义/待定义的 API 和数据库表

### 功能规划
- [用户认证系统](features/user-auth-plan.md)
- [游戏对局系统](features/game-core-plan.md)
- [AI 对弈系统](features/ai-opponent-plan.md)
- [匹配系统](features/matchmaking-plan.md)

### TDD 实现
→ [TDD-IMPLEMENTATION-SUMMARY.md](TDD-IMPLEMENTATION-SUMMARY.md) - 实现总结

### 环境搭建
→ [SETUP-GUIDE.md](SETUP-GUIDE.md) - 开发环境搭建指南

### Bug 修复
→ [BUGFIX-REPORT.md](BUGFIX-REPORT.md) - 后端联调问题修复报告

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **后端** | Django 5.x + DRF + Django Channels |
| **前端** | React 18 + TypeScript + Vite + Zustand |
| **数据库** | PostgreSQL 15 + Redis 7 |
| **AI 引擎** | Stockfish 16 |
| **部署** | Docker + Docker Compose |

---

## 📂 项目位置

```
~/.openclaw/workspace/
├── projects/chinese-chess/      # 项目根目录
│   ├── docs/                    # 项目文档（本目录）
│   ├── src/backend/             # Django 后端
│   ├── src/frontend-admin/      # 后台管理前端
│   ├── src/frontend-user/       # 用户端前端
│   └── tests/                   # 测试文件
└── skills/
    ├── chess-ai/                # 象棋 AI skill
    ├── game-state/              # 游戏状态 skill
    ├── websocket-realtime/      # WebSocket 实时对战 skill
    └── game-framework/          # 游戏框架 skill
```

---

## 🔗 相关资源

**工作区文档**（`~/.openclaw/workspace/docs/`）：
- [Django 文档](../../docs/django/README.md) - Django 最佳实践和版本指南
- [Agent 配置](../../docs/agents/README.md) - Agent 模型路由和配置
- [OpenClaw 配置](../../docs/openclaw/README.md) - OpenClaw 配置参考
- [模型路由](../../docs/models/README.md) - 模型选择和路由指南

---

**项目创建时间**：2026-03-02  
**文档更新时间**：2026-03-03  
**维护者**：小屁孩（御姐模式）
