"""
Python Shop 模型的 Django REST Framework 序列化器。

每个序列化器对应 ``myapp.models`` 中的一个模型类，控制模型实例
如何在 API 响应中与 JSON 互相转换。额外的只读字段
（如 ``classification_title``、``username``）将关联对象的数据
拉入扁平表示，方便前端使用。

日期时间字段统一格式化为 ``'%Y-%m-%d %H:%M:%S'``。
"""

from rest_framework import serializers

from myapp.models import (
    Thing, Classification, Tag, User, Comment, Record,
    LoginLog, Order, OrderLog, OpLog, Banner, Ad, Notice,
    ErrorLog, Address,
)


class ThingSerializer(serializers.ModelSerializer):
    """完整的 Thing（商品）表示，包含 M2M 字段。

    额外字段:
        classification_title:  通过外键获取的只读分类名称。
    """

    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        fields = '__all__'


class DetailThingSerializer(serializers.ModelSerializer):
    """Thing 详情视图 -- 排除 ``wish`` 和 ``collect`` M2M 字段。

    用于商品详情页，心愿单/收藏列表不在行内展开的场景。

    额外字段:
        classification_title:  只读分类名称。
    """

    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        exclude = ('wish', 'collect',)


class UpdateThingSerializer(serializers.ModelSerializer):
    """Thing 更新负载 -- 排除 ``wish`` 和 ``collect`` M2M 字段。

    防止在商品编辑操作中意外修改心愿单/收藏关系。

    额外字段:
        classification_title:  只读分类名称。
    """

    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        exclude = ('wish', 'collect',)


class ListThingSerializer(serializers.ModelSerializer):
    """Thing 列表视图 -- 排除 M2M 字段和长描述。

    针对只需要摘要数据的列表/网格视图进行优化。

    额外字段:
        classification_title:  只读分类名称。
    """

    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        exclude = ('wish', 'collect', 'description',)


class ClassificationSerializer(serializers.ModelSerializer):
    """商品分类的扁平序列化。"""

    class Meta:
        model = Classification
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """商品标签的扁平序列化。"""

    class Meta:
        model = Tag
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """用户帐户序列化，包含格式化后的 ``create_time``。

    注意：``password`` 字段被包含在内（原始代码注释掉了
    ``exclude = ('password',)`` 这一行）-- 在生产环境中应
    注意在持久化之前对密码进行哈希处理。
    """

    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = User
        fields = '__all__'
        # exclude = ('password',)


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化，包含反范式化的关联字段。

    额外字段:
        title:     关联 Thing 的只读商品标题。
        username:  关联 User 的只读作者用户名。
    """

    comment_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    title = serializers.ReadOnlyField(source='thing.title')
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Comment
        fields = ['id', 'content', 'comment_time', 'like_count', 'thing', 'user', 'title', 'username']


class RecordSerializer(serializers.ModelSerializer):
    """浏览历史记录的序列化。"""

    class Meta:
        model = Record
        fields = '__all__'


class LoginLogSerializer(serializers.ModelSerializer):
    """登录日志条目的序列化，包含格式化后的时间戳。"""

    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = LoginLog
        fields = '__all__'


class OpLogSerializer(serializers.ModelSerializer):
    """操作日志条目的序列化。

    ``re_*`` 前缀字段表示请求范围的数据
    （IP、URL、HTTP 方法、请求体、时间）。
    """

    re_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = OpLog
        fields = '__all__'


class ErrorLogSerializer(serializers.ModelSerializer):
    """错误日志条目的序列化，包含格式化后的时间戳。"""

    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = ErrorLog
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """订单序列化，包含格式化后的时间戳和反范式化字段。

    该序列化器声明了 ``expect_time`` 和 ``return_time`` 作为额外的
    DateTime 字段，这些字段在 Order 模型中不存在 --
    可能是供业务逻辑层计算值使用的。

    额外只读字段:
        username:  客户用户名（通过外键到 User）。
        title:     商品标题（通过外键到 Thing）。
        price:     商品价格（通过外键到 Thing）。
        cover:     商品封面图片（FileField，通过外键到 Thing）。
    """

    order_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    expect_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    return_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    username = serializers.ReadOnlyField(source='user.username')
    title = serializers.ReadOnlyField(source='thing.title')
    price = serializers.ReadOnlyField(source='thing.price')
    cover = serializers.FileField(source='thing.cover', required=False)

    class Meta:
        model = Order
        fields = '__all__'


class OrderLogSerializer(serializers.ModelSerializer):
    """订单审计日志条目的序列化。"""

    class Meta:
        model = OrderLog
        fields = '__all__'


class BannerSerializer(serializers.ModelSerializer):
    """横幅序列化，包含格式化后的时间戳和反范式化的商品标题。

    额外字段:
        title:  关联 Thing 的只读商品标题。
    """

    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    title = serializers.ReadOnlyField(source='thing.title')

    class Meta:
        model = Banner
        fields = '__all__'


class AdSerializer(serializers.ModelSerializer):
    """广告序列化，包含格式化后的时间戳。"""

    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Ad
        fields = '__all__'


class NoticeSerializer(serializers.ModelSerializer):
    """系统公告序列化，包含格式化后的时间戳。"""

    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Notice
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    """用户地址序列化，包含格式化后的时间戳。"""

    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Address
        fields = '__all__'
