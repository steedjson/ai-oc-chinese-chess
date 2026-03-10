import React, { useEffect, useState } from 'react';
import { Badge, Tooltip, Modal, Button, Spin } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

type ServiceStatus = 'online' | 'offline' | 'degraded' | 'checking';

interface ServiceStatusComponentProps {
  checkInterval?: number; // 检查间隔（毫秒）
  showDetails?: boolean; // 显示详细信息
}

interface HealthData {
  status: 'healthy' | 'unhealthy';
  components: {
    django?: { status: string; version?: string };
    database?: { status: string; backend?: string; error?: string };
    cache?: { status: string; backend?: string; error?: string };
    python?: { status: string; version?: string };
  };
}

/**
 * 服务状态检测组件
 * 
 * 功能：
 * - 定期检查后端健康状态
 * - 显示服务状态指示器
 * - 自动重试机制
 * - 详细健康信息展示
 */
export const ServiceStatus: React.FC<ServiceStatusComponentProps> = ({
  checkInterval = 30000,
  showDetails = false,
}) => {
  const [status, setStatus] = useState<ServiceStatus>('checking');
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [showModal, setShowModal] = useState(false);

  /**
   * 检查后端健康状态
   */
  const checkHealth = async () => {
    try {
      setStatus('checking');
      
      const response = await fetch('/api/v1/health/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // 5 秒超时
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: HealthData = await response.json();
      setHealthData(data);
      
      if (data.status === 'healthy') {
        setStatus('online');
        setRetryCount(0); // 重置重试计数
      } else {
        setStatus('degraded');
      }
      
      setLastCheck(new Date());
    } catch (error) {
      console.error('Health check failed:', error);
      setStatus('offline');
      setLastCheck(new Date());
      
      // 自动重试（最多 3 次）
      if (retryCount < 3) {
        setRetryCount(prev => prev + 1);
        // 指数退避：1s, 2s, 4s
        const retryDelay = Math.min(1000 * Math.pow(2, retryCount), 4000);
        setTimeout(() => {
          checkHealth();
        }, retryDelay);
      }
    }
  };

  /**
   * 手动重试
   */
  const handleRetry = () => {
    setRetryCount(0);
    checkHealth();
  };

  // 初始检查和定时检查
  useEffect(() => {
    checkHealth();
    
    const interval = setInterval(() => {
      checkHealth();
    }, checkInterval);
    
    return () => clearInterval(interval);
  }, [checkInterval]);

  /**
   * 获取状态图标
   */
  const getStatusIcon = () => {
    switch (status) {
      case 'online':
        return <CheckCircleOutlined className="text-green-500 text-lg" />;
      case 'offline':
        return <CloseCircleOutlined className="text-red-500 text-lg" />;
      case 'degraded':
        return <WarningOutlined className="text-yellow-500 text-lg" />;
      case 'checking':
        return <Spin size="small" />;
      default:
        return null;
    }
  };

  /**
   * 获取状态文本
   */
  const getStatusText = () => {
    switch (status) {
      case 'online':
        return '服务正常';
      case 'offline':
        return '服务不可用';
      case 'degraded':
        return '服务异常';
      case 'checking':
        return '检查中...';
      default:
        return '未知';
    }
  };

  /**
   * 渲染健康详情
   */
  const renderHealthDetails = () => {
    if (!healthData) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="font-medium">总体状态</span>
          <Badge
            status={healthData.status === 'healthy' ? 'success' : 'error'}
            text={healthData.status === 'healthy' ? '健康' : '异常'}
          />
        </div>

        <div className="space-y-2">
          <h4 className="font-medium">组件状态</h4>
          {Object.entries(healthData.components).map(([name, component]) => (
            <div key={name} className="flex items-center justify-between text-sm">
              <span className="capitalize">{name}</span>
              <div className="flex items-center gap-2">
                <Badge
                  status={
                    component.status === 'healthy'
                      ? 'success'
                      : component.status === 'unhealthy'
                      ? 'error'
                      : 'default'
                  }
                  text={component.status}
                />
                {component.version && (
                  <span className="text-gray-400">v{component.version}</span>
                )}
                {component.error && (
                  <Tooltip title={component.error}>
                    <WarningOutlined className="text-yellow-500" />
                  </Tooltip>
                )}
              </div>
            </div>
          ))}
        </div>

        {lastCheck && (
          <div className="text-xs text-gray-400">
            最后检查：{lastCheck.toLocaleTimeString('zh-CN')}
          </div>
        )}

        {status === 'offline' && (
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleRetry}
            block
          >
            重试连接
          </Button>
        )}
      </div>
    );
  };

  return (
    <>
      {/* 状态指示器 */}
      <Tooltip
        title={
          <div>
            <div>{getStatusText()}</div>
            {showDetails && lastCheck && (
              <div className="text-xs text-gray-400 mt-1">
                最后检查：{lastCheck.toLocaleTimeString('zh-CN')}
              </div>
            )}
          </div>
        }
      >
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80"
          onClick={() => setShowModal(true)}
        >
          {getStatusIcon()}
          <span className="text-sm hidden md:inline">{getStatusText()}</span>
        </div>
      </Tooltip>

      {/* 详情弹窗 */}
      <Modal
        title="后端服务状态"
        open={showModal}
        onCancel={() => setShowModal(false)}
        footer={
          status === 'offline' ? (
            <Button type="primary" icon={<ReloadOutlined />} onClick={handleRetry}>
              重试连接
            </Button>
          ) : (
            <Button onClick={() => setShowModal(false)}>关闭</Button>
          )
        }
      >
        {renderHealthDetails()}
      </Modal>
    </>
  );
};

export default ServiceStatus;
