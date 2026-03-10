"""
每日挑战 URL 路由
"""

from django.urls import path
from . import views


urlpatterns = [
    # 今日挑战
    path('today/', views.TodayChallengeView.as_view(), name='today-challenge'),
    path('today/attempt/', views.StartChallengeView.as_view(), name='start-challenge'),
    path('today/move/', views.SubmitMoveView.as_view(), name='submit-move'),
    path('today/complete/', views.CompleteChallengeView.as_view(), name='complete-challenge'),
    
    # 排行榜
    path('leaderboard/', views.ChallengeLeaderboardView.as_view(), name='challenge-leaderboard'),
    path('leaderboard/daily/', views.DailyLeaderboardView.as_view(), name='daily-leaderboard'),
    path('leaderboard/weekly/', views.WeeklyLeaderboardView.as_view(), name='weekly-leaderboard'),
    path('leaderboard/all-time/', views.AllTimeLeaderboardView.as_view(), name='all-time-leaderboard'),
    path('leaderboard/user/<str:user_id>/', views.UserLeaderboardRankView.as_view(), name='user-leaderboard-rank'),
    
    # 用户统计
    path('streak/', views.UserStreakView.as_view(), name='user-streak'),
    
    # 历史挑战
    path('history/', views.ChallengeHistoryView.as_view(), name='challenge-history'),
    
    # 管理端点
    path('generate-tomorrow/', views.generate_tomorrow_challenge_view, name='generate-tomorrow-challenge'),
]
