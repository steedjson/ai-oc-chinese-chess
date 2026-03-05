"""
Authentication URL routes.
"""

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, RefreshTokenView, CurrentUserView

app_name = 'auth'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('me/', CurrentUserView.as_view(), name='me'),
]
