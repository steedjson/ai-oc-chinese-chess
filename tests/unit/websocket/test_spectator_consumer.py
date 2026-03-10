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
        
        tokens = TokenService.generate_tokens(test_user)
        token = tokens['access_token']
        
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


# ==================== 补充测试用例 ====================

class TestSpectatorConsumerHeartbeat:
    """SpectatorConsumer 心跳测试"""
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_updates_time(self):
        """测试处理心跳更新时间"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.last_heartbeat = timezone.now() - timezone.timedelta(minutes=5)
        old_time = consumer.last_heartbeat
        
        await consumer._handle_heartbeat({})
        
        assert consumer.last_heartbeat >= old_time
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_sends_ack(self):
        """测试处理心跳发送确认"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer._handle_heartbeat({})
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'HEARTBEAT'
        assert call_args['payload']['acknowledged'] is True


class TestSpectatorConsumerPermissions:
    """SpectatorConsumer 权限测试"""
    
    @pytest.mark.asyncio
    async def test_can_spectate_pending_game(self, test_user, test_user2):
        """测试可以观战待开始游戏"""
        from games.spectator_consumer import SpectatorConsumer
        
        pending_game = Game.objects.create(
            game_type='online',
            status=GameStatus.PENDING,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(pending_game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is True
    
    @pytest.mark.asyncio
    async def test_can_spectate_black_win_game(self, test_user, test_user2):
        """测试不能观战黑方胜利游戏"""
        from games.spectator_consumer import SpectatorConsumer
        
        finished_game = Game.objects.create(
            game_type='online',
            status=GameStatus.BLACK_WIN,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            winner='black'
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(finished_game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is False
    
    @pytest.mark.asyncio
    async def test_can_spectate_draw_game(self, test_user, test_user2):
        """测试不能观战和棋"""
        from games.spectator_consumer import SpectatorConsumer
        
        draw_game = Game.objects.create(
            game_type='online',
            status=GameStatus.DRAW,
            red_player=test_user,
            black_player=test_user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(draw_game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        can_spectate = await consumer._can_spectate_game()
        
        assert can_spectate is False


class TestSpectatorConsumerGameOperations:
    """SpectatorConsumer 游戏操作测试"""
    
    @pytest.mark.asyncio
    async def test_get_game_state_with_spectator_count(self, game):
        """测试获取游戏状态包含观战人数"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        
        game_state = await consumer._get_game_state()
        
        assert 'game_id' in game_state
        assert 'spectator_count' in game_state
        assert 'fen' in game_state
        assert 'turn' in game_state
        assert 'status' in game_state
        assert 'players' in game_state
    
    @pytest.mark.asyncio
    async def test_get_spectator_count(self, game, test_user2):
        """测试获取观战人数"""
        from games.spectator_consumer import SpectatorConsumer
        from games.spectator import SpectatorManager
        
        # 先加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        consumer = SpectatorConsumer()
        
        count = await consumer._get_spectator_count()
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_join_spectate_returns_success(self, game, test_user2):
        """测试加入观战返回成功"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        
        result = await consumer._join_spectate()
        
        assert result['success'] is True
        assert 'spectator' in result


class TestSpectatorConsumerDisconnect:
    """SpectatorConsumer 断开连接测试"""
    
    @pytest.mark.asyncio
    async def test_disconnect_removes_from_groups(self, game, test_user2):
        """测试断开连接从群组移除"""
        from games.spectator_consumer import SpectatorConsumer
        from games.spectator import SpectatorManager
        
        # 先加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        consumer.room_group_name = f'spectate_{game.id}'
        consumer.player_room_group_name = f'game_{game.id}'
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_discard = AsyncMock()
        
        await consumer.disconnect(1000)
        
        # 验证调用了 group_discard
        assert consumer.channel_layer.group_discard.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_disconnect_updates_spectator_status(self, game, test_user2):
        """测试断开连接更新观战状态"""
        from games.spectator_consumer import SpectatorConsumer
        from games.spectator import SpectatorManager, SpectatorStatus
        
        # 先加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        consumer.room_group_name = f'spectate_{game.id}'
        consumer.player_room_group_name = f'game_{game.id}'
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_discard = AsyncMock()
        consumer.channel_layer.group_send = AsyncMock()
        
        await consumer.disconnect(1000)
        
        # 验证观战状态已更新
        spectator = await Spectator.async_get(game=game, user=test_user2)
        assert spectator.status == SpectatorStatus.LEFT


class TestSpectatorConsumerChannelHandlers:
    """SpectatorConsumer Channel 处理器测试"""
    
    @pytest.mark.asyncio
    async def test_game_state_update_handler(self):
        """测试游戏状态更新处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'fen': 'new_fen',
                'turn': 'b',
                'status': 'playing'
            }
        }
        
        await consumer.game_state_update(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'GAME_STATE_UPDATE'
        assert call_args['payload']['fen'] == 'new_fen'
    
    @pytest.mark.asyncio
    async def test_spectator_list_handler(self):
        """测试观战者列表处理器"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        event = {
            'data': {
                'spectators': [
                    {'user_id': '1', 'username': 'user1'},
                    {'user_id': '2', 'username': 'user2'}
                ],
                'count': 2
            }
        }
        
        await consumer.spectator_list(event)
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'SPECTATOR_LIST'
        assert len(call_args['payload']['spectators']) == 2


class TestSpectatorManagerConsumerFunctions:
    """SpectatorManagerConsumer 函数测试"""
    
    @pytest.mark.asyncio
    async def test_notify_spectators_with_channel_layer(self, game):
        """测试通知观战者使用 channel layer"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.notify_spectators(
                game_id=str(game.id),
                message_type='GAME_STATE_UPDATE',
                data={'key': 'value'}
            )
            
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == f'spectate_{game.id}'
    
    @pytest.mark.asyncio
    async def test_broadcast_move_format(self, game):
        """测试广播走棋格式"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        move_data = {
            'from': '04',
            'to': '24',
            'piece': 'C',
            'captured': None
        }
        
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.broadcast_move(
                game_id=str(game.id),
                move_data=move_data
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args['data']['type'] == 'move'
            assert call_args['data']['move'] == move_data
    
    @pytest.mark.asyncio
    async def test_broadcast_game_over_format(self, game):
        """测试广播游戏结束格式"""
        from games.spectator_consumer import SpectatorManagerConsumer
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        
        result_data = {
            'winner': 'red',
            'reason': 'checkmate',
            'rating_change': {'red': 10, 'black': -10}
        }
        
        with patch.object(channel_layer, 'group_send', new_callable=AsyncMock) as mock_send:
            await SpectatorManagerConsumer.broadcast_game_over(
                game_id=str(game.id),
                result_data=result_data
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][1]
            assert call_args['data']['winner'] == 'red'
            assert call_args['data']['reason'] == 'checkmate'


class TestSpectatorConsumerErrorHandling:
    """SpectatorConsumer 错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_send_error_format(self):
        """测试发送错误格式"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer._send_error('Test error message', 'TEST_ERROR_CODE')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['success'] is False
        assert call_args['payload']['error']['code'] == 'TEST_ERROR_CODE'
        assert call_args['payload']['error']['message'] == 'Test error message'
        assert 'timestamp' in call_args
    
    @pytest.mark.asyncio
    async def test_handle_join_with_game_state(self, game):
        """测试处理加入返回游戏状态"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.send = AsyncMock()
        
        await consumer._handle_join({'type': 'JOIN'})
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        
        assert call_args['type'] == 'JOIN_RESULT'
        assert call_args['payload']['success'] is True
        assert 'game_state' in call_args['payload']
    
    @pytest.mark.asyncio
    async def test_handle_leave_closes_connection(self):
        """测试处理离开关闭连接"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.close = AsyncMock()
        
        await consumer._handle_leave({'type': 'LEAVE'})
        
        consumer.close.assert_called_once()


class TestSpectatorConsumerAuthentication:
    """SpectatorConsumer 认证测试"""
    
    @pytest.mark.asyncio
    async def test_authenticate_from_header_bearer(self, test_user):
        """测试从 header Bearer 认证"""
        from authentication.services import TokenService
        from games.spectator_consumer import SpectatorConsumer
        
        tokens = TokenService.generate_tokens(test_user)
        token = tokens['access_token']
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': b'',
            'headers': [(b'authorization', f'Bearer {token}'.encode())]
        }
        
        async def mock_get_user(user_id):
            return {'id': str(test_user.id), 'username': test_user.username}
        
        consumer._get_user_by_id = mock_get_user
        
        user = await consumer._authenticate_connection()
        
        assert user is not None
        assert user['id'] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_token_format(self):
        """测试无效 token 格式认证失败"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': b'token=invalid_token_format_123',
            'headers': []
        }
        
        user = await consumer._authenticate_connection()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_missing_user_id(self):
        """测试缺少 user_id 认证失败"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'query_string': b'token=no_user_id',
            'headers': []
        }
        
        user = await consumer._authenticate_connection()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """测试获取用户不存在"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        
        fake_user_id = '00000000-0000-0000-0000-000000000000'
        user = await consumer._get_user_by_id(fake_user_id)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, test_user):
        """测试成功获取用户"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        
        user = await consumer._get_user_by_id(str(test_user.id))
        
        assert user is not None
        assert user['id'] == str(test_user.id)
        assert user['username'] == test_user.username


class TestSpectatorConsumerEdgeCases:
    """SpectatorConsumer 边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_disconnect_with_exception(self, game, test_user2):
        """测试断开连接异常处理"""
        from games.spectator_consumer import SpectatorConsumer
        from games.spectator import SpectatorManager
        
        # 先加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        consumer = SpectatorConsumer()
        consumer.game_id = str(game.id)
        consumer.user = {'id': str(test_user2.id), 'username': test_user2.username}
        consumer.room_group_name = f'spectate_{game.id}'
        consumer.player_room_group_name = f'game_{game.id}'
        consumer.channel_layer = MagicMock()
        consumer.channel_layer.group_discard = AsyncMock(side_effect=Exception('Error'))
        
        # 不应该抛出异常
        await consumer.disconnect(1000)
    
    @pytest.mark.asyncio
    async def test_receive_invalid_json(self):
        """测试接收无效 JSON"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer.receive('invalid json{{{')
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert call_args['payload']['error']['code'] == 'INVALID_JSON'
    
    @pytest.mark.asyncio
    async def test_receive_unknown_message_type(self):
        """测试接收未知消息类型"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.send = AsyncMock()
        
        await consumer.receive(json.dumps({'type': 'UNKNOWN_TYPE'}))
        
        consumer.send.assert_called_once()
        call_args = json.loads(consumer.send.call_args[1]['text_data'])
        assert call_args['type'] == 'ERROR'
        assert 'Unknown message type' in call_args['payload']['error']['message']
    
    @pytest.mark.asyncio
    async def test_connect_exception_handling(self):
        """测试连接异常处理"""
        from games.spectator_consumer import SpectatorConsumer
        
        consumer = SpectatorConsumer()
        consumer.scope = {
            'url_route': {'kwargs': {'game_id': 'test-id'}},
            'query_string': b'token=test',
            'headers': []
        }
        consumer.close = AsyncMock()
        
        # Mock _authenticate_connection to raise exception
        async def mock_auth():
            raise Exception('Test exception')
        
        consumer._authenticate_connection = mock_auth
        
        # 不应该抛出异常
        await consumer.connect()
