import React from 'react';
import { Card, Form, Input, Switch, Button, message, Typography, Select } from 'antd';
import { SettingOutlined, SecurityScanOutlined, BellOutlined } from '@ant-design/icons';

const { Title } = Typography;

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm();

  const handleSave = (values: any) => {
    console.log('保存设置:', values);
    message.success('设置保存成功');
  };

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>
        系统设置
      </Title>

      {/* 基本设置 */}
      <Card
        title={<><SettingOutlined /> 基本设置</>}
        style={{ marginBottom: 24 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            siteName: '中国象棋管理后台',
            siteDescription: '中国象棋游戏后台管理系统',
            language: 'zh-CN',
            timezone: 'Asia/Shanghai',
          }}
        >
          <Form.Item
            name="siteName"
            label="站点名称"
            rules={[{ required: true, message: '请输入站点名称' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="siteDescription"
            label="站点描述"
          >
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item
            name="language"
            label="系统语言"
          >
            <Select>
              <Select.Option value="zh-CN">简体中文</Select.Option>
              <Select.Option value="zh-TW">繁體中文</Select.Option>
              <Select.Option value="en-US">English</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="timezone"
            label="时区"
          >
            <Select>
              <Select.Option value="Asia/Shanghai">北京时间 (UTC+8)</Select.Option>
              <Select.Option value="Asia/Hong_Kong">香港时间 (UTC+8)</Select.Option>
              <Select.Option value="UTC">UTC</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存基本设置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 安全设置 */}
      <Card
        title={<><SecurityScanOutlined /> 安全设置</>}
        style={{ marginBottom: 24 }}
      >
        <Form
          layout="vertical"
          initialValues={{
            enableTwoFactor: false,
            sessionTimeout: 30,
            maxLoginAttempts: 5,
            enableIpWhitelist: false,
          }}
        >
          <Form.Item
            name="enableTwoFactor"
            label="启用双因素认证"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="sessionTimeout"
            label="会话超时时间（分钟）"
          >
            <Select style={{ width: 200 }}>
              <Select.Option value={15}>15 分钟</Select.Option>
              <Select.Option value={30}>30 分钟</Select.Option>
              <Select.Option value={60}>1 小时</Select.Option>
              <Select.Option value={120}>2 小时</Select.Option>
              <Select.Option value={480}>8 小时</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="maxLoginAttempts"
            label="最大登录尝试次数"
          >
            <Select style={{ width: 200 }}>
              <Select.Option value={3}>3 次</Select.Option>
              <Select.Option value={5}>5 次</Select.Option>
              <Select.Option value={10}>10 次</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="enableIpWhitelist"
            label="启用 IP 白名单"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary">保存安全设置</Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 通知设置 */}
      <Card
        title={<><BellOutlined /> 通知设置</>}
      >
        <Form
          layout="vertical"
          initialValues={{
            emailNotifications: true,
            systemAlerts: true,
            userRegistrationNotify: false,
            gameCompletionNotify: false,
          }}
        >
          <Form.Item
            name="emailNotifications"
            label="邮件通知"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="systemAlerts"
            label="系统告警"
            valuePropName="checked"
          >
            <Switch defaultChecked />
          </Form.Item>

          <Form.Item
            name="userRegistrationNotify"
            label="新用户注册通知"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="gameCompletionNotify"
            label="对局完成通知"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary">保存通知设置</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SettingsPage;
