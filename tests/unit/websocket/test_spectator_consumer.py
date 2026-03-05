"""
观战 WebSocket Consumer 单元测试

测试 spectator_consumer.py 中的 SpectatorConsumer
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from channels.testing import WebsocketCommunicator
from django.utils import timezone

from games.models import Game, GameStatus
from games.spectator import Spectator, SpectatorStatus
from users.models import User


# 注意：由于 WebSocket 测试需要完整的 ASGI 配置，这里主要测试逻辑方法
# 完整的 WebSocket 集成测试在 integration 目录中


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username='ws_spectator_user',
        email='ws_spectator@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户"""
    return User.objects.create_user(
        username='ws_spectator_user2',
        email='ws_spectator2@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def game(db, test_user, test_user2):
    """创建测试游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.PLAYING,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        turn='w'
    )


class TestSpectatorConsumerLogic:
    """SpectatorConsumer 逻辑方法测试"""
    
    @pytest.mark.asyncio
    async def test_authenticate_connection_success(self, test_user):
        """测试认证成功"""
        from authentication.services import TokenService
        from games.spectator_consumer import SpectatorConsumer
        
        token = TokenService.generate_token(str(test_user.id))
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': f'token={token}'.encode(),
            'headers': []
        }
        
        # Mock _get_user_by_id
        async def mock_get_user(user_id):
            return {'id': str(test_user.id), 'username': test_user.username}
        
        consumer._get_user_by_id = mock_get_user
        
        user = await consumer._authenticate_connection()
        
        assert user is not None
        assert user['id'] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_authenticate_connection_no_token(self):
        """测试无 token 认证失败"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': []
        }
        
        user = await consumer._authenticate_connection()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_connection_invalid_token(self):
        """测试无效 token 认证失败"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': b'token=invalid_token',
            'headers': []
        }
        
        user = await consumer._authenticate_connection()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_can_spectate_game_success(self, game, test_user2):
        """测试可以观战"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is True
    
    @pytest.mark.asyncio
    async def test_can_spectate_game_finished(self, test_user, test_user2):
        """测试已结束游戏不能观战"""
        from games.spectator_consumer import SpectatorConsumer
        
        finished_game = Game.objects.create(
            game_type='online',
            status=GameStatus.RED_WIN,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            winner='red'
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(finished_game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is False
    
    @pytest.mark.asyncio
    async def test_can_spectate_game_player_cannot_spectate(self, game, test_user):
        """测试游戏参与者不能观战"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user.id), 'username': test_user.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is False
    
    @pytest.mark.asyncio
    async def test_get_game_state(self, game):
        """测试获取游戏状态"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        
        game_state = await consumer._get_game_state()
        
        assert game_state['game_id'] == str(game.id)
        assert game_state['fen'] == game.fen_current
        assert game_state['turn'] == game.turn
        assert game_state['status'] == game.status
    
    @pytest.mark.asyncio
    async def test_join_spectate(self, game, test_user2):
        """测试加入观战"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        result = await consumer._join_spectate()
        
        assert result['success'] is True
        assert result['spectator'] is not None
    
    @pytest.mark.asyncio
    async def test_leave_spectate(self, game, test_user2):
        """测试离开观战"""
        from games.spectator_consumer import SpectatorConsumer
        
        # 先加入
        from games.spectator import SpectatorManager
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        result = await consumer._leave_spectate()
        
        # 验证观战记录已更新
        spectator = await Spectator.async_get(game=game, user=test_user2)
        assert spectator.status == SpectatorStatus.LEFT


class TestSpectatorManagerConsumer:
    """SpectatorManagerConsumer 测试"""
    
    @pytest.mark.asyncio
    async def test_notify_spectators(self, game):
        """测试通知观战者"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        # Mock group_send
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.notify_spectators(
                game_id=str(game.id),
                message_type='GAME_STATE_UPDATE',
                data={'type': 'test'}
            )
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_move(self, game):
        """测试广播走棋"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        move_data = {
            'from': '04',
            'to': '24',
            'piece': 'C'
        }
        
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.broadcast_move(
                game_id=str(game.id),
                move_data=move_data
            )
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_game_over(self, game):
        """测试广播游戏结束"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        result_data = {
            'winner': 'red',
            'reason': 'checkmate'
        }
        
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.broadcast_game_over(
                game_id=str(game.id),
                result_data=result_data
            )
            
            mock_send.assert_called_once()


class TestSpectatorMessageHandlers:
    """观战消息处理器测试"""
    
    @pytest.mark.asyncio
    async def test_handle_join(self):
        """测试处理加入消息"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer._handle_join({'type': 'JOIN'})
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'JOIN_RESULT'
        assert call_args['payload']['success'] is True
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        """测试处理心跳消息"""
        from games.spectator_consumer import SpectatorConsumer
        from datetime import datetime
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer._handle_heartbeat({'type': 'HEARTBEAT'})
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'HEARTBEAT'
        assert call_args['payload']['acknowledged'] is True
    
    @pytest.mark.asyncio
    async def test_send_error(self):
        """测试发送错误消息"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer._send_error('Test error', 'TEST_ERROR')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'TEST_ERROR'
        assert call_args['payload']['error']['message'] == 'Test error'


class TestSpectatorChannelHandlers:
    """观战 Channel 处理器测试"""
    
    @pytest.mark.asyncio
    async def test_move_made_handler(self):
        """测试走棋消息处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'move': {'from': '04', 'to': '24'},
                'fen': 'test_fen',
                'turn': 'b'
            }
        }
        
        await consumer.move_made(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'MOVE_MADE'
        assert 'move' in call_args['payload']
    
    @pytest.mark.asyncio
    async def test_game_over_handler(self):
        """测试游戏结束消息处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'winner': 'red',
                'reason': 'checkmate'
            }
        }
        
        await consumer.game_over(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'GAME_OVER'
        assert call_args['payload']['winner'] == 'red'
    
    @pytest.mark.asyncio
    async def test_spectator_join_handler(self):
        """测试观战者加入消息处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'user_id': '123',
                'username': 'test_user',
                'spectator_count': 5
            }
        }
        
        await consumer.spectator_join(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'SPECTATOR_JOIN'
    
    @pytest.mark.asyncio
    async def test_spectator_leave_handler(self):
        """测试观战者离开消息处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'user_id': '123',
                'username': 'test_user',
                'spectator_count': 4
            }
        }
        
        await consumer.spectator_leave(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'SPECTATOR_LEAVE'


class TestSpectatorStatusEnum:
    """SpectatorStatus 枚举测试"""
    
    def test_status_values(self):
        """测试状态值"""
        assert SpectatorStatus.WATCHING.value == 'watching'
        assert SpectatorStatus.LEFT.value == 'left'
        assert SpectatorStatus.KICKED.value == 'kicked'
    
    def test_status_labels(self):
        """测试状态标签"""
        assert SpectatorStatus.WATCHING.label == '观战中'
        assert SpectatorStatus.LEFT.label == '已离开'
        assert SpectatorStatus.KICKED.label == '被踢出'
    
    def test_status_choices(self):
        """测试状态选择"""
        choices = SpectatorStatus.choices
        assert len(choices) == 3
        
        choice_values = [choice[0] for choice in choices]
        assert 'watching' in choice_values
        assert 'left' in choice_values
        assert 'kicked' in choice_values
