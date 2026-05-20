"""
Conjunto de integração: Users

Funções do conjunto:
    User (models.py)              — persistência no banco
    UserSerializer (serializers)  — serialização de campos
    UserListCreateView (views.py) — GET (lista) + POST (criação)
    URL: /api/users/

Por que este conjunto existe:
    O teste unitário valida o serializer isolado.
    Este conjunto valida que a criação via POST persiste no banco
    e que o GET retorna exatamente o que foi persistido,
    exercitando a cadeia completa: view → ORM → banco → serializer → response.
"""

import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.mark.integration
@pytest.mark.django_db
class TestUserListCreateIntegration:
    """
    CT-INT-USR-01
    Conjunto: User model + UserSerializer + UserListCreateView
    """

    def test_lista_vazia_quando_nao_ha_usuarios(self):
        client = APIClient()
        response = client.get("/api/users/")
        assert response.status_code == 200
        assert response.data == []

    def test_cria_usuario_via_post_e_persiste_no_banco(self):
        client = APIClient()
        payload = {"name": "Usuário Teste", "email": "teste@sca.com"}

        response = client.post("/api/users/", data=payload, format="json")

        assert response.status_code == 201
        assert User.objects.count() == 1
        usuario = User.objects.get(email="teste@sca.com")
        assert usuario.name == "Usuário Teste"

    def test_get_retorna_usuario_recem_criado(self):
        User.objects.create(name="Usuário Alpha", email="alpha@sca.com")
        User.objects.create(name="Usuário Beta", email="beta@sca.com")

        client = APIClient()
        response = client.get("/api/users/")

        assert response.status_code == 200
        assert len(response.data) == 2
        emails = [u["email"] for u in response.data]
        assert "alpha@sca.com" in emails
        assert "beta@sca.com" in emails

    def test_resposta_contem_campos_corretos(self):
        User.objects.create(name="Campo Teste", email="campos@sca.com")

        client = APIClient()
        response = client.get("/api/users/")

        usuario = response.data[0]
        assert "id" in usuario
        assert "name" in usuario
        assert "email" in usuario

    def test_email_duplicado_retorna_400(self):
        User.objects.create(name="Primeiro", email="mesmo@sca.com")

        client = APIClient()
        payload = {"name": "Segundo", "email": "mesmo@sca.com"}
        response = client.post("/api/users/", data=payload, format="json")

        assert response.status_code == 400
        assert User.objects.count() == 1

    def test_post_sem_email_retorna_400(self):
        client = APIClient()
        response = client.post("/api/users/", data={"name": "Sem Email"}, format="json")
        assert response.status_code == 400
        assert User.objects.count() == 0
