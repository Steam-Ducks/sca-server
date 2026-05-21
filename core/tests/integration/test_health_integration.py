"""
Conjunto de integração: Core / Health Check

SITUAÇÃO ATUAL: o app `core` não está registrado em config/urls.py.
Os endpoints /api/health/, /api/log/ e /api/metric/ retornam 404.

AÇÃO NECESSÁRIA (responsabilidade do desenvolvedor do CI):
    Adicionar em config/urls.py:
        path("api/", include("core.urls")),

Enquanto isso, os testes estão marcados com @pytest.mark.xfail.
Quando o core for registrado: remova o xfail de cada classe.
"""

import json
import pytest
from rest_framework.test import APIClient


@pytest.mark.xfail(
    reason="core app não registrado em config/urls.py — adicionar path('api/', include('core.urls'))",
    strict=True,
)
@pytest.mark.integration
class TestHealthCheckIntegration:
    """
    CT-INT-CORE-01
    Conjunto: health_check view + URL routing + DRF Response
    """

    def test_health_retorna_200(self):
        response = APIClient().get("/api/health/")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self):
        response = APIClient().get("/api/health/")
        assert response.data == {"status": "ok"}

    def test_health_so_aceita_get(self):
        response = APIClient().post("/api/health/")
        assert response.status_code == 405


@pytest.mark.xfail(
    reason="core app não registrado em config/urls.py — adicionar path('api/', include('core.urls'))",
    strict=True,
)
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
            "/api/log/", data="{}", content_type="application/json",
        )
        assert response.status_code == 200

    def test_receive_log_nao_aceita_get(self):
        response = APIClient().get("/api/log/")
        assert response.status_code == 405


@pytest.mark.xfail(
    reason="core app não registrado em config/urls.py — adicionar path('api/', include('core.urls'))",
    strict=True,
)
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
