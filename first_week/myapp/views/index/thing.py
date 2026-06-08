"""前台商城 API 的 Thing（商品）视图。

提供商品的列表、搜索和筛选端点，管理心愿单和收藏，
以及追踪商品的热度计数（心愿数、推荐数）。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view

from myapp import utils
from myapp.handler import APIResponse
from myapp.models import Classification, Thing, Tag, User
from myapp.serializers import (
    ThingSerializer,
    ClassificationSerializer,
    ListThingSerializer,
    DetailThingSerializer,
)


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出商品，支持通过关键词、分类、标签和排序方式进行筛选。

    查询参数:
        keyword:  按商品标题搜索的关键词（模糊匹配）
        c:        分类（category）ID；包含其子分类
        tag:      按标签 ID 筛选
        sort:     'recent'（默认）按 create_time 降序排列，
                  'hot' 或 'recommend' 按页面浏览量降序排列

    参数:
        request: 带有可选查询参数的 DRF 请求对象。

    返回:
        成功时返回 code=0 及分页商品列表的 APIResponse。
    """
    if request.method == 'GET':
        keyword = request.GET.get("keyword", None)
        category_id = request.GET.get("c", None)
        tag_id = request.GET.get("tag", None)
        sort_mode = request.GET.get("sort", 'recent')

        order_field = '-create_time'
        if sort_mode == 'recent':
            order_field = '-create_time'
        elif sort_mode in ('hot', 'recommend'):
            order_field = '-pv'

        if keyword:
            things = Thing.objects.filter(
                title__contains=keyword
            ).order_by(order_field)
        elif category_id and int(category_id) > -1:
            classification_ids = [category_id]
            classifications = Classification.objects.filter(pid=category_id)
            serializer = ClassificationSerializer(classifications, many=True)
            sub_data = serializer.data
            for item in sub_data:
                classification_ids.append(item['id'])

            things = Thing.objects.filter(
                classification_id__in=classification_ids
            ).order_by(order_field)
        elif tag_id:
            tag = Tag.objects.get(id=tag_id)
            things = tag.thing_set.all().order_by(order_field)
        else:
            things = Thing.objects.all().defer('wish').order_by(order_field)

        serializer = ListThingSerializer(things, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['GET'])
def detail(request: HttpRequest) -> Any:
    """获取单个商品的详细信息。

    查询参数:
        id: 商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及商品完整详情的 APIResponse，
        商品不存在时返回 code=1 及错误信息。
    """
    if request.method != 'GET':
        return APIResponse(code=1, msg='仅支持GET请求')

    pk = request.GET.get('id', -1)
    try:
        thing = Thing.objects.get(pk=pk)
    except Thing.DoesNotExist:
        utils.log_error(request, '对象不存在')
        return APIResponse(code=1, msg='对象不存在')

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
def increaseWishCount(request: HttpRequest) -> Any:
    """将商品的 wish_count 增加一。

    查询参数:
        id: 商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的商品数据，
        商品不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        thing = Thing.objects.get(pk=pk)
    except Thing.DoesNotExist:
        utils.log_error(request, '对象不存在')
        return APIResponse(code=1, msg='对象不存在')

    thing.wish_count += 1
    thing.save()
    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


@api_view(['POST'])
def increaseRecommendCount(request: HttpRequest) -> Any:
    """将商品的 recommend_count 增加一。

    查询参数:
        id: 商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的商品数据，
        商品不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        thing = Thing.objects.get(pk=pk)
    except Thing.DoesNotExist:
        utils.log_error(request, '对象不存在')
        return APIResponse(code=1, msg='对象不存在')

    thing.recommend_count += 1
    thing.save()
    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


@api_view(['POST'])
def addWishUser(request: HttpRequest) -> Any:
    """将用户添加到商品的心愿单。

    查询参数:
        username: 用户名
        thingId:  商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的商品数据，
        操作失败时返回 code=1（参数缺失或对象不存在）。
    """
    username = request.GET.get('username', None)
    thing_id = request.GET.get('thingId', None)

    if not username or not thing_id:
        return APIResponse(code=1, msg='操作失败')

    try:
        user = User.objects.get(username=username)
        thing = Thing.objects.get(pk=thing_id)
    except (User.DoesNotExist, Thing.DoesNotExist):
        utils.log_error(request, '操作失败')
        return APIResponse(code=1, msg='操作失败')

    if user not in thing.wish.all():
        thing.wish.add(user)
        thing.wish_count += 1
        thing.save()

    serializer = ThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


@api_view(['POST'])
def removeWishUser(request: HttpRequest) -> Any:
    """将用户从商品的心愿单中移除。

    查询参数:
        username: 用户名
        thingId:  商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0，
        操作失败时返回 code=1（参数缺失或对象不存在）。
    """
    username = request.GET.get('username', None)
    thing_id = request.GET.get('thingId', None)

    if not username or not thing_id:
        return APIResponse(code=1, msg='操作失败')

    try:
        user = User.objects.get(username=username)
        thing = Thing.objects.get(pk=thing_id)
    except (User.DoesNotExist, Thing.DoesNotExist):
        utils.log_error(request, '操作失败')
        return APIResponse(code=1, msg='操作失败')

    if user in thing.wish.all():
        thing.wish.remove(user)
        thing.wish_count -= 1
        thing.save()

    return APIResponse(code=0, msg='操作成功')


@api_view(['GET'])
def getWishThingList(request: HttpRequest) -> Any:
    """获取用户的心愿单。

    查询参数:
        username: 用户名

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及用户心愿单中的商品列表，
        username 缺失或发生错误时返回 code=1。
    """
    username = request.GET.get('username', None)
    if not username:
        return APIResponse(code=1, msg='username不能为空')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='用户不存在')

    try:
        things = user.wish_things.all()
        serializer = ListThingSerializer(things, many=True)
        return APIResponse(code=0, msg='操作成功', data=serializer.data)
    except Exception as e:
        utils.log_error(request, '操作失败' + str(e))
        return APIResponse(code=1, msg='获取心愿单失败')


@api_view(['POST'])
def addCollectUser(request: HttpRequest) -> Any:
    """将用户添加到商品的收藏列表。

    查询参数:
        username: 用户名
        thingId:  商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的商品详情，
        操作失败时返回 code=1（参数缺失或对象不存在）。
    """
    username = request.GET.get('username', None)
    thing_id = request.GET.get('thingId', None)

    if not username or not thing_id:
        return APIResponse(code=1, msg='操作失败')

    try:
        user = User.objects.get(username=username)
        thing = Thing.objects.get(pk=thing_id)
    except (User.DoesNotExist, Thing.DoesNotExist):
        utils.log_error(request, '操作失败')
        return APIResponse(code=1, msg='操作失败')

    if user not in thing.collect.all():
        thing.collect.add(user)
        thing.collect_count += 1
        thing.save()

    serializer = DetailThingSerializer(thing)
    return APIResponse(code=0, msg='操作成功', data=serializer.data)


@api_view(['POST'])
def removeCollectUser(request: HttpRequest) -> Any:
    """将用户从商品的收藏列表中移除。

    查询参数:
        username: 用户名
        thingId:  商品的主键

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0，
        操作失败时返回 code=1（参数缺失或对象不存在）。
    """
    username = request.GET.get('username', None)
    thing_id = request.GET.get('thingId', None)

    if not username or not thing_id:
        return APIResponse(code=1, msg='操作失败')

    try:
        user = User.objects.get(username=username)
        thing = Thing.objects.get(pk=thing_id)
    except (User.DoesNotExist, Thing.DoesNotExist):
        utils.log_error(request, '操作失败')
        return APIResponse(code=1, msg='操作失败')

    if user in thing.collect.all():
        thing.collect.remove(user)
        thing.collect_count -= 1
        thing.save()

    return APIResponse(code=0, msg='操作成功')


@api_view(['GET'])
def getCollectThingList(request: HttpRequest) -> Any:
    """获取用户的收藏列表。

    查询参数:
        username: 用户名

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及用户收藏的商品列表，
        username 缺失或发生错误时返回 code=1。
    """
    username = request.GET.get('username', None)
    if not username:
        return APIResponse(code=1, msg='username不能为空')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='用户不存在')

    try:
        things = user.collect_things.all()
        serializer = ListThingSerializer(things, many=True)
        return APIResponse(code=0, msg='操作成功', data=serializer.data)
    except Exception as e:
        utils.log_error(request, '操作失败' + str(e))
        return APIResponse(code=1, msg='获取收藏失败')
