"""
myapp Django 应用的日志中间件。

捕获请求元数据和响应时间信息，然后通过 ``OpLogSerializer`` 持久化操作日志。
"""

import json
import time
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from myapp import utils
from myapp.serializers import OpLogSerializer


class OpLogs(MiddlewareMixin):
    """记录每个请求操作详情的 Django 中间件。

    记录请求 URL、HTTP 方法、客户端 IP 以及接收请求到发送响应之间的
    耗时（毫秒）。收集的数据在响应生成后通过 ``OpLogSerializer`` 持久化。

    属性:
        start_time: 请求首次处理时捕获的时间戳。
        end_time: 响应生成时捕获的时间戳。
        data: 累积请求元数据以用于日志条目的字典。
    """

    def __init__(self, *args: Any) -> None:
        """初始化中间件实例。

        参数:
            *args: 转发给父类的位置参数。
        """
        super().__init__(*args)
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.data: dict[str, Any] = {}

    def process_request(self, request: HttpRequest) -> None:
        """在请求处理开始时捕获请求元数据。

        参数:
            request: 传入的 HTTP 请求。
        """
        self.start_time = time.time()

        client_ip = utils.get_ip(request)
        http_method = request.method
        request_content = request.GET if http_method == 'GET' else request.POST
        if request_content:
            request_content = json.dumps(request_content)
        else:
            request_content = None

        self.data.update(
            {
                're_url': request.path,
                're_method': http_method,
                're_ip': client_ip,
            }
        )

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """捕获响应时间并持久化操作日志。

        参数:
            request: 传入的 HTTP 请求。
            response: 传出的 HTTP 响应。

        返回:
            HttpResponse: 响应对象，不做修改。
        """
        self.end_time = time.time()
        elapsed_ms = round((self.end_time - self.start_time) * 1000)
        self.data['access_time'] = elapsed_ms

        serializer = OpLogSerializer(data=self.data)
        if serializer.is_valid():
            serializer.save()

        return response
