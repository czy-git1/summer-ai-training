# COMMAND.md — Python Shop 命令速查手册

## 开发服务器

```bash
python manage.py runserver                    # 启动（127.0.0.1:8000）
python manage.py runserver 0.0.0.0:8080       # 指定 IP 和端口
python manage.py runserver --noreload         # 禁用热重载
```

## 数据库

```bash
python manage.py makemigrations myapp         # 生成迁移文件
python manage.py migrate                      # 执行迁移
python manage.py showmigrations               # 查看迁移状态
python manage.py sqlmigrate myapp 0001        # 查看迁移 SQL
python manage.py migrate myapp zero           # 回滚所有迁移
rm -f db.sqlite3 && python manage.py migrate  # 重置数据库（SQLite）
```

## 测试

```bash
python -m pytest tests/ -v                                        # 全部测试
python -m pytest tests/test_utils.py -v                           # 指定文件
python -m pytest tests/test_views_admin.py::TestAdminLogin -v     # 指定类
python -m pytest tests/test_views_admin.py::TestAdminLogin::test_login_success -v  # 指定方法
python -m pytest tests/ -x                                        # 遇错停止
python -m pytest tests/ --lf                                      # 仅上次失败
python -m pytest tests/ --durations=5                             # 最慢 5 个
python -m pytest tests/ --cov=myapp --cov-report=term-missing     # 覆盖率
python -m pytest tests/ --cov=myapp --cov-report=html             # HTML 覆盖率
```

## Django 管理

```bash
python manage.py check                       # 系统检查
python manage.py check --deploy              # 部署安全检查
python manage.py shell                       # 交互式 ORM Shell
python manage.py createsuperuser             # 创建超级用户
```

## 依赖

```bash
pip install -r requirements.txt              # 安装项目依赖
pip install pytest pytest-django pytest-cov  # 安装测试依赖
pip freeze > requirements.txt                # 导出环境依赖
```

## 关键包版本（Python 3.14 环境）

```bash
pip install django==6.0.6 pymysql==1.2.0
```

## API 快速测试

```bash
# 前台分类列表
curl http://127.0.0.1:8000/myapp/index/classification/list

# 管理员登录
curl -X POST http://127.0.0.1:8000/myapp/admin/adminLogin \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"123456"}'

# 管理后台（需认证）
curl http://127.0.0.1:8000/myapp/admin/overview/count \
  -H "ADMINTOKEN: <token>"

# 健康检查
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/myapp/index/tag/list
```

## 代码质量

```bash
python -m py_compile myapp/utils.py          # 单文件语法检查
python manage.py check                       # Django 完整性检查
```

## 认证头速查

| 端点头 | 角色 | 说明 |
|---------|------|------|
| `HTTP_ADMINTOKEN` | `role != '2'` | 管理后台 |
| `HTTP_TOKEN` | `role == '0'` | 前台用户 |

## 用户角色

| role | 角色 | 可登录 |
|------|------|--------|
| `'0'` | 管理员 | admin + index |
| `'2'` | 普通用户 | index |
| `'3'` | 演示管理员 | admin（受限） |

## 响应码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 失败（参数错误、对象不存在等） |
