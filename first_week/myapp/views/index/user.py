"""前台商城 API 的用户视图。

提供用户认证（登录、注册）、个人资料获取与更新以及密码修改的端点。
包含一个用于记录成功登录尝试的辅助函数。
"""

from typing import Any

from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes

from myapp import utils
from myapp.auth.authentication import TokenAuthtication
from myapp.handler import APIResponse
from myapp.models import User
from myapp.serializers import UserSerializer, LoginLogSerializer
from myapp.utils import md5value


def make_login_log(request: HttpRequest) -> None:
    """在登录日志表中记录一次登录尝试。

    从请求数据中提取用户名以及客户端 IP 和 User-Agent，
    然后持久化一条 LoginLog 记录。错误会被静默吞掉，
    以免中断登录流程。

    参数:
        request: 包含 request.data['username'] 的 DRF 请求对象。
    """
    try:
        username = request.data['username']
        log_data = {
            "username": username,
            "ip": utils.get_ip(request),
            "ua": utils.get_ua(request),
        }
        serializer = LoginLogSerializer(data=log_data)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
    except Exception as e:
        print(e)


@api_view(['POST'])
def login(request: HttpRequest) -> Any:
    """认证前台用户并颁发访问令牌。

    请求体中需要 'username' 和 'password'。密码在比较前
    通过 md5 进行哈希处理。后台管理员帐号（角色 '1' 和 '3'）将被拒绝。

    参数:
        request: 请求体中包含 username 和 password 的 DRF 请求对象。

    返回:
        成功时返回 code=0 及令牌，
        失败时返回 code=1 及错误信息。
    """
    username = request.data['username']
    password = utils.md5value(request.data['password'])

    users = User.objects.filter(username=username, password=password)
    if len(users) == 0:
        return APIResponse(code=1, msg='用户名或密码错误')

    user = users[0]

    if user.role in ['1', '3']:
        return APIResponse(code=1, msg='该帐号为后台管理员帐号')

    data = {
        'username': username,
        'password': password,
        'token': md5value(username),
    }
    serializer = UserSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
        make_login_log(request)
        return APIResponse(code=0, msg='登录成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='用户名或密码错误')


@api_view(['POST'])
def register(request: HttpRequest) -> Any:
    """注册新的前台用户帐号。

    请求体中需要 'username'、'password' 和 'repassword'。
    验证密码是否匹配以及用户名是否已被占用。
    新用户将被分配 role=2（普通用户）和 status=0（未激活）。

    参数:
        request: 请求体中包含注册字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及新用户数据，
        失败时返回 code=1 及错误信息。
    """
    username = request.data.get('username', None)
    password = request.data.get('password', None)
    confirmed_password = request.data.get('repassword', None)

    if not username or not password or not confirmed_password:
        return APIResponse(code=1, msg='用户名或密码不能为空')

    if password != confirmed_password:
        return APIResponse(code=1, msg='密码不一致')

    existing_users = User.objects.filter(username=username)
    if len(existing_users) > 0:
        return APIResponse(code=1, msg='该用户名已存在')

    user_data = {
        'username': username,
        'password': password,
        'role': 2,
        'status': 0,
    }
    user_data.update({'password': utils.md5value(request.data['password'])})
    serializer = UserSerializer(data=user_data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='创建失败')


@api_view(['GET'])
def info(request: HttpRequest) -> Any:
    """通过 ID 获取用户的个人资料信息。

    查询参数:
        id: 用户的主键

    参数:
        request: DRF 请求对象。

    返回:
        返回 code=0 及用户序列化后的个人资料数据。
    """
    if request.method == 'GET':
        pk = request.GET.get('id', -1)
        user = User.objects.get(pk=pk)
        serializer = UserSerializer(user)
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def update(request: HttpRequest) -> Any:
    """更新用户的个人资料信息（仅限非敏感字段）。

    需要令牌认证。敏感字段（username、password、role）
    在保存前会从更新数据中剥离。

    查询参数:
        id: 用户的主键

    参数:
        request: 请求体中包含待更新字段的 DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的用户数据，
        用户不存在或序列化失败时返回 code=1。
    """
    pk = request.GET.get('id', -1)
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    data = request.data.copy()
    for protected_field in ('username', 'password', 'role'):
        data.pop(protected_field, None)

    serializer = UserSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='更新失败')


@api_view(['POST'])
@authentication_classes([TokenAuthtication])
def updatePwd(request: HttpRequest) -> Any:
    """修改用户密码。

    需要令牌认证。在应用更改前验证当前密码。
    新密码需提供两次且两次输入的值必须一致。

    查询参数:
        id: 用户的主键

    请求体字段:
        password:     当前密码（明文，比较时会被哈希处理）
        newPassword1: 新密码
        newPassword2: 新密码确认

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及更新后的用户数据，
        失败时返回 code=1 及错误信息。
    """
    pk = request.GET.get('id', -1)
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return APIResponse(code=1, msg='对象不存在')

    current_password = request.data.get('password', None)
    new_password_1 = request.data.get('newPassword1', None)
    new_password_2 = request.data.get('newPassword2', None)

    if not current_password or not new_password_1 or not new_password_2:
        return APIResponse(code=1, msg='不能为空')

    if user.password != utils.md5value(current_password):
        return APIResponse(code=1, msg='原密码不正确')

    if new_password_1 != new_password_2:
        return APIResponse(code=1, msg='两次密码不一致')

    data = request.data.copy()
    data.update({'password': utils.md5value(new_password_1)})
    serializer = UserSerializer(user, data=data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='更新成功', data=serializer.data)

    print(serializer.errors)
    return APIResponse(code=1, msg='更新失败')
