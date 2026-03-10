import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import JoinRoomPage from '../JoinRoom';
import { useAuthStore } from '@/stores';

// Mock stores
vi.mock('@/stores', () => ({
  useAuthStore: vi.fn(),
}));

// Mock services
vi.mock('@/services', () => ({
  friendService: {
    getRoom: vi.fn(),
    joinRoom: vi.fn(),
  },
}));

const mockUseAuthStore = useAuthStore as any;

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('JoinRoomPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('未登录时显示登录提示', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
    });

    renderWithRouter(<JoinRoomPage />);
    
    expect(screen.getByText('请先登录')).toBeInTheDocument();
    expect(screen.getByText('去登录')).toBeInTheDocument();
  });

  it('已登录时显示加入表单', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    expect(screen.getByText('加入好友对战')).toBeInTheDocument();
    expect(screen.getByText('加入房间')).toBeInTheDocument();
  });

  it('房间号输入自动转换为大写', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByPlaceholderText('例如：CHESS2A3B5') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'chess12345' } });
    
    expect(input.value).toBe('CHESS12345');
  });

  it('房间号格式验证', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号');
    fireEvent.change(input, { target: { value: 'AB' } }); // 太短
    
    const submitButton = screen.getByText('加入房间');
    fireEvent.click(submitButton);
    
    expect(screen.getByText('房间号至少 5 位')).toBeInTheDocument();
  });

  it('从 URL 参数自动填充房间号', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    // Mock location with query param
    const originalLocation = window.location;
    delete (window as any).location;
    window.location = {
      ...originalLocation,
      search: '?room=CHESS12345',
    };

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号') as HTMLInputElement;
    expect(input.value).toBe('CHESS12345');
    
    // Restore
    window.location = originalLocation;
  });

  it('查询房间详情', async () => {
    const { friendService } = await import('@/services');
    const mockGetRoom = vi.mocked(friendService.getRoom);
    
    mockGetRoom.mockResolvedValue({
      success: true,
      data: {
        id: 1,
        room_code: 'CHESS12345',
        status: 'waiting',
        creator: 1,
        creator_username: 'testuser',
        game_id: 100,
        expires_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        invite_link: 'https://example.com/games/friend/join/CHESS12345',
      },
    });

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号');
    fireEvent.change(input, { target: { value: 'CHESS12345' } });
    
    const submitButton = screen.getByText('加入房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockGetRoom).toHaveBeenCalledWith('CHESS12345');
    });
  });

  it('房间不存在时显示错误', async () => {
    const { friendService } = await import('@/services');
    const mockGetRoom = vi.mocked(friendService.getRoom);
    
    mockGetRoom.mockResolvedValue({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: '房间不存在',
      },
    });

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号');
    fireEvent.change(input, { target: { value: 'INVALID' } });
    
    const submitButton = screen.getByText('加入房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('房间不存在')).toBeInTheDocument();
    });
  });

  it('房间已过期时显示错误', async () => {
    const { friendService } = await import('@/services');
    const mockGetRoom = vi.mocked(friendService.getRoom);
    
    mockGetRoom.mockResolvedValue({
      success: true,
      data: {
        id: 1,
        room_code: 'CHESS12345',
        status: 'expired',
        creator: 1,
        creator_username: 'testuser',
        game_id: 100,
        expires_at: new Date(Date.now() - 1000).toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        invite_link: 'https://example.com/games/friend/join/CHESS12345',
      },
    });

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号');
    fireEvent.change(input, { target: { value: 'CHESS12345' } });
    
    const submitButton = screen.getByText('加入房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('房间已过期')).toBeInTheDocument();
    });
  });

  it('加入房间成功', async () => {
    const { friendService } = await import('@/services');
    const mockGetRoom = vi.mocked(friendService.getRoom);
    const mockJoinRoom = vi.mocked(friendService.joinRoom);
    
    mockGetRoom.mockResolvedValue({
      success: true,
      data: {
        id: 1,
        room_code: 'CHESS12345',
        status: 'waiting',
        creator: 1,
        creator_username: 'testuser',
        game_id: 100,
        expires_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        invite_link: 'https://example.com/games/friend/join/CHESS12345',
      },
    });

    mockJoinRoom.mockResolvedValue({
      success: true,
      data: {
        message: '加入成功',
        room: {
          id: 1,
          room_code: 'CHESS12345',
          status: 'playing',
          creator: 1,
          creator_username: 'testuser',
          game_id: 100,
          expires_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          invite_link: 'https://example.com/games/friend/join/CHESS12345',
        },
        game_id: 100,
        your_color: 'black',
      },
    });

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    const input = screen.getByLabelText('房间号');
    fireEvent.change(input, { target: { value: 'CHESS12345' } });
    
    const submitButton = screen.getByText('加入房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockJoinRoom).toHaveBeenCalledWith('CHESS12345');
    });
  });

  it('显示创建房间按钮', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<JoinRoomPage />);
    
    expect(screen.getByText('创建房间')).toBeInTheDocument();
  });
});
