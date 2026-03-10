"""
残局挑战 URL 路由
"""
from django.urls import path
from puzzles.views import (
    PuzzleListView,
    PuzzleDetailView,
    PuzzleAttemptCreateView,
    PuzzleMoveView,
    PuzzleCompleteView,
    PuzzleProgressView,
    PuzzleLeaderboardView,
)

app_name = 'puzzles'

urlpatterns = [
    # 关卡列表
    path('', PuzzleListView.as_view(), name='puzzle-list'),
    
    # 关卡详情
    path('<uuid:id>/', PuzzleDetailView.as_view(), name='puzzle-detail'),
    
    # 创建挑战
    path('<uuid:id>/attempt/', PuzzleAttemptCreateView.as_view(), name='puzzle-attempt-create'),
    
    # 提交走法
    path('<uuid:id>/attempts/<uuid:attempt_id>/move/', PuzzleMoveView.as_view(), name='puzzle-move'),
    
    # 完成挑战
    path('<uuid:id>/attempts/<uuid:attempt_id>/complete/', PuzzleCompleteView.as_view(), name='puzzle-complete'),
    
    # 用户进度
    path('progress/', PuzzleProgressView.as_view(), name='puzzle-progress'),
    
    # 排行榜
    path('leaderboard/', PuzzleLeaderboardView.as_view(), name='puzzle-leaderboard'),
]
