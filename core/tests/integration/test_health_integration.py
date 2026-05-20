"""
Conjunto de integração: Core / Health Check

Funções do conjunto:
    health_check (views.py)  →  retorna {"status": "ok"}
    receive_log  (views.py)  →  aceita POST com payload de log do front
    receive_metric (views.py) → aceita POST com payload de métrica do front

Por que este conjunto existe como integração e não apenas unitário:
    Valida que o roteamento de URLs (core.urls → config.urls → Django)
    está conectado corretamente ao handler, sem mocks intermediários.
"""

import json
import pytest
from rest_framework.test import APIClient


@pytest.mark.integration
class TestHealthCheckIntegration:
    """
    CT-INT-CORE-01
    Conjunto: health_check view + URL routing + DRF Response

    Valida que o endpoint /api/health/ está acessível e responde
    corretamente sem qualquer dependência de banco de dados.
    """

    def test_health_retorna_200(self):
        client = APIClient()
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_health_retorna_status_ok(self):
        client = APIClient()
        response = client.get("/api/health/")
        assert response.data == {"status": "ok"}

    def test_health_so_aceita_get(self):
        client = APIClient()
        response = client.post("/api/health/")
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.integration
class TestReceiveLogIntegration:
    """
    CT-INT-CORE-02
    Conjunto: receive_log view + URL routing + JSON parsing

    Valida que o endpoint de recebimento de logs do frontend
    aceita POST com JSON e responde corretamente.
    """

    def test_receive_log_aceita_post_com_payload(self):
        client = APIClient()
        payload = {"level": "info", "message": "teste de integração", "context": {}}
        response = client.post(
            "/api/log/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_receive_log_aceita_payload_vazio(self):
        client = APIClient()
        response = client.post(
            "/api/log/",
            data="{}",
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_receive_log_nao_aceita_get(self):
        client = APIClient()
        response = client.get("/api/log/")
        assert response.status_code == 405


@pytest.mark.integration
class TestReceiveMetricIntegration:
    """
    CT-INT-CORE-03
    Conjunto: receive_metric view + URL routing + JSON parsing
    """

    def test_receive_metric_aceita_post(self):
        client = APIClient()
        payload = {"name": "page_load", "value": 320, "unit": "ms"}
        response = client.post(
            "/api/metric/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
