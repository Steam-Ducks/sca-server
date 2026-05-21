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
from rest_framework.test import APIClient


@pytest.mark.integration
class TestHealthCheckIntegration:
    """
    CTI-01 ao CTI-03
    Conjunto: health_check view + URL routing + DRF Response

    Carga: sem dados — endpoint é stateless (não lê banco).
    """

    def test_health_retorna_200(self):
        # CTI-01 (mínimo): GET /api/health/ → 200
        # Valida: URL registrada, view responde sem erro
        response = APIClient().get("/api/health/")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self):
        # CTI-02 (mínimo): corpo da resposta contém {"status": "ok"}
        # Valida: serialização da view até o cliente
        response = APIClient().get("/api/health/")
        assert response.data == {"status": "ok"}

    def test_health_so_aceita_get(self):
        # CTI-03 (adicional): POST → 405 Method Not Allowed
        response = APIClient().post("/api/health/")
        assert response.status_code == 405


@pytest.mark.integration
class TestReceiveLogIntegration:
    """
    CT-INT-CORE-02
    Conjunto: receive_log view + URL routing + JSON parsing
    """

    def test_receive_log_aceita_post_com_payload(self):
        payload = {"level": "info", "message": "teste de integração", "context": {}}
        response = APIClient().post(
            "/api/log/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_receive_log_aceita_payload_vazio(self):
        response = APIClient().post(
            "/api/log/",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_receive_log_nao_aceita_get(self):
        response = APIClient().get("/api/log/")
        assert response.status_code == 405


@pytest.mark.integration
class TestReceiveMetricIntegration:
    """
    CT-INT-CORE-03
    Conjunto: receive_metric view + URL routing + JSON parsing
    """

    def test_receive_metric_aceita_post(self):
        payload = {"name": "page_load", "value": 320, "unit": "ms"}
        response = APIClient().post(
            "/api/metric/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
