import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ConfigProvider, Spin, message } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore, useSettingsStore } from '@/stores';
import { initTokens, authService } from '@/services';
import { MainLayout } from '@/components/layout';
import {
  HomePage,
  AIGamePage,
  MatchmakingPage,
  ProfilePage,
  LeaderboardPage,
} from '@/pages';
import './styles/index.css';

// 登录页面（简化版）
const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const { setUser } = useAuthStore();

  const handleLogin = async () => {
    if (!username || !password) {
      message.warning('请输入用户名和密码');
      return;
    }

    setLoading(true);
    try {
      const result = await authService.login({ username, password });
      if (result.success && result.data) {
        const userResult = await authService.getCurrentUser();
        if (userResult.success && userResult.data) {
          setUser(userResult.data);
          message.success('登录成功');
          window.location.href = '/';
        }
      } else {
        message.error(result.error?.message || '登录失败');
      }
    } catch {
      message.error('登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-500 to-yellow-500">
      <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-2xl">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-gradient-to-br from-red-600 to-yellow-500 flex items-center justify-center">
            <span className="text-white font-chinese text-3xl font-bold">象</span>
          </div>
          <h1 className="text-2xl font-bold font-chinese">中国象棋</h1>
          <p className="text-gray-600 mt-2">请登录</p>
        </div>

        <div className="space-y-4">
          <input
            type="text"
            placeholder="用户名"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="密码"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
          />
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-red-600 to-yellow-500 text-white rounded-lg font-medium hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? '登录中...' : '登录'}
          </button>
          <button
            onClick={() => navigate('/')}
            className="w-full py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition"
          >
            返回首页
          </button>
        </div>
      </div>
    </div>
  );
};

// 加载组件
const LoadingFallback: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center">
    <Spin size="large" tip="加载中..." />
  </div>
);

const App: React.FC = () => {
  const { theme: currentTheme } = useSettingsStore();
  const { setUser, setLoading, isLoading } = useAuthStore();

  // 初始化 Token 和加载用户信息
  useEffect(() => {
    const initAuth = async () => {
      initTokens();
      
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const result = await authService.getCurrentUser();
          if (result.success && result.data) {
            setUser(result.data);
          } else {
            setUser(null);
          }
        } catch (error) {
          console.error('Failed to load user:', error);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [setUser, setLoading]);

  if (isLoading) {
    return <LoadingFallback />;
  }

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: currentTheme === 'dark' ? undefined : undefined,
        token: {
          colorPrimary: '#dc2626',
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <MainLayout>
                <HomePage />
              </MainLayout>
            }
          />
          <Route
            path="/ai-game"
            element={
              <MainLayout>
                <AIGamePage />
              </MainLayout>
            }
          />
          <Route
            path="/matchmaking"
            element={
              <MainLayout>
                <MatchmakingPage />
              </MainLayout>
            }
          />
          <Route
            path="/profile"
            element={
              <MainLayout>
                <ProfilePage />
              </MainLayout>
            }
          />
          <Route
            path="/leaderboard"
            element={
              <MainLayout>
                <LeaderboardPage />
              </MainLayout>
            }
          />
          <Route
            path="/login"
            element={
              <MainLayout>
                <LoginPage />
              </MainLayout>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
