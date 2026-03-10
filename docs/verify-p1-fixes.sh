#!/bin/bash

# P1 修复验证脚本
# 用于验证三个 P1 问题的修复是否成功

echo "======================================"
echo "  P1 高优先级问题修复验证"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 检查函数
check_result() {
  if [ $1 -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $2"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $2"
    ((FAILED++))
  fi
}

echo "1. 检查后端文件修改..."
echo "--------------------------------------"

# 检查 users/views.py 是否包含新的视图
if grep -q "class UserProfileView" src/backend/users/views.py; then
  check_result 0 "UserProfileView 已添加"
else
  check_result 1 "UserProfileView 未找到"
fi

if grep -q "class UserStatsView" src/backend/users/views.py; then
  check_result 0 "UserStatsView 已添加"
else
  check_result 1 "UserStatsView 未找到"
fi

if grep -q "class UserGamesView" src/backend/users/views.py; then
  check_result 0 "UserGamesView 已添加"
else
  check_result 1 "UserGamesView 未找到"
fi

# 检查 users/urls.py 是否包含新路由
if grep -q "profile/" src/backend/users/urls.py; then
  check_result 0 "Profile 路由已添加"
else
  check_result 1 "Profile 路由未找到"
fi

if grep -q "me/stats/" src/backend/users/urls.py; then
  check_result 0 "Stats 路由已添加"
else
  check_result 1 "Stats 路由未找到"
fi

echo ""
echo "2. 检查前端文件修改..."
echo "--------------------------------------"

# 检查 ProfilePage.tsx 是否移除 Mock 数据
if ! grep -q "mockGameHistory" src/frontend-user/src/pages/ProfilePage.tsx; then
  check_result 0 "ProfilePage Mock 数据已移除"
else
  check_result 1 "ProfilePage 仍包含 Mock 数据"
fi

# 检查是否使用真实 API
if grep -q "userService.getUserGames" src/frontend-user/src/pages/ProfilePage.tsx; then
  check_result 0 "ProfilePage 使用真实 API"
else
  check_result 1 "ProfilePage 未使用真实 API"
fi

# 检查 ServiceStatus 组件是否存在
if [ -f "src/frontend-user/src/components/layout/ServiceStatus.tsx" ]; then
  check_result 0 "ServiceStatus 组件已创建"
else
  check_result 1 "ServiceStatus 组件未找到"
fi

# 检查 WebSocketStatus 组件是否存在
if [ -f "src/frontend-user/src/components/game/WebSocketStatus.tsx" ]; then
  check_result 0 "WebSocketStatus 组件已创建"
else
  check_result 1 "WebSocketStatus 组件未找到"
fi

# 检查 Header 是否集成 ServiceStatus
if grep -q "ServiceStatus" src/frontend-user/src/components/layout/Header.tsx; then
  check_result 0 "Header 已集成 ServiceStatus"
else
  check_result 1 "Header 未集成 ServiceStatus"
fi

# 检查 WebSocket 服务是否有指数退避
if grep -q "exponentialDelay\|calculateDelay" src/frontend-user/src/services/websocket.service.ts; then
  check_result 0 "WebSocket 指数退避已实现"
else
  check_result 1 "WebSocket 指数退避未找到"
fi

echo ""
echo "3. 检查文档..."
echo "--------------------------------------"

# 检查修复报告是否存在
if [ -f "docs/P1-FIX-REPORT.md" ]; then
  check_result 0 "修复报告已创建"
else
  check_result 1 "修复报告未找到"
fi

echo ""
echo "======================================"
echo "  验证结果汇总"
echo "======================================"
echo -e "通过：${GREEN}${PASSED}${NC}"
echo -e "失败：${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ 所有检查项通过！${NC}"
  exit 0
else
  echo -e "${RED}✗ 部分检查项失败，请检查上述输出${NC}"
  exit 1
fi
