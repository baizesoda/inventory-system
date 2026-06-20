# 库存管理系统 (Inventory Management System)

> 基于 Django All-in-One 架构的中小型企业库存管理系统, 涵盖商品管理、出入库、盘点、数据看板与权限管理。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [演示账号](#演示账号)
- [项目结构](#项目结构)
- [文档导航](#文档导航)
- [常见问题](#常见问题)

---

## 功能特性

### 核心功能模块
- **商品管理** — 商品 SKU、分类、规格、单价、库存警戒线, 完整 CRUD 与搜索过滤
- **库存操作** — 入库 / 出库流水, 事务一致性保证, 撤销流水自动回滚库存
- **盘点管理** — 系统库存 vs 实际盘点, 自动生成差异调整流水
- **数据看板** — KPI 卡片 + 近 30 天出入库趋势折线图 + 分类饼图 + 低库存预警

### 辅助功能
- **用户认证** — 注册 / 登录 / 退出 / 修改个人资料 / 头像
- **角色权限(RBAC)** — 三种角色: 系统管理员 / 库管员 / 查看者
- **操作审计** — 所有关键操作记录到 OperationLog, 可追溯
- **Django Admin** — 内置超级后台, 便于数据维护

---

## 技术栈

| 层次 | 技术选型 |
|------|---------|
| 后端框架 | Django 5.0 (Python 3.11+) |
| 数据库 | SQLite(开发) / MySQL 8.0(生产) |
| 模板引擎 | Django Templates + Bootstrap 5 |
| 图表 | Chart.js 4.4 |
| 图标 | Bootstrap Icons |
| 应用服务器 | Gunicorn 22 |
| 反向代理 | Nginx 1.25 |
| 容器化 | Docker + docker-compose |

---

## 快速开始

### 方式一: 本地运行(开发模式)

```bash
# 1. 克隆 / 进入项目目录
cd inventory-system

# 2. (Linux/macOS) 一键启动
bash deploy/start.sh

# 2. (Windows) 一键启动
deploy\start.bat
```

脚本会自动完成: 创建虚拟环境 → 安装依赖 → 执行迁移 → 初始化演示数据 → 启动服务器。

浏览器访问: <http://127.0.0.1:8000>

### 方式二: Docker Compose 一键部署

```bash
cd deploy
docker compose up -d
```

部署完成后访问: <http://localhost>

### 方式三: 手动逐步启动

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py init_demo      # 生成演示数据
python manage.py createsuperuser  # (可选) 创建超级管理员
python manage.py runserver
```

---

## 演示账号

`init_demo` 命令会创建以下账号, 用于体验不同角色的权限差异:

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| `admin` | `admin123` | 系统管理员 | 所有功能 + 用户管理 |
| `keeper` | `keeper123` | 库管员 | 商品 / 库存 / 盘点增删改查 |
| `viewer` | `viewer123` | 查看者 | 所有数据只读 |
| `superadmin` | `admin123` | 超级管理员 | 可登录 Django Admin (`/admin/`) |

---

## 项目结构

```
inventory-system/
├── manage.py                  # Django 命令行入口
├── requirements.txt           # Python 依赖
├── README.md                  # 项目说明(本文件)
├── .env.example               # 环境变量示例
│
├── inventory_system/          # Django 项目配置包
│   ├── settings.py            # 全局配置
│   ├── urls.py                # 根 URL 路由
│   ├── wsgi.py / asgi.py      # 部署入口
│
├── apps/                      # 业务应用集合
│   ├── accounts/              # 账户与权限
│   ├── products/              # 商品管理
│   ├── inventory/             # 库存操作
│   └── dashboard/             # 数据看板
│
├── templates/                 # 全站模板
├── static/                    # 静态资源 (CSS/JS/图片)
│
├── deploy/                    # 部署相关
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── nginx.conf
│   ├── gunicorn.conf.py
│   ├── start.sh / start.bat   # 一键启动脚本
│
└── docs/                      # 文档
    ├── 01_architecture.md     # 架构设计
    ├── 02_database_design.md  # 数据库设计
    ├── 03_api_docs.md         # 接口文档
    ├── 04_deployment.md       # 部署说明
    └── 05_user_manual.md      # 用户手册
```

---

## 文档导航

- 项目架构设计 → [`docs/01_architecture.md`](docs/01_architecture.md)
- 数据库设计 → [`docs/02_database_design.md`](docs/02_database_design.md)
- API / URL 接口 → [`docs/03_api_docs.md`](docs/03_api_docs.md)
- 部署说明 → [`docs/04_deployment.md`](docs/04_deployment.md)
- 用户使用手册 → [`docs/05_user_manual.md`](docs/05_user_manual.md)

---

## 常见问题

**Q1: 启动报错 "No module named 'django'"?**
A: 请确认已激活虚拟环境(`source venv/bin/activate`)并执行 `pip install -r requirements.txt`。

**Q2: 切换到 MySQL 报错 "Access denied"?**
A: 检查 `.env` 文件中的 `DB_USER` / `DB_PASSWORD` 是否与 MySQL 实际配置一致。

**Q3: 上传商品图片不显示?**
A: 开发模式下 Django 会自动服务 `media/`, 生产环境需通过 Nginx 配置静态资源(已默认提供)。

**Q4: 如何重置演示数据?**
A: 删除 `db.sqlite3` 文件后重新执行 `python manage.py migrate && python manage.py init_demo`。

---

## License

MIT License © 2026
