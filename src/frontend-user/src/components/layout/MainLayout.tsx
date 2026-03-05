import React from 'react';
import { Layout, ConfigProvider, theme } from 'antd';
import { useSettingsStore } from '@/stores';
import Header from './Header';
import Footer from './Footer';
import zhCN from 'antd/locale/zh_CN';

const { Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { theme: currentTheme } = useSettingsStore();

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#dc2626',
          borderRadius: 8,
          fontFamily: "'Inter', 'Noto Serif SC', 'Songti SC', simsun, sans-serif",
        },
        components: {
          Button: {
            borderRadius: 8,
          },
          Card: {
            borderRadius: 12,
          },
        },
      }}
    >
      <Layout className="min-h-screen flex flex-col">
        <Header />
        <Content className="flex-1 w-full max-w-7xl mx-auto px-4 py-6">
          {children}
        </Content>
        <Footer />
      </Layout>
    </ConfigProvider>
  );
};

export default MainLayout;
