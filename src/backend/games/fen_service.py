"""
中国象棋 FEN (Forsyth-Edwards Notation) 格式服务

FEN 格式用于表示棋盘状态，格式为：
棋盘位置 回合 王车易位 吃过路兵 50 步规则 回合数

中国象棋 FEN 示例（初始局面）：
rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1

棋子代码：
- K/k: 帅/将
- A/a: 仕/士
- B/b: 相/象
- N/n: 马
- R/r: 车
- C/c: 炮
- P/p: 兵/卒
"""
from typing import Dict, List, Optional, Tuple


class FenService:
    """FEN 格式服务类"""
    
    # 初始 FEN
    INITIAL_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    
    # 棋子类型
    PIECE_TYPES = {'K', 'A', 'B', 'N', 'R', 'C', 'P'}
    
    @classmethod
    def get_initial_fen(cls) -> str:
        """获取初始局面 FEN"""
        return cls.INITIAL_FEN
    
    @classmethod
    def parse_fen(cls, fen: str) -> Dict:
        """
        解析 FEN 字符串为棋盘状态
        
        Args:
            fen: FEN 字符串
            
        Returns:
            棋盘状态字典，包含：
            - squares: Dict[str, str] 位置 -> 棋子
            - turn: str 当前回合 'w' 或 'b'
            - halfmove: int 50 步规则计数
            - fullmove: int 回合数
        """
        parts = fen.split()
        if len(parts) < 6:
            raise ValueError(f"Invalid FEN format: {fen}")
        
        board_str, turn, castling, en_passant, halfmove, fullmove = parts[:6]
        
        squares = cls._parse_board(board_str)
        
        return {
            "squares": squares,
            "turn": turn,
            "castling": castling,
            "en_passant": en_passant,
            "halfmove": int(halfmove),
            "fullmove": int(fullmove)
        }
    
    @classmethod
    def _parse_board(cls, board_str: str) -> Dict[str, str]:
        """
        解析棋盘部分
        
        FEN 从上到下表示第 10 行到第 1 行（黑方底线到红方底线）
        rows[0] = 第 10 行 (rank=10)
        rows[9] = 第 1 行 (rank=1)
        
        Args:
            board_str: FEN 的棋盘部分（斜杠分隔）
            
        Returns:
            位置 -> 棋子的字典
        """
        squares = {}
        rows = board_str.split('/')
        
        for row_idx, row in enumerate(rows):
            file_idx = 0
            for char in row:
                if char.isdigit():
                    # 数字表示空位数量
                    file_idx += int(char)
                else:
                    # 棋子
                    file_letter = chr(ord('a') + file_idx)
                    rank = 10 - row_idx  # row_idx=0 -> rank=10, row_idx=9 -> rank=1
                    position = f"{file_letter}{rank}"
                    squares[position] = char
                    file_idx += 1
        
        return squares
    
    @classmethod
    def generate_fen(cls, board: Dict) -> str:
        """
        从棋盘状态生成 FEN 字符串
        
        Args:
            board: 棋盘状态字典
            
        Returns:
            FEN 字符串
        """
        squares = board.get("squares", {})
        turn = board.get("turn", "w")
        halfmove = board.get("halfmove", 0)
        fullmove = board.get("fullmove", 1)
        
        # 生成棋盘部分
        board_rows = []
        for rank in range(10, 0, -1):
            row_str = ""
            empty_count = 0
            
            for file_idx in range(9):
                file_letter = chr(ord('a') + file_idx)
                position = f"{file_letter}{rank}"
                piece = squares.get(position)
                
                if piece:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += piece
                else:
                    empty_count += 1
            
            if empty_count > 0:
                row_str += str(empty_count)
            
            board_rows.append(row_str)
        
        board_str = "/".join(board_rows)
        
        return f"{board_str} {turn} - - {halfmove} {fullmove}"
    
    @classmethod
    def pos_to_coord(cls, position: str) -> Tuple[int, int]:
        """
        将代数坐标转换为棋盘坐标
        
        Args:
            position: 代数坐标（如 "e1", "e10"）
            
        Returns:
            (file, rank) 元组，file: 0-8, rank: 0-9
        """
        if len(position) < 2 or len(position) > 3:
            raise ValueError(f"Invalid position: {position}")
        
        file_letter = position[0].lower()
        rank_str = position[1:]
        
        file_idx = ord(file_letter) - ord('a')
        rank_idx = int(rank_str) - 1
        
        return (file_idx, rank_idx)
    
    @classmethod
    def coord_to_pos(cls, file: int, rank: int) -> str:
        """
        将棋盘坐标转换为代数坐标
        
        Args:
            file: 列索引 (0-8)
            rank: 行索引 (0-9)
            
        Returns:
            代数坐标字符串
        """
        if not (0 <= file <= 8):
            raise ValueError(f"Invalid file: {file}")
        if not (0 <= rank <= 9):
            raise ValueError(f"Invalid rank: {rank}")
        
        file_letter = chr(ord('a') + file)
        rank_num = rank + 1
        
        return f"{file_letter}{rank_num}"
    
    @classmethod
    def is_valid_position(cls, position: str) -> bool:
        """
        验证位置是否有效
        
        Args:
            position: 位置字符串
            
        Returns:
            是否有效
        """
        try:
            file_idx, rank_idx = cls.pos_to_coord(position)
            return 0 <= file_idx <= 8 and 0 <= rank_idx <= 9
        except (ValueError, IndexError):
            return False
    
    @classmethod
    def get_piece(cls, board: Dict, position: str) -> Optional[str]:
        """
        获取指定位置的棋子
        
        Args:
            board: 棋盘状态
            position: 位置
            
        Returns:
            棋子代码，空位或无效位置返回 None
        """
        squares = board.get("squares", {})
        return squares.get(position)
    
    @classmethod
    def is_red_piece(cls, piece: str) -> bool:
        """判断是否为红方棋子"""
        return piece is not None and piece.isupper()
    
    @classmethod
    def is_black_piece(cls, piece: str) -> bool:
        """判断是否为黑方棋子"""
        return piece is not None and piece.islower()
    
    @classmethod
    def get_piece_type(cls, piece: str) -> Optional[str]:
        """
        获取棋子类型
        
        Args:
            piece: 棋子代码
            
        Returns:
            棋子类型（大写），如 'K', 'A', 'B' 等
        """
        if not piece:
            return None
        return piece.upper()
    
    @classmethod
    def get_piece_color(cls, piece: str) -> Optional[str]:
        """
        获取棋子颜色
        
        Args:
            piece: 棋子代码
            
        Returns:
            'red' 或 'black'
        """
        if not piece:
            return None
        return 'red' if piece.isupper() else 'black'
