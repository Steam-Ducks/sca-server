from django.urls import path

from materials.views import (
    CostByProjectView,
    FilterOptionsView,
    MaterialsIndicatorsView,
    MaterialsTablePeriodoView,
    MaterialsTableView,
    TopMaterialsView,
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
    path("top-materials/", TopMaterialsView.as_view(), name="top-materials"),
    path("cost-by-project/", CostByProjectView.as_view(), name="cost-by-project"),
    path(
        "materials/filter-options/",
        FilterOptionsView.as_view(),
        name="materials-filter-options",
    ),
]
