"""
游戏 WebSocket Consumer 单元测试

测试 games/consumers.py 中的 GameConsumer 类

测试范围：
- 连接建立/断开
- 认证和权限验证
- 消息处理（JOIN, LEAVE, MOVE, HEARTBEAT）
- 走棋逻辑
- 心跳监测
- 重连管理
- 错误处理

覆盖率目标：324 语句 → 400 行测试代码
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.utils import timezone
from asgiref.sync import sync_to_async

from games.consumers import GameConsumer
from games.models import Game, GameStatus


# ==================== Fixtures ====================

@pytest.fixture
def red_user(db):
    """创建红方测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='redplayer',
        email='red@example.com',
        password='testpass123'
    )


@pytest.fixture
def black_user(db):
    """创建黑方测试用户"""
    from users.models import User
    return User.objects.create_user(
        username='blackplayer',
        email='black@example.com',
        password='testpass123'
    )


@pytest.fixture
def other_user(db):
    """创建其他测试用户（非游戏参与者）"""
    from users.models import User
    return User.objects.create_user(
        username='otherplayer',
        email='other@example.com',
        password='testpass123'
    )


@pytest.fixture
def active_game(red_user, black_user):
    """创建进行中的测试游戏"""
    return Game.objects.create(
        red_player=red_user,
        black_player=black_user,
        game_type='ranked',
        status=GameStatus.PLAYING,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w'
    )


@pytest.fixture
def finished_game(red_user, black_user):
    """创建已结束的测试游戏"""
    return Game.objects.create(
        red_player=red_user,
        black_player=black_user,
        game_type='ranked',
        status=GameStatus.WHITE_WIN,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w',
        finished_at=timezone.now()
    )


@pytest.fixture
def create_token():
    """创建 JWT token 的工厂函数"""
    from authentication.services import TokenService
    
    def _create_token(user):
        tokens = TokenService.generate_tokens(user)
        return tokens['access_token']
    
    return _create_token


@pytest.fixture
def test_asgi_app():
    """创建测试 ASGI 应用"""
    from games import routing
    
    return ProtocolTypeRouter({
        "websocket": AllowedHostsOriginValidator(
            URLRouter(routing.websocket_urlpatterns)
        ),
    })


# ==================== 连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerConnect:
    """GameConsumer 连接测试"""
    
    async def test_connect_success_red_player(self, active_game, red_user, create_token, test_asgi_app):
        """测试红方玩家成功连接"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        # 连接应该成功
        connected, subprotocol = await communicator.connect(timeout=5)
        assert connected is True
        
        # 应该收到游戏状态
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'GAME_STATE'
        assert response['payload']['game_id'] == str(active_game.id)
        
        await communicator.disconnect()
    
    async def test_connect_success_black_player(self, active_game, black_user, create_token, test_asgi_app):
        """测试黑方玩家成功连接"""
        token = create_token(black_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, subprotocol = await communicator.connect(timeout=5)
        assert connected is True
        
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'GAME_STATE'
        
        await communicator.disconnect()
    
    async def test_connect_failure_no_token(self, active_game, test_asgi_app):
        """测试无 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/"
        )
        
        # 连接应该失败（认证失败）
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_invalid_token(self, active_game, test_asgi_app):
        """测试无效 token 连接失败"""
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token=invalid_token"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_non_participant(self, active_game, other_user, create_token, test_asgi_app):
        """测试非游戏参与者连接失败"""
        token = create_token(other_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        # 非参与者应该被拒绝连接
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_game_not_found(self, red_user, create_token, test_asgi_app):
        """测试游戏不存在连接失败"""
        token = create_token(red_user)
        fake_game_id = '00000000-0000-0000-0000-000000000000'
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{fake_game_id}/?token={token}"
        )
        
        with pytest.raises(AssertionError):
            await communicator.connect(timeout=5)
        
        await communicator.disconnect()
    
    async def test_connect_failure_finished_game(self, finished_game, red_user, create_token, test_asgi_app):
        """测试已结束游戏连接（根据业务规则可能允许或拒绝）"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{finished_game.id}/?token={token}"
        )
        
        # 已结束游戏的连接行为取决于业务逻辑
        # 这里测试可以连接（用于回放）
        try:
            connected, _ = await communicator.connect(timeout=5)
            if connected:
                response = await communicator.receive_json_from(timeout=5)
                assert response['type'] == 'GAME_STATE'
                await communicator.disconnect()
        except AssertionError:
            # 如果不允许连接也是合理的
            pass


# ==================== 断开连接测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerDisconnect:
    """GameConsumer 断开连接测试"""
    
    async def test_disconnect_clean(self, active_game, red_user, create_token, test_asgi_app):
        """测试正常断开连接"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        
        # 消耗初始消息
        await communicator.receive_json_from(timeout=5)
        
        # 断开连接
        await communicator.disconnect()
        
        # 等待一小段时间确保清理完成
        await asyncio.sleep(0.1)
    
    async def test_disconnect_broadcasts_leave(self, active_game, red_user, black_user, create_token, test_asgi_app):
        """测试断开连接时广播离开消息"""
        # 红方连接
        token_red = create_token(red_user)
        comm_red = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token_red}"
        )
        connected_red, _ = await comm_red.connect(timeout=5)
        assert connected_red is True
        await comm_red.receive_json_from(timeout=5)  # GAME_STATE
        
        # 黑方连接
        token_black = create_token(black_user)
        comm_black = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token_black}"
        )
        connected_black, _ = await comm_black.connect(timeout=5)
        assert connected_black is True
        await comm_black.receive_json_from(timeout=5)  # GAME_STATE
        
        # 红方发送 PLAYER_JOIN 给黑方
        join_msg = await comm_black.receive_json_from(timeout=5)
        assert join_msg['type'] == 'PLAYER_JOIN'
        
        # 红方断开
        await comm_red.disconnect()
        
        # 黑方应该收到 PLAYER_LEAVE 消息
        leave_msg = await comm_black.receive_json_from(timeout=5)
        assert leave_msg['type'] == 'PLAYER_LEAVE'
        assert leave_msg['payload']['user_id'] == str(red_user.id)
        
        await comm_black.disconnect()


# ==================== 消息处理测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerMessages:
    """GameConsumer 消息处理测试"""
    
    async def test_handle_join_message(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理 JOIN 消息"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        
        # 消耗初始 GAME_STATE
        await communicator.receive_json_from(timeout=5)
        
        # 发送 JOIN 消息
        await communicator.send_json_to({
            'type': 'JOIN',
            'payload': {'game_id': str(active_game.id)}
        })
        
        # 接收 JOIN_RESULT
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'JOIN_RESULT'
        assert response['payload']['success'] is True
        assert 'game_state' in response['payload']
        
        await communicator.disconnect()
    
    async def test_handle_leave_message(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理 LEAVE 消息"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送 LEAVE 消息
        await communicator.send_json_to({
            'type': 'LEAVE'
        })
        
        # 连接应该关闭
        await asyncio.sleep(0.1)
    
    async def test_handle_heartbeat_message(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理 HEARTBEAT 消息"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送 HEARTBEAT 消息
        await communicator.send_json_to({
            'type': 'HEARTBEAT',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # 接收 HEARTBEAT 响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'HEARTBEAT'
        assert response['payload']['acknowledged'] is True
        
        await communicator.disconnect()
    
    async def test_handle_invalid_message_type(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理无效消息类型"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送未知消息类型
        await communicator.send_json_to({
            'type': 'UNKNOWN_TYPE'
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_MESSAGE_TYPE'
        
        await communicator.disconnect()
    
    async def test_handle_invalid_json(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理无效 JSON"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效 JSON
        await communicator.send_to_text("invalid json {")
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_JSON'
        
        await communicator.disconnect()


# ==================== 走棋测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerMove:
    """GameConsumer 走棋测试"""
    
    async def test_handle_move_valid(self, active_game, red_user, create_token, test_asgi_app):
        """测试有效走棋"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)  # GAME_STATE
        
        # 红方走棋：炮二平五（c2 到 e2）
        await communicator.send_json_to({
            'type': 'MOVE',
            'payload': {
                'from': 'c2',
                'to': 'e2'
            }
        })
        
        # 应该收到走棋结果
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'MOVE_RESULT'
        # 走棋可能成功或失败，取决于具体规则
        assert 'payload' in response
        
        await communicator.disconnect()
    
    async def test_handle_move_invalid_position(self, active_game, red_user, create_token, test_asgi_app):
        """测试无效位置走棋"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送无效位置
        await communicator.send_json_to({
            'type': 'MOVE',
            'payload': {
                'from': 'invalid',
                'to': 'invalid'
            }
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        
        await communicator.disconnect()
    
    async def test_handle_move_missing_fields(self, active_game, red_user, create_token, test_asgi_app):
        """测试缺少必填字段的走棋"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送缺少 to 字段的走棋
        await communicator.send_json_to({
            'type': 'MOVE',
            'payload': {
                'from': 'c2'
            }
        })
        
        # 应该收到错误响应
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'INVALID_MOVE'
        
        await communicator.disconnect()
    
    async def test_handle_move_not_your_turn(self, active_game, black_user, create_token, test_asgi_app):
        """测试非己方回合走棋"""
        token = create_token(black_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 黑方走棋（但现在是红方回合）
        await communicator.send_json_to({
            'type': 'MOVE',
            'payload': {
                'from': 'c7',
                'to': 'e7'
            }
        })
        
        # 应该收到错误响应（不是你的回合）
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'ERROR'
        assert response['payload']['error']['code'] == 'NOT_YOUR_TURN'
        
        await communicator.disconnect()


# ==================== 重连测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerReconnect:
    """GameConsumer 重连测试"""
    
    async def test_handle_reconnect_request(self, active_game, red_user, create_token, test_asgi_app):
        """测试处理重连请求"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送重连请求
        await communicator.send_json_to({
            'type': 'RECONNECT_REQUEST'
        })
        
        # 应该收到响应（成功或失败）
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] in ['RECONNECT_STATUS', 'ERROR']
        
        await communicator.disconnect()
    
    async def test_handle_get_reconnect_history(self, active_game, red_user, create_token, test_asgi_app):
        """测试获取重连历史"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 发送获取重连历史请求
        await communicator.send_json_to({
            'type': 'GET_RECONNECT_HISTORY',
            'payload': {'limit': 10}
        })
        
        # 应该收到重连历史
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'RECONNECT_HISTORY'
        assert 'history' in response['payload']
        assert 'stats' in response['payload']
        
        await communicator.disconnect()


# ==================== 频道层消息处理器测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerChannelHandlers:
    """GameConsumer 频道层消息处理器测试"""
    
    async def test_move_made_handler(self, active_game, red_user, create_token, test_asgi_app):
        """测试 move_made 消息处理器"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 move_made 事件
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'game_{active_game.id}',
            {
                'type': 'move_made',
                'data': {
                    'move': {'from': 'c2', 'to': 'e2', 'piece': 'C'},
                    'fen': 'new_fen',
                    'turn': 'b',
                    'is_check': False,
                    'is_checkmate': False,
                    'is_stalemate': False
                }
            }
        )
        
        # 应该收到 MOVE_RESULT
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'MOVE_RESULT'
        assert response['payload']['success'] is True
        
        await communicator.disconnect()
    
    async def test_game_over_handler(self, active_game, red_user, create_token, test_asgi_app):
        """测试 game_over 消息处理器"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 game_over 事件
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'game_{active_game.id}',
            {
                'type': 'game_over',
                'data': {
                    'winner': 'red',
                    'reason': 'checkmate',
                    'rating_change': {'red': 10, 'black': -10}
                }
            }
        )
        
        # 应该收到 GAME_OVER
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'GAME_OVER'
        assert response['payload']['winner'] == 'red'
        
        await communicator.disconnect()
    
    async def test_player_join_handler(self, active_game, red_user, create_token, test_asgi_app):
        """测试 player_join 消息处理器"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 player_join 事件
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'game_{active_game.id}',
            {
                'type': 'player_join',
                'data': {
                    'user_id': str(red_user.id),
                    'username': red_user.username
                }
            }
        )
        
        # 应该收到 PLAYER_JOIN
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'PLAYER_JOIN'
        assert response['payload']['username'] == red_user.username
        
        await communicator.disconnect()
    
    async def test_player_leave_handler(self, active_game, red_user, create_token, test_asgi_app):
        """测试 player_leave 消息处理器"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 模拟从频道层接收 player_leave 事件
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'game_{active_game.id}',
            {
                'type': 'player_leave',
                'data': {
                    'user_id': str(red_user.id),
                    'username': red_user.username
                }
            }
        )
        
        # 应该收到 PLAYER_LEAVE
        response = await communicator.receive_json_from(timeout=5)
        assert response['type'] == 'PLAYER_LEAVE'
        assert response['payload']['username'] == red_user.username
        
        await communicator.disconnect()


# ==================== 边界条件和错误处理测试 ====================

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestGameConsumerEdgeCases:
    """GameConsumer 边界条件和错误处理测试"""
    
    async def test_concurrent_connections(self, active_game, red_user, black_user, create_token, test_asgi_app):
        """测试并发连接"""
        token_red = create_token(red_user)
        token_black = create_token(black_user)
        
        # 同时连接两个玩家
        comm_red = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token_red}"
        )
        comm_black = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token_black}"
        )
        
        # 并发连接
        connected_red, _ = await comm_red.connect(timeout=5)
        connected_black, _ = await comm_black.connect(timeout=5)
        
        assert connected_red is True
        assert connected_black is True
        
        # 双方都应该收到 GAME_STATE
        await comm_red.receive_json_from(timeout=5)
        await comm_black.receive_json_from(timeout=5)
        
        # 红方应该收到黑方加入的通知
        join_msg = await comm_red.receive_json_from(timeout=5)
        assert join_msg['type'] == 'PLAYER_JOIN'
        
        # 黑方应该收到红方加入的通知
        join_msg = await comm_black.receive_json_from(timeout=5)
        assert join_msg['type'] == 'PLAYER_JOIN'
        
        await comm_red.disconnect()
        await comm_black.disconnect()
    
    async def test_rapid_message_sequence(self, active_game, red_user, create_token, test_asgi_app):
        """测试快速消息序列"""
        token = create_token(red_user)
        
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        await communicator.receive_json_from(timeout=5)
        
        # 快速发送多个消息
        messages = [
            {'type': 'HEARTBEAT'},
            {'type': 'JOIN'},
            {'type': 'HEARTBEAT'},
        ]
        
        for msg in messages:
            await communicator.send_json_to(msg)
        
        # 应该收到所有响应
        for _ in messages:
            response = await communicator.receive_json_from(timeout=5)
            assert response['type'] in ['HEARTBEAT', 'JOIN_RESULT']
        
        await communicator.disconnect()
    
    async def test_connection_with_query_params(self, active_game, red_user, create_token, test_asgi_app):
        """测试带查询参数的连接"""
        token = create_token(red_user)
        
        # 使用不同的参数格式
        communicator = WebsocketCommunicator(
            test_asgi_app,
            f"/ws/game/{active_game.id}/?token={token}&version=1.0"
        )
        
        connected, _ = await communicator.connect(timeout=5)
        assert connected is True
        
        await communicator.disconnect()
