# 中国象棋管理端架构设计文档

**版本**: 1.0.0  
**创建日期**: 2026-03-06  
**最后更新**: 2026-03-06  
**状态**: ✅ 阶段 1 完成

---

## 1. 项目概述

### 1.1 项目背景

中国象棋管理端是为平台管理员提供的后台管理系统，用于管理用户、游戏对局、AI 引擎、匹配系统等核心功能。

### 1.2 设计目标

- **高效管理**: 提供直观、高效的管理界面
- **权限控制**: 基于角色的访问控制 (RBAC)
- **实时监控**: 实时数据展示和监控能力
- **可扩展性**: 模块化设计，便于功能扩展

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **框架** | React | 19.2.0 | 前端核心框架 |
| **语言** | TypeScript | 5.9.3 | 类型安全 |
| **UI 库** | Ant Design | 6.3.1 | 企业级 UI 组件库 |
| **状态管理** | Zustand | 5.0.11 | 轻量级状态管理 |
| **服务端状态** | React Query | 5.90.21 | 数据获取与缓存 |
| **路由** | React Router | 7.13.1 | 客户端路由 |
| **HTTP 客户端** | Axios | 1.13.6 | API 请求 |
| **图表** | Recharts | 3.7.0 | 数据可视化 |
| **构建工具** | Vite | 7.3.1 | 快速构建 |

### 2.2 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                      表现层 (Pages)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │Dashboard│ │  Users  │ │  Games  │ │   AI    │ │Settings│ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    组件层 (Components)                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │
│  │   Layout        │ │    Charts       │ │   Common       │ │
│  │  (Header/Sider) │ │  (Trend/Dist)   │ │   Components   │ │
│  └─────────────────┘ └─────────────────┘ └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     状态层 (Stores)                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │
│  │   Auth Store    │ │    UI Store     │ │   App Store    │ │
│  │  (Zustand)      │ │   (Zustand)     │ │   (Zustand)    │ │
│  └─────────────────┘ └─────────────────┘ └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    服务层 (API Services)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │  Auth   │ │  Users  │ │  Games  │ │   AI    │ │  Stats │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      类型层 (Types)                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  User, Game, Matchmaking, AI, Statistics, API Response  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 项目结构

```
projects/chinese-chess/src/frontend-admin/
├── public/                     # 静态资源
│   └── favicon.ico
├── src/
│   ├── api/                    # API 服务层
│   │   ├── index.ts           # Axios 实例配置（拦截器）
│   │   ├── auth.ts            # 认证 API
│   │   ├── users.ts           # 用户管理 API
│   │   ├── games.ts           # 游戏管理 API
│   │   ├── matchmaking.ts     # 匹配管理 API
│   │   ├── ai.ts              # AI 管理 API
│   │   └── statistics.ts      # 统计分析 API
│   ├── components/             # 公共组件
│   │   ├── Layout/            # 布局组件
│   │   │   └── index.tsx      # 主布局（Header + Sider + Content）
│   │   └── Charts/            # 图表组件
│   │       ├── TrendChart.tsx # 趋势图
│   │       └── DistributionChart.tsx # 分布图
│   ├── hooks/                  # 自定义 Hooks
│   │   └── useHasPermission.ts # 权限检查 Hook
│   ├── pages/                  # 页面组件
│   │   ├── Login/             # 登录页
│   │   │   └── index.tsx
│   │   ├── Dashboard/         # 仪表盘
│   │   │   └── index.tsx
│   │   ├── Users/             # 用户管理
│   │   │   └── index.tsx
│   │   ├── Games/             # 游戏管理
│   │   │   └── index.tsx
│   │   ├── Matchmaking/       # 匹配管理
│   │   │   └── index.tsx
│   │   ├── AI/                # AI 管理
│   │   │   └── index.tsx
│   │   └── Settings/          # 系统设置
│   │       └── index.tsx
│   ├── stores/                 # Zustand 状态管理
│   │   └── auth.ts            # 认证状态
│   ├── types/                  # TypeScript 类型定义
│   │   └── index.ts           # 所有类型定义
│   ├── assets/                 # 静态资源
│   │   └── react.svg
│   ├── App.tsx                 # 应用入口（路由配置）
│   ├── App.css                 # 应用样式
│   ├── main.tsx                # React 入口
│   └── index.css               # 全局样式
├── index.html                  # HTML 模板
├── package.json                # 依赖配置
├── tsconfig.json               # TypeScript 配置
├── tsconfig.app.json          # 应用 TS 配置
├── tsconfig.node.json         # Node TS 配置
├── vite.config.ts             # Vite 配置
├── eslint.config.js           # ESLint 配置
└── README.md                   # 项目说明
```

---

## 4. 路由设计

### 4.1 路由表

| 路径 | 组件 | 权限 | 说明 |
|------|------|------|------|
| `/admin/login` | LoginPage | 公开 | 管理员登录 |
| `/admin` | AdminLayout | 认证 | 管理后台布局 |
| `/admin/dashboard` | Dashboard | 认证 | 仪表盘（默认首页） |
| `/admin/users` | UsersPage | 认证 | 用户管理 |
| `/admin/games` | GamesPage | 认证 | 游戏管理 |
| `/admin/matchmaking` | MatchmakingPage | 认证 | 匹配管理 |
| `/admin/ai` | AIPage | 认证 | AI 管理 |
| `/admin/settings` | SettingsPage | super_admin | 系统设置 |

### 4.2 路由守卫

```typescript
// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <>{children}</>;
};
```

---

## 5. 权限模型

### 5.1 角色定义

| 角色 | 标识 | 权限说明 |
|------|------|----------|
| **超级管理员** | `super_admin` | 全部权限，包括系统设置 |
| **运维人员** | `ops` | 日常管理权限，不包括系统设置 |

### 5.2 权限检查

```typescript
// 权限检查 Hook
export const useHasPermission = () => {
  const { user } = useAuthStore();
  
  const isSuperAdmin = user?.role === 'super_admin';
  const isOps = user?.role === 'ops';

  return {
    isSuperAdmin,
    isOps,
    role: user?.role
  };
};
```

### 5.3 权限矩阵

| 功能 | super_admin | ops |
|------|-------------|-----|
| 仪表盘 | ✅ | ✅ |
| 用户管理 | ✅ | ✅ |
| 游戏管理 | ✅ | ✅ |
| 匹配管理 | ✅ | ✅ |
| AI 管理 | ✅ | ✅ |
| 系统设置 | ✅ | ❌ |
| 删除用户 | ✅ | ❌ |
| 中止游戏 | ✅ | ❌ |

---

## 6. API 设计

### 6.1 基础配置

- **Base URL**: `/api/v1/admin`
- **认证方式**: Bearer Token
- **超时时间**: 30 秒

### 6.2 请求拦截器

```typescript
// 自动添加 Authorization header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 6.3 响应拦截器

```typescript
// 统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);
```

### 6.4 API 模块

| 模块 | 文件 | 主要接口 |
|------|------|----------|
| 认证 | `auth.ts` | `login()` |
| 用户 | `users.ts` | `getList()`, `updateStatus()`, `delete()` |
| 游戏 | `games.ts` | `getList()`, `abortGame()`, `clearExpiredWaiting()` |
| 匹配 | `matchmaking.ts` | `getRecords()`, `getEloRanking()` |
| AI | `ai.ts` | `getConfig()`, `updateConfig()`, `getEngineParams()` |
| 统计 | `statistics.ts` | `getDashboard()`, `getUserGrowth()` |

---

## 7. 状态管理

### 7.1 认证状态 (Auth Store)

```typescript
interface AuthState {
  token: string | null;
  user: {
    id: string;
    username: string;
    role: UserRole;
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}
```

### 7.2 持久化策略

- Token 和用户信息持久化到 localStorage
- 使用 Zustand 的 `persist` 中间件
- 登出时自动清除持久化数据

---

## 8. 组件设计

### 8.1 布局组件 (AdminLayout)

**功能**:
- 侧边栏导航（可折叠）
- 顶部 Header（用户信息、退出登录）
- 面包屑导航
- 响应式设计

**特性**:
- 暗色侧边栏主题
- 毛玻璃效果 Header
- 响应式断点处理
- 权限控制的菜单项

### 8.2 图表组件

**TrendChart** - 趋势图
- 展示用户增长趋势
- 支持自定义颜色

**DistributionChart** - 分布图
- 展示数据分布（饼图）
- 支持多数据系列

---

## 9. 安全设计

### 9.1 认证安全

- JWT Token 认证
- Token 存储于 localStorage
- 401 自动跳转登录
- 登录失败错误提示

### 9.2 授权安全

- 基于角色的访问控制
- 前端路由守卫
- 操作按钮权限控制
- API 请求携带 Token

### 9.3 数据安全

- 所有用户输入验证
- API 响应统一处理
- 敏感操作二次确认
- 错误信息不泄露敏感数据

---

## 10. 性能优化

### 10.1 构建优化

- Vite 快速构建
- 代码分割（路由懒加载）
- Tree Shaking
- Sourcemap 生成（开发环境）

### 10.2 运行时优化

- React Query 缓存策略
- 数据预取
- 组件按需渲染
- 防抖/节流处理

### 10.3 网络优化

- Axios 请求合并
- 请求取消（未使用）
- 响应数据缓存
- 代理配置（开发环境）

---

## 11. 开发规范

### 11.1 代码规范

- TypeScript 严格模式
- 函数式组件 + Hooks
- 统一使用 API 服务层
- 状态管理使用 Zustand
- 服务端状态使用 React Query

### 11.2 文件命名

- 组件文件：`PascalCase.tsx`
- 工具文件：`camelCase.ts`
- 类型文件：`index.ts`（统一导出）
- 样式文件：与组件同名

### 11.3 提交规范

```
feat: 新功能
fix: Bug 修复
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

---

## 12. 部署配置

### 12.1 开发环境

```bash
npm run dev
```
- 端口：5173
- API 代理：http://localhost:8000

### 12.2 生产环境

```bash
npm run build
npm run preview
```
- 输出目录：`dist/`
- Base 路径：`/admin/`

### 12.3 环境变量

```bash
# .env.development
VITE_API_BASE_URL=/api/v1/admin

# .env.production
VITE_API_BASE_URL=https://api.example.com/v1/admin
```

---

## 13. 未来扩展

### 13.1 计划功能

- [ ] 操作日志审计
- [ ] 数据导出功能
- [ ] 批量操作支持
- [ ] 实时 WebSocket 通知
- [ ] 主题切换（深色模式）
- [ ] 国际化支持

### 13.2 技术升级

- [ ] 引入 E2E 测试（Playwright）
- [ ] 组件单元测试（Vitest）
- [ ] 性能监控（Sentry）
- [ ] CI/CD 自动化

---

## 附录

### A. 依赖版本

```json
{
  "react": "^19.2.0",
  "antd": "^6.3.1",
  "zustand": "^5.0.11",
  "@tanstack/react-query": "^5.90.21",
  "react-router-dom": "^7.13.1",
  "axios": "^1.13.6",
  "recharts": "^3.7.0",
  "vite": "^7.3.1",
  "typescript": "~5.9.3"
}
```

### B. 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

---

**文档结束**
