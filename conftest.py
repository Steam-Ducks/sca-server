"""
conftest.py — fixtures compartilhadas para testes de integração (sca-server).

IMPORTANTE: O backend agora usa JWT + perfis de acesso.
Todos os testes de integração precisam de um cliente autenticado.
Este conftest fornece `api_client` com perfil `super_admin` via
`force_authenticate` — bypassa o JWT sem precisar gerar tokens.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from users.models import Perfil, User, UsuarioPerfil


# ── Usuário autenticado ───────────────────────────────────────────────────────


@pytest.fixture
def super_admin_user(db):
    """
    Cria um User com perfil super_admin para os testes de integração.
    super_admin tem acesso a todos os endpoints — ideal para CTIs.
    """
    user = User.objects.create_user(
        username="test_integration",
        password="test_integration_pass",
        name="Integration Tester",
        is_active=True,
    )
    perfil = Perfil.objects.create(
        nome="Super Admin Test",
        permissoes="super_admin",
    )
    UsuarioPerfil.objects.create(usuario=user, perfil=perfil)
    return user


@pytest.fixture
def api_user(super_admin_user):
    """
    Alias de super_admin_user — mantém compatibilidade com testes
    que usam o nome anterior da fixture (ex: audit/tests/test_views.py).
    """
    return super_admin_user


@pytest.fixture
def api_client(super_admin_user):
    """
    APIClient autenticado com super_admin.
    Substitui o `api_client` anterior (sem autenticação).

    Uso nos testes:
        def test_algo(self, api_client):
            response = api_client.get("/api/dashboard/kpis/")
            assert response.status_code == 200
    """
    client = APIClient()
    client.force_authenticate(user=super_admin_user)
    return client


# ── Request factories ─────────────────────────────────────────────────────────


@pytest.fixture
def api_request_factory():
    """Plain APIRequestFactory — use with force_authenticate when needed."""
    return APIRequestFactory()


@pytest.fixture
def auth_request_factory(monkeypatch):
    """
    APIRequestFactory pre-wrapped with force_authenticate and super_admin
    permission. Replaces the local _AuthFactory pattern in imports and
    monitoring tests.
    """
    from users import permissions as perm_mod

    monkeypatch.setattr(perm_mod, "_get_permissao", lambda u: "super_admin")
    base = APIRequestFactory()
    user = get_user_model()(username="_test", is_active=True)

    class _AuthFactory:
        def get(self, *args, **kwargs):
            req = base.get(*args, **kwargs)
            force_authenticate(req, user=user)
            return req

        def post(self, *args, **kwargs):
            req = base.post(*args, **kwargs)
            force_authenticate(req, user=user)
            return req

    return _AuthFactory()


# ── Assertion helpers ─────────────────────────────────────────────────────────


def assert_status(response, expected_code):
    assert response.status_code == expected_code, (
        f"Expected HTTP {expected_code}, got {response.status_code}. "
        f"Response data: {getattr(response, 'data', None)}"
    )


def assert_fields(data, *fields):
    for field in fields:
        assert field in data, (
            f"Field {field!r} not found in response. "
            f"Available keys: {list(data.keys())}"
        )
