import React from 'react';
import type { Piece } from '@/types';
import { getPieceAnimationClasses, type AnimationState } from '@/hooks/useChessAnimation';
import '@/styles/chess-animations.css';

interface ChessPieceProps {
  piece: Piece;
  isSelected?: boolean;
  isLastMove?: boolean;
  isCaptured?: boolean;
  animationState?: AnimationState;
  disabled?: boolean;
  onClick?: () => void;
}

// 棋子文字映射
const PIECE_CHARS: Record<string, { red: string; black: string }> = {
  king: { red: '帥', black: '將' },
  advisor: { red: '仕', black: '士' },
  elephant: { red: '相', black: '象' },
  horse: { red: '馬', black: '馬' },
  rook: { red: '車', black: '車' },
  cannon: { red: '炮', black: '砲' },
  pawn: { red: '兵', black: '卒' },
};

const ChessPiece: React.FC<ChessPieceProps> = ({
  piece,
  isSelected = false,
  isLastMove = false,
  isCaptured = false,
  animationState,
  disabled = false,
  onClick,
}) => {
  const char = PIECE_CHARS[piece.type][piece.color];
  const isRed = piece.color === 'red';

  // 获取动画类名
  const pieceAnimationClasses = animationState
    ? getPieceAnimationClasses(piece.position, animationState, isSelected)
    : '';

  return (
    <div
      className={`
        chess-piece
        relative
        w-[80%]
        h-[80%]
        rounded-full
        flex
        items-center
        justify-center
        transition-all
        duration-200
        ${pieceAnimationClasses}
        ${isSelected ? 'selected scale-110 z-10' : ''}
        ${isLastMove ? 'last-move' : ''}
        ${isCaptured ? 'piece-captured' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105'}
      `}
      style={{
        background: isRed
          ? 'radial-gradient(circle at 30% 30%, #fef2f2, #fecaca, #dc2626)'
          : 'radial-gradient(circle at 30% 30%, #f3f4f6, #d1d5db, #374151)',
        boxShadow: isSelected
          ? '0 0 20px rgba(234, 179, 8, 0.6), inset 0 -2px 4px rgba(0, 0, 0, 0.2)'
          : '2px 2px 4px rgba(0, 0, 0, 0.3), inset 0 -2px 4px rgba(0, 0, 0, 0.1)',
        border: `2px solid ${isRed ? '#991b1b' : '#1f2937'}`,
      }}
      onClick={() => !disabled && onClick?.()}
    >
      {/* 棋子外圈装饰 */}
      <div
        className="absolute inset-1 rounded-full"
        style={{
          border: `1px solid ${isRed ? 'rgba(153, 27, 27, 0.3)' : 'rgba(31, 41, 55, 0.3)'}`,
        }}
      />

      {/* 棋子文字 */}
      <span
        className={`
          font-chinese
          text-xl
          md:text-2xl
          font-bold
          select-none
          ${isRed ? 'text-red-700' : 'text-gray-900'}
          ${isSelected ? 'animate-pulse' : ''}
        `}
        style={{
          textShadow: '1px 1px 2px rgba(0, 0, 0, 0.2)',
        }}
      >
        {char}
      </span>

      {/* 高光效果 */}
      <div
        className="absolute top-1 left-1 w-1/3 h-1/3 rounded-full opacity-30"
        style={{
          background: 'radial-gradient(circle, rgba(255,255,255,0.8), transparent)',
        }}
      />
    </div>
  );
};

export default ChessPiece;
