/**
 * Footer 组件测试
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Footer from './Footer';

describe('Footer', () => {
  it('应该正确渲染页脚内容', () => {
    render(<Footer />);
    
    expect(screen.getByText('关于中国象棋')).toBeInTheDocument();
    expect(screen.getByText('快速链接')).toBeInTheDocument();
    expect(screen.getByText('联系我们', { selector: 'h3' })).toBeInTheDocument();
    expect(screen.getByText(/中国象棋是中国传统的棋类游戏/)).toBeInTheDocument();
  });

  it('应该显示快速链接', () => {
    render(<Footer />);
    
    expect(screen.getByText('首页')).toBeInTheDocument();
    expect(screen.getByText('AI 对战')).toBeInTheDocument();
    expect(screen.getByText('匹配对战')).toBeInTheDocument();
    expect(screen.getByText('排行榜')).toBeInTheDocument();
  });

  it('应该显示联系方式', () => {
    render(<Footer />);
    
    expect(screen.getByText('GitHub')).toBeInTheDocument();
    expect(screen.getByText('contact@chinese-chess.com')).toBeInTheDocument();
  });

  it('应该显示版权信息', () => {
    render(<Footer />);
    
    const year = new Date().getFullYear();
    expect(screen.getByText(new RegExp(`© ${year} 中国象棋平台`))).toBeInTheDocument();
  });
});
