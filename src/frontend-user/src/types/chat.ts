// 聊天相关类型定义

export interface ChatMessage {
  id: string;
  game_id: string;
  sender: {
    id: number;
    username: string;
    avatar_url?: string;
  } | null;
  content: string;
  message_type: 'text' | 'system' | 'emoji';
  room_type: 'game' | 'spectator';
  created_at: string;
  is_deleted?: boolean;
}

export interface ChatMessageResponse {
  id: string;
  game_id: string;
  sender: {
    id: number;
    username: string;
    avatar_url?: string;
  } | null;
  content: string;
  message_type: 'text' | 'system' | 'emoji';
  room_type: 'game' | 'spectator';
  created_at: string;
}

export interface SendMessageRequest {
  content: string;
  message_type: 'text' | 'emoji';
  room_type: 'game' | 'spectator';
}

export interface ChatHistoryResponse {
  success: boolean;
  messages: ChatMessageResponse[];
  has_more: boolean;
}

export interface UseChatReturn {
  messages: ChatMessage[];
  isConnected: boolean;
  isSending: boolean;
  sendMessage: (content: string, messageType?: 'text' | 'emoji') => Promise<void>;
  loadHistory: () => Promise<void>;
  disconnect: () => void;
  error?: string;
}

export interface ChatPanelProps {
  gameId: string;
  chatType: 'game' | 'spectator';
  token: string;
}

export interface EmojiPickerProps {
  onSelect: (emoji: string) => void;
  onClose: () => void;
}

// WebSocket 消息类型
export interface WSChatMessage {
  type: 'CHAT_MESSAGE' | 'GET_HISTORY' | 'DELETE_MESSAGE' | 'HEARTBEAT';
  content?: string;
  message_type?: 'text' | 'emoji';
  limit?: number;
  before?: string;
  message_id?: string;
}

export interface WSChatResponse {
  type: 'WELCOME' | 'CHAT_HISTORY' | 'CHAT_MESSAGE' | 'SYSTEM_MESSAGE' | 'MESSAGE_DELETED' | 'HEARTBEAT' | 'ERROR';
  payload: {
    room_type?: 'game' | 'spectator';
    game_id?: string;
    username?: string;
    timestamp?: string;
    success?: boolean;
    message?: ChatMessageResponse;
    messages?: ChatMessageResponse[];
    content?: string;
    message_type?: 'text' | 'system' | 'emoji';
    message_id?: string;
    acknowledged?: boolean;
    error?: {
      code: string;
      message: string;
    };
  };
}

// 表情列表
export const ALLOWED_EMOJIS = [
  '😀', '😂', '😍', '🥰', '😎', '🤔', '👍', '👎',
  '❤️', '🔥', '✨', '🎉', '🏆', '♟️', '🎯', '💪',
  '😅', '😭', '😱', '🙏', '💯', '🚀', '⭐', '🌟',
  '😊', '😋', '😌', '😏', '😜', '😝', '😇', '🤗',
  '🤔', '🤐', '🤑', '🤓', '😈', '👻', '💀', '👽',
];
