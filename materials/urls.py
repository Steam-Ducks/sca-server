from django.urls import path

from materials.views import MaterialsTableView

urlpatterns = [
    path("compras/", MaterialsTableView.as_view(), name="materials-table"),
    path("materials/", MaterialsTableView.as_view()),
]
