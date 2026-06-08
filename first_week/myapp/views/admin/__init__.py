"""管理后台视图模块包。

本包包含管理后台的视图模块，提供了对商品、评论、分类、标签、
记录、横幅、广告、公告、订单、登录/操作/错误日志以及用户管理
（含认证）的增删改查接口。
"""
from myapp.views.admin.overview import *
from myapp.views.admin.thing import *
from myapp.views.admin.comment import *
from myapp.views.admin.classification import *
from myapp.views.admin.tag import *
from myapp.views.admin.record import *
from myapp.views.admin.banner import *
from myapp.views.admin.ad import *
from myapp.views.admin.notice import *
from myapp.views.admin.order import *
from myapp.views.admin.loginLog import *
from myapp.views.admin.opLog import *
from myapp.views.admin.errorLog import *
from myapp.views.admin.user import *
