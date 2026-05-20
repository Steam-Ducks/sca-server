"""
Conjunto de integração: Materials (Gestão de Materiais)

Funções do conjunto:
    _parse_periodo (views.py)           — converte YYYY-MM em intervalo de datas
    _get_date_range (selectors.py)      — resolve intervalo a partir dos params
    get_materials_queryset (selectors)  — filtra SilverPedidoCompra com ORM
    MaterialsTableView (views.py)       — GET /api/compras/
    MaterialsTablePeriodoView           — GET /api/compras/periodo/<YYYY-MM>/
    MaterialsIndicatorsView             — GET /api/compras/indicadores/
    MaterialsTableSerializer            — serializa pedidos de compra
    MaterialsIndicatorsSerializer       — serializa indicadores agregados
"""

import pytest
from datetime import date, datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverMaterial,
    SilverFornecedor,
    SilverPedidoCompra,
    SilverSolicitacaoCompra,
    SilverComprasProjeto,
)


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=700, codigo_programa="INFRA", nome_programa="Infraestrutura",
        status="Em andamento", silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=700, codigo_projeto="PROJ-700", nome_projeto="Projeto Infra Base",
        programa=programa, custo_hora=150.0, status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def fornecedor(db):
    return SilverFornecedor.objects.create(
        id=700, codigo_fornecedor="FORN-700", razao_social="Fornecedor Teste Ltda",
        cidade="São Paulo", estado="SP", categoria="Eletrônicos", status="Ativo",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_marco(db, projeto, fornecedor):
    """Pedido de compra em março/2024."""
    return SilverPedidoCompra.objects.create(
        id=700, numero_pedido="PC-700",
        data_pedido=date(2024, 3, 10),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_junho(db, projeto, fornecedor):
    """Pedido de compra em junho/2024 — fora do período de março."""
    return SilverPedidoCompra.objects.create(
        id=701, numero_pedido="PC-701",
        data_pedido=date(2024, 6, 20),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestMaterialsTableIntegration:
    """
    CT-INT-MAT-01
    Conjunto: get_materials_queryset + MaterialsTableView + MaterialsTableSerializer
    """

    def test_lista_retorna_200(self):
        response = APIClient().get("/api/compras/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self):
        response = APIClient().get("/api/compras/")
        assert response.data == []

    def test_lista_retorna_pedidos_reais(self, projeto, pedido_marco):
        sol = SilverSolicitacaoCompra.objects.create(
            id=700, projeto=projeto, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        SilverComprasProjeto.objects.create(
            id=700, solicitacao=sol, valor_alocado=15_000.0,
            pedido_compra=pedido_marco, silver_ingested_at=datetime.now(tz=timezone.utc)
        )

        response = APIClient().get("/api/compras/")
        assert len(response.data) >= 1

    def test_filtro_por_projeto_retorna_apenas_dados_do_projeto(
        self, programa, pedido_marco
    ):
        proj_a = SilverProjeto.objects.create(
            id=710, codigo_projeto="PA", nome_projeto="Projeto A",
            programa=programa, custo_hora=100.0, status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        proj_b = SilverProjeto.objects.create(
            id=711, codigo_projeto="PB", nome_projeto="Projeto B",
            programa=programa, custo_hora=100.0, status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        sol_a = SilverSolicitacaoCompra.objects.create(
            id=710, projeto=proj_a, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        sol_b = SilverSolicitacaoCompra.objects.create(
            id=711, projeto=proj_b, silver_ingested_at=datetime.now(tz=timezone.utc)
        )

        SilverComprasProjeto.objects.create(
            id=710, solicitacao=sol_a, valor_alocado=10_000.0,
            pedido_compra=pedido_marco, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        SilverComprasProjeto.objects.create(
            id=711, solicitacao=sol_b, valor_alocado=99_000.0,
            pedido_compra=pedido_marco, silver_ingested_at=datetime.now(tz=timezone.utc)
        )

        response = APIClient().get("/api/compras/?projeto=Projeto A")

        assert response.status_code == 200
        projetos_retornados = {item.get("nome_projeto") for item in response.data}
        assert "Projeto A" in projetos_retornados
        assert "Projeto B" not in projetos_retornados


@pytest.mark.integration
@pytest.mark.django_db
class TestMaterialsTablePeriodoIntegration:
    """
    CT-INT-MAT-02
    Conjunto: _parse_periodo + get_materials_queryset + MaterialsTablePeriodoView
    """

    def test_periodo_valido_retorna_200(self):
        response = APIClient().get("/api/compras/periodo/2024-03/")
        assert response.status_code == 200

    def test_periodo_invalido_retorna_400(self):
        response = APIClient().get("/api/compras/periodo/2024-13/")
        assert response.status_code == 400

    def test_periodo_retorna_apenas_compras_do_mes(
        self, projeto, pedido_marco, pedido_junho
    ):
        sol = SilverSolicitacaoCompra.objects.create(
            id=720, projeto=projeto, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        # Compra em março — deve aparecer
        SilverComprasProjeto.objects.create(
            id=720, solicitacao=sol, valor_alocado=5_000.0,
            pedido_compra=pedido_marco, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        # Compra em junho — NÃO deve aparecer
        SilverComprasProjeto.objects.create(
            id=721, solicitacao=sol, valor_alocado=99_000.0,
            pedido_compra=pedido_junho, silver_ingested_at=datetime.now(tz=timezone.utc)
        )

        response = APIClient().get("/api/compras/periodo/2024-03/")

        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            assert item.get("data_pedido", "").startswith("2024-03")
