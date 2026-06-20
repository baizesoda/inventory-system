"""数据统计看板模块。"""
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """看板应用配置。"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = '数据看板'
