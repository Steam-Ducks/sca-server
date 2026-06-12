from django.urls import path

from monitoring.views import ExecucaoCargaView

urlpatterns = [
    path("execucoes/", ExecucaoCargaView.as_view(), name="monitoring-execucoes"),
]
