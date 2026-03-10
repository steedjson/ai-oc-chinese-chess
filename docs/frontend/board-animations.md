# 棋盘动画效果实现文档

**文档版本**: v1.0  
**创建时间**: 2026-03-06  
**作者**: OpenClaw 助手  
**状态**: ✅ 已完成

---

## 📋 概述

本文档描述中国象棋前端棋盘动画效果的完整实现，包括走棋动画、吃子动画、将军动画、胜负动画以及动画配置系统。

---

## 🎯 功能列表

| 功能 | 组件 | 状态 | 说明 |
|------|------|------|------|
| 走棋平滑移动 | `PieceMovement.tsx` | ✅ | 棋子从一个位置平滑移动到另一个位置 |
| 吃子特效 | `BoardAnimation.tsx` | ✅ | 吃子时播放爆炸和火花特效 |
| 将军提示 | `BoardAnimation.tsx` | ✅ | 将军时显示脉冲动画和文字提示 |
| 胜负庆祝 | `BoardAnimation.tsx` | ✅ | 游戏结束时显示彩带和结果消息 |
| 动画开关配置 | `BoardAnimation.tsx` | ✅ | 用户可自定义启用/禁用各类动画 |
| 最后一步标记 | `PieceMovement.tsx` | ✅ | 高亮显示最后一步的起点和终点 |
| 合法走法提示 | `PieceMovement.tsx` | ✅ | 显示可走位置的绿色圆圈提示 |
| 棋子选中高亮 | `PieceMovement.tsx` | ✅ | 选中棋子时显示蓝色光环 |

---

## 📁 文件结构

```
frontend/src/
├── components/
│   └── board/
│       ├── BoardAnimation.tsx      # 棋盘动画主组件
│       ├── BoardAnimation.css      # 棋盘动画样式
│       ├── PieceMovement.tsx       # 棋子移动组件
│       └── PieceMovement.css       # 棋子移动样式
└── styles/
    └── animations.css              # 全局动画样式（可选）

docs/frontend/
└── board-animations.md             # 本文档
```

---

## 🔧 组件详解

### 1. BoardAnimation.tsx - 棋盘动画主组件

#### 1.1 导出组件

| 组件名 | 用途 |
|--------|------|
| `BoardAnimationContainer` | 动画容器，包裹棋盘组件 |
| `CheckAnimation` | 将军动画 |
| `GameEndAnimation` | 游戏结束动画 |
| `CaptureAnimation` | 吃子动画 |
| `AnimationPanel` | 动画设置面板 |

#### 1.2 类型定义

```typescript
interface AnimationConfig {
  enabled: boolean;           // 是否启用所有动画
  moveAnimation: boolean;     // 是否启用走棋动画
  captureAnimation: boolean;  // 是否启用吃子动画
  checkAnimation: boolean;    // 是否启用将军动画
  gameEndAnimation: boolean;  // 是否启用胜负动画
  speedMultiplier: number;    // 动画速度倍率 (0.5-2.0)
}
```

#### 1.3 使用示例

```tsx
import { BoardAnimationContainer, CheckAnimation } from './board/BoardAnimation';

function ChessBoard() {
  const [animationConfig, setAnimationConfig] = useState({
    enabled: true,
    moveAnimation: true,
    captureAnimation: true,
    checkAnimation: true,
    gameEndAnimation: true,
    speedMultiplier: 1.0,
  });

  return (
    <BoardAnimationContainer
      animationConfig={animationConfig}
      onConfigChange={setAnimationConfig}
      checkConfig={{ isCheck: true, checkSide: 'red' }}
      gameEndConfig={{ isGameOver: false }}
      captureConfig={{ isCapturing: false }}
    >
      {/* 棋盘组件 */}
      <Board />
    </BoardAnimationContainer>
  );
}
```

---

### 2. PieceMovement.tsx - 棋子移动组件

#### 2.1 导出组件

| 组件名 | 用途 |
|--------|------|
| `PieceMovementContainer` | 移动容器，包裹棋盘组件 |
| `MovingPiece` | 移动中的棋子 |
| `LastMoveMarker` | 最后一步标记 |
| `LegalMovesHint` | 合法走法提示 |
| `PieceHighlight` | 棋子高亮效果 |

#### 2.2 自定义 Hook

```typescript
const {
  currentMove,    // 当前移动
  lastMove,       // 最后一步移动
  makeMove,       // 执行移动函数
  isMoving,       // 是否正在移动
  config,         // 配置
  setConfig,      // 更新配置
} = usePieceMovement();
```

#### 2.3 使用示例

```tsx
import { PieceMovementContainer, usePieceMovement } from './board/PieceMovement';

function GameBoard() {
  const { currentMove, lastMove, makeMove, config } = usePieceMovement();

  const handleMove = (from: string, to: string, piece: PieceData) => {
    makeMove(from, to, piece, isCapture);
  };

  return (
    <PieceMovementContainer
      currentMove={currentMove}
      lastMove={lastMove}
      config={config}
      cellSize={50}
      onMoveClick={handleMove}
    >
      {/* 棋盘组件 */}
      <Board />
    </PieceMovementContainer>
  );
}
```

---

## 🎨 动画效果详解

### 1. 走棋动画

**效果描述**: 棋子从起始位置平滑移动到目标位置

**实现方式**:
- 使用 CSS `transition` 实现平滑过渡
- 支持自定义动画时长和缓动函数
- 移动过程中棋子保持在最上层 (z-index: 50)

**配置项**:
```typescript
{
  duration: 300,      // 动画时长 (ms)
  easing: 'ease-in-out',  // 缓动函数
}
```

---

### 2. 吃子动画

**效果描述**: 吃子时播放爆炸和火花特效

**视觉效果**:
- 爆炸光圈扩散
- 8 个方向的火花飞溅
- 持续 800ms

**CSS 动画**:
```css
@keyframes captureExpand {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

@keyframes sparkFly {
  0% { transform: rotate(var(--rotation)) translateY(0); opacity: 1; }
  100% { transform: rotate(var(--rotation)) translateY(30px); opacity: 0; }
}
```

---

### 3. 将军动画

**效果描述**: 将军时显示醒目的提示动画

**视觉效果**:
- "将军!" 文字脉冲放大
- 文字发光效果
- 背景闪烁
- 持续 2000ms

**CSS 动画**:
```css
@keyframes checkPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.9; }
}

@keyframes textGlow {
  0% { text-shadow: 0 0 10px rgba(220, 38, 38, 0.8); }
  100% { text-shadow: 0 0 50px rgba(220, 38, 38, 0.4); }
}
```

---

### 4. 胜负动画

**效果描述**: 游戏结束时播放庆祝动画

**视觉效果**:
- 50 个彩带飘落 (仅胜利方)
- 结果消息卡片滑入
- 奖杯/握手图标跳动
- 彩带持续 5000ms

**CSS 动画**:
```css
@keyframes confettiFall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(600px) rotate(720deg); opacity: 0; }
}

@keyframes messageSlideIn {
  0% { transform: translateY(-50px) scale(0.8); opacity: 0; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}
```

---

### 5. 最后一步标记

**效果描述**: 高亮显示最后一步的起点和终点

**视觉效果**:
- 起点：蓝色虚线圆圈
- 终点：绿色虚线圆圈
- 脉冲动画

---

### 6. 合法走法提示

**效果描述**: 显示可走位置的绿色圆圈

**交互**:
- 点击圆圈可执行走棋
- Hover 时放大提示

---

## ⚙️ 配置系统

### 动画设置面板

**打开方式**: 点击棋盘右上角的 🎬 按钮

**可配置项**:

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| 启用动画 | Checkbox | true | 总开关 |
| 走棋动画 | Checkbox | true | 控制走棋平滑移动 |
| 吃子动画 | Checkbox | true | 控制吃子特效 |
| 将军动画 | Checkbox | true | 控制将军提示 |
| 胜负动画 | Checkbox | true | 控制游戏结束动画 |
| 动画速度 | Slider | 1.0x | 0.5x - 2.0x |

### 使用配置

```typescript
const defaultConfig: AnimationConfig = {
  enabled: true,
  moveAnimation: true,
  captureAnimation: true,
  checkAnimation: true,
  gameEndAnimation: true,
  speedMultiplier: 1.0,
};

// 通过 CSS 变量控制动画速度
<div style={{ '--animation-speed': config.speedMultiplier }}>
```

---

## 🎯 性能优化

### 1. CSS 变量

使用 CSS 变量实现动画速度的全局控制：

```css
.board-animation-container {
  --animation-speed: 1;
}

.check-pulse {
  animation: checkPulse calc(1s / var(--animation-speed)) ease-in-out infinite;
}
```

### 2. 硬件加速

使用 `transform` 和 `opacity` 触发 GPU 加速：

```css
.moving-piece {
  transform: translate(-50%, -50%);
  will-change: transform;
}
```

### 3. 动画禁用

当用户禁用动画时，直接不渲染动画组件：

```typescript
if (!config.enabled || !config.checkAnimation) return null;
```

---

## 📱 响应式设计

### 移动端适配

```css
@media (max-width: 768px) {
  .check-text {
    font-size: 32px;  /* 桌面端 48px */
  }

  .piece {
    width: 38px;      /* 桌面端 46px */
    height: 38px;
    font-size: 20px;  /* 桌面端 24px */
  }
}
```

### 深色模式支持

```css
@media (prefers-color-scheme: dark) {
  .animation-settings {
    background: rgba(31, 41, 55, 0.98);
  }

  .piece.red {
    background: linear-gradient(145deg, #ef4444 0%, #b91c1c 100%);
  }
}
```

---

## 🔗 集成指南

### 1. 与棋盘组件集成

```tsx
import { BoardAnimationContainer } from './board/BoardAnimation';
import { PieceMovementContainer } from './board/PieceMovement';

function ChessGame() {
  return (
    <BoardAnimationContainer
      checkConfig={{ isCheck, checkSide }}
      gameEndConfig={{ isGameOver, winner, winReason }}
    >
      <PieceMovementContainer
        currentMove={currentMove}
        lastMove={lastMove}
        legalMoves={legalMoves}
      >
        <Board />
      </PieceMovementContainer>
    </BoardAnimationContainer>
  );
}
```

### 2. 与游戏状态管理集成

```tsx
function GamePage() {
  const { gameState, makeMove } = useGameStore();
  const { currentMove, makeMove: animateMove } = usePieceMovement();

  const handleMove = async (from: string, to: string) => {
    // 1. 播放移动动画
    animateMove(from, to, piece, isCapture);
    
    // 2. 等待动画完成
    await sleep(300);
    
    // 3. 更新游戏状态
    await makeMove(from, to);
  };

  return <ChessGame />;
}
```

---

## 🧪 测试建议

### 单元测试

```typescript
describe('BoardAnimation', () => {
  it('should show check animation when isCheck is true', () => {
    render(<CheckAnimation isCheck={true} />);
    expect(screen.getByText('将军!')).toBeInTheDocument();
  });

  it('should hide check animation after 2000ms', async () => {
    render(<CheckAnimation isCheck={true} />);
    expect(screen.getByText('将军!')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('将军!')).not.toBeInTheDocument();
    }, { timeout: 2100 });
  });
});
```

### E2E 测试

```typescript
describe('Chess Board Animations', () => {
  it('should play move animation when piece is moved', async () => {
    await page.goto('/game/123');
    
    // 点击棋子
    await page.click('[data-position="e2"]');
    
    // 点击目标位置
    await page.click('[data-position="e4"]');
    
    // 验证移动动画
    const movingPiece = await page.$('.moving-piece');
    expect(movingPiece).not.toBeNull();
    
    // 等待动画完成
    await page.waitForSelector('.moving-piece', { state: 'detached' });
  });
});
```

---

## 📊 浏览器兼容性

| 浏览器 | 版本 | 支持情况 |
|--------|------|---------|
| Chrome | 90+ | ✅ 完全支持 |
| Firefox | 88+ | ✅ 完全支持 |
| Safari | 14+ | ✅ 完全支持 |
| Edge | 90+ | ✅ 完全支持 |
| 移动端 Safari | 14+ | ✅ 完全支持 |
| 移动端 Chrome | 90+ | ✅ 完全支持 |

**所需 CSS 特性**:
- CSS Custom Properties (变量)
- CSS Animations
- CSS Transitions
- CSS Gradients
- Flexbox

---

## 🐛 已知问题

| 问题 | 严重程度 | 状态 | 解决方案 |
|------|---------|------|---------|
| 快速连续走棋时动画可能重叠 | 低 | 待优化 | 添加动画队列 |
| 低端设备彩带动画可能卡顿 | 低 | 待优化 | 动态减少彩带数量 |

---

## 🚀 未来优化

### P1 高优先级

- [ ] 添加音效支持
- [ ] 实现动画队列，支持快速连续走棋
- [ ] 添加更多吃子特效样式

### P2 中优先级

- [ ] 实现棋子翻转动画（翻面效果）
- [ ] 添加悔棋动画
- [ ] 实现棋子被将军时的颤抖效果

### P3 低优先级

- [ ] 添加胜利/失败表情动画
- [ ] 实现棋子入场动画（新游戏开始）
- [ ] 添加特殊棋子（升变）动画

---

## 📝 更新日志

### v1.0 (2026-03-06)

- ✅ 实现走棋平滑移动动画
- ✅ 实现吃子爆炸特效
- ✅ 实现将军提示动画
- ✅ 实现游戏结束庆祝动画
- ✅ 实现动画配置面板
- ✅ 实现最后一步标记
- ✅ 实现合法走法提示
- ✅ 实现棋子选中高亮
- ✅ 响应式设计支持
- ✅ 深色模式支持

---

## 📚 相关文档

- [游戏对局系统功能规划](../features/game-core-plan.md)
- [前端架构设计](../architecture.md)
- [棋盘组件设计](./board-component-design.md) (待创建)

---

**最后更新**: 2026-03-06  
**维护者**: OpenClaw 助手
