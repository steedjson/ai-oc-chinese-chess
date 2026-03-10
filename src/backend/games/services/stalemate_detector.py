"""
困毙检测器

检测中国象棋中的困毙局面：
- 当前玩家未被将军
- 但没有任何合法走法
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from games.engine import Board

logger = logging.getLogger(__name__)


class StalemateDetector:
    """困毙检测器"""
    
    @staticmethod
    def check_stalemate(board: 'Board', current_player: str = None) -> bool:
        """
        检测困毙
        
        困毙条件：
        1. 当前玩家未被将军
        2. 当前玩家没有任何合法走法
        
        Args:
            board: 棋盘对象
            current_player: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn
            
        Returns:
            True: 困毙
            False: 未困毙
        """
        # 确定当前玩家
        if current_player is None:
            current_player = board.turn
        
        is_red = current_player == 'w'
        
        # 条件 1: 检查是否被将军（如果将军则不是困毙）
        if board._is_in_check(is_red):
            logger.debug(f"Stalemate check failed: {'Red' if is_red else 'Black'} is in check")
            return False
        
        # 条件 2: 检查是否有任何合法走法
        legal_moves = board.get_all_legal_moves()
        
        if len(legal_moves) == 0:
            logger.info(f"Stalemate detected: {'Red' if is_red else 'Black'} has no legal moves but not in check")
            return True
        
        logger.debug(f"Stalemate check failed: {'Red' if is_red else 'Black'} has {len(legal_moves)} legal moves")
        return False
    
    @staticmethod
    def check_stalemate_detailed(board: 'Board', current_player: str = None) -> dict:
        """
        详细的困毙检测，返回检测详情
        
        Args:
            board: 棋盘对象
            current_player: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn
            
        Returns:
            检测结果字典：
            - is_stalemate: 是否困毙
            - is_in_check: 是否被将军
            - legal_moves_count: 合法走法数量
            - reason: 原因说明
        """
        if current_player is None:
            current_player = board.turn
        
        is_red = current_player == 'w'
        is_in_check = board._is_in_check(is_red)
        legal_moves = board.get_all_legal_moves()
        
        result = {
            'is_stalemate': False,
            'is_in_check': is_in_check,
            'legal_moves_count': len(legal_moves),
            'reason': ''
        }
        
        if is_in_check:
            result['reason'] = '被将军（不是困毙）'
            return result
        
        if len(legal_moves) > 0:
            result['reason'] = f'有{len(legal_moves)}个合法走法'
            return result
        
        result['is_stalemate'] = True
        result['reason'] = '未被将军但无合法走法'
        return result
    
    @staticmethod
    def analyze_stalemate_cause(board: 'Board', current_player: str = None) -> dict:
        """
        分析困毙原因
        
        分析为什么玩家没有合法走法：
        - 所有棋子都被阻塞
        - 所有棋子移动都会导致被将军
        - 特定棋子受限
        
        Args:
            board: 棋盘对象
            current_player: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn
            
        Returns:
            分析结果字典
        """
        if current_player is None:
            current_player = board.turn
        
        is_red = current_player == 'w'
        analysis = {
            'is_red': is_red,
            'pieces_analyzed': [],
            'blocked_pieces': [],
            'check_threats': [],
            'summary': ''
        }
        
        # 分析每个棋子（复制字典避免迭代时修改）
        squares = dict(board.squares)
        for position, piece in squares.items():
            piece_is_red = piece.isupper()
            if (is_red and piece_is_red) or (not is_red and not piece_is_red):
                # 获取该棋子的所有可能走法（不考虑将军）
                pseudo_moves = board._get_piece_moves(position, piece)
                # 获取合法走法（考虑将军）
                legal_moves = board.get_legal_moves_for_piece(position)
                
                piece_analysis = {
                    'piece': piece,
                    'position': position,
                    'pseudo_moves_count': len(pseudo_moves),
                    'legal_moves_count': len(legal_moves)
                }
                analysis['pieces_analyzed'].append(piece_analysis)
                
                # 如果完全没有走法
                if len(pseudo_moves) == 0:
                    analysis['blocked_pieces'].append({
                        'piece': piece,
                        'position': position,
                        'reason': '无可用走法'
                    })
                # 如果有走法但都不合法（会导致被将军）
                elif len(legal_moves) == 0:
                    analysis['blocked_pieces'].append({
                        'piece': piece,
                        'position': position,
                        'reason': '所有走法都会导致被将军'
                    })
        
        # 生成总结
        if len(analysis['blocked_pieces']) == len(analysis['pieces_analyzed']):
            analysis['summary'] = '所有棋子都无法移动'
        else:
            analysis['summary'] = f'{len(analysis["blocked_pieces"])}个棋子无法移动'
        
        return analysis
