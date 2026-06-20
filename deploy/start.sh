#!/usr/bin/env bash
# ============== 库存管理系统 - 一键启动脚本 ==============
# 用途: 在本地开发或单机 Linux 服务器上快速启动系统
#
# 用法:
#   bash deploy/start.sh          # 开发模式(SQLite + runserver)
#   bash deploy.sh prod           # 生产模式(MySQL + Gunicorn)

set -e
cd "$(dirname "$0")/.."

echo "[1/5] 检查 Python 环境..."
command -v python3 >/dev/null 2>&1 || { echo "未检测到 python3, 请先安装"; exit 1; }

echo "[2/5] 创建虚拟环境(若不存在)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "[3/5] 安装依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "[4/5] 执行数据库迁移..."
python manage.py migrate --noinput

echo "[5/5] 初始化演示数据(若数据库为空)..."
python manage.py init_demo || true

MODE="${1:-dev}"
if [ "$MODE" = "prod" ]; then
    echo "============================================"
    echo " 生产模式启动 (Gunicorn @ :8000)"
    echo "============================================"
    python manage.py collectstatic --noinput
    gunicorn --bind 0.0.0.0:8000 --workers 3 \
        --config deploy/gunicorn.conf.py \
        inventory_system.wsgi:application
else
    echo "============================================"
    echo " 开发模式启动 (runserver @ :8000)"
    echo " 访问 http://127.0.0.1:8000"
    echo "============================================"
    python manage.py runserver 0.0.0.0:8000
fi
