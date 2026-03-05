# 中国象棋 - 前端用户端

基于 React 18 + TypeScript + Vite 构建的中国象棋前端应用。

## 🛠️ 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **状态管理**: Zustand
- **UI 组件库**: Ant Design 5
- **样式方案**: Tailwind CSS + CSS Modules
- **HTTP 客户端**: Axios + React Query
- **路由**: React Router v6
- **WebSocket**: Native WebSocket + 自定义封装
- **棋盘渲染**: 自定义 SVG + CSS Animation

## 📁 项目结构

```
src/frontend-user/
├── src/
│   ├── components/          # 组件
│   │   ├── common/          # 通用组件
│   │   ├── game/            # 游戏组件
│   │   │   ├── ChessBoard.tsx    # 棋盘组件
│   │   │   ├── ChessPiece.tsx    # 棋子组件
│   │   │   └── GameControls.tsx  # 游戏控制
│   │   ├── layout/          # 布局组件
│   │   │   ├── Header.tsx        # 头部导航
│   │   │   ├── Footer.tsx        # 页脚
│   │   │   └── MainLayout.tsx    # 主布局
│   │   └── matchmaking/     # 匹配组件
│   ├── pages/               # 页面
│   │   ├── HomePage.tsx          # 首页
│   │   ├── AIGamePage.tsx        # AI 对战
│   │   ├── MatchmakingPage.tsx   # 匹配对战
│   │   ├── ProfilePage.tsx       # 用户中心
│   │   └── LeaderboardPage.tsx   # 排行榜
│   ├── hooks/               # 自定义 Hooks
│   ├── stores/              # 状态管理 (Zustand)
│   │   ├── auth.store.ts         # 认证状态
│   │   ├── game.store.ts         # 游戏状态
│   │   ├── matchmaking.store.ts  # 匹配状态
│   │   └── settings.store.ts     # 设置状态
│   ├── services/            # API 服务
│   │   ├── api.ts                # HTTP 客户端
│   │   ├── auth.service.ts       # 认证服务
│   │   ├── game.service.ts       # 游戏服务
│   │   ├── ai.service.ts         # AI 服务
│   │   ├── matchmaking.service.ts # 匹配服务
│   │   ├── ranking.service.ts    # 排行榜服务
│   │   ├── user.service.ts       # 用户服务
│   │   └── websocket.service.ts  # WebSocket 服务
│   ├── styles/              # 样式
│   │   └── index.css             # 全局样式
│   ├── types/               # TypeScript 类型
│   │   └── index.ts              # 类型定义
│   ├── utils/               # 工具函数
│   ├── assets/              # 静态资源
│   ├── App.tsx              # 应用入口
│   └── main.tsx             # 渲染入口
├── public/                  # 公共静态资源
├── index.html               # HTML 模板
├── vite.config.ts           # Vite 配置
├── tailwind.config.js       # Tailwind 配置
├── tsconfig.json            # TypeScript 配置
└── package.json             # 依赖配置
```

## 🚀 快速开始

### 安装依赖

```bash
cd src/frontend-user
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 🔧 配置

### 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

主要配置项：

```env
# API 基础 URL
VITE_API_BASE_URL=/api/v1

# WebSocket 基础 URL
VITE_WS_BASE_URL=ws://localhost:8000/ws

# 环境
VITE_APP_ENV=development
```

### 代理配置

开发模式下，Vite 会自动代理 API 请求到后端：

- `/api/*` → `http://localhost:8000/api/*`
- `/ws/*` → `ws://localhost:8000/ws/*`

生产环境请修改 `.env` 中的配置。

## 📱 页面功能

### 首页 (/)
- 游戏入口
- 快速开始（AI 对战/匹配对战）
- 平台数据统计
- 公告/活动展示

### AI 对战 (/ai-game)
- 10 个难度等级选择
- SVG 棋盘渲染
- 走棋交互
- AI 走棋动画
- 游戏控制（悔棋/认输/和棋）
- 游戏结果展示

### 匹配对战 (/matchmaking)
- 加入匹配队列
- 匹配进度显示
- 对手信息
- 实时对战
- 游戏控制

### 用户中心 (/profile)
- 个人信息展示
- 战绩统计（胜率/对局数/Elo）
- 段位展示
- 对局历史

### 排行榜 (/leaderboard)
- Elo 排行榜
- 段位分布
- 搜索用户

## 🎨 主题

支持浅色/深色模式切换：

- 浅色模式：默认
- 深色模式：点击头部导航的主题切换按钮

## 🎯 核心特性

### 棋盘渲染
- 自定义 SVG 渲染，矢量图清晰
- CSS Animation 实现流畅走棋动画
- 支持选中高亮、合法走法提示
- 将军提示动画

### 状态管理
- Zustand 轻量状态管理
- 持久化存储（认证状态、设置）
- 模块化设计（auth/game/matchmaking/settings）

### API 集成
- Axios 统一 HTTP 客户端
- JWT Token 自动管理
- Token 过期自动刷新
- 请求/响应拦截器

### WebSocket 实时通信
- Native WebSocket 封装
- 自动重连机制（指数退避）
- 心跳保活（30 秒间隔）
- 断线状态恢复

## 📝 开发规范

### 命名规范
- 文件/目录：kebab-case（如 `chess-board.tsx`）
- 组件：PascalCase（如 `ChessBoard`）
- 变量/函数：camelCase（如 `isValidMove`）
- 类型/接口：PascalCase（如 `GameState`）

### 代码风格
- 使用 TypeScript 严格模式
- 使用函数组件 + Hooks
- 使用 Tailwind CSS 原子类
- 使用 Ant Design 组件库

### Git 提交规范
```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 🐛 常见问题

### 1. 样式不生效
确保 Tailwind CSS 已正确配置，检查 `tailwind.config.js` 中的 `content` 配置。

### 2. API 请求失败
检查 `.env` 配置，确保后端服务已启动。

### 3. WebSocket 连接失败
检查后端 WebSocket 服务是否正常运行，确认 Token 有效。

## 📄 许可证

MIT

## 👥 作者

中国象棋项目团队
