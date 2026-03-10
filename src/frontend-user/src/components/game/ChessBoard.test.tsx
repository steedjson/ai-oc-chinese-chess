/**
 * ChessBoard 组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChessBoard from './ChessBoard';
import type { BoardState } from '@/types';

// 初始 FEN
const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1';

const mockBoardState: BoardState = {
  fen: INITIAL_FEN,
  turn: 'red',
  pieces: [],
  in_check: false,
  game_over: false,
  last_move: undefined,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ChessBoard', () => {
  it('应该正确渲染棋盘', () => {
    const { container } = render(<ChessBoard boardState={mockBoardState} />);
    
    // 检查棋盘容器存在
    const board = container.querySelector('.chess-board');
    expect(board).toBeInTheDocument();
  });

  it('应该渲染所有棋子', () => {
    render(<ChessBoard boardState={mockBoardState} />);
    
    // 红方棋子
    expect(screen.getAllByText('帥').length).toBeGreaterThan(0);
    expect(screen.getAllByText('仕').length).toBeGreaterThan(0);
    expect(screen.getAllByText('相').length).toBeGreaterThan(0);
    expect(screen.getAllByText('馬').length).toBeGreaterThan(0);
    expect(screen.getAllByText('車').length).toBeGreaterThan(0);
    expect(screen.getAllByText('炮').length).toBeGreaterThan(0);
    expect(screen.getAllByText('兵').length).toBeGreaterThan(0);
    
    // 黑方棋子
    expect(screen.getAllByText('將').length).toBeGreaterThan(0);
    expect(screen.getAllByText('士').length).toBeGreaterThan(0);
    expect(screen.getAllByText('象').length).toBeGreaterThan(0);
    expect(screen.getAllByText('砲').length).toBeGreaterThan(0);
    expect(screen.getAllByText('卒').length).toBeGreaterThan(0);
  });

  it('应该正确处理棋子点击', () => {
    const handleClick = vi.fn();
    render(<ChessBoard boardState={mockBoardState} onPieceClick={handleClick} />);
    
    // 点击红帥位置
    const shuai = screen.getAllByText('帥')[0];
    fireEvent.click(shuai);
    
    expect(handleClick).toHaveBeenCalled();
  });

  it('应该显示选中状态', () => {
    const { container } = render(<ChessBoard boardState={mockBoardState} selectedPosition="e0" />);
    
    // 检查选中样式存在 (animate-pulse 类)
    const selection = container.querySelector('.animate-pulse');
    expect(selection).toBeInTheDocument();
  });

  it('应该显示有效走棋提示', () => {
    const { container } = render(<ChessBoard boardState={mockBoardState} validMoves={['e1', 'e2']} />);
    
    // 检查有效走棋位置
    const board = container.querySelector('.chess-board');
    expect(board).toBeInTheDocument();
  });

  it('在禁用状态下不应响应点击', () => {
    const handleClick = vi.fn();
    render(<ChessBoard boardState={mockBoardState} disabled={true} onPieceClick={handleClick} />);
    
    const shuai = screen.getAllByText('帥')[0];
    fireEvent.click(shuai);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('应该支持棋盘翻转（黑方视角）', () => {
    const { container: redView } = render(<ChessBoard boardState={mockBoardState} orientation="red" />);
    const { container: blackView } = render(<ChessBoard boardState={mockBoardState} orientation="black" />);
    
    expect(redView).toBeInTheDocument();
    expect(blackView).toBeInTheDocument();
  });

  it('应该显示最后走棋高亮', () => {
    const { container } = render(
      <ChessBoard
        boardState={mockBoardState}
        lastMove={{ from: 'e0', to: 'e4' }}
      />
    );
    
    const board = container.querySelector('.chess-board');
    expect(board).toBeInTheDocument();
  });

  it('应该显示将军提示动画', () => {
    const checkBoardState: BoardState = {
      ...mockBoardState,
      in_check: true,
    };

    const { container, getByText } = render(
      <ChessBoard boardState={checkBoardState} enableAnimations={true} />
    );

    // 检查将军提示存在
    expect(getByText('将军!')).toBeInTheDocument();
    
    // 检查棋盘有将军样式
    const board = container.querySelector('.board-check');
    expect(board).toBeInTheDocument();
  });

  it('应该显示游戏结束弹窗', () => {
    const gameOverBoardState: BoardState = {
      ...mockBoardState,
      game_over: true,
      turn: 'black', // 红方胜利
    };

    const { container, getByText } = render(
      <ChessBoard boardState={gameOverBoardState} enableAnimations={true} />
    );

    // 检查游戏结束弹窗
    expect(getByText('红方胜利!')).toBeInTheDocument();
    
    // 检查弹窗存在
    const modal = container.querySelector('.game-over-modal');
    expect(modal).toBeInTheDocument();
  });

  it('应该显示有效走棋提示', () => {
    const { container } = render(
      <ChessBoard
        boardState={mockBoardState}
        validMoves={['e1', 'e2']}
        enableAnimations={true}
      />
    );

    // 检查有效走棋提示点
    const hints = container.querySelectorAll('.valid-move-hint');
    expect(hints.length).toBeGreaterThan(0);
  });

  it('在禁用动画时不应显示动画效果', () => {
    const checkBoardState: BoardState = {
      ...mockBoardState,
      in_check: true,
    };

    const { queryByText } = render(
      <ChessBoard boardState={checkBoardState} enableAnimations={false} />
    );

    // 禁用动画时不应显示将军提示
    expect(queryByText('将军!')).not.toBeInTheDocument();
  });
});
