"""
myapp Django 应用的标准化 API 响应包装类。

为所有 API 端点提供一致的 JSON 响应封装，包含 code、message 和可选的 data 字段。
"""

from typing import Any, Optional

from rest_framework.response import Response


class APIResponse(Response):
    """用于 JSON API 响应的标准化 DRF Response 子类。

    将响应数据包装在一致的信封中，包含：

    - ``code``: 数值型的应用级状态码（0 = 成功）。
    - ``msg``: 人类可读的消息字符串。
    - ``data``: 可选的负载数据（为 None 时不包含在信封中）。
    - 任何额外的关键字参数会合并到信封中。
    """

    def __init__(
        self,
        code: int = 0,
        msg: str = '',
        data: Optional[Any] = None,
        status: int = 200,
        headers: Optional[dict] = None,
        content_type: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """初始化标准化 API 响应。

        参数:
            code: 应用级状态码（默认 0 表示成功）。
            msg: 描述结果的人类可读消息。
            data: 可选的响应负载（为 None 时不包含在信封中）。
            status: HTTP 状态码（默认 200）。
            headers: 可选的 HTTP 响应头。
            content_type: 可选的响应内容类型。
            **kwargs: 合并到响应信封中的额外字段。
        """
        payload: dict[str, Any] = {'code': code, 'msg': msg}
        if data is not None:
            payload['data'] = data
        payload.update(kwargs)

        super().__init__(
            data=payload,
            status=status,
            template_name=None,
            headers=headers,
            exception=False,
            content_type=content_type,
        )
