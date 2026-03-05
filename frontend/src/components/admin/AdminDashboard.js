import React, { useState, useEffect } from 'react';
import StatsOverview from './StatsOverview';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    activeGames: 0,
    totalPlayers: 0,
    aiUsageRate: 0,
    winRate: 0,
    gamesToday: 0,
    totalGames: 0
  });

  // Mock data loading - in a real app this would come from an API
  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setStats({
        activeGames: 24,
        totalPlayers: 1248,
        aiUsageRate: 68,
        winRate: 52,
        gamesToday: 156,
        totalGames: 8934
      });
    }, 500);
  }, []);

  return (
    <div className="admin-dashboard">
      <header className="dashboard-header">
        <h1>管理面板</h1>
        <p>实时监控系统运行状态</p>
      </header>

      <div className="dashboard-content">
        <StatsOverview stats={stats} />
        
        <div className="dashboard-grid">
          <div className="stat-card">
            <h3>活跃对局</h3>
            <div className="stat-value">{stats.activeGames}</div>
            <div className="stat-description">当前在线对局数量</div>
          </div>
          
          <div className="stat-card">
            <h3>总玩家数</h3>
            <div className="stat-value">{stats.totalPlayers}</div>
            <div className="stat-description">平台注册玩家总数</div>
          </div>
          
          <div className="stat-card">
            <h3>AI使用率</h3>
            <div className="stat-value">{stats.aiUsageRate}%</div>
            <div className="stat-description">AI对战占总对局比例</div>
          </div>
          
          <div className="stat-card">
            <h3>平均胜率</h3>
            <div className="stat-value">{stats.winRate}%</div>
            <div className="stat-description">玩家平均获胜概率</div>
          </div>
          
          <div className="stat-card">
            <h3>今日对局</h3>
            <div className="stat-value">{stats.gamesToday}</div>
            <div className="stat-description">24小时内完成对局数</div>
          </div>
          
          <div className="stat-card">
            <h3>总对局数</h3>
            <div className="stat-value">{stats.totalGames}</div>
            <div className="stat-description">平台累计对局总数</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;