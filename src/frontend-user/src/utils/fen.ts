/**
 * FEN (Forsyth-Edwards Notation) 工具函数
 * 用于中国象棋棋局状态的解析和生成
 */

import type { Piece, PieceType, BoardState } from '@/types';

// 棋子字符映射
const PIECE_CHARS: Record<PieceType, { red: string; black: string }> = {
  king: { red: 'K', black: 'k' },
  advisor: { red: 'A', black: 'a' },
  elephant: { red: 'B', black: 'b' },
  horse: { red: 'N', black: 'n' },
  rook: { red: 'R', black: 'r' },
  cannon: { red: 'C', black: 'c' },
  pawn: { red: 'P', black: 'p' },
};

// 反向映射
const CHAR_TO_PIECE: Record<string, PieceType> = {
  'K': 'king', 'k': 'king',
  'A': 'advisor', 'a': 'advisor',
  'B': 'elephant', 'b': 'elephant',
  'N': 'horse', 'n': 'horse',
  'R': 'rook', 'r': 'rook',
  'C': 'cannon', 'c': 'cannon',
  'P': 'pawn', 'p': 'pawn',
};

// 棋盘坐标
const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'];

/**
 * 解析 FEN 字符串为棋子数组
 * @param fen FEN 字符串
 * @returns 棋子数组
 */
export function parseFen(fen: string): Piece[] {
  const pieces: Piece[] = [];
  const parts = fen.split(' ');
  const boardPart = parts[0];
  const rows = boardPart.split('/');

  rows.forEach((row, rankIndex) => {
    let fileIndex = 0;
    for (const char of row) {
      if (/\d/.test(char)) {
        // 空位
        fileIndex += parseInt(char);
      } else {
        // 棋子
        const isRed = char === char.toUpperCase();
        const type = CHAR_TO_PIECE[char];
        
        if (type) {
          pieces.push({
            type,
            color: isRed ? 'red' : 'black',
            position: `${FILES[fileIndex]}${9 - rankIndex}`,
          });
        }
        fileIndex++;
      }
    }
  });

  return pieces;
}

/**
 * 从棋子数组生成 FEN 字符串
 * @param pieces 棋子数组
 * @returns FEN 字符串
 */
export function generateFen(pieces: Piece[]): string {
  const board: string[][] = Array(10).fill(null).map(() => Array(9).fill(''));

  // 填充棋盘
  pieces.forEach(piece => {
    const file = piece.position.charCodeAt(0) - 'a'.charCodeAt(0);
    const rank = 9 - parseInt(piece.position[1]);
    const char = PIECE_CHARS[piece.type][piece.color];
    board[rank][file] = char;
  });

  // 生成 FEN
  const rows: string[] = [];
  for (let rank = 0; rank < 10; rank++) {
    let row = '';
    let emptyCount = 0;

    for (let file = 0; file < 9; file++) {
      const cell = board[rank][file];
      if (cell === '') {
        emptyCount++;
      } else {
        if (emptyCount > 0) {
          row += emptyCount;
          emptyCount = 0;
        }
        row += cell;
      }
    }

    if (emptyCount > 0) {
      row += emptyCount;
    }

    rows.push(row);
  }

  return rows.join('/');
}

/**
 * 解析 FEN 获取完整棋盘状态
 * @param fen FEN 字符串
 * @returns 棋盘状态
 */
export function parseFenToBoardState(fen: string): BoardState {
  const parts = fen.split(' ');
  const turn = parts[1] === 'w' ? 'red' : 'black';
  const pieces = parseFen(fen);

  return {
    fen,
    turn,
    pieces,
    in_check: false,
    game_over: false,
  };
}

/**
 * 标准开局 FEN
 */
export const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1';

/**
 * 获取棋子的中文名称
 * @param piece 棋子
 * @returns 中文名称
 */
export function getPieceChineseName(piece: Piece): string {
  const names: Record<PieceType, { red: string; black: string }> = {
    king: { red: '帥', black: '將' },
    advisor: { red: '仕', black: '士' },
    elephant: { red: '相', black: '象' },
    horse: { red: '馬', black: '馬' },
    rook: { red: '車', black: '車' },
    cannon: { red: '炮', black: '砲' },
    pawn: { red: '兵', black: '卒' },
  };

  return names[piece.type][piece.color];
}

/**
 * 检查位置是否合法
 * @param position 位置字符串（如 "e2"）
 * @returns 是否合法
 */
export function isValidPosition(position: string): boolean {
  if (position.length !== 2) return false;
  
  const file = position[0];
  const rank = parseInt(position[1]);
  
  return file >= 'a' && file <= 'i' && rank >= 0 && rank <= 9;
}

/**
 * 位置字符串转换为坐标
 * @param position 位置字符串
 * @returns 坐标 [file, rank]
 */
export function positionToCoords(position: string): [number, number] {
  const file = position.charCodeAt(0) - 'a'.charCodeAt(0);
  const rank = parseInt(position[1]);
  return [file, rank];
}

/**
 * 坐标转换为位置字符串
 * @param file 列索引 (0-8)
 * @param rank 行索引 (0-9)
 * @returns 位置字符串
 */
export function coordsToPosition(file: number, rank: number): string {
  return `${String.fromCharCode('a'.charCodeAt(0) + file)}${rank}`;
}
