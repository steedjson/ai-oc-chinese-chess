/**
 * FEN 工具测试
 */

import { describe, it, expect } from 'vitest';
import { 
  parseFen, 
  generateFen, 
  parseFenToBoardState, 
  INITIAL_FEN,
  getPieceChineseName,
  isValidPosition,
  positionToCoords,
  coordsToPosition
} from './fen';

describe('FEN Utils', () => {
  it('应该能解析初始 FEN', () => {
    const pieces = parseFen(INITIAL_FEN);
    expect(pieces.length).toBe(32);
    
    // 检查红帥
    const redKing = pieces.find(p => p.type === 'king' && p.color === 'red');
    expect(redKing?.position).toBe('e0');
    
    // 检查黑將
    const blackKing = pieces.find(p => p.type === 'king' && p.color === 'black');
    expect(blackKing?.position).toBe('e9');
  });

  it('应该能从 pieces 生成 FEN', () => {
    const pieces = parseFen(INITIAL_FEN);
    const fen = generateFen(pieces);
    // 比较 FEN 的棋盘部分 (第一个空格前)
    expect(fen).toBe(INITIAL_FEN.split(' ')[0]);
  });

  it('应该能解析为 BoardState', () => {
    const state = parseFenToBoardState(INITIAL_FEN);
    expect(state.turn).toBe('red');
    expect(state.pieces.length).toBe(32);
  });

  it('应该返回正确的中文名称', () => {
    expect(getPieceChineseName({ type: 'king', color: 'red', position: 'e0' })).toBe('帥');
    expect(getPieceChineseName({ type: 'king', color: 'black', position: 'e9' })).toBe('將');
    expect(getPieceChineseName({ type: 'pawn', color: 'red', position: 'a3' })).toBe('兵');
    expect(getPieceChineseName({ type: 'pawn', color: 'black', position: 'a6' })).toBe('卒');
  });

  it('应该验证位置合法性', () => {
    expect(isValidPosition('e2')).toBe(true);
    expect(isValidPosition('a0')).toBe(true);
    expect(isValidPosition('i9')).toBe(true);
    expect(isValidPosition('j2')).toBe(false);
    expect(isValidPosition('e10')).toBe(false);
    expect(isValidPosition('e')).toBe(false);
  });

  it('坐标与字符串转换', () => {
    expect(positionToCoords('e2')).toEqual([4, 2]);
    expect(coordsToPosition(4, 2)).toBe('e2');
    expect(coordsToPosition(0, 0)).toBe('a0');
    expect(coordsToPosition(8, 9)).toBe('i9');
  });
});
