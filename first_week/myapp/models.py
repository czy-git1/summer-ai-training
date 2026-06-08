"""
Python Shop 电商应用的数据库模型。

本模块使用 Django ORM 定义完整的数据层，涵盖：

- **核心业务实体:**    User（用户）、Thing（商品）、Order（订单）、Comment（评论）
- **分类与元数据:**    Classification（分类）、Tag（标签）
- **用户管理数据:**    Address（地址）、Record（浏览历史）
- **运营日志:**        LoginLog（登录日志）、OpLog（操作日志）、ErrorLog（错误日志）、OrderLog（订单日志）
- **内容管理:**        Banner（横幅广告）、Ad（广告）、Notice（公告）

所有表通过 ``Meta.db_table`` 选项使用 ``b_`` 前缀（如 ``b_user``），
面向 MySQL / MariaDB 数据库后端。
"""

from django.db import models


class User(models.Model):
    """用户帐户与个人资料。

    属性:
        username (CharField):      登录名（最长 50 字符）。
        password (CharField):      登录密码（最长 50 字符，开发环境为明文）。
        role (CharField):          ``'0'`` = 管理员，``'1'`` = 普通用户。
        status (CharField):        ``'0'`` = 正常，``'1'`` = 封号。
        nickname (CharField):      对其他用户显示的昵称。
        avatar (FileField):        头像图片，上传至 ``avatar/`` 目录。
        mobile (CharField):        手机号码（最长 13 字符）。
        email (CharField):         电子邮箱（最长 50 字符）。
        gender (CharField):        ``'M'`` = 男，``'F'`` = 女。
        description (TextField):   简短个人简介或自我介绍。
        create_time (DateTimeField):  自动设置的帐户创建时间戳。
        score (IntegerField):      积分 / 信用分（默认 0）。
        push_email (CharField):    用于推送通知的邮箱地址。
        push_switch (BooleanField):   是否开启推送通知。
        admin_token (CharField):   后台管理认证令牌（32 字符）。
        token (CharField):         前端用户认证令牌（32 字符）。
    """

    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    ROLE_CHOICES = (
        ('0', '管理员'),
        ('1', '普通用户'),
    )
    STATUS_CHOICES = (
        ('0', '正常'),
        ('1', '封号'),
    )
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=True)
    role = models.CharField(max_length=2, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    nickname = models.CharField(blank=True, null=True, max_length=20)
    avatar = models.FileField(upload_to='avatar/', null=True)
    mobile = models.CharField(max_length=13, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    description = models.TextField(max_length=200, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    score = models.IntegerField(default=0, blank=True, null=True)
    push_email = models.CharField(max_length=40, blank=True, null=True)
    push_switch = models.BooleanField(blank=True, null=True, default=False)
    admin_token = models.CharField(max_length=32, blank=True, null=True)
    token = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = "b_user"


class Tag(models.Model):
    """商品标签，用于灵活分类。

    属性:
        title (CharField):        标签显示文本（最长 100 字符）。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_tag"


class Classification(models.Model):
    """层级化商品分类。

    通过 ``pid`` 字段（父级 ID）支持父子树结构。
    顶级分类的 ``pid`` = -1。

    属性:
        pid (IntegerField):       父级分类 ID（根节点为 -1）。
        title (CharField):        分类名称（最长 100 字符）。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    list_display = ("title", "id")
    id = models.BigAutoField(primary_key=True)
    pid = models.IntegerField(blank=True, null=True, default=-1)
    title = models.CharField(max_length=100, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        db_table = "b_classification"


class Thing(models.Model):
    """商品 / 物品列表（商城的中心实体）。

    属性:
        classification (FK):      该商品所属的分类。
        tag (M2M):                关联的标签。
        title (CharField):        商品名称（最长 100 字符）。
        cover (ImageField):       封面图片，上传至 ``cover/`` 目录。
        description (TextField):  完整商品描述（最长 1000 字符）。
        price (CharField):        显示价格（以字符串存储，最长 50 字符）。
        status (CharField):       ``'0'`` = 上架，``'1'`` = 下架。
        repertory (IntegerField): 库存数量。
        score (IntegerField):     平均评分 / 加权分数。
        create_time (DateTimeField):  自动设置的创建时间戳。
        pv (IntegerField):        页面浏览量计数器。
        recommend_count (IntegerField):  推荐计数。
        wish (M2M -> User):       将此商品加入心愿单的用户。
        wish_count (IntegerField):   反范式化的心愿单计数器。
        collect (M2M -> User):    将此商品加入收藏的用户。
        collect_count (IntegerField): 反范式化的收藏计数器。
    """

    STATUS_CHOICES = (
        ('0', '上架'),
        ('1', '下架'),
    )
    id = models.BigAutoField(primary_key=True)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='classification_thing')
    tag = models.ManyToManyField(Tag, blank=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    cover = models.ImageField(upload_to='cover/', null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    price = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    repertory = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    pv = models.IntegerField(default=0)
    recommend_count = models.IntegerField(default=0)
    wish = models.ManyToManyField(User, blank=True, related_name="wish_things")
    wish_count = models.IntegerField(default=0)
    collect = models.ManyToManyField(User, blank=True, related_name="collect_things")
    collect_count = models.IntegerField(default=0)

    class Meta:
            db_table = "b_thing"


class Comment(models.Model):
    """用户对商品的评论。

    属性:
        content (CharField):      评论内容（最长 200 字符）。
        user (FK -> User):        评论作者。
        thing (FK -> Thing):      被评论的商品。
        comment_time (DateTimeField):  自动设置的评论时间戳。
        like_count (IntegerField):    收到的点赞数。
    """

    id = models.BigAutoField(primary_key=True)
    content = models.CharField(max_length=200, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_comment')
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_comment')
    comment_time = models.DateTimeField(auto_now_add=True, null=True)
    like_count = models.IntegerField(default=0)

    class Meta:
        db_table = "b_comment"


class Record(models.Model):
    """用户浏览 / 查看历史记录条目。

    追踪用户查看了哪些商品以及查看时所在的分类。

    属性:
        user (FK -> User):          浏览用户。
        thing (FK -> Thing):        被查看的商品。
        title (CharField):          查看时商品名称的快照。
        classification (FK -> Classification):  查看时的分类上下文。
        record_time (DateTimeField):  自动设置的查看时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_record')
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_record')
    title = models.CharField(max_length=100, blank=True, null=True)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, null=True,
                                       related_name='classification')
    record_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_record"


class LoginLog(models.Model):
    """用户登录事件的审计日志。

    属性:
        username (CharField):      登录时使用的用户名。
        ip (CharField):            客户端 IP 地址。
        ua (CharField):            User-Agent 头字符串。
        log_time (DateTimeField):  自动设置的登录时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    ua = models.CharField(max_length=200, blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_login_log"


class OpLog(models.Model):
    """记录服务器处理的每个 HTTP 请求的操作日志。

    属性:
        re_ip (CharField):         客户端 IP 地址（``re_`` = request）。
        re_time (DateTimeField):   自动设置的请求时间戳。
        re_url (CharField):        请求 URL 路径。
        re_method (CharField):     HTTP 方法（GET、POST 等）。
        re_content (CharField):    请求体 / 负载快照。
        access_time (CharField):   额外的时间信息（字符串）。
    """

    id = models.BigAutoField(primary_key=True)
    re_ip = models.CharField(max_length=100, blank=True, null=True)
    re_time = models.DateTimeField(auto_now_add=True, null=True)
    re_url = models.CharField(max_length=200, blank=True, null=True)
    re_method = models.CharField(max_length=10, blank=True, null=True)
    re_content = models.CharField(max_length=200, blank=True, null=True)
    access_time = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = "b_op_log"


class ErrorLog(models.Model):
    """应用程序捕获的错误 / 异常日志。

    属性:
        ip (CharField):            发生错误时的客户端 IP。
        url (CharField):           触发错误的请求 URL。
        method (CharField):        失败请求的 HTTP 方法。
        content (CharField):       错误消息或堆栈跟踪摘录。
        log_time (DateTimeField):  自动设置的错误时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    content = models.CharField(max_length=200, blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_error_log"


class Order(models.Model):
    """客户订单。

    订单状态码（存储在 ``status`` 中）：
        - ``'1'`` -- 未支付
        - ``'2'`` -- 已支付
        - ``'7'`` -- 已取消

    属性:
        order_number (CharField):   唯一订单标识符（最长 13 字符）。
        user (FK -> User):          下订单的客户。
        thing (FK -> Thing):        订购的商品。
        count (IntegerField):       订购数量。
        status (CharField):         订单状态（见上方状态码）。
        order_time (DateTimeField): 自动设置的订单创建时间戳。
        pay_time (DateTimeField):   手动设置的支付时间戳。
        receiver_name (CharField):  收货人姓名。
        receiver_address (CharField):  收货地址。
        receiver_phone (CharField):    收货人电话号码。
        remark (CharField):         客户备注（最长 30 字符）。
    """

    id = models.BigAutoField(primary_key=True)
    order_number = models.CharField(max_length=13, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_order')
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_order')
    count = models.IntegerField(default=0)
    status = models.CharField(max_length=2, blank=True, null=True)  # 1=未支付, 2=已支付, 7=已取消
    order_time = models.DateTimeField(auto_now_add=True, null=True)
    pay_time = models.DateTimeField(null=True)
    receiver_name = models.CharField(max_length=20, blank=True, null=True)
    receiver_address = models.CharField(max_length=50, blank=True, null=True)
    receiver_phone = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = "b_order"


class OrderLog(models.Model):
    """订单状态变更的审计追踪。

    属性:
        user (FK -> User):      执行操作的行为人。
        thing (FK -> Thing):    操作关联的商品。
        action (CharField):     操作代码 / 描述（最长 2 字符）。
        log_time (DateTimeField):  自动设置的条目时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_order_log')
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_order_log')
    action = models.CharField(max_length=2, blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_order_log"


class Banner(models.Model):
    """链接到商品的轮播图 / 主横幅。

    属性:
        image (ImageField):       横幅图片，上传至 ``banner/`` 目录。
        thing (FK -> Thing):      横幅链接到的商品。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    image = models.ImageField(upload_to='banner/', null=True)
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_banner')
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_banner"


class Ad(models.Model):
    """带有外部链接的广告。

    属性:
        image (ImageField):       广告图片，上传至 ``ad/`` 目录。
        link (CharField):         广告指向的外部链接（最长 500 字符）。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    image = models.ImageField(upload_to='ad/', null=True)
    link = models.CharField(max_length=500, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_ad"


class Notice(models.Model):
    """系统公告 / 通知。

    属性:
        title (CharField):        公告标题（最长 100 字符）。
        content (CharField):      公告正文（最长 1000 字符）。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    content = models.CharField(max_length=1000, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_notice"


class Address(models.Model):
    """用户收货地址。

    属性:
        user (FK -> User):          所属用户。
        name (CharField):           收件人全名（最长 100 字符）。
        mobile (CharField):         收件人电话号码（最长 30 字符）。
        desc (CharField):           完整地址描述（最长 300 字符）。
        default (BooleanField):     是否为用户的默认地址。
        create_time (DateTimeField):  自动设置的创建时间戳。
    """

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_address')
    name = models.CharField(max_length=100, blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)
    desc = models.CharField(max_length=300, blank=True, null=True)
    default = models.BooleanField(blank=True, null=True, default=False)  # 是否为默认地址
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_address"
