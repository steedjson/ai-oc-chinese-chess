/**
 * WebSocket 断线重连服务（优化版）
 * 
 * 功能：
 * - 指数退避重连策略
 * - 重连时自动恢复游戏状态
 * - 显示重连进度提示
 * - 重连失败后的友好提示
 * - 连接状态管理
 * - 重连历史记录
 */

export type ReconnectState = 
  | 'disconnected'
  | 'reconnecting'
  | 'connected'
  | 'failed'
  | 'recovering';

export interface ReconnectInfo {
  state: ReconnectState;
  attempt: number;
  maxAttempts: number;
  nextRetryIn?: number; // 毫秒
  progress?: number; // 进度百分比
  message?: string; // 用户友好消息
}

export interface ReconnectHistory {
  timestamp: number;
  state: ReconnectState;
  attempt: number;
  duration?: number;
  reason?: string;
}

export interface ReconnectConfig {
  maxReconnectAttempts?: number;
  baseDelay?: number; // 基础延迟（毫秒）
  maxDelay?: number; // 最大延迟（毫秒）
  jitter?: number; // 随机抖动（毫秒）
  onStateChange?: (info: ReconnectInfo) => void;
  onReconnectStart?: (attempt: number) => void;
  onReconnectSuccess?: () => void;
  onReconnectFailed?: () => void;
  onRecovering?: () => void;
  onRecovered?: () => void;
}

export class WebSocketReconnect {
  private config: Required<ReconnectConfig>;
  
  // 重连状态
  private state: ReconnectState = 'disconnected';
  private attempt = 0;
  private reconnectTimer?: number;
  private startTime?: number;
  
  // 历史记录
  private history: ReconnectHistory[] = [];
  private maxHistorySize = 50;
  
  // 状态监听器
  private listeners: Set<(info: ReconnectInfo) => void> = new Set();
  
  constructor(config: ReconnectConfig = {}) {
    this.config = {
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      baseDelay: config.baseDelay ?? 1000,
      maxDelay: config.maxDelay ?? 30000,
      jitter: config.jitter ?? 500,
      onStateChange: config.onStateChange ?? (() => {}),
      onReconnectStart: config.onReconnectStart ?? (() => {}),
      onReconnectSuccess: config.onReconnectSuccess ?? (() => {}),
      onReconnectFailed: config.onReconnectFailed ?? (() => {}),
      onRecovering: config.onRecovering ?? (() => {}),
      onRecovered: config.onRecovered ?? (() => {}),
    };
  }
  
  /**
   * 开始重连流程
   */
  startReconnect(): void {
    if (this.state === 'reconnecting' || this.state === 'recovering') {
      console.log('[Reconnect] Already in progress');
      return;
    }
    
    this.attempt++;
    this.startTime = Date.now();
    
    if (this.attempt > this.config.maxReconnectAttempts) {
      this.handleFailed();
      return;
    }
    
    this.state = 'reconnecting';
    this.config.onReconnectStart(this.attempt);
    this.updateState();
    
    const delay = this.calculateDelay();
    console.log(
      `[Reconnect] Scheduling reconnect in ${Math.round(delay)}ms ` +
      `(attempt ${this.attempt}/${this.config.maxReconnectAttempts})`
    );
    
    this.reconnectTimer = window.setTimeout(() => {
      this.attemptReconnect();
    }, delay);
  }
  
  /**
   * 计算重连延迟（指数退避 + 随机抖动）
   */
  private calculateDelay(): number {
    const exponentialDelay = this.config.baseDelay * Math.pow(2, this.attempt - 1);
    const jitter = Math.random() * this.config.jitter;
    return Math.min(exponentialDelay + jitter, this.config.maxDelay);
  }
  
  /**
   * 尝试重连（由外部调用）
   */
  attemptReconnect(): void {
    if (this.state !== 'reconnecting') {
      return;
    }
    
    console.log(`[Reconnect] Attempting reconnect (attempt ${this.attempt})`);
    this.updateState();
  }
  
  /**
   * 重连成功
   */
  onSuccess(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    
    const duration = this.startTime ? Date.now() - this.startTime : 0;
    
    // 记录历史
    this.addToHistory({
      timestamp: Date.now(),
      state: 'connected',
      attempt: this.attempt,
      duration,
    });
    
    // 进入恢复状态
    this.state = 'recovering';
    this.config.onRecovering();
    this.updateState();
    
    console.log(`[Reconnect] Successfully reconnected after ${duration}ms`);
    
    // 模拟恢复过程（实际应该等待游戏状态同步）
    setTimeout(() => {
      this.handleRecovered();
    }, 500);
  }
  
  /**
   * 恢复完成
   */
  private handleRecovered(): void {
    this.state = 'connected';
    this.attempt = 0;
    this.config.onRecovered();
    this.config.onReconnectSuccess();
    this.updateState();
    
    console.log('[Reconnect] Recovery complete');
  }
  
  /**
   * 重连失败
   */
  private handleFailed(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    
    this.state = 'failed';
    
    // 记录历史
    this.addToHistory({
      timestamp: Date.now(),
      state: 'failed',
      attempt: this.attempt,
      reason: 'Max attempts reached',
    });
    
    this.config.onReconnectFailed();
    this.updateState();
    
    console.error('[Reconnect] All reconnect attempts failed');
  }
  
  /**
   * 手动重置
   */
  reset(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }
    
    this.state = 'disconnected';
    this.attempt = 0;
    this.startTime = undefined;
    this.updateState();
    
    console.log('[Reconnect] Reset');
  }
  
  /**
   * 添加历史记录
   */
  private addToHistory(record: ReconnectHistory): void {
    this.history.push(record);
    
    // 限制历史记录大小
    if (this.history.length > this.maxHistorySize) {
      this.history = this.history.slice(-this.maxHistorySize);
    }
  }
  
  /**
   * 获取重连信息
   */
  getReconnectInfo(): ReconnectInfo {
    const info: ReconnectInfo = {
      state: this.state,
      attempt: this.attempt,
      maxAttempts: this.config.maxReconnectAttempts,
    };
    
    // 计算下次重试时间
    if (this.state === 'reconnecting' && this.attempt <= this.config.maxReconnectAttempts) {
      info.nextRetryIn = this.calculateDelay();
    }
    
    // 计算进度
    if (this.state === 'reconnecting') {
      info.progress = Math.min((this.attempt / this.config.maxReconnectAttempts) * 100, 100);
    } else if (this.state === 'recovering') {
      info.progress = 100;
    } else if (this.state === 'connected') {
      info.progress = 100;
    } else {
      info.progress = 0;
    }
    
    // 用户友好消息
    info.message = this.getUserMessage();
    
    return info;
  }
  
  /**
   * 获取用户友好消息
   */
  private getUserMessage(): string {
    switch (this.state) {
      case 'reconnecting':
        if (this.attempt <= 2) {
          return '正在重新连接...';
        } else if (this.attempt <= 5) {
          return '连接不稳定，正在重试...';
        } else {
          return '连接困难，继续尝试...';
        }
      
      case 'recovering':
        return '连接成功，正在恢复游戏状态...';
      
      case 'connected':
        return '已连接';
      
      case 'failed':
        return '连接失败，请检查网络后重试';
      
      default:
        return '';
    }
  }
  
  /**
   * 更新状态并通知监听器
   */
  private updateState(): void {
    const info = this.getReconnectInfo();
    
    // 通知配置中的回调
    if (this.state === 'reconnecting') {
      this.config.onStateChange(info);
    } else {
      this.config.onStateChange(info);
    }
    
    // 通知所有监听器
    this.listeners.forEach(listener => {
      try {
        listener(info);
      } catch (error) {
        console.error('[Reconnect] Listener error:', error);
      }
    });
  }
  
  /**
   * 添加状态监听器
   */
  onStateChange(listener: (info: ReconnectInfo) => void): () => void {
    this.listeners.add(listener);
    
    // 立即通知当前状态
    listener(this.getReconnectInfo());
    
    // 返回取消监听函数
    return () => {
      this.listeners.delete(listener);
    };
  }
  
  /**
   * 获取历史记录
   */
  getHistory(limit: number = 10): ReconnectHistory[] {
    return this.history.slice(-limit);
  }
  
  /**
   * 获取统计信息
   */
  getStats(): {
    totalAttempts: number;
    totalSuccesses: number;
    totalFailures: number;
    successRate: number;
    avgReconnectTime: number;
  } {
    const totalAttempts = this.history.filter(h => h.state === 'reconnecting').length;
    const totalSuccesses = this.history.filter(h => h.state === 'connected').length;
    const totalFailures = this.history.filter(h => h.state === 'failed').length;
    
    const reconnectDurations = this.history
      .filter(h => h.duration !== undefined)
      .map(h => h.duration!);
    
    const avgReconnectTime = reconnectDurations.length > 0
      ? reconnectDurations.reduce((a, b) => a + b, 0) / reconnectDurations.length
      : 0;
    
    return {
      totalAttempts,
      totalSuccesses,
      totalFailures,
      successRate: totalAttempts > 0 ? (totalSuccesses / totalAttempts) * 100 : 0,
      avgReconnectTime,
    };
  }
  
  /**
   * 获取当前状态
   */
  getState(): ReconnectState {
    return this.state;
  }
  
  /**
   * 获取当前尝试次数
   */
  getAttempt(): number {
    return this.attempt;
  }
}

// 单例实例
let reconnectInstance: WebSocketReconnect | null = null;

/**
 * 获取 WebSocket 重连服务单例
 */
export function getWebSocketReconnect(config: ReconnectConfig = {}): WebSocketReconnect {
  if (!reconnectInstance) {
    reconnectInstance = new WebSocketReconnect(config);
  }
  return reconnectInstance;
}

/**
 * 创建新的重连服务实例
 */
export function createWebSocketReconnect(config: ReconnectConfig = {}): WebSocketReconnect {
  return new WebSocketReconnect(config);
}

export default getWebSocketReconnect;
