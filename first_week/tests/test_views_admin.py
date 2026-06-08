"""Integration tests for admin API views.

Tests the admin management backend endpoints under /myapp/admin/.
Requires a valid admin_token header for authenticated endpoints.
"""
import json

import pytest
from django.test import Client

ADMIN_HEADER = {'HTTP_ADMINTOKEN': 'test_admin_token_123'}
JSON_CONTENT = 'application/json'


class TestAdminLogin:
    """Tests for admin_login endpoint."""

    URL = '/myapp/admin/adminLogin'

    def test_login_success(self, db, client, user) -> None:
        """Should log in an admin user and return a token."""
        resp = client.post(
            self.URL,
            data=json.dumps({
                'username': 'testuser',
                'password': '123456',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert data['msg'] == '登录成功'
        assert 'admin_token' in data.get('data', {})

    def test_login_wrong_password(self, db, client, user) -> None:
        """Should reject login with wrong password."""
        resp = client.post(
            self.URL,
            data=json.dumps({
                'username': 'testuser',
                'password': 'wrongpassword',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 1

    def test_login_nonexistent_user(self, db, client) -> None:
        """Should reject login for nonexistent user."""
        resp = client.post(
            self.URL,
            data=json.dumps({
                'username': 'nonexistent',
                'password': '123456',
            }),
            content_type=JSON_CONTENT,
        )
        assert resp.json()['code'] == 1


class TestAdminOverview:
    """Tests for admin dashboard overview endpoints."""

    def test_count(self, db, client, user) -> None:
        """Should return entity counts when authenticated."""
        resp = client.get('/myapp/admin/overview/count', **ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert 'thingCount' in data['data']

    def test_count_unauthenticated(self, db, client) -> None:
        """Should reject count request without admin token."""
        resp = client.get('/myapp/admin/overview/count')
        assert resp.status_code == 403

    def test_sys_info(self, db, client, user) -> None:
        """Should return system info when authenticated."""
        resp = client.get('/myapp/admin/overview/sysInfo', **ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert 'sysName' in data['data']


class TestAdminThingCRUD:
    """Tests for admin Thing (product) CRUD endpoints."""

    URL_PREFIX = '/myapp/admin/thing'

    def test_list(self, db, client, user, thing) -> None:
        """Should list things with pagination."""
        resp = client.get(f'{self.URL_PREFIX}/list', **ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0
        assert 'list' in data['data']
        assert 'total' in data['data']

    def test_detail(self, db, client, user, thing) -> None:
        """Should return thing detail by id."""
        resp = client.get(
            f'{self.URL_PREFIX}/detail?id={thing.id}', **ADMIN_HEADER
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_detail_not_found(self, db, client, user) -> None:
        """Should return error for non-existent thing."""
        resp = client.get(
            f'{self.URL_PREFIX}/detail?id=99999', **ADMIN_HEADER
        )
        assert resp.json()['code'] == 1

    def test_create(self, db, client, user, classification) -> None:
        """Should create a new thing."""
        resp = client.post(
            f'{self.URL_PREFIX}/create',
            data=json.dumps({
                'title': 'New Product',
                'classification': classification.id,
                'price': '199.00',
            }),
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_update(self, db, client, user, thing) -> None:
        """Should update an existing thing."""
        resp = client.post(
            f'{self.URL_PREFIX}/update?id={thing.id}',
            data=json.dumps({'title': 'Updated Product'}),
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_delete(self, db, client, user, thing) -> None:
        """Should delete a thing."""
        resp = client.post(
            f'{self.URL_PREFIX}/delete?id={thing.id}',
            data='{}',
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestAdminUserManagement:
    """Tests for admin user management endpoints."""

    def test_list_users(self, db, client, user) -> None:
        """Should list users with pagination."""
        resp = client.get('/myapp/admin/user/list', **ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data['code'] == 0

    def test_create_user(self, db, client, user) -> None:
        """Should create a new user."""
        resp = client.post(
            '/myapp/admin/user/create',
            data=json.dumps({
                'username': 'newadmin',
                'password': 'pass123',
                'role': '0',
            }),
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_user_info(self, db, client, user) -> None:
        """Should return user info by id."""
        resp = client.get(
            f'/myapp/admin/user/info?id={user.id}', **ADMIN_HEADER
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestAdminClassification:
    """Tests for admin Classification CRUD."""

    def test_list(self, db, client, user, classification) -> None:
        """Should list classifications."""
        resp = client.get(
            '/myapp/admin/classification/list', **ADMIN_HEADER
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_create(self, db, client, user) -> None:
        """Should create a new classification."""
        resp = client.post(
            '/myapp/admin/classification/create',
            data=json.dumps({'title': 'New Category', 'pid': -1}),
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_delete(self, db, client, user, classification) -> None:
        """Should delete a classification."""
        resp = client.post(
            f'/myapp/admin/classification/delete?id={classification.id}',
            data='{}',
            content_type=JSON_CONTENT,
            **ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()['code'] == 0


class TestAdminLogs:
    """Tests for log viewing endpoints."""

    def test_login_log_list(self, db, client, user) -> None:
        """Should list login logs."""
        resp = client.get('/myapp/admin/loginLog/list', **ADMIN_HEADER)
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_op_log_list(self, db, client, user) -> None:
        """Should list operation logs."""
        resp = client.get('/myapp/admin/opLog/list', **ADMIN_HEADER)
        assert resp.status_code == 200
        assert resp.json()['code'] == 0

    def test_error_log_list(self, db, client, user) -> None:
        """Should list error logs."""
        resp = client.get('/myapp/admin/errorLog/list', **ADMIN_HEADER)
        assert resp.status_code == 200
        assert resp.json()['code'] == 0
