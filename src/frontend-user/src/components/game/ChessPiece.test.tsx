/**
 * ChessPiece 组件测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ChessPiece from './ChessPiece';
import type { Piece } from '@/types';

describe('ChessPiece', () => {
  const createPiece = (type: Piece['type'], color: Piece['color']): Piece => ({
    type,
    color,
    position: 'e0',
  });

  it('应该正确渲染红方棋子', () => {
    const piece = createPiece('king', 'red');
    render(<ChessPiece piece={piece} />);
    
    expect(screen.getByText('帥')).toBeInTheDocument();
  });

  it('应该正确渲染黑方棋子', () => {
    const piece = createPiece('king', 'black');
    render(<ChessPiece piece={piece} />);
    
    expect(screen.getByText('將')).toBeInTheDocument();
  });

  it('应该渲染所有类型的棋子', () => {
    const pieces: Array<{ type: Piece['type']; char: string }> = [
      { type: 'king', char: '帥' },
      { type: 'advisor', char: '仕' },
      { type: 'elephant', char: '相' },
      { type: 'horse', char: '馬' },
      { type: 'rook', char: '車' },
      { type: 'cannon', char: '炮' },
      { type: 'pawn', char: '兵' },
    ];

    pieces.forEach(({ type, char }) => {
      const { container } = render(<ChessPiece piece={createPiece(type, 'red')} />);
      expect(container).toHaveTextContent(char);
    });
  });

  it('应该显示选中状态', () => {
    const piece = createPiece('king', 'red');
    const { container } = render(<ChessPiece piece={piece} isSelected={true} />);
    
    const pieceElement = container.querySelector('.chess-piece');
    expect(pieceElement).toHaveClass('selected');
  });

  it('应该显示最后走棋状态', () => {
    const piece = createPiece('king', 'red');
    const { container } = render(<ChessPiece piece={piece} isLastMove={true} />);
    
    const pieceElement = container.querySelector('.chess-piece');
    expect(pieceElement).toHaveClass('last-move');
  });

  it('应该处理点击事件', () => {
    const handleClick = vi.fn();
    const piece = createPiece('king', 'red');
    
    render(<ChessPiece piece={piece} onClick={handleClick} />);
    
    fireEvent.click(screen.getByText('帥'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('在禁用状态下不应响应点击', () => {
    const handleClick = vi.fn();
    const piece = createPiece('king', 'red');
    
    render(<ChessPiece piece={piece} disabled={true} onClick={handleClick} />);
    
    fireEvent.click(screen.getByText('帥'));
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('应该有正确的样式类', () => {
    const piece = createPiece('king', 'red');
    const { container } = render(<ChessPiece piece={piece} />);
    
    const pieceElement = container.querySelector('.chess-piece');
    expect(pieceElement).toHaveClass('rounded-full');
  });

  it('红方棋子应该有红色渐变背景', () => {
    const piece = createPiece('king', 'red');
    const { container } = render(<ChessPiece piece={piece} />);
    
    const pieceElement = container.querySelector('.chess-piece') as HTMLElement;
    expect(pieceElement.style.background).toContain('radial-gradient');
  });

  it('黑方棋子应该有灰色渐变背景', () => {
    const piece = createPiece('king', 'black');
    const { container } = render(<ChessPiece piece={piece} />);
    
    const pieceElement = container.querySelector('.chess-piece') as HTMLElement;
    expect(pieceElement.style.background).toContain('radial-gradient');
  });

  it('应该有悬停效果', () => {
    const piece = createPiece('king', 'red');
    const { container } = render(<ChessPiece piece={piece} />);
    
    const pieceElement = container.querySelector('.chess-piece');
    expect(pieceElement).toHaveClass('hover:scale-105');
  });

  it('选中时应该有脉冲动画', () => {
    const piece = createPiece('king', 'red');
    render(<ChessPiece piece={piece} isSelected={true} />);
    
    const textElement = screen.getByText('帥');
    expect(textElement).toHaveClass('animate-pulse');
  });
});
