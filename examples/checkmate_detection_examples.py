#!/usr/bin/env python3
"""
将死/困毙检测使用示例

演示如何使用 CheckmateDetector 和 StalemateDetector
"""
import sys
import os

# 添加 backend 到 Python 路径
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src/backend')
sys.path.insert(0, backend_path)

from games.engine import Board
from games.services.checkmate_detector import CheckmateDetector
from games.services.stalemate_detector import StalemateDetector


def print_board(board: Board):
    """打印棋盘"""
    print("\n棋盘局面:")
    print("=" * 50)
    
    # 从第 10 行到第 1 行打印
    for rank in range(9, -1, -1):
        row = ""
        for file in range(9):
            pos = f"{chr(ord('a') + file)}{rank + 1}"
            piece = board.get_piece(pos)
            row += f" {piece or '.'} "
        print(f"{rank + 1:2d} {row}")
    
    print("    a   b   c   d   e   f   g   h   i")
    print(f"回合：{'红方' if board.turn == 'w' else '黑方'}")
    print("=" * 50)


def example_01_checkmate():
    """示例 1: 将死检测"""
    print("\n" + "=" * 60)
    print("示例 1: 将死检测")
    print("=" * 60)
    
    # 创建一个将死局面
    fen = "3ak4/4R4/9/9/9/9/9/9/9/4K4 b - - 0 1"
    board = Board(fen=fen)
    
    print_board(board)
    
    # 检测将死
    is_checkmate = CheckmateDetector.check_checkmate(board, 'b')
    
    print(f"\n检测结果:")
    print(f"  是否将死：{is_checkmate}")
    
    # 获取详细信息
    result = CheckmateDetector.check_checkmate_detailed(board, 'b')
    print(f"  是否被将军：{result['is_in_check']}")
    print(f"  合法走法数：{result['legal_moves_count']}")
    print(f"  原因：{result['reason']}")


def example_02_stalemate():
    """示例 2: 困毙检测"""
    print("\n" + "=" * 60)
    print("示例 2: 困毙检测")
    print("=" * 60)
    
    # 创建一个局面
    fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
    board = Board(fen=fen)
    
    print_board(board)
    
    # 检测困毙
    is_stalemate = StalemateDetector.check_stalemate(board, 'b')
    
    print(f"\n检测结果:")
    print(f"  是否困毙：{is_stalemate}")
    
    # 获取详细信息
    result = StalemateDetector.check_stalemate_detailed(board, 'b')
    print(f"  是否被将军：{result['is_in_check']}")
    print(f"  合法走法数：{result['legal_moves_count']}")
    print(f"  原因：{result['reason']}")


def example_03_analysis():
    """示例 3: 困毙原因分析"""
    print("\n" + "=" * 60)
    print("示例 3: 困毙原因分析")
    print("=" * 60)
    
    # 创建一个局面
    fen = "3ak4/9/9/9/9/9/9/9/4K4/9 b - - 0 1"
    board = Board(fen=fen)
    
    print_board(board)
    
    # 分析困毙原因
    analysis = StalemateDetector.analyze_stalemate_cause(board, 'b')
    
    print(f"\n分析结果:")
    print(f"  分析方：{'红方' if analysis['is_red'] else '黑方'}")
    print(f"  分析棋子数：{len(analysis['pieces_analyzed'])}")
    print(f"  无法移动的棋子数：{len(analysis['blocked_pieces'])}")
    print(f"  总结：{analysis['summary']}")
    
    if analysis['blocked_pieces']:
        print(f"\n  无法移动的棋子详情:")
        for blocked in analysis['blocked_pieces'][:5]:  # 只显示前 5 个
            print(f"    - {blocked['piece']} 在 {blocked['position']}: {blocked['reason']}")


def example_04_initial_position():
    """示例 4: 初始局面检测"""
    print("\n" + "=" * 60)
    print("示例 4: 初始局面检测")
    print("=" * 60)
    
    # 初始局面
    board = Board()
    
    print_board(board)
    
    # 检测将死和困毙
    is_checkmate = CheckmateDetector.check_checkmate(board, 'w')
    is_stalemate = StalemateDetector.check_stalemate(board, 'w')
    
    print(f"\n检测结果:")
    print(f"  是否将死：{is_checkmate}")
    print(f"  是否困毙：{is_stalemate}")
    print(f"  合法走法数：{len(board.get_all_legal_moves())}")


def example_05_patterns():
    """示例 5: 将死模式识别"""
    print("\n" + "=" * 60)
    print("示例 5: 将死模式识别")
    print("=" * 60)
    
    # 创建一个将死局面
    fen = "3ak4/4R4/9/9/9/9/9/9/9/4K4 b - - 0 1"
    board = Board(fen=fen)
    
    print_board(board)
    
    # 识别将死模式
    patterns = CheckmateDetector.get_checkmate_patterns(board)
    
    print(f"\n识别到的将死模式:")
    if patterns:
        for pattern in patterns:
            print(f"  - {pattern}")
    else:
        print("  未识别到典型将死模式（或局面不是将死）")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("将死/困毙检测使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_01_checkmate()
    example_02_stalemate()
    example_03_analysis()
    example_04_initial_position()
    example_05_patterns()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
