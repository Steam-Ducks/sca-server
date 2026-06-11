from django.urls import resolve, reverse

from users.views import LoginView, UserListCreateView


def test_user_list_create_url_resolves():
    url = reverse("user-list-create")
    resolver = resolve(url)
    assert resolver.func.view_class == UserListCreateView


def test_auth_login_url_resolves():
    url = reverse("auth-login")
    resolver = resolve(url)
    assert resolver.func.view_class == LoginView
