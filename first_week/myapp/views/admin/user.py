"""管理后台的用户管理和认证视图。

提供以下接口：
  - admin_login   -- 管理员认证，生成令牌并记录登录日志。
  - list_api      -- 分页的用户列表。
  - create        -- 创建用户，自动对密码进行哈希处理。
  - update        -- 更新用户信息（用户名/密码/令牌字段受保护）。
  - updatePwd     -- 修改密码，需验证旧密码。
  - delete        -- 删除用户。
  - info          -- 查询单个用户详情。
"""

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.serializers import Serializer

from myapp import utils
from myapp.auth.authentication import AdminTokenAuthtication
from myapp.handler import APIResponse
from myapp.models import User
from myapp.serializers import LoginLogSerializer, UserSerializer
from .base import (
    create_instance,
    delete_instance,
    get_object_or_error,
    paginate_queryset,
    update_instance,
)

# 通过通用更新接口时不得被覆盖的字段。
_PROTECTED_USER_FIELDS: set[str] = {
    'username',
    'password',
    'admin_token',
    'token',
}


def _record_login_log(username: str, request: HttpRequest) -> None:
    """在登录日志模型中记录一次登录事件。

    创建一条登录日志条目，包含用户的用户名、IP 地址和 User-Agent 字符串。

    参数:
        username: 已认证用户的用户名。
        request: HTTP 请求对象（用于提取 IP 和 UA）。
    """
    try:
        login_data = {
            "username": username,
            "ip": utils.get_ip(request),
            "ua": utils.get_ua(request),
        }
        login_serializer = LoginLogSerializer(data=login_data)
        if login_serializer.is_valid():
            login_serializer.save()
    except Exception as e:
        print(e)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def list_api(request: HttpRequest) -> APIResponse:
    """列出所有用户，按创建时间倒序排列。

    支持的查询参数：
        page (int):     页码（默认为 1）。
        pageSize (int): 每页条数（默认为 10）。

    参数:
        request: 传入的 HTTP GET 请求。

    返回:
        code=0 的 APIResponse，'data' 中包含分页的用户列表。
    """
    queryset = User.objects.all().order_by('-create_time')
    result = paginate_queryset(queryset, request)
    serializer = UserSerializer(result['page_obj'], many=True)
    return APIResponse(code=0, msg='查询成功', data={
        'list': serializer.data,
        'total': result['total'],
    })


@api_view(['POST'])
def admin_login(request: HttpRequest) -> APIResponse:
    """认证管理员用户并生成管理员令牌。

    需要在请求体中提供 'username' 和 'password'。密码在比对前
    会先进行 MD5 哈希处理。只有 role 不为 '2'（前台用户）的
    用户才允许登录。

    认证成功后，用户的 admin_token 字段会被更新为由用户名生成
    的新令牌，并记录一条登录日志。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'username' 和
            'password' 字段。

    返回:
        成功时返回 code=0 并附带序列化的用户数据（包含新的
        admin_token），失败时返回 code=1 并附带错误信息。
    """
    username: str = request.data.get('username')
    password: str = utils.md5value(request.data.get('password'))

    users = User.objects.filter(username=username, password=password)
    if not users:
        return APIResponse(code=1, msg='用户名或密码错误')

    user = users[0]

    if user.role in ['2']:
        return APIResponse(code=1, msg='该帐号为前台用户帐号')

    data = {
        'username': username,
        'password': password,
        'admin_token': utils.md5value(username),
    }
    serializer: Serializer = UserSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
        _record_login_log(username, request)
        return APIResponse(code=0, msg='登录成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='用户名或密码错误')


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request: HttpRequest) -> APIResponse:
    """创建新用户，并对密码进行哈希处理。

    如果请求数据中存在 'password' 字段，则在传递给序列化器之前
    会先对其值进行 MD5 哈希处理。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含用户字段。

    返回:
        成功时返回 code=0 并附带创建的用户数据，
        验证失败时返回 code=1。
    """
    data = request.data.copy()
    if 'password' in data:
        data['password'] = utils.md5value(data['password'])
    return create_instance(UserSerializer, data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request: HttpRequest) -> APIResponse:
    """更新用户资料，保护敏感字段。

    在序列化器处理数据之前，会从更新载荷中静默移除 'username'、
    'password'、'admin_token' 和 'token' 字段，以防止意外覆盖。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数，
            请求体中包含要更新的用户字段。

    返回:
        成功时返回 code=0 并附带更新后的用户数据，
        未找到或验证失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        user = get_object_or_error(User, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    data = request.data.copy()
    for field in _PROTECTED_USER_FIELDS:
        data.pop(field, None)

    return update_instance(UserSerializer, user, data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def updatePwd(request: HttpRequest) -> APIResponse:
    """验证旧密码后修改用户密码。

    请求体中需要包含：
        - password:      当前（旧）密码（明文，通过 MD5 比对）。
        - newPassword1:  期望的新密码。
        - newPassword2:  新密码的确认。

    验证规则：
        1. 三个字段均为必填。
        2. 旧密码必须与存储的哈希值匹配。
        3. newPassword1 和 newPassword2 必须一致。

    参数:
        request: 传入的 HTTP POST 请求，请求体中包含密码字段，
            并需携带 'id' 查询参数。

    返回:
        成功时返回 code=0 并附带更新后的用户数据，
        失败时返回 code=1 并附带相应的错误信息。
    """
    pk = request.GET.get('id', -1)
    try:
        user = get_object_or_error(User, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    old_password = request.data.get('password', None)
    new_password1 = request.data.get('newPassword1', None)
    new_password2 = request.data.get('newPassword2', None)

    if not old_password or not new_password1 or not new_password2:
        return APIResponse(code=1, msg='不能为空')

    if user.password != utils.md5value(old_password):
        return APIResponse(code=1, msg='原密码不正确')

    if new_password1 != new_password2:
        return APIResponse(code=1, msg='两次密码不一致')

    data = request.data.copy()
    data.update({'password': utils.md5value(new_password1)})
    return update_instance(UserSerializer, user, data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request: HttpRequest) -> APIResponse:
    """删除由 'id' 查询参数指定的用户。

    参数:
        request: 传入的 HTTP POST 请求，需包含 'id' 查询参数。

    返回:
        删除成功时返回 code=0，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    return delete_instance(User, pk)


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def info(request: HttpRequest) -> APIResponse:
    """通过主键获取单个用户的详细信息。

    需要 'id' 查询参数，包含用户的主键。

    参数:
        request: 传入的 HTTP GET 请求，需包含 'id' 查询参数。

    返回:
        成功时返回 code=0 并附带序列化的用户数据，
        对象不存在时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        user = get_object_or_error(User, pk)
    except ValueError as e:
        return APIResponse(code=1, msg=str(e))

    serializer = UserSerializer(user)
    return APIResponse(code=0, msg='查询成功', data=serializer.data)
