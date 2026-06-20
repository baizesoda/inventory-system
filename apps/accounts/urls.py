"""
账户模块路由表。
"""
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:pk>/toggle/', views.user_toggle_active_view, name='user_toggle'),
    path('logs/', views.operation_log_view, name='logs'),
]
