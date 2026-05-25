"""
CT01 — Validar autenticação do usuário
CT02 — Validar bloqueio de acesso direto para usuários sem permissão

Endpoint de referência para CT02: GET /api/users/
  - Restrito ao perfil super_admin (CanAccessUsers).
  - Simples de testar: não depende de dados de negócio.
"""

from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from users.models import Perfil, User, UsuarioPerfil
from users.permissions import _get_permissao


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_user(username, password, perfil_nome, permissao):
    perfil, _ = Perfil.objects.get_or_create(
        nome=perfil_nome,
        defaults={"descricao": "", "permissoes": permissao},
    )
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"name": username, "email": f"{username}@test.com"},
    )
    if created:
        user.set_password(password)
        user.save()
    UsuarioPerfil.objects.get_or_create(usuario=user, defaults={"perfil": perfil})
    return user


@pytest.fixture
def superadmin(db):
    return _make_user("sa_ct", "senha123", "Super Admin", "super_admin")


@pytest.fixture
def financeiro(db):
    return _make_user("fin_ct", "senha123", "Financeiro", "financeiro")


@pytest.fixture
def user_sem_perfil(db):
    user, created = User.objects.get_or_create(
        username="semperfil",
        defaults={"name": "Sem Perfil", "email": "semperfil@test.com"},
    )
    if created:
        user.set_password("senha123")
        user.save()
    return user


# ---------------------------------------------------------------------------
# _get_permissao unit tests
# ---------------------------------------------------------------------------


def test_get_permissao_retorna_permissao_do_perfil(monkeypatch):
    user = User(username="_u")
    monkeypatch.setattr(
        User,
        "usuario_perfil",
        property(
            lambda self: SimpleNamespace(
                perfil=SimpleNamespace(permissoes="financeiro")
            )
        ),
    )
    assert _get_permissao(user) == "financeiro"


def test_get_permissao_retorna_none_quando_sem_perfil():
    user = User(username="_u")
    assert _get_permissao(user) is None


def test_get_permissao_retorna_none_quando_perfil_invalido(monkeypatch):
    user = User(username="_u")
    monkeypatch.setattr(
        User,
        "usuario_perfil",
        property(lambda self: SimpleNamespace(perfil=None)),
    )
    assert _get_permissao(user) is None


# ---------------------------------------------------------------------------
# CT01 — Autenticação
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCT01Autenticacao:
    """CT01: Validar autenticação do usuário."""

    def test_login_retorna_tokens_com_credenciais_validas(self, superadmin):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "sa_ct", "password": "senha123"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_identifica_perfil_do_usuario(self, superadmin):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "sa_ct", "password": "senha123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["user"]["perfil"] == "super_admin"

    def test_login_retorna_dados_do_usuario(self, superadmin):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "sa_ct", "password": "senha123"},
            format="json",
        )
        assert response.data["user"]["username"] == "sa_ct"

    def test_login_retorna_401_com_senha_errada(self, superadmin):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "sa_ct", "password": "errada"},
            format="json",
        )
        assert response.status_code == 401
        assert "error" in response.data

    def test_login_retorna_401_usuario_inexistente(self):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "naoexiste", "password": "qualquer"},
            format="json",
        )
        assert response.status_code == 401

    def test_login_perfil_financeiro_identificado(self, financeiro):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": "fin_ct", "password": "senha123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["user"]["perfil"] == "financeiro"


# ---------------------------------------------------------------------------
# CT02 — Bloqueio de acesso direto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCT02BloqueioAcesso:
    """CT02: Validar bloqueio de acesso direto para usuários sem permissão."""

    def test_acesso_sem_autenticacao_retorna_401(self):
        client = APIClient()
        response = client.get("/api/users/")
        assert response.status_code == 401

    def test_acesso_com_perfil_errado_retorna_403(self, financeiro):
        # Financeiro não tem permissão para /api/users/ (super_admin apenas)
        client = APIClient()
        client.force_authenticate(user=financeiro)
        response = client.get("/api/users/")
        assert response.status_code == 403

    def test_acesso_com_perfil_correto_retorna_200(self, superadmin):
        client = APIClient()
        client.force_authenticate(user=superadmin)
        response = client.get("/api/users/")
        assert response.status_code == 200

    def test_acesso_sem_perfil_retorna_403(self, user_sem_perfil):
        client = APIClient()
        client.force_authenticate(user=user_sem_perfil)
        response = client.get("/api/users/")
        assert response.status_code == 403

    def test_mensagem_erro_403_perfil_errado(self, financeiro):
        client = APIClient()
        client.force_authenticate(user=financeiro)
        response = client.get("/api/users/")
        assert "detail" in response.data

    def test_mensagem_erro_403_sem_perfil(self, user_sem_perfil):
        client = APIClient()
        client.force_authenticate(user=user_sem_perfil)
        response = client.get("/api/users/")
        assert "detail" in response.data
        assert "não encontrado" in response.data["detail"].lower()

    def test_token_invalido_retorna_401(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer tokeninvalido")
        response = client.get("/api/users/")
        assert response.status_code == 401
