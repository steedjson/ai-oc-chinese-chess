"""
WebSocket 基础 Consumer

提供可复用的 Consumer 基类，包含：
- 心跳管理
- 认证处理
- 消息格式化
- 错误处理
- 日志记录
"""
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer

from .config import get_config, get_logger
from .middleware import JWTAuthMiddleware, PermissionMiddleware, LoggingMiddleware, PerformanceMonitorMiddleware

logger = get_logger('consumers')


class BaseConsumer(AsyncWebsocketConsumer):
    """
    WebSocket 基础 Consumer 类
    
    提供通用的 WebSocket 功能，所有 Consumer 应继承此类
    
    功能：
    - 心跳追踪和管理
    - 统一认证处理
    - 统一错误处理
    - 统一日志记录
    - 性能监控
    - 消息格式化
    
    使用示例：
        class GameConsumer(BaseConsumer):
            async def connect(self):
                # 使用父类的认证方法
                authenticated = await self.authenticate()
                if not authenticated:
                    return
                
                # 继续连接逻辑...
                await super().connect()
            
            async def receive(self, text_data):
                # 使用父类的消息处理方法
                await self.handle_message(text_data)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.config = get_config()
        self.logger = get_logger('consumers')
        self.auth_middleware = JWTAuthMiddleware()
        self.permission_middleware = PermissionMiddleware()
        self.logging_middleware = LoggingMiddleware()
        self.performance_monitor = PerformanceMonitorMiddleware()
        
        # 心跳管理
        self.last_heartbeat = None
        self.heartbeat_task = None
        
        # 用户信息
        self.user = None
        
        # 资源信息
        self.resource_id = None
        self.resource_type = None
    
    async def authenticate(self) -> bool:
        """
        验证连接身份
        
        Returns:
            是否认证成功
        """
        with self.performance_monitor.measure('authenticate'):
            try:
                user = await self.auth_middleware.authenticate(self.scope)
                
                if not user:
                    await self._send_connection_error('Invalid or expired token')
                    return False
                
                self.user = user
                self.logger.info(f"User {user.get('username')} authenticated")
                return True
                
            except Exception as e:
                self.logger.error(f"Authentication error: {e}")
                await self._send_connection_error('Authentication failed')
                return False
    
    def check_permission(self, resource_data: Dict[str, Any]) -> bool:
        """
        检查资源访问权限
        
        Args:
            resource_data: 资源数据
        
        Returns:
            是否有权限
        """
        if not self.user:
            return False
        
        try:
            if self.resource_type == 'game':
                return self.permission_middleware.check_game_permission(self.user, resource_data)
            elif self.resource_type == 'ai_game':
                return self.permission_middleware.check_ai_game_permission(self.user, resource_data)
            elif self.resource_type == 'matchmaking':
                return self.permission_middleware.check_matchmaking_permission(self.user)
            else:
                return True
                
        except Exception as e:
            self.logger.error(f"Permission check error: {e}")
            return False
    
    def start_heartbeat_tracking(self):
        """开始心跳追踪"""
        from django.utils import timezone
        self.last_heartbeat = timezone.now()
    
    def update_heartbeat(self):
        """更新心跳时间"""
        from django.utils import timezone
        self.last_heartbeat = timezone.now()
    
    def is_connection_healthy(self) -> bool:
        """
        检查连接是否健康
        
        Returns:
            连接是否健康
        """
        if not self.last_heartbeat:
            return True
        
        return self.config.is_connection_healthy(self.last_heartbeat)
    
    async def handle_heartbeat(self, data: Dict[str, Any]):
        """
        处理心跳消息
        
        Args:
            data: 消息数据
        """
        self.update_heartbeat()
        
        await self.send(text_data=self._format_message(
            'HEARTBEAT',
            {
                'acknowledged': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        ))
    
    def _extract_token_from_scope(self) -> Optional[str]:
        """
        从 scope 中提取 token
        
        Returns:
            Token 字符串，未找到返回 None
        """
        config = get_config()
        
        # 尝试从 URL 参数获取
        query_string = self.scope.get('query_string', b'').decode()
        if query_string:
            params = {}
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
            
            token = params.get(config.TOKEN_URL_PARAM)
            if token:
                return token
        
        # 尝试从 headers 获取
        headers = dict(self.scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode()
        
        if auth_header.startswith(config.TOKEN_PREFIX):
            return auth_header[len(config.TOKEN_PREFIX):]
        
        return None
    
    def _format_message(self, message_type: str, payload: Dict[str, Any]) -> str:
        """
        格式化消息
        
        Args:
            message_type: 消息类型
            payload: 消息负载
        
        Returns:
            JSON 字符串
        """
        message = {
            'type': message_type,
            'payload': payload,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.logging_middleware.log_message(
            message_type,
            'outbound',
            self.user.get('id') if self.user else 'anonymous',
            self.resource_id or 'unknown'
        )
        
        return json.dumps(message)
    
    def _format_error(self, code: str, message: str) -> str:
        """
        格式化错误消息
        
        Args:
            code: 错误码
            message: 错误信息
        
        Returns:
            JSON 字符串
        """
        error = {
            'type': 'ERROR',
            'payload': {
                'success': False,
                'error': {
                    'code': code,
                    'message': message
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.logging_middleware.log_error(
            Exception(message),
            {
                'error_code': code,
                'user_id': self.user.get('id') if self.user else 'anonymous',
                'resource_id': self.resource_id or 'unknown'
            }
        )
        
        return json.dumps(error)
    
    async def _send_connection_error(self, message: str):
        """发送连接错误并关闭"""
        await self.send(text_data=json.dumps({
            'type': 'ERROR',
            'payload': {
                'success': False,
                'error': {
                    'code': 'CONNECTION_ERROR',
                    'message': message
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
        await self.close(code=4001)
    
    async def _send_error(self, code: str, message: str):
        """发送错误消息"""
        await self.send(text_data=self._format_error(code, message))
    
    def _log_action(self, action: str, duration_ms: float, context: Optional[Dict[str, Any]] = None):
        """
        记录操作日志
        
        Args:
            action: 操作名称
            duration_ms: 耗时
            context: 上下文信息
        """
        self.logging_middleware.log_performance(
            action,
            duration_ms,
            context or {}
        )
    
    async def connect(self):
        """
        建立 WebSocket 连接
        
        子类应该调用 super().connect() 来初始化心跳追踪
        """
        self.start_heartbeat_tracking()
        
        self.logging_middleware.log_connection(
            self.user or {'id': 'anonymous', 'username': 'anonymous'},
            self.resource_id or 'unknown',
            self.resource_type or 'unknown'
        )
    
    async def disconnect(self, close_code: int):
        """
        断开 WebSocket 连接
        
        Args:
            close_code: 关闭代码
        """
        self.logging_middleware.log_disconnection(
            self.user or {'id': 'anonymous', 'username': 'anonymous'},
            self.resource_id or 'unknown',
            f'code_{close_code}'
        )
    
    async def receive(self, text_data: str):
        """
        接收消息
        
        子类应该重写此方法来处理具体消息
        
        Args:
            text_data: 接收到的文本数据
        """
        start_time = time.time()
        
        try:
            # 更新心跳
            self.update_heartbeat()
            
            # 解析消息
            data = json.loads(text_data)
            message_type = data.get('type')
            
            self.logging_middleware.log_message(
                message_type or 'UNKNOWN',
                'inbound',
                self.user.get('id') if self.user else 'anonymous',
                self.resource_id or 'unknown'
            )
            
            # 处理心跳
            if message_type == 'HEARTBEAT':
                await self.handle_heartbeat(data)
                return
            
            # 子类处理其他消息类型
            
        except json.JSONDecodeError:
            await self._send_error('INVALID_JSON', 'Invalid JSON format')
        except Exception as e:
            self.logger.error(f"Error in receive: {e}")
            await self._send_error('INTERNAL_ERROR', str(e))
        finally:
            # 记录性能
            duration_ms = (time.time() - start_time) * 1000
            self._log_action('receive_message', duration_ms)
