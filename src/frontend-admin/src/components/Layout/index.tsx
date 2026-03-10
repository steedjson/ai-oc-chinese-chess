import React, { useState } from 'react';
import { Breadcrumb, Layout, Menu, theme, Dropdown, Avatar, Space, Badge, Tooltip, Button } from 'antd';
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
  BellOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  ThunderboltFilled,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation, Link, Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/auth';
import { useHasPermission } from '../../hooks/useHasPermission';
import { Tag } from 'antd';
import '../styles/index.css';

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

const breadcrumbIconMap: Record<string, React.ReactNode> = {
  '/admin/dashboard': <DashboardOutlined />,
  '/admin/users': <TeamOutlined />,
  '/admin/games': <ThunderboltOutlined />,
  '/admin/matchmaking': <SwapOutlined />,
  '/admin/ai': <RobotOutlined />,
  '/admin/settings': <SettingOutlined />,
};

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { isSuperAdmin } = useHasPermission();
  const {
    token: { colorBgContainer },
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
    setLoading(true);
    navigate(key);
    setTimeout(() => setLoading(false), 300);
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
      onClick: () => navigate('/admin/settings'),
    },
    {
      type: 'divider' as const,
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
    const icon = breadcrumbIconMap[url];
    return {
      key: url,
      title: index === pathSnippets.length - 1 ? (
        <span className="breadcrumb-item-last">{name}</span>
      ) : (
        <Link to={url} className="breadcrumb-item-link">
          {icon && <span style={{ marginRight: 4 }}>{icon}</span>}
          {name}
        </Link>
      ),
    };
  });

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        breakpoint="lg"
        collapsedWidth={80}
        width={200}
        onBreakpoint={(broken) => {
          if (broken) setCollapsed(true);
        }}
        className="sider-collapse-transition"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 1001,
          boxShadow: collapsed ? 'none' : 'var(--shadow-sider)',
          background: 'var(--color-bg-dark)',
        }}
      >
        {/* 品牌 Logo 区域 */}
        <div
          className="page-fade-in"
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
            marginBottom: 8,
            padding: '0 16px',
          }}
        >
          {collapsed ? (
            <ThunderboltFilled style={{ fontSize: 24, color: 'white' }} />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <ThunderboltFilled style={{ fontSize: 24, color: 'white' }} />
              <span
                style={{
                  color: 'white',
                  fontSize: 16,
                  fontWeight: 600,
                  letterSpacing: 0.5,
                }}
              >
                中国象棋管理
              </span>
            </div>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            borderRight: 'none',
            background: 'transparent',
          }}
        />

        {/* 底部操作区 */}
        {!collapsed && (
          <div
            className="page-fade-in"
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              padding: '16px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'rgba(0, 0, 0, 0.2)',
            }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Tooltip title="帮助文档" placement="right">
                <Button
                  type="text"
                  icon={<QuestionCircleOutlined />}
                  style={{
                    width: '100%',
                    justifyContent: 'flex-start',
                    color: 'rgba(255, 255, 255, 0.65)',
                  }}
                  onClick={() => window.open('/docs', '_blank')}
                >
                  帮助文档
                </Button>
              </Tooltip>
            </Space>
          </div>
        )}
      </Sider>

      {/* 主布局区 */}
      <Layout
        className="content-margin-transition"
        style={{
          marginLeft: collapsed ? 80 : 200,
          minHeight: '100vh',
          background: 'var(--color-bg)',
        }}
      >
        {/* 顶部 Header */}
        <Header
          className="header-sticky-transition page-fade-in"
          style={{
            padding: '0 24px',
            background: 'rgba(255, 255, 255, 0.8)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 1000,
            boxShadow: 'var(--shadow-header)',
            borderBottom: '1px solid var(--color-border)',
            height: 'var(--header-height)',
          }}
        >
          {/* 左侧：折叠按钮 + 搜索 */}
          <Space size="large">
            <Tooltip title={collapsed ? '展开菜单' : '收起菜单'}>
              <span
                onClick={() => setCollapsed(!collapsed)}
                style={{
                  fontSize: 18,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '8px',
                  borderRadius: 'var(--radius)',
                  transition: 'all var(--duration) var(--ease-in-out)',
                }}
                className="trigger-hover"
              >
                {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              </span>
            </Tooltip>

            {/* 全局搜索入口 */}
            <Tooltip title="全局搜索 (Cmd+K)">
              <Button
                type="text"
                icon={<SearchOutlined />}
                style={{
                  color: 'var(--color-text-secondary)',
                  fontSize: 16,
                }}
                onClick={() => navigate('/admin/dashboard')}
              />
            </Tooltip>
          </Space>

          {/* 右侧：通知 + 用户 */}
          <Space size="large">
            {/* 通知铃铛 */}
            <Tooltip title="通知">
              <Badge count={3} offset={[-2, 4]} className="notification-badge-pulse">
                <Button
                  type="text"
                  icon={<BellOutlined style={{ fontSize: 18 }} />}
                  style={{
                    color: 'var(--color-text-secondary)',
                  }}
                />
              </Badge>
            </Tooltip>

            {/* 用户下拉菜单 */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <Space
                style={{
                  cursor: 'pointer',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-lg)',
                  transition: 'all var(--duration) var(--ease-in-out)',
                }}
                className="user-dropdown-hover"
              >
                <Avatar
                  style={{
                    backgroundColor: 'var(--color-primary)',
                    boxShadow: 'var(--shadow-float)',
                  }}
                  icon={<UserOutlined />}
                  size="default"
                />
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <span
                    style={{
                      fontWeight: 500,
                      color: 'var(--color-text)',
                      fontSize: 14,
                    }}
                  >
                    {user?.username || '管理员'}
                  </span>
                  {user?.role === 'super_admin' ? (
                    <Tag color="gold" style={{ margin: 0, fontSize: 12 }}>超级管理员</Tag>
                  ) : (
                    <Tag color="blue" style={{ margin: 0, fontSize: 12 }}>运维</Tag>
                  )}
                </div>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区 */}
        <Content
          className="page-fade-in"
          style={{
            margin: '0 16px',
            padding: 'var(--spacing-lg)',
            minHeight: 280,
          }}
        >
          {/* 面包屑 */}
          <Breadcrumb
            separator=">"
            items={breadcrumbItems}
            style={{
              margin: '0 0 var(--spacing-lg) 0',
              fontSize: 14,
            }}
          />

          {/* 内容卡片 */}
          <div
            className="card-enter"
            style={{
              padding: 'var(--spacing-lg)',
              background: 'var(--color-bg-card)',
              borderRadius: 'var(--radius-xl)',
              minHeight: 'calc(100vh - 180px)',
              boxShadow: 'var(--shadow-card)',
              transition: 'all var(--duration) var(--ease-in-out)',
            }}
          >
            {loading ? (
              <div className="skeleton-loading" style={{ height: '100%', borderRadius: 'var(--radius)' }} />
            ) : (
              <Outlet />
            )}
          </div>
        </Content>
      </Layout>

      {/* 样式增强 */}
      <style>{`
        /* 面包屑样式 */
        .breadcrumb-item-link {
          color: var(--color-primary);
          transition: all var(--duration) var(--ease-in-out);
          text-decoration: none;
          display: inline-flex;
          align-items: center;
        }
        
        .breadcrumb-item-link:hover {
          color: var(--color-primary-hover);
          text-decoration: underline;
        }
        
        .breadcrumb-item-last {
          color: var(--color-text);
          font-weight: 500;
        }
        
        /* 菜单项增强 */
        .ant-menu-dark .ant-menu-item-selected {
          background: var(--color-bg-dark-selected) !important;
          border-left: 3px solid var(--color-primary);
        }
        
        .ant-menu-dark .ant-menu-item:hover {
          background: rgba(255, 255, 255, 0.08);
        }
        
        /* 响应式优化 */
        @media (max-width: 992px) {
          .ant-layout-sider-collapsed + .ant-layout {
            margin-left: 80px !important;
          }
        }
        
        @media (max-width: 576px) {
          .ant-layout-header {
            padding: 0 16px !important;
            height: var(--header-height-mobile) !important;
          }
          
          .ant-layout-sider-collapsed + .ant-layout {
            margin-left: 0 !important;
          }
          
          .ant-layout-sider-collapsed {
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
          }
          
          .ant-layout-content {
            padding: var(--spacing-md) !important;
          }
        }
        
        /* 滚动条美化 */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: var(--color-bg);
        }
        
        ::-webkit-scrollbar-thumb {
          background: var(--color-border-secondary);
          border-radius: var(--radius-full);
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: var(--color-text-disabled);
        }
      `}</style>
    </Layout>
  );
};

export default AdminLayout;
