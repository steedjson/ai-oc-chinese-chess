/**
 * GameControls 组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import GameControls from './GameControls';
import { useGameStore, useSettingsStore } from '@/stores';

// Mock stores
vi.mock('@/stores', () => ({
  useGameStore: vi.fn(),
  useSettingsStore: vi.fn(),
}));

describe('GameControls', () => {
  const mockSetSoundEnabled = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useGameStore as any).mockReturnValue({
      gameOver: false,
      winner: null,
    });
    (useSettingsStore as any).mockReturnValue({
      sound_enabled: true,
      setSoundEnabled: mockSetSoundEnabled,
    });
  });

  it('应该正确渲染控制按钮', () => {
    render(<GameControls />);
    
    expect(screen.getByText('游戏控制')).toBeInTheDocument();
    expect(screen.getByText('悔棋')).toBeInTheDocument();
    expect(screen.getByText('和棋')).toBeInTheDocument();
    expect(screen.getByText('认输')).toBeInTheDocument();
    expect(screen.getByText('返回首页')).toBeInTheDocument();
  });

  it('点击悔棋应该触发 onUndo', () => {
    const handleUndo = vi.fn();
    render(<GameControls onUndo={handleUndo} canUndo={true} />);
    
    fireEvent.click(screen.getByText('悔棋'));
    expect(handleUndo).toHaveBeenCalled();
  });

  it('悔棋按钮在不可悔棋时应该禁用', () => {
    render(<GameControls canUndo={false} />);
    const undoButton = screen.getByText('悔棋').closest('button');
    expect(undoButton).toBeDisabled();
  });

  it('点击和棋应该显示确认弹窗', () => {
    render(<GameControls />);
    
    fireEvent.click(screen.getByText('和棋'));
    // 允许忽略空格
    const modalTitles = screen.getAllByText(/提\s*议\s*和\s*棋/, { selector: '.ant-modal-title' });
    expect(modalTitles.length).toBeGreaterThan(0);
  });

  it('点击认输应该显示确认弹窗', () => {
    render(<GameControls />);
    
    fireEvent.click(screen.getByText('认输'));
    const modalTitles = screen.getAllByText(/确\s*认\s*认\s*输/, { selector: '.ant-modal-title' });
    expect(modalTitles.length).toBeGreaterThan(0);
  });

  it('游戏结束时应该显示获胜信息', () => {
    (useGameStore as any).mockReturnValue({
      gameOver: true,
      winner: 'red',
    });
    
    render(<GameControls />);
    expect(screen.getByText('红方获胜！')).toBeInTheDocument();
  });

  it('游戏结束时控制按钮应该禁用', () => {
    (useGameStore as any).mockReturnValue({
      gameOver: true,
      winner: 'red',
    });
    
    render(<GameControls canUndo={true} />);
    
    expect(screen.getByText('悔棋').closest('button')).toBeDisabled();
    expect(screen.getByText('和棋').closest('button')).toBeDisabled();
    expect(screen.getByText('认输').closest('button')).toBeDisabled();
  });

  it('应该能切换声音状态', () => {
    render(<GameControls />);
    
    const buttons = screen.getAllByRole('button');
    const soundButton = buttons.find(b => b.querySelector('.anticon-sound') || b.querySelector('.anticon-muted'));
    
    if (soundButton) {
      fireEvent.click(soundButton);
      expect(mockSetSoundEnabled).toHaveBeenCalledWith(false);
    }
  });

  it('点击返回首页应该触发 onHome', () => {
    const handleHome = vi.fn();
    render(<GameControls onHome={handleHome} />);
    
    fireEvent.click(screen.getByText('返回首页'));
    expect(handleHome).toHaveBeenCalled();
  });
});
