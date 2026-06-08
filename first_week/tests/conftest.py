"""Pytest fixtures for the python_shop test suite."""
import os

import django
import pytest
from django.test import Client

# Ensure Django settings are configured before any test runs.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from myapp.models import (  # noqa: E402
    Address,
    Classification,
    Comment,
    Tag,
    Thing,
    User,
)
from myapp.serializers import (  # noqa: E402
    ClassificationSerializer,
    CommentSerializer,
    TagSerializer,
    ThingSerializer,
    UserSerializer,
)


@pytest.fixture
def client() -> Client:
    """Return a Django test client instance."""
    return Client()


@pytest.fixture
def classification(db) -> Classification:
    """Create and return a sample Classification instance."""
    return Classification.objects.create(
        title='Test Category',
        pid=-1,
    )


@pytest.fixture
def tag(db) -> Tag:
    """Create and return a sample Tag instance."""
    return Tag.objects.create(title='Test Tag')


@pytest.fixture
def user(db) -> User:
    """Create and return a sample User instance with admin role."""
    return User.objects.create(
        username='testuser',
        password='e10adc3949ba59abbe56e057f20f883e',  # MD5 of '123456'
        role='0',
        status='0',
        admin_token='test_admin_token_123',
    )


@pytest.fixture
def normal_user(db) -> User:
    """Create and return a sample normal (non-admin) User instance."""
    return User.objects.create(
        username='normaluser',
        password='e10adc3949ba59abbe56e057f20f883e',
        role='2',
        status='0',
        token='test_user_token_456',
    )


@pytest.fixture
def thing(db, classification, tag) -> Thing:
    """Create and return a sample Thing instance."""
    instance = Thing.objects.create(
        title='Test Product',
        classification=classification,
        price='99.00',
        status='0',
        repertory=100,
    )
    instance.tag.add(tag)
    return instance


@pytest.fixture
def comment(db, user, thing) -> Comment:
    """Create and return a sample Comment instance."""
    return Comment.objects.create(
        content='Great product!',
        user=user,
        thing=thing,
    )


@pytest.fixture
def address(db, normal_user) -> Address:
    """Create and return a sample Address instance."""
    return Address.objects.create(
        user=normal_user,
        name='Home',
        mobile='13800138000',
        desc='123 Main Street',
        default=True,
    )
