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
    CTI-01 ao CTI-06
    Conjunto: User model + UserSerializer + UserListCreateView

    Carga: 0–2 objetos User por teste (banco limpo a cada teste).
    """

    @pytest.fixture(autouse=True)
    def setup(self, db):
        # Remove seed data so each test starts with an empty users table.
        # force_authenticate uses an unsaved user to avoid affecting counts.
        User.objects.all().delete()
        auth_user = User(username="_auth", name="Auth User", is_active=True)
        self.client = APIClient()
        self.client.force_authenticate(user=auth_user)

    def test_lista_vazia_quando_nao_ha_usuarios(self):
        # CTI-01 (mínimo): banco vazio → GET retorna 200 com lista vazia
        # Valida: view responde sem erro quando não há dados
        response = self.client.get("/api/users/")
        assert response.status_code == 200
        assert response.data == []

    def test_cria_usuario_via_post_e_persiste_no_banco(self):
        # CTI-02 (mínimo): POST persiste no banco → dado existe no ORM
        # Valida: view → ORM → banco (cadeia completa de escrita)
        payload = {"username": "testusr", "name": "Usuário Teste", "email": "teste@sca.com"}

        response = self.client.post("/api/users/", data=payload, format="json")

        assert response.status_code == 201
        assert User.objects.count() == 1
        usuario = User.objects.get(email="teste@sca.com")
        assert usuario.name == "Usuário Teste"

    def test_get_retorna_usuario_recem_criado(self):
        # CTI-03 (mínimo): dado inserido → aparece na resposta GET
        # Valida: ORM → serializer → response (cadeia completa de leitura)
        User.objects.create_user(username="alpha", name="Usuário Alpha", email="alpha@sca.com")
        User.objects.create_user(username="beta", name="Usuário Beta", email="beta@sca.com")

        response = self.client.get("/api/users/")

        assert response.status_code == 200
        assert len(response.data) == 2
        emails = [u["email"] for u in response.data]
        assert "alpha@sca.com" in emails
        assert "beta@sca.com" in emails

    def test_resposta_contem_campos_corretos(self):
        # CTI-04 (adicional): estrutura dos campos da resposta
        # Valida: serializer inclui todos os campos esperados pelo frontend
        User.objects.create_user(username="campos", name="Campo Teste", email="campos@sca.com")

        response = self.client.get("/api/users/")

        usuario = response.data[0]
        assert "id" in usuario
        assert "name" in usuario
        assert "email" in usuario

    def test_email_duplicado_retorna_400(self):
        # CTI-05 (adicional): regra de negócio — e-mail único
        # Valida: validação do serializer bloqueia duplicata antes de persistir
        User.objects.create_user(username="primeiro", name="Primeiro", email="mesmo@sca.com")

        payload = {"username": "segundo", "name": "Segundo", "email": "mesmo@sca.com"}
        response = self.client.post("/api/users/", data=payload, format="json")

        assert response.status_code == 400
        assert User.objects.count() == 1

    def test_post_sem_email_retorna_400(self):
        # CTI-06 (adicional): campo obrigatório ausente → 400
        # Valida: validação de campos obrigatórios na cadeia view → serializer
        response = self.client.post("/api/users/", data={"username": "semEmail", "name": "Sem Email"}, format="json")
        assert response.status_code == 400
        assert User.objects.count() == 0
