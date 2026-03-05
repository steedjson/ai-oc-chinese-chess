/**
 * Matchmaking Store 测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useMatchmakingStore } from './matchmaking.store';

describe('Matchmaking Store', () => {
  beforeEach(() => {
    useMatchmakingStore.getState().reset();
  });

  it('应该有初始状态', () => {
    const state = useMatchmakingStore.getState();
    expect(state.isMatching).toBe(false);
    expect(state.status).toBeNull();
    expect(state.matchFound).toBeNull();
  });

  it('应该能开始匹配', () => {
    const { startMatching } = useMatchmakingStore.getState();
    
    startMatching();
    
    const state = useMatchmakingStore.getState();
    expect(state.isMatching).toBe(true);
    expect(state.isSearching).toBe(true);
    expect(state.matchStartTime).toBeDefined();
  });

  it('应该能更新状态', () => {
    const { updateStatus } = useMatchmakingStore.getState();
    
    updateStatus({
      is_matching: true,
      search_range: 200,
      queue_position: 5,
      estimated_wait_time: 30,
    });
    
    const state = useMatchmakingStore.getState();
    expect(state.searchRange).toBe(200);
    expect(state.queuePosition).toBe(5);
  });

  it('应该能处理匹配成功', () => {
    const { setMatchFound } = useMatchmakingStore.getState();
    const mockMatch = { 
      match_id: 'm123', 
      opponent: { username: 'opp' },
      expires_at: '...',
      player_color: 'red' as any
    };
    
    setMatchFound(mockMatch);
    
    const state = useMatchmakingStore.getState();
    expect(state.matchFound).toEqual(mockMatch);
    expect(state.showMatchDialog).toBe(true);
    expect(state.isMatching).toBe(false);
  });

  it('应该能重置状态', () => {
    const { startMatching, reset } = useMatchmakingStore.getState();
    startMatching();
    reset();
    expect(useMatchmakingStore.getState().isMatching).toBe(false);
  });
});
