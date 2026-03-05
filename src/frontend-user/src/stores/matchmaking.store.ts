import { create } from 'zustand';
import type { MatchmakingStatus, MatchFound } from '@/types';

interface MatchmakingState {
  // 匹配状态
  isMatching: boolean;
  status: MatchmakingStatus | null;
  matchFound: MatchFound | null;
  
  // 匹配信息
  queuePosition: number | null;
  estimatedWaitTime: number | null;
  searchRange: number;
  matchStartTime: Date | null;
  
  // UI 状态
  isSearching: boolean;
  showMatchDialog: boolean;
  
  // 动作
  startMatching: () => void;
  stopMatching: () => void;
  updateStatus: (status: MatchmakingStatus) => void;
  setMatchFound: (match: MatchFound | null) => void;
  setShowMatchDialog: (show: boolean) => void;
  reset: () => void;
}

const initialState = {
  isMatching: false,
  status: null,
  matchFound: null,
  queuePosition: null,
  estimatedWaitTime: null,
  searchRange: 100,
  matchStartTime: null,
  isSearching: false,
  showMatchDialog: false,
};

export const useMatchmakingStore = create<MatchmakingState>((set) => ({
  ...initialState,

  startMatching: () => set({
    isMatching: true,
    isSearching: true,
    matchStartTime: new Date(),
    status: {
      is_matching: true,
      search_range: 100,
      started_at: new Date().toISOString(),
    },
  }),

  stopMatching: () => set({
    isMatching: false,
    isSearching: false,
    status: null,
  }),

  updateStatus: (status) => set({
    status,
    isMatching: status.is_matching,
    queuePosition: status.queue_position || null,
    estimatedWaitTime: status.estimated_wait_time || null,
    searchRange: status.search_range,
  }),

  setMatchFound: (match) => set({
    matchFound: match,
    showMatchDialog: !!match,
    isMatching: false,
    isSearching: false,
  }),

  setShowMatchDialog: (show) => set({ showMatchDialog: show }),

  reset: () => set(initialState),
}));

export default useMatchmakingStore;
