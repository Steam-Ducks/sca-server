import pytest

from users.serializers import UserSerializer


@pytest.mark.django_db
def test_user_serializer_is_valid_with_correct_data():
    data = {
        "name": "Ana",
        "email": "ana@email.com",
    }

    serializer = UserSerializer(data=data)

    assert serializer.is_valid()
    assert serializer.validated_data["email"] == "ana@email.com"
