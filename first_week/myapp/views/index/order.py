"""前台商城 API 的订单视图。

提供订单的列表、创建和取消端点。
订单与用户和商品关联，并通过生命周期追踪状态
（1=进行中，7=已取消）。
"""

import datetime
from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp import utils
from myapp.auth.authentication import TokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Order, Thing
from myapp.serializers import OrderSerializer


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出用户的订单，可按订单状态筛选。

    查询参数:
        userId:      用户的主键
        orderStatus: （可选）按状态字符串筛选（模糊匹配）

    参数:
        request: DRF 请求对象。

    返回:
        返回 code=0 及订单列表的 APIResponse。
    """
    if request.method == 'GET':
        user_id = request.GET.get('userId', -1)
        order_status = request.GET.get('orderStatus', '')

        orders = (
            Order.objects.all()
            .filter(user=user_id)
            .filter(status__contains=order_status)
            .order_by('-order_time')
        )
        serializer = OrderSerializer(orders, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def create(request: HttpRequest) -> Any:
    """创建新订单。

    需要令牌认证。验证所有必填字段（user、thing、count）是否存在
    以及库存是否充足。成功后创建 status=1（进行中）的订单。

    参数:
        request: 请求体中包含订单字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及已创建的订单数据，
        失败时返回 code=1 及错误信息。
    """
    data = request.data.copy()

    if data['user'] is None or data['thing'] is None or data['count'] is None:
        return APIResponse(code=1, msg='参数错误')

    thing = Thing.objects.get(pk=data['thing'])
    count = data['count']
    if thing.repertory < int(count):
        return APIResponse(code=1, msg='库存不足')

    data['create_time'] = datetime.datetime.now()
    data['order_number'] = str(utils.get_timestamp())
    data['status'] = '1'

    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def cancel_order(request: HttpRequest) -> Any:
    """将现有订单的状态设置为 7（已取消）以取消订单。

    需要令牌认证。

    查询参数:
        id: 订单的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的订单数据，
        订单不存在或更新失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    update_data = {'status': 7}
    serializer = OrderSerializer(order, data=update_data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='取消成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='更新失败')
