/**
 * BoardAnimation.tsx - 棋盘动画效果组件
 * 
 * 功能：
 * - 将军动画提示
 * - 胜负动画庆祝效果
 * - 吃子动画特效
 * - 动画开关配置
 * 
 * @author OpenClaw 助手
 * @date 2026-03-06
 */

import React, { useEffect, useState, useCallback } from 'react';
import './BoardAnimation.css';

// ============ 类型定义 ============

export interface AnimationConfig {
  /** 是否启用所有动画 */
  enabled: boolean;
  /** 是否启用走棋动画 */
  moveAnimation: boolean;
  /** 是否启用吃子动画 */
  captureAnimation: boolean;
  /** 是否启用将军动画 */
  checkAnimation: boolean;
  /** 是否启用胜负动画 */
  gameEndAnimation: boolean;
  /** 动画速度倍率 (0.5-2.0) */
  speedMultiplier: number;
}

export interface CheckAnimationProps {
  /** 是否将军状态 */
  isCheck: boolean;
  /** 将军方 (red/black) */
  checkSide?: 'red' | 'black';
  /** 动画配置 */
  config?: AnimationConfig;
}

export interface GameEndAnimationProps {
  /** 是否游戏结束 */
  isGameOver: boolean;
  /** 获胜方 (red/black/draw) */
  winner?: 'red' | 'black' | 'draw';
  /** 获胜原因 */
  winReason?: 'checkmate' | 'stalemate' | 'resign' | 'timeout';
  /** 动画配置 */
  config?: AnimationConfig;
}

export interface CaptureAnimationProps {
  /** 是否触发吃子 */
  isCapturing: boolean;
  /** 被吃棋子类型 */
  capturedPiece?: string;
  /** 吃子位置 */
  position?: string;
  /** 动画配置 */
  config?: AnimationConfig;
}

// ============ 默认配置 ============

const DEFAULT_CONFIG: AnimationConfig = {
  enabled: true,
  moveAnimation: true,
  captureAnimation: true,
  checkAnimation: true,
  gameEndAnimation: true,
  speedMultiplier: 1.0,
};

// ============ 将军动画组件 ============

export const CheckAnimation: React.FC<CheckAnimationProps> = ({
  isCheck,
  checkSide = 'red',
  config = DEFAULT_CONFIG,
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!config.enabled || !config.checkAnimation) {
      return;
    }

    if (isCheck) {
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isCheck, config]);

  if (!visible || !config.checkAnimation) return null;

  return (
    <div className={`check-animation ${checkSide}`}>
      <div className="check-pulse">
        <span className="check-text">将军!</span>
      </div>
      <div className="check-flash"></div>
    </div>
  );
};

// ============ 游戏结束动画组件 ============

export const GameEndAnimation: React.FC<GameEndAnimationProps> = ({
  isGameOver,
  winner,
  winReason,
  config = DEFAULT_CONFIG,
}) => {
  const [showConfetti, setShowConfetti] = useState(false);
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (!config.enabled || !config.gameEndAnimation) {
      return;
    }

    if (isGameOver) {
      setShowMessage(true);
      if (winner && winner !== 'draw') {
        setShowConfetti(true);
        const timer = setTimeout(() => setShowConfetti(false), 5000);
        return () => clearTimeout(timer);
      }
    }
  }, [isGameOver, winner, config]);

  if (!isGameOver || !config.gameEndAnimation) return null;

  const getMessage = () => {
    if (!winner) return '游戏结束';
    if (winner === 'draw') return '和棋!';
    
    const winText = winner === 'red' ? '红方胜利!' : '黑方胜利!';
    const reasonText = {
      checkmate: '将死',
      stalemate: '困毙',
      resign: '认输',
      timeout: '超时',
    }[winReason || 'checkmate'];

    return `${winText} (${reasonText})`;
  };

  return (
    <div className="game-end-animation">
      {showConfetti && winner !== 'draw' && (
        <div className="confetti-container">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                backgroundColor: winner === 'red' ? '#dc2626' : '#1e293b',
              }}
            />
          ))}
        </div>
      )}
      <div className={`game-end-message ${winner || ''}`}>
        <div className="message-content">
          <span className="message-icon">{winner === 'draw' ? '🤝' : '🏆'}</span>
          <span className="message-text">{getMessage()}</span>
        </div>
      </div>
    </div>
  );
};

// ============ 吃子动画组件 ============

export const CaptureAnimation: React.FC<CaptureAnimationProps> = ({
  isCapturing,
  capturedPiece,
  position,
  config = DEFAULT_CONFIG,
}) => {
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (!config.enabled || !config.captureAnimation) {
      return;
    }

    if (isCapturing) {
      setActive(true);
      const timer = setTimeout(() => setActive(false), 800);
      return () => clearTimeout(timer);
    }
  }, [isCapturing, config]);

  if (!active || !config.captureAnimation) return null;

  return (
    <div className="capture-animation">
      <div className="capture-effect">
        <div className="capture-explosion"></div>
        <div className="capture-sparks">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="spark"
              style={{
                transform: `rotate(${i * 45}deg)`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

// ============ 动画配置面板组件 ============

export interface AnimationPanelProps {
  config: AnimationConfig;
  onChange: (config: AnimationConfig) => void;
}

export const AnimationPanel: React.FC<AnimationPanelProps> = ({
  config,
  onChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = useCallback((key: keyof AnimationConfig) => {
    if (key === 'enabled') {
      onChange({ ...config, [key]: !config[key] });
    } else {
      onChange({
        ...config,
        [key]: !config[key],
        enabled: true,
      });
    }
  }, [config, onChange]);

  const handleSpeedChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    onChange({ ...config, speedMultiplier: value });
  }, [config, onChange]);

  return (
    <div className="animation-panel">
      <button
        className="animation-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="动画设置"
      >
        🎬
      </button>

      {isOpen && (
        <div className="animation-settings">
          <h4>动画设置</h4>

          <label className="setting-item">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={() => handleToggle('enabled')}
            />
            <span>启用动画</span>
          </label>

          <label className="setting-item">
            <input
              type="checkbox"
              checked={config.moveAnimation}
              onChange={() => handleToggle('moveAnimation')}
              disabled={!config.enabled}
            />
            <span>走棋动画</span>
          </label>

          <label className="setting-item">
            <input
              type="checkbox"
              checked={config.captureAnimation}
              onChange={() => handleToggle('captureAnimation')}
              disabled={!config.enabled}
            />
            <span>吃子动画</span>
          </label>

          <label className="setting-item">
            <input
              type="checkbox"
              checked={config.checkAnimation}
              onChange={() => handleToggle('checkAnimation')}
              disabled={!config.enabled}
            />
            <span>将军动画</span>
          </label>

          <label className="setting-item">
            <input
              type="checkbox"
              checked={config.gameEndAnimation}
              onChange={() => handleToggle('gameEndAnimation')}
              disabled={!config.enabled}
            />
            <span>胜负动画</span>
          </label>

          <div className="setting-item">
            <span>动画速度：{config.speedMultiplier.toFixed(1)}x</span>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={config.speedMultiplier}
              onChange={handleSpeedChange}
              className="speed-slider"
            />
          </div>

          <button
            className="reset-btn"
            onClick={() => onChange(DEFAULT_CONFIG)}
          >
            恢复默认
          </button>
        </div>
      )}
    </div>
  );
};

// ============ 主导出组件 ============

interface BoardAnimationContainerProps {
  children: React.ReactNode;
  checkConfig?: CheckAnimationProps;
  gameEndConfig?: GameEndAnimationProps;
  captureConfig?: CaptureAnimationProps;
  animationConfig?: AnimationConfig;
  onConfigChange?: (config: AnimationConfig) => void;
}

/**
 * 棋盘动画容器组件
 * 包裹棋盘组件，提供完整的动画效果
 */
export const BoardAnimationContainer: React.FC<BoardAnimationContainerProps> = ({
  children,
  checkConfig,
  gameEndConfig,
  captureConfig,
  animationConfig = DEFAULT_CONFIG,
  onConfigChange,
}) => {
  return (
    <div className="board-animation-container" style={{
      '--animation-speed': animationConfig.speedMultiplier,
    } as React.CSSProperties}>
      {children}

      {checkConfig && (
        <CheckAnimation
          isCheck={checkConfig.isCheck}
          checkSide={checkConfig.checkSide}
          config={animationConfig}
        />
      )}

      {gameEndConfig && (
        <GameEndAnimation
          isGameOver={gameEndConfig.isGameOver}
          winner={gameEndConfig.winner}
          winReason={gameEndConfig.winReason}
          config={animationConfig}
        />
      )}

      {captureConfig && (
        <CaptureAnimation
          isCapturing={captureConfig.isCapturing}
          capturedPiece={captureConfig.capturedPiece}
          position={captureConfig.position}
          config={animationConfig}
        />
      )}

      {onConfigChange && (
        <AnimationPanel
          config={animationConfig}
          onChange={onConfigChange}
        />
      )}
    </div>
  );
};

export default BoardAnimationContainer;
