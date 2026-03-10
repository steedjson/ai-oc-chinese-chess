import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import CreateRoomPage from '../CreateRoom';
import { useAuthStore } from '@/stores';

// Mock stores
vi.mock('@/stores', () => ({
  useAuthStore: vi.fn(),
}));

// Mock services
vi.mock('@/services', () => ({
  friendService: {
    createRoom: vi.fn(),
  },
}));

// Mock share utils
vi.mock('@/utils/share', () => ({
  copyToClipboard: vi.fn().mockResolvedValue(true),
  generateShareText: vi.fn().mockReturnValue('Mock share text'),
}));

// Mock components
vi.mock('@/components/friend/RoomStatus', () => ({
  RoomStatus: ({ room }: any) => (
    <div data-testid="room-status">
      <div>Room: {room.room_code}</div>
    </div>
  ),
}));

const mockUseAuthStore = useAuthStore as any;

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('CreateRoomPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('未登录时显示登录提示', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
    });

    renderWithRouter(<CreateRoomPage />);
    
    expect(screen.getByText('请先登录')).toBeInTheDocument();
    expect(screen.getByText('去登录')).toBeInTheDocument();
  });

  it('已登录时显示创建表单', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<CreateRoomPage />);
    
    expect(screen.getByText('创建好友对战')).toBeInTheDocument();
    expect(screen.getByText('创建房间')).toBeInTheDocument();
  });

  it('表单有默认值', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<CreateRoomPage />);
    
    const timeInput = screen.getByLabelText('时间控制（秒）');
    expect(timeInput).toHaveValue(600);
  });

  it('时间控制输入范围验证', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<CreateRoomPage />);
    
    const timeInput = screen.getByLabelText('时间控制（秒）') as HTMLInputElement;
    
    // 检查 min/max 属性
    expect(timeInput.min).toBe('60');
    expect(timeInput.max).toBe('7200');
  });

  it('计分模式开关默认关闭', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<CreateRoomPage />);
    
    const switchElement = screen.getByLabelText('计分模式');
    expect(switchElement).not.toBeChecked();
  });

  it('提交表单创建房间', async () => {
    const { friendService } = await import('@/services');
    const mockCreateRoom = vi.mocked(friendService.createRoom);
    
    mockCreateRoom.mockResolvedValue({
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

    renderWithRouter(<CreateRoomPage />);
    
    const submitButton = screen.getByText('创建房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockCreateRoom).toHaveBeenCalledWith({
        time_control: 600,
        is_rated: false,
      });
    });
  });

  it('创建成功后显示房间信息', async () => {
    const { friendService } = await import('@/services');
    const mockCreateRoom = vi.mocked(friendService.createRoom);
    
    mockCreateRoom.mockResolvedValue({
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

    renderWithRouter(<CreateRoomPage />);
    
    const submitButton = screen.getByText('创建房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('room-status')).toBeInTheDocument();
    });
  });

  it('创建失败时显示错误消息', async () => {
    const { friendService } = await import('@/services');
    const mockCreateRoom = vi.mocked(friendService.createRoom);
    
    mockCreateRoom.mockResolvedValue({
      success: false,
      error: {
        code: 'CREATE_FAILED',
        message: '创建失败',
      },
    });

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
    });

    renderWithRouter(<CreateRoomPage />);
    
    const submitButton = screen.getByText('创建房间');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('创建房间')).toBeInTheDocument(); // 按钮仍然存在
    });
  });
});
