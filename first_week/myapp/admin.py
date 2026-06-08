"""myapp 应用的 Django admin 站点配置。

将核心业务模型（Classification、Tag、Thing、User、Comment）
注册到 Django 管理界面，以便进行便捷的数据管理。
"""
from django.contrib import admin

from myapp.models import Classification, Thing, Tag, User, Comment

admin.site.register(Classification)
admin.site.register(Tag)
admin.site.register(Thing)
admin.site.register(User)
admin.site.register(Comment)
