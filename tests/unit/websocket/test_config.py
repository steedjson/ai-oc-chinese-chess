"""
WebSocket 配置单元测试

测试 WebSocket 配置模块的各项功能
"""
import pytest
from unittest.mock import patch, MagicMock


class TestWebSocketConfig:
    """测试 WebSocket 配置"""
    
    def test_heartbeat_config_defaults(self):
        """测试心跳配置默认值"""
        from websocket.config import WebSocketConfig
        
        config = WebSocketConfig()
        
        assert config.HEARTBEAT_INTERVAL == 30
        assert config.TIMEOUT_THRESHOLD == 90
        assert config.MAX_MISSED_HEARTBEATS == 3
    
    def test_timeout_config_defaults(self):
        """测试超时配置默认值"""
        from websocket.config import WebSocketConfig
        
        config = WebSocketConfig()
        
        assert config.CONNECT_TIMEOUT == 30
        assert config.DISCONNECT_TIMEOUT == 5
        assert config.MESSAGE_TIMEOUT == 10
    
    def test_auth_config_defaults(self):
        """测试认证配置默认值"""
        from websocket.config import WebSocketConfig
        
        config = WebSocketConfig()
        
        assert config.JWT_ALGORITHM == 'HS256'
        assert config.TOKEN_URL_PARAM == 'token'
        assert config.TOKEN_HEADER_NAME == 'authorization'
    
    def test_log_config_defaults(self):
        """测试日志配置默认值"""
        from websocket.config import WebSocketConfig
        
        config = WebSocketConfig()
        
        assert config.LOG_CONNECTIONS is True
        assert config.LOG_MESSAGES is True
        assert config.LOG_ERRORS is True
        assert config.LOG_PERFORMANCE is True
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        from websocket.config import get_logger
        
        logger = get_logger('test_module')
        
        assert logger is not None
        assert 'websocket' in logger.name


class TestWebSocketMiddleware:
    """测试 WebSocket 中间件"""
    
    def test_permission_check_game_player(self):
        """测试权限检查 - 游戏参与者"""
        from websocket.middleware import PermissionMiddleware
        
        middleware = PermissionMiddleware()
        
        # Mock game data
        game_data = {
            'red_player_id': '123',
            'black_player_id': '456'
        }
        
        user = {'id': '123'}
        
        result = middleware.check_game_permission(user, game_data)
        assert result is True
        
        user = {'id': '456'}
        result = middleware.check_game_permission(user, game_data)
        assert result is True
        
        user = {'id': '789'}
        result = middleware.check_game_permission(user, game_data)
        assert result is False
    
    def test_permission_check_ai_game(self):
        """测试权限检查 - AI 对局"""
        from websocket.middleware import PermissionMiddleware
        
        middleware = PermissionMiddleware()
        
        ai_game_data = {'player_id': '123'}
        user = {'id': '123'}
        
        result = middleware.check_ai_game_permission(user, ai_game_data)
        assert result is True
        
        user = {'id': '456'}
        result = middleware.check_ai_game_permission(user, ai_game_data)
        assert result is False
    
    def test_permission_check_matchmaking(self):
        """测试权限检查 - 匹配系统"""
        from websocket.middleware import PermissionMiddleware
        
        middleware = PermissionMiddleware()
        
        user = {'id': '123', 'is_active': True}
        result = middleware.check_matchmaking_permission(user)
        assert result is True
        
        user = {'id': '123', 'is_active': False}
        result = middleware.check_matchmaking_permission(user)
        assert result is False


class TestBaseConsumer:
    """测试基础 Consumer 类"""
    
    def test_base_consumer_format_message(self):
        """测试消息格式化"""
        from websocket.consumers import BaseConsumer
        
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        message_str = consumer._format_message('TEST_TYPE', {'key': 'value'})
        
        import json
        message = json.loads(message_str)
        
        assert message['type'] == 'TEST_TYPE'
        assert message['payload'] == {'key': 'value'}
        assert 'timestamp' in message
    
    def test_base_consumer_format_error(self):
        """测试错误消息格式化"""
        from websocket.consumers import BaseConsumer
        
        consumer = BaseConsumer()
        consumer.user = {'id': '123'}
        consumer.resource_id = 'test-123'
        
        error_str = consumer._format_error('TEST_ERROR', 'Test error message')
        
        import json
        error = json.loads(error_str)
        
        assert error['type'] == 'ERROR'
        assert error['payload']['success'] is False
        assert error['payload']['error']['code'] == 'TEST_ERROR'
        assert error['payload']['error']['message'] == 'Test error message'
    
    def test_base_consumer_extract_token_from_query(self):
        """测试从 URL 参数提取 token"""
        from websocket.consumers import BaseConsumer
        
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'token=test_token_123&other=value'
        }
        
        token = consumer._extract_token_from_scope()
        assert token == 'test_token_123'
    
    def test_base_consumer_extract_token_from_header(self):
        """测试从 header 提取 token"""
        from websocket.consumers import BaseConsumer
        
        consumer = BaseConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': [(b'authorization', b'Bearer header_token_456')]
        }
        
        token = consumer._extract_token_from_scope()
        assert token == 'header_token_456'


class TestWebSocketRouting:
    """测试 WebSocket 路由配置"""
    
    def test_routing_imports(self):
        """测试路由模块可以正常导入"""
        from websocket import routing
        
        assert hasattr(routing, 'websocket_urlpatterns')
        assert isinstance(routing.websocket_urlpatterns, list)
    
    def test_routing_has_game_pattern(self):
        """测试路由包含游戏模式"""
        from websocket.routing import websocket_urlpatterns
        
        # 应该有至少 3 个路由
        assert len(websocket_urlpatterns) >= 3
        
        # 检查路由名称
        patterns_str = ' '.join([str(p.name) for p in websocket_urlpatterns])
        assert 'ws-game' in patterns_str
        assert 'ws-ai-game' in patterns_str
        assert 'ws-matchmaking' in patterns_str
    
    def test_route_config_exists(self):
        """测试路由配置存在"""
        from websocket.routing import ROUTE_CONFIG, get_route_config, get_all_routes
        
        assert 'game' in ROUTE_CONFIG
        assert 'ai_game' in ROUTE_CONFIG
        assert 'matchmaking' in ROUTE_CONFIG
        
        game_config = get_route_config('game')
        assert game_config is not None
        assert 'pattern' in game_config
        
        all_routes = get_all_routes()
        assert len(all_routes) == 3
    
    def test_route_validation(self):
        """测试路由验证"""
        from websocket.routing import validate_route
        
        assert validate_route('game') is True
        assert validate_route('ai_game') is True
        assert validate_route('matchmaking') is True
        assert validate_route('invalid') is False
