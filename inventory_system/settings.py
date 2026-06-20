"""
Django 项目的全局配置文件。

包含以下核心配置项:
    - 已安装应用 INSTALLED_APPS
    - 中间件 MIDDLEWARE
    - 模板引擎 TEMPLATES
    - 数据库 DATABASES
    - 静态文件与媒体文件 STATIC / MEDIA
    - 认证与权限 AUTH
    - 国际化与本地化
"""
import os
from pathlib import Path

# 项目根目录(BASE_DIR = .../inventory_system/)
BASE_DIR = Path(__file__).resolve().parent.parent

# ============== 基础配置 ==============
# 安全警告: 生产环境请务必设置为 False, 并使用随机生成的密钥
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-please-change-this-key-in-production-env'
)
# 调试模式, 生产环境必须为 False
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
# 允许访问的主机, 生产环境请改为实际域名或 IP
ALLOWED_HOSTS = ['*']

# ============== 应用定义 ==============
INSTALLED_APPS = [
    # Django 内置应用
    'django.contrib.admin',          # 后台管理
    'django.contrib.auth',           # 用户认证
    'django.contrib.contenttypes',   # 内容类型框架
    'django.contrib.sessions',       # 会话管理
    'django.contrib.messages',       # 消息框架
    'django.contrib.staticfiles',    # 静态文件服务
    'django.contrib.humanize',       # 数字/日期人类可读过滤器
    # 项目自有应用
    'apps.accounts.AccountsConfig',   # 账户与权限管理
    'apps.products.ProductsConfig',   # 商品管理模块
    'apps.inventory.InventoryConfig', # 库存操作模块
    'apps.dashboard.DashboardConfig', # 数据统计看板
]

# ============== 中间件 ==============
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inventory_system.urls'

# ============== 模板配置 ==============
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 模板目录, 全局模板放在项目根 templates 文件夹
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'inventory_system.wsgi.application'
ASGI_APPLICATION = 'inventory_system.asgi.application'

# ============== 数据库配置 ==============
# 默认使用 SQLite(开发环境零配置), 生产环境可通过环境变量切换为 MySQL
if os.environ.get('DB_ENGINE') == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'inventory_db'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============== 密码校验规则 ==============
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============== 国际化 ==============
LANGUAGE_CODE = 'zh-hans'  # 简体中文
TIME_ZONE = 'Asia/Shanghai'  # 东八区
USE_I18N = True
USE_TZ = False  # 使用本地时间, 便于业务报表

# ============== 静态文件 ==============
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectfast 输出目录

# ============== 媒体文件(用户上传) ==============
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============== 主键字段类型 ==============
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============== 登录重定向 ==============
LOGIN_URL = 'accounts:login'           # 未登录用户跳转的登录页
LOGIN_REDIRECT_URL = 'dashboard:index'  # 登录成功后跳转首页
LOGOUT_REDIRECT_URL = 'accounts:login'  # 退出后跳转登录页

# ============== 分页大小 ==============
PAGE_SIZE = 10  # 列表页默认每页显示条数

# ============== 默认角色名称(用于初始化权限) ==============
ROLE_ADMIN = 'admin'      # 系统管理员: 所有权限
ROLE_KEEPER = 'keeper'    # 库管员: 商品与库存操作权限
ROLE_VIEWER = 'viewer'    # 普通查看者: 只读权限
