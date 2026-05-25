"""
Conjunto de integração: Costs

Funções do conjunto:
    GoldCosts (sca_data.models)    — tabela gold."costs" (PostgreSQL)
    GoldCostsTableView (views.py)  — GET /api/costs/
    GoldCostsSerializer            — serializa campos + converte data para ISO
    URL: /api/costs/

Por que este conjunto existe:
    Os testes unitários validam view e serializer com mocks.
    Este conjunto valida que a leitura real do banco gold,
    a serialização de DateTimeField e os filtros por campo e data
    funcionam ponta a ponta: banco → ORM → view → serializer → response.
"""

import os
import pytest
from datetime import datetime, timezone

from sca_data.models import GoldCosts

# Skip quando PostgreSQL não está disponível (CI SQLite).
# Para rodar localmente: export DB_HOST=postgres
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with gold schema — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


@pytest.fixture
def client(api_client):
    return api_client


@pytest.fixture
def custo_gold(db):
    return GoldCosts.objects.create(
        nome_programa="MANSUP",
        nome_projeto="Conversor DC-DC",
        gerente_programa="Gerente A",
        responsavel_projeto="Resp A",
        custo=150_000.0,
        data=datetime(2024, 3, 15, tzinfo=timezone.utc),
        gold_updated_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def dois_custos(db):
    """Fixture com dois projetos de programas distintos para testar filtros."""
    GoldCosts.objects.create(
        nome_programa="MANSUP",
        nome_projeto="Proj MANSUP",
        custo=100_000.0,
        data=datetime(2024, 1, 10, tzinfo=timezone.utc),
        gold_updated_at=datetime.now(tz=timezone.utc),
    )
    GoldCosts.objects.create(
        nome_programa="INFRA",
        nome_projeto="Proj INFRA",
        custo=200_000.0,
        data=datetime(2024, 6, 20, tzinfo=timezone.utc),
        gold_updated_at=datetime.now(tz=timezone.utc),
    )


class TestGoldCostsTableIntegration:
    """
    CTI-01 ao CTI-07
    Conjunto: GoldCosts (gold schema) + GoldCostsTableView + GoldCostsSerializer

    Carga: 0–2 objetos GoldCosts por teste (banco limpo a cada teste).
    """

    def test_lista_retorna_200(self, client):
        # CTI-01 (mínimo): banco vazio → GET /api/costs/ retorna 200
        # Valida: rota registrada, view instanciada, resposta sem erro
        response = client.get("/api/costs/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self, client):
        # CTI-02 (mínimo): banco vazio → resposta é lista vazia
        # Valida: view não lança exceção quando gold.costs está sem registros
        response = client.get("/api/costs/")
        assert response.status_code == 200
        assert response.data == []

    def test_retorna_custo_real_do_banco(self, custo_gold, client):
        # CTI-03 (mínimo): dado inserido → aparece na resposta com campos corretos
        # Valida: GoldCosts → GoldCostsSerializer → response (cadeia de leitura)
        response = client.get("/api/costs/")

        assert response.status_code == 200
        assert len(response.data) == 1
        item = response.data[0]
        assert item["nome_projeto"] == "Conversor DC-DC"
        assert item["nome_programa"] == "MANSUP"
        assert float(item["custo"]) == 150_000.0

    def test_data_serializada_em_formato_iso(self, custo_gold, client):
        # CTI-04 (adicional): campo data (DateTimeField) → serializado como YYYY-MM-DD
        # Valida: GoldCostsSerializer.get_data converte DateTimeField para date ISO
        response = client.get("/api/costs/")
        item = response.data[0]
        assert item["data"] == "2024-03-15"

    def test_filtro_por_nome_programa(self, dois_custos, client):
        # CTI-05 (mínimo): ?nome_programa= → response contém só dados do programa
        # Valida: filtro ORM field lookup aplicado pela view antes da serialização
        response = client.get("/api/costs/?nome_programa=MANSUP")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["nome_programa"] == "MANSUP"

    def test_filtro_por_nome_projeto(self, dois_custos, client):
        # CTI-06 (mínimo): ?nome_projeto= → response contém só o projeto filtrado
        response = client.get("/api/costs/?nome_projeto=Proj INFRA")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["nome_projeto"] == "Proj INFRA"

    def test_filtro_por_intervalo_de_datas(self, dois_custos, client):
        # CTI-07 (adicional): ?data_gte + ?data_lte → só registros no intervalo
        # Valida: parse_date + make_aware + filter(data__gte/lte) na view
        response = client.get("/api/costs/?data_gte=2024-01-01&data_lte=2024-03-31")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["nome_programa"] == "MANSUP"
