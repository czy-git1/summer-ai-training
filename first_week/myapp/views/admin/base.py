"""管理后台视图模块的通用工具函数。

提供管理后台视图模块中共用的增删改查辅助函数，包括对象获取、
分页、序列化、创建/更新/删除操作以及标准化的 API 响应。
"""
from typing import Any

from django.core.paginator import Page, Paginator
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from rest_framework.serializers import Serializer

from myapp.handler import APIResponse


def get_object_or_error(
    model_class: type[Model], pk: Any, error_msg: str = '对象不存在'
) -> Model:
    """通过主键获取模型实例，若不存在则抛出 ValueError。

    参数:
        model_class: 要查询的 Django 模型类。
        pk: 要获取的对象的主键值。
        error_msg: 对象未找到时包含的错误信息。

    返回:
        匹配给定主键的模型实例。

    异常:
        ValueError: 当不存在具有给定主键的对象时抛出。
    """
    try:
        return model_class.objects.get(pk=pk)
    except model_class.DoesNotExist:
        raise ValueError(error_msg)


def paginate_queryset(
    queryset: QuerySet,
    request: HttpRequest,
    default_page_size: int = 10,
) -> dict[str, Any]:
    """根据请求中的查询参数对查询集进行分页。

    从 request.GET 中读取 'page' 和 'pageSize' 来确定返回哪一页
    的结果，若未提供则回退到合理的默认值。

    参数:
        queryset: 要进行分页的 Django 查询集。
        request: 包含 'page' 和 'pageSize' 查询参数的 HTTP 请求对象。
        default_page_size: 当未提供 'pageSize' 时使用的默认每页条数。

    返回:
        一个字典，包含：
            - 'page_obj': 包含当前页结果的 Django Page 对象。
            - 'total': 所有页的总条目数。
            - 'page': 当前页码。
            - 'page_size': 每页的条目数。
    """
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", default_page_size))
    paginator = Paginator(queryset, page_size)
    page_obj: Page = paginator.get_page(page)
    return {
        'page_obj': page_obj,
        'total': paginator.count,
        'page': page,
        'page_size': page_size,
    }


def create_instance(
    serializer_class: type[Serializer], data: dict[str, Any]
) -> APIResponse:
    """使用给定的序列化器创建新的模型实例。

    根据序列化器验证输入数据；如果验证通过，则保存实例并返回成功
    响应。否则打印验证错误并返回失败响应。

    参数:
        serializer_class: 用于验证和保存的 DRF 序列化器类。
        data: 要反序列化并持久化的字段值字典。

    返回:
        成功时返回 code=0 并附带序列化数据的 APIResponse，
        失败时返回 code=1 并附带错误信息。
    """
    serializer = serializer_class(data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    print(serializer.errors)
    return APIResponse(code=1, msg='创建失败')


def update_instance(
    serializer_class: type[Serializer],
    instance: Model,
    data: dict[str, Any],
) -> APIResponse:
    """使用序列化器更新已有的模型实例。

    通过序列化器将给定数据绑定到已有实例；验证并保存，返回成功
    或失败响应。

    参数:
        serializer_class: 用于验证和保存更新后实例的 DRF 序列化器类。
        instance: 要更新的已有模型实例。
        data: 要应用到实例的字段值字典。

    返回:
        成功时返回 code=0 并附带更新后数据的 APIResponse，
        验证失败时返回 code=1。
    """
    serializer = serializer_class(instance, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)
    print(serializer.errors)
    return APIResponse(code=1, msg='更新失败')


def delete_instance(
    model_class: type[Model], pk: Any
) -> APIResponse:
    """通过主键删除模型实例。

    通过主键查找对象；如果找到则删除并返回成功响应。如果对象
    不存在则返回错误响应。

    参数:
        model_class: 要删除其实例的 Django 模型类。
        pk: 要删除的对象的主键值。

    返回:
        删除成功时返回 code=0 并附带成功信息的 APIResponse，
        对象未找到时返回 code=1。
    """
    try:
        instance = model_class.objects.get(pk=pk)
        instance.delete()
        return APIResponse(code=0, msg='删除成功')
    except model_class.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')
