import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RoomStatus } from '../RoomStatus';
import type { FriendRoom } from '@/types';

// Mock message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
    },
  };
});

// Mock share utils
vi.mock('@/utils/share', () => ({
  copyToClipboard: vi.fn().mockResolvedValue(true),
  generateShareText: vi.fn().mockReturnValue('Mock share text'),
}));

const mockRoom: FriendRoom = {
  id: 1,
  room_code: 'CHESS12345',
  status: 'waiting',
  creator: 1,
  creator_username: 'testuser',
  game_id: 100,
  expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 小时后
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  invite_link: 'https://example.com/games/friend/join/CHESS12345',
};

describe('RoomStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('渲染房间基本信息', () => {
    render(<RoomStatus room={mockRoom} />);
    
    expect(screen.getByText('CHESS12345')).toBeInTheDocument();
    expect(screen.getByText('房主：testuser')).toBeInTheDocument();
    expect(screen.getByText('等待中')).toBeInTheDocument();
  });

  it('显示游戏 ID', () => {
    render(<RoomStatus room={mockRoom} />);
    
    expect(screen.getByText('#100')).toBeInTheDocument();
  });

  it('显示倒计时（等待状态）', () => {
    render(<RoomStatus room={mockRoom} />);
    
    expect(screen.getByText('房间过期倒计时')).toBeInTheDocument();
  });

  it('不显示倒计时（非等待状态）', () => {
    const finishedRoom: FriendRoom = {
      ...mockRoom,
      status: 'finished',
    };
    
    render(<RoomStatus room={finishedRoom} />);
    
    expect(screen.queryByText('房间过期倒计时')).not.toBeInTheDocument();
  });

  it('显示分享按钮（等待状态）', () => {
    render(<RoomStatus room={mockRoom} />);
    
    expect(screen.getByText('分享房间')).toBeInTheDocument();
    expect(screen.getByText('复制链接')).toBeInTheDocument();
  });

  it('显示加入按钮（当提供 onJoin 回调）', () => {
    const onJoin = vi.fn();
    render(<RoomStatus room={mockRoom} onJoin={onJoin} />);
    
    expect(screen.getByText('加入房间')).toBeInTheDocument();
  });

  it('显示开始游戏按钮（当提供 onStartGame 回调）', () => {
    const onStartGame = vi.fn();
    render(<RoomStatus room={mockRoom} onStartGame={onStartGame} />);
    
    expect(screen.getByText('开始游戏')).toBeInTheDocument();
  });

  it('点击分享按钮调用分享处理', async () => {
    const onShare = vi.fn();
    render(<RoomStatus room={mockRoom} onShare={onShare} />);
    
    const shareButton = screen.getByText('分享房间');
    fireEvent.click(shareButton);
    
    await waitFor(() => {
      expect(onShare).toHaveBeenCalled();
    });
  });

  it('点击复制链接按钮', async () => {
    render(<RoomStatus room={mockRoom} />);
    
    const copyButton = screen.getByText('复制链接');
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(screen.getByText('链接已复制')).toBeInTheDocument();
    });
  });

  it('显示对局中状态', () => {
    const playingRoom: FriendRoom = {
      ...mockRoom,
      status: 'playing',
      started_at: new Date().toISOString(),
    };
    
    render(<RoomStatus room={playingRoom} />);
    
    expect(screen.getByText('对局中')).toBeInTheDocument();
    expect(screen.getByText('进入对局')).toBeInTheDocument();
  });

  it('显示已结束状态', () => {
    const finishedRoom: FriendRoom = {
      ...mockRoom,
      status: 'finished',
      finished_at: new Date().toISOString(),
    };
    
    render(<RoomStatus room={finishedRoom} />);
    
    expect(screen.getByText('已结束')).toBeInTheDocument();
    expect(screen.getByText('此房间已结束')).toBeInTheDocument();
  });

  it('显示已过期状态', () => {
    const expiredRoom: FriendRoom = {
      ...mockRoom,
      status: 'expired',
    };
    
    render(<RoomStatus room={expiredRoom} />);
    
    expect(screen.getByText('已过期')).toBeInTheDocument();
    expect(screen.getByText('此房间已结束')).toBeInTheDocument();
  });
});
