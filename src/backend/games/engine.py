"""
中国象棋规则引擎

实现 7 种棋子的走法规则验证：
- K/k: 帅/将 - 九宫格内直线移动
- A/a: 仕/士 - 九宫格内斜线移动
- B/b: 相/象 - 田字移动，不能过河，有象眼
- N/n: 马 - 日字移动，有蹩马腿
- R/r: 车 - 直线移动
- C/c: 炮 - 直线移动，吃子需炮架
- P/p: 兵/卒 - 过河前只能前进，过河后可横走
"""
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from games.fen_service import FenService


@dataclass
class Move:
    """走棋数据类"""
    from_pos: str
    to_pos: str
    piece: str
    captured: Optional[str] = None
    is_check: bool = False
    is_capture: bool = False
    
    def __post_init__(self):
        """验证走棋"""
        if not FenService.is_valid_position(self.from_pos):
            raise ValueError(f"Invalid from position: {self.from_pos}")
        if not FenService.is_valid_position(self.to_pos):
            raise ValueError(f"Invalid to position: {self.to_pos}")


class Board:
    """象棋棋盘类"""
    
    # 初始 FEN
    INITIAL_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    
    def __init__(self, fen: str = None):
        """
        初始化棋盘
        
        Args:
            fen: FEN 字符串，None 则使用初始局面
        """
        self.squares: Dict[str, str] = {}
        self.turn: str = 'w'  # 'w' 红方，'b' 黑方
        self.halfmove: int = 0
        self.fullmove: int = 1
        
        if fen is None:
            fen = self.INITIAL_FEN
        
        self.load_fen(fen)
    
    def load_fen(self, fen: str) -> None:
        """
        加载 FEN 字符串
        
        Args:
            fen: FEN 字符串
        """
        board_data = FenService.parse_fen(fen)
        self.squares = board_data["squares"]
        self.turn = board_data["turn"]
        self.halfmove = board_data["halfmove"]
        self.fullmove = board_data["fullmove"]
    
    def to_fen(self) -> str:
        """
        生成 FEN 字符串
        
        Returns:
            FEN 字符串
        """
        board_data = {
            "squares": self.squares,
            "turn": self.turn,
            "halfmove": self.halfmove,
            "fullmove": self.fullmove
        }
        return FenService.generate_fen(board_data)
    
    def get_piece(self, position: str) -> Optional[str]:
        """
        获取指定位置的棋子
        
        Args:
            position: 位置
            
        Returns:
            棋子代码，空位或无效位置返回 None
        """
        return self.squares.get(position)
    
    def _create_move(self, from_pos: str, to_pos: str) -> Optional[Move]:
        """
        创建走棋对象
        
        Args:
            from_pos: 起始位置
            to_pos: 目标位置
            
        Returns:
            Move 对象，无效位置返回 None
        """
        piece = self.get_piece(from_pos)
        if not piece:
            return None
        
        captured = self.get_piece(to_pos)
        
        return Move(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=piece,
            captured=captured,
            is_capture=captured is not None
        )
    
    def get_legal_moves_for_piece(self, position: str) -> List[Move]:
        """
        获取指定位置棋子的所有合法走法
        
        Args:
            position: 棋子位置
            
        Returns:
            合法走法列表
        """
        piece = self.get_piece(position)
        if not piece:
            return []
        
        piece_type = piece.upper()
        
        # 获取棋子的所有可能走法
        pseudo_legal_moves = self._get_piece_moves(position, piece)
        
        # 过滤掉会导致己方被将军的走法
        legal_moves = []
        for move in pseudo_legal_moves:
            if self._is_legal_move(move):
                legal_moves.append(move)
        
        return legal_moves
    
    def get_all_legal_moves(self) -> List[Move]:
        """
        获取当前回合方的所有合法走法
        
        Returns:
            合法走法列表
        """
        legal_moves = []
        
        # 复制字典避免迭代时修改
        squares_copy = dict(self.squares)
        for position, piece in squares_copy.items():
            # 只处理当前回合方的棋子
            is_red = piece.isupper()
            if (self.turn == 'w' and is_red) or (self.turn == 'b' and not is_red):
                piece_moves = self.get_legal_moves_for_piece(position)
                legal_moves.extend(piece_moves)
        
        return legal_moves
    
    def _get_piece_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取棋子的所有可能走法（不考虑是否被将军）
        
        Args:
            position: 棋子位置
            piece: 棋子代码
            
        Returns:
            走法列表
        """
        piece_type = piece.upper()
        
        if piece_type == 'K':
            return self._get_king_moves(position, piece)
        elif piece_type == 'A':
            return self._get_advisor_moves(position, piece)
        elif piece_type == 'B':
            return self._get_bishop_moves(position, piece)
        elif piece_type == 'N':
            return self._get_knight_moves(position, piece)
        elif piece_type == 'R':
            return self._get_rook_moves(position, piece)
        elif piece_type == 'C':
            return self._get_cannon_moves(position, piece)
        elif piece_type == 'P':
            return self._get_pawn_moves(position, piece)
        
        return []
    
    def _get_king_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取将/帅的走法
        
        规则：
        - 在九宫格内移动
        - 每次一步，直线移动
        - 红帅：d1-f1, d2-f2, e1-e3（1-3 行，4-6 列）
        - 黑将：d10-f10, d9-f9, e8-e10（8-10 行，4-6 列）
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        is_red = piece.isupper()
        
        # 九宫格范围（基于 0 的索引）
        # 红方：1-3 行 → rank_idx 0-2
        # 黑方：8-10 行 → rank_idx 7-9
        if is_red:
            min_rank, max_rank = 0, 2  # 红方 1-3 行
        else:
            min_rank, max_rank = 7, 9  # 黑方 8-10 行
        
        min_file, max_file = 3, 5  # d-f 列（4-6 列）
        
        # 四个方向：上下左右
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for df, dr in directions:
            new_file = file_idx + df
            new_rank = rank_idx + dr
            
            # 检查是否在九宫格内
            if min_file <= new_file <= max_file and min_rank <= new_rank <= max_rank:
                to_pos = FenService.coord_to_pos(new_file, new_rank)
                target_piece = self.get_piece(to_pos)
                
                # 不能吃己方棋子
                if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                    moves.append(self._create_move(position, to_pos))
        
        return moves
    
    def _get_advisor_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取士/仕的走法
        
        规则：
        - 在九宫格内移动
        - 每次一步，斜线移动
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        is_red = piece.isupper()
        
        # 九宫格范围
        if is_red:
            min_rank, max_rank = 0, 2
        else:
            min_rank, max_rank = 7, 9
        
        min_file, max_file = 3, 5
        
        # 四个斜线方向
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for df, dr in directions:
            new_file = file_idx + df
            new_rank = rank_idx + dr
            
            # 检查是否在九宫格内
            if min_file <= new_file <= max_file and min_rank <= new_rank <= max_rank:
                to_pos = FenService.coord_to_pos(new_file, new_rank)
                target_piece = self.get_piece(to_pos)
                
                # 不能吃己方棋子
                if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                    moves.append(self._create_move(position, to_pos))
        
        return moves
    
    def _get_bishop_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取象/相的走法
        
        规则：
        - 走田字（对角线两步）
        - 不能过河
        - 象眼不能被堵住
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        is_red = piece.isupper()
        
        # 象眼位置（田字中心）
        eye_offsets = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        # 目标位置（田字对角）
        target_offsets = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        
        for (eye_df, eye_dr), (target_df, target_dr) in zip(eye_offsets, target_offsets):
            new_file = file_idx + target_df
            new_rank = rank_idx + target_dr
            
            # 检查边界
            if not (0 <= new_file <= 8 and 0 <= new_rank <= 9):
                continue
            
            # 检查是否过河
            if is_red and new_rank > 4:  # 红相不能过河（rank > 5）
                continue
            if not is_red and new_rank < 5:  # 黑象不能过河（rank < 6）
                continue
            
            # 检查象眼
            eye_file = file_idx + eye_df
            eye_rank = rank_idx + eye_dr
            eye_pos = FenService.coord_to_pos(eye_file, eye_rank)
            
            if self.get_piece(eye_pos) is not None:
                continue  # 象眼被堵
            
            to_pos = FenService.coord_to_pos(new_file, new_rank)
            target_piece = self.get_piece(to_pos)
            
            # 不能吃己方棋子
            if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                moves.append(self._create_move(position, to_pos))
        
        return moves
    
    def _get_knight_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取马的走法
        
        规则：
        - 走日字
        - 有蹩马腿限制
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        
        # 马的走法：(目标偏移，蹩腿位置偏移)
        knight_moves = [
            ((1, 2), (0, 1)),   # 右上
            ((2, 1), (1, 0)),   # 右远上
            ((2, -1), (1, 0)),  # 右远下
            ((1, -2), (0, -1)), # 右下
            ((-1, -2), (0, -1)),# 左下
            ((-2, -1), (-1, 0)),# 左远下
            ((-2, 1), (-1, 0)), # 左远上
            ((-1, 2), (0, 1)),  # 左上
        ]
        
        for (target_df, target_dr), (leg_df, leg_dr) in knight_moves:
            new_file = file_idx + target_df
            new_rank = rank_idx + target_dr
            
            # 检查边界
            if not (0 <= new_file <= 8 and 0 <= new_rank <= 9):
                continue
            
            # 检查蹩马腿
            leg_file = file_idx + leg_df
            leg_rank = rank_idx + leg_dr
            leg_pos = FenService.coord_to_pos(leg_file, leg_rank)
            
            if self.get_piece(leg_pos) is not None:
                continue  # 蹩马腿
            
            to_pos = FenService.coord_to_pos(new_file, new_rank)
            target_piece = self.get_piece(to_pos)
            
            # 不能吃己方棋子
            if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                moves.append(self._create_move(position, to_pos))
        
        return moves
    
    def _get_rook_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取车的走法
        
        规则：
        - 直线移动（横竖均可）
        - 不能越过其他棋子
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        
        # 四个方向：上下左右
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for df, dr in directions:
            new_file = file_idx + df
            new_rank = rank_idx + dr
            
            while 0 <= new_file <= 8 and 0 <= new_rank <= 9:
                to_pos = FenService.coord_to_pos(new_file, new_rank)
                target_piece = self.get_piece(to_pos)
                
                if target_piece is None:
                    # 空位，可以移动
                    moves.append(self._create_move(position, to_pos))
                else:
                    # 有棋子
                    if FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                        # 敌方棋子，可以吃
                        moves.append(self._create_move(position, to_pos))
                    # 无论吃不吃，都不能继续前进
                    break
                
                new_file += df
                new_rank += dr
        
        return moves
    
    def _get_cannon_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取炮的走法
        
        规则：
        - 不吃子时：同车（直线移动）
        - 吃子时：需要炮架（隔一个棋子）
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        
        # 四个方向：上下左右
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for df, dr in directions:
            new_file = file_idx + df
            new_rank = rank_idx + dr
            screen_found = False  # 是否找到炮架
            
            while 0 <= new_file <= 8 and 0 <= new_rank <= 9:
                to_pos = FenService.coord_to_pos(new_file, new_rank)
                target_piece = self.get_piece(to_pos)
                
                if not screen_found:
                    # 还没找到炮架
                    if target_piece is None:
                        # 空位，可以移动（不吃子）
                        moves.append(self._create_move(position, to_pos))
                    else:
                        # 找到炮架
                        screen_found = True
                else:
                    # 已经找到炮架
                    if target_piece is not None:
                        # 有棋子，可以吃（隔山打牛）
                        if FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                            moves.append(self._create_move(position, to_pos))
                        # 无论吃不吃，都不能继续前进
                        break
                
                new_file += df
                new_rank += dr
        
        return moves
    
    def _get_pawn_moves(self, position: str, piece: str) -> List[Move]:
        """
        获取兵/卒的走法
        
        规则：
        - 过河前：只能向前走
        - 过河后：可以向前或横走
        - 不能后退
        - 每次一步
        """
        moves = []
        file_idx, rank_idx = FenService.pos_to_coord(position)
        is_red = piece.isupper()
        
        # 红兵向前是 rank 增加，黑卒向前是 rank 减少
        forward_dr = 1 if is_red else -1
        
        # 是否过河
        crossed_river = False
        if is_red:
            crossed_river = rank_idx >= 5  # 红兵 rank >= 6 为过河
        else:
            crossed_river = rank_idx <= 4  # 黑卒 rank <= 5 为过河
        
        # 向前走
        new_rank = rank_idx + forward_dr
        if 0 <= new_rank <= 9:
            to_pos = FenService.coord_to_pos(file_idx, new_rank)
            target_piece = self.get_piece(to_pos)
            
            if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                moves.append(self._create_move(position, to_pos))
        
        # 过河后可以横走
        if crossed_river:
            for df in [-1, 1]:  # 左右
                new_file = file_idx + df
                if 0 <= new_file <= 8:
                    to_pos = FenService.coord_to_pos(new_file, rank_idx)
                    target_piece = self.get_piece(to_pos)
                    
                    if target_piece is None or FenService.get_piece_color(target_piece) != FenService.get_piece_color(piece):
                        moves.append(self._create_move(position, to_pos))
        
        return moves
    
    def _is_legal_move(self, move: Move) -> bool:
        """
        验证走棋是否合法（不会导致己方被将军）
        
        Args:
            move: 走棋对象
            
        Returns:
            是否合法
        """
        if move is None:
            return False
        
        # 模拟走棋
        original_piece = self.squares.get(move.to_pos)
        self.squares[move.to_pos] = self.squares[move.from_pos]
        del self.squares[move.from_pos]
        
        # 检查是否被将军
        is_in_check = self._is_in_check(move.piece.isupper())
        
        # 恢复棋盘
        self.squares[move.from_pos] = self.squares[move.to_pos]
        if original_piece:
            self.squares[move.to_pos] = original_piece
        else:
            del self.squares[move.to_pos]
        
        return not is_in_check
    
    def _is_in_check(self, is_red: bool) -> bool:
        """
        检查是否被将军
        
        Args:
            is_red: 是否检查红方
            
        Returns:
            是否被将军
        """
        # 找到将/帅的位置
        king_piece = 'K' if is_red else 'k'
        king_pos = None
        
        for pos, piece in self.squares.items():
            if piece == king_piece:
                king_pos = pos
                break
        
        if not king_pos:
            return False  # 将/帅不存在（不应该发生）
        
        # 检查是否有敌方棋子可以攻击到将/帅
        enemy_color = 'black' if is_red else 'red'
        
        for pos, piece in self.squares.items():
            if FenService.get_piece_color(piece) == enemy_color:
                # 获取该棋子的攻击范围
                attacks = self._get_piece_attacks(pos, piece)
                if king_pos in attacks:
                    return True
        
        return False
    
    def _get_piece_attacks(self, position: str, piece: str) -> List[str]:
        """
        获取棋子的攻击范围（不考虑是否被将军）
        
        Args:
            position: 棋子位置
            piece: 棋子代码
            
        Returns:
            可以攻击的位置列表
        """
        moves = self._get_piece_moves(position, piece)
        return [m.to_pos for m in moves]
    
    def make_move(self, move: Move) -> bool:
        """
        执行走棋
        
        Args:
            move: 走棋对象
            
        Returns:
            是否成功
        """
        if move is None or not self._is_legal_move(move):
            return False
        
        # 更新棋盘
        self.squares[move.to_pos] = self.squares[move.from_pos]
        del self.squares[move.from_pos]
        
        # 更新回合
        self.turn = 'b' if self.turn == 'w' else 'w'
        
        # 更新 50 步规则计数
        if move.is_capture or move.piece.upper() == 'P':
            self.halfmove = 0
        else:
            self.halfmove += 1
        
        # 更新回合数
        if self.turn == 'w':
            self.fullmove += 1
        
        return True
    
    def _is_valid_king_move(self, move: Move, piece: str) -> bool:
        """
        验证将/帅的走棋是否有效
        
        Args:
            move: 走棋对象
            piece: 棋子代码
            
        Returns:
            是否有效
        """
        # 这个函数主要用于测试
        file_idx, rank_idx = FenService.pos_to_coord(move.to_pos)
        is_red = piece.isupper()
        
        # 九宫格范围
        if is_red:
            min_rank, max_rank = 0, 2
        else:
            min_rank, max_rank = 7, 9
        
        min_file, max_file = 3, 5
        
        return min_file <= file_idx <= max_file and min_rank <= rank_idx <= max_rank
    
    def is_check(self, is_red: bool) -> bool:
        """
        检查指定方是否被将军
        
        Args:
            is_red: 是否检查红方
            
        Returns:
            是否被将军
        """
        return self._is_in_check(is_red)
    
    def is_checkmate(self) -> bool:
        """
        检查是否将死
        
        将死条件：
        1. 当前回合方被将军
        2. 当前回合方没有任何合法走法
        
        Returns:
            是否将死
        """
        is_red_turn = self.turn == 'w'
        
        # 首先检查是否被将军
        if not self._is_in_check(is_red_turn):
            return False
        
        # 检查是否有任何合法走法
        legal_moves = self.get_all_legal_moves()
        return len(legal_moves) == 0
    
    def is_stalemate(self) -> bool:
        """
        检查是否困毙（无棋可走但未被将军）
        
        困毙条件：
        1. 当前回合方未被将军
        2. 当前回合方没有任何合法走法
        
        Returns:
            是否困毙
        """
        is_red_turn = self.turn == 'w'
        
        # 首先检查是否被将军（如果将军则不是困毙）
        if self._is_in_check(is_red_turn):
            return False
        
        # 检查是否有任何合法走法
        legal_moves = self.get_all_legal_moves()
        return len(legal_moves) == 0
    
    def get_legal_moves_for_position(self, position: str) -> List[Move]:
        """
        获取指定位置的所有合法走法（考虑将军情况）
        
        Args:
            position: 棋子位置
            
        Returns:
            合法走法列表
        """
        return self.get_legal_moves_for_piece(position)
    
    def get_all_legal_moves_for_side(self, is_red: bool) -> List[Move]:
        """
        获取指定方的所有合法走法
        
        Args:
            is_red: 是否获取红方的走法
            
        Returns:
            合法走法列表
        """
        legal_moves = []
        
        # 复制字典避免迭代时修改
        squares_copy = dict(self.squares)
        for position, piece in squares_copy.items():
            # 只处理指定方的棋子
            piece_is_red = piece.isupper()
            if (is_red and piece_is_red) or (not is_red and not piece_is_red):
                piece_moves = self.get_legal_moves_for_piece(position)
                legal_moves.extend(piece_moves)
        
        return legal_moves


class MoveValidator:
    """走棋验证器"""
    
    def __init__(self, board: Board):
        """
        初始化验证器
        
        Args:
            board: 棋盘对象
        """
        self.board = board
    
    def is_valid_move(self, move: Move) -> bool:
        """
        验证走棋是否合法
        
        Args:
            move: 走棋对象
            
        Returns:
            是否合法
        """
        if move is None:
            return False
        
        # 检查是否是当前回合
        piece_color = FenService.get_piece_color(move.piece)
        expected_turn = 'w' if piece_color == 'red' else 'b'
        
        if self.board.turn != expected_turn:
            return False
        
        # 检查棋子是否在正确位置
        actual_piece = self.board.get_piece(move.from_pos)
        if actual_piece != move.piece:
            return False
        
        # 检查走棋是否符合规则
        legal_moves = self.board.get_legal_moves_for_piece(move.from_pos)
        legal_positions = [m.to_pos for m in legal_moves]
        
        return move.to_pos in legal_positions
