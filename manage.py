#!/usr/bin/env python
"""Django 的命令行管理工具。

运行开发服务器:    python manage.py runserver
执行数据库迁移:    python manage.py migrate
创建超级管理员:    python manage.py createsuperuser
启动应用:          python manage.py startapp <app_name>
"""
import os
import sys


def main():
    """运行管理命令的入口函数。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django, 请确认已安装 Django 并激活了虚拟环境。"
            "执行: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
