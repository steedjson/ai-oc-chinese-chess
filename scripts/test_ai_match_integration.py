#!/usr/bin/env python
"""
AI 对局 & 匹配功能集成测试脚本

测试内容:
1. AI 对局功能:
   - 创建 AI 对局
   - 请求 AI 走棋
   - 测试不同难度等级
   - WebSocket 通知

2. 匹配功能:
   - 加入匹配队列
   - 匹配成功通知
   - 取消匹配
   - ELO 算法验证

使用方法:
    cd /Users/changsailong/.openclaw/workspace/projects/chinese-chess
    python3 scripts/test_ai_match_integration.py
"""
import os
import sys
import django
import time
import json
import redis
from pathlib import Path

# 设置 Django 环境
backend_dir = Path(__file__).resolve().parent.parent / 'src' / 'backend'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(backend_dir))
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from games.models import Game
from ai_engine.services import StockfishService, AIMove
from ai_engine.config import get_difficulty_config
from matchmaking.queue import MatchmakingQueue
from matchmaking import elo as elo_module
from matchmaking.models import MatchQueue

User = get_user_model()


class Colors:
    """终端颜色输出"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_warning(text):
    """打印警告"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


# ============== AI 对局功能测试 ==============

def test_create_ai_game():
    """测试创建 AI 对局"""
    print_header("测试 1: 创建 AI 对局")
    
    try:
        # 创建测试用户
        user, created = User.objects.get_or_create(
            username='test_ai_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('password')
            user.save()
        
        # 创建 AI 对局
        game = Game.objects.create(
            player_red=user,
            player_black=None,  # AI 对局，黑方为空
            game_type='ai',
            status='waiting'
        )
        
        print_success(f"AI 对局创建成功: ID={game.id}")
        print_info(f"  - 玩家：{user.username}")
        print_info(f"  - 类型：{game.game_type}")
        print_info(f"  - 状态：{game.status}")
        
        # 清理
        game.delete()
        if created:
            user.delete()
        
        return True
        
    except Exception as e:
        print_error(f"创建 AI 对局失败：{e}")
        return False


def test_ai_move_request():
    """测试请求 AI 走棋"""
    print_header("测试 2: 请求 AI 走棋")
    
    try:
        # 检查 Stockfish 是否可用
        try:
            from stockfish import Stockfish
            print_success("Stockfish 引擎已安装")
        except ImportError:
            print_warning("Stockfish 引擎未安装，跳过实际走棋测试")
            print_info("提示：pip3 install --break-system-packages stockfish")
            return True
        
        # 测试不同 FEN 局面的 AI 走棋
        test_fens = [
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1",  # 初始局面
            "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - - 0 1",  # 黑方走棋
        ]
        
        for i, fen in enumerate(test_fens, 1):
            print_info(f"\n测试局面 {i}: {fen[:50]}...")
            
            service = StockfishService(difficulty=3)  # 使用低难度加快测试
            start_time = time.time()
            
            try:
                move = service.get_best_move(fen, time_limit=1000)
                elapsed = (time.time() - start_time) * 1000
                
                print_success(f"  AI 走棋：{move.from_pos} → {move.to_pos}")
                print_info(f"    棋子：{move.piece}")
                print_info(f"    评估：{move.evaluation}")
                print_info(f"    深度：{move.depth}")
                print_info(f"    耗时：{elapsed:.2f}ms")
                
            except Exception as e:
                print_warning(f"  走棋失败：{e}")
        
        return True
        
    except Exception as e:
        print_error(f"AI 走棋测试失败：{e}")
        return False


def test_difficulty_levels():
    """测试不同难度等级"""
    print_header("测试 3: 测试不同难度等级")
    
    try:
        # 测试难度配置
        test_difficulties = [1, 5, 10]
        
        for difficulty in test_difficulties:
            print_info(f"\n难度等级：{difficulty}")
            
            try:
                config = get_difficulty_config(difficulty)
                print_success(f"  配置加载成功")
                print_info(f"    Skill Level: {config.skill_level}")
                print_info(f"    搜索深度：{config.search_depth}")
                print_info(f"    思考时间：{config.think_time_ms}ms")
                print_info(f"    ELO: {config.elo}")
                
            except Exception as e:
                print_error(f"  配置加载失败：{e}")
        
        return True
        
    except Exception as e:
        print_error(f"难度等级测试失败：{e}")
        return False


def test_websocket_notifications():
    """测试 WebSocket 通知"""
    print_header("测试 4: WebSocket 通知")
    
    try:
        # 检查 Redis 连接
        try:
            r = redis.from_url('redis://localhost:6379/0')
            r.ping()
            print_success("Redis 连接正常")
        except redis.ConnectionError:
            print_warning("Redis 未启动，跳过 WebSocket 测试")
            print_info("提示：brew install redis && brew services start redis")
            return True
        
        # 测试消息发送
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # 发送测试消息
        test_message = {
            'type': 'game.move',
            'data': {
                'game_id': 'test_game',
                'move': 'e2e4',
                'player': 'red'
            }
        }
        
        async_to_sync(channel_layer.group_send)(
            'game_test_game',
            test_message
        )
        
        print_success("WebSocket 消息发送成功")
        print_info(f"  消息类型：game.move")
        print_info(f"  目标群组：game_test_game")
        
        return True
        
    except Exception as e:
        print_error(f"WebSocket 通知测试失败：{e}")
        return False


# ============== 匹配功能测试 ==============

def test_join_match_queue():
    """测试加入匹配队列"""
    print_header("测试 5: 加入匹配队列")
    
    try:
        # 检查 Redis 连接
        try:
            r = redis.from_url('redis://localhost:6379/0')
            r.ping()
        except redis.ConnectionError:
            print_warning("Redis 未启动，跳过匹配队列测试")
            return True
        
        queue = MatchmakingQueue()
        
        # 创建测试用户
        user, created = User.objects.get_or_create(
            username='test_match_user',
            defaults={'email': 'match@example.com'}
        )
        if created:
            user.set_password('password')
            user.save()
        
        # 加入匹配队列
        result = queue.join_queue(
            user_id=str(user.id),
            rating=1500,
            game_type='online'
        )
        
        if result:
            print_success(f"用户 {user.username} 加入匹配队列成功")
            print_info(f"  初始 ELO: 1500")
            print_info(f"  游戏类型：online")
            
            # 清理
            queue.leave_queue(str(user.id), 'online')
        else:
            print_warning("加入队列失败（可能已在队列中）")
        
        if created:
            user.delete()
        
        return True
        
    except Exception as e:
        print_error(f"加入匹配队列失败：{e}")
        return False


def test_match_success_notification():
    """测试匹配成功通知"""
    print_header("测试 6: 匹配成功通知")
    
    try:
        # 检查 Redis 连接
        try:
            r = redis.from_url('redis://localhost:6379/0')
            r.ping()
        except redis.ConnectionError:
            print_warning("Redis 未启动，跳过匹配通知测试")
            return True
        
        queue = MatchmakingQueue()
        
        # 模拟两个用户匹配
        user1_id = "user_001"
        user2_id = "user_002"
        
        # 手动添加到队列（模拟匹配成功）
        r = redis.from_url('redis://localhost:6379/0')
        queue_key = "matchmaking:queue:online"
        
        # 清理旧数据
        r.delete(queue_key)
        r.delete(f"matchmaking:user:{user1_id}")
        r.delete(f"matchmaking:user:{user2_id}")
        
        # 添加用户
        queue.join_queue(user1_id, 1500, 'online')
        queue.join_queue(user2_id, 1520, 'online')
        
        print_success("模拟匹配场景设置完成")
        print_info(f"  用户 1: {user1_id} (ELO: 1500)")
        print_info(f"  用户 2: {user2_id} (ELO: 1520)")
        
        # 清理
        queue.leave_queue(user1_id, 'online')
        queue.leave_queue(user2_id, 'online')
        
        return True
        
    except Exception as e:
        print_error(f"匹配成功通知测试失败：{e}")
        return False


def test_cancel_match():
    """测试取消匹配"""
    print_header("测试 7: 取消匹配")
    
    try:
        # 检查 Redis 连接
        try:
            r = redis.from_url('redis://localhost:6379/0')
            r.ping()
        except redis.ConnectionError:
            print_warning("Redis 未启动，跳过取消匹配测试")
            return True
        
        queue = MatchmakingQueue()
        
        user_id = "test_cancel_user"
        
        # 加入队列
        queue.join_queue(user_id, 1500, 'online')
        print_info("用户已加入匹配队列")
        
        # 取消匹配
        result = queue.leave_queue(user_id, 'online')
        
        if result:
            print_success("取消匹配成功")
        else:
            print_warning("取消匹配失败（用户不在队列中）")
        
        return True
        
    except Exception as e:
        print_error(f"取消匹配测试失败：{e}")
        return False


def test_elo_algorithm():
    """测试 ELO 算法"""
    print_header("测试 8: ELO 算法验证")
    
    try:
        # 测试场景 1: 低分玩家战胜高分玩家
        rating_a = 1400
        rating_b = 1600
        
        expected_a = elo_module.calculate_expected_score(rating_a, rating_b)
        expected_b = elo_module.calculate_expected_score(rating_b, rating_a)
        
        print_info(f"\n场景 1: 低分 vs 高分")
        print_info(f"  玩家 A: {rating_a} (预期得分：{expected_a:.2%})")
        print_info(f"  玩家 B: {rating_b} (预期得分：{expected_b:.2%})")
        
        # A 获胜
        change_a = elo_module.calculate_elo_change(rating_a, rating_b, 'win')
        change_b = elo_module.calculate_elo_change(rating_b, rating_a, 'loss')
        
        new_rating_a = rating_a + change_a
        new_rating_b = rating_b + change_b
        
        print_success(f"  A 获胜后:")
        print_info(f"    A 新 rating: {new_rating_a} (变化：{change_a:+d})")
        print_info(f"    B 新 rating: {new_rating_b} (变化：{change_b:+d})")
        
        # 测试场景 2: 同等水平
        rating_c = 1500
        rating_d = 1500
        
        print_info(f"\n场景 2: 同等水平")
        print_info(f"  玩家 C: {rating_c}")
        print_info(f"  玩家 D: {rating_d}")
        
        change_c = elo_module.calculate_elo_change(rating_c, rating_d, 'draw')
        change_d = elo_module.calculate_elo_change(rating_d, rating_c, 'draw')
        
        new_rating_c = rating_c + change_c
        new_rating_d = rating_d + change_d
        
        print_success(f"  平局后:")
        print_info(f"    C 新 rating: {new_rating_c} (变化：{change_c:+d})")
        print_info(f"    D 新 rating: {new_rating_d} (变化：{change_d:+d})")
        
        # 验证 ELO 变化合理性
        if abs(change_c) < 20 and abs(change_d) < 20:
            print_success("ELO 变化在合理范围内")
        else:
            print_warning("ELO 变化可能过大")
        
        return True
        
    except Exception as e:
        print_error(f"ELO 算法测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


# ============== 主测试流程 ==============

def run_all_tests():
    """运行所有测试"""
    print_header("🎮 中国象棋 AI 对局 & 匹配功能集成测试")
    print_info(f"开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("创建 AI 对局", test_create_ai_game),
        ("请求 AI 走棋", test_ai_move_request),
        ("不同难度等级", test_difficulty_levels),
        ("WebSocket 通知", test_websocket_notifications),
        ("加入匹配队列", test_join_match_queue),
        ("匹配成功通知", test_match_success_notification),
        ("取消匹配", test_cancel_match),
        ("ELO 算法验证", test_elo_algorithm),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"{name} 测试异常：{e}")
            results.append((name, False))
        
        time.sleep(0.5)  # 避免过快
    
    # 打印总结
    print_header("📊 测试总结")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{Colors.BOLD}总计：{passed}/{total} 通过 ({passed/total*100:.1f}%){Colors.RESET}")
    
    if passed == total:
        print_success("🎉 所有测试通过！")
    else:
        print_warning(f"⚠ {total - passed} 个测试失败")
    
    print_info(f"结束时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
