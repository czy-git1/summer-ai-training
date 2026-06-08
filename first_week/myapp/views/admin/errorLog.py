"""管理后台的错误日志管理视图。

提供查看应用运行期间捕获的系统错误日志的列表接口。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import ErrorLog
from myapp.serializers import ErrorLogSerializer
from .base import paginate_queryset


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request: HttpRequest) -> APIResponse:
    """列出所有错误日志，按日志时间倒序排列。

    支持的查询参数：
        page (int):     页码（默认为 1）。
        pageSize (int): 每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的错误日志列表。
    """
    queryset = ErrorLog.objects.all().order_by('-log_time')
    result = paginate_queryset(queryset, request)
    serializer = ErrorLogSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })
