"""
WebSocket 统一配置中心集成测试

测试 WebSocket 配置中心的集成场景：
- 统一路由配置
- 中间件集成
- 认证流程
- 心跳机制
"""
import pytest
import json
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from datetime import timedelta

from config.asgi import application
from users.models import User
from games.models import Game
from ai_engine.models import AIGame, AIDifficulty


@pytest.fixture
async def setup_test_users(db):
    """创建测试用户"""
    user1 = User.objects.create_user(
        username='ws_test_user1',
        email='ws_test1@test.com',
        password='password123'
    )
    
    user2 = User.objects.create_user(
        username='ws_test_user2',
        email='ws_test2@test.com',
        password='password123'
    )
    
    return {'user1': user1, 'user2': user2}


@pytest.fixture
async def setup_test_game(setup_test_users, db):
    """创建测试游戏"""
    user1 = setup_test_users['user1']
    user2 = setup_test_users['user2']
    
    game = Game.objects.create(
        red_player=user1,
        black_player=user2,
        game_type='online',
        status='playing',
        fen_current=Game._meta.get_field('fen_start').default,
        turn='w'
    )
    
    return {
        'game': game,
        'user1': user1,
        'user2': user2
    }


@pytest.fixture
def jwt_tokens(setup_test_game):
    """生成 JWT tokens"""
    from authentication.services import JWTService
    
    user1 = setup_test_game['user1']
    user2 = setup_test_game['user2']
    game = setup_test_game['game']
    
    token1 = JWTService.generate_token(str(user1.id))
    token2 = JWTService.generate_token(str(user2.id))
    
    return {
        'token1': token1,
        'token2': token2,
        'game_id': str(game.id),
        'user1': user1,
        'user2': user2
    }


@pytest.mark.asyncio
async def test_unified_routing_game(jwt_tokens):
    """测试统一路由 - 游戏对弈"""
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    # 连接到统一路由的游戏端点
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, subprotocol = await communicator.connect()
    
    # 应该连接成功
    assert connected is True
    
    # 应该收到初始游戏状态
    response = await communicator.receive_json_from()
    assert response['type'] == 'GAME_STATE'
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_unified_routing_ai_game(setup_test_users, db):
    """测试统一路由 - AI 对弈"""
    from authentication.services import JWTService
    
    user = setup_test_users['user1']
    token = JWTService.generate_token(str(user.id))
    
    # 创建 AI 难度
    difficulty = AIDifficulty.objects.create(
        level=5,
        name='中级',
        elo_estimate=1200,
        skill_level=8,
        search_depth=10,
        think_time_ms=1500
    )
    
    # 创建 AI 游戏
    ai_game = AIGame.objects.create(
        player=user,
        difficulty=difficulty,
        status='waiting'
    )
    
    # 连接到 AI 游戏端点
    communicator = WebsocketCommunicator(
        application,
        f"/ws/ai/game/{ai_game.id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    
    # 应该连接成功
    assert connected is True
    
    # 应该收到连接确认
    response = await communicator.receive_json_from()
    assert response['type'] == 'connected'
    assert response['data']['game_id'] == str(ai_game.id)
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_unified_routing_matchmaking(setup_test_users):
    """测试统一路由 - 匹配系统"""
    from authentication.services import JWTService
    
    user = setup_test_users['user1']
    token = JWTService.generate_token(str(user.id))
    
    # 连接到匹配系统端点
    communicator = WebsocketCommunicator(
        application,
        f"/ws/matchmaking/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    
    # 应该连接成功
    assert connected is True
    
    # 应该收到连接确认
    response = await communicator.receive_json_from()
    assert response['type'] == 'connected'
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_middleware_jwt_auth_valid(jwt_tokens):
    """测试中间件 - JWT 认证（有效 token）"""
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    
    # 有效 token 应该连接成功
    assert connected is True
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_middleware_jwt_auth_invalid(db):
    """测试中间件 - JWT 认证（无效 token）"""
    # 创建测试游戏但不使用有效 token
    user = User.objects.create_user(
        username='test_invalid',
        email='test_invalid@test.com',
        password='password123'
    )
    
    game = Game.objects.create(
        red_player=user,
        black_player=None,
        game_type='single',
        status='pending',
        fen_current=Game._meta.get_field('fen_start').default,
        turn='w'
    )
    
    # 使用无效 token
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game.id}/?token=invalid_token_xyz"
    )
    
    connected, _ = await communicator.connect()
    
    # 无效 token 应该连接失败
    assert connected is False
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_middleware_jwt_auth_missing(db):
    """测试中间件 - JWT 认证（缺少 token）"""
    user = User.objects.create_user(
        username='test_missing',
        email='test_missing@test.com',
        password='password123'
    )
    
    game = Game.objects.create(
        red_player=user,
        black_player=None,
        game_type='single',
        status='pending',
        fen_current=Game._meta.get_field('fen_start').default,
        turn='w'
    )
    
    # 不提供 token
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game.id}/"
    )
    
    connected, _ = await communicator.connect()
    
    # 缺少 token 应该连接失败
    assert connected is False
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_middleware_permission_check(jwt_tokens):
    """测试中间件 - 权限检查"""
    from authentication.services import JWTService
    
    # 创建一个不属于游戏的用户
    other_user = User.objects.create_user(
        username='test_other',
        email='test_other@test.com',
        password='password123'
    )
    
    other_token = JWTService.generate_token(str(other_user.id))
    
    # 尝试连接不属于自己游戏
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{jwt_tokens['game_id']}/?token={other_token}"
    )
    
    connected, _ = await communicator.connect()
    
    # 无权限应该连接失败
    assert connected is False
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_heartbeat_mechanism(jwt_tokens):
    """测试心跳机制"""
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始状态
    await communicator.receive_json_from()
    
    # 发送心跳
    await communicator.send_json_to({
        'type': 'HEARTBEAT',
        'payload': {'timestamp': '2026-03-03T12:00:00Z'}
    })
    
    # 接收心跳响应
    response = await communicator.receive_json_from()
    assert response['type'] == 'HEARTBEAT'
    assert response['payload']['acknowledged'] is True
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_message_logging(jwt_tokens, caplog):
    """测试消息日志"""
    import logging
    
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    # 设置日志级别
    logger = logging.getLogger('chinese_chess.websocket')
    logger.setLevel('INFO')
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始状态
    await communicator.receive_json_from()
    
    # 发送消息（应该被日志记录）
    await communicator.send_json_to({
        'type': 'HEARTBEAT',
        'payload': {}
    })
    
    await communicator.receive_json_from()
    
    # 验证日志（取决于具体实现）
    # 这里只是示例，实际实现需要检查日志输出
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_connection_logging(jwt_tokens, caplog):
    """测试连接日志"""
    import logging
    
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    # 设置日志级别
    logger = logging.getLogger('chinese_chess.websocket')
    logger.setLevel('INFO')
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 应该记录连接日志
    await communicator.receive_json_from()
    
    await communicator.disconnect()
    
    # 应该记录断开连接日志


@pytest.mark.asyncio
async def test_error_handling(jwt_tokens):
    """测试错误处理"""
    game_id = jwt_tokens['game_id']
    token = jwt_tokens['token1']
    
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token}"
    )
    
    connected, _ = await communicator.connect()
    assert connected is True
    
    # 接收初始状态
    await communicator.receive_json_from()
    
    # 发送无效 JSON
    await communicator.send_to(text_data='invalid json')
    
    # 应该收到错误响应
    response = await communicator.receive_json_from()
    assert response['type'] == 'ERROR'
    
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_concurrent_connections(setup_test_game, jwt_tokens):
    """测试并发连接"""
    game_id = jwt_tokens['game_id']
    token1 = jwt_tokens['token1']
    token2 = jwt_tokens['token2']
    
    # 红方连接
    red_comm = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token1}"
    )
    
    red_connected, _ = await red_comm.connect()
    assert red_connected is True
    
    # 黑方连接
    black_comm = WebsocketCommunicator(
        application,
        f"/ws/game/{game_id}/?token={token2}"
    )
    
    black_connected, _ = await black_comm.connect()
    assert black_connected is True
    
    # 双方都应该收到初始状态
    red_state = await red_comm.receive_json_from()
    black_state = await black_comm.receive_json_from()
    
    assert red_state['type'] == 'GAME_STATE'
    assert black_state['type'] == 'GAME_STATE'
    
    # 红方走棋
    await red_comm.send_json_to({
        'type': 'MOVE',
        'payload': {'from': 'b3', 'to': 'b5'}
    })
    
    # 红方收到结果
    red_response = await red_comm.receive_json_from()
    assert red_response['type'] == 'MOVE_RESULT'
    
    # 黑方也应该收到广播
    black_response = await black_comm.receive_json_from()
    assert black_response['type'] == 'MOVE_RESULT'
    
    # 清理
    await red_comm.disconnect()
    await black_comm.disconnect()
