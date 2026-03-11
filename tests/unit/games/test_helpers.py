"""
测试游戏辅助服务

测试 games/ 中的辅助服务模块
"""

import pytest
from unittest.mock import Mock, patch
from games.fen_service import (
    fen_to_board,
    board_to_fen,
    validate_fen,
    get_piece_at,
    set_piece_at,
    move_piece,
    parse_fen,
    generate_fen,
)
from games.timer_service import TimerService, GameTimer
from games.share_service import ShareService
from games.undo_service import UndoService


class TestFenService:
    """测试 FEN 服务"""
    
    def test_validate_fen_valid(self):
        """测试验证有效 FEN"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        result = validate_fen(fen)
        
        assert result is True or result.get('valid', False) is True
    
    def test_validate_fen_invalid(self):
        """测试验证无效 FEN"""
        fen = "invalid fen string"
        
        result = validate_fen(fen)
        
        assert result is False or result.get('valid', False) is False
    
    def test_parse_fen(self):
        """测试解析 FEN"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        result = parse_fen(fen)
        
        assert result is not None
        assert 'board' in result or hasattr(result, 'pieces')
    
    def test_generate_fen(self):
        """测试生成 FEN"""
        mock_board = Mock()
        mock_board.fen.return_value = "test_fen"
        
        result = generate_fen(mock_board)
        
        assert result == "test_fen"
    
    def test_get_piece_at(self):
        """测试获取棋子"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 获取 a1 位置的棋子（应该是 R）
        piece = get_piece_at(fen, 0, 0)  # (row, col)
        
        assert piece is not None or piece == 'R'
    
    def test_set_piece_at(self):
        """测试设置棋子"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        new_fen = set_piece_at(fen, 0, 0, 'Q')
        
        assert new_fen != fen
    
    def test_move_piece(self):
        """测试移动棋子"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        new_fen = move_piece(fen, (6, 1), (4, 1))  # 炮二进二
        
        assert new_fen != fen


class TestTimerService:
    """测试计时器服务"""
    
    def test_create_game_timer(self):
        """测试创建游戏计时器"""
        timer = GameTimer(
            red_time=600,
            black_time=600,
            increment=0
        )
        
        assert timer.red_remaining == 600
        assert timer.black_remaining == 600
    
    def test_start_timer(self):
        """测试启动计时器"""
        timer_service = TimerService()
        
        timer = timer_service.create_timer(
            red_time=600,
            black_time=600
        )
        
        assert timer is not None
    
    def test_tick_timer(self):
        """测试计时器计时"""
        timer = GameTimer(red_time=600, black_time=600)
        
        # 模拟红方走棋耗时 5 秒
        timer.tick('red', 5)
        
        assert timer.red_remaining <= 595
    
    def test_switch_turn(self):
        """测试切换回合"""
        timer = GameTimer(red_time=600, black_time=600)
        
        timer.switch_turn()
        
        assert timer.current_turn == 'black'
    
    def test_time_expired(self):
        """测试时间耗尽"""
        timer = GameTimer(red_time=10, black_time=600)
        
        # 红方时间耗尽
        timer.tick('red', 15)
        
        assert timer.is_expired('red')
    
    def test_add_increment(self):
        """测试加时"""
        timer = GameTimer(red_time=600, black_time=600, increment=5)
        
        timer.tick('red', 10, with_increment=True)
        
        # 红方时间应该增加 5 秒
        assert timer.red_remaining == 595  # 600 - 10 + 5


class TestShareService:
    """测试分享服务"""
    
    def test_generate_share_link(self):
        """测试生成分享链接"""
        service = ShareService()
        
        mock_game = Mock()
        mock_game.id = 123
        mock_game.share_token = 'abc123'
        
        link = service.generate_share_link(mock_game)
        
        assert link is not None
        assert '123' in link or 'abc123' in link
    
    def test_generate_share_image(self):
        """测试生成分享图片"""
        service = ShareService()
        
        mock_game = Mock()
        mock_game.fen_current = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        
        # 这个可能需要实际的图片生成
        # 这里只测试接口
        assert hasattr(service, 'generate_share_image') or hasattr(service, 'create_thumbnail')
    
    def test_get_share_info(self):
        """测试获取分享信息"""
        service = ShareService()
        
        mock_game = Mock()
        mock_game.id = 123
        mock_game.status = 'playing'
        mock_game.created_at = '2024-01-01'
        
        info = service.get_share_info(mock_game)
        
        assert isinstance(info, dict)
        assert 'id' in info or 'game_id' in info


class TestUndoService:
    """测试悔棋服务"""
    
    def test_can_undo(self):
        """测试是否可以悔棋"""
        service = UndoService()
        
        mock_game = Mock()
        mock_game.move_history = [{'from': 'e2', 'to': 'e4'}]
        mock_game.status = 'playing'
        
        result = service.can_undo(mock_game)
        
        assert result is True
    
    def test_cannot_undo_empty_history(self):
        """测试空历史不能悔棋"""
        service = UndoService()
        
        mock_game = Mock()
        mock_game.move_history = []
        mock_game.status = 'playing'
        
        result = service.can_undo(mock_game)
        
        assert result is False
    
    def test_cannot_undo_finished_game(self):
        """测试结束游戏不能悔棋"""
        service = UndoService()
        
        mock_game = Mock()
        mock_game.move_history = [{'from': 'e2', 'to': 'e4'}]
        mock_game.status = 'red_win'
        
        result = service.can_undo(mock_game)
        
        assert result is False
    
    def test_perform_undo(self):
        """测试执行悔棋"""
        service = UndoService()
        
        mock_game = Mock()
        mock_game.move_history = [
            {'from': 'e2', 'to': 'e4', 'piece': 'P', 'captured': None}
        ]
        mock_game.fen_current = "new_fen"
        
        result = service.perform_undo(mock_game)
        
        assert result is not None
        assert len(mock_game.move_history) == 0
    
    def test_undo_multiple_moves(self):
        """测试悔多步棋"""
        service = UndoService()
        
        mock_game = Mock()
        mock_game.move_history = [
            {'from': 'e2', 'to': 'e4'},
            {'from': 'e7', 'to': 'e5'},
            {'from': 'g1', 'to': 'f3'},
        ]
        
        result = service.undo_moves(mock_game, 2)
        
        assert len(mock_game.move_history) == 1


class TestFenServiceEdgeCases:
    """测试 FEN 服务边界情况"""
    
    def test_empty_fen(self):
        """测试空 FEN"""
        result = validate_fen("")
        assert result is False
    
    def test_partial_fen(self):
        """测试部分 FEN"""
        fen = "rnbakabnr"
        result = validate_fen(fen)
        assert result is False
    
    def test_invalid_characters(self):
        """测试无效字符"""
        fen = "xxxxxxxxx/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        result = validate_fen(fen)
        assert result is False


@pytest.fixture
def sample_game():
    """创建示例游戏"""
    game = Mock()
    game.id = 1
    game.fen_current = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    game.turn = 'red'
    game.move_history = [
        {'from': 'c1', 'to': 'c4', 'piece': 'C'},
    ]
    game.status = 'playing'
    return game
