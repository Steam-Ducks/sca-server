"""
Conjunto de integração: Core / Health Check

Funções do conjunto:
    health_check (views.py) — GET /api/health/ → {"status": "ok"}
    receive_log (views.py)  — POST /api/log/
    receive_metric          — POST /api/metric/

Registrado em config/urls.py: path("api/", include("core.urls"))
"""

import json
import pytest


@pytest.mark.integration
class TestHealthCheckIntegration:
    """
    CTI-01 ao CTI-03
    Conjunto: health_check view + URL routing + DRF Response

    Carga: sem dados — endpoint é stateless (não lê banco).
    """

    def test_health_retorna_200(self, api_client):
        # CTI-01 (mínimo): GET /api/health/ → 200
        # Valida: URL registrada, view responde sem erro
        response = api_client.get("/api/health/")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self, api_client):
        # CTI-02 (mínimo): corpo da resposta contém {"status": "ok"}
        # Valida: serialização da view até o cliente
        response = api_client.get("/api/health/")
        assert response.data == {"status": "ok"}

    def test_health_so_aceita_get(self, api_client):
        # CTI-03 (adicional): POST → 405 Method Not Allowed
        response = api_client.post("/api/health/")
        assert response.status_code == 405


@pytest.mark.integration
@pytest.mark.xfail(
    reason="/api/log/ not registered in core/urls.py — endpoint not yet implemented",
)
class TestReceiveLogIntegration:
    """
    CT-INT-CORE-02
    Conjunto: receive_log view + URL routing + JSON parsing
    """

    def test_receive_log_aceita_post_com_payload(self, api_client):
        payload = {"level": "info", "message": "teste de integração", "context": {}}
        response = api_client.post(
            "/api/log/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_receive_log_aceita_payload_vazio(self, api_client):
        response = api_client.post(
            "/api/log/",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_receive_log_nao_aceita_get(self, api_client):
        response = api_client.get("/api/log/")
        assert response.status_code == 405


@pytest.mark.integration
@pytest.mark.xfail(
    reason="/api/metric/ not registered in core/urls.py — endpoint not yet implemented",
)
class TestReceiveMetricIntegration:
    """
    CT-INT-CORE-03
    Conjunto: receive_metric view + URL routing + JSON parsing
    """

    def test_receive_metric_aceita_post(self, api_client):
        payload = {"name": "page_load", "value": 320, "unit": "ms"}
        response = api_client.post(
            "/api/metric/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
