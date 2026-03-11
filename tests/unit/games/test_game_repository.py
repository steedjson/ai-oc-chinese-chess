"""
Game Repository 测试
测试游戏数据仓库核心功能：游戏创建、查询、更新、删除
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from games.models import Game, GameMove, GameStatus


# ==================== Game Model 测试 ====================

class TestGameModel:
    """Game 模型测试"""
    
    @pytest.mark.django_db
    def test_game_creation(self):
        """测试游戏创建"""
        game = Game.objects.create(
            game_type='online',
            status=GameStatus.PLAYING,
            fen_start='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
            fen_current='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR',
            turn='w'
        )
        
        assert game.id is not None
        assert game.game_type == 'online'
        assert game.status == GameStatus.PLAYING
        assert game.turn == 'w'
        assert game.move_count == 0
        assert game.is_rated is True
    
    @pytest.mark.django_db
    def test_game_str(self):
        """测试游戏字符串表示"""
        game = Game.objects.create(
            game_type='single',
            status=GameStatus.PENDING,
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        assert str(game) == f"Game {game.id} - pending"
    
    @pytest.mark.django_db
    def test_game_default_values(self):
        """测试游戏默认值"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        assert game.game_type == 'single'
        assert game.status == GameStatus.PENDING
        assert game.turn == 'w'
        assert game.move_count == 0
        assert game.is_rated is True
        assert game.time_control_base == 600
        assert game.time_control_increment == 0
    
    @pytest.mark.django_db
    def test_game_with_players(self, django_user_model):
        """测试带玩家的游戏"""
        red_player = django_user_model.objects.create_user(
            username='redplayer',
            email='red@example.com',
            password='pass123'
        )
        black_player = django_user_model.objects.create_user(
            username='blackplayer',
            email='black@example.com',
            password='pass123'
        )
        
        game = Game.objects.create(
            game_type='ranked',
            red_player=red_player,
            black_player=black_player,
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        assert game.red_player == red_player
        assert game.black_player == black_player
    
    @pytest.mark.django_db
    def test_game_finished(self, django_user_model):
        """测试已完成游戏"""
        red_player = django_user_model.objects.create_user(
            username='redplayer',
            email='red@example.com',
            password='pass123'
        )
        
        game = Game.objects.create(
            game_type='ranked',
            red_player=red_player,
            fen_start='initial_fen',
            fen_current='final_fen',
            status=GameStatus.RED_WIN,
            winner='red',
            win_reason='checkmate'
        )
        
        assert game.status == GameStatus.RED_WIN
        assert game.winner == 'red'
        assert game.win_reason == 'checkmate'
    
    @pytest.mark.django_db
    def test_game_ai_config(self):
        """测试 AI 配置"""
        game = Game.objects.create(
            game_type='single',
            fen_start='initial_fen',
            fen_current='initial_fen',
            ai_level=5,
            ai_side='black'
        )
        
        assert game.ai_level == 5
        assert game.ai_side == 'black'
    
    @pytest.mark.django_db
    def test_game_time_control(self):
        """测试时间控制"""
        game = Game.objects.create(
            game_type='online',
            fen_start='initial_fen',
            fen_current='initial_fen',
            time_control_base=900,
            time_control_increment=3,
            red_time_remaining=900,
            black_time_remaining=900
        )
        
        assert game.time_control_base == 900
        assert game.time_control_increment == 3
        assert game.red_time_remaining == 900
        assert game.black_time_remaining == 900
    
    @pytest.mark.django_db
    def test_game_move_count_update(self):
        """测试走棋数更新"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        assert game.move_count == 0
        
        # 模拟走棋
        game.move_count = 10
        game.save()
        
        game.refresh_from_db()
        assert game.move_count == 10


# ==================== GameMove Model 测试 ====================

class TestGameMoveModel:
    """GameMove 模型测试"""
    
    @pytest.mark.django_db
    def test_gamemove_creation(self):
        """测试走棋记录创建"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=1,
            piece='P',
            from_pos='e2',
            to_pos='e4'
        )
        
        assert move.id is not None
        assert move.game == game
        assert move.move_number == 1
        assert move.piece == 'P'
        assert move.from_pos == 'e2'
        assert move.to_pos == 'e4'
    
    @pytest.mark.django_db
    def test_gamemove_str(self):
        """测试走棋记录字符串表示"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=5,
            piece='C',
            from_pos='b2',
            to_pos='b5',
            notation='炮二进二'
        )
        
        assert str(move) == f"Move 5: C b2-b5"
    
    @pytest.mark.django_db
    def test_gamemove_with_capture(self):
        """测试吃子走棋记录"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=10,
            piece='R',
            from_pos='a1',
            to_pos='a5',
            captured='p',
            is_capture=True
        )
        
        assert move.captured == 'p'
        assert move.is_capture is True
    
    @pytest.mark.django_db
    def test_gamemove_with_check(self):
        """测试将军走棋记录"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=15,
            piece='C',
            from_pos='c2',
            to_pos='c7',
            is_check=True
        )
        
        assert move.is_check is True
    
    @pytest.mark.django_db
    def test_gamemove_notation(self):
        """测试走棋记谱"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=1,
            piece='P',
            from_pos='e2',
            to_pos='e4',
            notation='炮二平五',
            san='e2e4'
        )
        
        assert move.notation == '炮二平五'
        assert move.san == 'e2e4'
    
    @pytest.mark.django_db
    def test_gamemove_think_time(self):
        """测试思考时间记录"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        move = GameMove.objects.create(
            game=game,
            move_number=5,
            piece='P',
            from_pos='d2',
            to_pos='d4',
            think_time_ms=5000
        )
        
        assert move.think_time_ms == 5000


# ==================== Game QuerySet 测试 ====================

class TestGameQuerySet:
    """Game 查询集测试"""
    
    @pytest.mark.django_db
    def test_game_filter_by_status(self):
        """测试按状态过滤游戏"""
        Game.objects.create(fen_start='fen1', fen_current='fen1', status=GameStatus.PLAYING)
        Game.objects.create(fen_start='fen2', fen_current='fen2', status=GameStatus.RED_WIN)
        Game.objects.create(fen_start='fen3', fen_current='fen3', status=GameStatus.DRAW)
        
        playing_games = Game.objects.filter(status=GameStatus.PLAYING)
        assert playing_games.count() == 1
        
        finished_games = Game.objects.filter(status__in=[GameStatus.RED_WIN, GameStatus.BLACK_WIN, GameStatus.DRAW])
        assert finished_games.count() == 2
    
    @pytest.mark.django_db
    def test_game_filter_by_player(self, django_user_model):
        """测试按玩家过滤游戏"""
        player = django_user_model.objects.create_user(
            username='testplayer',
            email='test@example.com',
            password='pass123'
        )
        
        Game.objects.create(fen_start='fen1', fen_current='fen1', red_player=player)
        Game.objects.create(fen_start='fen2', fen_current='fen2', black_player=player)
        Game.objects.create(fen_start='fen3', fen_current='fen3')  # 玩家不是该用户
        
        player_games = Game.objects.filter(
            models.Q(red_player=player) | models.Q(black_player=player)
        )
        assert player_games.count() == 2
    
    @pytest.mark.django_db
    def test_game_filter_by_game_type(self):
        """测试按游戏类型过滤"""
        Game.objects.create(fen_start='fen1', fen_current='fen1', game_type='single')
        Game.objects.create(fen_start='fen2', fen_current='fen2', game_type='online')
        Game.objects.create(fen_start='fen3', fen_current='fen3', game_type='friend')
        
        single_games = Game.objects.filter(game_type='single')
        assert single_games.count() == 1
        
        online_games = Game.objects.filter(game_type='online')
        assert online_games.count() == 1
    
    @pytest.mark.django_db
    def test_game_order_by_created_at(self):
        """测试按创建时间排序"""
        game1 = Game.objects.create(fen_start='fen1', fen_current='fen1')
        game2 = Game.objects.create(fen_start='fen2', fen_current='fen2')
        game3 = Game.objects.create(fen_start='fen3', fen_current='fen3')
        
        games = Game.objects.order_by('-created_at')
        game_ids = [g.id for g in games]
        
        # 最新的应该在前
        assert game_ids[0] == game3.id
    
    @pytest.mark.django_db
    def test_game_moves_relationship(self):
        """测试游戏与走棋记录的关系"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        GameMove.objects.create(game=game, move_number=1, piece='P', from_pos='e2', to_pos='e4')
        GameMove.objects.create(game=game, move_number=2, piece='p', from_pos='e7', to_pos='e5')
        GameMove.objects.create(game=game, move_number=3, piece='N', from_pos='b8', to_pos='c6')
        
        assert game.moves.count() == 3
        
        first_move = game.moves.filter(move_number=1).first()
        assert first_move is not None
        assert first_move.from_pos == 'e2'


# ==================== Game Repository Service 测试 ====================

class TestGameRepository:
    """游戏仓库服务测试"""
    
    @pytest.mark.django_db
    def test_create_game_success(self):
        """测试成功创建游戏"""
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        game = repo.create_game(
            game_type='online',
            fen_start='initial_fen',
            red_player_id=None,
            black_player_id=None
        )
        
        assert game is not None
        assert game.game_type == 'online'
        assert game.status == GameStatus.PENDING
    
    @pytest.mark.django_db
    def test_get_game_by_id_success(self):
        """测试成功获取游戏"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        retrieved_game = repo.get_game_by_id(str(game.id))
        
        assert retrieved_game is not None
        assert retrieved_game.id == game.id
    
    @pytest.mark.django_db
    def test_get_game_by_id_not_found(self):
        """测试游戏不存在"""
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        game = repo.get_game_by_id('nonexistent-id')
        
        assert game is None
    
    @pytest.mark.django_db
    def test_update_game_status(self):
        """测试更新游戏状态"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen',
            status=GameStatus.PENDING
        )
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        updated = repo.update_game_status(str(game.id), GameStatus.PLAYING)
        
        assert updated is True
        game.refresh_from_db()
        assert game.status == GameStatus.PLAYING
    
    @pytest.mark.django_db
    def test_update_fen(self):
        """测试更新 FEN"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        updated = repo.update_fen(str(game.id), 'new_fen')
        
        assert updated is True
        game.refresh_from_db()
        assert game.fen_current == 'new_fen'
    
    @pytest.mark.django_db
    def test_finish_game(self):
        """测试结束游戏"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen',
            status=GameStatus.PLAYING
        )
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        updated = repo.finish_game(str(game.id), 'red', 'checkmate')
        
        assert updated is True
        game.refresh_from_db()
        assert game.status == GameStatus.RED_WIN
        assert game.winner == 'red'
        assert game.win_reason == 'checkmate'
        assert game.finished_at is not None
    
    @pytest.mark.django_db
    def test_get_player_games(self, django_user_model):
        """测试获取玩家游戏"""
        player = django_user_model.objects.create_user(
            username='testplayer',
            email='test@example.com',
            password='pass123'
        )
        
        Game.objects.create(fen_start='fen1', fen_current='fen1', red_player=player)
        Game.objects.create(fen_start='fen2', fen_current='fen2', black_player=player)
        Game.objects.create(fen_start='fen3', fen_current='fen3')
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        games = repo.get_player_games(str(player.id))
        
        assert len(games) == 2
    
    @pytest.mark.django_db
    def test_get_active_games(self):
        """测试获取活跃游戏"""
        Game.objects.create(fen_start='fen1', fen_current='fen1', status=GameStatus.PLAYING)
        Game.objects.create(fen_start='fen2', fen_current='fen2', status=GameStatus.PLAYING)
        Game.objects.create(fen_start='fen3', fen_current='fen3', status=GameStatus.RED_WIN)
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        games = repo.get_active_games()
        
        assert len(games) == 2
        for game in games:
            assert game.status == GameStatus.PLAYING
    
    @pytest.mark.django_db
    def test_delete_game(self):
        """测试删除游戏"""
        game = Game.objects.create(
            fen_start='initial_fen',
            fen_current='initial_fen'
        )
        game_id = str(game.id)
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        deleted = repo.delete_game(game_id)
        
        assert deleted is True
        assert Game.objects.filter(id=game_id).count() == 0
    
    @pytest.mark.django_db
    def test_get_recent_games(self):
        """测试获取最近游戏"""
        for i in range(10):
            Game.objects.create(
                fen_start=f'fen{i}',
                fen_current=f'fen{i}',
                status=GameStatus.RED_WIN
            )
        
        from games.services.game_repository import GameRepository
        
        repo = GameRepository()
        games = repo.get_recent_games(limit=5)
        
        assert len(games) == 5


# 导入 models 用于测试
from django.db import models


# 运行测试
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
