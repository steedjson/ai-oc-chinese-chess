# 棋盘动画组件使用示例

本文档提供棋盘动画组件的实际使用示例，帮助开发者快速集成。

---

## 📦 基础使用

### 1. 最简单的集成

```tsx
import React, { useState } from 'react';
import { BoardAnimationContainer } from './board/BoardAnimation';
import { PieceMovementContainer } from './board/PieceMovement';
import { Board } from './board/Board';

function ChessGame() {
  const [fen, setFen] = useState('rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1');

  return (
    <BoardAnimationContainer>
      <PieceMovementContainer>
        <Board fen={fen} />
      </PieceMovementContainer>
    </BoardAnimationContainer>
  );
}
```

---

## 🎮 完整游戏示例

### 2. 带完整动画效果的游戏页面

```tsx
import React, { useState, useCallback } from 'react';
import {
  BoardAnimationContainer,
  PieceMovementContainer,
  usePieceMovement,
  type PieceData,
} from './board';
import { Board } from './board/Board';
import { useGameStore } from '@/stores/gameStore';

function GamePage() {
  // 游戏状态
  const { gameState, makeMove: gameMakeMove } = useGameStore();
  
  // 动画状态
  const {
    currentMove,
    lastMove,
    makeMove: animateMove,
    isMoving,
    config,
    setConfig,
  } = usePieceMovement();

  // 选中状态
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [legalMoves, setLegalMoves] = useState<string[]>([]);

  // 处理棋子点击
  const handlePieceClick = useCallback((position: string) => {
    if (selectedPosition === position) {
      // 取消选中
      setSelectedPosition(null);
      setLegalMoves([]);
      return;
    }

    if (selectedPosition && legalMoves.includes(position)) {
      // 执行走棋
      const piece = gameState.board.getPiece(selectedPosition);
      const isCapture = gameState.board.hasPiece(position);
      
      // 播放动画
      animateMove(selectedPosition, position, piece, isCapture);
      
      // 更新游戏状态（等待动画完成）
      setTimeout(() => {
        gameMakeMove(selectedPosition, position);
        setSelectedPosition(null);
        setLegalMoves([]);
      }, config.duration);
    } else {
      // 选中棋子
      setSelectedPosition(position);
      setLegalMoves(gameState.getLegalMoves(position));
    }
  }, [selectedPosition, legalMoves, gameState, animateMove, gameMakeMove, config.duration]);

  return (
    <div className="game-page">
      <BoardAnimationContainer
        animationConfig={config}
        onConfigChange={setConfig}
        checkConfig={{
          isCheck: gameState.isCheck,
          checkSide: gameState.turn,
        }}
        gameEndConfig={{
          isGameOver: gameState.isGameOver,
          winner: gameState.winner,
          winReason: gameState.winReason,
        }}
      >
        <PieceMovementContainer
          currentMove={currentMove}
          lastMove={lastMove}
          selectedPosition={selectedPosition}
          legalMoves={legalMoves}
          config={config}
          cellSize={50}
          onMoveClick={handlePieceClick}
        >
          <Board
            fen={gameState.fen}
            onPieceClick={handlePieceClick}
            orientation={gameState.playerSide}
          />
        </PieceMovementContainer>
      </BoardAnimationContainer>

      {/* 游戏信息面板 */}
      <GameInfoPanel gameState={gameState} />
    </div>
  );
}
```

---

## ⚙️ 自定义配置

### 3. 动画配置持久化

```tsx
import React, { useEffect, useState } from 'react';
import { BoardAnimationContainer, type AnimationConfig } from './board/BoardAnimation';

const STORAGE_KEY = 'chess-animation-config';

const defaultConfig: AnimationConfig = {
  enabled: true,
  moveAnimation: true,
  captureAnimation: true,
  checkAnimation: true,
  gameEndAnimation: true,
  speedMultiplier: 1.0,
};

function GameWithPersistedConfig() {
  const [config, setConfig] = useState<AnimationConfig>(() => {
    // 从 localStorage 读取配置
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : defaultConfig;
  });

  // 保存配置到 localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  }, [config]);

  return (
    <BoardAnimationContainer
      animationConfig={config}
      onConfigChange={setConfig}
    >
      {/* 棋盘组件 */}
    </BoardAnimationContainer>
  );
}
```

---

## 🎯 特定场景示例

### 4. 仅显示最后一步标记

```tsx
import { PieceMovementContainer, LastMoveMarker } from './board/PieceMovement';

function MinimalBoard({ lastMove }) {
  return (
    <PieceMovementContainer config={{ showLastMove: true, showLegalMoves: false }}>
      <Board />
      <LastMoveMarker lastMove={lastMove} />
    </PieceMovementContainer>
  );
}
```

### 5. 回放模式（禁用所有动画）

```tsx
function ReplayMode({ moves }) {
  const disabledConfig = {
    enabled: false,
    moveAnimation: false,
    captureAnimation: false,
    checkAnimation: false,
    gameEndAnimation: false,
    speedMultiplier: 1.0,
  };

  return (
    <BoardAnimationContainer animationConfig={disabledConfig}>
      <PieceMovementContainer config={disabledConfig}>
        <Board />
      </PieceMovementContainer>
    </BoardAnimationContainer>
  );
}
```

### 6. 移动端优化配置

```tsx
function MobileGame() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  const mobileConfig = {
    enabled: true,
    moveAnimation: true,
    captureAnimation: isMobile, // 移动端禁用吃子特效以提升性能
    checkAnimation: true,
    gameEndAnimation: isMobile, // 移动端简化胜负动画
    speedMultiplier: 1.2, // 移动端加快速度
  };

  return (
    <BoardAnimationContainer animationConfig={mobileConfig}>
      <PieceMovementContainer config={mobileConfig}>
        <Board />
      </PieceMovementContainer>
    </BoardAnimationContainer>
  );
}
```

---

## 🎨 样式定制

### 7. 自定义棋子样式

```tsx
import './CustomPiece.css';

function CustomPiece({ piece, position }) {
  return (
    <div className={`custom-piece ${piece.side} ${piece.type}`} data-position={position}>
      <span className="piece-label">
        {getPieceLabel(piece.type, piece.side)}
      </span>
    </div>
  );
}

// CustomPiece.css
.custom-piece {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  /* 自定义渐变 */
  background: linear-gradient(145deg, #ffd700 0%, #ff8c00 100%);
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 2px 4px rgba(255, 255, 255, 0.5);
}

.custom-piece.red {
  background: linear-gradient(145deg, #ff6b6b 0%, #c0392b 100%);
}

.custom-piece.black {
  background: linear-gradient(145deg, #555 0%, #222 100%);
}
```

### 8. 自定义动画效果

```tsx
// 添加自定义动画类
.animate-custom-move {
  animation: customMove 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes customMove {
  0% {
    transform: translate(-50%, -50%) scale(0.5) rotate(-180deg);
    opacity: 0;
  }
  100% {
    transform: translate(-50%, -50%) scale(1) rotate(0deg);
    opacity: 1;
  }
}

// 使用
<MovingPiece 
  move={currentMove}
  className="animate-custom-move"
/>
```

---

## 🧪 测试示例

### 9. 单元测试

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { CheckAnimation } from './board/BoardAnimation';

describe('CheckAnimation', () => {
  it('should display check message when isCheck is true', () => {
    render(<CheckAnimation isCheck={true} checkSide="red" />);
    expect(screen.getByText('将军!')).toBeInTheDocument();
  });

  it('should hide check message after 2000ms', async () => {
    render(<CheckAnimation isCheck={true} />);
    
    await waitFor(
      () => {
        expect(screen.queryByText('将军!')).not.toBeInTheDocument();
      },
      { timeout: 2100 }
    );
  });

  it('should not display when animation is disabled', () => {
    render(
      <CheckAnimation 
        isCheck={true} 
        config={{ enabled: false, checkAnimation: false, speedMultiplier: 1 }}
      />
    );
    expect(screen.queryByText('将军!')).not.toBeInTheDocument();
  });
});
```

### 10. E2E 测试 (Playwright)

```typescript
import { test, expect } from '@playwright/test';

test('should play move animation', async ({ page }) => {
  await page.goto('/game/123');
  
  // 点击起始位置
  await page.click('[data-position="e2"]');
  
  // 点击目标位置
  await page.click('[data-position="e4"]');
  
  // 验证移动动画出现
  const movingPiece = page.locator('.moving-piece');
  await expect(movingPiece).toBeVisible();
  
  // 等待动画完成
  await movingPiece.waitFor({ state: 'detached', timeout: 1000 });
  
  // 验证最后一步标记
  const lastMoveMarker = page.locator('.last-move-marker');
  await expect(lastMoveMarker).toHaveCount(2);
});

test('should show check animation when king is in check', async ({ page }) => {
  await page.goto('/game/456');
  
  // 执行一步导致将军的走棋
  await page.click('[data-position="c2"]');
  await page.click('[data-position="c7"]');
  
  // 验证将军动画
  const checkAnimation = page.locator('.check-animation');
  await expect(checkAnimation).toBeVisible();
  
  const checkText = page.locator('.check-text');
  await expect(checkText).toContainText('将军!');
});
```

---

## 🔧 高级用法

### 11. 动画队列管理

```tsx
import { useRef, useCallback } from 'react';
import { usePieceMovement } from './board/PieceMovement';

function useQueuedMoves() {
  const { makeMove, isMoving, config } = usePieceMovement();
  const moveQueue = useRef<Array<MoveAnimation>>([]);

  const processQueue = useCallback(() => {
    if (moveQueue.current.length === 0 || isMoving) return;

    const nextMove = moveQueue.current.shift();
    if (nextMove) {
      makeMove(nextMove.from, nextMove.to, nextMove.piece, nextMove.isCapture);
      
      // 动画完成后处理下一个
      setTimeout(processQueue, config.duration);
    }
  }, [makeMove, isMoving, config.duration]);

  const queueMove = useCallback((move: MoveAnimation) => {
    moveQueue.current.push(move);
    processQueue();
  }, [processQueue]);

  return { queueMove, isMoving };
}
```

### 12. 与 WebSocket 实时同步

```tsx
import { useEffect } from 'react';
import { usePieceMovement } from './board/PieceMovement';
import { useWebSocket } from '@/hooks/useWebSocket';

function RealtimeGame({ gameId }) {
  const { makeMove, currentMove } = usePieceMovement();
  const { subscribe, send } = useWebSocket(`/ws/game/${gameId}/`);

  // 订阅对手走棋
  useEffect(() => {
    return subscribe('move_made', (data) => {
      const { from, to, piece, isCapture } = data.move;
      makeMove(from, to, piece, isCapture);
    });
  }, [subscribe, makeMove]);

  // 发送走棋
  const handleMove = (from: string, to: string) => {
    send('make_move', { from, to });
  };

  return <Board />;
}
```

---

## 📱 响应式设计

### 13. 自适应棋盘大小

```tsx
function ResponsiveBoard() {
  const [cellSize, setCellSize] = useState(50);

  useEffect(() => {
    const updateCellSize = () => {
      const width = window.innerWidth;
      if (width < 400) {
        setCellSize(35);
      } else if (width < 600) {
        setCellSize(40);
      } else if (width < 800) {
        setCellSize(45);
      } else {
        setCellSize(50);
      }
    };

    updateCellSize();
    window.addEventListener('resize', updateCellSize);
    return () => window.removeEventListener('resize', updateCellSize);
  }, []);

  return (
    <PieceMovementContainer cellSize={cellSize}>
      <Board />
    </PieceMovementContainer>
  );
}
```

---

## 🎭 无障碍支持

### 14. 支持减少动画偏好

```tsx
import { useEffect, useState } from 'react';

function AccessibleGame() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const config = {
    enabled: !prefersReducedMotion,
    moveAnimation: !prefersReducedMotion,
    captureAnimation: !prefersReducedMotion,
    checkAnimation: true, // 保留必要的提示
    gameEndAnimation: !prefersReducedMotion,
    speedMultiplier: 1.0,
  };

  return (
    <BoardAnimationContainer animationConfig={config}>
      <PieceMovementContainer config={config}>
        <Board />
      </PieceMovementContainer>
    </BoardAnimationContainer>
  );
}
```

---

## 📚 相关资源

- [完整 API 文档](./README.md)
- [样式定制指南](../../../docs/frontend/styling-guide.md)
- [性能优化建议](../../../docs/frontend/performance.md)

---

**最后更新**: 2026-03-06
