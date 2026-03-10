import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage, UseChatReturn, WSChatMessage, WSChatResponse } from '@/types/chat';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/chat';
const RATE_LIMIT_INTERVAL = 2000; // 2 秒限流

export const useChat = (gameId: string, roomType: 'game' | 'spectator', token: string): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string>();
  
  const wsRef = useRef<WebSocket | null>(null);
  const lastMessageTimeRef = useRef<number>(0);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>();

  // 连接 WebSocket
  const connect = useCallback(() => {
    try {
      const wsUrl = `${WS_BASE_URL}/${roomType}/${gameId}/?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[Chat] WebSocket connected');
        setIsConnected(true);
        setError(undefined);
        reconnectAttemptsRef.current = 0;

        // 请求历史消息
        requestHistory();

        // 启动心跳
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        try {
          const data: WSChatResponse = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('[Chat] Failed to parse message:', err);
        }
      };

      ws.onclose = () => {
        console.log('[Chat] WebSocket disconnected');
        setIsConnected(false);
        stopHeartbeat();

        // 尝试重连（最多 5 次）
        if (reconnectAttemptsRef.current < 5) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`[Chat] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = (err) => {
        console.error('[Chat] WebSocket error:', err);
        setError('连接失败，请重试');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[Chat] Failed to connect:', err);
      setError('无法连接到聊天服务');
    }
  }, [gameId, roomType, token]);

  // 处理 WebSocket 消息
  const handleWebSocketMessage = useCallback((data: WSChatResponse) => {
    switch (data.type) {
      case 'WELCOME':
        console.log('[Chat] Welcome to chat room');
        break;

      case 'CHAT_HISTORY':
        if (data.payload.messages) {
          const newMessages: ChatMessage[] = data.payload.messages.map(msg => ({
            ...msg,
            is_deleted: false,
          }));
          setMessages(prev => [...newMessages, ...prev]);
        }
        break;

      case 'CHAT_MESSAGE':
        if (data.payload.message) {
          const newMessage: ChatMessage = {
            ...data.payload.message,
            is_deleted: false,
          };
          setMessages(prev => [...prev, newMessage]);
        }
        break;

      case 'SYSTEM_MESSAGE':
        if (data.payload.content) {
          const systemMessage: ChatMessage = {
            id: `system-${Date.now()}`,
            game_id: gameId,
            sender: null,
            content: data.payload.content,
            message_type: 'system',
            room_type: roomType,
            created_at: new Date().toISOString(),
            is_deleted: false,
          };
          setMessages(prev => [...prev, systemMessage]);
        }
        break;

      case 'MESSAGE_DELETED':
        if (data.payload.message_id) {
          setMessages(prev => prev.filter(m => m.id !== data.payload.message_id));
        }
        break;

      case 'ERROR':
        if (data.payload.error) {
          console.error('[Chat] Error:', data.payload.error);
          if (data.payload.error.code === 'RATE_LIMITED') {
            setError(data.payload.error.message);
            setTimeout(() => setError(undefined), 3000);
          } else {
            setError(data.payload.error.message);
          }
        }
        break;

      case 'HEARTBEAT':
        // 心跳响应，无需处理
        break;
    }
  }, [gameId, roomType]);

  // 请求历史消息
  const requestHistory = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const lastMessage = messages[messages.length - 1];
    const msg: WSChatMessage = {
      type: 'GET_HISTORY',
      limit: 50,
    };

    if (lastMessage) {
      msg.before = lastMessage.created_at;
    }

    wsRef.current.send(JSON.stringify(msg));
  }, [messages]);

  // 发送消息
  const sendMessage = useCallback(async (content: string, messageType: 'text' | 'emoji' = 'text') => {
    if (!content.trim()) {
      setError('消息内容不能为空');
      setTimeout(() => setError(undefined), 2000);
      return;
    }

    // 限流检查
    const now = Date.now();
    const timeSinceLastMessage = now - lastMessageTimeRef.current;
    if (timeSinceLastMessage < RATE_LIMIT_INTERVAL) {
      const waitTime = Math.ceil((RATE_LIMIT_INTERVAL - timeSinceLastMessage) / 1000);
      setError(`发送频率过快，请等待${waitTime}秒`);
      setTimeout(() => setError(undefined), 3000);
      return;
    }

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('未连接到聊天服务');
      setTimeout(() => setError(undefined), 3000);
      return;
    }

    setIsSending(true);
    setError(undefined);

    try {
      const msg: WSChatMessage = {
        type: 'CHAT_MESSAGE',
        content,
        message_type: messageType,
      };

      wsRef.current.send(JSON.stringify(msg));
      lastMessageTimeRef.current = now;
    } catch (err) {
      console.error('[Chat] Failed to send message:', err);
      setError('发送失败，请重试');
      setTimeout(() => setError(undefined), 3000);
    } finally {
      setIsSending(false);
    }
  }, []);

  // 加载历史消息
  const loadHistory = useCallback(async () => {
    requestHistory();
  }, [requestHistory]);

  // 断开连接
  const disconnect = useCallback(() => {
    stopHeartbeat();
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setMessages([]);
  }, []);

  // 启动心跳
  const startHeartbeat = useCallback(() => {
    stopHeartbeat();
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const msg: WSChatMessage = { type: 'HEARTBEAT' };
        wsRef.current.send(JSON.stringify(msg));
      }
    }, 30000); // 30 秒心跳
  }, []);

  // 停止心跳
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = undefined;
    }
  }, []);

  // 初始化连接
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // 清理
  useEffect(() => {
    return () => {
      stopHeartbeat();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [stopHeartbeat]);

  return {
    messages,
    isConnected,
    isSending,
    sendMessage,
    loadHistory,
    disconnect,
    error,
  };
};

export default useChat;
