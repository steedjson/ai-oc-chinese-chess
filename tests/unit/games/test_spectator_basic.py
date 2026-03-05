"""
观战系统基础测试

测试核心功能
"""
import pytest
import asyncio
from django.utils import timezone
from games.models import Game, GameStatus
from games.spectator import Spectator, SpectatorStatus, SpectatorManager
from users.models import User


@pytest.mark.django_db
class TestSpectatorBasic:
    """基础功能测试"""
    
    def test_create_spectator(self):
        """测试创建观战记录"""
        user = User.objects.create_user(
            username=f'test_user_{timezone.now().timestamp()}',
            email=f'test_{timezone.now().timestamp()}@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            username=f'test_user2_{timezone.now().timestamp()}',
            email=f'test2_{timezone.now().timestamp()}@example.com',
            password='pass123'
        )
        
        game = Game.objects.create(
            game_type='online',
            status=GameStatus.PLAYING,
            red_player=user,
            black_player=user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            turn='w'
        )
        
        spectator = Spectator.objects.create(
            game=game,
            user=user2
        )
        
        assert spectator.game == game
        assert spectator.user == user2
        assert spectator.status == SpectatorStatus.WATCHING
    
    def test_spectator_manager_join_sync(self):
        """测试加入观战（同步版本）"""
        user = User.objects.create_user(
            username=f'test_user3_{timezone.now().timestamp()}',
            email=f'test3_{timezone.now().timestamp()}@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            username=f'test_user4_{timezone.now().timestamp()}',
            email=f'test4_{timezone.now().timestamp()}@example.com',
            password='pass123'
        )
        
        game = Game.objects.create(
            game_type='online',
            status=GameStatus.PLAYING,
            red_player=user,
            black_player=user2,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - 0 1',
            turn='w'
        )
        
        # 创建第三个用户来观战
        user3 = User.objects.create_user(
            username=f'test_user5_{timezone.now().timestamp()}',
            email=f'test5_{timezone.now().timestamp()}@example.com',
            password='pass123'
        )
        
        # 使用同步方法测试
        from games.spectator import SpectatorManager
        result = SpectatorManager.join_spectate_sync(
            game_id=str(game.id),
            user_id=str(user3.id)
        )
        
        assert result['success'] is True, f"Failed: {result.get('error')}"
        assert result['spectator'] is not None
    
    def test_spectator_status_choices(self):
        """测试状态选择"""
        assert SpectatorStatus.WATCHING.value == 'watching'
        assert SpectatorStatus.LEFT.value == 'left'
        assert SpectatorStatus.KICKED.value == 'kicked'
