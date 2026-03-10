"""
URL configuration for chinese_chess project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/', include('games.urls')),
    path('api/v1/ai/', include('ai_engine.urls')),
    path('api/v1/matchmaking/', include('matchmaking.urls', namespace='matchmaking')),
    path('api/v1/ranking/', include('matchmaking.urls', namespace='ranking')),
    path('api/v1/puzzles/', include('puzzles.urls')),
    path('api/v1/daily-challenge/', include('daily_challenge.urls')),
    path('api/health/', include('health.urls')),
]
