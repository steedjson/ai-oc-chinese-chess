import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatPanel from '../ChatPanel';

// Mock useChat hook
vi.mock('@/hooks/useChat', () => ({
  useChat: vi.fn(),
}));

// Mock EmojiPicker
vi.mock('../EmojiPicker', () => ({
  default: ({ onSelect, onClose }: { onSelect: (emoji: string) => void; onClose: () => void }) => (
    <div data-testid="emoji-picker">
      <button onClick={() => onSelect('😀')}>😀</button>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

const mockUseChat = vi.mocked(await import('@/hooks/useChat')).useChat;

describe('ChatPanel', () => {
  const defaultProps = {
    gameId: 'test-game-id',
    chatType: 'game' as const,
    token: 'test-token',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat panel with title', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    expect(screen.getByText('对局聊天')).toBeInTheDocument();
  });

  it('shows connection status', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const connectedStatus = screen.getByText('●');
    expect(connectedStatus).toHaveClass('chat-status-connected');
  });

  it('shows empty message when no messages', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    expect(screen.getByText('暂无消息，开始聊天吧～')).toBeInTheDocument();
  });

  it('disables input when not connected', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: false,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('连接中...');
    expect(input).toBeDisabled();
  });

  it('allows typing when connected', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(input).toHaveValue('Hello');
  });

  it('calls sendMessage when pressing Enter', async () => {
    const sendMessageMock = vi.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: sendMessageMock,
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(sendMessageMock).toHaveBeenCalledWith('Test message', 'text');
    });
  });

  it('calls sendMessage when clicking send button', async () => {
    const sendMessageMock = vi.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: sendMessageMock,
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('输入消息...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(sendMessageMock).toHaveBeenCalledWith('Test message', 'text');
    });
  });

  it('shows emoji picker when clicking emoji button', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const emojiButton = screen.getByRole('button', { name: /smile/i });
    fireEvent.click(emojiButton);

    expect(screen.getByTestId('emoji-picker')).toBeInTheDocument();
  });

  it('can collapse chat panel', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
    });

    render(<ChatPanel {...defaultProps} />);
    
    const collapseButton = screen.getByRole('button', { name: /down/i });
    fireEvent.click(collapseButton);

    expect(screen.getByText('展开聊天')).toBeInTheDocument();
  });

  it('shows error message when provided', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      isConnected: true,
      isSending: false,
      sendMessage: vi.fn(),
      loadHistory: vi.fn(),
      disconnect: vi.fn(),
      error: '发送频率过快，请等待 2 秒',
    });

    render(<ChatPanel {...defaultProps} />);
    
    expect(screen.getByText('发送频率过快，请等待 2 秒')).toBeInTheDocument();
  });
});
