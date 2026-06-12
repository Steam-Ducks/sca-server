import pytest

from users.models import User
from users.serializers import LoginSerializer, UserSerializer


@pytest.mark.django_db
def test_user_serializer_returns_expected_fields():
    user = User.objects.create_user(
        username="ana", name="Ana", email="ana@email.com", password="senha123"
    )
    data = UserSerializer(user).data
    assert data["username"] == "ana"
    assert data["email"] == "ana@email.com"
    assert "password" not in data


@pytest.mark.django_db
def test_validate_email_rejeita_email_duplicado():
    User.objects.create_user(username="primeiro", email="dup@email.com")
    serializer = UserSerializer(
        data={"username": "segundo", "name": "Segundo", "email": "dup@email.com"}
    )
    assert not serializer.is_valid()
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_validate_email_aceita_proprio_email_no_update():
    user = User.objects.create_user(
        username="joana", name="Joana", email="joana@email.com"
    )
    serializer = UserSerializer(
        instance=user,
        data={"username": "joana", "name": "Joana", "email": "joana@email.com"},
    )
    assert serializer.is_valid()


def test_login_serializer_valid_with_username_and_password():
    serializer = LoginSerializer(data={"username": "admin", "password": "admin123"})
    assert serializer.is_valid()


def test_login_serializer_invalid_without_password():
    serializer = LoginSerializer(data={"username": "admin"})
    assert not serializer.is_valid()
    assert "password" in serializer.errors


def test_login_serializer_invalid_without_username():
    serializer = LoginSerializer(data={"password": "admin123"})
    assert not serializer.is_valid()
    assert "username" in serializer.errors


def test_login_serializer_invalid_with_empty_fields():
    serializer = LoginSerializer(data={"username": "", "password": ""})
    assert not serializer.is_valid()
