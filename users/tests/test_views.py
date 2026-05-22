import pytest
from rest_framework.test import APIClient

from users.models import Perfil, User, UsuarioPerfil


@pytest.fixture
def user_with_profile(db):
    perfil, _ = Perfil.objects.get_or_create(
        nome="Super Admin",
        defaults={"descricao": "Acesso total", "permissoes": "super_admin"},
    )
    user, created = User.objects.get_or_create(
        username="superadmin",
        defaults={"name": "Super Admin", "email": "superadmin@test.com"},
    )
    if created:
        user.set_password("superadmin123")
        user.save()
    UsuarioPerfil.objects.get_or_create(usuario=user, defaults={"perfil": perfil})
    return user


@pytest.fixture
def auth_client(user_with_profile):
    client = APIClient()
    client.force_authenticate(user=user_with_profile)
    return client


# --- Login endpoint ---


@pytest.mark.django_db
def test_login_returns_200_with_valid_credentials(user_with_profile):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"username": "superadmin", "password": "superadmin123"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_response_contains_user_info(user_with_profile):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"username": "superadmin", "password": "superadmin123"},
        format="json",
    )
    assert response.data["user"]["username"] == "superadmin"
    assert response.data["user"]["name"] == "Super Admin"
    assert response.data["user"]["perfil"] == "Super Admin"


@pytest.mark.django_db
def test_login_returns_401_with_wrong_password(user_with_profile):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"username": "superadmin", "password": "errada"},
        format="json",
    )
    assert response.status_code == 401
    assert "error" in response.data


@pytest.mark.django_db
def test_login_returns_401_with_nonexistent_user():
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"username": "fantasma", "password": "qualquer"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_returns_400_with_missing_fields():
    client = APIClient()
    response = client.post("/api/auth/login/", {"username": "admin"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_returns_400_with_empty_body():
    client = APIClient()
    response = client.post("/api/auth/login/", {}, format="json")
    assert response.status_code == 400


# --- Users list endpoint ---


@pytest.mark.django_db
def test_list_users_returns_401_without_authentication():
    client = APIClient()
    response = client.get("/api/users/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_list_users_returns_200_when_authenticated(auth_client):
    response = auth_client.get("/api/users/")
    assert response.status_code == 200
