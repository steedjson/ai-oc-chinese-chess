import React from 'react';
import { ALLOWED_EMOJIS } from '@/types/chat';
import { CloseOutlined } from '@ant-design/icons';

export interface EmojiPickerProps {
  onSelect: (emoji: string) => void;
  onClose: () => void;
}

const EmojiPicker: React.FC<EmojiPickerProps> = ({ onSelect, onClose }) => {
  const handleEmojiClick = (emoji: string) => {
    onSelect(emoji);
  };

  return (
    <div className="emoji-picker-overlay" onClick={onClose}>
      <div className="emoji-picker-panel" onClick={(e) => e.stopPropagation()}>
        <div className="emoji-picker-header">
          <span className="emoji-picker-title">选择表情</span>
          <button className="emoji-picker-close" onClick={onClose}>
            <CloseOutlined />
          </button>
        </div>
        
        <div className="emoji-picker-grid">
          {ALLOWED_EMOJIS.map((emoji) => (
            <button
              key={emoji}
              className="emoji-picker-item"
              onClick={() => handleEmojiClick(emoji)}
              title={emoji}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      <style>{`
        .emoji-picker-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          animation: fadeIn 0.2s ease;
        }

        .emoji-picker-panel {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border-radius: 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
          max-width: 400px;
          width: 90%;
          max-height: 500px;
          overflow: hidden;
          animation: slideUp 0.3s ease;
        }

        .emoji-picker-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        .emoji-picker-title {
          font-size: 16px;
          font-weight: 600;
          color: #1a1a1a;
        }

        .emoji-picker-close {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #666;
          padding: 4px 8px;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .emoji-picker-close:hover {
          background: rgba(0, 0, 0, 0.05);
          color: #1a1a1a;
        }

        .emoji-picker-grid {
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          gap: 8px;
          padding: 16px;
          max-height: 400px;
          overflow-y: auto;
        }

        .emoji-picker-item {
          background: none;
          border: none;
          font-size: 28px;
          cursor: pointer;
          padding: 8px;
          border-radius: 8px;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .emoji-picker-item:hover {
          background: rgba(220, 38, 38, 0.1);
          transform: scale(1.2);
        }

        .emoji-picker-item:active {
          transform: scale(0.95);
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        @media (max-width: 480px) {
          .emoji-picker-grid {
            grid-template-columns: repeat(6, 1fr);
          }
          
          .emoji-picker-item {
            font-size: 24px;
          }
        }
      `}</style>
    </div>
  );
};

export default EmojiPicker;
