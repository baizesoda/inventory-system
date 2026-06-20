# ============== 构建阶段 ==============
# 基础镜像: Python 3.11 官方精简版
FROM python:3.11-slim

# 设置环境变量, 避免 Python 写入 .pyc 文件并实时刷新日志
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖(mysqlclient 需要 pkg-config 和 libmysqlclient;
# Pillow 需要 libjpeg/zlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    pkg-config \
    default-libmysqlclient-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖文件, 利用 Docker 缓存层加速构建
COPY requirements.txt requirements-prod.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt -r requirements-prod.txt

# 拷贝项目代码
COPY . /app/

# 收集静态文件到 STATIC_ROOT
RUN python manage.py collectstatic --noinput || true

# 暴露端口(Gunicorn 默认监听 8000)
EXPOSE 8000

# 容器启动命令: 使用 Gunicorn 启动 WSGI 应用
CMD ["gunicorn", "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--config", "deploy/gunicorn.conf.py", \
     "inventory_system.wsgi:application"]
