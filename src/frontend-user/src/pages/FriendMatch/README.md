# 好友对战前端实现

## 概述

好友对战功能的前端实现，支持创建房间、加入房间、房间状态显示和分享功能。

## 功能特性

### 1. 创建房间页面 (`CreateRoom.tsx`)

- **路径**: `/games/friend/create/`
- **功能**:
  - 房间配置表单（时间控制、是否计分）
  - 创建房间按钮
  - 生成房间号和邀请链接
  - 自动复制邀请信息到剪贴板
  - 显示房间状态和分享选项

### 2. 加入房间页面 (`JoinRoom.tsx`)

- **路径**: `/games/friend/join/`
- **功能**:
  - 输入房间号表单
  - 加入房间按钮
  - 支持 URL 参数直接加入（`/friend/join?room=CHESS12345`）
  - 房间详情预览
  - 错误提示（房间不存在、已过期等）

### 3. 房间状态组件 (`RoomStatus.tsx`)

- **位置**: `src/components/friend/RoomStatus.tsx`
- **功能**:
  - 显示房间状态（等待中/对局中/已结束/已过期）
  - 显示房主和加入者
  - 倒计时显示（过期时间）
  - 分享按钮（复制链接、分享信息）
  - 操作按钮（加入房间、开始游戏、进入对局）

### 4. 分享工具 (`share.ts`)

- **位置**: `src/utils/share.ts`
- **功能**:
  - 复制链接到剪贴板（支持 HTTPS 和 HTTP 环境）
  - 生成分享文本
  - 生成分享图片（Canvas）
  - 社交媒体分享（微信、微博、QQ、Twitter）
  - 系统分享 API（如果支持）
  - 生成二维码（可选）

## API 端点

前端调用以下后端 API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/games/friend/create/` | POST | 创建房间 |
| `/api/games/friend/join/` | POST | 加入房间 |
| `/api/games/friend/rooms/{room_code}/` | GET | 获取房间详情 |
| `/api/games/friend/my-rooms/` | GET | 我的房间列表 |
| `/api/games/friend/active-rooms/` | GET | 活跃房间列表 |

## 文件结构

```
src/frontend-user/src/
├── pages/
│   └── FriendMatch/
│       ├── CreateRoom.tsx          # 创建房间页面
│       ├── JoinRoom.tsx            # 加入房间页面
│       ├── __tests__/
│       │   ├── CreateRoom.test.tsx
│       │   └── JoinRoom.test.tsx
│       └── README.md               # 本文档
├── components/
│   └── friend/
│       ├── RoomStatus.tsx          # 房间状态组件
│       ├── index.ts
│       └── __tests__/
│           └── RoomStatus.test.tsx
├── services/
│   ├── friend.service.ts           # 好友对战服务
│   └── __tests__/
│       └── friend.service.test.ts
├── utils/
│   ├── share.ts                    # 分享工具
│   └── __tests__/
│       └── share.test.ts
└── types/
    └── friend.ts                   # 类型定义
```

## 使用示例

### 创建房间

```tsx
import { friendService } from '@/services';

const result = await friendService.createRoom({
  time_control: 600,  // 10 分钟
  is_rated: false,
});

if (result.success && result.data) {
  console.log('房间号:', result.data.room_code);
  console.log('邀请链接:', result.data.invite_link);
}
```

### 加入房间

```tsx
import { friendService } from '@/services';

const result = await friendService.joinRoom('CHESS12345');

if (result.success && result.data) {
  console.log('加入成功！');
  console.log('游戏 ID:', result.data.game_id);
  console.log('你的颜色:', result.data.your_color);
}
```

### 分享房间

```tsx
import { copyToClipboard, generateShareText } from '@/utils/share';

const shareText = generateShareText('CHESS12345', 'https://example.com/join/CHESS12345');
await copyToClipboard(shareText);
```

## 测试

运行测试：

```bash
cd src/frontend-user
npm test -- friend
```

测试覆盖：

- ✅ 创建房间页面组件
- ✅ 加入房间页面组件
- ✅ 房间状态组件
- ✅ 好友对战服务
- ✅ 分享工具函数

## 验收标准

- [x] 可以创建好友对战房间
- [x] 房间号唯一且易读（如 CHESS2A3B5）
- [x] 可以通过房间号加入房间
- [x] 可以通过链接直接加入（URL 参数）
- [x] 房间状态正确显示
- [x] 分享功能可用
- [x] 代码有测试覆盖

## 技术栈

- React 18 + TypeScript
- Ant Design 5.x
- React Router 6.x
- Zustand (状态管理)
- Axios (HTTP 客户端)
- Vitest (测试框架)

## 注意事项

1. **登录验证**: 所有操作都需要用户登录
2. **房间号格式**: 自动转换为大写（CHESS + 5 位字母数字）
3. **过期时间**: 房间 24 小时后过期
4. **分享功能**: 优先使用系统分享 API，降级到复制链接
5. **错误处理**: 所有 API 调用都有错误提示

## 后续优化

- [ ] 添加二维码生成（使用 qrcode 库）
- [ ] 添加房间列表页面
- [ ] 添加房间历史记录
- [ ] 优化分享图片样式
- [ ] 添加房间密码功能
- [ ] 添加观战功能
