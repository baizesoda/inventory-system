"""
Django 项目主配置包。

包含整个库存管理系统的全局设置项, 所有应用都通过此包进行加载。
子模块:
    - settings: 全局配置(数据库、中间件、模板、静态文件等)
    - urls:     根 URL 路由表
    - wsgi:     WSGI 部署入口(同步部署, 如 Gunicorn)
    - asgi:     ASGI 部署入口(异步部署, 如 Daphne)
"""
