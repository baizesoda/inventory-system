"""
ASGI 配置 - 用于异步部署(如 Daphne/Uvicorn, 支持 WebSocket)。

部署命令示例:
    daphne inventory_system.asgi:application --port 8000
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')

application = get_asgi_application()
