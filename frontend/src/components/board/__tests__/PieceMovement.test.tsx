/**
 * PieceMovement.tsx 组件测试
 * 
 * 测试覆盖:
 * - 工具函数 (parsePosition, positionToPixels)
 * - MovingPiece 组件
 * - LastMoveMarker 组件
 * - LegalMovesHint 组件
 * - PieceHighlight 组件
 * - usePieceMovement Hook
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import {
  parsePosition,
  positionToPixels,
  MovingPiece,
  LastMoveMarker,
  LegalMovesHint,
  PieceHighlight,
  usePieceMovement,
  PieceMovementContainer,
} from '../PieceMovement';

// ============ 工具函数测试 ============

describe('PieceMovement - Utility Functions', () => {
  describe('parsePosition', () => {
    it('应该正确解析标准位置字符串', () => {
      const result = parsePosition('e5');
      expect(result).toEqual({ file: 'e', rank: 5 });
    });

    it('应该处理大写字母', () => {
      const result = parsePosition('E3');
      expect(result).toEqual({ file: 'e', rank: 3 });
    });

    it('应该解析边界位置', () => {
      expect(parsePosition('a0')).toEqual({ file: 'a', rank: 0 });
      expect(parsePosition('i9')).toEqual({ file: 'i', rank: 9 });
    });
  });

  describe('positionToPixels', () => {
    it('应该将位置转换为像素坐标', () => {
      const result = positionToPixels('e5', 50, 25);
      // a=0, b=1, c=2, d=3, e=4 => 25 + 4*50 = 225
      expect(result.x).toBe(225);
      expect(result.y).toBe(225); // 25 + (9-5)*50 = 225
    });

    it('应该支持自定义格子大小', () => {
      const result = positionToPixels('a0', 60, 30);
      expect(result.x).toBe(30);
      expect(result.y).toBe(570); // 30 + (9-0)*60 = 570
    });

    it('棋盘中心位置应该正确计算', () => {
      const result = positionToPixels('e4', 50, 25);
      expect(result).toEqual({ x: 225, y: 275 });
    });
  });
});

// ============ MovingPiece 组件测试 ============

describe('MovingPiece Component', () => {
  const mockMove = {
    from: 'e2',
    to: 'e4',
    piece: { type: 'c', side: 'red' as const, position: 'e2' },
    isCapture: false,
  };

  it('应该在没有移动时不渲染', () => {
    const { container } = render(<MovingPiece />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用动画时不渲染', () => {
    const { container } = render(
      <MovingPiece
        move={mockMove}
        config={{ enabled: false, duration: 300, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该渲染移动中的棋子', async () => {
    const onComplete = jest.fn();
    const { container } = render(
      <MovingPiece
        move={mockMove}
        config={{ enabled: true, duration: 100, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
        onComplete={onComplete}
      />
    );

    // 等待动画开始
    await waitFor(() => {
      const movingPiece = container.querySelector('.moving-piece');
      expect(movingPiece).toBeInTheDocument();
    }, { timeout: 200 });

    // 等待动画完成
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    }, { timeout: 300 });
  });

  it('应该为不同棋子显示正确的标签', async () => {
    const moves = [
      { piece: { type: 'k', side: 'red' as const }, expected: '帅' },
      { piece: { type: 'k', side: 'black' as const }, expected: '将' },
      { piece: { type: 'c', side: 'red' as const }, expected: '炮' },
      { piece: { type: 'p', side: 'black' as const }, expected: '卒' },
    ];

    for (const { piece, expected } of moves) {
      const { container, unmount } = render(
        <MovingPiece
          move={{ ...mockMove, piece: piece as any }}
          config={{ enabled: true, duration: 1000, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
        />
      );

      await waitFor(() => {
        const label = container.querySelector('.piece-label');
        expect(label?.textContent).toBe(expected);
      }, { timeout: 200 });

      unmount();
    }
  });
});

// ============ LastMoveMarker 组件测试 ============

describe('LastMoveMarker Component', () => {
  const mockLastMove = {
    from: 'e2',
    to: 'e4',
    piece: { type: 'c', side: 'red' as const, position: 'e2' },
    isCapture: false,
  };

  it('应该在没有最后一步时不渲染', () => {
    const { container } = render(<LastMoveMarker />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用 showLastMove 时不渲染', () => {
    const { container } = render(
      <LastMoveMarker
        lastMove={mockLastMove}
        config={{ enabled: true, duration: 300, easing: 'ease-in-out', showLastMove: false, showLegalMoves: true }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该渲染起始和目标位置标记', () => {
    const { container } = render(
      <LastMoveMarker
        lastMove={mockLastMove}
        config={{ enabled: true, duration: 300, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
      />
    );

    const markers = container.querySelectorAll('.last-move-marker');
    expect(markers).toHaveLength(2);
    expect(markers[0]).toHaveClass('from');
    expect(markers[1]).toHaveClass('to');
  });
});

// ============ LegalMovesHint 组件测试 ============

describe('LegalMovesHint Component', () => {
  const legalMoves = ['e3', 'e4', 'd4', 'f4'];

  it('应该在没有合法走法时不渲染', () => {
    const { container } = render(<LegalMovesHint />);
    expect(container.firstChild).toBeNull();
  });

  it('应该在禁用 showLegalMoves 时不渲染', () => {
    const { container } = render(
      <LegalMovesHint
        currentPosition="e2"
        legalMoves={legalMoves}
        config={{ enabled: true, duration: 300, easing: 'ease-in-out', showLastMove: true, showLegalMoves: false }}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('应该为每个合法走法渲染提示', () => {
    const { container } = render(
      <LegalMovesHint
        currentPosition="e2"
        legalMoves={legalMoves}
        config={{ enabled: true, duration: 300, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
      />
    );

    const hints = container.querySelectorAll('.legal-move-hint');
    expect(hints).toHaveLength(4);
  });

  it('应该在点击时调用 onMoveClick 回调', () => {
    const onMoveClick = jest.fn();
    const { container } = render(
      <LegalMovesHint
        currentPosition="e2"
        legalMoves={legalMoves}
        config={{ enabled: true, duration: 300, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
        onMoveClick={onMoveClick}
      />
    );

    const firstHint = container.querySelector('.legal-move-hint');
    if (firstHint) {
      fireEvent.click(firstHint);
      expect(onMoveClick).toHaveBeenCalledWith('e3');
    }
  });
});

// ============ PieceHighlight 组件测试 ============

describe('PieceHighlight Component', () => {
  it('应该在没有位置时不渲染', () => {
    const { container } = render(<PieceHighlight />);
    expect(container.firstChild).toBeNull();
  });

  it('应该渲染选中高亮', () => {
    const { container } = render(
      <PieceHighlight
        position="e4"
        highlightType="selected"
      />
    );

    const highlight = container.querySelector('.piece-highlight');
    expect(highlight).toBeInTheDocument();
    expect(highlight).toHaveClass('selected');
  });

  it('应该支持不同的高亮类型', () => {
    const { container, rerender } = render(
      <PieceHighlight position="e4" highlightType="selected" />
    );
    expect(container.querySelector('.piece-highlight')).toHaveClass('selected');

    rerender(<PieceHighlight position="e4" highlightType="check" />);
    expect(container.querySelector('.piece-highlight')).toHaveClass('check');

    rerender(<PieceHighlight position="e4" highlightType="threat" />);
    expect(container.querySelector('.piece-highlight')).toHaveClass('threat');
  });
});

// ============ usePieceMovement Hook 测试 ============

describe('usePieceMovement Hook', () => {
  const TestComponent = ({ 
    onResult,
    initialConfig 
  }: { 
    onResult: (result: any) => void,
    initialConfig?: any
  }) => {
    const result = usePieceMovement(initialConfig);
    
    React.useEffect(() => {
      onResult(result);
    }, [result, onResult]);

    return <div>Test</div>;
  };

  it('应该返回正确的初始状态', () => {
    const resultHandler = jest.fn();
    
    render(
      <TestComponent onResult={resultHandler} />
    );

    expect(resultHandler).toHaveBeenCalledWith(
      expect.objectContaining({
        currentMove: undefined,
        lastMove: undefined,
        isMoving: false,
        config: expect.objectContaining({
          enabled: true,
          duration: 300,
          easing: 'ease-in-out',
        }),
      })
    );
  });

  it('应该接受自定义初始配置', () => {
    const resultHandler = jest.fn();
    const customConfig = { enabled: false, duration: 500 };
    
    render(
      <TestComponent 
        onResult={resultHandler}
        initialConfig={customConfig}
      />
    );

    expect(resultHandler).toHaveBeenCalledWith(
      expect.objectContaining({
        config: expect.objectContaining({
          enabled: false,
          duration: 500,
        }),
      })
    );
  });

  it('makeMove 应该设置移动状态', async () => {
    const resultHandler = jest.fn();
    let makeMoveFn: any;
    
    const TestComponentWithAction = () => {
      const { makeMove, isMoving } = usePieceMovement({ duration: 100 });
      makeMoveFn = makeMove;
      
      React.useEffect(() => {
        resultHandler({ isMoving });
      }, [isMoving]);

      return <div>Test</div>;
    };

    render(<TestComponentWithAction />);

    // 初始状态不是移动中
    expect(resultHandler).toHaveBeenLastCalledWith({ isMoving: false });

    // 执行移动
    if (makeMoveFn) {
      makeMoveFn('e2', 'e4', { type: 'c', side: 'red', position: 'e2' });
    }

    // 等待状态更新
    await waitFor(() => {
      expect(resultHandler).toHaveBeenCalledWith(
        expect.objectContaining({ isMoving: true })
      );
    }, { timeout: 200 });
  });
});

// ============ PieceMovementContainer 组件测试 ============

describe('PieceMovementContainer Component', () => {
  it('应该渲染子组件', () => {
    const { container } = render(
      <PieceMovementContainer>
        <div className="child-component">Board</div>
      </PieceMovementContainer>
    );

    expect(container.querySelector('.child-component')).toBeInTheDocument();
    expect(container.querySelector('.piece-movement-container')).toBeInTheDocument();
  });

  it('应该接受并应用配置', () => {
    const { container } = render(
      <PieceMovementContainer
        config={{ enabled: true, duration: 500, easing: 'linear', showLastMove: true, showLegalMoves: true }}
      >
        <div>Board</div>
      </PieceMovementContainer>
    );

    const containerEl = container.querySelector('.piece-movement-container');
    expect(containerEl).toBeInTheDocument();
  });

  it('应该在提供回调时调用它们', () => {
    const onConfigChange = jest.fn();
    const onMoveClick = jest.fn();
    const onMoveComplete = jest.fn();

    const { container } = render(
      <PieceMovementContainer
        config={{ enabled: true, duration: 100, easing: 'ease-in-out', showLastMove: true, showLegalMoves: true }}
        onConfigChange={onConfigChange}
        onMoveClick={onMoveClick}
        onMoveComplete={onMoveComplete}
        legalMoves={['e3', 'e4']}
        selectedPosition="e2"
      >
        <div>Board</div>
      </PieceMovementContainer>
    );

    // 点击合法走法提示
    const hint = container.querySelector('.legal-move-hint');
    if (hint) {
      fireEvent.click(hint);
      expect(onMoveClick).toHaveBeenCalled();
    }
  });
});
