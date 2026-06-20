"""看板模块路由表。"""
from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/trend/', views.trend_api, name='trend_api'),
]
