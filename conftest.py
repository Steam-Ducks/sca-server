"""
conftest.py — fixtures compartilhadas (sca-server).

Carregado para TODOS os testes (unitários e integração).
Por isso: zero imports de sca_data aqui fora de funções.

Testes unitários rodam com SQLite + sca_data fora do INSTALLED_APPS.
Qualquer import de sca_data.models no topo deste arquivo quebra os unitários.

Fixtures de dados silver/gold ficam em cada pasta tests/integration/
dos apps — não aqui.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Cliente HTTP DRF — disponível para unitários e integração."""
    return APIClient()