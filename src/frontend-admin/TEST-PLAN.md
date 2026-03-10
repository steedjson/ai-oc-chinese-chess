# 前端测试覆盖率提升计划

## 任务信息
- **任务 ID**: OCW-CORE-011
- **目标**: 提升前端测试覆盖率到 80%
- **启动时间**: 2026-03-08T21:00
- **项目**: projects/chinese-chess/src/frontend-admin

## 当前状态分析

### 项目结构
- **框架**: React 19 + TypeScript + Vite
- **状态管理**: Zustand (带 persist 中间件)
- **数据获取**: TanStack React Query
- **UI 库**: Ant Design 6
- **路由**: React Router 7
- **HTTP 客户端**: Axios

### 源代码文件清单 (22 个文件)

#### 核心文件 (3 个)
1. `src/App.tsx` - 主应用组件，路由配置
2. `src/main.tsx` - 入口文件
3. `src/types/index.ts` - TypeScript 类型定义

#### API 层 (7 个)
4. `src/api/index.ts` - Axios 客户端配置
5. `src/api/auth.ts` - 认证 API
6. `src/api/users.ts` - 用户管理 API
7. `src/api/games.ts` - 游戏管理 API
8. `src/api/statistics.ts` - 统计数据 API
9. `src/api/ai.ts` - AI 管理 API
10. `src/api/matchmaking.ts` - 匹配管理 API

#### Store (1 个)
11. `src/stores/auth.ts` - 认证状态管理 (Zustand)

#### Hooks (1 个)
12. `src/hooks/useHasPermission.ts` - 权限检查 Hook

#### Components (2 个)
13. `src/components/Layout/index.tsx` - 主布局组件
14. `src/components/Charts/TrendChart.tsx` - 趋势图表
15. `src/components/Charts/DistributionChart.tsx` - 分布图表

#### Pages (7 个)
16. `src/pages/Login/index.tsx` - 登录页
17. `src/pages/Dashboard/index.tsx` - 仪表盘
18. `src/pages/Users/index.tsx` - 用户管理
19. `src/pages/Games/index.tsx` - 游戏管理
20. `src/pages/Matchmaking/index.tsx` - 匹配管理
21. `src/pages/AI/index.tsx` - AI 管理
22. `src/pages/Settings/index.tsx` - 系统设置

### 当前测试覆盖率
- **测试文件数**: 0
- **覆盖率**: 0%

## 测试策略

### 测试工具选型
- **测试框架**: Vitest (与 Vite 原生集成)
- **渲染测试**: @testing-library/react
- **Mock 工具**: Vitest 内置 mock + MSW (API Mock)
- **覆盖率工具**: Vitest coverage (c8/v8)

### 测试分层

#### 第一层：单元测试 (Unit Tests) - 优先级最高
**目标文件**:
- `src/stores/auth.ts` - 测试状态管理逻辑
- `src/hooks/useHasPermission.ts` - 测试权限检查逻辑
- `src/api/*.ts` - 测试 API 调用

**预计覆盖率贡献**: 30%

#### 第二层：组件测试 (Component Tests) - 优先级高
**目标文件**:
- `src/pages/Login/index.tsx` - 测试表单交互
- `src/components/Layout/index.tsx` - 测试布局和菜单
- `src/components/Charts/*.tsx` - 测试图表渲染

**预计覆盖率贡献**: 35%

#### 第三层：页面测试 (Page Tests) - 优先级中
**目标文件**:
- `src/pages/Dashboard/index.tsx` - 测试数据展示
- 其他 Pages - 测试基本渲染和交互

**预计覆盖率贡献**: 25%

#### 第四层：集成测试 (Integration Tests) - 优先级低
**目标**:
- `src/App.tsx` - 测试路由和认证守卫

**预计覆盖率贡献**: 10%

## 实施步骤

### 阶段 1：测试基础设施搭建 (1-2 小时)
1. 安装测试依赖
2. 配置 Vitest
3. 配置测试工具链
4. 创建测试工具函数

### 阶段 2：核心逻辑测试 (2-3 小时)
1. 测试 auth store
2. 测试 useHasPermission hook
3. 测试 API 客户端

### 阶段 3：组件测试 (3-4 小时)
1. 测试 Login 页面
2. 测试 Layout 组件
3. 测试图表组件

### 阶段 4：页面测试 (2-3 小时)
1. 测试 Dashboard 页面
2. 测试其他页面基本功能

### 阶段 5：集成测试和优化 (1-2 小时)
1. 测试 App 路由
2. 优化测试覆盖率
3. 生成覆盖率报告

## 验收标准

### 覆盖率要求
- **总体覆盖率**: ≥80%
- **分支覆盖率**: ≥75%
- **函数覆盖率**: ≥80%
- **行覆盖率**: ≥80%

### 测试质量要求
- 所有测试独立运行
- 无测试依赖外部服务
- 测试执行时间 < 30 秒
- CI 友好配置

## 风险与缓解

### 风险 1: Zustand persist 中间件测试困难
**缓解**: Mock localStorage 和 persist 中间件

### 风险 2: React Query 测试复杂
**缓解**: 使用 QueryClientProvider 包装测试组件

### 风险 3: Ant Design 组件 Mock 复杂
**缓解**: 使用 @testing-library/react 的推荐方式

## 时间估算
- **总时间**: 8-12 小时
- **测试文件数**: 约 15-20 个
- **测试用例数**: 约 80-100 个

## 依赖安装命令
```bash
cd /Users/changsailong/.openclaw/workspace/projects/chinese-chess/src/frontend-admin
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/coverage-v8 happy-dom
```

## 配置文件
需要创建:
- `vitest.config.ts`
- `src/test/setup.ts`
- 更新 `package.json` scripts
