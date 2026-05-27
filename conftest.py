"""
conftest.py — fixtures compartilhadas para testes de integração (sca-server).

IMPORTANTE: O backend agora usa JWT + perfis de acesso.
Todos os testes de integração precisam de um cliente autenticado.
Este conftest fornece `api_client` com perfil `super_admin` via
`force_authenticate` — bypassa o JWT sem precisar gerar tokens.
"""

from datetime import datetime, timezone

import pytest
from rest_framework.test import APIClient

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
