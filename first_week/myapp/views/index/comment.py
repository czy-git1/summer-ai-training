"""前台商城 API 的评论视图。

提供评论的列表、创建、删除和点赞端点。
支持按时间或热度（点赞数）排序。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view

from myapp.handler import APIResponse
from myapp.models import Comment
from myapp.serializers import CommentSerializer


def _get_comment_order_field(sort_order: str) -> str:
    """将排序键解析为 Django order_by 字段字符串。

    参数:
        sort_order: 'recent' 表示按时间排序，其他值表示按点赞数排序。

    返回:
        适用于 Django order_by 的字段字符串（如 '-comment_time'）。
    """
    if sort_order == 'recent':
        return '-comment_time'
    return '-like_count'


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出指定商品的评论。

    查询参数:
        thingId: 商品的主键（必填）
        order:   'recent'（默认）按评论时间降序排列，
                 其他值按点赞数降序排列

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及评论列表，
        thingId 缺失时返回 code=1。
    """
    if request.method != 'GET':
        return APIResponse(code=1, msg='仅支持GET请求')

    thing_id = request.GET.get("thingId", None)
    if not thing_id:
        return APIResponse(code=1, msg='thingId不能为空')

    sort_order = request.GET.get("order", 'recent')
    order_field = _get_comment_order_field(sort_order)

    comments = (
        Comment.objects
        .select_related("thing")
        .filter(thing=thing_id)
        .order_by(order_field)
    )
    serializer = CommentSerializer(comments, many=True)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['GET'])
def list_my_comment(request: HttpRequest) -> Any:
    """列出指定用户发表的评论。

    查询参数:
        userId: 用户的主键（必填）
        order:  'recent'（默认）按评论时间降序排列，
                其他值按点赞数降序排列

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及评论列表，
        userId 缺失时返回 code=1。
    """
    if request.method != 'GET':
        return APIResponse(code=1, msg='仅支持GET请求')

    user_id = request.GET.get("userId", None)
    if not user_id:
        return APIResponse(code=1, msg='userId不能为空')

    sort_order = request.GET.get("order", 'recent')
    order_field = _get_comment_order_field(sort_order)

    comments = (
        Comment.objects
        .select_related("thing")
        .filter(user=user_id)
        .order_by(order_field)
    )
    serializer = CommentSerializer(comments, many=True)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
def create(request: HttpRequest) -> Any:
    """创建一条新评论。

    评论数据直接从请求体中获取，并通过 CommentSerializer 进行验证。

    参数:
        request: 请求体中包含评论字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及已保存的评论数据，
        序列化失败时返回 code=1。
    """
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='创建失败')


@api_view(['POST'])
def delete(request: HttpRequest) -> Any:
    """通过 ID 删除一条或多条评论。

    查询参数:
        ids: 评论主键的逗号分隔列表

    参数:
        request: DRF 请求对象。

    返回:
        成功删除时返回 code=0，
        任何评论不存在时返回 code=1。
    """
    try:
        ids = request.GET.get('ids')
        id_list = ids.split(',')
        Comment.objects.filter(id__in=id_list).delete()
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    return APIResponse(code=0, msg='删除成功')


@api_view(['POST'])
def like(request: HttpRequest) -> Any:
    """将评论的 like_count 增加一。

    查询参数:
        commentId: 评论的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0，
        评论不存在时返回 code=1。
    """
    comment_id = request.GET.get('commentId')
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    comment.like_count += 1
    comment.save()
    return APIResponse(code=0, msg='推荐成功')
