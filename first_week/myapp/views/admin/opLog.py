"""管理后台的操作日志管理视图。

提供查看系统中管理员操作历史记录的列表接口。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import OpLog
from myapp.serializers import OpLogSerializer
from .base import paginate_queryset


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request: HttpRequest) -> APIResponse:
    """列出所有操作日志，按操作时间倒序排列。

    支持的查询参数：
        page (int):     页码（默认为 1）。
        pageSize (int): 每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的操作日志列表。
    """
    queryset = OpLog.objects.all().order_by('-re_time')
    result = paginate_queryset(queryset, request)
    serializer = OpLogSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })
