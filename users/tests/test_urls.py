from django.urls import resolve, reverse

from users.views import UserListCreateView


def test_user_list_create_url_resolves_correctly():
    url = reverse("user-list-create")
    resolver = resolve(url)

    assert resolver.func.view_class == UserListCreateView
