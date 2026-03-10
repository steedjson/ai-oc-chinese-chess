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

export type ReconnectState = 
  | 'disconnected'
  | 'reconnecting'
  | 'connected'
  | 'failed';

export interface ReconnectInfo {
  state: ReconnectState;
  attempt: number;
  maxAttempts: number;
  nextRetryIn?: number; // 毫秒
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string = '';
  private config: WebSocketConfig = {};
  
  // 重连配置 - 指数退避
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000; // 1 秒
  private maxDelay = 30000; // 30 秒
  private reconnectTimer?: number;
  
  // 状态管理
  private reconnectState: ReconnectState = 'disconnected';
  private reconnectListeners: ((info: ReconnectInfo) => void)[] = [];
  
  private heartbeatInterval?: number;
  private isManualClose = false;

  /**
   * 连接到 WebSocket 服务器
   */
  connect(endpoint: string, config: WebSocketConfig = {}) {
    this.config = config;
    this.isManualClose = false;
    this.reconnectAttempts = 0;
    this.reconnectState = 'reconnecting';
    this.notifyReconnectListeners();

    const token = getAccessToken();
    const separator = endpoint.includes('?') ? '&' : '?';
    this.url = `ws://localhost:8000/ws/${endpoint}${separator}token=${token}`;

    this.createConnection();
    this.startHeartbeat();
  }

  /**
   * 添加重连状态监听器
   */
  onReconnectStateChange(listener: (info: ReconnectInfo) => void): () => void {
    this.reconnectListeners.push(listener);
    // 立即通知当前状态
    listener(this.getReconnectInfo());
    // 返回取消监听函数
    return () => {
      const index = this.reconnectListeners.indexOf(listener);
      if (index > -1) {
        this.reconnectListeners.splice(index, 1);
      }
    };
  }

  /**
   * 通知所有监听器
   */
  private notifyReconnectListeners() {
    const info = this.getReconnectInfo();
    this.reconnectListeners.forEach(listener => {
      try {
        listener(info);
      } catch (error) {
        console.error('[WebSocket] Reconnect listener error:', error);
      }
    });
  }

  /**
   * 获取重连信息
   */
  getReconnectInfo(): ReconnectInfo {
    return {
      state: this.reconnectState,
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      nextRetryIn: this.reconnectState === 'reconnecting' 
        ? this.calculateDelay() 
        : undefined,
    };
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
        this.reconnectState = 'connected';
        this.notifyReconnectListeners();
        this.config.onOpen?.();
      };

      this.ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        this.stopHeartbeat();
        this.config.onClose?.(event);

        // 自动重连（如果不是手动关闭）
        if (!this.isManualClose) {
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectState = 'reconnecting';
            this.scheduleReconnect();
          } else {
            this.reconnectState = 'failed';
            this.notifyReconnectListeners();
            console.warn('[WebSocket] Max reconnect attempts reached');
          }
        } else {
          this.reconnectState = 'disconnected';
          this.notifyReconnectListeners();
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
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectState = 'reconnecting';
        this.scheduleReconnect();
      } else {
        this.reconnectState = 'failed';
        this.notifyReconnectListeners();
      }
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
   * 计算重连延迟（指数退避）
   */
  private calculateDelay(): number {
    const exponentialDelay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    // 添加随机抖动（0-1000ms）避免同时重连
    const jitter = Math.random() * 1000;
    return Math.min(exponentialDelay + jitter, this.maxDelay);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = this.calculateDelay();
    
    console.log(
      `[WebSocket] Scheduling reconnect in ${Math.round(delay)}ms ` +
      `(attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );
    
    this.notifyReconnectListeners();
    
    this.reconnectTimer = window.setTimeout(() => {
      if (!this.isManualClose) {
        console.log(`[WebSocket] Reconnecting... (attempt ${this.reconnectAttempts})`);
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
   * 手动重连
   */
  reconnect() {
    if (this.reconnectState === 'failed' || this.reconnectState === 'disconnected') {
      console.log('[WebSocket] Manual reconnect triggered');
      this.reconnectAttempts = 0;
      this.reconnectState = 'reconnecting';
      this.notifyReconnectListeners();
      this.isManualClose = false;
      this.createConnection();
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this.reconnectState = 'disconnected';
    this.notifyReconnectListeners();
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
