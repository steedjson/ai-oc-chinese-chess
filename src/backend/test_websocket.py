#!/usr/bin/env python
"""
WebSocket 连接测试脚本
测试三个 WebSocket 端点：
1. 游戏房间 WebSocket
2. AI 对弈 WebSocket
3. 匹配系统 WebSocket
"""

import asyncio
import websockets
import json
import sys

# 测试配置
BASE_URL = "ws://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcyNTUwMjg4LCJpYXQiOjE3NzI1NDMwODgsImp0aSI6ImM2YjE2ZDJkMTFhNzRiZDdhMzgwY2RmYTc5N2NjZTg2IiwidXNlcl9pZCI6MX0.ac7T6Dn9e_F3KjdVqAC0aKgdoUgWvtgHiMWXlArhwvU"
GAME_ID = "24fb613b-b390-417d-95f2-cf39d89cd1b7"  # 有效的游戏 ID
AI_GAME_ID = "dc8d9748-b12a-464c-86c9-8e0ba1175794"  # 有效的 AI 游戏 ID

results = {
    "game_websocket": {"status": "pending", "error": None},
    "ai_websocket": {"status": "pending", "error": None},
    "matchmaking_websocket": {"status": "pending", "error": None},
}

async def test_game_websocket():
    """测试游戏房间 WebSocket 连接"""
    print("\n" + "="*60)
    print("测试 1: 游戏房间 WebSocket")
    print("="*60)
    
    uri = f"{BASE_URL}/ws/game/{GAME_ID}/?token={TOKEN}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 连接成功：{uri}")
            
            # 发送 JOIN 消息
            join_msg = json.dumps({"type": "JOIN"})
            print(f"📤 发送：{join_msg}")
            await websocket.send(join_msg)
            
            # 接收响应（带超时）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 接收：{response}")
                
                # 验证响应格式
                try:
                    data = json.loads(response)
                    print(f"✅ 响应格式正确")
                except json.JSONDecodeError:
                    print(f"⚠️ 响应不是 JSON 格式")
                
            except asyncio.TimeoutError:
                print(f"⚠️ 接收响应超时（5 秒）")
            
            # 正常关闭
            await websocket.close()
            print(f"✅ 连接正常关闭")
            
            results["game_websocket"] = {"status": "passed", "error": None}
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        error_msg = f"❌ WebSocket 连接失败 (HTTP {e.status_code}): {e}"
        print(error_msg)
        results["game_websocket"] = {"status": "failed", "error": error_msg}
        return False
    except Exception as e:
        error_msg = f"❌ 发生错误：{type(e).__name__}: {e}"
        print(error_msg)
        results["game_websocket"] = {"status": "failed", "error": error_msg}
        return False

async def test_ai_websocket():
    """测试 AI 对弈 WebSocket 连接"""
    print("\n" + "="*60)
    print("测试 2: AI 对弈 WebSocket")
    print("="*60)
    
    uri = f"{BASE_URL}/ws/ai/game/{AI_GAME_ID}/?token={TOKEN}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 连接成功：{uri}")
            
            # 发送测试消息
            test_msg = json.dumps({"type": "JOIN"})
            print(f"📤 发送：{test_msg}")
            await websocket.send(test_msg)
            
            # 接收响应（带超时）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 接收：{response}")
            except asyncio.TimeoutError:
                print(f"⚠️ 接收响应超时（5 秒）")
            
            # 正常关闭
            await websocket.close()
            print(f"✅ 连接正常关闭")
            
            results["ai_websocket"] = {"status": "passed", "error": None}
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        error_msg = f"❌ WebSocket 连接失败 (HTTP {e.status_code}): {e}"
        print(error_msg)
        results["ai_websocket"] = {"status": "failed", "error": error_msg}
        return False
    except Exception as e:
        error_msg = f"❌ 发生错误：{type(e).__name__}: {e}"
        print(error_msg)
        results["ai_websocket"] = {"status": "failed", "error": error_msg}
        return False

async def test_matchmaking_websocket():
    """测试匹配系统 WebSocket 连接"""
    print("\n" + "="*60)
    print("测试 3: 匹配系统 WebSocket")
    print("="*60)
    
    uri = f"{BASE_URL}/ws/matchmaking/?token={TOKEN}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 连接成功：{uri}")
            
            # 发送加入匹配消息
            join_msg = json.dumps({"type": "JOIN_QUEUE", "mode": "classic"})
            print(f"📤 发送：{join_msg}")
            await websocket.send(join_msg)
            
            # 接收响应（带超时）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 接收：{response}")
            except asyncio.TimeoutError:
                print(f"⚠️ 接收响应超时（5 秒）- 这可能是正常的，因为匹配需要时间")
            
            # 正常关闭
            await websocket.close()
            print(f"✅ 连接正常关闭")
            
            results["matchmaking_websocket"] = {"status": "passed", "error": None}
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        error_msg = f"❌ WebSocket 连接失败 (HTTP {e.status_code}): {e}"
        print(error_msg)
        results["matchmaking_websocket"] = {"status": "failed", "error": error_msg}
        return False
    except Exception as e:
        error_msg = f"❌ 发生错误：{type(e).__name__}: {e}"
        print(error_msg)
        results["matchmaking_websocket"] = {"status": "failed", "error": error_msg}
        return False

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 WebSocket 连接测试开始")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {TOKEN[:50]}...")
    
    # 依次运行测试
    await test_game_websocket()
    await test_ai_websocket()
    await test_matchmaking_websocket()
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = result["status"]
        if status == "passed":
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif status == "failed":
            print(f"❌ {test_name}: FAILED")
            print(f"   错误：{result['error']}")
            failed += 1
        else:
            print(f"⚠️ {test_name}: {status}")
    
    print("\n" + "-"*60)
    print(f"总计：{passed} 通过，{failed} 失败")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
