/**
 * PieceMovement.tsx - 棋子移动动画组件
 * 
 * 功能：
 * - 走棋平滑移动动画
 * - 棋子选中/高亮效果
 * - 合法走法提示
 * - 最后一步标记
 * 
 * @author OpenClaw 助手
 * @date 2026-03-06
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import './PieceMovement.css';

// ============ 类型定义 ============

export interface Position {
  /** 列 (a-i) */
  file: string;
  /** 行 (0-9) */
  rank: number;
}

export interface PieceData {
  /** 棋子类型 (k/a/b/n/r/c/p) */
  type: string;
  /** 阵营 (red/black) */
  side: 'red' | 'black';
  /** 位置 */
  position: string;
}

export interface MoveAnimation {
  /** 起始位置 */
  from: string;
  /** 目标位置 */
  to: string;
  /** 棋子数据 */
  piece: PieceData;
  /** 是否吃子 */
  isCapture: boolean;
}

export interface PieceMovementConfig {
  /** 是否启用移动动画 */
  enabled: boolean;
  /** 动画持续时间 (ms) */
  duration: number;
  /** 动画缓动函数 */
  easing: 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
  /** 显示最后一步标记 */
  showLastMove: boolean;
  /** 显示合法走法提示 */
  showLegalMoves: boolean;
}

// ============ 默认配置 ============

const DEFAULT_CONFIG: PieceMovementConfig = {
  enabled: true,
  duration: 300,
  easing: 'ease-in-out',
  showLastMove: true,
  showLegalMoves: true,
};

// ============ 工具函数 ============

/**
 * 将位置字符串转换为坐标
 * @param position 位置字符串 (如 "e5")
 * @returns 坐标对象
 */
export const parsePosition = (position: string): Position => {
  const file = position.charAt(0).toLowerCase();
  const rank = parseInt(position.charAt(1), 10);
  return { file, rank };
};

/**
 * 将坐标转换为像素位置
 * @param position 位置字符串
 * @param cellSize 格子大小 (px)
 * @param offset 偏移量 (px)
 * @returns 像素坐标
 */
export const positionToPixels = (
  position: string,
  cellSize: number = 50,
  offset: number = 25
): { x: number; y: number } => {
  const { file, rank } = parsePosition(position);
  const fileIndex = file.charCodeAt(0) - 'a'.charCodeAt(0);
  const x = offset + fileIndex * cellSize;
  const y = offset + (9 - rank) * cellSize;
  return { x, y };
};

// ============ 移动中的棋子组件 ============

export interface MovingPieceProps {
  /** 移动动画数据 */
  move?: MoveAnimation;
  /** 棋盘格子大小 */
  cellSize?: number;
  /** 配置 */
  config?: PieceMovementConfig;
  /** 动画完成回调 */
  onComplete?: () => void;
}

export const MovingPiece: React.FC<MovingPieceProps> = ({
  move,
  cellSize = 50,
  config = DEFAULT_CONFIG,
  onComplete,
}) => {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!move || !config.enabled) {
      setPosition(null);
      return;
    }

    const fromPos = positionToPixels(move.from, cellSize);
    const toPos = positionToPixels(move.to, cellSize);

    // 设置起始位置
    setPosition(fromPos);

    // 触发动画
    const timer = setTimeout(() => {
      setPosition(toPos);
    }, 50);

    // 动画完成后回调
    const completeTimer = setTimeout(() => {
      setPosition(null);
      onComplete?.();
    }, config.duration + 50);

    return () => {
      clearTimeout(timer);
      clearTimeout(completeTimer);
    };
  }, [move, cellSize, config, onComplete]);

  if (!move || !position || !config.enabled) return null;

  return (
    <div
      className="moving-piece"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        transition: `all ${config.duration}ms ${config.easing}`,
      }}
    >
      <div className={`piece ${move.piece.side} ${move.piece.type}`}>
        <span className="piece-label">
          {getPieceLabel(move.piece.type, move.piece.side)}
        </span>
      </div>
    </div>
  );
};

/**
 * 获取棋子标签
 */
const getPieceLabel = (type: string, side: 'red' | 'black'): string => {
  const labels: Record<string, { red: string; black: string }> = {
    k: { red: '帅', black: '将' },
    a: { red: '仕', black: '士' },
    b: { red: '相', black: '象' },
    n: { red: '马', black: '马' },
    r: { red: '车', black: '车' },
    c: { red: '炮', black: '炮' },
    p: { red: '兵', black: '卒' },
  };
  return labels[type]?.[side] || '';
};

// ============ 最后一步标记组件 ============

export interface LastMoveMarkerProps {
  /** 最后一步移动 */
  lastMove?: MoveAnimation;
  /** 棋盘格子大小 */
  cellSize?: number;
  /** 配置 */
  config?: PieceMovementConfig;
}

export const LastMoveMarker: React.FC<LastMoveMarkerProps> = ({
  lastMove,
  cellSize = 50,
  config = DEFAULT_CONFIG,
}) => {
  if (!lastMove || !config.showLastMove) return null;

  const fromPos = positionToPixels(lastMove.from, cellSize);
  const toPos = positionToPixels(lastMove.to, cellSize);

  return (
    <>
      <div
        className="last-move-marker from"
        style={{
          left: `${fromPos.x - cellSize / 2}px`,
          top: `${fromPos.y - cellSize / 2}px`,
          width: `${cellSize}px`,
          height: `${cellSize}px`,
        }}
      />
      <div
        className="last-move-marker to"
        style={{
          left: `${toPos.x - cellSize / 2}px`,
          top: `${toPos.y - cellSize / 2}px`,
          width: `${cellSize}px`,
          height: `${cellSize}px`,
        }}
      />
    </>
  );
};

// ============ 合法走法提示组件 ============

export interface LegalMovesHintProps {
  /** 当前位置 */
  currentPosition?: string;
  /** 合法走法位置列表 */
  legalMoves?: string[];
  /** 棋盘格子大小 */
  cellSize?: number;
  /** 配置 */
  config?: PieceMovementConfig;
  /** 点击走法回调 */
  onMoveClick?: (position: string) => void;
}

export const LegalMovesHint: React.FC<LegalMovesHintProps> = ({
  currentPosition,
  legalMoves,
  cellSize = 50,
  config = DEFAULT_CONFIG,
  onMoveClick,
}) => {
  if (!currentPosition || !legalMoves || !config.showLegalMoves) return null;

  return (
    <>
      {legalMoves.map((position) => {
        const pos = positionToPixels(position, cellSize);
        return (
          <div
            key={position}
            className="legal-move-hint"
            style={{
              left: `${pos.x}px`,
              top: `${pos.y}px`,
            }}
            onClick={() => onMoveClick?.(position)}
          >
            <div className="hint-circle" />
          </div>
        );
      })}
    </>
  );
};

// ============ 棋子高亮效果组件 ============

export interface PieceHighlightProps {
  /** 高亮位置 */
  position?: string;
  /** 高亮类型 */
  highlightType?: 'selected' | 'check' | 'threat';
  /** 棋盘格子大小 */
  cellSize?: number;
}

export const PieceHighlight: React.FC<PieceHighlightProps> = ({
  position,
  highlightType = 'selected',
  cellSize = 50,
}) => {
  if (!position) return null;

  const pos = positionToPixels(position, cellSize);

  return (
    <div
      className={`piece-highlight ${highlightType}`}
      style={{
        left: `${pos.x}px`,
        top: `${pos.y}px`,
        width: `${cellSize}px`,
        height: `${cellSize}px`,
      }}
    >
      <div className="highlight-ring" />
    </div>
  );
};

// ============ 主容器组件 ============

export interface PieceMovementContainerProps {
  children: React.ReactNode;
  /** 当前移动动画 */
  currentMove?: MoveAnimation;
  /** 最后一步移动 */
  lastMove?: MoveAnimation;
  /** 当前选中位置 */
  selectedPosition?: string;
  /** 合法走法列表 */
  legalMoves?: string[];
  /** 棋盘格子大小 */
  cellSize?: number;
  /** 配置 */
  config?: PieceMovementConfig;
  /** 配置变更回调 */
  onConfigChange?: (config: PieceMovementConfig) => void;
  /** 走法点击回调 */
  onMoveClick?: (position: string) => void;
  /** 移动完成回调 */
  onMoveComplete?: () => void;
}

export const PieceMovementContainer: React.FC<PieceMovementContainerProps> = ({
  children,
  currentMove,
  lastMove,
  selectedPosition,
  legalMoves,
  cellSize = 50,
  config = DEFAULT_CONFIG,
  onConfigChange,
  onMoveClick,
  onMoveComplete,
}) => {
  return (
    <div className="piece-movement-container" style={{
      '--move-duration': `${config.duration}ms`,
      '--move-easing': config.easing,
    } as React.CSSProperties}>
      {children}

      {/* 最后一步标记 */}
      <LastMoveMarker
        lastMove={lastMove}
        cellSize={cellSize}
        config={config}
      />

      {/* 合法走法提示 */}
      <LegalMovesHint
        currentPosition={selectedPosition}
        legalMoves={legalMoves}
        cellSize={cellSize}
        config={config}
        onMoveClick={onMoveClick}
      />

      {/* 选中棋子高亮 */}
      {selectedPosition && (
        <PieceHighlight
          position={selectedPosition}
          highlightType="selected"
          cellSize={cellSize}
        />
      )}

      {/* 移动中的棋子 */}
      <MovingPiece
        move={currentMove}
        cellSize={cellSize}
        config={config}
        onComplete={onMoveComplete}
      />
    </div>
  );
};

// ============ 使用 Hook 管理移动状态 ============

export interface UsePieceMovementReturn {
  /** 当前移动 */
  currentMove: MoveAnimation | undefined;
  /** 最后一步移动 */
  lastMove: MoveAnimation | undefined;
  /** 执行移动 */
  makeMove: (from: string, to: string, piece: PieceData, isCapture?: boolean) => void;
  /** 是否正在移动 */
  isMoving: boolean;
  /** 配置 */
  config: PieceMovementConfig;
  /** 更新配置 */
  setConfig: React.Dispatch<React.SetStateAction<PieceMovementConfig>>;
}

/**
 * 管理棋子移动状态的 Hook
 */
export const usePieceMovement = (
  initialConfig: Partial<PieceMovementConfig> = {}
): UsePieceMovementReturn => {
  const [config, setConfig] = useState<PieceMovementConfig>({
    ...DEFAULT_CONFIG,
    ...initialConfig,
  });

  const [currentMove, setCurrentMove] = useState<MoveAnimation | undefined>();
  const [lastMove, setLastMove] = useState<MoveAnimation | undefined>();
  const [isMoving, setIsMoving] = useState(false);

  const makeMove = useCallback(
    (from: string, to: string, piece: PieceData, isCapture = false) => {
      if (isMoving) return;

      const move: MoveAnimation = { from, to, piece, isCapture };
      setCurrentMove(move);
      setIsMoving(true);

      // 动画完成后更新状态
      setTimeout(() => {
        setCurrentMove(undefined);
        setLastMove(move);
        setIsMoving(false);
      }, config.duration);
    },
    [isMoving, config.duration]
  );

  return {
    currentMove,
    lastMove,
    makeMove,
    isMoving,
    config,
    setConfig,
  };
};

export default PieceMovementContainer;
