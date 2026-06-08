"""Unit tests for the permission module."""
from rest_framework.test import APIRequestFactory

from myapp.models import User
from myapp.permission.permission import isDemoAdminUser


class TestIsDemoAdminUser:
    """Tests for isDemoAdminUser()."""

    def test_demo_admin_detected(self, db) -> None:
        """Should return True for a user with role='3' (demo admin)."""
        User.objects.create(
            username='demo_admin',
            password='hash',
            role='3',
            admin_token='demo_token_789',
        )

        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'demo_token_789'

        assert isDemoAdminUser(request) is True

    def test_normal_admin_returns_false(self, db, user) -> None:
        """Should return False for a regular admin user (role='0')."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'test_admin_token_123'

        assert isDemoAdminUser(request) is False

    def test_missing_token_returns_false(self, db) -> None:
        """Should return False when no admin_token header is present."""
        factory = APIRequestFactory()
        request = factory.get('/')

        assert isDemoAdminUser(request) is False

    def test_invalid_token_returns_false(self, db) -> None:
        """Should return False when token does not match any user."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'nonexistent_token'

        assert isDemoAdminUser(request) is False
