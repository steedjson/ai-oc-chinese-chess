"""
Matchmaking URL routes.
"""

from django.urls import path
from .views import StartMatchmakingView, CancelMatchmakingView, MatchStatusView

app_name = 'matchmaking'

urlpatterns = [
    path('start/', StartMatchmakingView.as_view(), name='start'),
    path('cancel/', CancelMatchmakingView.as_view(), name='cancel'),
    path('status/', MatchStatusView.as_view(), name='status'),
]
