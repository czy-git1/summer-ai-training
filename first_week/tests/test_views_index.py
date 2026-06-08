"""Integration tests for frontend (index) API views.

Tests the customer-facing endpoints under /myapp/index/.
Most endpoints require a valid user token (HTTP_TOKEN header).
"""
import json

import pytest

USER_HEADER = {'HTTP_TOKEN': 'test_user_token_456'}
JSON_CONTENT = 'application/json'


class TestIndexClassification:
    """Tests for index classification endpoint."""

    URL = '/myapp/index/classification/list'

    def test_list_returns_tree(self, db, client, classification) -> None:
        """Should return classification tree with '全部' as first node."""
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert len(data['data']) >= 1
        assert data['data'][0]['title'] == '全部'
        assert data['data'][0]['key'] == -1

    def test_list_empty_database(self, db, client) -> None:
        """Should return only the '全部' node when no classifications exist."""
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert data['data'] == [{
            'key': -1,
            'title': '全部',
            'isParent': True,
            'children': [],
        }]


class TestIndexThing:
    """Tests for index Thing (product) endpoints."""

    URL_PREFIX = '/myapp/index/thing'

    def test_list(self, db, client, thing) -> None:
        """Should list things."""
        resp = client.get(f'{self.URL_PREFIX}/list')
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_list_with_keyword(self, db, client, thing) -> None:
        """Should filter things by keyword."""
        resp = client.get(
            f'{self.URL_PREFIX}/list?keyword=Test'
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0

    def test_detail(self, db, client, thing) -> None:
        """Should return thing detail."""
        resp = client.get(
            f'{self.URL_PREFIX}/detail?id={thing.id}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_detail_not_found(self, db, client) -> None:
        """Should return error for non-existent thing."""
        resp = client.get(f'{self.URL_PREFIX}/detail?id=99999')
        assert resp.json()['code'] == 1

    def test_increase_wish_count(self, db, client, thing) -> None:
        """Should increase the wish count of a thing."""
        resp = client.post(
            f'{self.URL_PREFIX}/increaseWishCount?id={thing.id}',
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_get_wish_list(self, db, client, normal_user) -> None:
        """Should return wish list for a user."""
        resp = client.get(
            f'{self.URL_PREFIX}/getWishThingList?username={normal_user.username}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] in [0, 1]

    def test_get_collect_list(self, db, client, normal_user) -> None:
        """Should return collect list for a user."""
        resp = client.get(
            f'{self.URL_PREFIX}/getCollectThingList?username={normal_user.username}'
        )
        assert resp.status_code == 200


class TestIndexUser:
    """Tests for index user endpoints."""

    URL_PREFIX = '/myapp/index/user'

    def test_login_success(self, db, client, normal_user) -> None:
        """Should log in a normal user and return a token."""
        resp = client.post(
            f'{self.URL_PREFIX}/login',
            data=json.dumps({
                'username': 'normaluser',
                'password': '123456',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert data['msg'] == '登录成功'

    def test_login_wrong_password(self, db, client, normal_user) -> None:
        """Should reject login with wrong password."""
        resp = client.post(
            f'{self.URL_PREFIX}/login',
            data=json.dumps({
                'username': 'normaluser',
                'password': 'wrong',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.json()['code'] == 1

    def test_register_new_user(self, db, client) -> None:
        """Should register a new user."""
        resp = client.post(
            f'{self.URL_PREFIX}/register',
            data=json.dumps({
                'username': 'newuser',
                'password': 'password123',
                'repassword': 'password123',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_register_duplicate_username(self, db, client, normal_user) -> None:
        """Should reject registration with duplicate username."""
        resp = client.post(
            f'{self.URL_PREFIX}/register',
            data=json.dumps({
                'username': 'normaluser',
                'password': 'password123',
                'repassword': 'password123',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.json()['code'] == 1

    def test_register_password_mismatch(self, db, client) -> None:
        """Should reject registration when passwords don't match."""
        resp = client.post(
            f'{self.URL_PREFIX}/register',
            data=json.dumps({
                'username': 'anotheruser',
                'password': 'password123',
                'repassword': 'different',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.json()['code'] == 1

    def test_info(self, db, client, normal_user) -> None:
        """Should return user info by id."""
        resp = client.get(
            f'{self.URL_PREFIX}/info?id={normal_user.id}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_update_authenticated(self, db, client, normal_user) -> None:
        """Should update user profile when authenticated."""
        resp = client.post(
            f'{self.URL_PREFIX}/update?id={normal_user.id}',
            data=json.dumps({'nickname': 'New Nick'}),
            content_type=JSON_CONTENT,
            **USER_HEADER,
        )
        assert resp.status_code == 200


class TestIndexComment:
    """Tests for index Comment endpoints."""

    URL_PREFIX = '/myapp/index/comment'

    def test_list_requires_thing_id(self, db, client) -> None:
        """Should return error when thingId is missing."""
        resp = client.get(f'{self.URL_PREFIX}/list')
        assert resp.json()['code'] == 1

    def test_list_with_thing_id(self, db, client, comment) -> None:
        """Should list comments for a given thingId."""
        resp = client.get(
            f'{self.URL_PREFIX}/list?thingId={comment.thing.id}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_create_comment(self, db, client, normal_user, thing) -> None:
        """Should create a comment for a thing."""
        resp = client.post(
            f'{self.URL_PREFIX}/create',
            data=json.dumps({
                'content': 'Nice product!',
                'user': normal_user.id,
                'thing': thing.id,
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestIndexTag:
    """Tests for index Tag endpoint."""

    def test_list_tags(self, db, client, tag) -> None:
        """Should list all tags."""
        resp = client.get('/myapp/index/tag/list')
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestIndexNotice:
    """Tests for index Notice endpoint."""

    URL = '/myapp/index/notice/list_api'

    def test_list_notices(self, db, client) -> None:
        """Should list notices (empty list is valid response)."""
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestIndexOrder:
    """Tests for index Order endpoints."""

    URL_PREFIX = '/myapp/index/order'

    def test_list_own_orders(self, db, client, normal_user) -> None:
        """Should list orders for the given userId."""
        resp = client.get(
            f'{self.URL_PREFIX}/list?userId={normal_user.id}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_create_order(self, db, client, normal_user, thing) -> None:
        """Should create an order when authenticated."""
        resp = client.post(
            f'{self.URL_PREFIX}/create',
            data=json.dumps({
                'user': normal_user.id,
                'thing': thing.id,
                'count': 1,
            }),
            content_type=JSON_CONTENT,
            **USER_HEADER,
        )
        assert resp.status_code == 200


class TestIndexAddress:
    """Tests for index Address endpoints."""

    URL_PREFIX = '/myapp/index/address'

    def test_list_requires_user_id(self, db, client) -> None:
        """Should return error when userId is missing."""
        resp = client.get(f'{self.URL_PREFIX}/list')
        assert resp.json()['code'] == 1

    def test_list_user_addresses(self, db, client, normal_user, address) -> None:
        """Should list addresses for the given userId."""
        resp = client.get(
            f'{self.URL_PREFIX}/list?userId={normal_user.id}'
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_create_address(self, db, client, normal_user) -> None:
        """Should create an address when authenticated."""
        resp = client.post(
            f'{self.URL_PREFIX}/create',
            data={
                'desc': 'Office Address',
                'user': normal_user.id,
                'name': 'Office',
                'mobile': '13900139000',
            },
            **USER_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0
