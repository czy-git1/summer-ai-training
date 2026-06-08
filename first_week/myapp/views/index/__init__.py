"""Index（前台）视图子包。

聚合所有前台视图模块：classification、tag、user、thing、comment、
order、notice 和 address。每个模块提供微信小程序客户端消费的 API 端点。
"""

from myapp.views.index.classification import *
from myapp.views.index.tag import *
from myapp.views.index.user import *
from myapp.views.index.thing import *
from myapp.views.index.comment import *
from myapp.views.index.order import *
from myapp.views.index.notice import *
from myapp.views.index.address import *
