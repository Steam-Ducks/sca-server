"""
Conjunto de integração: Users

Funções do conjunto:
    User (models.py — AbstractUser)   — persistência no banco Django auth
    Perfil + UsuarioPerfil            — sistema de perfis de acesso
    UserSerializer (serializers)      — serialização de campos
    LoginView (views.py)              — POST /api/auth/login/
    UserListCreateView (views.py)     — GET + POST /api/users/ (super_admin)

MUDANÇA: User agora estende AbstractUser. Login usa JWT.
Endpoint /api/users/ requer perfil super_admin.

CTI-01 ao CTI-07
"""

import pytest
from rest_framework.test import APIClient

from users.models import Perfil, User, UsuarioPerfil


@pytest.mark.integration
@pytest.mark.django_db
class TestLoginIntegration:
    """
    CTI-01 ao CTI-04
    Conjunto: LoginView + User (AbstractUser) + JWT
    """

    def test_login_com_credenciais_validas_retorna_200(self, db):
        User.objects.create_user(username="joao", password="senha123", name="João")
        response = APIClient().post(
            "/api/auth/login/",
            data={"username": "joao", "password": "senha123"},
            format="json",
        )
        assert response.status_code == 200

    def test_login_retorna_access_e_refresh_tokens(self, db):
        User.objects.create_user(username="maria", password="senha456", name="Maria")
        response = APIClient().post(
            "/api/auth/login/",
            data={"username": "maria", "password": "senha456"},
            format="json",
        )
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_login_com_credenciais_invalidas_retorna_401(self, db):
        response = APIClient().post(
            "/api/auth/login/",
            data={"username": "naoexiste", "password": "errada"},
            format="json",
        )
        assert response.status_code == 401

    def test_login_retorna_perfil_do_usuario(self, db):
        user = User.objects.create_user(
            username="carlos", password="senha789", name="Carlos"
        )
        perfil = Perfil.objects.create(nome="Financeiro Test", permissoes="financeiro")
        UsuarioPerfil.objects.create(usuario=user, perfil=perfil)
        response = APIClient().post(
            "/api/auth/login/",
            data={"username": "carlos", "password": "senha789"},
            format="json",
        )
        assert response.data["user"]["perfil"] == "financeiro"


@pytest.mark.integration
@pytest.mark.django_db
class TestUserListIntegration:
    """
    CTI-05 ao CTI-07
    Conjunto: UserListCreateView + UserSerializer + CanAccessUsers
    api_client do conftest vem autenticado como super_admin.
    """

    def test_lista_retorna_200_para_super_admin(self, api_client):
        response = api_client.get("/api/users/")
        assert response.status_code == 200

    def test_lista_retorna_403_sem_autenticacao(self):
        response = APIClient().get("/api/users/")
        assert response.status_code == 403

    def test_usuario_criado_aparece_na_lista(self, api_client, db):
        User.objects.create_user(
            username="novo_user", password="pass123", name="Novo Usuário"
        )
        response = api_client.get("/api/users/")
        usernames = [u["username"] for u in response.data]
        assert "novo_user" in usernames
