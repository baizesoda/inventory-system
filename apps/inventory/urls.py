"""库存模块路由表。"""
from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # 出入库流水
    path('records/', views.record_list, name='record_list'),
    path('records/create/', views.record_create, name='record_create'),
    path('records/<int:pk>/', views.record_detail, name='record_detail'),
    path('records/<int:pk>/delete/', views.record_delete, name='record_delete'),
    # 盘点
    path('checks/', views.check_list, name='check_list'),
    path('checks/create/', views.check_create, name='check_create'),
]
