"""Unit tests for authentication classes."""
import pytest
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory

from myapp.auth.authentication import AdminTokenAuthtication, TokenAuthtication
from myapp.models import User


class TestAdminTokenAuthentication:
    """Tests for AdminTokenAuthtication."""

    def test_valid_admin_token(self, db, user) -> None:
        """Should authenticate successfully with a valid admin token."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'test_admin_token_123'

        auth = AdminTokenAuthtication()
        # authenticate returns None on success (DRF convention)
        result = auth.authenticate(request)
        assert result is None

    def test_missing_token_raises(self, db) -> None:
        """Should raise AuthenticationFailed when no token is provided."""
        factory = APIRequestFactory()
        request = factory.get('/')

        auth = AdminTokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)

    def test_invalid_token_raises(self, db) -> None:
        """Should raise AuthenticationFailed with an invalid token."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'invalid_token_xyz'

        auth = AdminTokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)

    def test_foreground_user_raises(self, db, normal_user) -> None:
        """Should raise AuthenticationFailed for role='2' users."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_ADMINTOKEN'] = 'test_user_token_456'

        auth = AdminTokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)


class TestTokenAuthentication:
    """Tests for TokenAuthtication (frontend)."""

    def test_valid_user_token(self, db, normal_user) -> None:
        """Should authenticate successfully with a valid user token."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_TOKEN'] = 'test_user_token_456'

        auth = TokenAuthtication()
        result = auth.authenticate(request)
        assert result is None

    def test_missing_token_raises(self, db) -> None:
        """Should raise AuthenticationFailed when no token is provided."""
        factory = APIRequestFactory()
        request = factory.get('/')

        auth = TokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)

    def test_admin_user_raises(self, db, user) -> None:
        """Should raise AuthenticationFailed for admin role users."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_TOKEN'] = 'test_admin_token_123'

        auth = TokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)

    def test_empty_token_raises(self, db) -> None:
        """Should raise AuthenticationFailed when token is empty string."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.META['HTTP_TOKEN'] = ''

        auth = TokenAuthtication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(request)
