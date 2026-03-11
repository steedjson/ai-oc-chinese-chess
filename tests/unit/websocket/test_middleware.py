"""
WebSocket Middleware 测试
测试 WebSocket 中间件核心功能：JWT 认证、权限检查、日志记录、性能监控
"""
import pytest
import time
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from channels.db import database_sync_to_async

from websocket.middleware import (
    JWTAuthMiddleware, PermissionMiddleware, LoggingMiddleware,
    PerformanceMonitorMiddleware, PerformanceContext, require_auth
)


# ==================== JWTAuthMiddleware 测试 ====================

class TestJWTAuthMiddlewareInit:
    """JWTAuthMiddleware 初始化测试"""
    
    def test_middleware_initialization(self):
        """测试中间件初始化"""
        middleware = JWTAuthMiddleware()
        assert middleware is not None


class TestExtractToken:
    """Token 提取测试"""
    
    def test_extract_token_from_url_param(self):
        """测试从 URL 参数提取 token"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'token=test_token_123'
        }
        
        token = middleware._extract_token(scope)
        
        assert token == 'test_token_123'
    
    def test_extract_token_from_url_param_multiple(self):
        """测试从多个 URL 参数中提取 token"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'game_id=123&token=test_token_456&other=value'
        }
        
        token = middleware._extract_token(scope)
        
        assert token == 'test_token_456'
    
    def test_extract_token_from_header(self):
        """测试从 Header 提取 token"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'',
            'headers': [
                (b'authorization', b'Bearer test_token_789')
            ]
        }
        
        token = middleware._extract_token(scope)
        
        assert token == 'test_token_789'
    
    def test_extract_token_no_token(self):
        """测试无 token 情况"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'',
            'headers': []
        }
        
        token = middleware._extract_token(scope)
        
        assert token is None
    
    def test_extract_token_empty_query_string(self):
        """测试空查询字符串"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b''
        }
        
        token = middleware._extract_token(scope)
        
        assert token is None
    
    def test_extract_token_malformed_query(self):
        """测试格式错误的查询字符串"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'invalid_format'
        }
        
        token = middleware._extract_token(scope)
        
        assert token is None
    
    def test_extract_token_header_no_bearer(self):
        """测试 Header 无 Bearer 前缀"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b'',
            'headers': [
                (b'authorization', b'Test token_123')
            ]
        }
        
        token = middleware._extract_token(scope)
        
        assert token is None


class TestAuthenticate:
    """认证测试"""
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    @patch('websocket.middleware.User')
    async def test_authenticate_success(self, mock_user_model, mock_token_service):
        """测试认证成功"""
        middleware = JWTAuthMiddleware()
        
        # Mock token 验证
        mock_token_service.verify_token.return_value = {
            'user_id': '1',
            'username': 'testuser',
            'exp': time.time() + 3600
        }
        
        # Mock 用户查询
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.is_active = True
        mock_user_model.objects.get.return_value = mock_user
        
        scope = {
            'query_string': b'token=test_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is not None
        assert user['id'] == '1'
        assert user['username'] == 'testuser'
        assert user['email'] == 'test@example.com'
        assert user['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_authenticate_no_token(self):
        """测试无 token 认证失败"""
        middleware = JWTAuthMiddleware()
        
        scope = {
            'query_string': b''
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is None
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    async def test_authenticate_invalid_token(self, mock_token_service):
        """测试无效 token"""
        middleware = JWTAuthMiddleware()
        
        # Mock token 验证失败
        mock_token_service.verify_token.side_effect = Exception("Invalid token")
        
        scope = {
            'query_string': b'token=invalid_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is None
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    async def test_authenticate_expired_token(self, mock_token_service):
        """测试过期 token"""
        middleware = JWTAuthMiddleware()
        
        # Mock token 已过期
        mock_token_service.verify_token.return_value = None
        
        scope = {
            'query_string': b'token=expired_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is None
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    @patch('websocket.middleware.User')
    async def test_authenticate_user_not_found(self, mock_user_model, mock_token_service):
        """测试用户不存在"""
        middleware = JWTAuthMiddleware()
        
        # Mock token 验证成功
        mock_token_service.verify_token.return_value = {
            'user_id': '999',
            'exp': time.time() + 3600
        }
        
        # Mock 用户不存在
        mock_user_model.objects.get.side_effect = Exception("User not found")
        
        scope = {
            'query_string': b'token=test_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is None
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    @patch('websocket.middleware.User')
    async def test_authenticate_inactive_user(self, mock_user_model, mock_token_service):
        """测试非活跃用户"""
        middleware = JWTAuthMiddleware()
        
        mock_token_service.verify_token.return_value = {
            'user_id': '1',
            'exp': time.time() + 3600
        }
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.is_active = False  # 非活跃
        mock_user_model.objects.get.return_value = mock_user
        
        scope = {
            'query_string': b'token=test_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is not None
        assert user['is_active'] is False
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    @patch('websocket.middleware.User')
    async def test_authenticate_with_sub_claim(self, mock_user_model, mock_token_service):
        """测试使用 sub claim 作为 user_id"""
        middleware = JWTAuthMiddleware()
        
        # Token 使用 sub 而不是 user_id
        mock_token_service.verify_token.return_value = {
            'sub': '123',
            'exp': time.time() + 3600
        }
        
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = 'subuser'
        mock_user_model.objects.get.return_value = mock_user
        
        scope = {
            'query_string': b'token=test_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is not None
        assert user['id'] == '123'
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.TokenService')
    async def test_authenticate_no_user_id_in_payload(self, mock_token_service):
        """测试 payload 中无 user_id"""
        middleware = JWTAuthMiddleware()
        
        # Token payload 既没有 user_id 也没有 sub
        mock_token_service.verify_token.return_value = {
            'exp': time.time() + 3600,
            'other': 'data'
        }
        
        scope = {
            'query_string': b'token=test_token'
        }
        
        user = await middleware.authenticate(scope)
        
        assert user is None


# ==================== PermissionMiddleware 测试 ====================

class TestPermissionMiddlewareInit:
    """PermissionMiddleware 初始化测试"""
    
    def test_permission_middleware_initialization(self):
        """测试权限中间件初始化"""
        middleware = PermissionMiddleware()
        assert middleware is not None


class TestCheckGamePermission:
    """游戏权限检查测试"""
    
    def test_check_game_permission_red_player(self):
        """测试红方玩家权限"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1'}
        game_data = {'red_player_id': '1', 'black_player_id': '2'}
        
        result = middleware.check_game_permission(user, game_data)
        
        assert result is True
    
    def test_check_game_permission_black_player(self):
        """测试黑方玩家权限"""
        middleware = PermissionMiddleware()
        
        user = {'id': '2'}
        game_data = {'red_player_id': '1', 'black_player_id': '2'}
        
        result = middleware.check_game_permission(user, game_data)
        
        assert result is True
    
    def test_check_game_permission_spectator_not_allowed(self):
        """测试观战者无权限"""
        middleware = PermissionMiddleware()
        
        user = {'id': '3'}
        game_data = {'red_player_id': '1', 'black_player_id': '2'}
        
        result = middleware.check_game_permission(user, game_data)
        
        assert result is False
    
    def test_check_game_permission_invalid_user(self):
        """测试无效用户"""
        middleware = PermissionMiddleware()
        
        user = {}  # 无 id
        game_data = {'red_player_id': '1', 'black_player_id': '2'}
        
        result = middleware.check_game_permission(user, game_data)
        
        assert result is False
    
    def test_check_game_permission_invalid_game_data(self):
        """测试无效游戏数据"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1'}
        game_data = {}  # 无玩家 ID
        
        result = middleware.check_game_permission(user, game_data)
        
        assert result is False


class TestCheckAiGamePermission:
    """AI 对局权限检查测试"""
    
    def test_check_ai_game_permission_owner(self):
        """测试 AI 对局所有者"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1'}
        ai_game_data = {'player_id': '1'}
        
        result = middleware.check_ai_game_permission(user, ai_game_data)
        
        assert result is True
    
    def test_check_ai_game_permission_not_owner(self):
        """测试非 AI 对局所有者"""
        middleware = PermissionMiddleware()
        
        user = {'id': '2'}
        ai_game_data = {'player_id': '1'}
        
        result = middleware.check_ai_game_permission(user, ai_game_data)
        
        assert result is False


class TestCheckMatchmakingPermission:
    """匹配系统权限检查测试"""
    
    def test_check_matchmaking_permission_active_user(self):
        """测试活跃用户匹配权限"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1', 'is_active': True}
        
        result = middleware.check_matchmaking_permission(user)
        
        assert result is True
    
    def test_check_matchmaking_permission_inactive_user(self):
        """测试非活跃用户匹配权限"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1', 'is_active': False}
        
        result = middleware.check_matchmaking_permission(user)
        
        assert result is False
    
    def test_check_matchmaking_permission_default_active(self):
        """测试默认活跃状态"""
        middleware = PermissionMiddleware()
        
        user = {'id': '1'}  # 无 is_active 字段
        
        result = middleware.check_matchmaking_permission(user)
        
        assert result is True  # 默认允许


# ==================== LoggingMiddleware 测试 ====================

class TestLoggingMiddlewareInit:
    """LoggingMiddleware 初始化测试"""
    
    @patch('websocket.middleware.get_config')
    def test_logging_middleware_initialization(self, mock_get_config):
        """测试日志中间件初始化"""
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        
        middleware = LoggingMiddleware()
        
        assert middleware is not None
        assert middleware.logger is not None


class TestLogConnection:
    """连接日志测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_connection_enabled(self, mock_get_logger, mock_get_config):
        """测试启用连接日志"""
        mock_config = Mock()
        mock_config.LOG_CONNECTIONS = True
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        user = {'id': '1', 'username': 'testuser'}
        middleware.log_connection(user, 'game_123', 'game')
        
        mock_logger.info.assert_called_once()
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_connection_disabled(self, mock_get_logger, mock_get_config):
        """测试禁用连接日志"""
        mock_config = Mock()
        mock_config.LOG_CONNECTIONS = False
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        user = {'id': '1', 'username': 'testuser'}
        middleware.log_connection(user, 'game_123', 'game')
        
        mock_logger.info.assert_not_called()


class TestLogDisconnection:
    """断开连接日志测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_disconnection_success(self, mock_get_logger, mock_get_config):
        """测试成功记录断开连接"""
        mock_config = Mock()
        mock_config.LOG_CONNECTIONS = True
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        user = {'id': '1', 'username': 'testuser'}
        middleware.log_disconnection(user, 'game_123', 'normal')
        
        mock_logger.info.assert_called_once()


class TestLogMessage:
    """消息日志测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_message_inbound(self, mock_get_logger, mock_get_config):
        """测试记录接收消息"""
        mock_config = Mock()
        mock_config.LOG_MESSAGES = True
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        middleware.log_message('MOVE', 'inbound', 'user_1', 'game_123')
        
        mock_logger.debug.assert_called_once()
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_message_outbound(self, mock_get_logger, mock_get_config):
        """测试记录发送消息"""
        mock_config = Mock()
        mock_config.LOG_MESSAGES = True
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        middleware.log_message('GAME_STATE', 'outbound', 'user_1', 'game_123')
        
        mock_logger.debug.assert_called_once()


class TestLogError:
    """错误日志测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_error_enabled(self, mock_get_logger, mock_get_config):
        """测试启用错误日志"""
        mock_config = Mock()
        mock_config.LOG_ERRORS = True
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        error = Exception("Test error")
        context = {'user_id': '1', 'game_id': '123'}
        
        middleware.log_error(error, context)
        
        mock_logger.error.assert_called_once()
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_error_disabled(self, mock_get_logger, mock_get_config):
        """测试禁用错误日志"""
        mock_config = Mock()
        mock_config.LOG_ERRORS = False
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        error = Exception("Test error")
        middleware.log_error(error, {})
        
        mock_logger.error.assert_not_called()


class TestLogPerformance:
    """性能日志测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_performance_fast(self, mock_get_logger, mock_get_config):
        """测试记录快速操作"""
        mock_config = Mock()
        mock_config.LOG_PERFORMANCE = True
        mock_config.SLOW_MESSAGE_THRESHOLD_MS = 100
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        middleware.log_performance('process_move', 50.0, {})
        
        mock_logger.debug.assert_called_once()
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.get_logger')
    def test_log_performance_slow(self, mock_get_logger, mock_get_config):
        """测试记录慢操作"""
        mock_config = Mock()
        mock_config.LOG_PERFORMANCE = True
        mock_config.SLOW_MESSAGE_THRESHOLD_MS = 100
        mock_get_config.return_value = mock_config
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        middleware = LoggingMiddleware()
        
        middleware.log_performance('slow_operation', 200.0, {})
        
        mock_logger.warning.assert_called_once()


# ==================== PerformanceMonitorMiddleware 测试 ====================

class TestPerformanceMonitorMiddlewareInit:
    """PerformanceMonitorMiddleware 初始化测试"""
    
    @patch('websocket.middleware.get_config')
    def test_performance_monitor_initialization(self, mock_get_config):
        """测试性能监控初始化"""
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        
        middleware = PerformanceMonitorMiddleware()
        
        assert middleware is not None


class TestPerformanceContext:
    """性能上下文测试"""
    
    @patch('websocket.middleware.LoggingMiddleware')
    def test_performance_context_enter(self, mock_logging_middleware):
        """测试进入性能上下文"""
        mock_logging = Mock()
        mock_logging_middleware.return_value = mock_logging
        
        context = PerformanceContext('test_action', mock_logging)
        
        result = context.__enter__()
        
        assert result is context
        assert context.start_time is not None
    
    @patch('websocket.middleware.LoggingMiddleware')
    def test_performance_context_exit(self, mock_logging_middleware):
        """测试退出性能上下文"""
        mock_logging = Mock()
        mock_logging_middleware.return_value = mock_logging
        
        context = PerformanceContext('test_action', mock_logging)
        context.start_time = time.time() - 0.1  # 100ms 前
        
        context.__exit__(None, None, None)
        
        mock_logging.log_performance.assert_called_once()
    
    @patch('websocket.middleware.LoggingMiddleware')
    def test_performance_context_exit_with_exception(self, mock_logging_middleware):
        """测试异常时退出性能上下文"""
        mock_logging = Mock()
        mock_logging_middleware.return_value = mock_logging
        
        context = PerformanceContext('test_action', mock_logging)
        context.start_time = time.time()
        
        result = context.__exit__(Exception, Exception("test"), None)
        
        assert result is False  # 不抑制异常


class TestMeasureDecorator:
    """性能测量装饰器测试"""
    
    @patch('websocket.middleware.get_config')
    @patch('websocket.middleware.LoggingMiddleware')
    def test_measure_decorator(self, mock_logging_middleware, mock_get_config):
        """测试性能测量装饰器"""
        mock_config = Mock()
        mock_config.LOG_PERFORMANCE = True
        mock_get_config.return_value = mock_config
        
        mock_logging = Mock()
        mock_logging_middleware.return_value = mock_logging
        
        middleware = PerformanceMonitorMiddleware()
        
        with middleware.measure('test_action'):
            time.sleep(0.01)  # 模拟操作
        
        mock_logging.log_performance.assert_called_once()


# ==================== require_auth Decorator 测试 ====================

class TestRequireAuthDecorator:
    """require_auth 装饰器测试"""
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.JWTAuthMiddleware')
    async def test_require_auth_success(self, mock_jwt_middleware_class):
        """测试认证成功"""
        mock_jwt_middleware = Mock()
        mock_jwt_middleware.authenticate = AsyncMock(return_value={'id': '1', 'username': 'testuser'})
        mock_jwt_middleware_class.return_value = mock_jwt_middleware
        
        # 创建 mock consumer
        mock_consumer = Mock()
        mock_consumer.scope = {'user': None}
        mock_consumer.close = AsyncMock()
        
        # 创建装饰的函数
        @require_auth
        async def test_func(self):
            return {'user': self.scope['user']}
        
        result = await test_func(mock_consumer)
        
        assert result['user']['id'] == '1'
        mock_consumer.close.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('websocket.middleware.JWTAuthMiddleware')
    async def test_require_auth_failure(self, mock_jwt_middleware_class):
        """测试认证失败"""
        mock_jwt_middleware = Mock()
        mock_jwt_middleware.authenticate = AsyncMock(return_value=None)
        mock_jwt_middleware_class.return_value = mock_jwt_middleware
        
        # 创建 mock consumer
        mock_consumer = Mock()
        mock_consumer.scope = {'user': None}
        mock_consumer.close = AsyncMock()
        
        # 创建装饰的函数
        @require_auth
        async def test_func(self):
            return {'user': self.scope['user']}
        
        await test_func(mock_consumer)
        
        mock_consumer.close.assert_called_once()
        assert mock_consumer.close.call_args[1]['code'] == 4001


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
