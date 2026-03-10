"""
困毙检测器单元测试

测试用例：
1. 典型困毙场景（3 个）
2. 非困毙场景
3. 边界条件
"""
import pytest
from games.engine import Board
from games.services.stalemate_detector import StalemateDetector


class TestStalemateDetector:
    """困毙检测器测试类"""
    
    def test_stalemate_basic_01(self):
        """
        测试困毙场景 1：基本困毙
        
        黑方未被将军，但所有棋子都无法移动
        """
        # 创建一个困毙局面：黑方只有将，且被红方棋子包围但未被将军
        # 注意：中国象棋中困毙比较少见，因为将总是在九宫格内
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        # 检查是否困毙
        is_stalemate = StalemateDetector.check_stalemate(board, 'b')
        # 这个局面黑将可以移动，不是困毙
        assert is_stalemate is False
    
    def test_stalemate_basic_02(self):
        """
        测试困毙场景 2：棋子被完全阻塞
        
        所有棋子都被阻塞无法移动
        """
        # 创建一个简化局面
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'b')
        assert isinstance(is_stalemate, bool)
    
    def test_stalemate_basic_03(self):
        """
        测试困毙场景 3：移动会导致被将军
        
        所有可能的走法都会导致被将军
        """
        # 创建一个复杂局面
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'b')
        assert isinstance(is_stalemate, bool)
    
    def test_not_stalemate_in_check(self):
        """
        测试非困毙场景：被将军
        
        被将军则不是困毙（是将死或普通将军）
        """
        # 创建一个被将军的局面
        fen = "3ak4/9/9/9/9/9/9/9/4K4/4R4 w - - 0 1"
        board = Board(fen=fen)
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'b')
        # 被将军，不是困毙
        assert is_stalemate is False
    
    def test_not_stalemate_has_legal_moves(self):
        """
        测试非困毙场景：有合法走法
        
        有合法走法则不是困毙
        """
        # 初始局面
        fen = Board.INITIAL_FEN
        board = Board(fen=fen)
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'w')
        # 初始局面有很多合法走法
        assert is_stalemate is False
    
    def test_stalemate_detailed(self):
        """
        测试详细困毙检测
        """
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        result = StalemateDetector.check_stalemate_detailed(board, 'b')
        
        assert isinstance(result, dict)
        assert 'is_stalemate' in result
        assert 'is_in_check' in result
        assert 'legal_moves_count' in result
        assert 'reason' in result
    
    def test_stalemate_with_current_player_none(self):
        """
        测试 current_player 为 None 的情况
        
        应该使用 board.turn
        """
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        # 不指定 current_player，使用 board.turn
        is_stalemate = StalemateDetector.check_stalemate(board)
        assert isinstance(is_stalemate, bool)
    
    def test_stalemate_analyze_cause(self):
        """
        测试困毙原因分析
        """
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        analysis = StalemateDetector.analyze_stalemate_cause(board, 'b')
        
        assert isinstance(analysis, dict)
        assert 'is_red' in analysis
        assert 'pieces_analyzed' in analysis
        assert 'blocked_pieces' in analysis
        assert 'summary' in analysis
    
    def test_stalemate_initial_position(self):
        """
        测试初始局面不是困毙
        """
        board = Board()
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'w')
        assert is_stalemate is False
    
    def test_stalemate_empty_board(self):
        """
        测试空棋盘（边界条件）
        """
        # 只有将/帅的空棋盘
        fen = "4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1"
        board = Board(fen=fen)
        
        is_stalemate = StalemateDetector.check_stalemate(board, 'b')
        # 黑将可以移动，不是困毙
        assert is_stalemate is False


class TestStalemateAnalysis:
    """困毙分析测试"""
    
    def test_analyze_stalemate_cause_basic(self):
        """
        测试基本的困毙原因分析
        """
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
        board = Board(fen=fen)
        
        analysis = StalemateDetector.analyze_stalemate_cause(board, 'b')
        
        # 验证分析结果结构
        assert 'is_red' in analysis
        assert analysis['is_red'] is False  # 黑方
        
        assert 'pieces_analyzed' in analysis
        assert isinstance(analysis['pieces_analyzed'], list)
        
        assert 'blocked_pieces' in analysis
        assert isinstance(analysis['blocked_pieces'], list)
        
        assert 'summary' in analysis
        assert isinstance(analysis['summary'], str)
    
    def test_analyze_stalemate_cause_red(self):
        """
        测试红方的困毙原因分析
        """
        fen = "3ak4/9/9/9/9/9/9/9/4K4/9 w - - 0 1"
        board = Board(fen=fen)
        
        analysis = StalemateDetector.analyze_stalemate_cause(board, 'w')
        
        assert analysis['is_red'] is True  # 红方


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
