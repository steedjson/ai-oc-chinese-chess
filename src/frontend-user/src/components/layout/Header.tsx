import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Button, theme } from 'antd';
import {
  HomeOutlined,
  RobotOutlined,
  TeamOutlined,
  TrophyOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  MoonOutlined,
  SunOutlined,
} from '@ant-design/icons';
import { useAuthStore, useSettingsStore } from '@/stores';
import { authService } from '@/services';
import ServiceStatus from './ServiceStatus';
import type { MenuProps } from 'antd';

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { theme: currentTheme, toggleTheme } = useSettingsStore();
  const { token } = theme.useToken();

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: <Link to="/profile">个人中心</Link>,
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">设置</Link>,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: async () => {
        await authService.logout();
        logout();
        navigate('/');
      },
    },
  ];

  // 主导航菜单
  const mainMenuItems: MenuProps['items'] = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: 'ai-game',
      icon: <RobotOutlined />,
      label: <Link to="/ai-game">AI 对战</Link>,
    },
    {
      key: 'matchmaking',
      icon: <TeamOutlined />,
      label: <Link to="/matchmaking">匹配对战</Link>,
    },
    {
      key: 'leaderboard',
      icon: <TrophyOutlined />,
      label: <Link to="/leaderboard">排行榜</Link>,
    },
  ];

  return (
    <AntHeader
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        background: token.colorBgContainer,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      }}
    >
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600 to-yellow-500 flex items-center justify-center">
          <span className="text-white font-chinese text-xl font-bold">象</span>
        </div>
        <span className="text-xl font-bold font-chinese text-gradient hidden sm:inline">
          中国象棋
        </span>
      </Link>

      {/* 主导航 */}
      <Menu
        mode="horizontal"
        items={mainMenuItems}
        selectedKeys={[]}
        style={{
          flex: 1,
          minWidth: 0,
          borderBottom: 'none',
          background: 'transparent',
        }}
        className="hidden md:flex"
      />

      {/* 右侧操作区 */}
      <div className="flex items-center gap-3">
        {/* 服务状态 */}
        <ServiceStatus showDetails={true} />

        {/* 主题切换 */}
        <Button
          type="text"
          icon={currentTheme === 'light' ? <MoonOutlined /> : <SunOutlined />}
          onClick={toggleTheme}
          size="large"
        />

        {/* 用户信息 */}
        {isAuthenticated && user ? (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
            <div className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
              <Avatar
                src={user.avatar_url}
                icon={<UserOutlined />}
                size="large"
                className="bg-gradient-to-br from-red-500 to-yellow-500"
              />
              <div className="hidden lg:block">
                <div className="font-medium text-sm">{user.nickname || user.username}</div>
                <div className="text-xs text-gray-500">天梯分：{user.rating}</div>
              </div>
            </div>
          </Dropdown>
        ) : (
          <Button
            type="primary"
            onClick={() => navigate('/login')}
            className="bg-gradient-to-r from-red-600 to-yellow-500"
          >
            登录
          </Button>
        )}
      </div>
    </AntHeader>
  );
};

export default Header;
