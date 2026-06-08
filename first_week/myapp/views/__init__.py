"""myapp Django 应用的视图包。

聚合 admin 和 index（前台）子包中的所有视图模块，
使它们可以通过单一的导入路径使用。
"""

from myapp.views.admin import *
from myapp.views.index import *
