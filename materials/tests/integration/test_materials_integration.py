"""
Conjunto de integração: Materials (Gestão de Materiais)

Funções do conjunto:
    parse_period (core/utils)           — converte YYYY-MM em intervalo de datas
    get_materials_queryset (selectors)  — filtra SilverPedidoCompra com ORM
    MaterialsTableView (views.py)       — endpoint GET /api/compras/
    MaterialsTablePeriodoView           — endpoint GET /api/compras/periodo/<YYYY-MM>/
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

# Skip when PostgreSQL is unavailable (SQLite CI environment).
# To run locally: export DB_HOST=postgres (or your host) before pytest.
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver/gold schemas — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=700,
        codigo_programa="INFRA",
        nome_programa="Infraestrutura",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    # SilverProjeto.id is BigIntegerField — explicit id required
    return SilverProjeto.objects.create(
        id=700,
        codigo_projeto="PROJ-700",
        nome_projeto="Projeto Infra Base",
        programa=programa,
        custo_hora=150.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def material(db):
    # SilverMaterial.id is BigIntegerField (no auto-increment) — explicit id required
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
    """SilverSolicitacaoCompra required by get_materials_queryset Q(solicitacao__isnull=False)."""
    # SilverSolicitacaoCompra.id is BigIntegerField — explicit id required
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
    """Pedido de compra em março/2024, vinculado à solicitação."""
    # SilverPedidoCompra.id is BigIntegerField — explicit id required
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
    """Pedido de compra em junho/2024, vinculado à mesma solicitação."""
    return SilverPedidoCompra.objects.create(
        id=701,
        numero_pedido="PC-701",
        fornecedor=fornecedor,
        solicitacao=solicitacao,
        data_pedido=date(2024, 6, 20),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


class TestMaterialsTableIntegration:
    """
    CT-INT-MAT-01
    Conjunto: get_materials_queryset + MaterialsTableView + MaterialsTableSerializer
    """

    def test_lista_retorna_200(self, api_client):
        # CTI-01 (mínimo): banco vazio → GET /api/compras/ retorna 200
        response = api_client.get("/api/compras/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self, api_client):
        # CTI-02 (mínimo): banco vazio → resposta é lista vazia
        response = api_client.get("/api/compras/")
        assert response.data == []

    def test_lista_retorna_pedidos_reais(self, api_client, projeto, pedido_marco):
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

        # The view filters via solicitacao__projeto — need separate solicitacoes per project
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
        assert "Projeto B" not in projetos_retornados


class TestMaterialsTablePeriodoIntegration:
    """
    CT-INT-MAT-02
    Conjunto: parse_period + get_materials_queryset + MaterialsTablePeriodoView
    """

    def test_periodo_valido_retorna_200(self, api_client):
        # CTI-05 (mínimo): período válido no path → 200
        response = api_client.get("/api/compras/periodo/2024-03/")
        assert response.status_code == 200

    def test_periodo_invalido_retorna_400(self, api_client):
        # CTI-06 (adicional): formato de período inválido → 400
        # Valida: parse_period levanta ValidationError propagada pela view
        response = api_client.get("/api/compras/periodo/2024-13/")
        assert response.status_code == 400

    def test_periodo_retorna_apenas_compras_do_mes(
        self, api_client, projeto, pedido_marco, pedido_junho
    ):
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
        # periodo may be a string "YYYY-MM" or date object — str() handles both
        for item in response.data:
            assert str(item.get("periodo", "")).startswith("2024-03")
