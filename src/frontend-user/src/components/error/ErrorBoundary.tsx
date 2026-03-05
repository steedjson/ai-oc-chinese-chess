/**
 * 错误边界组件
 * 捕获组件渲染错误，显示友好的错误页面
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import ErrorFallback from './ErrorFallback';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  /**
   * 当错误发生时更新 state
   */
  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  /**
   * 捕获错误并记录日志
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    
    // 记录错误日志
    this.logError(error, errorInfo);
    
    // 调用外部错误处理回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * 记录错误日志
   */
  private logError(error: Error, errorInfo: ErrorInfo) {
    // 开发环境：输出到控制台
    if (import.meta.env.DEV) {
      console.error('🔴 ErrorBoundary caught an error:', {
        error,
        componentStack: errorInfo.componentStack,
      });
    }

    // 生产环境：发送到错误监控服务
    if (import.meta.env.PROD) {
      // TODO: 集成错误监控服务（如 Sentry）
      // Sentry.captureException(error, {
      //   extra: {
      //     componentStack: errorInfo.componentStack,
      //   },
      // });
      
      // 暂时记录到 localStorage
      try {
        const errorLog = {
          timestamp: new Date().toISOString(),
          message: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack,
        };
        
        const existingLogs = JSON.parse(localStorage.getItem('error_logs') || '[]');
        existingLogs.push(errorLog);
        // 只保留最近 100 条错误日志
        if (existingLogs.length > 100) {
          existingLogs.shift();
        }
        localStorage.setItem('error_logs', JSON.stringify(existingLogs));
      } catch (e) {
        console.error('Failed to save error log:', e);
      }
    }
  }

  /**
   * 重置错误状态
   */
  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  /**
   * 重试（重新加载页面）
   */
  retry = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // 使用自定义 fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 使用默认错误降级 UI
      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onRetry={this.retry}
          onReset={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
