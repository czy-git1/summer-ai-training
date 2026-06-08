"""前台商城 API 的标签视图。

提供商品标签的列表端点，
按最新创建优先排序。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view

from myapp.handler import APIResponse
from myapp.models import Tag
from myapp.serializers import TagSerializer


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出所有标签，按创建时间降序排列。

    参数:
        request: DRF 请求对象。

    返回:
        返回 code=0 及标签列表的 APIResponse。
    """
    if request.method == 'GET':
        tags = Tag.objects.all().order_by('-create_time')
        serializer = TagSerializer(tags, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
