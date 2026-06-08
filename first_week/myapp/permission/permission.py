"""
myapp Django 应用的权限辅助函数。

提供检查用户角色和权限的工具函数，
特别是用于区分演示管理员帐户。
"""

from django.http import HttpRequest

from myapp.models import User


def isDemoAdminUser(request: HttpRequest) -> bool:
    """检查请求是否来自演示管理员用户。

    演示管理员用户通过角色 ``'3'`` 以及在 ``HTTP_ADMINTOKEN``
    头中携带有效的管理员令牌来识别。

    参数:
        request: 传入的 HTTP 请求对象。

    返回:
        bool: 如果请求来自演示管理员用户则返回 True，否则返回 False。
    """
    admin_token = request.META.get("HTTP_ADMINTOKEN")
    users = User.objects.filter(admin_token=admin_token)

    if len(users) == 0:
        return False

    user = users[0]
    if user.role == '3':
        print('演示帐号===>')
        return True

    return False
