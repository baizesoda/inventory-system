# 03 - 接口 (URL) 文档

> 文档版本: v1.0
> 最后更新: 2026-06-20

本项目采用 **服务端渲染 + 表单提交** 模式, 大部分接口返回 HTML 页面。所有写操作要求登录并具备相应角色权限。

---

## 1. 接口约定

### 1.1 通用规则

- 所有页面均要求登录(除 `/accounts/login` 与 `/accounts/register`)
- POST 请求必须携带 CSRF Token: `{% csrf_token %}` 或 HTTP Header `X-CSRFToken`
- 列表页支持 GET 查询参数过滤
- 错误提示通过 Django messages 框架在页面顶部显示

### 1.2 HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功(返回 HTML 或 JSON) |
| 302 | 重定向(登录成功、权限不足时) |
| 403 | CSRF 校验失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 1.3 权限说明

文档中权限标记含义:

- 🔓 **公开**: 无需登录
- 👤 **登录**: 任意登录用户
- ✏️ **编辑**: 管理员或库管员(`@editor_required`)
- 👑 **管理员**: 仅系统管理员(`@admin_required`)

---

## 2. 账户模块 (`/accounts/`)

| 方法 | URL | 权限 | 说明 |
|------|-----|------|------|
| GET/POST | `/accounts/login/` | 🔓 | 登录 |
| GET/POST | `/accounts/register/` | 🔓 | 注册 |
| GET | `/accounts/logout/` | 👤 | 退出登录 |
| GET/POST | `/accounts/profile/` | 👤 | 查看/修改个人资料 |
| GET | `/accounts/users/` | 👑 | 用户列表 |
| GET/POST | `/accounts/users/<pk>/edit/` | 👑 | 编辑用户 |
| POST | `/accounts/users/<pk>/toggle/` | 👑 | 启用/停用账号 |
| GET | `/accounts/logs/` | 👤 | 操作日志(查看者只看本人) |

### 2.1 登录接口

**请求** `POST /accounts/login/`

```
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123&csrfmiddlewaretoken=...
```

**响应**
- 成功: 302 重定向到 `?next=` 指定的 URL 或 `/dashboard/`
- 失败: 200 重新渲染登录页, 顶部红色提示"用户名或密码错误"

### 2.2 用户管理 - 修改角色

**请求** `POST /accounts/users/3/edit/`

```
username=keeper&email=keeper@example.com&first_name=张三&role=keeper&is_active=on&csrfmiddlewaretoken=...
```

**响应**: 302 重定向到 `/accounts/users/`

---

## 3. 商品模块 (`/products/`)

| 方法 | URL | 权限 | 说明 |
|------|-----|------|------|
| GET | `/products/` | 👤 | 商品列表(支持查询参数过滤) |
| GET | `/products/create/` | ✏️ | 新增商品表单 |
| POST | `/products/create/` | ✏️ | 提交新增 |
| GET | `/products/<pk>/` | 👤 | 商品详情 |
| GET | `/products/<pk>/edit/` | ✏️ | 编辑商品表单 |
| POST | `/products/<pk>/edit/` | ✏️ | 提交修改 |
| GET | `/products/<pk>/delete/` | ✏️ | 删除确认页 |
| POST | `/products/<pk>/delete/` | ✏️ | 确认删除 |
| GET | `/products/categories/` | 👤 | 分类列表 |
| GET/POST | `/products/categories/create/` | ✏️ | 新增分类 |
| GET/POST | `/products/categories/<pk>/edit/` | ✏️ | 编辑分类 |
| GET/POST | `/products/categories/<pk>/delete/` | ✏️ | 删除分类 |

### 3.1 商品列表过滤参数

`GET /products/?keyword=键盘&category=2&low_stock_only=on&page=1`

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | SKU 或商品名称模糊匹配 |
| `category` | int | 分类 ID |
| `low_stock_only` | bool | 仅显示低库存(<=safety_stock)商品 |
| `page` | int | 页码 |

### 3.2 商品新增表单字段

`POST /products/create/`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sku | string | ✅ | SKU 编号, 自动转大写 |
| name | string | ✅ | 商品名称 |
| category | int | ✅ | 分类 ID |
| specification | string | - | 规格型号 |
| unit | string | - | 单位, 默认"件" |
| price | decimal | ✅ | 销售单价 |
| cost | decimal | - | 成本价 |
| safety_stock | int | - | 安全库存 |
| image | file | - | 商品图片 |
| remark | string | - | 备注 |
| is_active | bool | - | 是否启用 |

---

## 4. 库存模块 (`/inventory/`)

| 方法 | URL | 权限 | 说明 |
|------|-----|------|------|
| GET | `/inventory/records/` | 👤 | 出入库流水列表 |
| GET/POST | `/inventory/records/create/` | ✏️ | 新增出入库 |
| GET | `/inventory/records/<pk>/` | 👤 | 流水详情 |
| GET/POST | `/inventory/records/<pk>/delete/` | ✏️ | 撤销流水 |
| GET | `/inventory/checks/` | 👤 | 盘点列表 |
| GET/POST | `/inventory/checks/create/` | ✏️ | 新增盘点 |

### 4.1 流水列表过滤

`GET /inventory/records/?keyword=Water&type=outbound&date_from=2026-06-01&date_to=2026-06-30`

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | SKU/名称/备注 |
| `type` | enum | `inbound` / `outbound` |
| `date_from` | date | 开始日期 |
| `date_to` | date | 结束日期 |
| `page` | int | 页码 |

### 4.2 新增出入库

`POST /inventory/records/create/`

```
product=5&type=inbound&quantity=100&unit_price=28.00&remark=采购入库&csrfmiddlewaretoken=...
```

**业务规则**:
- 出库时 `quantity` 必须 ≤ `product.stock`, 否则返回错误页
- 操作在 `transaction.atomic()` 中执行
- 同时写入 `OperationLog`

---

## 5. 看板模块 (`/dashboard/`)

| 方法 | URL | 权限 | 说明 |
|------|-----|------|------|
| GET | `/dashboard/` | 👤 | 看板首页(HTML) |
| GET | `/dashboard/api/trend/?days=30` | 👤 | 趋势数据 JSON |

### 5.1 趋势数据接口

**请求** `GET /dashboard/api/trend/?days=7`

**响应** `200 OK`

```json
{
  "days": ["06-01", "06-02", "06-03", "..."],
  "in_qty":  [10, 25, 0, 30, "..."],
  "out_qty": [5,  15, 8, 12, "..."]
}
```

字段说明:
- `days`: 日期标签数组(MM-DD 格式)
- `in_qty`: 对应日期的入库数量
- `out_qty`: 对应日期的出库数量

---

## 6. Django 超级管理后台

| URL | 说明 |
|-----|------|
| `/admin/` | Django 自带超级后台(仅 is_staff=True 用户可登录) |
| `/admin/auth/user/` | 用户管理 |
| `/admin/products/product/` | 商品管理 |
| `/admin/products/category/` | 分类管理 |
| `/admin/inventory/inoutrecord/` | 流水管理 |
| `/admin/accounts/operationlog/` | 操作日志(只读) |

---

## 7. 错误处理

### 7.1 业务错误示例

**出库超库存**

```
POST /inventory/records/create/
```

响应: 200(重新渲染表单页), 错误信息显示在表单上方:
```
出库失败: 当前库存仅剩 5, 不足以出库 100。
```

### 7.2 权限不足

未登录用户访问需要登录的页面 → 302 重定向到 `/accounts/login/?next=/原URL/`

登录但无权限用户(如 viewer 访问 `/products/create/`)→ 302 重定向到 `/dashboard/`, 提示:
```
权限不足, 无法执行此操作。
```

---

## 8. 后续 RESTful API 演进建议

若需对接移动端或第三方系统, 可在保持现有 View 不变的前提下, 增加以下路由:

```
/api/v1/auth/login/           (POST)   - 返回 Token
/api/v1/products/             (GET, POST)
/api/v1/products/<pk>/        (GET, PUT, DELETE)
/api/v1/inventory/records/    (GET, POST)
/api/v1/dashboard/summary/    (GET)
```

推荐使用 `Django REST Framework`, 直接复用现有 Model 与业务逻辑。
