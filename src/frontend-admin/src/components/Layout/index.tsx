import React, { useState } from 'react';
import { Breadcrumb, Layout, Menu, theme, Dropdown, Avatar, Space } from 'antd';
import {
  DashboardOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  SwapOutlined,
  RobotOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation, Link, Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/auth';
import { useHasPermission } from '../../hooks/useHasPermission';
import { Tag } from 'antd';

const { Header, Sider, Content } = Layout;

const breadcrumbNameMap: Record<string, string> = {
  '/admin': '首页',
  '/admin/dashboard': '仪表盘',
  '/admin/users': '用户管理',
  '/admin/games': '游戏管理',
  '/admin/matchmaking': '匹配管理',
  '/admin/ai': 'AI 管理',
  '/admin/settings': '系统设置',
};

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { isSuperAdmin } = useHasPermission();
  const {
    token: { colorBgContainer, borderRadiusLG, boxShadowSecondary },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/admin/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/admin/users',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: '/admin/games',
      icon: <ThunderboltOutlined />,
      label: '游戏管理',
    },
    {
      key: '/admin/matchmaking',
      icon: <SwapOutlined />,
      label: '匹配管理',
    },
    {
      key: '/admin/ai',
      icon: <RobotOutlined />,
      label: 'AI 管理',
    },
    ...(isSuperAdmin ? [
      {
        key: '/admin/settings',
        icon: <SettingOutlined />,
        label: '系统设置',
      },
    ] : []),
  ];

  // 路由拦截：如果是 ops 且尝试访问设置页面，重定向到仪表盘
  if (location.pathname === '/admin/settings' && !isSuperAdmin) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/admin/settings'), // 假设个人中心在设置页或有专门页面
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: handleLogout,
    },
  ];

  const pathSnippets = location.pathname.split('/').filter((i) => i);
  const breadcrumbItems = pathSnippets.map((_, index) => {
    const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
    const name = breadcrumbNameMap[url] || url;
    return {
      key: url,
      title: index === pathSnippets.length - 1 ? (
        <span>{name}</span>
      ) : (
        <Link to={url}>{name}</Link>
      ),
    };
  });

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        breakpoint="lg"
        collapsedWidth={80}
        onBreakpoint={(broken) => {
          if (broken) setCollapsed(true);
        }}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 1001, // 提高 Z-Index 确保在 Header 之上且阴影可见
          boxShadow: collapsed ? 'none' : '2px 0 8px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.2s cubic-bezier(0.645, 0.045, 0.355, 1)',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: collapsed ? 24 : 18,
            fontWeight: 'bold',
            background: 'rgba(255, 255, 255, 0.05)',
            marginBottom: 8,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {collapsed ? '♟️' : '中国象棋管理'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout 
        style={{ 
          marginLeft: collapsed ? 80 : 200, 
          transition: 'margin-left 0.2s cubic-bezier(0.645, 0.045, 0.355, 1)',
          minHeight: '100vh'
        }}
      >
        <Header
          style={{
            padding: '0 24px',
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 1000,
            boxShadow: '0 1px 4px rgba(0, 21, 41, 0.08)',
            borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          }}
        >
          <span
            onClick={() => setCollapsed(!collapsed)}
            style={{ 
              fontSize: 18, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '4px 8px',
              borderRadius: 4,
              transition: 'background 0.3s'
            }}
            className="trigger-hover"
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </span>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
            <Space 
              style={{ 
                cursor: 'pointer', 
                padding: '0 12px', 
                borderRadius: borderRadiusLG,
                transition: 'all 0.3s',
              }}
              className="user-dropdown-hover"
            >
              <Avatar 
                style={{ 
                  backgroundColor: '#1890ff',
                  boxShadow: '0 2px 4px rgba(24, 144, 255, 0.2)'
                }} 
                icon={<UserOutlined />} 
              />
              <span style={{ fontWeight: 500, color: 'rgba(0, 0, 0, 0.85)' }}>
                {user?.username || '管理员'}
              </span>
              {user?.role === 'super_admin' ? (
                <Tag color="gold" style={{ marginRight: 0 }}>超级管理员</Tag>
              ) : (
                <Tag color="blue" style={{ marginRight: 0 }}>运维</Tag>
              )}
            </Space>
          </Dropdown>
        </Header>
        <Content
          style={{
            margin: '0 16px',
            padding: '16px 24px',
            minHeight: 280,
          }}
        >
          <Breadcrumb 
            items={breadcrumbItems} 
            style={{ margin: '16px 0' }}
          />
          <div
            style={{
              padding: 24,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              minHeight: 'calc(100vh - 180px)',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
      <style>{`
        .trigger-hover:hover { background: rgba(0, 0, 0, 0.025); }
        .user-dropdown-hover:hover { background: rgba(0, 0, 0, 0.025); }
        @media (max-width: 992px) {
          .ant-layout-sider-collapsed + .ant-layout { margin-left: 80px !important; }
          .ant-layout-sider:not(.ant-layout-sider-collapsed) + .ant-layout { margin-left: 200px !important; }
        }
        @media (max-width: 576px) {
          .ant-layout-sider-collapsed + .ant-layout { margin-left: 0 !important; }
          .ant-layout-sider-collapsed { width: 0 !important; min-width: 0 !important; max-width: 0 !important; }
        }
      `}</style>
    </Layout>
  );
};

export default AdminLayout;
