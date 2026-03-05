import React, { useMemo, useCallback } from 'react';
import type { Piece, BoardState } from '@/types';

interface ChessBoardProps {
  boardState: BoardState;
  selectedPosition?: string | null;
  validMoves?: string[];
  lastMove?: { from: string; to: string } | null;
  onPieceClick?: (position: string) => void;
  onMove?: (from: string, to: string) => void;
  orientation?: 'red' | 'black';
  disabled?: boolean;
}

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'];
const RANKS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];

function parseFen(fen: string): Piece[] {
  const pieces: Piece[] = [];
  const rows = fen.split(' ')[0].split('/');
  
  rows.forEach((row, rankIndex) => {
    let fileIndex = 0;
    for (const char of row) {
      if (/\d/.test(char)) {
        fileIndex += parseInt(char);
      } else {
        const color = char === char.toUpperCase() ? 'red' : 'black';
        const pieceChar = char.toLowerCase();
        const typeMap: Record<string, Piece['type']> = {
          'k': 'king', 'a': 'advisor', 'b': 'elephant', 'n': 'horse',
          'r': 'rook', 'c': 'cannon', 'p': 'pawn',
        };
        
        pieces.push({
          type: typeMap[pieceChar],
          color,
          position: `${FILES[fileIndex]}${9 - rankIndex}`,
        });
        fileIndex++;
      }
    }
  });
  
  return pieces;
}

const ChessBoard: React.FC<ChessBoardProps> = ({
  boardState,
  selectedPosition,
  validMoves = [],
  lastMove,
  onPieceClick,
  onMove,
  orientation = 'red',
  disabled = false,
}) => {
  const pieces = useMemo(() => parseFen(boardState.fen), [boardState.fen]);

  const squares = useMemo(() => {
    const squares: Array<{
      file: string;
      rank: number;
      position: string;
      piece?: Piece;
      isLastMoveFrom?: boolean;
      isLastMoveTo?: boolean;
      isValidMove?: boolean;
      isSelected?: boolean;
    }> = [];

    const ranks = orientation === 'red' ? RANKS : [...RANKS].reverse();
    const files = orientation === 'red' ? FILES : [...FILES].reverse();

    ranks.forEach((rank) => {
      files.forEach((file) => {
        const position = `${file}${rank}`;
        const piece = pieces.find((p) => p.position === position);
        
        squares.push({
          file,
          rank,
          position,
          piece,
          isLastMoveFrom: lastMove?.from === position,
          isLastMoveTo: lastMove?.to === position,
          isValidMove: validMoves.includes(position),
          isSelected: selectedPosition === position,
        });
      });
    });

    return squares;
  }, [orientation, pieces, validMoves, selectedPosition, lastMove]);

  const handlePieceClick = useCallback(
    (position: string) => {
      if (disabled) return;
      if (onPieceClick) onPieceClick(position);
      if (selectedPosition && validMoves.includes(position) && onMove) {
        onMove(selectedPosition, position);
      }
    },
    [disabled, selectedPosition, validMoves, onPieceClick, onMove]
  );

  return (
    <div className="chess-board relative rounded-lg overflow-hidden" style={{ width: '100%', maxWidth: '450px', aspectRatio: '9 / 10' }}>
      <svg viewBox="0 0 450 500" className="w-full h-full" style={{ background: 'var(--board-light)' }}>
        <rect width="450" height="500" fill="url(#grid)" />
        <rect x="25" y="25" width="400" height="450" fill="none" stroke="var(--line)" strokeWidth="3" />
        
        {Array.from({ length: 10 }).map((_, i) => (
          <line key={`h-${i}`} x1="25" y1={25 + i * 50} x2="425" y2={25 + i * 50} stroke="var(--line)" strokeWidth="1.5" />
        ))}
        
        {Array.from({ length: 9 }).map((_, i) => (
          <g key={`v-${i}`}>
            <line x1={25 + i * 50} y1="25" x2={25 + i * 50} y2="225" stroke="var(--line)" strokeWidth="1.5" />
            <line x1={25 + i * 50} y1="275" x2={25 + i * 50} y2="475" stroke="var(--line)" strokeWidth="1.5" />
          </g>
        ))}
        
        <line x1="175" y1="25" x2="275" y2="125" stroke="var(--line)" strokeWidth="1.5" />
        <line x1="275" y1="25" x2="175" y2="125" stroke="var(--line)" strokeWidth="1.5" />
        <line x1="175" y1="375" x2="275" y2="475" stroke="var(--line)" strokeWidth="1.5" />
        <line x1="275" y1="375" x2="175" y2="475" stroke="var(--line)" strokeWidth="1.5" />
        
        <text x="125" y="255" textAnchor="middle" className="font-chinese" fontSize="24" fill="var(--line)">楚 河</text>
        <text x="325" y="255" textAnchor="middle" className="font-chinese" fontSize="24" fill="var(--line)">汉 界</text>
      </svg>

      <div className="absolute inset-0">
        {squares.map((square) => (
          <div
            key={square.position}
            className="absolute w-[11.11%] h-[10%] flex items-center justify-center"
            style={{
              left: `${(FILES.indexOf(square.file) / 8) * 100}%`,
              top: `${(orientation === 'red' ? square.rank : 9 - square.rank) * 10}%`,
            }}
            onClick={() => handlePieceClick(square.position)}
          >
            {square.piece && (
              <div
                className="w-[80%] h-[80%] rounded-full flex items-center justify-center cursor-pointer transition-transform hover:scale-105"
                style={{
                  background: square.piece.color === 'red'
                    ? 'radial-gradient(circle at 30% 30%, #fef2f2, #fecaca, #dc2626)'
                    : 'radial-gradient(circle at 30% 30%, #f3f4f6, #d1d5db, #374151)',
                  border: `2px solid ${square.piece.color === 'red' ? '#991b1b' : '#1f2937'}`,
                }}
              >
                <span className={`font-chinese text-xl font-bold ${square.piece.color === 'red' ? 'text-red-700' : 'text-gray-900'}`}>
                  {square.piece.type === 'king' ? (square.piece.color === 'red' ? '帥' : '將') :
                   square.piece.type === 'advisor' ? (square.piece.color === 'red' ? '仕' : '士') :
                   square.piece.type === 'elephant' ? (square.piece.color === 'red' ? '相' : '象') :
                   square.piece.type === 'horse' ? '馬' :
                   square.piece.type === 'rook' ? '車' :
                   square.piece.type === 'cannon' ? (square.piece.color === 'red' ? '炮' : '砲') :
                   (square.piece.color === 'red' ? '兵' : '卒')}
                </span>
              </div>
            )}
            {square.isSelected && (
              <div className="absolute inset-1 border-2 border-yellow-400 rounded-full animate-pulse" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChessBoard;
