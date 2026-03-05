"""
User URL routes.
"""

from django.urls import path
from .views import UserDetailView, ChangePasswordView

app_name = 'users'

urlpatterns = [
    path('<int:pk>/', UserDetailView.as_view(), name='detail'),
    path('<int:pk>/password/', ChangePasswordView.as_view(), name='change-password'),
]
