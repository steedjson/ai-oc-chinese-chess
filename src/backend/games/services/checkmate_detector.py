"""
将死检测器

检测中国象棋中的将死局面：
- 当前玩家被将军
- 且没有任何合法走法可以解将
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from games.engine import Board

logger = logging.getLogger(__name__)


class CheckmateDetector:
    """将死检测器"""
    
    @staticmethod
    def check_checkmate(board: 'Board', current_player: str = None) -> bool:
        """
        检测将死
        
        将死条件：
        1. 当前玩家被将军
        2. 当前玩家没有任何合法走法可以解将
        
        Args:
            board: 棋盘对象
            current_player: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn
            
        Returns:
            True: 将死
            False: 未将死
        """
        # 确定当前玩家
        if current_player is None:
            current_player = board.turn
        
        is_red = current_player == 'w'
        
        # 条件 1: 检查是否被将军
        if not board._is_in_check(is_red):
            logger.debug(f"Checkmate check failed: {'Red' if is_red else 'Black'} is not in check")
            return False
        
        # 条件 2: 检查是否有任何合法走法
        legal_moves = board.get_all_legal_moves()
        
        if len(legal_moves) == 0:
            logger.info(f"Checkmate detected: {'Red' if is_red else 'Black'} has no legal moves")
            return True
        
        logger.debug(f"Checkmate check failed: {'Red' if is_red else 'Black'} has {len(legal_moves)} legal moves")
        return False
    
    @staticmethod
    def check_checkmate_detailed(board: 'Board', current_player: str = None) -> dict:
        """
        详细的将死检测，返回检测详情
        
        Args:
            board: 棋盘对象
            current_player: 当前玩家 ('w' 红方，'b' 黑方)，None 则使用 board.turn
            
        Returns:
            检测结果字典：
            - is_checkmate: 是否将死
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
            'is_checkmate': False,
            'is_in_check': is_in_check,
            'legal_moves_count': len(legal_moves),
            'reason': ''
        }
        
        if not is_in_check:
            result['reason'] = '未被将军'
            return result
        
        if len(legal_moves) > 0:
            result['reason'] = f'有{len(legal_moves)}个合法走法可以解将'
            return result
        
        result['is_checkmate'] = True
        result['reason'] = '被将军且无合法走法'
        return result
    
    @staticmethod
    def get_checkmate_patterns(board: 'Board') -> list:
        """
        获取常见的将死模式
        
        用于分析和教学，识别典型将死局面：
        - 重炮将死
        - 马后炮将死
        - 卧槽马将死
        - 挂角马将死
        - 铁门栓将死
        - 大刀剜心将死
        
        Args:
            board: 棋盘对象
            
        Returns:
            识别出的将死模式列表
        """
        patterns = []
        
        # 简化实现：检测基本将死模式
        # 完整实现需要复杂的模式识别
        
        if not board.is_checkmate():
            return patterns
        
        # 检测重炮（双炮将死）
        if CheckmateDetector._detect_double_cannon_pattern(board):
            patterns.append('重炮将死')
        
        # 检测马后炮
        if CheckmateDetector._detect_horse_cannon_pattern(board):
            patterns.append('马后炮将死')
        
        # 检测卧槽马
        if CheckmateDetector._detect_slot_horse_pattern(board):
            patterns.append('卧槽马将死')
        
        return patterns
    
    @staticmethod
    def _detect_double_cannon_pattern(board: 'Board') -> bool:
        """检测重炮将死模式"""
        # 简化实现
        # 需要检查是否有两个炮在一条线上攻击将/帅
        return False
    
    @staticmethod
    def _detect_horse_cannon_pattern(board: 'Board') -> bool:
        """检测马后炮将死模式"""
        # 简化实现
        # 需要检查马和炮的配合
        return False
    
    @staticmethod
    def _detect_slot_horse_pattern(board: 'Board') -> bool:
        """检测卧槽马将死模式"""
        # 简化实现
        # 需要检查马在特定位置
        return False
