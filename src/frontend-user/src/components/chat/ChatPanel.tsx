import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';
import EmojiPicker from './EmojiPicker';
import { SendOutlined, SmileOutlined, DownOutlined, UpOutlined } from '@ant-design/icons';
import type { ChatPanelProps } from '@/types/chat';

const ChatPanel: React.FC<ChatPanelProps> = ({ gameId, chatType, token }) => {
  const { messages, isConnected, isSending, sendMessage, error } = useChat(gameId, chatType, token);
  const [inputValue, setInputValue] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 处理发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || isSending) return;
    
    await sendMessage(inputValue.trim(), 'text');
    setInputValue('');
  };

  // 处理表情选择
  const handleEmojiSelect = async (emoji: string) => {
    setShowEmojiPicker(false);
    await sendMessage(emoji, 'emoji');
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  // 渲染消息
  const renderMessage = (message: typeof messages[0], index: number) => {
    const isSystem = message.message_type === 'system';
    const isEmoji = message.message_type === 'emoji';
    const isOwn = message.sender?.username === undefined; // 简化判断

    if (isSystem) {
      return (
        <div key={message.id || index} className="chat-message chat-message-system">
          <span className="chat-message-content">{message.content}</span>
        </div>
      );
    }

    return (
      <div
        key={message.id || index}
        className={`chat-message ${isOwn ? 'chat-message-own' : 'chat-message-other'}`}
      >
        {!isOwn && (
          <div className="chat-message-avatar">
            {message.sender?.avatar_url ? (
              <img src={message.sender.avatar_url} alt={message.sender.username} />
            ) : (
              <div className="chat-avatar-placeholder">
                {message.sender?.username?.[0]?.toUpperCase() || '?'}
              </div>
            )}
          </div>
        )}
        
        <div className="chat-message-body">
          {!isOwn && (
            <div className="chat-message-sender">
              {message.sender?.username || '未知用户'}
            </div>
          )}
          
          <div className={`chat-message-content ${isEmoji ? 'chat-emoji' : ''}`}>
            {message.content}
          </div>
          
          <div className="chat-message-time">
            {formatTime(message.created_at)}
          </div>
        </div>
      </div>
    );
  };

  if (isCollapsed) {
    return (
      <div className="chat-panel chat-panel-collapsed">
        <button className="chat-panel-expand" onClick={() => setIsCollapsed(false)}>
          <UpOutlined />
          <span>展开聊天</span>
        </button>
      </div>
    );
  }

  return (
    <div className="chat-panel">
      {/* 头部 */}
      <div className="chat-panel-header">
        <div className="chat-panel-title">
          <span className="chat-title-text">
            {chatType === 'game' ? '对局聊天' : '观战聊天'}
          </span>
          <span className={`chat-status ${isConnected ? 'chat-status-connected' : 'chat-status-disconnected'}`}>
            {isConnected ? '●' : '○'}
          </span>
        </div>
        <button className="chat-panel-collapse" onClick={() => setIsCollapsed(true)}>
          <DownOutlined />
        </button>
      </div>

      {/* 消息列表 */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <span>暂无消息，开始聊天吧～</span>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => renderMessage(msg, index))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}

      {/* 输入区域 */}
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <button
            className="chat-emoji-btn"
            onClick={() => setShowEmojiPicker(!showEmojiPicker)}
            disabled={isSending}
          >
            <SmileOutlined />
          </button>
          
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder={isConnected ? '输入消息...' : '连接中...'}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!isConnected || isSending}
            maxLength={500}
          />
          
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || isSending || !isConnected}
          >
            {isSending ? (
              <span className="chat-loading" />
            ) : (
              <SendOutlined />
            )}
          </button>
        </div>
        
        <div className="chat-input-hint">
          按 Enter 发送
        </div>
      </div>

      {/* 表情选择器 */}
      {showEmojiPicker && (
        <EmojiPicker
          onSelect={handleEmojiSelect}
          onClose={() => setShowEmojiPicker(false)}
        />
      )}

      {/* 样式 */}
      <style>{`
        .chat-panel {
          display: flex;
          flex-direction: column;
          height: 400px;
          background: rgba(255, 255, 255, 0.85);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border-radius: 12px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.3);
          overflow: hidden;
          transition: all 0.3s ease;
        }

        .chat-panel-collapsed {
          height: auto;
        }

        .chat-panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(234, 179, 8, 0.1) 100%);
          border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }

        .chat-panel-title {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .chat-title-text {
          font-size: 15px;
          font-weight: 600;
          color: #1a1a1a;
        }

        .chat-status {
          font-size: 12px;
        }

        .chat-status-connected {
          color: #10b981;
        }

        .chat-status-disconnected {
          color: #ef4444;
        }

        .chat-panel-collapse {
          background: none;
          border: none;
          font-size: 14px;
          cursor: pointer;
          color: #666;
          padding: 4px 8px;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .chat-panel-collapse:hover {
          background: rgba(0, 0, 0, 0.05);
        }

        .chat-panel-expand {
          display: flex;
          align-items: center;
          gap: 6px;
          background: none;
          border: none;
          padding: 8px 16px;
          cursor: pointer;
          color: #666;
          font-size: 14px;
          transition: all 0.2s;
        }

        .chat-panel-expand:hover {
          background: rgba(0, 0, 0, 0.05);
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          background: rgba(255, 255, 255, 0.5);
        }

        .chat-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #999;
          font-size: 14px;
        }

        .chat-message {
          display: flex;
          gap: 10px;
          margin-bottom: 16px;
          animation: messageSlideIn 0.3s ease;
        }

        .chat-message-system {
          justify-content: center;
        }

        .chat-message-system .chat-message-content {
          background: rgba(220, 38, 38, 0.1);
          color: #dc2626;
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 13px;
          font-weight: 500;
        }

        .chat-message-avatar {
          flex-shrink: 0;
        }

        .chat-message-avatar img {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          object-fit: cover;
        }

        .chat-avatar-placeholder {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, #dc2626 0%, #eab308 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          font-size: 14px;
        }

        .chat-message-body {
          flex: 1;
          min-width: 0;
        }

        .chat-message-sender {
          font-size: 13px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .chat-message-content {
          display: inline-block;
          padding: 8px 12px;
          background: rgba(0, 0, 0, 0.05);
          border-radius: 12px;
          font-size: 14px;
          color: #1a1a1a;
          max-width: 100%;
          word-wrap: break-word;
        }

        .chat-message-own .chat-message-body {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }

        .chat-message-own .chat-message-content {
          background: linear-gradient(135deg, #dc2626 0%, #eab308 100%);
          color: white;
        }

        .chat-emoji {
          font-size: 32px;
          padding: 4px;
          background: none;
        }

        .chat-message-time {
          font-size: 11px;
          color: #999;
          margin-top: 4px;
        }

        .chat-error {
          padding: 8px 16px;
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
          font-size: 13px;
          text-align: center;
          animation: errorShake 0.3s ease;
        }

        .chat-input-area {
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.8);
          border-top: 1px solid rgba(0, 0, 0, 0.05);
        }

        .chat-input-wrapper {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .chat-emoji-btn {
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
          color: #666;
          padding: 8px;
          border-radius: 50%;
          transition: all 0.2s;
        }

        .chat-emoji-btn:hover:not(:disabled) {
          background: rgba(220, 38, 38, 0.1);
          color: #dc2626;
        }

        .chat-emoji-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .chat-input {
          flex: 1;
          padding: 10px 14px;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 20px;
          font-size: 14px;
          outline: none;
          transition: all 0.2s;
          background: rgba(255, 255, 255, 0.9);
        }

        .chat-input:focus {
          border-color: #dc2626;
          box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
        }

        .chat-input:disabled {
          background: rgba(0, 0, 0, 0.03);
          cursor: not-allowed;
        }

        .chat-send-btn {
          background: linear-gradient(135deg, #dc2626 0%, #eab308 100%);
          border: none;
          font-size: 18px;
          color: white;
          padding: 10px 16px;
          border-radius: 20px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          min-width: 44px;
        }

        .chat-send-btn:hover:not(:disabled) {
          transform: scale(1.05);
          box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
        }

        .chat-send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .chat-loading {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .chat-input-hint {
          text-align: center;
          font-size: 11px;
          color: #999;
          margin-top: 6px;
        }

        @keyframes messageSlideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes errorShake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        /* 滚动条样式 */
        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.02);
        }

        .chat-messages::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.1);
          border-radius: 3px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.2);
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
          .chat-panel {
            height: 350px;
          }
          
          .chat-message-avatar img,
          .chat-avatar-placeholder {
            width: 32px;
            height: 32px;
          }
        }
      `}</style>
    </div>
  );
};

export default ChatPanel;
