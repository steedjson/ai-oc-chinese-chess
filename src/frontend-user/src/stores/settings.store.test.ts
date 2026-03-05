/**
 * Settings Store 测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useSettingsStore } from './settings.store';

describe('Settings Store', () => {
  beforeEach(() => {
    useSettingsStore.getState().reset();
  });

  it('应该有默认设置', () => {
    const state = useSettingsStore.getState();
    expect(state.theme).toBe('light');
    expect(state.sound_enabled).toBe(true);
    expect(state.board_orientation).toBe('red');
  });

  it('应该能切换主题', () => {
    const { toggleTheme } = useSettingsStore.getState();
    
    toggleTheme();
    expect(useSettingsStore.getState().theme).toBe('dark');
    
    toggleTheme();
    expect(useSettingsStore.getState().theme).toBe('light');
  });

  it('应该能设置声音开关', () => {
    const { setSoundEnabled } = useSettingsStore.getState();
    
    setSoundEnabled(false);
    expect(useSettingsStore.getState().sound_enabled).toBe(false);
    
    setSoundEnabled(true);
    expect(useSettingsStore.getState().sound_enabled).toBe(true);
  });

  it('应该能重置设置', () => {
    const { setTheme, setSoundEnabled, reset } = useSettingsStore.getState();
    
    setTheme('dark');
    setSoundEnabled(false);
    reset();
    
    expect(useSettingsStore.getState().theme).toBe('light');
    expect(useSettingsStore.getState().sound_enabled).toBe(true);
  });

  it('应该能设置棋盘视角', () => {
    const { setBoardOrientation } = useSettingsStore.getState();
    setBoardOrientation('black');
    expect(useSettingsStore.getState().board_orientation).toBe('black');
  });
});
