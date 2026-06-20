"""
项目根 URL 路由表。

URL 总体结构:
    /                       -> 重定向到看板或登录页
    /accounts/              -> 账户应用(登录、退出、用户管理)
    /dashboard/             -> 数据统计看板
    /products/              -> 商品管理
    /inventory/             -> 库存操作
    /admin/                 -> Django 自带超级后台
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Django 自带超级管理后台
    path('admin/', admin.site.urls),

    # 根路径: 重定向到看板(未登录会被自动跳转到登录页)
    path('', RedirectView.as_view(pattern_name='dashboard:index', permanent=False)),

    # 各功能模块
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    path('products/', include('apps.products.urls', namespace='products')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
]

# 开发环境下提供静态文件与媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
