import pytest

from users.models import User


@pytest.mark.django_db
def test_user_string_representation():
    user = User.objects.create(name="Maria", email="maria@email.com")

    assert str(user) == "Maria"
