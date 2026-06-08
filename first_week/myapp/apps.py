"""myapp 模块的 Django 应用配置。

定义了 MyappConfig 类，供 Django 的应用注册表用于发现
和管理本应用的模型、信号及其他功能。
"""
from django.apps import AppConfig


class MyappConfig(AppConfig):
    """myapp Django 应用的配置类。

    属性:
        default_auto_field: 本应用中模型的默认主键字段类型。
        name: 指向应用包的 Python 点号路径。
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
