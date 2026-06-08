"""管理后台的横幅管理视图。

提供应用中展示的推广或信息横幅的列表、创建、更新和删除接口。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Banner
from myapp.serializers import BannerSerializer
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
    """列出所有横幅，按创建时间倒序排列。

    支持的查询参数：
        page (int):     页码（默认为 1）。
        pageSize (int): 每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的横幅列表。
    """
    queryset = Banner.objects.all().order_by('-create_time')
    result = paginate_queryset(queryset, request)
    serializer = BannerSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request: HttpRequest) -> APIResponse:
    """根据请求体创建新横幅。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含横幅字段。

    返回:
        成功时返回 code=0 并附带创建的横幅数据，
        验证失败时返回 code=1。
    """
    return create_instance(BannerSerializer, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request: HttpRequest) -> APIResponse:
    """更新由 'id' 查询参数指定的已有横幅。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数，
            请求体中包含要更新的横幅字段。

    返回:
        成功时返回 code=0 并附带更新后的横幅数据，
        未找到或验证失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        banner = get_object_or_error(Banner, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    return update_instance(BannerSerializer, banner, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request: HttpRequest) -> APIResponse:
    """删除由 'id' 查询参数指定的横幅。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        删除成功时返回 code=0，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    return delete_instance(Banner, pk)
