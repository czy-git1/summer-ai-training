"""
myapp Django 应用的实用工具函数。

提供时间戳生成、MD5 哈希、数据库游标结果转换、HTTP 请求元数据提取、
日期计算和错误日志记录等辅助功能。
"""

import datetime
import hashlib
import time
from typing import Any, Optional

from django.http import HttpRequest

from myapp.serializers import ErrorLogSerializer


def get_timestamp() -> int:
    """返回当前 Unix 时间戳（毫秒）。

    返回:
        int: 自 Unix 纪元以来的当前时间，单位为毫秒。
    """
    return int(round(time.time() * 1000))


def md5value(key: str) -> str:
    """计算字符串的小写 MD5 十六进制摘要。

    参数:
        key: 要哈希的输入字符串。

    返回:
        str: 32 位小写 MD5 十六进制摘要。
    """
    md5_hash = hashlib.md5()
    md5_hash.update(key.encode("utf-8"))
    digest = md5_hash.hexdigest().lower()
    print('计算md5:', digest)
    return digest


def dict_fetchall(cursor: Any) -> list[dict]:
    """将数据库游标中的所有行转换为字典列表。

    每个字典将列名映射到对应行中的值。

    参数:
        cursor: 已执行查询的 DB-API 2.0 游标对象。

    返回:
        list[dict]: 字典列表，每行一个字典，以列名为键。
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row)) for row in cursor.fetchall()
    ]


def get_ip(request: HttpRequest) -> Optional[str]:
    """从 HTTP 请求中提取客户端 IP 地址。

    优先检查 X-Forwarded-For 头（用于代理请求），
    其次回退到 REMOTE_ADDR。

    参数:
        request: 传入的 HTTP 请求对象。

    返回:
        Optional[str]: 客户端 IP 地址，如果未找到则返回 None。
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_ua(request: HttpRequest) -> str:
    """从 HTTP 请求中提取 User-Agent 字符串。

    返回值最多截断为 200 个字符。

    参数:
        request: 传入的 HTTP 请求对象。

    返回:
        str: User-Agent 头值的前 200 个字符。
    """
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent is None:
        return ''
    return user_agent[0:200]


def getWeekDays() -> list[str]:
    """返回过去 7 天的日期，按升序排列。

    返回:
        list[str]: 包含 7 个日期字符串的列表，格式为 YYYY-MM-DD，
            从 6 天前到今天。
    """
    now = datetime.datetime.now()
    week_days = [
        (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(6, -1, -1)
    ]
    return week_days


def get_monday() -> str:
    """返回本周星期一的日期。

    返回:
        str: 星期一的日期，格式为 YYYY-MM-DD。
    """
    now = datetime.datetime.now()
    monday_date = now - datetime.timedelta(days=now.weekday())
    return monday_date.strftime('%Y-%m-%d')


def log_error(request: HttpRequest, content: str) -> None:
    """通过 ErrorLogSerializer 持久化记录错误事件。

    捕获客户端 IP、HTTP 方法、请求 URL 和错误内容，
    如果序列化器验证成功则保存记录。

    参数:
        request: 传入的 HTTP 请求对象。
        content: 描述错误的说明或消息。
    """
    data = {
        'ip': get_ip(request),
        'method': request.method,
        'url': request.path,
        'content': content,
    }
    serializer = ErrorLogSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
