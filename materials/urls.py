from django.urls import path

from materials.views import (
    MaterialsIndicatorsView,
    MaterialsTablePeriodoView,
    MaterialsTableView,
)

urlpatterns = [
    path("compras/", MaterialsTableView.as_view(), name="materials-table"),
    path("materials/", MaterialsTableView.as_view()),
    path(
        "compras/periodo/<str:periodo>/",
        MaterialsTablePeriodoView.as_view(),
        name="materials-table-periodo",
    ),
    path(
        "materials/indicators/",
        MaterialsIndicatorsView.as_view(),
        name="materials-indicators",
    ),
]
