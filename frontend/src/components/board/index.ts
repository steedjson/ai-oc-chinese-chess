/**
 * 棋盘组件导出
 * 
 * @author OpenClaw 助手
 * @date 2026-03-06
 */

// 动画组件
export {
  BoardAnimationContainer,
  CheckAnimation,
  GameEndAnimation,
  CaptureAnimation,
  AnimationPanel,
} from './BoardAnimation';

export type {
  AnimationConfig,
  CheckAnimationProps,
  GameEndAnimationProps,
  CaptureAnimationProps,
  AnimationPanelProps,
} from './BoardAnimation';

// 移动组件
export {
  PieceMovementContainer,
  MovingPiece,
  LastMoveMarker,
  LegalMovesHint,
  PieceHighlight,
  usePieceMovement,
  parsePosition,
  positionToPixels,
} from './PieceMovement';

export type {
  Position,
  PieceData,
  MoveAnimation,
  PieceMovementConfig,
  MovingPieceProps,
  LastMoveMarkerProps,
  LegalMovesHintProps,
  PieceHighlightProps,
  PieceMovementContainerProps,
  UsePieceMovementReturn,
} from './PieceMovement';
