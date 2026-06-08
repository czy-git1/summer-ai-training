"""
myapp Django 应用的认证后端。

定义了基于令牌的认证类，用于管理后台和前端 API 端点，
通过 User 模型上的自定义 token 字段进行验证。
"""

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request

from myapp.models import User


class AdminTokenAuthtication(BaseAuthentication):
    """通过 ``HTTP_ADMINTOKEN`` 头认证管理员/演示用户。

    验证请求携带的管理员令牌是否与 User 记录匹配，
    且该用户的角色不是 ``'2'``（普通用户）。
    如果令牌缺失、无效或属于不允许的角色，则抛出 ``AuthenticationFailed``。
    """

    def authenticate(self, request: Request) -> None:
        """使用管理员令牌认证请求。

        参数:
            request: 传入的 DRF 请求。

        异常:
            exceptions.AuthenticationFailed: 认证失败时抛出。
        """
        admin_token = request.META.get("HTTP_ADMINTOKEN")
        print(f"检查adminToken==>{admin_token}")

        users = User.objects.filter(admin_token=admin_token)

        # 拒绝条件：令牌缺失、无匹配用户或用户角色为 '2'（普通用户）
        if not admin_token or not users.exists() or users[0].role == '2':
            raise exceptions.AuthenticationFailed("AUTH_FAIL_END")

        print('adminToken验证通过')


class TokenAuthtication(BaseAuthentication):
    """通过 ``HTTP_TOKEN`` 头认证前端用户。

    验证请求携带的令牌是否与 User 记录匹配，
    且该用户的角色为 ``'0'``（普通用户）。
    拒绝角色为 ``'1'`` 或 ``'3'`` 的令牌。
    """

    def authenticate(self, request: Request) -> None:
        """使用前端用户令牌认证请求。

        参数:
            request: 传入的 DRF 请求。

        异常:
            exceptions.AuthenticationFailed: 认证失败时抛出。
        """
        token = request.META.get("HTTP_TOKEN", "")

        if token is None:
            print("检查token==>token 为空")
            raise exceptions.AuthenticationFailed("AUTH_FAIL_FRONT")

        print(f"检查token==>{token}")
        users = User.objects.filter(token=token)

        # 拒绝条件：令牌缺失、无匹配用户或用户角色在 ['1', '3'] 中
        if not token or not users.exists() or (users[0].role in ['1', '3']):
            raise exceptions.AuthenticationFailed("AUTH_FAIL_FRONT")

        print('token验证通过')
