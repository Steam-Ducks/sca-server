from django.urls import path

from technical_hours.views import (
    TechnicalHoursKpiView,
    TechnicalHoursTablePeriodoView,
    TechnicalHoursTableView,
)

urlpatterns = [
    path(
        "horas-tecnicas/",
        TechnicalHoursTableView.as_view(),
        name="technical-hours-table",
    ),
    path(
        "horas-tecnicas/kpis/",
        TechnicalHoursKpiView.as_view(),
        name="technical-hours-kpis",
    ),
    path(
        "horas-tecnicas/periodo/<str:periodo>/",
        TechnicalHoursTablePeriodoView.as_view(),
        name="technical-hours-table-periodo",
    ),
]
