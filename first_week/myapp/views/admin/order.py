"""管理后台的订单管理视图。

提供客户订单的列表、创建、更新、取消、延期和删除接口，包括订单号
的自动生成和状态管理功能。
"""
import datetime
from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.serializers import Serializer

from myapp import utils
from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Order
from myapp.serializers import OrderSerializer
from .base import (
    delete_instance,
    get_object_or_error,
    paginate_queryset,
    update_instance,
)


def _partial_update_order(
    pk: Any,
    status: str,
    success_msg: str,
    error_msg: str = '更新失败',
) -> APIResponse:
    """对订单执行部分状态更新。

    辅助函数，通过主键获取订单，并使用部分序列化器更新来设置其
    状态字段。

    参数:
        pk: 要更新的订单主键。
        status: 要分配的新状态值。
        success_msg: API 响应的成功信息。
        error_msg: 验证失败时返回的错误信息。

    返回:
        包含部分更新结果的 APIResponse。
    """
    try:
        order = get_object_or_error(Order, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    serializer: Serializer = OrderSerializer(
        order,
        data={'status': status},
        partial=True,
    )
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg=success_msg, data=serializer.data)
    print(serializer.errors)
    return APIResponse(code=1, msg=error_msg)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request: HttpRequest) -> APIResponse:
    """列出订单，支持按状态可选筛选。

    支持的查询参数：
        orderStatus (str, 可选): 筛选状态包含此子串的订单。
        page (int):             页码（默认为 1）。
        pageSize (int):         每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的订单列表。
    """
    order_status = request.GET.get("orderStatus", '')

    queryset = (
        Order.objects.all()
        .filter(status__contains=order_status)
        .order_by('-order_time')
    )
    result = paginate_queryset(queryset, request)
    serializer = OrderSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request: HttpRequest) -> APIResponse:
    """创建新订单，并自动生成元数据。

    自动设置以下字段：
        - order_number（订单号）：基于时间戳的唯一值。
        - status（状态）：设为 '1'（待处理/新订单）。
        - order_time（下单时间）：设为当前日期时间。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含订单字段。

    返回:
        成功时返回 code=0 并附带创建的订单数据，
        验证失败时返回 code=1。
    """
    data = request.data.copy()
    data['order_number'] = str(utils.get_timestamp())
    data['status'] = '1'
    data['order_time'] = datetime.datetime.now()

    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    print(serializer.errors)
    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request: HttpRequest) -> APIResponse:
    """更新由 'id' 查询参数指定的已有订单。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数，
            请求体中包含要更新的订单字段。

    返回:
        成功时返回 code=0 并附带更新后的订单数据，
        未找到或验证失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        order = get_object_or_error(Order, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    return update_instance(OrderSerializer, order, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def cancel_order(request: HttpRequest) -> APIResponse:
    """取消订单，将其状态设置为 '7'（已取消）。

    对由 'id' 查询参数指定的订单执行部分更新。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        成功时返回 code=0 并附带已取消的订单数据。
    """
    pk = request.GET.get('id', -1)
    return _partial_update_order(
        pk=pk,
        status='7',
        success_msg='取消成功',
        error_msg='更新失败',
    )


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delay(request: HttpRequest) -> APIResponse:
    """延期订单，将其状态设置为 '3'（已延期）。

    对由 'id' 查询参数指定的订单执行部分更新。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        成功时返回 code=0 并附带已延期的订单数据。
    """
    pk = request.GET.get('id', -1)
    return _partial_update_order(
        pk=pk,
        status='3',
        success_msg='延期成功',
        error_msg='操作失败',
    )


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request: HttpRequest) -> APIResponse:
    """删除由 'id' 查询参数指定的订单。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        删除成功时返回 code=0，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    return delete_instance(Order, pk)
