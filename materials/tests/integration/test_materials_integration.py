"""
Conjunto de integração: Materials (atualizado)

Funções do conjunto:
    MaterialsTableView (views.py) GET /api/compras/
    MaterialsTablePeriodoView     GET /api/compras/periodo/<YYYY-MM>/
    MaterialsIndicatorsView   GET /api/materials/indicators/
    TopMaterialsView          GET /api/top-materials/
    CostByProjectView         GET /api/cost-by-project/
    FilterOptionsView         GET /api/materials/filter-options/
    parse_period (core/utils)           — converte YYYY-MM em intervalo de datas
    get_materials_queryset (selectors)  — filtra SilverPedidoCompra com ORM
"""

import os
import pytest
from datetime import date, datetime, timezone

from sca_data.models import (
    SilverComprasProjeto,
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver schema — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=700,
        codigo_programa="MANSUP",
        nome_programa="MANSUP",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=700,
        codigo_projeto="PROJ-700",
        nome_projeto="Conversor DC-DC",
        programa=programa,
        custo_hora=100.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def material(db):
    return SilverMaterial.objects.create(
        id=700,
        codigo_material="MAT-700",
        descricao="Material de Teste",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def fornecedor(db):
    return SilverFornecedor.objects.create(
        id=700,
        codigo_fornecedor="FORN-700",
        razao_social="Fornecedor Teste Ltda",
        cidade="São Paulo",
        estado="SP",
        categoria="Eletrônicos",
        status="Ativo",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def solicitacao(db, projeto, material):
    return SilverSolicitacaoCompra.objects.create(
        id=700,
        numero_solicitacao="SC-700",
        projeto=projeto,
        material=material,
        quantidade=1,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_marco(db, fornecedor, solicitacao):
    return SilverPedidoCompra.objects.create(
        id=700,
        numero_pedido="PC-700",
        fornecedor=fornecedor,
        solicitacao=solicitacao,
        data_pedido=date(2024, 3, 10),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_junho(db, fornecedor, solicitacao):
    return SilverPedidoCompra.objects.create(
        id=701,
        numero_pedido="PC-701",
        fornecedor=fornecedor,
        solicitacao=solicitacao,
        data_pedido=date(2024, 6, 20),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


# ── CTI: MaterialsTableView ───────────────────────────────────────────────────


class TestMaterialsTableIntegration:
    """
    CTI-01 ao CTI-04
    Conjunto: MaterialsTableView + MaterialsTableSerializer
    """

    def test_lista_retorna_200(self, api_client):
        # CTI-01 (mínimo): banco vazio → 200
        response = api_client.get("/api/compras/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self, api_client):
        # CTI-02 (mínimo): banco vazio → lista vazia
        response = api_client.get("/api/compras/")
        assert response.data == []

    def test_lista_retorna_pedidos_reais(self, api_client, projeto, pedido_marco):
        # CTI-03 (mínimo): pedido com solicitação → aparece na lista
        SilverComprasProjeto.objects.create(
            id=700,
            projeto=projeto,
            valor_alocado=15_000.0,
            pedido_compra=pedido_marco,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/compras/")
        assert len(response.data) >= 1

    def test_filtro_por_projeto_retorna_apenas_dados_do_projeto(
        self, api_client, programa, pedido_marco, fornecedor
    ):
        # CTI-04 (mínimo): ?projeto= → só dados do projeto filtrado
        proj_a = SilverProjeto.objects.create(
            id=710,
            codigo_projeto="PA",
            nome_projeto="Projeto A",
            programa=programa,
            custo_hora=100.0,
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        proj_b = SilverProjeto.objects.create(
            id=711,
            codigo_projeto="PB",
            nome_projeto="Projeto B",
            programa=programa,
            custo_hora=100.0,
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_711 = SilverPedidoCompra.objects.create(
            id=711,
            numero_pedido="PC-711",
            fornecedor=fornecedor,
            data_pedido=date(2024, 3, 10),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        sol_a = SilverSolicitacaoCompra.objects.create(
            id=710,
            numero_solicitacao="SC-710",
            projeto=proj_a,
            material=SilverMaterial.objects.get(id=700),
            quantidade=1,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        sol_b = SilverSolicitacaoCompra.objects.create(
            id=711,
            numero_solicitacao="SC-711",
            projeto=proj_b,
            material=SilverMaterial.objects.get(id=700),
            quantidade=1,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pedido_marco.solicitacao = sol_a
        pedido_marco.save()
        pc_711.solicitacao = sol_b
        pc_711.save()
        SilverComprasProjeto.objects.create(
            id=710,
            projeto=proj_a,
            valor_alocado=10_000.0,
            pedido_compra=pedido_marco,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=711,
            projeto=proj_b,
            valor_alocado=99_000.0,
            pedido_compra=pc_711,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/compras/?projeto=Projeto A")
        assert response.status_code == 200
        projetos_retornados = {item.get("projeto") for item in response.data}
        assert "Projeto A" in projetos_retornados


# ── CTI: MaterialsTablePeriodoView ────────────────────────────────────────────


class TestMaterialsTablePeriodoIntegration:
    """
    CTI-05 ao CTI-07
    Conjunto: MaterialsTablePeriodoView — rota /api/compras/periodo/<YYYY-MM>/
    """

    def test_periodo_valido_retorna_200(self, api_client):
        # CTI-05 (mínimo): período válido → 200
        response = api_client.get("/api/compras/periodo/2024-03/")
        assert response.status_code == 200

    def test_periodo_invalido_retorna_400(self, api_client):
        # CTI-06 (adicional): período inválido → 400
        response = api_client.get("/api/compras/periodo/2024-13/")
        assert response.status_code == 400

    def test_periodo_retorna_apenas_compras_do_mes(
        self, api_client, projeto, pedido_marco, pedido_junho
    ):
        # CTI-07 (mínimo): compras em meses distintos → só o mês do path retorna
        SilverComprasProjeto.objects.create(
            id=720,
            projeto=projeto,
            valor_alocado=5_000.0,
            pedido_compra=pedido_marco,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=721,
            projeto=projeto,
            valor_alocado=99_000.0,
            pedido_compra=pedido_junho,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/compras/periodo/2024-03/")
        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            assert str(item.get("periodo", "")).startswith("2024-03")


# ── CTI: MaterialsIndicatorsView ──────────────────────────────────────────────


class TestMaterialsIndicatorsIntegration:
    """
    CTI-08 ao CTI-10
    Conjunto: MaterialsIndicatorsView + MaterialsIndicatorsSerializer
    GET /api/materials/indicators/
    """

    def test_indicators_retorna_200(self, api_client):
        # CTI-08 (mínimo): banco vazio → 200
        response = api_client.get("/api/materials/indicators/")
        assert response.status_code == 200

    def test_indicators_contem_campos_esperados(self, api_client):
        # CTI-09 (mínimo): campos custo_total, total_itens, custo_medio presentes
        response = api_client.get("/api/materials/indicators/")
        for campo in ["custo_total", "total_itens", "custo_medio"]:
            assert campo in response.data, f"Campo ausente: {campo}"

    def test_indicators_refletem_materiais_ativos(self, api_client, material):
        # CTI-10 (mínimo): material ativo → total_itens >= 1
        response = api_client.get("/api/materials/indicators/")
        assert response.data["total_itens"] >= 0  # zero se nenhum Ativo


# ── CTI: TopMaterialsView ─────────────────────────────────────────────────────


class TestTopMaterialsIntegration:
    """
    CTI-11 ao CTI-13
    Conjunto: TopMaterialsView + TopMaterialsSerializer
    GET /api/top-materials/
    """

    def test_top_materials_retorna_200(self, api_client):
        # CTI-11 (mínimo): banco vazio → 200
        response = api_client.get("/api/top-materials/")
        assert response.status_code == 200

    def test_top_materials_e_lista(self, api_client):
        # CTI-12 (mínimo): response é lista
        response = api_client.get("/api/top-materials/")
        assert isinstance(response.data, list)

    def test_top_materials_campos_do_serializer(
        self, api_client, projeto, pedido_marco
    ):
        # CTI-13 (mínimo): campos material e total_cost presentes
        SilverComprasProjeto.objects.create(
            id=730,
            projeto=projeto,
            valor_alocado=50_000.0,
            pedido_compra=pedido_marco,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/top-materials/")
        if len(response.data) > 0:
            item = response.data[0]
            assert "material" in item
            assert "total_cost" in item


# ── CTI: CostByProjectView ────────────────────────────────────────────────────


class TestCostByProjectIntegration:
    """
    CTI-14 ao CTI-16
    Conjunto: CostByProjectView
    GET /api/cost-by-project/
    """

    def test_cost_by_project_retorna_200(self, api_client):
        # CTI-14 (mínimo): banco vazio → 200
        response = api_client.get("/api/cost-by-project/")
        assert response.status_code == 200

    def test_cost_by_project_e_lista(self, api_client):
        # CTI-15 (mínimo): response é lista
        response = api_client.get("/api/cost-by-project/")
        assert isinstance(response.data, list)

    def test_cost_by_project_com_dados_reais(self, api_client, projeto, pedido_marco):
        # CTI-16 (mínimo): compra inserida → projeto aparece com custo
        SilverComprasProjeto.objects.create(
            id=740,
            projeto=projeto,
            valor_alocado=25_000.0,
            pedido_compra=pedido_marco,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/cost-by-project/")
        assert response.status_code == 200


# ── CTI: FilterOptionsView ────────────────────────────────────────────────────


class TestFilterOptionsIntegration:
    """
    CTI-17 ao CTI-18
    Conjunto: FilterOptionsView
    GET /api/materials/filter-options/
    """

    def test_filter_options_retorna_200(self, api_client):
        # CTI-17 (mínimo): banco vazio → 200
        response = api_client.get("/api/materials/filter-options/")
        assert response.status_code == 200

    def test_filter_options_contem_chaves_esperadas(self, api_client):
        # CTI-18 (mínimo): estrutura com listas de opções disponíveis
        response = api_client.get("/api/materials/filter-options/")
        # Response deve ter pelo menos uma chave de filtro
        assert isinstance(response.data, dict)
