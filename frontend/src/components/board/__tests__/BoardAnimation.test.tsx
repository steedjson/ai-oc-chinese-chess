/**
 * BoardAnimation.tsx 组件测试
 * 
 * 测试覆盖:
 * - CheckAnimation 组件
 * - GameEndAnimation 组件
 * - CaptureAnimation 组件
 * - AnimationPanel 组件
 * - BoardAnimationContainer 组件
 */

import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import {
  CheckAnimation,
  GameEndAnimation,
  CaptureAnimation,
  AnimationPanel,
  BoardAnimationContainer,
} from '../BoardAnimation';

// ============ CheckAnimation 组件测试 ============

describe('CheckAnimation Component', () => {
  it('应该在非将军状态时不渲染', () => {
    const { container } = render(<CheckAnimation isCheck={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用动画时不渲染', () => {
    const { container } = render(
      <CheckAnimation
        isCheck={true}
        config={{
          enabled: false,
          moveAnimation: true,
          captureAnimation: true,
          checkAnimation: false,
          gameEndAnimation: true,
          speedMultiplier: 1.0,
        }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该在将军时显示动画', async () => {
    const { container, rerender } = render(<CheckAnimation isCheck={false} />);
    expect(container.firstChild).toBeNull();

    rerender(<CheckAnimation isCheck={true} />);

    // 等待动画显示
    await waitFor(() => {
      const checkAnimation = container.querySelector('.check-animation');
      expect(checkAnimation).toBeInTheDocument();
    }, { timeout: 100 });

    // 验证将军文本
    const checkText = container.querySelector('.check-text');
    expect(checkText?.textContent).toBe('将军!');
  });

  it('应该支持不同阵营的将军', async () => {
    const { container, rerender } = render(<CheckAnimation isCheck={true} checkSide="red" />);
    
    await waitFor(() => {
      expect(container.querySelector('.check-animation')).toHaveClass('red');
    }, { timeout: 100 });

    rerender(<CheckAnimation isCheck={true} checkSide="black" />);
    
    await waitFor(() => {
      expect(container.querySelector('.check-animation')).toHaveClass('black');
    }, { timeout: 100 });
  });

  it('应该在动画时间后自动隐藏', async () => {
    jest.useFakeTimers();
    
    const { container } = render(<CheckAnimation isCheck={true} />);
    
    // 等待动画显示
    await waitFor(() => {
      expect(container.querySelector('.check-animation')).toBeInTheDocument();
    }, { timeout: 100 });

    // 快进时间
    act(() => {
      jest.advanceTimersByTime(2000);
    });

    // 动画应该已隐藏
    await waitFor(() => {
      expect(container.querySelector('.check-animation')).not.toBeInTheDocument();
    }, { timeout: 100 });

    jest.useRealTimers();
  });
});

// ============ GameEndAnimation 组件测试 ============

describe('GameEndAnimation Component', () => {
  it('应该在游戏未结束时不渲染', () => {
    const { container } = render(<GameEndAnimation isGameOver={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用动画时不渲染', () => {
    const { container } = render(
      <GameEndAnimation
        isGameOver={true}
        config={{
          enabled: false,
          moveAnimation: true,
          captureAnimation: true,
          checkAnimation: true,
          gameEndAnimation: false,
          speedMultiplier: 1.0,
        }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该显示游戏结束消息', async () => {
    const { container } = render(<GameEndAnimation isGameOver={true} />);

    await waitFor(() => {
      const message = container.querySelector('.game-end-message');
      expect(message).toBeInTheDocument();
    }, { timeout: 100 });

    expect(container.querySelector('.message-text')?.textContent).toBe('游戏结束');
  });

  it('应该显示和棋消息', async () => {
    const { container } = render(
      <GameEndAnimation isGameOver={true} winner="draw" />
    );

    await waitFor(() => {
      expect(container.querySelector('.message-text')?.textContent).toBe('和棋!');
    }, { timeout: 100 });

    // 和棋应该显示握手图标
    expect(container.querySelector('.message-icon')?.textContent).toBe('🤝');
  });

  it('应该显示红方胜利消息', async () => {
    const { container } = render(
      <GameEndAnimation 
        isGameOver={true} 
        winner="red" 
        winReason="checkmate"
      />
    );

    await waitFor(() => {
      const message = container.querySelector('.message-text');
      expect(message?.textContent).toContain('红方胜利!');
      expect(message?.textContent).toContain('将死');
    }, { timeout: 100 });

    // 应该有彩带效果
    expect(container.querySelector('.confetti-container')).toBeInTheDocument();
  });

  it('应该显示黑方胜利消息', async () => {
    const { container } = render(
      <GameEndAnimation 
        isGameOver={true} 
        winner="black" 
        winReason="resign"
      />
    );

    await waitFor(() => {
      const message = container.querySelector('.message-text');
      expect(message?.textContent).toContain('黑方胜利!');
      expect(message?.textContent).toContain('认输');
    }, { timeout: 100 });
  });

  it('应该支持不同的获胜原因', async () => {
    const reasons = [
      { reason: 'checkmate' as const, text: '将死' },
      { reason: 'stalemate' as const, text: '困毙' },
      { reason: 'resign' as const, text: '认输' },
      { reason: 'timeout' as const, text: '超时' },
    ];

    for (const { reason, text } of reasons) {
      const { container, unmount } = render(
        <GameEndAnimation 
          isGameOver={true} 
          winner="red" 
          winReason={reason}
        />
      );

      await waitFor(() => {
        expect(container.querySelector('.message-text')?.textContent).toContain(text);
      }, { timeout: 100 });

      unmount();
    }
  });
});

// ============ CaptureAnimation 组件测试 ============

describe('CaptureAnimation Component', () => {
  it('应该在非吃子状态时不渲染', () => {
    const { container } = render(<CaptureAnimation isCapturing={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用动画时不渲染', () => {
    const { container } = render(
      <CaptureAnimation
        isCapturing={true}
        config={{
          enabled: false,
          moveAnimation: true,
          captureAnimation: false,
          checkAnimation: true,
          gameEndAnimation: true,
          speedMultiplier: 1.0,
        }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该在吃子时显示动画效果', async () => {
    const { container } = render(<CaptureAnimation isCapturing={true} />);

    await waitFor(() => {
      const captureEffect = container.querySelector('.capture-effect');
      expect(captureEffect).toBeInTheDocument();
    }, { timeout: 100 });

    // 应该有爆炸效果
    expect(container.querySelector('.capture-explosion')).toBeInTheDocument();
  });

  it('应该渲染火花特效', async () => {
    const { container } = render(<CaptureAnimation isCapturing={true} />);

    await waitFor(() => {
      const sparks = container.querySelectorAll('.spark');
      expect(sparks.length).toBeGreaterThan(0);
    }, { timeout: 100 });
  });

  it('应该在动画时间后自动隐藏', async () => {
    jest.useFakeTimers();
    
    const { container } = render(<CaptureAnimation isCapturing={true} />);
    
    // 等待动画显示
    await waitFor(() => {
      expect(container.querySelector('.capture-effect')).toBeInTheDocument();
    }, { timeout: 100 });

    // 快进时间
    act(() => {
      jest.advanceTimersByTime(800);
    });

    // 动画应该已隐藏
    await waitFor(() => {
      expect(container.querySelector('.capture-effect')).not.toBeInTheDocument();
    }, { timeout: 100 });

    jest.useRealTimers();
  });
});

// ============ AnimationPanel 组件测试 ============

describe('AnimationPanel Component', () => {
  const mockConfig = {
    enabled: true,
    moveAnimation: true,
    captureAnimation: true,
    checkAnimation: true,
    gameEndAnimation: true,
    speedMultiplier: 1.0,
  };

  it('应该渲染动画设置按钮', () => {
    const { container } = render(
      <AnimationPanel
        config={mockConfig}
        onChange={jest.fn()}
      />
    );

    expect(container.querySelector('.animation-toggle-btn')).toBeInTheDocument();
  });

  it('应该可以打开设置面板', () => {
    const { container } = render(
      <AnimationPanel
        config={mockConfig}
        onChange={jest.fn()}
      />
    );

    const toggleBtn = container.querySelector('.animation-toggle-btn');
    fireEvent.click(toggleBtn!);

    expect(container.querySelector('.animation-settings')).toBeInTheDocument();
  });

  it('应该可以切换启用动画', () => {
    const onChange = jest.fn();
    const { container } = render(
      <AnimationPanel
        config={mockConfig}
        onChange={onChange}
      />
    );

    // 打开面板
    fireEvent.click(container.querySelector('.animation-toggle-btn')!);

    // 找到启用动画的 checkbox
    const enabledCheckbox = container.querySelector('input[type="checkbox"]');
    fireEvent.click(enabledCheckbox!);

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: false })
    );
  });

  it('应该可以切换各个动画选项', () => {
    const onChange = jest.fn();
    const { container } = render(
      <AnimationPanel
        config={mockConfig}
        onChange={onChange}
      />
    );

    // 打开面板
    fireEvent.click(container.querySelector('.animation-toggle-btn')!);

    // 找到所有 checkbox
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    
    // 切换走棋动画 (第二个 checkbox)
    fireEvent.click(checkboxes[1]);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ moveAnimation: false, enabled: true })
    );

    // 切换吃子动画 (第三个 checkbox)
    fireEvent.click(checkboxes[2]);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ captureAnimation: false, enabled: true })
    );
  });

  it('应该在总开关禁用时禁用其他选项', () => {
    const onChange = jest.fn();
    const disabledConfig = { ...mockConfig, enabled: false };
    const { container } = render(
      <AnimationPanel
        config={disabledConfig}
        onChange={onChange}
      />
    );

    // 打开面板
    fireEvent.click(container.querySelector('.animation-toggle-btn')!);

    // 找到所有 checkbox
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    
    // 除第一个外，其他应该都被禁用
    for (let i = 1; i < checkboxes.length; i++) {
      expect(checkboxes[i]).toBeDisabled();
    }
  });

  it('应该可以调整动画速度', () => {
    const onChange = jest.fn();
    const { container } = render(
      <AnimationPanel
        config={mockConfig}
        onChange={onChange}
      />
    );

    // 打开面板
    fireEvent.click(container.querySelector('.animation-toggle-btn')!);

    // 找到速度滑块
    const speedSlider = container.querySelector('input[type="range"]') as HTMLInputElement;
    fireEvent.change(speedSlider, { target: { value: '1.5' } });

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ speedMultiplier: 1.5 })
    );
  });

  it('应该可以恢复默认设置', () => {
    const onChange = jest.fn();
    const { container } = render(
      <AnimationPanel
        config={{ ...mockConfig, enabled: false, speedMultiplier: 2.0 }}
        onChange={onChange}
      />
    );

    // 打开面板
    fireEvent.click(container.querySelector('.animation-toggle-btn')!);

    // 点击恢复默认按钮
    const resetBtn = container.querySelector('.reset-btn');
    fireEvent.click(resetBtn!);

    expect(onChange).toHaveBeenCalledWith({
      enabled: true,
      moveAnimation: true,
      captureAnimation: true,
      checkAnimation: true,
      gameEndAnimation: true,
      speedMultiplier: 1.0,
    });
  });
});

// ============ BoardAnimationContainer 组件测试 ============

describe('BoardAnimationContainer Component', () => {
  const mockCheckConfig = { isCheck: true, checkSide: 'red' as const };
  const mockGameEndConfig = { isGameOver: true, winner: 'red' as const };
  const mockCaptureConfig = { isCapturing: true };

  it('应该渲染子组件', () => {
    const { container } = render(
      <BoardAnimationContainer>
        <div className="board">Board Content</div>
      </BoardAnimationContainer>
    );

    expect(container.querySelector('.board')).toBeInTheDocument();
    expect(container.querySelector('.board-animation-container')).toBeInTheDocument();
  });

  it('应该渲染将军动画', async () => {
    const { container } = render(
      <BoardAnimationContainer checkConfig={mockCheckConfig}>
        <div>Board</div>
      </BoardAnimationContainer>
    );

    await waitFor(() => {
      expect(container.querySelector('.check-animation')).toBeInTheDocument();
    }, { timeout: 100 });
  });

  it('应该渲染游戏结束动画', async () => {
    const { container } = render(
      <BoardAnimationContainer gameEndConfig={mockGameEndConfig}>
        <div>Board</div>
      </BoardAnimationContainer>
    );

    await waitFor(() => {
      expect(container.querySelector('.game-end-animation')).toBeInTheDocument();
    }, { timeout: 100 });
  });

  it('应该渲染吃子动画', async () => {
    const { container } = render(
      <BoardAnimationContainer captureConfig={mockCaptureConfig}>
        <div>Board</div>
      </BoardAnimationContainer>
    );

    await waitFor(() => {
      expect(container.querySelector('.capture-animation')).toBeInTheDocument();
    }, { timeout: 100 });
  });

  it('应该渲染动画设置面板', () => {
    const onConfigChange = jest.fn();
    const { container } = render(
      <BoardAnimationContainer
        animationConfig={{
          enabled: true,
          moveAnimation: true,
          captureAnimation: true,
          checkAnimation: true,
          gameEndAnimation: true,
          speedMultiplier: 1.0,
        }}
        onConfigChange={onConfigChange}
      >
        <div>Board</div>
      </BoardAnimationContainer>
    );

    expect(container.querySelector('.animation-panel')).toBeInTheDocument();
  });

  it('应该同时渲染多个动画', async () => {
    const { container } = render(
      <BoardAnimationContainer
        checkConfig={mockCheckConfig}
        gameEndConfig={mockGameEndConfig}
        captureConfig={mockCaptureConfig}
      >
        <div>Board</div>
      </BoardAnimationContainer>
    );

    await waitFor(() => {
      expect(container.querySelector('.check-animation')).toBeInTheDocument();
      expect(container.querySelector('.game-end-animation')).toBeInTheDocument();
      expect(container.querySelector('.capture-animation')).toBeInTheDocument();
    }, { timeout: 100 });
  });
});
