/**
 * 象棋动画 Hook
 * 管理棋盘和棋子的各种动画效果
 */

import { useState, useCallback, useEffect, useRef } from 'react';

export interface AnimationState {
  isMoving: boolean;
  isCapturing: boolean;
  isInCheck: boolean;
  isGameOver: boolean;
  lastMoveFrom: string | null;
  lastMoveTo: string | null;
  capturedPosition: string | null;
  winner: 'red' | 'black' | null;
}

export interface UseChessAnimationProps {
  onAnimationComplete?: (type: string) => void;
  animationDuration?: number;
}

export function useChessAnimation({
  onAnimationComplete,
  animationDuration = 300,
}: UseChessAnimationProps = {}) {
  const [animationState, setAnimationState] = useState<AnimationState>({
    isMoving: false,
    isCapturing: false,
    isInCheck: false,
    isGameOver: false,
    lastMoveFrom: null,
    lastMoveTo: null,
    capturedPosition: null,
    winner: null,
  });

  const animationTimers = useRef<Record<string, NodeJS.Timeout>>({});

  // 清理定时器
  useEffect(() => {
    return () => {
      Object.values(animationTimers.current).forEach(clearTimeout);
    };
  }, []);

  /**
   * 触发行棋动画
   */
  const triggerMoveAnimation = useCallback(
    (from: string, to: string, isCapture: boolean = false) => {
      setAnimationState((prev) => ({
        ...prev,
        isMoving: true,
        isCapturing: isCapture,
        lastMoveFrom: from,
        lastMoveTo: to,
        capturedPosition: isCapture ? to : null,
      }));

      // 移动动画完成后
      animationTimers.current.move = setTimeout(() => {
        setAnimationState((prev) => ({
          ...prev,
          isMoving: false,
          isCapturing: false,
        }));
        onAnimationComplete?.('move');
      }, animationDuration);

      // 吃子动画持续时间更长
      if (isCapture) {
        animationTimers.current.capture = setTimeout(() => {
          setAnimationState((prev) => ({
            ...prev,
            capturedPosition: null,
          }));
          onAnimationComplete?.('capture');
        }, animationDuration + 100);
      }
    },
    [animationDuration, onAnimationComplete]
  );

  /**
   * 触发将军动画
   */
  const triggerCheckAnimation = useCallback(() => {
    setAnimationState((prev) => ({
      ...prev,
      isInCheck: true,
    }));

    // 将军动画持续 2 秒
    animationTimers.current.check = setTimeout(() => {
      setAnimationState((prev) => ({
        ...prev,
        isInCheck: false,
      }));
      onAnimationComplete?.('check');
    }, 2000);
  }, [onAnimationComplete]);

  /**
   * 触发游戏结束动画
   */
  const triggerGameOverAnimation = useCallback(
    (winner: 'red' | 'black' | null) => {
      setAnimationState((prev) => ({
        ...prev,
        isGameOver: true,
        winner,
      }));

      onAnimationComplete?.('gameOver');
    },
    [onAnimationComplete]
  );

  /**
   * 清除游戏结束动画
   */
  const clearGameOverAnimation = useCallback(() => {
    setAnimationState((prev) => ({
      ...prev,
      isGameOver: false,
      winner: null,
    }));
  }, []);

  /**
   * 更新最后走棋位置高亮
   */
  const updateLastMove = useCallback((from: string | null, to: string | null) => {
    setAnimationState((prev) => ({
      ...prev,
      lastMoveFrom: from,
      lastMoveTo: to,
    }));
  }, []);

  /**
   * 清除所有动画
   */
  const clearAllAnimations = useCallback(() => {
    Object.values(animationTimers.current).forEach(clearTimeout);
    animationTimers.current = {};

    setAnimationState({
      isMoving: false,
      isCapturing: false,
      isInCheck: false,
      isGameOver: false,
      lastMoveFrom: null,
      lastMoveTo: null,
      capturedPosition: null,
      winner: null,
    });
  }, []);

  return {
    animationState,
    triggerMoveAnimation,
    triggerCheckAnimation,
    triggerGameOverAnimation,
    clearGameOverAnimation,
    updateLastMove,
    clearAllAnimations,
  };
}

/**
 * 棋子动画类名生成器
 */
export function getPieceAnimationClasses(
  position: string,
  animationState: AnimationState,
  isSelected: boolean = false
): string {
  const classes: string[] = [];

  // 移动中的棋子
  if (animationState.isMoving && animationState.lastMoveFrom === position) {
    classes.push('chess-piece-moving');
  }

  // 被吃的棋子
  if (animationState.isCapturing && animationState.capturedPosition === position) {
    classes.push('piece-captured');
  }

  // 胜利方的棋子
  if (animationState.isGameOver && animationState.winner) {
    classes.push('piece-winner');
  }

  // 选中的棋子
  if (isSelected) {
    classes.push('piece-selected');
  }

  return classes.join(' ');
}

/**
 * 棋盘格子动画类名生成器
 */
export function getSquareAnimationClasses(
  position: string,
  animationState: AnimationState,
  isValidMove: boolean = false
): string {
  const classes: string[] = [];

  // 最后走棋的起始/目标位置
  if (animationState.lastMoveFrom === position || animationState.lastMoveTo === position) {
    classes.push('last-move-highlight');
  }

  // 吃子位置闪光
  if (animationState.capturedPosition === position) {
    classes.push('capture-flash');
  }

  // 有效走棋提示
  if (isValidMove) {
    classes.push('valid-move-hint');
  }

  return classes.join(' ');
}

export default useChessAnimation;
