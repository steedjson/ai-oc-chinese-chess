# 中国象棋管理后台前端

基于 React + TypeScript + Ant Design 的后台管理系统。

## 技术栈

- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design 5.x
- **状态管理**: Zustand + React Query
- **HTTP 客户端**: Axios
- **路由**: React Router v6
- **构建工具**: Vite

## 功能模块

- ✅ 用户管理（列表、详情、状态管理）
- ✅ 游戏管理（对局记录、详情查看）
- ✅ 匹配管理（匹配记录、Elo 排行榜）
- ✅ AI 管理（对局记录、难度配置）
- ✅ 数据统计（仪表盘、概览数据）
- ✅ 系统设置

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173/admin/

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
src/
├── api/              # API 服务层
│   ├── index.ts      # Axios 实例配置
│   ├── auth.ts       # 认证 API
│   ├── users.ts      # 用户管理 API
│   ├── games.ts      # 游戏管理 API
│   ├── matchmaking.ts # 匹配管理 API
│   ├── ai.ts         # AI 管理 API
│   └── statistics.ts # 统计分析 API
├── components/       # 公共组件
│   └── Layout/       # 布局组件
├── pages/            # 页面组件
│   ├── Login/        # 登录页
│   ├── Dashboard/    # 仪表盘
│   ├── Users/        # 用户管理
│   ├── Games/        # 游戏管理
│   ├── Matchmaking/  # 匹配管理
│   ├── AI/           # AI 管理
│   └── Settings/     # 系统设置
├── stores/           # Zustand 状态
│   └── auth.ts       # 认证状态
├── types/            # TypeScript 类型定义
└── utils/            # 工具函数
```

## API 配置

开发环境下，API 请求会代理到 `http://localhost:8000`

在 `vite.config.ts` 中修改代理配置：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 认证

- 登录页面：`/admin/login`
- Token 存储在 localStorage
- Axios 拦截器自动添加 Authorization header

## 开发规范

- 使用 TypeScript 严格模式
- 组件采用函数式 + Hooks
- 统一使用 API 服务层
- 状态管理使用 Zustand
- 服务端状态使用 React Query
