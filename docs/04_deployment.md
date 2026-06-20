# 04 - 部署说明文档

> 文档版本: v1.0
> 最后更新: 2026-06-20

本文档介绍库存管理系统的三种部署方式, 按推荐程度排序:

1. **Docker Compose 一键部署**(推荐生产环境)
2. **Gunicorn + Nginx 手动部署**(传统 Linux 服务器)
3. **本地开发模式**(学习测试用)

---

## 1. 系统要求

### 1.1 硬件最低配置

| 资源 | 最低 | 推荐 |
|------|------|------|
| CPU | 1 核 | 2 核 |
| 内存 | 1 GB | 2 GB |
| 磁盘 | 5 GB | 20 GB |

### 1.2 软件版本

| 组件 | 版本 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS / CentOS 8+ / Debian 12+ |
| Python | 3.11+ |
| MySQL | 8.0+(生产) / SQLite(开发) |
| Docker | 24.0+ |
| docker-compose | 2.20+ |
| Nginx | 1.25+(可选) |

---

## 2. 方式一: Docker Compose 部署(推荐)

### 2.1 准备环境

```bash
# Ubuntu 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable --now docker

# 验证
docker --version
docker compose version
```

### 2.2 配置环境变量

```bash
cd deploy
cp ../.env.example .env
vim .env
```

修改关键字段:

```ini
DJANGO_SECRET_KEY=请替换为50位以上的随机字符串
DJANGO_DEBUG=False
DB_ENGINE=mysql
DB_NAME=inventory_db
DB_PASSWORD=请使用强密码
```

生成随机 SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2.3 启动服务

```bash
cd deploy
docker compose up -d
```

首次启动会:
1. 拉取 MySQL / Nginx 镜像
2. 构建 Django 应用镜像
3. 执行数据库迁移
4. 初始化演示数据
5. 启动三个容器: `inventory_db` / `inventory_web` / `inventory_nginx`

### 2.4 验证部署

```bash
# 查看容器状态
docker compose ps

# 查看 Web 日志
docker compose logs -f web

# 浏览器访问
curl http://localhost
```

### 2.5 常用运维命令

```bash
# 停止
docker compose down

# 重启 Web 容器
docker compose restart web

# 进入 Web 容器执行命令
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# 查看数据库
docker compose exec db mysql -uroot -p inventory_db

# 重新构建(代码更新后)
docker compose up -d --build web
```

### 2.6 数据备份

```bash
# 备份 MySQL
docker compose exec db mysqldump -uroot -p inventory_db > backup_$(date +%Y%m%d).sql

# 备份媒体文件(用户上传)
docker cp inventory_web:/app/media ./media_backup_$(date +%Y%m%d)
```

恢复:

```bash
docker compose exec -T db mysql -uroot -p inventory_db < backup_20260620.sql
```

---

## 3. 方式二: Gunicorn + Nginx 手动部署

### 3.1 系统准备(Ubuntu 22.04)

```bash
# 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-venv python3-dev \
    build-essential libmariadb-dev pkg-config \
    nginx mysql-server
```

### 3.2 创建系统用户与目录

```bash
sudo useradd -m -s /bin/bash inventory
sudo mkdir -p /opt/inventory
sudo chown inventory:inventory /opt/inventory
```

### 3.3 拉取代码与安装依赖

```bash
sudo su - inventory
cd /opt/inventory
git clone <your-repo-url> .

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3.4 配置环境变量

```bash
cp .env.example .env
vim .env  # 修改 DB_ENGINE=mysql 等
```

### 3.5 初始化数据库

```bash
mysql -uroot -p <<'SQL'
CREATE DATABASE inventory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'inventory'@'localhost' IDENTIFIED BY '强密码';
GRANT ALL ON inventory_db.* TO 'inventory'@'localhost';
FLUSH PRIVILEGES;
SQL

python manage.py migrate
python manage.py init_demo
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 3.6 配置 Systemd 服务

创建 `/etc/systemd/system/inventory.service`:

```ini
[Unit]
Description=Inventory Management System (Gunicorn)
After=network.target mysql.service

[Service]
User=inventory
Group=inventory
WorkingDirectory=/opt/inventory
EnvironmentFile=/opt/inventory/.env
ExecStart=/opt/inventory/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/inventory.sock \
    --config /opt/inventory/deploy/gunicorn.conf.py \
    inventory_system.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动:

```bash
sudo systemctl daemon-reload
sudo systemctl enable inventory
sudo systemctl start inventory
sudo systemctl status inventory  # 检查状态
```

### 3.7 配置 Nginx

创建 `/etc/nginx/sites-available/inventory`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /opt/inventory/staticfiles/;
    }
    location /media/ {
        alias /opt/inventory/media/;
    }
    location / {
        proxy_pass http://unix:/run/inventory.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用并重启:

```bash
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 4. 方式三: 本地开发部署

### 4.1 Linux / macOS

```bash
bash deploy/start.sh
```

### 4.2 Windows

```cmd
deploy\start.bat
```

启动后访问: <http://127.0.0.1:8000>

---

## 5. HTTPS 配置(生产强烈推荐)

### 5.1 Let's Encrypt 免费证书

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

certbot 会自动修改 Nginx 配置, 添加 443 监听与证书路径。

### 5.2 settings.py 安全加固

在 `.env` 中追加:

```ini
DJANGO_DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

---

## 6. 日志与监控

### 6.1 应用日志

- Gunicorn 访问日志: `stdout`(Docker)/`/var/log/inventory/gunicorn.log`(手动)
- 操作审计日志: 数据库表 `accounts_operationlog`(系统内查看)

### 6.2 关键监控指标

- CPU / 内存: `docker stats` 或 `top`
- 数据库慢查询: `mysql.slow_log`
- HTTP 错误率: Nginx access log 中 5xx 占比

---

## 7. 升级流程

### 7.1 Docker 部署

```bash
cd deploy
git pull
docker compose up -d --build web
docker compose exec web python manage.py migrate
```

### 7.2 手动部署

```bash
sudo su - inventory
cd /opt/inventory
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit

sudo systemctl restart inventory
```

---

## 8. 常见部署问题排查

### Q1: Docker 构建报错 "Could not build wheel for mysqlclient"

A: 在 Dockerfile 中已经预装了 `default-libmysqlclient-dev` 与 `pkg-config`。若本地构建请确认系统已安装对应开发库。

### Q2: 容器启动后 502 Bad Gateway

A: 检查 web 容器是否启动成功:

```bash
docker compose logs web | tail -50
```

常见原因: SECRET_KEY 未设置、数据库连接失败、迁移未执行。

### Q3: 静态文件 404

A: 确认已执行 `python manage.py collectstatic --noinput`, 且 Nginx 配置中的 `alias` 路径指向 `STATIC_ROOT`。

### Q4: 上传图片后页面不显示

A: 检查 `MEDIA_ROOT` 是否有写入权限, Nginx 是否正确挂载了 `media/` 目录。
