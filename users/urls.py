from django.urls import path

from users.views import UserListCreateView

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
]
