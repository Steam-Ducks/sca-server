import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_list_users_returns_200():
    client = APIClient()

    response = client.get("/api/users/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_create_user_returns_201():
    client = APIClient()

    payload = {
        "name": "João",
        "email": "joao@email.com",
    }

    response = client.post("/api/users/", payload, format="json")

    assert response.status_code == 201
    assert response.data["email"] == "joao@email.com"
