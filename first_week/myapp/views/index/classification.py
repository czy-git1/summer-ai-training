"""前台商城 API 的分类视图。

提供分类树端点，返回商城商品分类系统的层级分类结构，
包含父子关系。
"""

from typing import Any

from django.db import connection
from django.http import HttpRequest
from rest_framework.decorators import api_view

from myapp.handler import APIResponse
from myapp.utils import dict_fetchall


@api_view(['GET'])
def list_api(request: HttpRequest) -> Any:
    """返回分类树，顶部包含"全部"节点。

    查询 b_classification 表构建嵌套的分类树。
    顶层分类（pid=-1）成为父节点；其关联的子分类成为子节点。
    始终在开头插入一个 key=-1、title="全部" 的合成根节点。

    参数:
        request: DRF 请求对象。

    返回:
        成功时返回 code=0 及分类树节点列表的 APIResponse。
    """
    if request.method == 'GET':
        sql = (
            'SELECT x.id AS parentId, x.title AS parentTitle, '
            'y.id AS childId, y.title AS childTitle '
            'FROM b_classification AS x '
            'LEFT JOIN b_classification AS y ON y.pid = x.id '
            'WHERE x.pid = -1 '
            'ORDER BY x.create_time DESC'
        )
        tree_nodes = [{
            'key': -1,
            'title': '全部',
            'isParent': True,
            'children': [],
        }]
        with connection.cursor() as cursor:
            cursor.execute(sql)
            flat_results = dict_fetchall(cursor)

            for row in flat_results:
                found_parent = False
                for parent_node in tree_nodes:
                    if parent_node['key'] == row['parentId']:
                        found_parent = True
                        if row['childId']:
                            parent_node['children'].append({
                                'key': row['childId'],
                                'title': row['childTitle'],
                                'isParent': False,
                            })
                        break

                if not found_parent:
                    new_parent = {
                        'key': row['parentId'],
                        'title': row['parentTitle'],
                        'isParent': True,
                        'children': [],
                    }
                    if row['childId']:
                        new_parent['children'].append({
                            'key': row['childId'],
                            'title': row['childTitle'],
                            'isParent': False,
                        })
                    tree_nodes.append(new_parent)

        return APIResponse(code=0, msg='查询成功', data=tree_nodes)
