"""
FEN 服务测试
测试 FEN 格式的编码/解码功能
"""
import pytest
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent.parent / 'src' / 'backend'
sys.path.insert(0, str(backend_dir))

from games.fen_service import FenService


class TestFenService:
    """FEN 服务测试类"""
    
    def test_initial_fen(self):
        """测试初始局面 FEN"""
        fen = FenService.get_initial_fen()
        assert fen == "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    
    def test_parse_initial_fen(self):
        """测试解析初始 FEN"""
        fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        board = FenService.parse_fen(fen)
        
        assert board["turn"] == "w"
        assert len(board["squares"]) == 32  # 初始 32 个棋子
        
        # 验证黑将位置
        assert board["squares"]["e10"] == "k"
        # 验证红帅位置
        assert board["squares"]["e1"] == "K"
    
    def test_generate_fen(self):
        """测试从棋盘状态生成 FEN"""
        board = {
            "squares": {"e1": "K", "e10": "k"},
            "turn": "w",
            "halfmove": 0,
            "fullmove": 1
        }
        fen = FenService.generate_fen(board)
        
        assert "K" in fen
        assert "k" in fen
        assert " w " in fen or " w-" in fen
    
    def test_position_to_coordinate(self):
        """测试代数坐标转棋盘位置"""
        # 红方底线
        assert FenService.pos_to_coord("e1") == (4, 0)
        # 黑方底线
        assert FenService.pos_to_coord("e10") == (4, 9)
        # 边界检查
        assert FenService.pos_to_coord("a1") == (0, 0)
        assert FenService.pos_to_coord("i10") == (8, 9)
    
    def test_coordinate_to_position(self):
        """测试棋盘位置转代数坐标"""
        assert FenService.coord_to_pos(4, 0) == "e1"
        assert FenService.coord_to_pos(4, 9) == "e10"
        assert FenService.coord_to_pos(0, 0) == "a1"
        assert FenService.coord_to_pos(8, 9) == "i10"
    
    def test_is_valid_position(self):
        """测试位置有效性验证"""
        # 有效位置
        assert FenService.is_valid_position("e1") is True
        assert FenService.is_valid_position("a1") is True
        assert FenService.is_valid_position("i10") is True
        
        # 无效位置
        assert FenService.is_valid_position("j1") is False  # 超出列
        assert FenService.is_valid_position("a0") is False  # 超出行
        assert FenService.is_valid_position("a11") is False  # 超出行
        assert FenService.is_valid_position("e") is False  # 格式错误
    
    def test_get_piece_at_position(self):
        """测试获取指定位置的棋子"""
        fen = FenService.get_initial_fen()
        board = FenService.parse_fen(fen)
        
        # 黑方车
        assert board["squares"].get("a10") == "r"
        assert board["squares"].get("i10") == "r"
        # 红方车
        assert board["squares"].get("a1") == "R"
        assert board["squares"].get("i1") == "R"
        # 空位置
        assert board["squares"].get("e5") is None
    
    def test_fen_round_trip(self):
        """测试 FEN 解析和生成的往返一致性"""
        original_fen = FenService.get_initial_fen()
        board = FenService.parse_fen(original_fen)
        generated_fen = FenService.generate_fen(board)
        
        # 由于空格处理可能不同，只比较关键部分
        assert original_fen.split()[:2] == generated_fen.split()[:2]
    
    def test_is_red_piece(self):
        """测试红方棋子判断"""
        assert FenService.is_red_piece("K") is True
        assert FenService.is_red_piece("R") is True
        assert FenService.is_red_piece("P") is True
        assert FenService.is_red_piece("k") is False
        assert FenService.is_red_piece(None) is False
    
    def test_is_black_piece(self):
        """测试黑方棋子判断"""
        assert FenService.is_black_piece("k") is True
        assert FenService.is_black_piece("r") is True
        assert FenService.is_black_piece("p") is True
        assert FenService.is_black_piece("K") is False
        assert FenService.is_black_piece(None) is False
    
    def test_get_piece_type(self):
        """测试获取棋子类型"""
        assert FenService.get_piece_type("K") == "K"
        assert FenService.get_piece_type("k") == "K"
        assert FenService.get_piece_type("R") == "R"
        assert FenService.get_piece_type("r") == "R"
        assert FenService.get_piece_type(None) is None
    
    def test_get_piece_color(self):
        """测试获取棋子颜色"""
        assert FenService.get_piece_color("K") == "red"
        assert FenService.get_piece_color("R") == "red"
        assert FenService.get_piece_color("k") == "black"
        assert FenService.get_piece_color("r") == "black"
        assert FenService.get_piece_color(None) is None
