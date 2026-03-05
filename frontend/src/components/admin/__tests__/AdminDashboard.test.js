import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import AdminDashboard from '../AdminDashboard';

// Mock the CSS import
jest.mock('../AdminDashboard.css', () => ({}));

describe('AdminDashboard', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  test('renders header correctly', () => {
    render(<AdminDashboard />);
    
    expect(screen.getByText('管理面板')).toBeInTheDocument();
    expect(screen.getByText('实时监控系统运行状态')).toBeInTheDocument();
  });

  test('renders all stat card labels', () => {
    render(<AdminDashboard />);
    
    expect(screen.getAllByText('活跃对局')).toHaveLength(2);
    expect(screen.getAllByText('总玩家数')).toHaveLength(2);
    expect(screen.getAllByText('AI 使用率')).toHaveLength(1);
    expect(screen.getAllByText('平均胜率')).toHaveLength(2);
    expect(screen.getAllByText('今日对局')).toHaveLength(1);
    expect(screen.getAllByText('总对局数')).toHaveLength(2);
  });

  test('displays stats after data loading', async () => {
    render(<AdminDashboard />);
    
    // Fast-forward timers
    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    await waitFor(() => {
      expect(screen.getAllByText('24')).toHaveLength(2);
    });

    expect(screen.getAllByText('1248')).toHaveLength(2);
    expect(screen.getAllByText('156')).toHaveLength(1);
    expect(screen.getAllByText('8934')).toHaveLength(2);
  });

  test('displays stat descriptions', async () => {
    render(<AdminDashboard />);
    
    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    await waitFor(() => {
      expect(screen.getByText('当前在线对局数量')).toBeInTheDocument();
    });

    expect(screen.getByText('平台注册玩家总数')).toBeInTheDocument();
    expect(screen.getByText('玩家平均获胜概率')).toBeInTheDocument();
    expect(screen.getByText('平台累计对局总数')).toBeInTheDocument();
  });

  test('renders StatsOverview component', async () => {
    render(<AdminDashboard />);
    
    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    await waitFor(() => {
      expect(screen.getByText('游戏模式分布')).toBeInTheDocument();
    });

    expect(screen.getByText('活跃时段')).toBeInTheDocument();
    expect(screen.getByText('性能指标')).toBeInTheDocument();
  });
});
