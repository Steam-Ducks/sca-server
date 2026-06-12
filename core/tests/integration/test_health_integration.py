"""
Conjunto de integração: Core

Funções do conjunto:
    health_check (views.py)  — GET /api/health/ → {"status": "ok"} (AllowAny)
    status_view (views.py)   — GET /api/status/ → diagnóstico completo (AllowAny)

Registrado em config/urls.py: path("api/", include("core.urls"))

/api/log/ e /api/metric/ não existem em core/urls.py — xfail documentado.

CTI-01 ao CTI-06
"""

import pytest


@pytest.mark.integration
@pytest.mark.django_db
class TestHealthCheckIntegration:
    """
    CTI-01 ao CTI-03
    Conjunto: health_check view + URL routing + DRF Response
    Endpoint AllowAny — não requer autenticação.
    """

    def test_health_retorna_200(self, api_client):
        # CTI-01
        response = api_client.get("/api/health/")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self, api_client):
        # CTI-02
        response = api_client.get("/api/health/")
        assert response.data == {"status": "ok"}

    def test_health_so_aceita_get(self, api_client):
        # CTI-03
        response = api_client.post("/api/health/")
        assert response.status_code == 405


@pytest.mark.integration
@pytest.mark.django_db
class TestStatusViewIntegration:
    """
    CTI-04 ao CTI-06
    Conjunto: status_view + _check_services + _get_recent_processes + _get_db_stats
    Endpoint AllowAny — retorna diagnóstico completo do sistema.
    """

    def test_status_retorna_200(self, api_client):
        # CTI-04
        response = api_client.get("/api/status/")
        assert response.status_code == 200

    def test_status_contem_campos_obrigatorios(self, api_client):
        # CTI-05
        response = api_client.get("/api/status/")
        for campo in ["status", "timestamp", "services", "data_integrity"]:
            assert campo in response.data, f"Campo ausente: {campo}"

    def test_status_verifica_conexao_banco(self, api_client):
        # CTI-06 — com PostgreSQL real, database deve estar "ok"
        response = api_client.get("/api/status/")
        assert response.data["services"]["database"]["status"] == "ok"


@pytest.mark.integration
@pytest.mark.xfail(
    reason="/api/log/ não registrado em core/urls.py — endpoint não implementado",
)
class TestReceiveLogIntegration:
    """CTI-07 — xfail: endpoint não existe ainda."""

    def test_receive_log_aceita_post(self, api_client):
        response = api_client.post(
            "/api/log/",
            data={"level": "info", "message": "test"},
            format="json",
        )
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.xfail(
    reason="/api/metric/ não registrado em core/urls.py — endpoint não implementado",
)
class TestReceiveMetricIntegration:
    """CTI-08 — xfail: endpoint não existe ainda."""

    def test_receive_metric_aceita_post(self, api_client):
        response = api_client.post(
            "/api/metric/",
            data={"name": "page_load", "value": 320},
            format="json",
        )
        assert response.status_code == 200
