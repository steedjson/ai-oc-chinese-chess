"""
游戏服务

提供游戏核心功能：
- 走棋处理
- 游戏状态管理
- 将死/困毙检测
"""
import logging
from typing import Optional, Dict, Any
from datetime import timezone

from django.utils import timezone as django_timezone

from games.models import Game, GameMove
from games.engine import Board, Move
from games.services.checkmate_detector import CheckmateDetector
from games.services.stalemate_detector import StalemateDetector

logger = logging.getLogger(__name__)


class GameService:
    """游戏服务类"""
    
    def __init__(self):
        """初始化游戏服务"""
        self.checkmate_detector = CheckmateDetector()
        self.stalemate_detector = StalemateDetector()
    
    def make_move(self, game_id: int, move_data: Dict[str, str]) -> Dict[str, Any]:
        """
        执行走棋
        
        流程：
        1. 加载游戏和棋盘
        2. 执行走棋
        3. 检查是否将死
        4. 检查是否困毙
        5. 更新游戏状态
        6. 返回结果
        
        Args:
            game_id: 游戏 ID
            move_data: 走棋数据 {from_pos, to_pos, piece}
            
        Returns:
            走棋结果字典
        """
        try:
            # 加载游戏
            game = Game.objects.get(id=game_id)
            
            # 加载棋盘
            board = Board(fen=game.fen_current)
            
            # 创建走棋对象
            move = Move(
                from_pos=move_data['from_pos'],
                to_pos=move_data['to_pos'],
                piece=move_data['piece'],
                captured=board.get_piece(move_data['to_pos'])
            )
            
            # 验证走棋合法性
            if not board._is_legal_move(move):
                return {
                    'success': False,
                    'error_code': 'ILLEGAL_MOVE',
                    'error_message': '非法走棋'
                }
            
            # 执行走棋
            board.make_move(move)
            
            # 确定当前玩家（走棋后轮到对方）
            current_player = board.turn
            opponent_player = 'red' if current_player == 'w' else 'black'
            
            # 检查将死
            is_checkmate = self.checkmate_detector.check_checkmate(board, current_player)
            
            # 检查困毙
            is_stalemate = False
            if not is_checkmate:
                is_stalemate = self.stalemate_detector.check_stalemate(board, current_player)
            
            # 准备结果
            result = {
                'success': True,
                'fen': board.to_fen(),
                'turn': board.turn,
                'is_check': board.is_check(current_player == 'w'),
                'is_checkmate': is_checkmate,
                'is_stalemate': is_stalemate,
                'game_over': is_checkmate or is_stalemate
            }
            
            # 更新游戏状态
            game.fen_current = board.to_fen()
            game.turn = board.turn
            game.move_count += 1
            
            if is_checkmate or is_stalemate:
                # 游戏结束
                if is_checkmate:
                    # 将死：对方获胜
                    game.status = 'white_win' if opponent_player == 'red' else 'black_win'
                    result['winner'] = opponent_player
                    result['win_reason'] = 'checkmate'
                else:
                    # 困毙：平局
                    game.status = 'draw'
                    result['winner'] = None
                    result['win_reason'] = 'stalemate'
                
                game.finished_at = django_timezone.now()
                logger.info(f"Game {game_id} ended: {result['win_reason']}, winner={result.get('winner')}")
            
            game.save()
            
            # 记录走棋
            self._record_move(game, move, move_data.get('notation', ''))
            
            logger.info(f"Move made in game {game_id}: {move.from_pos}->{move.to_pos}, "
                       f"checkmate={is_checkmate}, stalemate={is_stalemate}")
            
            return result
            
        except Game.DoesNotExist:
            logger.error(f"Game {game_id} not found")
            return {
                'success': False,
                'error_code': 'GAME_NOT_FOUND',
                'error_message': '游戏不存在'
            }
        except Exception as e:
            logger.error(f"Error making move: {e}", exc_info=True)
            return {
                'success': False,
                'error_code': 'MOVE_ERROR',
                'error_message': str(e)
            }
    
    def _record_move(self, game: Game, move: Move, notation: str = '') -> None:
        """
        记录走棋历史
        
        Args:
            game: 游戏对象
            move: 走棋对象
            notation: 记谱
        """
        GameMove.objects.create(
            game=game,
            move_number=game.move_count,
            piece=move.piece,
            from_pos=move.from_pos,
            to_pos=move.to_pos,
            captured=move.captured,
            notation=notation or f"{move.piece}{move.from_pos}-{move.to_pos}"
        )
    
    def check_game_status(self, game_id: int) -> Dict[str, Any]:
        """
        检查游戏状态
        
        Args:
            game_id: 游戏 ID
            
        Returns:
            游戏状态字典
        """
        try:
            game = Game.objects.get(id=game_id)
            board = Board(fen=game.fen_current)
            
            current_player = board.turn
            is_red = current_player == 'w'
            
            # 检查将死
            is_checkmate = self.checkmate_detector.check_checkmate(board, current_player)
            
            # 检查困毙
            is_stalemate = False
            if not is_checkmate:
                is_stalemate = self.stalemate_detector.check_stalemate(board, current_player)
            
            # 检查将军
            is_check = board.is_check(is_red)
            
            return {
                'game_id': game_id,
                'fen': game.fen_current,
                'turn': board.turn,
                'is_check': is_check,
                'is_checkmate': is_checkmate,
                'is_stalemate': is_stalemate,
                'game_over': is_checkmate or is_stalemate,
                'status': game.status
            }
            
        except Game.DoesNotExist:
            return {
                'error': 'Game not found'
            }
        except Exception as e:
            logger.error(f"Error checking game status: {e}")
            return {
                'error': str(e)
            }
    
    def get_legal_moves(self, game_id: int) -> Dict[str, Any]:
        """
        获取当前所有合法走法
        
        Args:
            game_id: 游戏 ID
            
        Returns:
            合法走法列表
        """
        try:
            game = Game.objects.get(id=game_id)
            board = Board(fen=game.fen_current)
            
            legal_moves = board.get_all_legal_moves()
            
            return {
                'game_id': game_id,
                'legal_moves_count': len(legal_moves),
                'legal_moves': [
                    {
                        'from_pos': move.from_pos,
                        'to_pos': move.to_pos,
                        'piece': move.piece,
                        'captured': move.captured
                    }
                    for move in legal_moves
                ]
            }
            
        except Game.DoesNotExist:
            return {
                'error': 'Game not found'
            }
        except Exception as e:
            logger.error(f"Error getting legal moves: {e}")
            return {
                'error': str(e)
            }
