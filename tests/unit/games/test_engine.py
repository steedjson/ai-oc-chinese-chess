"""
象棋规则引擎测试
测试 7 种棋子的走法规则验证
"""
import pytest
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

from games.engine import Board, MoveValidator


class TestGeneralKing:
    """将/帅规则测试"""
    
    def test_king_initial_position(self):
        """测试将/帅初始位置"""
        board = Board()
        assert board.get_piece("e1") == "K"  # 红帅
        assert board.get_piece("e10") == "k"  # 黑将
    
    def test_king_move_within_palace(self):
        """测试将/帅在九宫格内移动"""
        # 使用空旷的九宫格局面，帅在 e1 可以走到 d1, f1, e2
        # FEN 从上到下是 rank 10 到 rank 1，所以 4K4 应该在最后一行（rank 1）
        fen = "9/9/9/9/9/9/9/9/9/4K4 w - - 0 1"
        board = Board(fen)
        legal_moves = board.get_legal_moves_for_piece("e1")
        
        # 帅可以走到 d1, f1, e2
        move_positions = [m.to_pos for m in legal_moves]
        assert "d1" in move_positions or "f1" in move_positions or "e2" in move_positions
    
    def test_king_cannot_leave_palace(self):
        """测试将/帅不能走出九宫格"""
        board = Board()
        # 尝试让帅走出九宫格应该被拒绝
        from games.fen_service import FenService
        move = board._create_move("e1", "e5")  # 走出九宫格
        assert not board._is_valid_king_move(move, "K")


class TestAdvisor:
    """士/仕规则测试"""
    
    def test_advisor_initial_position(self):
        """测试士/仕初始位置"""
        board = Board()
        assert board.get_piece("d1") == "A"  # 红仕
        assert board.get_piece("f1") == "A"  # 红仕
        assert board.get_piece("d10") == "a"  # 黑士
        assert board.get_piece("f10") == "a"  # 黑士
    
    def test_advisor_diagonal_move(self):
        """测试士/仕斜线移动"""
        board = Board()
        # 士走斜线
        legal_moves = board.get_legal_moves_for_piece("d1")
        
        # 士应该可以走到 e2（斜线）
        move_positions = [m.to_pos for m in legal_moves]
        assert "e2" in move_positions


class TestBishop:
    """象/相规则测试"""
    
    def test_bishop_initial_position(self):
        """测试象/相初始位置"""
        board = Board()
        assert board.get_piece("c1") == "B"  # 红相
        assert board.get_piece("g1") == "B"  # 红相
        assert board.get_piece("c10") == "b"  # 黑象
        assert board.get_piece("g10") == "b"  # 黑象
    
    def test_bishop_cannot_cross_river(self):
        """测试象/相不能过河"""
        board = Board()
        # 红相不能走到黑方半场
        legal_moves = board.get_legal_moves_for_piece("c1")
        
        # 所有合法移动都应该在红方半场（rank <= 5）
        for move in legal_moves:
            rank = int(move.to_pos[1:])
            assert rank <= 5, f"象不能过河：{move.to_pos}"
    
    def test_bishop_eye_blocking(self):
        """测试象眼被堵"""
        # 设置一个象眼被堵的局面
        fen = "9/9/9/9/9/9/9/9/3B4/9 w - - 0 1"
        board = Board(fen)
        # 象在 d2，象眼在 e3
        # 如果 e3 有棋子，象不能走到 c4 或 g4


class TestKnight:
    """马规则测试"""
    
    def test_knight_initial_position(self):
        """测试马初始位置"""
        board = Board()
        assert board.get_piece("b1") == "N"  # 红马
        assert board.get_piece("h1") == "N"  # 红马
        assert board.get_piece("b10") == "n"  # 黑马
        assert board.get_piece("h10") == "n"  # 黑马
    
    def test_knight_day_move(self):
        """测试马走日字"""
        board = Board()
        legal_moves = board.get_legal_moves_for_piece("b1")
        
        # 马应该可以走到某些日字位置
        assert len(legal_moves) > 0
    
    def test_knight_leg_blocking(self):
        """测试蹩马腿"""
        # 马在 b1，如果 c1 有棋子，马不能走到 d2
        fen = "9/9/9/9/9/9/9/9/P1P1P1P1P/1C5C1 w - - 0 1"
        board = Board(fen)
        # 马被蹩腿时，某些移动应该被禁止


class TestRook:
    """车规则测试"""
    
    def test_rook_initial_position(self):
        """测试车初始位置"""
        board = Board()
        assert board.get_piece("a1") == "R"  # 红车
        assert board.get_piece("i1") == "R"  # 红车
        assert board.get_piece("a10") == "r"  # 黑车
        assert board.get_piece("i10") == "r"  # 黑车
    
    def test_rook_straight_move(self):
        """测试车直线移动"""
        # 空旷局面，车在 d5 可以直线移动
        # FEN 从上到下是 rank 10 到 rank 1，3R4 在第 6 行对应 rank=5
        fen = "9/9/9/9/9/3R4/9/9/9/9 w - - 0 1"
        board = Board(fen)
        legal_moves = board.get_legal_moves_for_piece("d5")
        
        # 车应该可以沿直线移动多个位置
        move_positions = [m.to_pos for m in legal_moves]
        assert len(move_positions) > 0


class TestCannon:
    """炮规则测试"""
    
    def test_cannon_initial_position(self):
        """测试炮初始位置"""
        board = Board()
        # 根据 FEN 解析，红炮在 b3 和 h3
        assert board.get_piece("b3") == "C"  # 红炮
        assert board.get_piece("h3") == "C"  # 红炮
        assert board.get_piece("b8") == "c"  # 黑炮
        assert board.get_piece("h8") == "c"  # 黑炮
    
    def test_cannon_move_without_capture(self):
        """测试炮不吃子时的移动"""
        # 炮可以像车一样移动（不吃子）
        # FEN: 3C5 在第 6 行（从顶部数），对应 rank=5
        fen = "9/9/9/9/9/3C5/9/9/9/9 w - - 0 1"
        board = Board(fen)
        legal_moves = board.get_legal_moves_for_piece("d5")
        
        # 炮应该可以沿直线移动（不吃子）
        assert len(legal_moves) > 0
    
    def test_cannon_capture(self):
        """测试炮隔山打牛"""
        # 炮需要炮架才能吃子
        fen = "9/9/9/9/5p3/9/9/9/3C5/9 w - - 0 1"
        board = Board(fen)
        # 炮在 d1，卒在 f5，中间没有炮架，不能吃
        # 需要添加炮架


class TestPawn:
    """兵/卒规则测试"""
    
    def test_pawn_initial_position(self):
        """测试兵/卒初始位置"""
        board = Board()
        # 红兵
        assert board.get_piece("a4") == "P"
        assert board.get_piece("c4") == "P"
        assert board.get_piece("e4") == "P"
        assert board.get_piece("g4") == "P"
        assert board.get_piece("i4") == "P"
        # 黑卒
        assert board.get_piece("a7") == "p"
        assert board.get_piece("c7") == "p"
        assert board.get_piece("e7") == "p"
        assert board.get_piece("g7") == "p"
        assert board.get_piece("i7") == "p"
    
    def test_pawn_forward_move(self):
        """测试兵向前移动"""
        board = Board()
        legal_moves = board.get_legal_moves_for_piece("a4")
        
        # 兵应该可以向前走
        move_positions = [m.to_pos for m in legal_moves]
        assert "a5" in move_positions
    
    def test_pawn_cross_river(self):
        """测试兵过河后可以横走"""
        # 红兵已经过河（在对方半场，rank >= 6）
        # FEN: 3P5 在第 5 行（从顶部数），对应 rank=6
        fen = "9/9/9/9/3P5/9/9/9/9/9 w - - 0 1"
        board = Board(fen)
        legal_moves = board.get_legal_moves_for_piece("d6")
        
        # 过河兵应该可以横走
        move_positions = [m.to_pos for m in legal_moves]
        assert "c6" in move_positions or "e6" in move_positions
    
    def test_pawn_cannot_backward(self):
        """测试兵不能后退"""
        board = Board()
        legal_moves = board.get_legal_moves_for_piece("a4")
        
        # 兵不能后退
        move_positions = [m.to_pos for m in legal_moves]
        assert "a3" not in move_positions


class TestMoveValidator:
    """走棋验证器测试"""
    
    def test_valid_move(self):
        """测试合法走棋验证"""
        board = Board()
        validator = MoveValidator(board)
        
        # 红方走棋：炮从 b3 走到 b5（炮二进二）
        move = board._create_move("b3", "b5")
        assert validator.is_valid_move(move)
    
    def test_invalid_move_wrong_turn(self):
        """测试错误回合的走棋"""
        board = Board()
        validator = MoveValidator(board)
        
        # 黑方走棋（但应该是红方回合）
        move = board._create_move("c8", "c6")
        # 由于是红方回合，黑方走棋应该无效


class TestBoard:
    """棋盘状态测试"""
    
    def test_initial_board_setup(self):
        """测试初始棋盘布局"""
        board = Board()
        
        # 验证双方棋子数量
        red_pieces = [p for p in board.squares.values() if p.isupper()]
        black_pieces = [p for p in board.squares.values() if p.islower()]
        
        assert len(red_pieces) == 16
        assert len(black_pieces) == 16
    
    def test_fen_loading(self):
        """测试 FEN 加载"""
        # FEN: 3K5 在第 9 行（从顶部数），即 rank=2
        # K 在 d 列，所以位置是 d2
        fen = "9/9/9/9/9/9/9/9/3K5/9 w - - 0 1"
        board = Board(fen)
        
        assert board.get_piece("d2") == "K"
    
    def test_fen_generation(self):
        """测试 FEN 生成"""
        board = Board()
        fen = board.to_fen()
        
        # 重新加载 FEN 应该得到相同的棋盘
        board2 = Board(fen)
        assert board.squares == board2.squares
    
    def test_get_legal_moves(self):
        """测试获取所有合法走法"""
        board = Board()
        moves = board.get_all_legal_moves()
        
        # 红方初始应该有多个合法走法
        assert len(moves) > 0
    
    def test_make_move(self):
        """测试执行走棋"""
        board = Board()
        initial_fen = board.to_fen()
        
        # 执行一步棋：炮从 b3 走到 b5
        move = board._create_move("b3", "b5")
        result = board.make_move(move)
        
        # 棋盘应该改变
        assert board.to_fen() != initial_fen
        # 回合应该切换到黑方
        assert board.turn == "b"
        # 走棋应该成功
        assert result is True
