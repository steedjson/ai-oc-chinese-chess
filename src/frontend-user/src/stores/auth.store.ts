import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  // 状态
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // 动作
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
  updateRating: (newRating: number) => void;
  updateStats: (stats: Partial<Pick<User, 'total_games' | 'wins' | 'losses' | 'draws'>>) => void;
}

const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      ...initialState,

      setUser: (user) => set({
        user,
        isAuthenticated: !!user,
        isLoading: false,
      }),

      setLoading: (isLoading) => set({ isLoading }),

      logout: () => set(initialState),

      updateRating: (newRating) => set((state) => ({
        user: state.user ? { ...state.user, rating: newRating } : null,
      })),

      updateStats: (stats) => set((state) => ({
        user: state.user ? { ...state.user, ...stats } : null,
      })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

export default useAuthStore;
