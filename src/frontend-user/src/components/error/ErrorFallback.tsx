/**
 * 错误降级 UI 组件
 * 显示友好的错误提示和恢复操作
 */

import React from 'react';
import type { ErrorInfo } from 'react';

interface Props {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onRetry: () => void;
  onReset: () => void;
}

const ErrorFallback: React.FC<Props> = ({ error, errorInfo, onRetry, onReset }) => {
  const isDevelopment = import.meta.env.DEV;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        {/* 错误图标 */}
        <div className="mb-6">
          <div className="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
            <svg
              className="w-10 h-10 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        {/* 错误标题 */}
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          哎呀，出错了！
        </h1>
        <p className="text-gray-600 mb-6">
          组件渲染时遇到了问题，我们正在努力修复。
        </p>

        {/* 错误详情（仅开发环境） */}
        {isDevelopment && error && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg text-left">
            <div className="text-sm font-semibold text-gray-700 mb-2">
              错误详情：
            </div>
            <div className="text-xs text-red-600 font-mono break-all">
              {error.toString()}
            </div>
            {errorInfo && (
              <div className="mt-2 text-xs text-gray-500 font-mono break-all max-h-40 overflow-y-auto">
                {errorInfo.componentStack}
              </div>
            )}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="space-y-3">
          <button
            onClick={onRetry}
            className="w-full px-6 py-3 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.058A5.002 5.002 0 019.058 5a5 5 0 110 10H4v5l7-7-7-7z"
              />
            </svg>
            重试
          </button>

          <button
            onClick={onReset}
            className="w-full px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-lg transition-colors duration-200"
          >
            返回上一页
          </button>

          <a
            href="/"
            className="block w-full px-6 py-3 bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-600 font-semibold rounded-lg transition-colors duration-200 text-center"
          >
            返回首页
          </a>
        </div>

        {/* 技术支持信息 */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            如果问题持续，请联系技术支持
          </p>
          <p className="text-xs text-gray-400 mt-1">
            错误 ID: {error ? btoa(encodeURIComponent(error.message)).slice(0, 8) : 'unknown'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ErrorFallback;
