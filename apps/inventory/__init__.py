"""库存操作模块。"""
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """库存应用配置。"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = '库存操作'
