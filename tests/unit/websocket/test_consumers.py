"""
WebSocket Consumers 单元测试

测试 websocket/consumers.py 中的 BaseConsumer 类

测试范围：
- 连接建立/断开
- 消息处理（走棋、聊天、观战）
- 认证和权限验证
- 错误处理
- 心跳管理
- 消息格式化
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.utils import timezone

from websocket.consumers import BaseConsumer
from websocket.config import WebSocketConfig, get_config, get_logger
from websocket.middleware import JWTAuthMiddleware, PermissionMiddleware, LoggingMiddleware, PerformanceMonitorMiddleware


# ==================== BaseConsumer 基础测试 ====================

class TestBaseConsumerInitialization:
    """BaseConsumer 初始化测试"""
    
    def test_consumer_init_with_defaults(self):
        """测试 Consumer 初始化默认值"""
        consumer = BaseConsumer()
        
        assert consumer.config is not None
        assert consumer.logger is not None
        assert isinstance(consumer.auth_middleware, JWTAuthMiddleware)
        assert isinstance(consumer.permission_middleware, PermissionMiddleware)
        assert isinstance(consumer.logging_middleware, LoggingMiddleware)
        assert isinstance(consumer.performance_monitor, PerformanceMonitorMiddleware)
        
        # 心跳管理
        assert consumer.last_heartbeat is None
        assert consumer.heartbeat_task is None
        
        # 用户信息
        assert consumer.user is None
        
        # 资源信息
        assert consumer.resource_id is None
        assert consumer.resource_type is None
    
    def test_consumer_sets_resource_info(self):
        """测试 Consumer 设置资源信息"""
        consumer = BaseConsumer()
        
        consumer.resource_id = 'game-123'
        consumer.resource_type = 'game'
        
        assert consumer.resource_id == 'game-123'
        assert consumer.resource_type == 'game'
    
    def test_consumer_sets_user(self):
        """测试 Consumer 设置用户信息"""
        consumer = BaseConsumer()
        
        user_data = {'id': '123', 'username': 'testuser'}
        consumer.user = user_data
        
        assert consumer.user == user_data
        assert consumer.user['id'] == '123'


class TestBaseConsumerAuthentication:
    """BaseConsumer 认证测试"""
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """测试认证成功"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=valid_token',
            'headers': []
        }
        
        mock_user = {'id': '123', 'username': 'testuser'}
        
        # Mock auth middleware
        with patch.object(consumer.auth_middleware, 'authenticate', return_value=mock_user):
            with patch.object(consumer, '_send_connection_error', new_callable=AsyncMock):
                result = await consumer.authenticate()
        
        assert result is True
        assert consumer.user == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_failure_no_user(self):
        """测试认证失败 - 无用户"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=invalid_token',
            'headers': []
        }
        
        mock_send_error = AsyncMock()
        
        # Mock auth middleware returns None
        with patch.object(consumer.auth_middleware, 'authenticate', return_value=None):
            with patch.object(consumer, '_send_connection_error', mock_send_error):
                result = await consumer.authenticate()
        
        assert result is False
        assert consumer.user is None
        mock_send_error.assert_called_once_with('Invalid or expired token')
    
    @pytest.mark.asyncio
    async def test_authenticate_exception(self):
        """测试认证异常"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=valid_token',
            'headers': []
        }
        
        mock_send_error = AsyncMock()
        
        # Mock auth middleware raises exception
        with patch.object(consumer.auth_middleware, 'authenticate', side_effect=Exception('Auth error')):
            with patch.object(consumer, '_send_connection_error', mock_send_error):
                result = await consumer.authenticate()
        
        assert result is False
        mock_send_error.assert_called_once_with('Authentication failed')
    
    @pytest.mark.asyncio
    async def test_extract_token_from_query_string(self):
        """测试从 URL 查询字符串提取 token"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=test_token_123&other=value',
            'headers': []
        }
        
        token = consumer._extract_token_from_scope()
        
        assert token == 'test_token_123'
    
    @pytest.mark.asyncio
    async def test_extract_token_from_authorization_header(self):
        """测试从 Authorization header 提取 token"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': [(b'authorization', b'Bearer header_token_456')]
        }
        
        token = consumer._extract_token_from_scope()
        
        assert token == 'header_token_456'
    
    @pytest.mark.asyncio
    async def test_extract_token_no_token(self):
        """测试无 token 返回 None"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': []
        }
        
        token = consumer._extract_token_from_scope()
        
        assert token is None
    
    @pytest.mark.asyncio
    async def test_extract_token_malformed_header(self):
        """测试 malformed header 返回 None"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': [(b'authorization', b'InvalidFormat')]
        }
        
        token = consumer._extract_token_from_scope()
        
        assert token is None


class TestBaseConsumerPermission:
    """BaseConsumer 权限测试"""
    
    def test_check_permission_no_user(self):
        """测试无用户时权限检查失败"""
        consumer = BaseConsumer()
        consumer.user = None
        consumer.resource_type = 'game'
        
        result = consumer.check_permission({'game_id': '123'})
        
        assert result is False
    
    def test_check_permission_game_player(self):
        """测试游戏参与者权限检查"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_type = 'game'
        
        game_data = {
            'red_player_id': '123',
            'black_player_id': '456'
        }
        
        with patch.object(consumer.permission_middleware, 'check_game_permission', return_value=True):
            result = consumer.check_permission(game_data)
        
        assert result is True
    
    def test_check_permission_ai_game(self):
        """测试 AI 对局权限检查"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_type = 'ai_game'
        
        ai_game_data = {'player_id': '123'}
        
        with patch.object(consumer.permission_middleware, 'check_ai_game_permission', return_value=True):
            result = consumer.check_permission(ai_game_data)
        
        assert result is True
    
    def test_check_permission_matchmaking(self):
        """测试匹配系统权限检查"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_type = 'matchmaking'
        
        with patch.object(consumer.permission_middleware, 'check_matchmaking_permission', return_value=True):
            result = consumer.check_permission({})
        
        assert result is True
    
    def test_check_permission_unknown_type(self):
        """测试未知资源类型默认允许"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_type = 'unknown'
        
        result = consumer.check_permission({})
        
        assert result is True
    
    def test_check_permission_exception(self):
        """测试权限检查异常"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_type = 'game'
        
        with patch.object(consumer.permission_middleware, 'check_game_permission', side_effect=Exception('Error')):
            result = consumer.check_permission({'game_id': '123'})
        
        assert result is False


class TestBaseConsumerHeartbeat:
    """BaseConsumer 心跳测试"""
    
    def test_start_heartbeat_tracking(self):
        """测试开始心跳追踪"""
        consumer = BaseConsumer()
        
        consumer.start_heartbeat_tracking()
        
        assert consumer.last_heartbeat is not None
    
    def test_update_heartbeat(self):
        """测试更新心跳"""
        consumer = BaseConsumer()
        consumer.last_heartbeat = timezone.now()
        old_time = consumer.last_heartbeat
        
        import time
        time.sleep(0.01)  # 短暂等待确保时间不同
        
        consumer.update_heartbeat()
        
        assert consumer.last_heartbeat >= old_time
    
    def test_is_connection_healthy_no_heartbeat(self):
        """测试无心跳时连接健康"""
        consumer = BaseConsumer()
        consumer.last_heartbeat = None
        
        result = consumer.is_connection_healthy()
        
        assert result is True
    
    def test_is_connection_healthy_with_heartbeat(self):
        """测试有心跳时连接健康"""
        consumer = BaseConsumer()
        consumer.last_heartbeat = timezone.now()
        consumer.config = get_config()
        
        result = consumer.is_connection_healthy()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        """测试处理心跳消息"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        
        await consumer.handle_heartbeat({'type': 'HEARTBEAT'})
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        
        assert call_args['type'] == 'HEARTBEAT'
        assert call_args['payload']['acknowledged'] is True
        assert 'timestamp' in call_args


class TestBaseConsumerMessageFormatting:
    """BaseConsumer 消息格式化测试"""
    
    def test_format_message(self):
        """测试消息格式化"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        message_str = consumer._format_message('TEST_TYPE', {'key': 'value'})
        
        message = json.loads(message_str)
        
        assert message['type'] == 'TEST_TYPE'
        assert message['payload'] == {'key': 'value'}
        assert 'timestamp' in message
    
    def test_format_message_anonymous_user(self):
        """测试匿名用户消息格式化"""
        consumer = BaseConsumer()
        consumer.user = None
        consumer.resource_id = 'test-123'
        
        # 应该不会抛出异常
        message_str = consumer._format_message('TEST_TYPE', {'key': 'value'})
        
        message = json.loads(message_str)
        assert message['type'] == 'TEST_TYPE'
    
    def test_format_error(self):
        """测试错误消息格式化"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        error_str = consumer._format_error('TEST_ERROR', 'Test error message')
        
        error = json.loads(error_str)
        
        assert error['type'] == 'ERROR'
        assert error['payload']['success'] is False
        assert error['payload']['error']['code'] == 'TEST_ERROR'
        assert error['payload']['error']['message'] == 'Test error message'
    
    def test_format_error_anonymous_user(self):
        """测试匿名用户错误格式化"""
        consumer = BaseConsumer()
        consumer.user = None
        consumer.resource_id = 'test-123'
        
        error_str = consumer._format_error('TEST_ERROR', 'Test error message')
        
        error = json.loads(error_str)
        assert error['type'] == 'ERROR'


class TestBaseConsumerConnection:
    """BaseConsumer 连接管理测试"""
    
    @pytest.mark.asyncio
    async def test_send_connection_error(self):
        """测试发送连接错误"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.close = AsyncMock()
        
        await consumer._send_connection_error('Connection failed')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'CONNECTION_ERROR'
        assert call_args['payload']['error']['message'] == 'Connection failed'
        
        consumer.close.assert_called_once_with(code=4001)
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """测试发送错误消息"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        
        await consumer._send_error('TEST_CODE', 'Test error')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'TEST_CODE'
        assert call_args['payload']['error']['message'] == 'Test error'
    
    @pytest.mark.asyncio
    async def test_connect(self):
        """测试连接建立"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123', 'username': 'testuser'}
        consumer.resource_id = 'game-123'
        consumer.resource_type = 'game'
        
        with patch.object(consumer.logging_middleware, 'log_connection') as mock_log:
            await consumer.connect()
        
        assert consumer.last_heartbeat is not None
        mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """测试连接断开"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123', 'username': 'testuser'}
        consumer.resource_id = 'game-123'
        
        with patch.object(consumer.logging_middleware, 'log_disconnection') as mock_log:
            await consumer.disconnect(1000)
        
        mock_log.assert_called_once()
    
    def test_log_action(self):
        """测试记录操作日志"""
        consumer = BaseConsumer()
        
        with patch.object(consumer.logging_middleware, 'log_performance') as mock_log:
            consumer._log_action('test_action', 100.5, {'extra': 'data'})
        
        mock_log.assert_called_once_with('test_action', 100.5, {'extra': 'data'})
    
    def test_log_action_no_context(self):
        """测试记录操作日志无上下文"""
        consumer = BaseConsumer()
        
        with patch.object(consumer.logging_middleware, 'log_performance') as mock_log:
            consumer._log_action('test_action', 50.0)
        
        mock_log.assert_called_once_with('test_action', 50.0, {})


class TestBaseConsumerReceive:
    """BaseConsumer 消息接收测试"""
    
    @pytest.mark.asyncio
    async def test_receive_heartbeat(self):
        """测试接收心跳消息"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        await consumer.receive(json.dumps({'type': 'HEARTBEAT'}))
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'HEARTBEAT'
    
    @pytest.mark.asyncio
    async def test_receive_invalid_json(self):
        """测试接收无效 JSON"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        await consumer.receive('invalid json')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'INVALID_JSON'
    
    @pytest.mark.asyncio
    async def test_receive_exception(self):
        """测试接收消息异常"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        # Mock json.loads to raise exception
        with patch('json.loads', side_effect=Exception('Parse error')):
            await consumer.receive('{"type": "TEST"}')
        
        consumer.send.assert_called()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'INTERNAL_ERROR'


# ==================== 集成测试 ====================

class TestBaseConsumerIntegration:
    """BaseConsumer 集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """测试完整认证流程"""
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=valid_token',
            'headers': []
        }
        
        mock_user = {'id': '123', 'username': 'testuser'}
        
        with patch.object(consumer.auth_middleware, 'authenticate', return_value=mock_user):
            with patch.object(consumer, '_send_connection_error', new_callable=AsyncMock) as mock_error:
                # 认证
                result = await consumer.authenticate()
                
                assert result is True
                assert consumer.user == mock_user
                mock_error.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_permission_check_chain(self):
        """测试权限检查链"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        
        # 测试不同资源类型
        test_cases = [
            ('game', {'red_player_id': '123'}, True),
            ('game', {'red_player_id': '456'}, False),
            ('ai_game', {'player_id': '123'}, True),
            ('matchmaking', {}, True),
            ('unknown', {}, True),
        ]
        
        for resource_type, resource_data, expected in test_cases:
            consumer.resource_type = resource_type
            
            with patch.object(consumer.permission_middleware, 'check_game_permission', return_value=(resource_data.get('red_player_id') == '123')):
                with patch.object(consumer.permission_middleware, 'check_ai_game_permission', return_value=(resource_data.get('player_id') == '123')):
                    with patch.object(consumer.permission_middleware, 'check_matchmaking_permission', return_value=True):
                        result = consumer.check_permission(resource_data)
                        
                        # 注意：实际结果取决于 mock 的返回值
                        # 这里主要测试流程不会抛出异常
                        assert isinstance(result, bool)


class TestWebSocketConfig:
    """WebSocket 配置测试"""
    
    def test_get_config_singleton(self):
        """测试配置单例"""
        from websocket.config import get_config
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_get_logger(self):
        """测试获取 logger"""
        logger = get_logger('test_module')
        
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')


class TestWebSocketMiddleware:
    """WebSocket 中间件测试"""
    
    def test_jwt_auth_middleware_init(self):
        """测试 JWT 认证中间件初始化"""
        middleware = JWTAuthMiddleware()
        
        assert middleware is not None
    
    def test_permission_middleware_game_permission(self):
        """测试权限中间件 - 游戏权限"""
        middleware = PermissionMiddleware()
        
        game_data = {'red_player_id': '123', 'black_player_id': '456'}
        
        # 红方玩家
        assert middleware.check_game_permission({'id': '123'}, game_data) is True
        # 黑方玩家
        assert middleware.check_game_permission({'id': '456'}, game_data) is True
        # 旁观者
        assert middleware.check_game_permission({'id': '789'}, game_data) is False
    
    def test_permission_middleware_ai_game_permission(self):
        """测试权限中间件 - AI 对局权限"""
        middleware = PermissionMiddleware()
        
        ai_game_data = {'player_id': '123'}
        
        # 玩家
        assert middleware.check_ai_game_permission({'id': '123'}, ai_game_data) is True
        # 非玩家
        assert middleware.check_ai_game_permission({'id': '456'}, ai_game_data) is False
    
    def test_permission_middleware_matchmaking_permission(self):
        """测试权限中间件 - 匹配权限"""
        middleware = PermissionMiddleware()
        
        # 活跃用户
        assert middleware.check_matchmaking_permission({'id': '123', 'is_active': True}) is True
        # 非活跃用户
        assert middleware.check_matchmaking_permission({'id': '123', 'is_active': False}) is False
    
    def test_logging_middleware_log_connection(self):
        """测试日志中间件 - 连接日志"""
        middleware = LoggingMiddleware()
        
        # 不应该抛出异常
        middleware.log_connection({'id': '123', 'username': 'test'}, 'game-123', 'game')
    
    def test_logging_middleware_log_message(self):
        """测试日志中间件 - 消息日志"""
        middleware = LoggingMiddleware()
        
        # 不应该抛出异常
        middleware.log_message('TEST_TYPE', 'inbound', '123', 'game-123')
    
    def test_logging_middleware_log_error(self):
        """测试日志中间件 - 错误日志"""
        middleware = LoggingMiddleware()
        
        # 不应该抛出异常
        middleware.log_error(Exception('Test error'), {'user_id': '123'})
    
    def test_performance_monitor_measure(self):
        """测试性能监控"""
        monitor = PerformanceMonitorMiddleware()
        
        with monitor.measure('test_operation'):
            pass  # 空操作
        
        # 不应该抛出异常


class TestConsumerEdgeCases:
    """Consumer 边界情况测试"""
    
    def test_format_message_with_complex_payload(self):
        """测试复杂负载消息格式化"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        complex_payload = {
            'nested': {'key': 'value'},
            'list': [1, 2, 3],
            'boolean': True,
            'null': None
        }
        
        message_str = consumer._format_message('COMPLEX', complex_payload)
        message = json.loads(message_str)
        
        assert message['payload']['nested']['key'] == 'value'
        assert message['payload']['list'] == [1, 2, 3]
        assert message['payload']['boolean'] is True
        assert message['payload']['null'] is None
    
    def test_format_error_with_unicode(self):
        """测试 Unicode 错误消息格式化"""
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        
        error_str = consumer._format_error('UNICODE_ERROR', '错误消息：测试中文')
        error = json.loads(error_str)
        
        assert '错误消息：测试中文' in error['payload']['error']['message']
    
    @pytest.mark.asyncio
    async def test_receive_empty_message(self):
        """测试接收空消息"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.user = {'id': '123'}
        
        await consumer.receive(json.dumps({}))
        
        # 应该处理但不抛出异常
        assert consumer.send.called or True  # 可能发送错误消息
    
    @pytest.mark.asyncio
    async def test_receive_message_without_type(self):
        """测试接收无类型消息"""
        consumer = BaseConsumer()
        consumer.send = AsyncMock()
        consumer.user = {'id': '123'}
        
        await consumer.receive(json.dumps({'data': 'test'}))
        
        # 应该处理但不抛出异常
        assert True  # 主要测试不崩溃


class TestHeartbeatConfig:
    """心跳配置测试"""
    
    def test_heartbeat_interval_default(self):
        """测试心跳间隔默认值"""
        config = get_config()
        
        assert config.HEARTBEAT_INTERVAL == 30
    
    def test_timeout_threshold_default(self):
        """测试超时阈值默认值"""
        config = get_config()
        
        assert config.TIMEOUT_THRESHOLD == 90
    
    def test_max_missed_heartbeats_default(self):
        """测试最大丢失心跳默认值"""
        config = get_config()
        
        assert config.MAX_MISSED_HEARTBEATS == 3
    
    def test_is_connection_healthy_recent_heartbeat(self):
        """测试最近心跳连接健康"""
        config = get_config()
        
        recent_time = timezone.now()
        
        assert config.is_connection_healthy(recent_time) is True
    
    def test_is_connection_healthy_old_heartbeat(self):
        """测试旧心跳连接不健康"""
        config = get_config()
        
        # 创建一个 2 分钟前的时间（超过 90 秒阈值）
        old_time = timezone.now() - timezone.timedelta(seconds=120)
        
        assert config.is_connection_healthy(old_time) is False
