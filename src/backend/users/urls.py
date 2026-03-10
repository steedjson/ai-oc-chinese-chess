"""
User URL routes.
"""

from django.urls import path
from .views import UserDetailView, ChangePasswordView, UserProfileView, UserStatsView, UserGamesView

app_name = 'users'

urlpatterns = [
    # 当前用户相关
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('me/stats/', UserStatsView.as_view(), name='user-stats'),
    
    # 指定用户相关
    path('<int:pk>/', UserDetailView.as_view(), name='detail'),
    path('<int:pk>/password/', ChangePasswordView.as_view(), name='change-password'),
    path('<int:pk>/stats/', UserStatsView.as_view(), name='user-stats-detail'),
    path('<int:pk>/games/', UserGamesView.as_view(), name='user-games'),
]
