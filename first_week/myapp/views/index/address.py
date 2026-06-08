"""前台商城 API 的地址视图。

提供用户收货地址的 CRUD 端点。每个用户只能有一个地址
被标记为默认地址；设置新的默认地址会清除之前的默认标记。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp import utils
from myapp.auth.authentication import TokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Address
from myapp.serializers import AddressSerializer


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出指定用户的所有地址。

    查询参数:
        userId: 用户的主键（必填）

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及地址列表，
        未提供 userId 时返回 code=1。
    """
    if request.method != 'GET':
        return APIResponse(code=1, msg='仅支持GET请求')

    user_id = request.GET.get('userId', -1)
    if user_id == -1:
        return APIResponse(code=1, msg='userId不能为空')

    addresses = Address.objects.filter(user=user_id).order_by('-create_time')
    serializer = AddressSerializer(addresses, many=True)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def create(request: HttpRequest) -> Any:
    """创建新的收货地址。

    需要令牌认证。如果新地址被标记为默认地址，
    则清除同一用户所有其他地址的默认标记。

    参数:
        request: 请求体中包含地址字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及已创建的地址数据，
        必填字段缺失或序列化失败时返回 code=1。
    """
    address_desc = request.POST.get('desc', None)
    user = request.POST.get('user', None)
    is_default = request.POST.get('default', False)

    if address_desc is None or user is None:
        return APIResponse(code=1, msg='不能为空')

    if is_default:
        Address.objects.filter(user=user).update(default=False)

    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    utils.log_error(request, '参数错误')
    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def update(request: HttpRequest) -> Any:
    """更新现有的收货地址。

    需要令牌认证。如果更新后的地址被标记为默认地址，
    则清除同一用户所有其他地址的默认标记。

    查询参数:
        id: 地址的主键

    参数:
        request: 请求体中包含更新后地址字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的地址数据，
        地址不存在或更新失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        address = Address.objects.get(pk=pk)
    except Address.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    user = request.data['user']
    is_default = request.data['default']

    if is_default:
        Address.objects.filter(user=user).update(default=False)

    serializer = AddressSerializer(address, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    utils.log_error(request, '参数错误')
    return APIResponse(code=1, msg='更新失败')


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def delete(request: HttpRequest) -> Any:
    """通过 ID 删除一条或多条地址。

    需要令牌认证。

    查询参数:
        ids: 地址主键的逗号分隔列表

    参数:
        request: DRF 请求对象。

    返回:
        成功删除时返回 code=0，
        任何地址不存在时返回 code=1。
    """
    try:
        ids = request.GET.get('ids')
        id_list = ids.split(',')
        Address.objects.filter(id__in=id_list).delete()
    except Address.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    return APIResponse(code=0, msg='删除成功')
