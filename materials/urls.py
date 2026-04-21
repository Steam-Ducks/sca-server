from django.urls import path

from materials.views import MaterialsIndicatorsView, MaterialsTableView

urlpatterns = [
    path("compras/", MaterialsTableView.as_view(), name="materials-table"),
    path("materials/", MaterialsTableView.as_view()),
    path(
        "materials/indicators/",
        MaterialsIndicatorsView.as_view(),
        name="materials-indicators",
    ),
]
