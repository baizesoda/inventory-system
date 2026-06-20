# ============== Gunicorn 配置文件 ==============
# 文档: https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing

# 监听地址(由 Dockerfile / docker-compose 中的 --bind 覆盖)
bind = '0.0.0.0:8000'

# Worker 数量: 推荐 (2 * CPU 核数 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# 每个 Worker 处理的请求数, 达到后自动重启(防止内存泄漏)
max_requests = 1000
max_requests_jitter = 50

# 单个 Worker 处理请求的超时时间(秒)
timeout = 30

# 长连接 keep-alive 超时(秒)
keepalive = 5

# 日志输出位置
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# 进程名(便于 ps/top 识别)
proc_name = 'inventory_gunicorn'

# 静默预处理钩子
preload_app = True
