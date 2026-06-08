"""前台商城 API 的通知视图。

提供系统公告/通知的列表端点，
按最新优先排序。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view

from myapp.handler import APIResponse
from myapp.models import Notice
from myapp.serializers import NoticeSerializer


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """列出所有通知，按创建时间降序排列。

    参数:
        request: DRF 请求对象。

    返回:
        返回 code=0 及通知列表的 APIResponse。
    """
    if request.method == 'GET':
        notices = Notice.objects.all().order_by('-create_time')
        serializer = NoticeSerializer(notices, many=True)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
