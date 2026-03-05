"""
AI Engine URL 路由配置
"""
from django.urls import path, include
from .views import (
    AIGameListView, AIGameDetailView,
    AIMoveView, AIHintView, AIAnalyzeView,
    AIDifficultyListView, AIEngineStatusView
)

app_name = 'ai_engine'

urlpatterns = [
    # AI 对局管理
    path('games/', AIGameListView.as_view(), name='ai-game-list'),
    path('games/<uuid:game_id>/', AIGameDetailView.as_view(), name='ai-game-detail'),
    
    # AI 走棋
    path('games/<uuid:game_id>/move/', AIMoveView.as_view(), name='ai-game-move'),
    
    # AI 提示
    path('games/<uuid:game_id>/hint/', AIHintView.as_view(), name='ai-game-hint'),
    
    # AI 分析
    path('games/<uuid:game_id>/analyze/', AIAnalyzeView.as_view(), name='ai-game-analyze'),
    
    # 难度配置
    path('difficulties/', AIDifficultyListView.as_view(), name='ai-difficulty-list'),
    
    # 引擎状态
    path('engines/status/', AIEngineStatusView.as_view(), name='ai-engine-status'),
]
