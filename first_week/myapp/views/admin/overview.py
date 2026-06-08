"""管理后台的仪表盘概览视图。

提供管理后台仪表盘使用的聚合统计数据（各类实体数量）和基本系统
信息接口。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Classification, Comment, Order, Tag, Thing, User


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def count(request: HttpRequest) -> APIResponse:
    """返回管理后台仪表盘的聚合实体数量统计。

    统计数据库中当前存储的商品、分类、标签、用户、评论和订单数量。

    参数:
        request: 传入的 HTTP GET 请求（需携带已认证的管理员令牌）。

    返回:
        code=0 的 APIResponse，其中 'data' 字典以每种实体类型
        （如 'thingCount'、'userCount'）为键，映射到其总数。
    """
    data: dict[str, int] = {
        'thingCount': Thing.objects.count(),
        'classificationCount': Classification.objects.count(),
        'tagCount': Tag.objects.count(),
        'userCount': User.objects.count(),
        'commentCount': Comment.objects.count(),
        'orderCount': Order.objects.count(),
    }
    return APIResponse(code=0, msg='查询成功', data=data)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def sysInfo(request: HttpRequest) -> APIResponse:
    """返回基本系统标识信息。

    提供系统名称和版本字符串，供管理后台前端在关于/页脚部分显示。

    参数:
        request: 传入的 HTTP GET 请求（需携带已认证的管理员令牌）。

    返回:
        code=0 的 APIResponse，其中 'data' 字典包含 'sysName'
        和 'version'。
    """
    data: dict[str, str] = {
        'sysName': '管理后台',
        'version': '1.0.0',
    }
    return APIResponse(code=0, msg='查询成功', data=data)
