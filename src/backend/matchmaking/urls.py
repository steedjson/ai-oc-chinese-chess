"""
Matchmaking URL routes.
"""

from django.urls import path
from .views import StartMatchmakingView, CancelMatchmakingView, MatchStatusView, LeaderboardView, UserRankView

app_name = 'matchmaking'

urlpatterns = [
    path('start/', StartMatchmakingView.as_view(), name='start'),
    path('cancel/', CancelMatchmakingView.as_view(), name='cancel'),
    path('status/', MatchStatusView.as_view(), name='status'),
    
    # 排行榜
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('user/<str:user_id>/', UserRankView.as_view(), name='user-rank'),
    path('user/', UserRankView.as_view(), name='user-rank-self'),
]
