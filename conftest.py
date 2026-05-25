import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_user(db):
    from users.models import Perfil, UsuarioPerfil

    user = User.objects.create_user(username="testuser", password="testpass123")
    perfil, _ = Perfil.objects.get_or_create(
        nome="Super Admin",
        defaults={"descricao": "Acesso total", "permissoes": "super_admin"},
    )
    UsuarioPerfil.objects.get_or_create(usuario=user, defaults={"perfil": perfil})
    return user


@pytest.fixture
def api_client(api_user):
    client = APIClient()
    client.force_authenticate(user=api_user)
    return client
