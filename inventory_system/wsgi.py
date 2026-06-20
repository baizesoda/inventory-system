"""
WSGI 配置 - 用于同步部署(如 Gunicorn/uWSGI + Nginx)。

部署命令示例:
    gunicorn inventory_system.wsgi:application --bind 0.0.0.0:8000
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')

application = get_wsgi_application()
