"""
WebSocket 中间件

提供 WebSocket 连接处理的中间件：
- JWT 认证中间件
- 权限检查中间件
- 日志中间件
- 性能监控中间件
"""
import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps

from channels.db import database_sync_to_async

from .config import get_config, get_logger
from authentication.services import TokenService

logger = get_logger('middleware')


class JWTAuthMiddleware:
    """
    JWT 认证中间件
    
    验证 WebSocket 连接的 JWT Token，提取用户信息
    
    使用方式：
        middleware = JWTAuthMiddleware()
        user = await middleware.authenticate(scope)
        if not user:
            await self.close(code=4001)  # Django Channels 只支持 code 参数
            return
    """
    
    async def authenticate(self, scope: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        验证连接身份
        
        Args:
            scope: ASGI scope 字典
        
        Returns:
            用户信息字典，验证失败返回 None
        """
        try:
            # 提取 token
            token = self._extract_token(scope)
            if not token:
                logger.warning("No token provided in WebSocket connection")
                return None
            
            # 验证 JWT token
            payload = await self._verify_token(token)
            if not payload:
                logger.warning("Invalid or expired JWT token")
                return None
            
            # 获取用户信息
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning("No user_id in JWT payload")
                return None
            
            user = await self._get_user_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return None
            
            logger.info(f"User {user.get('username')} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def _extract_token(self, scope: Dict[str, Any]) -> Optional[str]:
        """
        从 scope 中提取 token
        
        支持两种方式：
        1. URL 参数：?token=xxx
        2. Header: Authorization: Bearer xxx
        
        Args:
            scope: ASGI scope 字典
        
        Returns:
            Token 字符串，未找到返回 None
        """
        config = get_config()
        
        # 尝试从 URL 参数获取
        query_string = scope.get('query_string', b'').decode()
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
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', b'').decode()
        
        if auth_header.startswith(config.TOKEN_PREFIX):
            return auth_header[len(config.TOKEN_PREFIX):]
        
        return None
    
    async def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 JWT token
        
        Args:
            token: JWT token
        
        Returns:
            Token payload，验证失败返回 None
        """
        try:
            # TokenService.verify_token 是同步方法，直接调用
            # 使用 asyncio.get_event_loop().run_in_executor 在后台线程中执行
            import asyncio
            loop = asyncio.get_event_loop()
            payload = await loop.run_in_executor(None, TokenService.verify_token, token)
            return payload
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    @database_sync_to_async
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取用户信息
        
        Args:
            user_id: 用户 ID
        
        Returns:
            用户信息字典，未找到返回 None
        """
        try:
            from users.models import User
            user = User.objects.get(id=user_id)
            return {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            }
        except Exception:
            return None


class PermissionMiddleware:
    """
    权限检查中间件
    
    检查用户是否有权限访问特定资源
    
    使用方式：
        middleware = PermissionMiddleware()
        if not middleware.check_game_permission(user, game_data):
            await self.close(code=4003)  # Django Channels 只支持 code 参数
            return
    """
    
    def check_game_permission(self, user: Dict[str, Any], game_data: Dict[str, Any]) -> bool:
        """
        检查用户是否有权限加入游戏
        
        Args:
            user: 用户信息
            game_data: 游戏数据（包含 red_player_id, black_player_id）
        
        Returns:
            是否有权限
        """
        try:
            user_id = str(user['id'])
            red_player_id = str(game_data.get('red_player_id', ''))
            black_player_id = str(game_data.get('black_player_id', ''))
            
            # 检查是否是游戏参与者
            if user_id == red_player_id or user_id == black_player_id:
                return True
            
            # 未来可以扩展：检查是否允许观战
            # if game_data.get('allow_spectators'):
            #     return True
            
            logger.warning(f"User {user_id} not authorized to join game")
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def check_ai_game_permission(self, user: Dict[str, Any], ai_game_data: Dict[str, Any]) -> bool:
        """
        检查用户是否有权限访问 AI 对局
        
        Args:
            user: 用户信息
            ai_game_data: AI 对局数据（包含 player_id）
        
        Returns:
            是否有权限
        """
        try:
            user_id = str(user['id'])
            player_id = str(ai_game_data.get('player_id', ''))
            
            return user_id == player_id
            
        except Exception as e:
            logger.error(f"AI game permission check error: {e}")
            return False
    
    def check_matchmaking_permission(self, user: Dict[str, Any]) -> bool:
        """
        检查用户是否有权限使用匹配系统
        
        Args:
            user: 用户信息
        
        Returns:
            是否有权限（默认所有活跃用户都可以）
        """
        try:
            return user.get('is_active', True)
            
        except Exception as e:
            logger.error(f"Matchmaking permission check error: {e}")
            return False


class LoggingMiddleware:
    """
    日志中间件
    
    记录 WebSocket 连接、消息、错误等日志
    
    使用方式：
        middleware = LoggingMiddleware()
        middleware.log_connection(user, game_id)
        middleware.log_message(message_type, direction)
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger('logging')
    
    def log_connection(self, user: Dict[str, Any], resource_id: str, resource_type: str = 'game'):
        """
        记录连接日志
        
        Args:
            user: 用户信息
            resource_id: 资源 ID（游戏 ID、房间 ID 等）
            resource_type: 资源类型
        """
        if not self.config.LOG_CONNECTIONS:
            return
        
        self.logger.info(
            f"WebSocket connection established",
            extra={
                'user_id': user.get('id'),
                'username': user.get('username'),
                'resource_type': resource_type,
                'resource_id': resource_id
            }
        )
    
    def log_disconnection(self, user: Dict[str, Any], resource_id: str, reason: str = 'normal'):
        """
        记录断开连接日志
        
        Args:
            user: 用户信息
            resource_id: 资源 ID
            reason: 断开原因
        """
        if not self.config.LOG_CONNECTIONS:
            return
        
        self.logger.info(
            f"WebSocket connection disconnected",
            extra={
                'user_id': user.get('id'),
                'username': user.get('username'),
                'resource_id': resource_id,
                'reason': reason
            }
        )
    
    def log_message(self, message_type: str, direction: str, user_id: str, resource_id: str):
        """
        记录消息日志
        
        Args:
            message_type: 消息类型
            direction: 方向 ('inbound' 或 'outbound')
            user_id: 用户 ID
            resource_id: 资源 ID
        """
        if not self.config.LOG_MESSAGES:
            return
        
        self.logger.debug(
            f"WebSocket message: {message_type} ({direction})",
            extra={
                'user_id': user_id,
                'resource_id': resource_id,
                'message_type': message_type,
                'direction': direction
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        if not self.config.LOG_ERRORS:
            return
        
        self.logger.error(
            f"WebSocket error: {str(error)}",
            extra=context
        )
    
    def log_performance(self, action: str, duration_ms: float, context: Dict[str, Any]):
        """
        记录性能日志
        
        Args:
            action: 操作名称
            duration_ms: 耗时（毫秒）
            context: 上下文信息
        """
        if not self.config.LOG_PERFORMANCE:
            return
        
        # 检查是否是慢操作
        is_slow = duration_ms > self.config.SLOW_MESSAGE_THRESHOLD_MS
        
        log_level = 'warning' if is_slow else 'debug'
        
        getattr(self.logger, log_level)(
            f"WebSocket performance: {action} took {duration_ms:.2f}ms",
            extra={
                'action': action,
                'duration_ms': duration_ms,
                'is_slow': is_slow,
                **context
            }
        )


class PerformanceMonitorMiddleware:
    """
    性能监控中间件
    
    监控 WebSocket 操作的性能指标
    
    使用方式：
        middleware = PerformanceMonitorMiddleware()
        with middleware.measure('process_move'):
            # 执行操作
            pass
    """
    
    def __init__(self):
        self.config = get_config()
        self.logging_middleware = LoggingMiddleware()
    
    def measure(self, action: str):
        """
        性能测量装饰器
        
        Args:
            action: 操作名称
        
        Returns:
            上下文管理器
        """
        return PerformanceContext(action, self.logging_middleware)


class PerformanceContext:
    """性能测量上下文管理器"""
    
    def __init__(self, action: str, logging_middleware: LoggingMiddleware):
        self.action = action
        self.logging_middleware = logging_middleware
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.logging_middleware.log_performance(
            self.action,
            duration_ms,
            {}
        )
        return False  # 不抑制异常


# 装饰器函数
def require_auth(func: Callable) -> Callable:
    """
    要求认证的装饰器
    
    使用方式：
        @require_auth
        async def connect(self):
            # 已认证的用户
            pass
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        middleware = JWTAuthMiddleware()
        user = await middleware.authenticate(self.scope)
        
        if not user:
            await self.close(code=4001)  # Django Channels 只支持 code 参数
            return
        
        # 将用户信息注入到 scope
        self.scope['user'] = user
        return await func(self, *args, **kwargs)
    
    return wrapper
