/**
 * useChessAnimation Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChessAnimation, getPieceAnimationClasses, getSquareAnimationClasses } from './useChessAnimation';

describe('useChessAnimation', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('应该初始化默认状态', () => {
    const { result } = renderHook(() => useChessAnimation());

    expect(result.current.animationState).toEqual({
      isMoving: false,
      isCapturing: false,
      isInCheck: false,
      isGameOver: false,
      lastMoveFrom: null,
      lastMoveTo: null,
      capturedPosition: null,
      winner: null,
    });
  });

  it('应该触发行棋动画', () => {
    const onAnimationComplete = vi.fn();
    const { result } = renderHook(() => useChessAnimation({ onAnimationComplete }));

    act(() => {
      result.current.triggerMoveAnimation('e0', 'e4');
    });

    expect(result.current.animationState.isMoving).toBe(true);
    expect(result.current.animationState.lastMoveFrom).toBe('e0');
    expect(result.current.animationState.lastMoveTo).toBe('e4');
    expect(result.current.animationState.isCapturing).toBe(false);

    // 前进到动画完成
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current.animationState.isMoving).toBe(false);
    expect(onAnimationComplete).toHaveBeenCalledWith('move');
  });

  it('应该触发吃子动画', () => {
    const onAnimationComplete = vi.fn();
    const { result } = renderHook(() => useChessAnimation({ onAnimationComplete }));

    act(() => {
      result.current.triggerMoveAnimation('h0', 'h7', true);
    });

    expect(result.current.animationState.isCapturing).toBe(true);
    expect(result.current.animationState.capturedPosition).toBe('h7');

    // 前进到移动动画完成
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current.animationState.isMoving).toBe(false);
    expect(result.current.animationState.isCapturing).toBe(false);

    // 前进到吃子动画完成
    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.animationState.capturedPosition).toBe(null);
    expect(onAnimationComplete).toHaveBeenCalledWith('capture');
  });

  it('应该触发将军动画', () => {
    const onAnimationComplete = vi.fn();
    const { result } = renderHook(() => useChessAnimation({ onAnimationComplete }));

    act(() => {
      result.current.triggerCheckAnimation();
    });

    expect(result.current.animationState.isInCheck).toBe(true);

    // 前进到动画完成 (2 秒)
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.animationState.isInCheck).toBe(false);
    expect(onAnimationComplete).toHaveBeenCalledWith('check');
  });

  it('应该触发游戏结束动画', () => {
    const onAnimationComplete = vi.fn();
    const { result } = renderHook(() => useChessAnimation({ onAnimationComplete }));

    act(() => {
      result.current.triggerGameOverAnimation('red');
    });

    expect(result.current.animationState.isGameOver).toBe(true);
    expect(result.current.animationState.winner).toBe('red');
    expect(onAnimationComplete).toHaveBeenCalledWith('gameOver');
  });

  it('应该清除游戏结束动画', () => {
    const { result } = renderHook(() => useChessAnimation());

    act(() => {
      result.current.triggerGameOverAnimation('red');
    });

    expect(result.current.animationState.isGameOver).toBe(true);

    act(() => {
      result.current.clearGameOverAnimation();
    });

    expect(result.current.animationState.isGameOver).toBe(false);
    expect(result.current.animationState.winner).toBe(null);
  });

  it('应该更新最后走棋位置', () => {
    const { result } = renderHook(() => useChessAnimation());

    act(() => {
      result.current.updateLastMove('e0', 'e4');
    });

    expect(result.current.animationState.lastMoveFrom).toBe('e0');
    expect(result.current.animationState.lastMoveTo).toBe('e4');
  });

  it('应该清除所有动画', () => {
    const onAnimationComplete = vi.fn();
    const { result } = renderHook(() => useChessAnimation({ onAnimationComplete }));

    act(() => {
      result.current.triggerMoveAnimation('e0', 'e4');
      result.current.triggerCheckAnimation();
    });

    act(() => {
      result.current.clearAllAnimations();
    });

    expect(result.current.animationState).toEqual({
      isMoving: false,
      isCapturing: false,
      isInCheck: false,
      isGameOver: false,
      lastMoveFrom: null,
      lastMoveTo: null,
      capturedPosition: null,
      winner: null,
    });
  });
});

describe('getPieceAnimationClasses', () => {
  const baseAnimationState = {
    isMoving: false,
    isCapturing: false,
    isInCheck: false,
    isGameOver: false,
    lastMoveFrom: null,
    lastMoveTo: null,
    capturedPosition: null,
    winner: null,
  };

  it('应该返回空字符串当没有动画时', () => {
    const classes = getPieceAnimationClasses('e0', baseAnimationState);
    expect(classes).toBe('');
  });

  it('应该返回移动中棋子类名', () => {
    const animationState = {
      ...baseAnimationState,
      isMoving: true,
      lastMoveFrom: 'e0',
    };

    const classes = getPieceAnimationClasses('e0', animationState);
    expect(classes).toContain('chess-piece-moving');
  });

  it('应该返回被吃棋子类名', () => {
    const animationState = {
      ...baseAnimationState,
      isCapturing: true,
      capturedPosition: 'e4',
    };

    const classes = getPieceAnimationClasses('e4', animationState);
    expect(classes).toContain('piece-captured');
  });

  it('应该返回胜利方棋子类名', () => {
    const animationState = {
      ...baseAnimationState,
      isGameOver: true,
      winner: 'red' as const,
    };

    const classes = getPieceAnimationClasses('e0', animationState);
    expect(classes).toContain('piece-winner');
  });

  it('应该返回选中棋子类名', () => {
    const classes = getPieceAnimationClasses('e0', baseAnimationState, true);
    expect(classes).toContain('piece-selected');
  });

  it('应该组合多个类名', () => {
    const animationState = {
      ...baseAnimationState,
      isMoving: true,
      lastMoveFrom: 'e0',
      isGameOver: true,
      winner: 'red' as const,
    };

    const classes = getPieceAnimationClasses('e0', animationState, true);
    expect(classes).toContain('chess-piece-moving');
    expect(classes).toContain('piece-winner');
    expect(classes).toContain('piece-selected');
  });
});

describe('getSquareAnimationClasses', () => {
  const baseAnimationState = {
    isMoving: false,
    isCapturing: false,
    isInCheck: false,
    isGameOver: false,
    lastMoveFrom: null,
    lastMoveTo: null,
    capturedPosition: null,
    winner: null,
  };

  it('应该返回空字符串当没有动画时', () => {
    const classes = getSquareAnimationClasses('e0', baseAnimationState);
    expect(classes).toBe('');
  });

  it('应该返回最后走棋高亮类名', () => {
    const animationState = {
      ...baseAnimationState,
      lastMoveFrom: 'e0',
      lastMoveTo: 'e4',
    };

    const classesFrom = getSquareAnimationClasses('e0', animationState);
    const classesTo = getSquareAnimationClasses('e4', animationState);

    expect(classesFrom).toContain('last-move-highlight');
    expect(classesTo).toContain('last-move-highlight');
  });

  it('应该返回吃子闪光类名', () => {
    const animationState = {
      ...baseAnimationState,
      capturedPosition: 'e4',
    };

    const classes = getSquareAnimationClasses('e4', animationState);
    expect(classes).toContain('capture-flash');
  });

  it('应该返回有效走棋提示类名', () => {
    const classes = getSquareAnimationClasses('e4', baseAnimationState, true);
    expect(classes).toContain('valid-move-hint');
  });
});
