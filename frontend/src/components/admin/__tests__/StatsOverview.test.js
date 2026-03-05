import React from 'react';
import { render, screen } from '@testing-library/react';
import StatsOverview from '../StatsOverview';

describe('StatsOverview', () => {
  const defaultStats = {
    totalPlayers: 1248,
    activeGames: 24,
    aiUsageRate: 68,
    winRate: 52,
    totalGames: 8934,
    playerRetention: 75,
  };

  test('renders all stat card titles', () => {
    render(<StatsOverview stats={defaultStats} />);

    expect(screen.getByText('总玩家数')).toBeInTheDocument();
    expect(screen.getByText('活跃对局')).toBeInTheDocument();
    expect(screen.getByText('总对局数')).toBeInTheDocument();
    expect(screen.getByText('平均胜率')).toBeInTheDocument();
    expect(screen.getByText('AI 使用率')).toBeInTheDocument();
    expect(screen.getByText('玩家留存率')).toBeInTheDocument();
  });

  test('displays correct stat values', () => {
    render(<StatsOverview stats={defaultStats} />);

    expect(screen.getByText('1248')).toBeInTheDocument();
    expect(screen.getByText('24')).toBeInTheDocument();
  });

  test('displays game modes distribution section', () => {
    render(<StatsOverview stats={defaultStats} />);

    expect(screen.getByText('游戏模式分布')).toBeInTheDocument();
    expect(screen.getByText('人对人:')).toBeInTheDocument();
  });

  test('displays peak hours section', () => {
    render(<StatsOverview stats={defaultStats} />);

    expect(screen.getByText('活跃时段')).toBeInTheDocument();
  });

  test('displays performance metrics section', () => {
    render(<StatsOverview stats={defaultStats} />);

    expect(screen.getByText('性能指标')).toBeInTheDocument();
  });

  test('handles empty stats with default values', () => {
    render(<StatsOverview stats={{}} />);

    expect(screen.getByText('总玩家数')).toBeInTheDocument();
  });

  test('handles partial stats', () => {
    const partialStats = {
      totalPlayers: 500,
      activeGames: 10,
    };

    render(<StatsOverview stats={partialStats} />);

    expect(screen.getByText('总玩家数')).toBeInTheDocument();
    expect(screen.getByText('活跃对局')).toBeInTheDocument();
  });

  test('renders with icons', () => {
    render(<StatsOverview stats={defaultStats} />);

    const icons = document.querySelectorAll('[data-icon]');
    expect(icons.length).toBeGreaterThanOrEqual(4);
  });
});
