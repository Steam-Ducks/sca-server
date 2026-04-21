from django.urls import path

from technical_hours.views import TechnicalHoursTableView

urlpatterns = [
    path(
        "horas-tecnicas/",
        TechnicalHoursTableView.as_view(),
        name="technical-hours-table",
    ),
]
