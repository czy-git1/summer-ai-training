# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Python Shop — 一个电商平台后端，基于 Django REST Framework，提供管理后台 API 和前台用户 API。

## 常用命令

### 开发服务器

```bash
# 启动开发服务器（默认 127.0.0.1:8000）
python manage.py runserver

# 指定端口和 IP
python manage.py runserver 0.0.0.0:8080

# 启动后自动打开浏览器（需要系统支持）
python manage.py runserver --noreload    # 禁用热重载（生产环境勿用）
```

### 数据库

```bash
# 为 myapp 创建新迁移文件
python manage.py makemigrations myapp

# 查看迁移 SQL（不实际执行）
python manage.py sqlmigrate myapp 0001

# 应用所有未执行的迁移
python manage.py migrate

# 查看迁移状态
python manage.py showmigrations

# 回滚 myapp 的所有迁移
python manage.py migrate myapp zero

# 重置数据库（SQLite 开发环境）
rm -f db.sqlite3 && python manage.py migrate
```

### 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行指定测试文件
python -m pytest tests/test_utils.py -v

# 运行指定测试类/方法
python -m pytest tests/test_views_admin.py::TestAdminLogin -v
python -m pytest tests/test_views_admin.py::TestAdminLogin::test_login_success -v

# 失败时立即停止（快速调试）
python -m pytest tests/ -x

# 只运行上次失败的测试
python -m pytest tests/ --lf

# 显示最慢的 5 个测试
python -m pytest tests/ --durations=5

# 覆盖率报告（需安装 pytest-cov）
pip install pytest-cov
python -m pytest tests/ --cov=myapp --cov-report=term-missing --cov-report=html
```

### Django 管理

```bash
# 系统检查（验证配置和模型）
python manage.py check

# 检查部署相关安全问题
python manage.py check --deploy

# Django shell（交互式 ORM 调试）
python manage.py shell

# 列出所有 URL 路由
python manage.py show_urls 2>/dev/null || python -c "
from django.urls import get_resolver
for p in get_resolver().url_patterns:
    print(p.pattern, p.name)
"

# 创建超级用户（Django 内置 admin）
python manage.py createsuperuser
```

### 依赖管理

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装测试依赖
pip install pytest pytest-django pytest-cov

# 导出当前环境依赖
pip freeze > requirements.txt

# 升级关键包（Python 3.14 环境）
pip install django==6.0.6 pymysql==1.2.0
```

### API 测试（curl）

```bash
# 测试前台分类列表
curl -s http://127.0.0.1:8000/myapp/index/classification/list | python -m json.tool

# 测试管理员登录
curl -s -X POST http://127.0.0.1:8000/myapp/admin/adminLogin \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"123456"}'

# 测试需要认证的端点（先登录获取 token，再传入）
curl -s http://127.0.0.1:8000/myapp/admin/overview/count \
  -H "ADMINTOKEN: <token>"

# 快速验证服务器是否响应
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/myapp/index/tag/list
```

### 代码质量

```bash
# 检查 Python 语法（不执行）
python -m py_compile myapp/utils.py

# 检查整个项目是否可导入（需配置 DJANGO_SETTINGS_MODULE）
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()
import myapp.views.admin, myapp.views.index
print('All imports OK')
"
```

## 环境注意事项

- **Python 3.14** 环境，依赖已从 `requirements.txt` 中的原始版本升级：
  - Django 3.2.11 → **6.0.6**（3.2 不兼容 Python 3.13+，`cgi` 模块已移除）
  - PyMySQL 1.0.2 → **1.2.0**（Django 6.0 要求 MySQLdb 版本 ≥ 2.2.1）
- 在 `server/__init__.py` 中通过 `pymysql.install_as_MySQLdb()` 进行 PyMySQL 猴子补丁
- 开发环境使用 **SQLite**（`db.sqlite3`），原项目配置的是 MySQL（`shop` 库，`root/4643830`）
- Django `USE_L10N` 已在 settings 中移除（Django 5.0+ 废弃）
- CSRF 中间件 `CsrfViewMiddleware` 已注释（这是纯 API 后端，使用基于令牌的认证，不使用 cookie）

## 架构

### URL 路由

```
/                           → Django 内置 admin（/admin/）
/myapp/                     → 所有业务 API（包含在 myapp/urls.py 中）
/myapp/admin/overview/...   → 仪表盘统计、系统信息
/myapp/admin/thing/...      → 商品 CRUD（还有 comment、classification、tag、order 等）
/myapp/admin/user/...       → 用户管理 + admin_login（无需认证的登录端点）
/myapp/admin/loginLog/...   → 登录日志（加上 opLog、errorLog）
/myapp/index/...            → 前台 API：classification、thing、user、comment、order、address、tag、notice
```

### 认证

- **管理员令牌**：`AdminTokenAuthtication` 通过 `HTTP_ADMINTOKEN` 头进行认证。验证用户存在且角色不是 `'2'`（前台用户）。应用于除 `admin_login` 外的所有 `/myapp/admin/` 端点。
- **用户令牌**：`TokenAuthtication` 通过 `HTTP_TOKEN` 头进行认证。验证用户角色是 `'0'`（普通用户），拒绝角色 `'1'` 或 `'3'` 的用户。
- 管理员登录（`/myapp/admin/adminLogin`）对密码进行 MD5 哈希处理，生成 `admin_token`，并记录 LoginLog。

### 视图层模式

- **管理后台视图**（`myapp/views/admin/`）：15 个模块，每个模块共享一个从 `base.py` 导入的 CRUD 模式。关键辅助函数：
  - `get_object_or_error(model_class, pk)` — 通过主键获取对象，若不存在则抛出 `ValueError`
  - `paginate_queryset(queryset, request)` — 从 `?page=&pageSize=` 查询参数中读取分页信息
  - `create_instance(serializer_class, data)` — 验证并保存，返回 `APIResponse`
  - `update_instance(serializer_class, instance, data)` — 更新已存在的实例
  - `delete_instance(model_class, pk)` — 通过主键删除
- **前台视图**（`myapp/views/index/`）：8 个模块，包含面向客户的端点。分类端点使用原始 SQL（左连接）来构建父子分类树。
- 通用响应格式：`{"code": 0, "msg": "成功信息", "data": {...}}`（code=0 表示成功，code=1 表示失败）

### 模型（15 个表，以 `b_` 为前缀）

核心业务：`User`、`Thing`（商品）、`Comment`、`Order`、`Address`
分类：`Classification`（树形结构，`pid=-1` 为根节点）、`Tag`
日志：`LoginLog`、`OpLog`、`ErrorLog`、`Record`、`OrderLog`
内容：`Banner`、`Ad`、`Notice`

用户角色：`'0'`=管理员、`'1'`=普通用户（在代码中为 `'2'`）、`'3'`=演示管理员
订单状态：`'1'`=待支付、`'2'`=已支付、`'7'`=已取消、`'3'`=延期

### 中间件

- `OpLogs`（`myapp/middlewares/LogMiddleware.py`）：记录每次请求的 IP、方法、路径和响应耗时（毫秒），通过 `OpLogSerializer` 持久化

### 权限

- `isDemoAdminUser(request)`：检查认证用户是否具有角色 `'3'`（演示管理员，拥有受限权限）

## 编码规范

- 遵循 **PEP 8** 规范（4 空格缩进、UTF-8 编码、LF 换行）。
- **命名约定**：
  - 模块/包：`snake_case`（如 `log_middleware.py`、`views/admin/`）
  - 类：`PascalCase`（如 `APIResponse`、`AdminTokenAuthtication`）
  - 函数/方法/变量：`snake_case`（如 `list_api`、`admin_token`、`page_size`）
  - 常量：`UPPER_SNAKE_CASE`（如 `_PROTECTED_USER_FIELDS`）
  - 私有函数：前缀 `_`（如 `_record_login_log`、`_partial_update_order`）
- **导入顺序**：标准库 → 第三方库（Django、DRF）→ 本地模块，各组之间空一行。多模块导入使用括号分组，避免反斜杠续行。
- 所有变量名使用有意义的英文单词，避免拼音或无意义缩写。

## 文档要求

- **每个 `.py` 文件**必须以中文模块级 docstring 开头，描述文件用途。
- **每个类**必须有中文 docstring，说明类的职责和主要属性。
- **每个函数/方法**必须有中文 docstring，使用三段式结构：
  ```
  功能描述（一句话）。

  参数:
      参数名: 参数说明。

  返回:
      返回值类型: 返回值说明。

  异常:
      异常类型: 何时抛出。
  ```
- **复杂逻辑**（如树形构建算法、SQL 拼接、状态机转换）必须添加行内中文注释解释意图。
- **保持注释与代码一致**：修改代码时必须同步更新注释。

## 类型注解

- **所有新函数**必须添加完整的类型注解（参数类型和返回值类型）。
- `HttpRequest` 类型的请求参数统一使用 `from django.http import HttpRequest`。
- 使用 `typing` 模块：`Any`、`Optional`、`dict[str, Any]`、`list[dict]` 等。
- 现有函数在重构时逐步补齐类型注解，不强制一次性补全。
- 类型注解中保留英文（Python 语法要求），如 `: int`、`: str`、`-> APIResponse`。

## 重构规则

- **优先提取重复代码**：发现 3 处以上相同逻辑时，提取为独立函数。参考 `myapp/views/admin/base.py` 中的 5 个共享辅助函数。
- **守卫子句优于嵌套**：先处理异常/边界情况并提前返回，减少 `if/else` 嵌套层级。
- **函数长度**：单个函数不超过 30 行（不含 docstring）。超出则拆分辅助函数。
- **保持功能完全不变**：重构时仅改进代码结构和可读性，不改变任何业务逻辑、API 响应格式或数据库查询。
- **变量重命名时**：确保搜索整个代码库，同步修改所有引用位置。

## 测试要求

- 使用 **pytest** + **pytest-django** 框架，配置文件 `pytest.ini`。
- 测试文件放在 `tests/` 目录，命名模式 `test_<模块名>.py`。
- 测试夹具（fixtures）统一在 `tests/conftest.py` 中定义。
- 每个核心函数至少覆盖 3 类场景：
  - **正常输入**：验证预期输出
  - **边界值**：空列表、None、零值、最大/最小值
  - **异常输入**：不存在的 ID、缺失必填参数、无权限、无效数据
- **测试类命名**：`Test<被测功能>`，测试方法命名：`test_<场景描述>`。
- 目标覆盖率 **≥ 80%**，当前 87 个测试全部通过。
- 运行命令：`python -m pytest tests/ -v`。

## 常用命令速查表

### 开发运行

| 命令 | 说明 |
|------|------|
| `python manage.py runserver` | 启动开发服务器 |
| `python manage.py runserver 0.0.0.0:8080` | 指定 IP 和端口 |
| `python manage.py shell` | 打开 Django 交互式 Shell |
| `python manage.py check` | 系统完整性检查 |

### 数据库

| 命令 | 说明 |
|------|------|
| `python manage.py makemigrations myapp` | 生成迁移文件 |
| `python manage.py migrate` | 执行迁移 |
| `python manage.py showmigrations` | 查看迁移状态 |
| `python manage.py migrate myapp zero` | 回滚所有迁移 |
| `python manage.py sqlmigrate myapp 0001` | 查看迁移 SQL |

### 测试

| 命令 | 说明 |
|------|------|
| `python -m pytest tests/ -v` | 运行全部测试 |
| `python -m pytest tests/test_utils.py -v` | 运行单个文件 |
| `python -m pytest tests/ -x` | 遇错立即停止 |
| `python -m pytest tests/ --lf` | 仅运行上次失败的 |
| `python -m pytest tests/ --durations=5` | 显示最慢的 5 个 |
| `python -m pytest tests/ --cov=myapp --cov-report=term-missing` | 覆盖率报告 |

### 认证 Token 速查

| 端点头 | 角色要求 | 说明 |
|---------|---------|------|
| `HTTP_ADMINTOKEN` | `role != '2'` | 管理后台认证 |
| `HTTP_TOKEN` | `role == '0'` | 前台用户认证 |

### 响应码速查

| code | 含义 |
|------|------|
| `0` | 成功 |
| `1` | 业务失败（参数错误、对象不存在、密码错误等） |
| HTTP 200 | 正常响应 |
| HTTP 403 | 认证失败 |
| HTTP 404 | 路由不存在 |

### 用户角色码

| role | 角色 | 可登录端 |
|------|------|---------|
| `'0'` | 管理员 | admin / index |
| `'2'` | 普通用户 | index 仅 |
| `'3'` | 演示管理员 | admin（受限） |

### 关键文件路径

| 路径 | 说明 |
|------|------|
| `server/settings.py` | Django 配置 |
| `server/urls.py` | 根 URL 路由 |
| `server/__init__.py` | PyMySQL 猴子补丁 |
| `myapp/models.py` | 15 个数据模型 |
| `myapp/serializers.py` | 18 个序列化器 |
| `myapp/urls.py` | 业务 API 路由 |
| `myapp/views/admin/base.py` | 管理后台 CRUD 共享辅助 |
| `myapp/views/admin/user.py` | 用户管理 + admin_login |
| `myapp/auth/authentication.py` | 令牌认证后端 |
| `myapp/middlewares/LogMiddleware.py` | 操作日志中间件 |
| `tests/conftest.py` | pytest 共享夹具 |
| `pytest.ini` | pytest 配置 |
