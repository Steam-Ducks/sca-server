from django.urls import path

from users.views import LoginView, UserListCreateView

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
]
