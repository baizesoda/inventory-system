# 01 - 项目架构设计文档

> 文档版本: v1.0
> 最后更新: 2026-06-20

## 1. 架构概述

本项目采用 **All-in-One (单体全栈)** 架构模式, 即前后端代码统一在 Django 项目内, 前端通过 Django 模板引擎服务端渲染 HTML 页面。

### 1.1 架构选型理由

| 选项 | 优点 | 缺点 | 是否选用 |
|------|------|------|---------|
| All-in-One (Django) | 开发快、部署简单、运维成本低 | 单体扩展性受限 | ✅ |
| 前后端分离 (Vue/React + API) | 前端体验好、易扩展 | 开发与运维复杂度高 | ✗ |

**选型依据**: 库存管理属于功能集中的业务系统, 团队规模小, 用户量可控, All-in-One 模式能最大化开发效率。

### 1.2 高层架构图

```
┌─────────────────────────────────────────────────┐
│                  用户浏览器                       │
│        (Bootstrap 5 + Chart.js + HTML)           │
└───────────────────┬─────────────────────────────┘
                    │ HTTP / HTTPS
                    ▼
┌─────────────────────────────────────────────────┐
│              Nginx (反向代理)                    │
│  - 静态/媒体文件直接服务                          │
│  - 动态请求转发到 Gunicorn                        │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          Gunicorn (应用服务器)                   │
│          多 worker 进程, 同步 WSGI               │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│                Django 5.0                        │
│  ┌─────────────────────────────────────────┐    │
│  │  MIDDLEWARE (认证 / CSRF / 会话 / ...)   │    │
│  ├─────────────────────────────────────────┤    │
│  │  URL Router → View                      │    │
│  │  ┌──────┬──────┬──────────┬─────────┐   │    │
│  │  │accounts│products│inventory│dashboard│  │    │
│  │  └──────┴──────┴──────────┴─────────┘   │    │
│  ├─────────────────────────────────────────┤    │
│  │  ORM (Model)                            │    │
│  └─────────────────────────────────────────┘    │
└───────────────────┬─────────────────────────────┘
                    │ SQL
                    ▼
┌─────────────────────────────────────────────────┐
│       数据库(SQLite / MySQL 8.0)                │
└─────────────────────────────────────────────────┘
```

---

## 2. 分层架构

系统遵循经典的三层架构, 自上而下:

### 2.1 表现层 (Presentation Layer)
- **技术**: Django Template + Bootstrap 5
- **职责**: 渲染 HTML、接收用户输入、显示消息提示
- **位置**: `templates/` 目录

### 2.2 业务逻辑层 (Business Layer)
- **技术**: Django View + Form
- **职责**: 处理业务规则(如出库时校验库存、撤销流水时回滚库存)
- **位置**: `apps/*/views.py`、`apps/*/forms.py`
- **关键设计**: 出入库与盘点操作使用 `transaction.atomic()` 保证事务一致性

### 2.3 数据访问层 (Data Access Layer)
- **技术**: Django ORM
- **职责**: 与数据库交互
- **位置**: `apps/*/models.py`

---

## 3. 模块划分

按业务领域将系统拆分为 4 个松耦合的 Django App:

| App | 主要职责 | 关键 Model |
|-----|---------|-----------|
| `accounts` | 用户、角色、权限、操作日志 | `UserProfile`, `OperationLog` |
| `products` | 商品、分类管理 | `Product`, `Category` |
| `inventory` | 出入库流水、盘点 | `InOutRecord`, `StockCheck` |
| `dashboard` | 数据统计与可视化 | (无独立 Model, 聚合其他模块数据) |

### 模块依赖关系

```
dashboard ─── 读取 ───► products
                       ──► inventory
                       ──► accounts
inventory  ─── 关联 ───► products
                       ──► accounts(User)
products   ─── 关联 ───► (无外部依赖)
accounts   ─── 扩展 ───► Django auth.User
```

---

## 4. 权限架构 (RBAC)

### 4.1 角色定义

| 角色标识 | 名称 | 权限范围 |
|---------|------|---------|
| `admin` | 系统管理员 | 全部功能 + 用户管理 + 角色分配 |
| `keeper` | 库管员 | 商品 / 分类 / 出入库 / 盘点 CRUD |
| `viewer` | 查看者 | 所有列表与详情只读 |

### 4.2 实现机制

权限通过两个层次实现:

1. **认证层**: `@login_required` (Django 内置) - 强制登录
2. **授权层**: `@role_required(*roles)` / `@editor_required` (自定义装饰器) - 按角色判断

装饰器位置: `apps/accounts/decorators.py`。装饰器内部读取 `request.user.profile.role` 字段, 命中允许角色才执行视图, 否则重定向到看板并提示"权限不足"。

### 4.3 超级管理员

Django 内置的 `is_superuser=True` 用户拥有全部权限, 不受角色装饰器限制, 主要用于登录 `/admin/` 后台。

---

## 5. 关键业务流程

### 5.1 出库流程(事务一致性)

```
用户提交出库表单
       │
       ▼
┌──────────────────────────────┐
│ 1. 表单校验(quantity > 0)    │
│ 2. 业务校验(quantity ≤ stock)│
└──────────────┬───────────────┘
               │ 通过
               ▼
┌──────────────────────────────┐
│ transaction.atomic() {       │
│   3. SELECT ... FOR UPDATE   │  ← 行锁防止并发超扣
│   4. 二次校验库存            │
│   5. product.stock -= qty    │
│   6. product.save()          │
│   7. InOutRecord.create()    │
│   8. OperationLog.create()   │
│ }                            │
└──────────────────────────────┘
```

### 5.2 撤销流水(库存回滚)

```
点击"撤销"
       │
       ▼
transaction.atomic() {
  product = SELECT_FOR_UPDATE
  if (原流水为入库)  product.stock -= qty
  else              product.stock += qty
  product.save()
  record.delete()
}
```

### 5.3 盘点差异调整

```
录入实际库存
       │
       ▼
计算 difference = actual - recorded
       │
       ▼ (若 difference ≠ 0)
自动生成 InOutRecord(type=inbound|outbound)
同步 product.stock = actual
```

---

## 6. 安全设计

| 风险 | 防护措施 |
|------|---------|
| CSRF | Django `CsrfViewMiddleware`, 所有 POST 表单必须包含 `{% csrf_token %}` |
| SQL 注入 | 全部使用 ORM, 无原始 SQL 拼接 |
| XSS | Django 模板默认 HTML 转义 |
| 密码泄露 | 使用 PBKDF2 哈希存储; 校验强密码(`AUTH_PASSWORD_VALIDATORS`) |
| 越权访问 | 视图层 `@role_required` + 模板层 `{% if %}` 双重控制 |
| 文件上传 | `ImageField` 校验图片格式; 生产通过 Nginx 限速与大小限制 |
| Session 劫持 | `SessionMiddleware` 使用签名 Cookie, HTTPS 部署时设置 `Secure` 标志 |

---

## 7. 可扩展性

虽然是 All-in-One 单体, 但代码组织上预留了扩展空间:

- **拆分前后端**: View 已经返回上下文, 只需补充 JSON 序列化即可改造为 RESTful API
- **接入消息队列**: `OperationLog` 写入可异步化(Celery)
- **接入缓存**: 看板的 KPI 聚合可加 Redis 缓存, 减轻数据库压力
- **多租户**: 给 Model 增加 `tenant_id` 字段即可演进为 SaaS

---

## 8. 性能考量

- 列表页统一分页(默认每页 10 条, 可在 `settings.PAGE_SIZE` 调整)
- 外键查询使用 `select_related('category')` 减少 N+1
- 看板聚合使用 `Sum` / `Count` / `TruncDate` 在数据库端完成
- 静态文件由 Nginx 直接服务, 不经过 Python
