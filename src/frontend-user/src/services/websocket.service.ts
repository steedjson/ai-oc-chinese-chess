import { getAccessToken } from './api';
import type { WSMessage } from '@/types';

type WSMessageType = 
  | 'connect'
  | 'game_state'
  | 'move'
  | 'move_invalid'
  | 'chat'
  | 'player_join'
  | 'player_leave'
  | 'game_start'
  | 'game_end'
  | 'offer_draw'
  | 'accept_draw'
  | 'resign'
  | 'timeout'
  | 'error'
  | 'reconnect'
  | 'heartbeat';

interface WebSocketConfig {
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WSMessage) => void;
  onReconnect?: (attempt: number) => void;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string = '';
  private config: WebSocketConfig = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval?: number;
  private isManualClose = false;

  /**
   * 连接到 WebSocket 服务器
   */
  connect(endpoint: string, config: WebSocketConfig = {}) {
    this.config = config;
    this.isManualClose = false;
    this.reconnectAttempts = 0;

    const token = getAccessToken();
    const separator = endpoint.includes('?') ? '&' : '?';
    this.url = `ws://localhost:8000/ws/${endpoint}${separator}token=${token}`;

    this.createConnection();
    this.startHeartbeat();
  }

  /**
   * 创建 WebSocket 连接
   */
  private createConnection() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.reconnectAttempts = 0;
        this.config.onOpen?.();
      };

      this.ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        this.stopHeartbeat();
        this.config.onClose?.(event);

        // 自动重连（如果不是手动关闭）
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (event) => {
        console.error('[WebSocket] Error', event);
        this.config.onError?.(event);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WSMessage) {
    // 处理心跳响应
    if (message.type === 'heartbeat') {
      return;
    }

    this.config.onMessage?.(message);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.config.onReconnect?.(this.reconnectAttempts);
        this.createConnection();
      }
    }, delay);
  }

  /**
   * 发送消息
   */
  send(type: WSMessageType, data?: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WSMessage = { type, data };
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
    }
  }

  /**
   * 发送走棋
   */
  sendMove(from: string, to: string) {
    this.send('move', { from, to });
  }

  /**
   * 发送聊天消息
   */
  sendChat(content: string) {
    this.send('chat', { content });
  }

  /**
   * 投降
   */
  sendResign() {
    this.send('resign');
  }

  /**
   * 提议和棋
   */
  sendOfferDraw() {
    this.send('offer_draw');
  }

  /**
   * 接受和棋
   */
  sendAcceptDraw() {
    this.send('accept_draw');
  }

  /**
   * 请求重连同步
   */
  sendReconnect(gameId: string) {
    this.send('reconnect', { game_id: gameId });
  }

  /**
   * 开始心跳
   */
  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = window.setInterval(() => {
      this.send('heartbeat', { timestamp: Date.now() });
    }, 30000); // 30 秒
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = undefined;
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 获取连接状态
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// 单例实例
let wsInstance: WebSocketService | null = null;

export function getWebSocketService(): WebSocketService {
  if (!wsInstance) {
    wsInstance = new WebSocketService();
  }
  return wsInstance;
}

export default getWebSocketService;
