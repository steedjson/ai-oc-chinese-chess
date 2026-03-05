import React from 'react';
import { Layout, Typography, Space, Divider } from 'antd';
import {
  GithubOutlined,
  MailOutlined,
} from '@ant-design/icons';

const { Footer: AntFooter } = Layout;
const { Text, Link } = Typography;

const Footer: React.FC = () => {
  return (
    <AntFooter
      style={{
        background: 'var(--bg-secondary)',
        padding: '24px 0',
        marginTop: 'auto',
      }}
    >
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* 关于 */}
          <div>
            <h3 className="text-lg font-bold font-chinese mb-4 text-gradient">关于中国象棋</h3>
            <Text className="text-gray-600 dark:text-gray-400">
              中国象棋是中国传统的棋类游戏，历史悠久，深受人们喜爱。
              本平台提供 AI 对战、在线匹配、天梯排名等功能，
              让您随时随地享受象棋的乐趣。
            </Text>
          </div>

          {/* 快速链接 */}
          <div>
            <h3 className="text-lg font-bold font-chinese mb-4">快速链接</h3>
            <Space direction="vertical" size="small">
              <Link href="/" className="hover:text-red-600 transition-colors">首页</Link>
              <Link href="/ai-game" className="hover:text-red-600 transition-colors">AI 对战</Link>
              <Link href="/matchmaking" className="hover:text-red-600 transition-colors">匹配对战</Link>
              <Link href="/leaderboard" className="hover:text-red-600 transition-colors">排行榜</Link>
            </Space>
          </div>

          {/* 联系方式 */}
          <div>
            <h3 className="text-lg font-bold font-chinese mb-4">联系我们</h3>
            <Space direction="vertical" size="small">
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <GithubOutlined />
                <Link href="https://github.com/chinese-chess" target="_blank" rel="noopener noreferrer">
                  GitHub
                </Link>
              </div>
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <MailOutlined />
                <Link href="mailto:contact@chinese-chess.com">
                  contact@chinese-chess.com
                </Link>
              </div>
            </Space>
          </div>
        </div>

        <Divider className="my-6" />

        {/* 版权信息 */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <Text className="text-gray-500 text-sm">
            © {new Date().getFullYear()} 中国象棋平台。All rights reserved.
          </Text>
          <Space size="large">
            <Link href="/terms" className="text-gray-500 hover:text-red-600 text-sm">
              服务条款
            </Link>
            <Link href="/privacy" className="text-gray-500 hover:text-red-600 text-sm">
              隐私政策
            </Link>
            <Link href="/contact" className="text-gray-500 hover:text-red-600 text-sm">
              联系我们
            </Link>
          </Space>
        </div>
      </div>
    </AntFooter>
  );
};

export default Footer;
