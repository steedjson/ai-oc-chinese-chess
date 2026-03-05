import { create } from 'zustand';
import type { Game, Move, PieceColor, BoardState } from '@/types';

interface GameState {
  // 当前游戏
  currentGame: Game | null;
  
  // 棋盘状态
  boardState: BoardState | null;
  
  // 游戏状态
  isPlaying: boolean;
  isMyTurn: boolean;
  myColor: PieceColor | null;
  opponentColor: PieceColor | null;
  
  // UI 状态
  selectedPosition: string | null;
  validMoves: string[];
  lastMove: Move | null;
  isAnimating: boolean;
  
  // 游戏结果
  gameOver: boolean;
  winner: 'red' | 'black' | 'draw' | null;
  gameResult: string | null;
  
  // 动作
  setCurrentGame: (game: Game | null) => void;
  setBoardState: (state: BoardState) => void;
  setMyTurn: (isMyTurn: boolean) => void;
  setMyColor: (color: PieceColor | null) => void;
  setSelectedPosition: (position: string | null) => void;
  setValidMoves: (moves: string[]) => void;
  makeMove: (move: Move) => void;
  setGameOver: (winner: 'red' | 'black' | 'draw' | null, result: string) => void;
  resetGame: () => void;
  updateFen: (fen: string) => void;
}

const initialBoardState: BoardState = {
  fen: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
  turn: 'red',
  pieces: [],
  last_move: undefined,
  in_check: false,
  game_over: false,
};

const initialState = {
  currentGame: null,
  boardState: null,
  isPlaying: false,
  isMyTurn: false,
  myColor: null,
  opponentColor: null,
  selectedPosition: null,
  validMoves: [],
  lastMove: null,
  isAnimating: false,
  gameOver: false,
  winner: null,
  gameResult: null,
};

export const useGameStore = create<GameState>((set, get) => ({
  ...initialState,

  setCurrentGame: (game) => {
    if (!game) {
      set(initialState);
      return;
    }

    // 根据游戏类型确定玩家颜色
    const playerColor: 'red' | 'black' = game.game_type === 'ai' ? 'red' : 'red';

    set({
      currentGame: game,
      isPlaying: game.status === 'playing',
      myColor: playerColor,
      opponentColor: playerColor === 'red' ? 'black' : 'red',
      isMyTurn: game.status === 'playing',
      gameOver: game.status === 'finished',
      winner: game.winner || null,
    });
  },

  setBoardState: (state) => set({ boardState: state }),

  setMyTurn: (isMyTurn) => set({ isMyTurn }),

  setMyColor: (color) => set({ 
    myColor: color,
    opponentColor: color === 'red' ? 'black' : 'red',
  }),

  setSelectedPosition: (position) => set({ selectedPosition: position }),

  setValidMoves: (moves) => set({ validMoves: moves }),

  makeMove: (move) => {
    const { currentGame } = get();
    if (!currentGame) return;

    set({
      lastMove: move,
      selectedPosition: null,
      validMoves: [],
      isMyTurn: false,
      isAnimating: true,
    });

    // 更新 FEN
    setTimeout(() => {
      set({ isAnimating: false });
    }, 300);
  },

  setGameOver: (winner, result) => set({
    gameOver: true,
    winner,
    gameResult: result,
    isPlaying: false,
  }),

  resetGame: () => set(initialState),

  updateFen: (fen) => set((state) => {
    if (!state.boardState) return { boardState: { ...initialBoardState, fen } };
    
    const parts = fen.split(' ');
    const turn: PieceColor = parts[1] === 'w' ? 'red' : 'black';
    
    return {
      boardState: {
        ...state.boardState,
        fen,
        turn,
      },
      isMyTurn: state.myColor ? state.myColor === turn : false,
    };
  }),
}));

export default useGameStore;
