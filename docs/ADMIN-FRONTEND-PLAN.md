# 后台管理前端开发计划

## 项目概述

为中国象棋游戏创建后台管理系统前端，用于管理员管理用户、游戏、匹配系统和 AI 配置。

## 技术栈

| 类别 | 技术选型 | 说明 |
|------|---------|------|
| 框架 | React 18 + TypeScript | 类型安全的组件开发 |
| UI 库 | Ant Design 5.x | 企业级 UI 组件库 |
| 状态管理 | Zustand + React Query | 轻量状态管理 + 服务端状态 |
| HTTP 客户端 | Axios | 请求拦截、错误处理 |
| 路由 | React Router v6 | 声明式路由 |
| 构建工具 | Vite | 快速开发和构建 |

## 项目结构

```
src/frontend-admin/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 服务层
│   │   ├── index.ts       # Axios 实例配置
│   │   ├── users.ts       # 用户管理 API
│   │   ├── games.ts       # 游戏管理 API
│   │   ├── matchmaking.ts # 匹配管理 API
│   │   ├── ai.ts          # AI 管理 API
│   │   └── statistics.ts  # 统计分析 API
│   ├── components/        # 公共组件
│   │   ├── Layout/        # 布局组件
│   │   ├── Table/         # 表格组件
│   │   └── Charts/        # 图表组件
│   ├── pages/             # 页面组件
│   │   ├── Login/         # 登录页
│   │   ├── Dashboard/     # 仪表盘
│   │   ├── Users/         # 用户管理
│   │   ├── Games/         # 游戏管理
│   │   ├── Matchmaking/   # 匹配管理
│   │   ├── AI/            # AI 管理
│   │   └── Settings/      # 系统设置
│   ├── stores/            # Zustand 状态
│   │   └── auth.ts        # 认证状态
│   ├── hooks/             # 自定义 Hooks
│   │   └── useAuth.ts     # 认证 Hook
│   ├── types/             # TypeScript 类型
│   │   ├── user.ts
│   │   ├── game.ts
│   │   └── index.ts
│   ├── utils/             # 工具函数
│   ├── App.tsx            # 应用入口
│   └── main.tsx           # 渲染入口
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 页面结构

```
/admin
├── /login          # 登录页
├── /dashboard      # 仪表盘（数据概览）
├── /users          # 用户管理
│   └── /users/:id  # 用户详情
├── /games          # 游戏管理
│   └── /games/:id  # 游戏详情
├── /matchmaking    # 匹配管理
├── /ai             # AI 管理
└── /settings       # 系统设置
```

## API 对接

后端 API 基础路径：`/api/v1/admin/`

### API 端点

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 用户管理 | `/users/` | GET | 获取用户列表 |
| 用户管理 | `/users/:id` | GET | 获取用户详情 |
| 用户管理 | `/users/:id/status` | PUT | 禁用/启用用户 |
| 游戏管理 | `/games/` | GET | 获取游戏列表 |
| 游戏管理 | `/games/:id` | GET | 获取游戏详情 |
| 匹配管理 | `/matchmaking/` | GET | 获取匹配记录 |
| 匹配管理 | `/matchmaking/ranking` | GET | Elo 排行榜 |
| AI 管理 | `/ai/games/` | GET | AI 对局记录 |
| AI 管理 | `/ai/config/` | GET/PUT | AI 难度配置 |
| 统计分析 | `/statistics/daily` | GET | 日活统计 |
| 统计分析 | `/statistics/monthly` | GET | 月活统计 |
| 统计分析 | `/statistics/users` | GET | 用户增长 |
| 统计分析 | `/statistics/game-time` | GET | 游戏时长 |

## 功能模块

### 1. 用户管理（优先级：高）
- [ ] 用户列表（分页、搜索、筛选）
- [ ] 用户详情查看
- [ ] 禁用/启用用户
- [ ] 用户数据统计

### 2. 游戏管理（优先级：高）
- [ ] 游戏记录列表（分页、筛选）
- [ ] 游戏详情查看
- [ ] 对局数据统计

### 3. 匹配系统管理（优先级：中）
- [ ] 匹配记录查询
- [ ] Elo 排行榜
- [ ] 匹配统计

### 4. AI 管理（优先级：中）
- [ ] AI 对局记录
- [ ] AI 难度配置
- [ ] AI 调优

### 5. 数据统计（优先级：中）
- [ ] 日活/月活统计
- [ ] 用户增长曲线
- [ ] 游戏时长统计

## 开发阶段

### 阶段一：项目初始化（当前）
- [x] 创建项目目录
- [ ] 初始化 Vite + React + TypeScript
- [ ] 安装依赖（Ant Design, Zustand, React Query, Axios, React Router）
- [ ] 配置项目结构

### 阶段二：基础架构
- [ ] 配置 Axios 实例和拦截器
- [ ] 创建 API 服务层
- [ ] 实现认证状态管理
- [ ] 创建布局组件

### 阶段三：核心页面
- [ ] 登录页面
- [ ] 仪表盘页面
- [ ] 用户管理页面
- [ ] 游戏管理页面

### 阶段四：高级功能
- [ ] 匹配管理页面
- [ ] AI 管理页面
- [ ] 系统设置页面
- [ ] 数据可视化图表

### 阶段五：测试和优化
- [ ] 功能测试
- [ ] 性能优化
- [ ] 文档完善

## 验证标准

| 检查项 | 验证方法 | 通过标准 |
|--------|---------|---------|
| 项目创建 | 检查目录 | 目录已创建 |
| 依赖安装 | npm install | 无错误 |
| 开发服务器 | npm run dev | 正常启动 |
| 页面访问 | 访问 localhost:5173 | 页面正常显示 |
| 登录功能 | 输入账号密码 | 登录成功 |

## 时间估算

- 阶段一：0.5 天
- 阶段二：1 天
- 阶段三：2 天
- 阶段四：1.5 天
- 阶段五：1 天

**总计：约 6 天**
