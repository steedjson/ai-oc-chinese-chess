"""
聊天系统单元测试

测试 ChatMessage 模型和 ChatMessageManager
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from uuid import uuid4

from games.chat import ChatMessage, ChatMessageManager, MessageType
from games.models import Game
from users.models import User


@pytest.mark.django_db
class TestChatMessageModel:
    """测试 ChatMessage 模型"""
    
    def test_create_text_message(self, game, user):
        """测试创建文本消息"""
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='Hello, World!',
            message_type=MessageType.TEXT,
            room_type='game'
        )
        
        assert message.content == 'Hello, World!'
        assert message.message_type == MessageType.TEXT
        assert message.room_type == 'game'
        assert message.sender == user
        assert message.game == game
        assert message.is_deleted is False
        assert message.message_uuid is not None
    
    def test_create_system_message(self, game):
        """测试创建系统消息（无发送者）"""
        message = ChatMessage.objects.create(
            game=game,
            sender=None,
            content='游戏开始',
            message_type=MessageType.SYSTEM,
            room_type='game'
        )
        
        assert message.sender is None
        assert message.message_type == MessageType.SYSTEM
        assert message.content == '游戏开始'
    
    def test_create_emoji_message(self, game, user):
        """测试创建表情消息"""
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='😀',
            message_type=MessageType.EMOJI,
            room_type='game'
        )
        
        assert message.message_type == MessageType.EMOJI
        assert message.content == '😀'
    
    def test_message_to_dict(self, game, user):
        """测试消息转换为字典"""
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='Test message',
            message_type=MessageType.TEXT,
            room_type='game'
        )
        
        data = message.to_dict()
        
        assert data['id'] == str(message.message_uuid)
        assert data['game_id'] == str(game.id)
        assert data['sender']['id'] == str(user.id)
        assert data['sender']['username'] == user.username
        assert data['content'] == 'Test message'
        assert data['message_type'] == 'text'
        assert data['room_type'] == 'game'
        assert 'created_at' in data
    
    def test_soft_delete(self, game, user):
        """测试软删除"""
        message = ChatMessage.objects.create(
            game=game,
            sender=user,
            content='To be deleted',
            message_type=MessageType.TEXT,
            room_type='game'
        )
        
        assert message.is_deleted is False
        
        message.is_deleted = True
        message.save()
        
        assert message.is_deleted is True
        
        # 已删除的消息不应出现在默认查询中
        from games.chat import ChatMessageManager
        messages = ChatMessageManager.get_message_history_sync(
            game_id=str(game.id),
            room_type='game',
            limit=50
        )
        
        assert len(messages) == 0


@pytest.mark.django_db
class TestChatMessageManager:
    """测试 ChatMessageManager"""
    
    def test_send_message_success(self, game, user):
        """测试成功发送消息"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Hello!',
            message_type='text',
            room_type='game'
        )
        
        assert result['success'] is True
        assert result['message'] is not None
        assert result['error'] is None
        assert result['message'].content == 'Hello!'
    
    def test_send_message_empty_content(self, game, user):
        """测试发送空消息"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='',
            message_type='text',
            room_type='game'
        )
        
        assert result['success'] is False
        assert result['message'] is None
        assert '不能为空' in result['error']
    
    def test_send_message_too_long(self, game, user):
        """测试发送超长消息"""
        long_content = 'x' * 600  # 超过 500 字符限制
        
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content=long_content,
            message_type='text',
            room_type='game'
        )
        
        assert result['success'] is False
        assert result['message'] is None
        assert '长度不能超过' in result['error']
    
    def test_send_message_rate_limit(self, game, user):
        """测试消息限流"""
        # 发送第一条消息
        result1 = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Message 1',
            message_type='text',
            room_type='game'
        )
        assert result1['success'] is True
        
        # 立即发送第二条消息（应该被限流）
        result2 = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Message 2',
            message_type='text',
            room_type='game'
        )
        
        assert result2['success'] is False
        assert '发送频率过快' in result2['error']
    
    def test_send_emoji_message_valid(self, game, user):
        """测试发送有效表情"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='😀',
            message_type='emoji',
            room_type='game'
        )
        
        assert result['success'] is True
        assert result['message'].message_type == MessageType.EMOJI
    
    def test_send_emoji_message_invalid(self, game, user):
        """测试发送无效表情"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Invalid emoji 🚫',
            message_type='emoji',
            room_type='game'
        )
        
        assert result['success'] is False
        assert '不支持的表情' in result['error']
    
    def test_get_message_history(self, game, user):
        """测试获取消息历史"""
        import time
        # 创建多条消息（需要避开限流）
        messages_created = []
        for i in range(5):
            # 直接创建消息，绕过限流
            message = ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
            messages_created.append(message)
            time.sleep(0.1)  # 小延迟确保时间戳不同
        
        # 获取历史消息
        messages = ChatMessageManager.get_message_history_sync(
            game_id=str(game.id),
            room_type='game',
            limit=50
        )
        
        assert len(messages) == 5
        # 验证按时间正序排列
        for i in range(len(messages) - 1):
            assert messages[i]['created_at'] <= messages[i+1]['created_at']
    
    def test_get_message_history_limit(self, game, user):
        """测试获取消息历史（限制数量）"""
        import time
        # 创建 10 条消息（直接创建，绕过限流）
        for i in range(10):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
            time.sleep(0.05)
        
        # 只获取 5 条
        messages = ChatMessageManager.get_message_history_sync(
            game_id=str(game.id),
            room_type='game',
            limit=5
        )
        
        assert len(messages) == 5
    
    def test_get_message_count(self, game, user):
        """测试获取消息数量"""
        # 创建 3 条消息（直接创建，绕过限流）
        for i in range(3):
            ChatMessage.objects.create(
                game=game,
                sender=user,
                content=f'Message {i}',
                message_type=MessageType.TEXT,
                room_type='game'
            )
        
        count = ChatMessageManager.get_message_count_sync(
            game_id=str(game.id),
            room_type='game'
        )
        
        assert count == 3
    
    def test_delete_message_success(self, game, user):
        """测试成功删除消息"""
        # 创建消息
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='To delete',
            message_type='text',
            room_type='game'
        )
        
        message_uuid = str(result['message'].message_uuid)
        
        # 删除消息
        delete_result = ChatMessageManager.delete_message_sync(
            message_uuid=message_uuid,
            user_id=str(user.id)
        )
        
        assert delete_result['success'] is True
        
        # 验证消息已软删除
        message = ChatMessage.objects.get(message_uuid=message_uuid)
        assert message.is_deleted is True
    
    def test_delete_message_no_permission(self, game, user, user2):
        """测试无权限删除他人消息"""
        # 用户 1 创建消息
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='My message',
            message_type='text',
            room_type='game'
        )
        
        message_uuid = str(result['message'].message_uuid)
        
        # 用户 2 尝试删除（应该失败）
        delete_result = ChatMessageManager.delete_message_sync(
            message_uuid=message_uuid,
            user_id=str(user2.id)
        )
        
        assert delete_result['success'] is False
        assert '无权限' in delete_result['error']
    
    def test_is_valid_emoji(self):
        """测试表情验证"""
        assert ChatMessageManager.is_valid_emoji('😀') is True
        assert ChatMessageManager.is_valid_emoji('👍') is True
        assert ChatMessageManager.is_valid_emoji('❤️') is True
        assert ChatMessageManager.is_valid_emoji('Hello') is False
        assert ChatMessageManager.is_valid_emoji('Hello 😀') is True


@pytest.mark.django_db
class TestChatMessageRoomTypes:
    """测试不同房间类型"""
    
    def test_game_room_chat(self, game, user):
        """测试对局房间聊天"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Game room message',
            message_type='text',
            room_type='game'
        )
        
        assert result['success'] is True
        assert result['message'].room_type == 'game'
    
    def test_spectator_room_chat(self, game, user):
        """测试观战房间聊天"""
        result = ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Spectator room message',
            message_type='text',
            room_type='spectator'
        )
        
        assert result['success'] is True
        assert result['message'].room_type == 'spectator'
    
    def test_separate_message_histories(self, game, user):
        """测试不同房间类型的消息历史独立"""
        # 在对局房间发送消息
        ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Game message',
            message_type='text',
            room_type='game'
        )
        
        # 在观战房间发送消息
        ChatMessageManager.send_message_sync(
            game_id=str(game.id),
            user_id=str(user.id),
            content='Spectator message',
            message_type='text',
            room_type='spectator'
        )
        
        # 获取对局房间消息
        game_messages = ChatMessageManager.get_message_history_sync(
            game_id=str(game.id),
            room_type='game',
            limit=50
        )
        
        # 获取观战房间消息
        spectator_messages = ChatMessageManager.get_message_history_sync(
            game_id=str(game.id),
            room_type='spectator',
            limit=50
        )
        
        assert len(game_messages) == 1
        assert len(spectator_messages) == 1
        assert game_messages[0]['content'] == 'Game message'
        assert spectator_messages[0]['content'] == 'Spectator message'


# Pytest fixtures
@pytest.fixture
def user():
    """创建测试用户"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user2():
    """创建第二个测试用户"""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123'
    )


@pytest.fixture
def game(user, user2):
    """创建测试游戏"""
    from games.models import GameStatus
    
    return Game.objects.create(
        red_player=user,
        black_player=user2,
        game_type='online',
        status=GameStatus.PLAYING,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
        turn='w'
    )
