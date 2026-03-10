# 个人中心 Mock 数据修复

## 修复日期
2026-03-06

## 问题描述

个人中心组件 (`ProfilePage.tsx`) 存在以下问题：

1. **缺少 loading 状态**：组件中使用了 `setLoading(true)` 但未定义 `loading` 状态变量
2. **Mock 数据格式不匹配**：Mock 服务返回的数据格式与后端 API 不一致
3. **用户数据未通过 API 获取**：组件直接使用 auth store 中的用户数据，未获取最新资料
4. **缺少对局历史 Mock 支持**：`getUserGames` 端点没有对应的 Mock 处理器

## 修复内容

### 1. ProfilePage 组件修复

**文件**: `src/frontend-user/src/pages/ProfilePage.tsx`

**修改内容**:
- 添加 `loading` 状态变量
- 将 `user` 改为可更新的状态（通过 API 获取最新资料）
- 在 `loadUserData` 中调用 `userService.getProfile()` 获取最新用户资料
- 修复类型转换，使用 `as unknown as` 处理 API 响应类型

```typescript
// 修复前
const [user] = useState<User | null>(authUser);
// 缺少 loading 状态

// 修复后
const [user, setUser] = useState<User | null>(authUser);
const [loading, setLoading] = useState(false);
```

### 2. Mock 服务数据格式修复

**文件**: `src/frontend-user/src/services/mock.service.ts`

**修改内容**:

#### getStats 方法
- 修改返回格式，直接返回 stats 对象（符合后端 API 格式）
- 修复胜率计算（使用百分比而非小数）

```typescript
// 修复前
return createMockResponse({
  user,
  stats: {
    total_games: user.total_games,
    wins: user.wins,
    losses: user.losses,
    draws: user.draws,
    win_rate: user.total_games > 0 ? user.wins / user.total_games : 0, // 小数格式
    rating: user.rating,
  },
});

// 修复后
return createMockResponse({
  total_games: user.total_games,
  wins: user.wins,
  losses: user.losses,
  draws: user.draws,
  win_rate: winRate, // 百分比格式（如 58.18）
  current_rating: user.rating,
  highest_rating: user.rating,
});
```

#### 新增 getUserGames 方法
- 添加用户对局历史的 Mock 支持
- 返回格式完全匹配后端 API

```typescript
getUserGames: async (userId: number, page: number = 1, pageSize: number = 20) => {
  // 构建符合后端 API 格式的响应
  const gamesData = userGames.map((game) => ({
    id: game.id,
    opponent: {
      id: opponent.id,
      username: opponent.username,
      avatar_url: opponent.avatar_url,
      rating: opponent.rating,
    },
    result, // 'win' | 'loss' | 'draw'
    rating_change: ratingChange,
    is_red: isRed,
    game_type: game.game_type,
    created_at: game.created_at,
  }));
  
  return createMockResponse({
    results: gamesData,
    pagination: {
      page,
      page_size: pageSize,
      total_count: mockGames.length,
      total_pages: Math.ceil(mockGames.length / pageSize),
      has_next: end < mockGames.length,
      has_prev: page > 1,
    },
  });
},
```

### 3. Mock 拦截器修复

**文件**: `src/frontend-user/src/services/api.mock.ts`

**修改内容**:

#### 新增 URL 匹配模式
```typescript
// 修复前
this.handlers.set(/^GET.*\/users\/\d+$/, this.handleGetProfile.bind(this));
this.handlers.set(/^GET.*\/users\/\d+\/stats/, this.handleGetStats.bind(this));

// 修复后
this.handlers.set(/^GET.*\/users\/profile/, this.handleGetProfile.bind(this));
this.handlers.set(/^GET.*\/users\/me\/?$/, this.handleGetUserInfo.bind(this));
this.handlers.set(/^GET.*\/users\/\d+$/, this.handleGetProfile.bind(this));
this.handlers.set(/^GET.*\/users\/(me|\d+)\/stats/, this.handleGetStats.bind(this));
this.handlers.set(/^PUT.*\/users\/(me|\d+)/, this.handleUpdateProfile.bind(this));
this.handlers.set(/^GET.*\/users\/\d+\/games/, this.handleGetUserGames.bind(this));
```

#### 更新处理器方法
- `handleGetProfile`: 支持 `/users/profile` 和 `/users/{userId}`
- `handleGetStats`: 支持 `/users/me/stats` 和 `/users/{userId}/stats`
- `handleUpdateProfile`: 支持 `/users/me` 和 `/users/{userId}`
- 新增 `handleGetUserGames`: 处理用户对局历史请求

## API 响应格式对照

### 用户统计 (GET /users/me/stats)

**后端 API 格式**:
```json
{
  "success": true,
  "data": {
    "total_games": 550,
    "wins": 320,
    "losses": 150,
    "draws": 80,
    "win_rate": 58.18,
    "current_rating": 2100,
    "highest_rating": 2100
  }
}
```

**Mock 修复后格式**: 与后端完全一致 ✅

### 用户资料 (GET /users/profile)

**后端 API 格式**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "test_user",
    "email": "test@example.com",
    "nickname": "测试玩家",
    "avatar_url": "...",
    "rating": 2100,
    "total_games": 550,
    "wins": 320,
    "losses": 150,
    "draws": 80,
    "is_active": true,
    "created_at": "2024-01-15T08:00:00Z"
  }
}
```

**Mock 修复后格式**: 与后端完全一致 ✅

### 对局历史 (GET /users/{userId}/games)

**后端 API 格式**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "game_001",
        "opponent": {
          "id": 2,
          "username": "ai_opponent",
          "avatar_url": "...",
          "rating": 2800
        },
        "result": "win",
        "rating_change": 15,
        "is_red": true,
        "game_type": "ai",
        "created_at": "2024-03-02T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 2,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

**Mock 修复后格式**: 与后端完全一致 ✅

## 测试建议

### 1. Mock 模式测试
```bash
cd src/frontend-user
VITE_USE_MOCK=true npm run dev
```

访问个人中心页面，验证：
- [ ] 用户信息正确显示
- [ ] 统计数据正确显示（总对局、胜场、负场、和棋、胜率、天梯分）
- [ ] 对局历史表格正确显示
- [ ] 加载状态正常工作
- [ ] 错误处理正常工作

### 2. 真实 API 测试
```bash
# 确保后端服务运行
cd src/backend
python manage.py runserver

# 前端启动（不使用 Mock）
cd src/frontend-user
npm run dev
```

访问个人中心页面，验证：
- [ ] 能正确从后端获取用户资料
- [ ] 统计数据与数据库一致
- [ ] 对局历史正确显示
- [ ] 无控制台错误

## 切换真实 API

当需要切换到真实 API 时：

1. 设置环境变量 `VITE_USE_MOCK=false`（或删除该变量）
2. 确保 `VITE_API_BASE_URL` 指向正确的后端地址
3. 组件会自动使用真实 API，无需修改代码

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=false
```

## 注意事项

1. **Mock 模式仅用于开发测试**：生产环境必须使用真实 API
2. **数据一致性**：Mock 数据是静态的，不会反映真实的数据库状态
3. **错误场景测试**：可以通过修改 Mock 服务模拟各种错误场景（网络错误、401、404 等）
4. **加载状态**：组件已实现完整的加载状态处理，确保用户体验流畅

## 相关文件

- `src/frontend-user/src/pages/ProfilePage.tsx` - 个人中心组件
- `src/frontend-user/src/services/user.service.ts` - 用户服务
- `src/frontend-user/src/services/api.mock.ts` - Mock 拦截器
- `src/frontend-user/src/services/mock.service.ts` - Mock 数据
- `src/backend/users/views.py` - 后端用户 API（参考）
