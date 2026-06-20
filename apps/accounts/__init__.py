"""账户与权限管理模块。"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """账户应用配置。"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = '账户与权限'

    def ready(self):
        """应用启动时导入信号处理器。"""
        from . import signals  # noqa: F401
