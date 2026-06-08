"""管理后台的公告管理视图。

提供向用户展示的系统公告和通知的列表、创建、更新和删除接口。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Notice
from myapp.serializers import NoticeSerializer
from .base import (
    create_instance,
    delete_instance,
    get_object_or_error,
    paginate_queryset,
    update_instance,
)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request: HttpRequest) -> APIResponse:
    """列出所有公告，按创建时间倒序排列。

    支持的查询参数：
        page (int):     页码（默认为 1）。
        pageSize (int): 每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的公告列表。
    """
    queryset = Notice.objects.all().order_by('-create_time')
    result = paginate_queryset(queryset, request)
    serializer = NoticeSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request: HttpRequest) -> APIResponse:
    """根据请求体创建新公告。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含公告字段。

    返回:
        成功时返回 code=0 并附带创建的公告数据，
        验证失败时返回 code=1。
    """
    return create_instance(NoticeSerializer, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request: HttpRequest) -> APIResponse:
    """更新由 'id' 查询参数指定的已有公告。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数，
            请求体中包含要更新的公告字段。

    返回:
        成功时返回 code=0 并附带更新后的公告数据，
        未找到或验证失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        notice = get_object_or_error(Notice, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    return update_instance(NoticeSerializer, notice, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request: HttpRequest) -> APIResponse:
    """删除由 'id' 查询参数指定的公告。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        删除成功时返回 code=0，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    return delete_instance(Notice, pk)
