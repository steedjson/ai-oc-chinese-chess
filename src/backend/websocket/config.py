"""
WebSocket 配置文件

定义 WebSocket 全局配置：
- 心跳配置
- 超时配置
- 认证配置
- 日志配置
- 性能监控配置
"""
import logging
from typing import Optional


class WebSocketConfig:
    """
    WebSocket 全局配置类
    
    单例模式，所有配置集中管理
    """
    
    _instance: Optional['WebSocketConfig'] = None
    
    def __new__(cls) -> 'WebSocketConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # ========== 心跳配置 ==========
        # 心跳间隔（秒）
        self.HEARTBEAT_INTERVAL = 30
        
        # 超时阈值（秒）- 超过此时间无心跳判定掉线
        self.TIMEOUT_THRESHOLD = 90
        
        # 最大允许丢失心跳次数
        self.MAX_MISSED_HEARTBEATS = 3
        
        # ========== 超时配置 ==========
        # 连接超时（秒）
        self.CONNECT_TIMEOUT = 30
        
        # 断开连接超时（秒）
        self.DISCONNECT_TIMEOUT = 5
        
        # 消息处理超时（秒）
        self.MESSAGE_TIMEOUT = 10
        
        # ========== 认证配置 ==========
        # JWT 算法
        self.JWT_ALGORITHM = 'HS256'
        
        # Token URL 参数名
        self.TOKEN_URL_PARAM = 'token'
        
        # Token Header 名称
        self.TOKEN_HEADER_NAME = 'authorization'
        
        # Token 前缀
        self.TOKEN_PREFIX = 'Bearer '
        
        # ========== 日志配置 ==========
        # 是否记录连接日志
        self.LOG_CONNECTIONS = True
        
        # 是否记录消息日志
        self.LOG_MESSAGES = True
        
        # 是否记录错误日志
        self.LOG_ERRORS = True
        
        # 是否记录性能日志
        self.LOG_PERFORMANCE = True
        
        # 日志级别
        self.LOG_LEVEL = 'INFO'
        
        # ========== 性能监控配置 ==========
        # 是否启用性能监控
        self.ENABLE_PERFORMANCE_MONITORING = True
        
        # 性能指标采样间隔（秒）
        self.PERFORMANCE_SAMPLE_INTERVAL = 60
        
        # 慢消息阈值（毫秒）
        self.SLOW_MESSAGE_THRESHOLD_MS = 100
        
        # ========== 重连配置 ==========
        # 是否允许重连
        self.ALLOW_RECONNECT = True
        
        # 重连最大尝试次数
        self.MAX_RECONNECT_ATTEMPTS = 5
        
        # 重连基础延迟（毫秒）
        self.RECONNECT_BASE_DELAY_MS = 1000
        
        # 重连延迟指数基数
        self.RECONNECT_DELAY_EXPONENT = 2
        
        # ========== 并发配置 ==========
        # 单用户最大连接数
        self.MAX_CONNECTIONS_PER_USER = 3
        
        # 全局最大连接数（0 表示无限制）
        self.MAX_GLOBAL_CONNECTIONS = 10000
        
        # ========== 消息配置 ==========
        # 最大消息大小（字节）
        self.MAX_MESSAGE_SIZE = 65536  # 64KB
        
        # 消息队列容量
        self.MESSAGE_QUEUE_CAPACITY = 100
        
        # 广播超时（秒）
        self.BROADCAST_TIMEOUT = 5
        
        self._initialized = True
    
    def get_heartbeat_interval(self) -> int:
        """获取心跳间隔（秒）"""
        return self.HEARTBEAT_INTERVAL
    
    def get_timeout_threshold(self) -> int:
        """获取超时阈值（秒）"""
        return self.TIMEOUT_THRESHOLD
    
    def is_connection_healthy(self, last_heartbeat_time) -> bool:
        """
        检查连接是否健康
        
        Args:
            last_heartbeat_time: 上次心跳时间
        
        Returns:
            连接是否健康
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        elapsed = (now - last_heartbeat_time).total_seconds()
        
        return elapsed < self.TIMEOUT_THRESHOLD
    
    def get_reconnect_delay(self, attempt: int) -> int:
        """
        计算重连延迟（毫秒）
        
        使用指数退避算法：delay = base * (2 ^ attempt)
        
        Args:
            attempt: 重连尝试次数（从 0 开始）
        
        Returns:
            延迟毫秒数
        """
        import math
        delay = self.RECONNECT_BASE_DELAY_MS * math.pow(
            self.RECONNECT_DELAY_EXPONENT,
            min(attempt, 10)  # 限制最大指数
        )
        return int(min(delay, 30000))  # 最大 30 秒


# 全局配置实例
_config: Optional[WebSocketConfig] = None


def get_config() -> WebSocketConfig:
    """
    获取全局配置实例
    
    Returns:
        WebSocketConfig 实例
    """
    global _config
    if _config is None:
        _config = WebSocketConfig()
    return _config


def get_logger(name: str) -> logging.Logger:
    """
    获取 WebSocket 模块日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
    
    Returns:
        配置好的 Logger 实例
    """
    logger_name = f"chinese_chess.websocket.{name}"
    logger = logging.getLogger(logger_name)
    
    # 如果还没有处理器，添加控制台处理器
    if not logger.handlers:
        logger.setLevel(get_config().LOG_LEVEL)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(get_config().LOG_LEVEL)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger
