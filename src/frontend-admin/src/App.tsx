import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// 页面
import LoginPage from './pages/Login';
import AdminLayout from './components/Layout';
import Dashboard from './pages/Dashboard';
import UsersPage from './pages/Users';
import GamesPage from './pages/Games';
import MatchmakingPage from './pages/Matchmaking';
import AIPage from './pages/AI';
import SettingsPage from './pages/Settings';

// 认证守卫
import { useAuthStore } from './stores/auth';

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{
      token: {
        colorPrimary: '#1890ff',
        borderRadius: 6,
      },
    }}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* 登录页 */}
            <Route path="/admin/login" element={<LoginPage />} />
            
            {/* 管理后台 */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="games" element={<GamesPage />} />
              <Route path="matchmaking" element={<MatchmakingPage />} />
              <Route path="ai" element={<AIPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            
            {/* 默认重定向 */}
            <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
