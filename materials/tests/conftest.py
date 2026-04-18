import pytest


@pytest.fixture
def rf():
    from django.test import RequestFactory
    return RequestFactory()
