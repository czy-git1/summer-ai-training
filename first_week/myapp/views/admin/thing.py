"""管理后台的商品管理视图。

提供商品模型的列表、详情、创建、更新和删除接口，支持按关键字和
分类进行可选筛选。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import Thing
from myapp.serializers import ListThingSerializer, ThingSerializer
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
    """列出商品，支持可选的关键字和分类筛选。

    支持的查询参数：
        keyword (str, 可选): 按标题子串匹配筛选。
        c (int, 可选):      按分类 ID 筛选。
        page (int):         页码（默认为 1）。
        pageSize (int):     每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的商品列表。
    """
    keyword = request.GET.get("keyword", None)
    classification_id = request.GET.get("c", None)

    queryset = Thing.objects.all().order_by('-create_time')
    if keyword:
        queryset = queryset.filter(title__contains=keyword)
    if classification_id:
        queryset = queryset.filter(classification_id=classification_id)

    result = paginate_queryset(queryset, request)
    serializer = ListThingSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def detail(request: HttpRequest) -> APIResponse:
    """通过主键获取单个商品的详细信息。

    需要 'id' 查询参数，包含商品的主键。
    成功时返回序列化的商品数据，对象不存在时返回错误信息。

    参数:
        request: 传入的 HTTP GET 请求，需包含 'id' 查询参数。

    返回:
        成功时返回 code=0 并附带序列化商品数据的 APIResponse，
        未找到时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        thing = get_object_or_error(Thing, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request: HttpRequest) -> APIResponse:
    """根据请求体创建新商品。

    使用 ThingSerializer 验证并持久化提交的数据。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含商品字段。

    返回:
        成功时返回 code=0 并附带创建的商品数据，
        验证失败时返回 code=1 并附带错误信息。
    """
    return create_instance(ThingSerializer, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request: HttpRequest) -> APIResponse:
    """更新由 'id' 查询参数指定的已有商品。

    需要 'id' 查询参数来指定要更新的商品，请求体中包含新的字段值。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数，
            请求体中包含要更新的字段。

    返回:
        成功时返回 code=0 并附带更新后的商品数据，
        对象未找到或验证失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        thing = get_object_or_error(Thing, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    return update_instance(ThingSerializer, thing, request.data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request: HttpRequest) -> APIResponse:
    """删除由 'id' 查询参数指定的商品。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        删除成功时返回 code=0，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    return delete_instance(Thing, pk)
