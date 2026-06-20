# 02 - 数据库设计文档

> 文档版本: v1.0
> 最后更新: 2026-06-20

## 1. 数据库选型

| 项目 | 开发环境 | 生产环境 |
|------|---------|---------|
| 数据库 | SQLite 3 | MySQL 8.0 |
| 切换方式 | 默认 | 环境变量 `DB_ENGINE=mysql` |
| 字符集 | UTF-8 | utf8mb4(支持 emoji) |

切换通过 `inventory_system/settings.py` 中的 `if os.environ.get('DB_ENGINE') == 'mysql'` 实现。

---

## 2. ER 图

```
┌──────────────┐  1     N ┌──────────────┐
│   Category   │◄─────────│   Product    │
│   (分类)     │          │   (商品)     │
└──────────────┘          └──────┬───────┘
       │                         │ 1
       │                         │
       │                         │ N
       │                  ┌──────┴───────┐
       │                  │ InOutRecord  │
       │                  │ (出入库流水) │
       │                  └──────┬───────┘
       │                         │
       │                         │
       │                  ┌──────┴───────┐
       │                  │  StockCheck  │
       │                  │  (盘点记录)  │
       │                  └──────────────┘
       │
┌──────┴───────┐  1     1 ┌──────────────┐  N     1 ┌──────────────┐
│  UserProfile │◄─────────│     User     │──────────►│OperationLog │
│  (用户档案)  │          │ (Django内置) │           │ (操作日志)   │
└──────────────┘          └──────────────┘           └──────────────┘
```

---

## 3. 表结构详细设计

### 3.1 `auth_user` (Django 内置, 略作说明)

Django 自带的用户表, 不需要重新定义。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 自增主键 |
| username | VARCHAR(150) UNIQUE | 登录用户名 |
| password | VARCHAR(128) | PBKDF2 哈希密码 |
| email | VARCHAR(254) | 邮箱 |
| first_name | VARCHAR(150) | 姓名 |
| is_active | BOOLEAN | 账号启用状态 |
| is_staff | BOOLEAN | 可登录 admin |
| is_superuser | BOOLEAN | 超级管理员 |
| date_joined | DATETIME | 注册时间 |
| last_login | DATETIME | 最后登录时间 |

### 3.2 `accounts_userprofile` - 用户档案

**用途**: 扩展 Django User, 存储角色等业务字段。一对一关系。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| user_id | BIGINT | UNIQUE, FK→auth_user.id, ON DELETE CASCADE | 关联用户 |
| role | VARCHAR(20) | NOT NULL, 默认 'viewer' | 角色: admin/keeper/viewer |
| phone | VARCHAR(20) | 可空 | 联系电话 |
| avatar | VARCHAR(100) | 可空 | 头像路径 |
| created_at | DATETIME | auto_now_add | 创建时间 |

**索引**: `user_id` (UNIQUE)

### 3.3 `products_category` - 商品分类

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 分类名称 |
| code | VARCHAR(20) | UNIQUE, NOT NULL | 分类编码 |
| description | TEXT | 可空 | 分类描述 |
| created_at | DATETIME | auto_now_add | 创建时间 |

### 3.4 `products_product` - 商品

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| sku | VARCHAR(50) | UNIQUE, NOT NULL | 商品唯一编号 |
| name | VARCHAR(100) | NOT NULL | 商品名称 |
| category_id | BIGINT | FK→products_category.id, ON DELETE PROTECT | 所属分类 |
| specification | VARCHAR(100) | 可空 | 规格型号 |
| unit | VARCHAR(10) | 默认 '件' | 计量单位 |
| price | DECIMAL(10,2) | NOT NULL, ≥ 0 | 销售单价 |
| cost | DECIMAL(10,2) | 默认 0, ≥ 0 | 成本单价 |
| stock | INTEGER | 默认 0, ≥ 0 | **当前库存(由流水维护)** |
| safety_stock | INTEGER | 默认 10 | 安全警戒库存 |
| image | VARCHAR(100) | 可空 | 商品图片 |
| remark | TEXT | 可空 | 备注 |
| is_active | BOOLEAN | 默认 TRUE | 是否在用 |
| created_at | DATETIME | auto_now_add | 创建时间 |
| updated_at | DATETIME | auto_now | 更新时间 |

**索引**: `name`, `category_id`, `sku`(UNIQUE)

> **设计说明**: `stock` 字段虽然在 Product 表中, 但应用层 **禁止直接修改**,
> 必须通过 `inventory` 模块的 InOutRecord 流水修改, 以保证可追溯。

### 3.5 `inventory_inoutrecord` - 出入库流水

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| product_id | BIGINT | FK→products_product.id, ON DELETE PROTECT | 商品 |
| type | VARCHAR(10) | NOT NULL | 'inbound'(入库) / 'outbound'(出库) |
| quantity | INTEGER | NOT NULL, ≥ 1 | 数量 |
| unit_price | DECIMAL(10,2) | 默认 0 | 单价 |
| operator_id | BIGINT | FK→auth_user.id, ON DELETE SET NULL | 操作人 |
| remark | VARCHAR(200) | 可空 | 备注 |
| created_at | DATETIME | 默认 now | 操作时间 |

**索引**: `(type, created_at)` 复合索引, `product_id`

### 3.6 `inventory_stockcheck` - 库存盘点记录

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| product_id | BIGINT | FK→products_product.id | 商品 |
| recorded_stock | INTEGER | NOT NULL | 系统记录库存 |
| actual_stock | INTEGER | NOT NULL | 实际盘点库存 |
| difference | INTEGER | NOT NULL (自动计算) | 差异 = actual - recorded |
| operator_id | BIGINT | FK→auth_user.id, ON DELETE SET NULL | 盘点人 |
| remark | TEXT | 可空 | 备注 |
| created_at | DATETIME | auto_now_add | 盘点时间 |

### 3.7 `accounts_operationlog` - 操作日志

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | 自增 | 主键 |
| user_id | BIGINT | FK→auth_user.id, ON DELETE SET NULL | 操作人 |
| action | VARCHAR(20) | NOT NULL | create/update/delete/inbound/outbound/login/logout |
| target | VARCHAR(200) | 可空 | 操作对象描述 |
| detail | TEXT | 可空 | 详细描述 |
| created_at | DATETIME | auto_now_add | 操作时间 |

---

## 4. 数据完整性约束

### 4.1 外键级联策略

| 关系 | 策略 | 理由 |
|------|------|------|
| User → UserProfile | CASCADE | 用户删除时档案一并删除 |
| Product → Category | PROTECT | 防止误删仍有商品的分类 |
| InOutRecord → Product | PROTECT | 防止误删有流水记录的商品 |
| InOutRecord → User | SET NULL | 用户删除后流水保留, 操作人置空 |

### 4.2 业务约束(应用层)

- 商品 `price`、`cost`、`stock`、`safety_stock` 均 ≥ 0(`MinValueValidator`)
- 出库 `quantity` ≤ 商品当前 `stock`(视图层校验 + 事务层二次校验)
- 删除分类前必须先清空该分类下的商品

---

## 5. 事务与并发

### 5.1 关键事务边界

`apps/inventory/views.py` 中以下操作都在 `transaction.atomic()` 中执行:

- **新增出入库**: SELECT FOR UPDATE → 修改库存 → 写流水 → 写日志
- **撤销流水**: SELECT FOR UPDATE → 反向调整库存 → 删除流水
- **盘点差异调整**: 写盘点记录 → 写调整流水 → 同步库存

### 5.2 乐观锁 vs 悲观锁

由于库存操作对一致性要求高, 选用 **悲观锁** (`select_for_update()`), 在事务内对 Product 行加锁, 避免并发场景下库存超扣。

---

## 6. 数据库迁移

Django 通过 `makemigrations` 与 `migrate` 管理 Schema 变更:

```bash
# 模型变更后生成迁移文件
python manage.py makemigrations

# 应用迁移到数据库
python manage.py migrate
```

迁移文件位于每个 app 的 `migrations/` 目录, 应当提交到版本库。

---

## 7. 初始数据

通过自定义管理命令 `init_demo` 创建:

- 3 个演示用户(对应 3 种角色)
- 1 个超级管理员(用于 Django Admin)
- 4 个商品分类、12 个商品
- 30 天的随机出入库流水(供看板展示)

```bash
python manage.py init_demo
```
