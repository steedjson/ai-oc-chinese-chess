import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AppSettings } from '@/types';

interface SettingsState extends AppSettings {
  // 动作
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
  setSoundEnabled: (enabled: boolean) => void;
  setAnimationEnabled: (enabled: boolean) => void;
  setShowMoveHints: (show: boolean) => void;
  setBoardOrientation: (orientation: 'red' | 'black') => void;
  setLanguage: (language: 'zh' | 'en') => void;
  reset: () => void;
}

const defaultSettings: AppSettings = {
  theme: 'light',
  sound_enabled: true,
  animation_enabled: true,
  show_move_hints: true,
  board_orientation: 'red',
  language: 'zh',
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      ...defaultSettings,

      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },

      toggleTheme: () => {
        const newTheme = get().theme === 'light' ? 'dark' : 'light';
        get().setTheme(newTheme);
      },

      setSoundEnabled: (enabled) => set({ sound_enabled: enabled }),

      setAnimationEnabled: (enabled) => set({ animation_enabled: enabled }),

      setShowMoveHints: (show) => set({ show_move_hints: show }),

      setBoardOrientation: (orientation) => set({ board_orientation: orientation }),

      setLanguage: (language) => set({ language }),

      reset: () => {
        set(defaultSettings);
        document.documentElement.setAttribute('data-theme', defaultSettings.theme);
      },
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({
        theme: state.theme,
        sound_enabled: state.sound_enabled,
        animation_enabled: state.animation_enabled,
        show_move_hints: state.show_move_hints,
        board_orientation: state.board_orientation,
        language: state.language,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          document.documentElement.setAttribute('data-theme', state.theme);
        }
      },
    }
  )
);

export default useSettingsStore;
