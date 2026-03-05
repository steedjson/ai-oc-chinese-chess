"""
观战系统单元测试

测试 spectator.py 中的 Spectator 模型和 SpectatorManager
"""
import pytest
import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from games.models import Game, GameStatus
from games.spectator import Spectator, SpectatorStatus, SpectatorManager


User = get_user_model()


@pytest.fixture
def test_user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username=f'spectator_user_{timezone.now().timestamp()}',
        email='spectator@example.com',
        password='SecurePass123'
    )


@pytest.fixture
def test_user2(db):
    """创建第二个测试用户"""
    return User.objects.create_user(
        username=f'spectator_user2_{timezone.now().timestamp()}',
        email='spectator2@example.com',
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


@pytest.fixture
def pending_game(db, test_user, test_user2):
    """创建等待中的游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.PENDING,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        turn='w'
    )


@pytest.fixture
def finished_game(db, test_user, test_user2):
    """创建已结束的游戏"""
    return Game.objects.create(
        game_type='online',
        status=GameStatus.RED_WIN,
        red_player=test_user,
        black_player=test_user2,
        fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
        turn='w',
        winner='red'
    )


class TestSpectatorModel:
    """Spectator 模型测试"""
    
    def test_create_spectator(self, db, game, test_user):
        """测试创建观战记录"""
        spectator = Spectator.objects.create(
            game=game,
            user=test_user
        )
        
        assert spectator.game == game
        assert spectator.user == test_user
        assert spectator.status == SpectatorStatus.WATCHING
        assert spectator.is_anonymous is False
        assert spectator.joined_at is not None
        assert spectator.left_at is None
    
    def test_spectator_str(self, db, game, test_user):
        """测试字符串表示"""
        spectator = Spectator.objects.create(
            game=game,
            user=test_user
        )
        
        assert str(spectator) == f"Spectator {test_user.username} watching Game {game.id}"
    
    def test_spectator_unique_together(self, db, game, test_user):
        """测试唯一约束"""
        Spectator.objects.create(
            game=game,
            user=test_user
        )
        
        # 尝试创建重复记录应该失败
        with pytest.raises(Exception):
            Spectator.objects.create(
                game=game,
                user=test_user
            )
    
    def test_spectator_leave_updates_status(self, db, game, test_user):
        """测试离开观战更新状态"""
        spectator = Spectator.objects.create(
            game=game,
            user=test_user
        )
        
        spectator.status = SpectatorStatus.LEFT
        spectator.save()
        
        assert spectator.status == SpectatorStatus.LEFT
        assert spectator.left_at is not None
        assert spectator.duration is not None
    
    def test_spectator_anonymous(self, db, game, test_user):
        """测试匿名观战"""
        spectator = Spectator.objects.create(
            game=game,
            user=test_user,
            is_anonymous=True
        )
        
        assert spectator.is_anonymous is True


class TestSpectatorManagerJoin:
    """SpectatorManager.join_spectate 测试"""
    
    @pytest.mark.asyncio
    async def test_join_spectate_success(self, game, test_user):
        """测试成功加入观战"""
        result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user.id)
        )
        
        assert result['success'] is True
        assert result['spectator'] is not None
        assert result['error'] is None
        assert result['spectator'].game == game
        assert result['spectator'].user == test_user
    
    @pytest.mark.asyncio
    async def test_join_spectate_game_not_found(self, test_user):
        """测试游戏不存在"""
        fake_game_id = str(uuid.uuid4())
        
        result = await SpectatorManager.join_spectate(
            game_id=fake_game_id,
            user_id=str(test_user.id)
        )
        
        assert result['success'] is False
        assert result['spectator'] is None
        assert result['error'] == '游戏不存在'
    
    @pytest.mark.asyncio
    async def test_join_spectate_user_not_found(self, game):
        """测试用户不存在"""
        fake_user_id = str(uuid.uuid4())
        
        result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=fake_user_id
        )
        
        assert result['success'] is False
        assert result['spectator'] is None
        assert result['error'] == '用户不存在'
    
    @pytest.mark.asyncio
    async def test_join_spectate_game_finished(self, finished_game, test_user):
        """测试已结束游戏不能观战"""
        result = await SpectatorManager.join_spectate(
            game_id=str(finished_game.id),
            user_id=str(test_user.id)
        )
        
        assert result['success'] is False
        assert result['spectator'] is None
        assert '游戏未进行中' in result['error']
    
    @pytest.mark.asyncio
    async def test_join_spectate_player_cannot_spectate(self, game, test_user):
        """测试游戏参与者不能观战"""
        # test_user 是红方玩家
        result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user.id)
        )
        
        assert result['success'] is False
        assert result['spectator'] is None
        assert '游戏参与者不能观战' in result['error']
    
    @pytest.mark.asyncio
    async def test_join_spectate_already_watching(self, game, test_user):
        """测试重复加入观战"""
        # 第一次加入
        result1 = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user.id)
        )
        assert result1['success'] is True
        
        # 第二次加入
        result2 = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user.id)
        )
        assert result2['success'] is True
        assert result2.get('message') == '已在观战中'
        assert result2['spectator'].id == result1['spectator'].id
    
    @pytest.mark.asyncio
    async def test_join_spectate_anonymous(self, game, test_user2):
        """测试匿名观战"""
        result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id),
            is_anonymous=True
        )
        
        assert result['success'] is True
        assert result['spectator'].is_anonymous is True
    
    @pytest.mark.asyncio
    async def test_join_spectate_pending_game(self, pending_game, test_user2):
        """测试观战等待中的游戏"""
        result = await SpectatorManager.join_spectate(
            game_id=str(pending_game.id),
            user_id=str(test_user2.id)
        )
        
        assert result['success'] is True


class TestSpectatorManagerLeave:
    """SpectatorManager.leave_spectate 测试"""
    
    @pytest.mark.asyncio
    async def test_leave_spectate_success(self, game, test_user2):
        """测试成功离开观战"""
        # 先加入
        join_result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        assert join_result['success'] is True
        
        # 等待一小段时间
        import asyncio
        await asyncio.sleep(0.1)
        
        # 离开
        leave_result = await SpectatorManager.leave_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        assert leave_result['success'] is True
        assert 'duration' in leave_result
    
    @pytest.mark.asyncio
    async def test_leave_spectate_not_watching(self, game, test_user2):
        """测试未观战时离开"""
        result = await SpectatorManager.leave_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        assert result['success'] is False
        assert result['error'] == '未在观战中'


class TestSpectatorManagerGetSpectators:
    """SpectatorManager.get_spectators 测试"""
    
    @pytest.mark.asyncio
    async def test_get_spectators_empty(self, game):
        """测试没有观战者"""
        result = await SpectatorManager.get_spectators(game_id=str(game.id))
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_spectators_with_spectators(self, game, test_user2):
        """测试获取观战者列表"""
        # 加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        result = await SpectatorManager.get_spectators(game_id=str(game.id))
        
        assert len(result) == 1
        assert result[0]['user_id'] == str(test_user2.id)
        assert result[0]['username'] == test_user2.username
        assert 'joined_at' in result[0]
        assert 'duration' in result[0]
    
    @pytest.mark.asyncio
    async def test_get_spectators_anonymous(self, game, test_user2):
        """测试匿名观战者"""
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id),
            is_anonymous=True
        )
        
        result = await SpectatorManager.get_spectators(game_id=str(game.id))
        
        assert len(result) == 1
        assert result[0]['user_id'] is None  # 匿名用户不显示 ID
        assert result[0]['username'] == '匿名用户'
        assert result[0]['is_anonymous'] is True
    
    @pytest.mark.asyncio
    async def test_get_spectators_limit(self, game, test_user, test_user2):
        """测试限制返回数量"""
        # 创建多个观战者
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        result = await SpectatorManager.get_spectators(
            game_id=str(game.id),
            limit=1
        )
        
        assert len(result) <= 1


class TestSpectatorManagerCount:
    """SpectatorManager.get_spectator_count 测试"""
    
    @pytest.mark.asyncio
    async def test_get_spectator_count_empty(self, game):
        """测试空计数"""
        count = await SpectatorManager.get_spectator_count(game_id=str(game.id))
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_get_spectator_count_with_spectators(self, game, test_user2):
        """测试有观战者时的计数"""
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        count = await SpectatorManager.get_spectator_count(game_id=str(game.id))
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_get_spectator_count_excludes_left(self, game, test_user2):
        """测试不计入已离开的观战者"""
        # 加入
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        # 离开
        await SpectatorManager.leave_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        count = await SpectatorManager.get_spectator_count(game_id=str(game.id))
        assert count == 0


class TestSpectatorManagerKick:
    """SpectatorManager.kick_spectator 测试"""
    
    @pytest.mark.asyncio
    async def test_kick_spectator_by_owner(self, game, test_user, test_user2):
        """测试游戏创建者踢出观战者"""
        # test_user2 加入观战
        join_result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        spectator_id = str(join_result['spectator'].id)
        
        # test_user（红方/创建者）踢出
        kick_result = await SpectatorManager.kick_spectator(
            game_id=str(game.id),
            spectator_id=spectator_id,
            operator_id=str(test_user.id)
        )
        
        assert kick_result['success'] is True
        assert '已将' in kick_result['message']
        
        # 验证状态已更新
        spectator = await Spectator.async_get(id=spectator_id)
        assert spectator.status == SpectatorStatus.KICKED
    
    @pytest.mark.asyncio
    async def test_kick_spectator_by_non_owner(self, game, test_user, test_user2):
        """测试非创建者踢出观战者（应该失败）"""
        # test_user2 加入观战
        join_result = await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        spectator_id = str(join_result['spectator'].id)
        
        # 创建第三个用户来尝试踢人
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='SecurePass123'
        )
        
        kick_result = await SpectatorManager.kick_spectator(
            game_id=str(game.id),
            spectator_id=spectator_id,
            operator_id=str(user3.id)
        )
        
        assert kick_result['success'] is False
        assert '无权限' in kick_result['error']
    
    @pytest.mark.asyncio
    async def test_kick_spectator_not_found(self, game, test_user):
        """测试踢出不存在的观战者"""
        fake_spectator_id = str(uuid.uuid4())
        
        kick_result = await SpectatorManager.kick_spectator(
            game_id=str(game.id),
            spectator_id=fake_spectator_id,
            operator_id=str(test_user.id)
        )
        
        assert kick_result['success'] is False
        assert '观战者不存在' in kick_result['error']


class TestSpectatorManagerCleanup:
    """SpectatorManager.cleanup_inactive_spectators 测试"""
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_spectators(self, game, test_user2):
        """测试清理不活跃观战者"""
        # 加入观战
        await SpectatorManager.join_spectate(
            game_id=str(game.id),
            user_id=str(test_user2.id)
        )
        
        # 模拟不活跃（更新 updated_at 为过去时间）
        from datetime import timedelta
        Spectator.objects.filter(
            game=game,
            user=test_user2
        ).update(
            updated_at=timezone.now() - timedelta(minutes=60)
        )
        
        # 清理
        count = await SpectatorManager.cleanup_inactive_spectators(
            game_id=str(game.id),
            timeout_minutes=30
        )
        
        assert count == 1
        
        # 验证状态已更新
        count_after = await SpectatorManager.get_spectator_count(game_id=str(game.id))
        assert count_after == 0


class TestSpectatorStatus:
    """SpectatorStatus 枚举测试"""
    
    def test_status_choices(self):
        """测试状态选择"""
        assert SpectatorStatus.WATCHING.value == 'watching'
        assert SpectatorStatus.LEFT.value == 'left'
        assert SpectatorStatus.KICKED.value == 'kicked'
    
    def test_status_labels(self):
        """测试状态标签"""
        assert SpectatorStatus.WATCHING.label == '观战中'
        assert SpectatorStatus.LEFT.label == '已离开'
        assert SpectatorStatus.KICKED.label == '被踢出'
