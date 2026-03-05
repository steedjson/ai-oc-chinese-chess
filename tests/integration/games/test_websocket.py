"""
WebSocket 实时对战集成测试

测试游戏房间 WebSocket 连接、走棋、游戏状态同步等功能
"""
import pytest
import json
from typing import Dict, Any
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from datetime import timedelta

# 导入 ASGI 应用
from config.asgi import get_asgi_application
from games.models import Game
from users.models import User
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# 创建测试专用的 ASGI 应用（不使用 AuthMiddlewareStack，避免数据库锁定问题）
django_asgi_app = get_asgi_application()
from websocket.routing import websocket_urlpatterns

# 测试用 ASGI 应用 - 不使用 AuthMiddlewareStack
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        URLRouter(websocket_urlpatterns)
    ),
})


@pytest.fixture
def create_test_game(db):
    """创建测试游戏"""
    # 创建测试用户
    red_player = User.objects.create_user(
        username='red_player',
        email='red@test.com',
        password='password123'
    )
    
    black_player = User.objects.create_user(
        username='black_player',
        email='black@test.com',
        password='password123'
    )
    
    # 创建游戏
    game = Game.objects.create(
        red_player=red_player,
        black_player=black_player,
        game_type='online',
        status='playing',
        fen_current=Game._meta.get_field('fen_start').default,
        turn='w'
    )
    
    return {
        'game': game,
        'red_player': red_player,
        'black_player': black_player
    }


@pytest.fixture
def jwt_token(create_test_game):
    """获取 JWT token"""
    from authentication.services import TokenService
    
    red_player = create_test_game['red_player']
    tokens = TokenService.generate_tokens(red_player)
    token = tokens['access_token']
    
    # 验证 token payload 确保有 user_id
    payload = TokenService.verify_token(token)
    assert 'user_id' in payload, f"JWT payload missing user_id, got: {payload.keys()}"
    
    return {
        'token': token,
        'game_id': str(create_test_game['game'].id),
        'red_player': red_player
    }


@pytest.mark.asyncio
@pytest.mark.django_db
@pytest.mark.django_db
async def test_websocket_connection(jwt_token):
    """测试 WebSocket 连接"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    # 连接到 WebSocket（使用更长的超时时间）
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    # 增加超时时间到 5 秒
    connected, subprotocol = await communicator.connect(timeout=5)
    
    # 应该连接成功
    assert connected is True, f"WebSocket connection failed, subprotocol: {subprotocol}"
    
    # 接收初始游戏状态（增加超时）
    response = await communicator.receive_json_from(timeout=5)
    
    assert response['type'] == 'GAME_STATE'
    assert 'payload' in response
    assert 'fen' in response['payload']
    
    # 断开连接
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_invalid_token():
    """测试无效的 JWT token"""
    # 使用无效 token 连接
    communicator = WebsocketCommunicator(
        application,
        "/ws/game/12345/?token=invalid_token"
    )
    
    connected, subprotocol = await communicator.connect()
    
    # 应该连接失败
    assert connected is False
    
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_join_room(jwt_token):
    """测试加入游戏房间"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始游戏状态
    await communicator.receive_json_from()
    
    # 发送 JOIN 消息
    await communicator.send_json_to({
        'type': 'JOIN',
        'payload': {}
    })
    
    # 接收 JOIN_RESULT
    response = await communicator.receive_json_from()
    
    assert response['type'] == 'JOIN_RESULT'
    assert response['payload']['success'] is True
    
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_make_move(jwt_token):
    """测试走棋"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始游戏状态
    initial_state = await communicator.receive_json_from()
    assert initial_state['type'] == 'GAME_STATE'
    
    # 发送走棋消息（炮二进二：b3 -> b5）
    await communicator.send_json_to({
        'type': 'MOVE',
        'payload': {
            'from': 'b3',
            'to': 'b5'
        }
    })
    
    # 接收走棋结果
    response = await communicator.receive_json_from()
    
    assert response['type'] == 'MOVE_RESULT'
    assert response['payload']['success'] is True
    assert response['payload']['move']['from'] == 'b3'
    assert response['payload']['move']['to'] == 'b5'
    
    # 验证 FEN 已更新
    assert 'fen' in response['payload']
    
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_invalid_move(jwt_token):
    """测试无效走棋"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始游戏状态
    await communicator.receive_json_from()
    
    # 发送无效走棋（马不能走到那里）
    await communicator.send_json_to({
        'type': 'MOVE',
        'payload': {
            'from': 'b1',  # 马
            'to': 'e5'     # 无效位置
        }
    })
    
    # 接收错误消息
    response = await communicator.receive_json_from()
    
    assert response['type'] == 'ERROR'
    assert response['payload']['success'] is False
    
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_heartbeat(jwt_token):
    """测试心跳机制"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始游戏状态
    await communicator.receive_json_from()
    
    # 发送心跳
    await communicator.send_json_to({
        'type': 'HEARTBEAT',
        'payload': {}
    })
    
    # 接收心跳响应
    response = await communicator.receive_json_from()
    
    assert response['type'] == 'HEARTBEAT'
    assert response['payload']['acknowledged'] is True
    
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_game_state_sync(jwt_token, create_test_game):
    """测试游戏状态同步（多玩家）"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    # 红方连接
    red_communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    red_connected, _ = await red_communicator.connect()
    assert red_connected is True
    
    # 红方接收初始状态
    await red_communicator.receive_json_from()
    
    # 创建黑方 token
    from authentication.services import JWTService
    black_player = create_test_game['black_player']
    black_token = JWTService.generate_token(str(black_player.id))
    
    # 黑方连接
    black_communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={black_token}"
    )
    
    black_connected, _ = await black_communicator.connect()
    assert black_connected is True
    
    # 黑方接收初始状态
    await black_communicator.receive_json_from()
    
    # 红方走棋
    await red_communicator.send_json_to({
        'type': 'MOVE',
        'payload': {
            'from': 'b3',
            'to': 'b5'
        }
    })
    
    # 红方接收走棋结果
    red_response = await red_communicator.receive_json_from()
    assert red_response['type'] == 'MOVE_RESULT'
    
    # 黑方也应该收到走棋广播
    black_response = await black_communicator.receive_json_from()
    assert black_response['type'] == 'MOVE_RESULT'
    assert black_response['payload']['move']['from'] == 'b3'
    assert black_response['payload']['move']['to'] == 'b5'
    
    # 清理
    await red_communicator.disconnect()
    await black_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_player_join_leave(jwt_token):
    """测试玩家加入/离开通知"""
    game_id = jwt_token['game_id']
    token = jwt_token['token']
    
    # 红方连接
    red_communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    red_connected, _ = await red_communicator.connect()
    assert red_connected is True
    
    # 接收初始状态
    await red_communicator.receive_json_from()
    
    # 创建黑方 token 并连接
    from authentication.services import JWTService
    from users.models import User
    
    black_player = User.objects.get(username='black_player')
    black_token = JWTService.generate_token(str(black_player.id))
    
    black_communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={black_token}"
    )
    
    black_connected, _ = await black_communicator.connect()
    assert black_connected is True
    
    # 黑方接收初始状态
    await black_communicator.receive_json_from()
    
    # 红方应该收到黑方加入的通知
    red_notification = await red_communicator.receive_json_from()
    assert red_notification['type'] == 'PLAYER_JOIN'
    assert 'user_id' in red_notification['payload']
    
    # 黑方断开连接
    await black_communicator.disconnect()
    
    # 红方应该收到黑方离开的通知
    red_leave_notification = await red_communicator.receive_json_from()
    assert red_leave_notification['type'] == 'PLAYER_LEAVE'
    
    # 清理
    await red_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_unauthorized_access(db, jwt_token):
    """测试未授权访问"""
    # 创建一个不属于游戏的用户
    other_user = User.objects.create_user(
        username='other_user',
        email='other@test.com',
        password='password123'
    )
    
    from authentication.services import JWTService
    other_token = JWTService.generate_token(str(other_user.id))
    
    # 尝试连接
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{jwt_token['game_id']}/?token={other_token}"
    )
    
    connected, _ = await communicator.connect()
    
    # 应该连接失败（无权访问）
    assert connected is False
    
    await communicator.disconnect()


# 辅助函数
async def receive_json_with_timeout(communicator, timeout=1.0):
    """带超时的接收 JSON"""
    import asyncio
    try:
        response = await asyncio.wait_for(
            communicator.receive_json_from(),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        return None
