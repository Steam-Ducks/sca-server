"""
Conjunto de integração: Dashboard (atualizado)

Funções do conjunto:
    get_dashboard_kpis (selectors.py)         — KPIs agregados
    get_projects_by_period (selectors.py)     — lista de projetos por período
    get_program_summary (selectors.py)        — resumo por programa
    get_cost_composition (selectors.py)       — composição materiais vs horas
    get_top_projects_by_cost (selectors.py)   — ranking de projetos
    get_cost_evolution (selectors.py)         — evolução mensal
    DashboardKPIsView     GET /api/dashboard/kpis/
    MainDashboardView     GET /api/dashboard/projects/
    SummaryTableView      GET /api/dashboard/summary/
    CostCompositionView   GET /api/dashboard/composition/
    TopProjectsView       GET /api/dashboard/top-projects/
    CostEvolutionView     GET /api/dashboard/cost-evolution/
"""

import os
import pytest
from datetime import date, datetime, timezone

from sca_data.models import (
    SilverComprasProjeto,
    SilverFornecedor,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
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
        id=100,
        codigo_programa="MANSUP",
        nome_programa="MANSUP",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=100,
        codigo_projeto="PROJ-100",
        nome_projeto="Conversor DC-DC",
        programa=programa,
        custo_hora=200.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def fornecedor(db):
    return SilverFornecedor.objects.create(
        id=100,
        codigo_fornecedor="FORN-100",
        razao_social="Fornecedor SA",
        cidade="SP",
        estado="SP",
        categoria="Eletrônicos",
        status="Ativo",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_compra(db, fornecedor):
    return SilverPedidoCompra.objects.create(
        id=100,
        numero_pedido="PC-100",
        fornecedor=fornecedor,
        data_pedido=date(2024, 3, 15),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def tarefa(db, projeto):
    return SilverTarefaProjeto.objects.create(
        id=100,
        codigo_tarefa="TAR-100",
        titulo="Implementação",
        projeto=projeto,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


# ── CTI: DashboardKPIsView ────────────────────────────────────────────────────


class TestDashboardKPIsIntegration:
    """
    CTI-01 ao CTI-05
    Conjunto: get_dashboard_kpis + DashboardKPIsView + DashboardKPIsSerializer

    Carga: 0–3 objetos silver por teste.
    """

    def test_kpis_retornam_200_com_banco_vazio(self, api_client):
        # CTI-01 (mínimo): banco vazio → GET retorna 200
        response = api_client.get("/api/dashboard/kpis/")
        assert response.status_code == 200

    def test_kpis_contem_todos_os_campos_esperados(self, api_client):
        # CTI-02 (mínimo): estrutura de campos da resposta
        response = api_client.get("/api/dashboard/kpis/")
        for campo in [
            "total_consolidated_cost",
            "total_materials_cost",
            "total_hours_cost",
            "total_projects",
            "total_programs",
        ]:
            assert campo in response.data, f"Campo ausente: {campo}"

    def test_custo_materiais_reflete_soma_real_do_banco(
        self, api_client, projeto, pedido_compra
    ):
        # CTI-03 (mínimo): compra inserida → custo_materiais somado
        SilverComprasProjeto.objects.create(
            id=1,
            projeto=projeto,
            valor_alocado=80_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=2,
            projeto=projeto,
            valor_alocado=20_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/kpis/")
        assert float(response.data["total_materials_cost"]) == 100_000.0

    def test_custo_horas_reflete_horas_trabalhadas_reais(
        self, api_client, projeto, tarefa
    ):
        # CTI-04 (adicional): horas técnicas → custo_horas = horas × custo_hora
        SilverTempoTarefa.objects.create(
            id=1,
            tarefa=tarefa,
            usuario="dev1@sca.com",
            data=date(2024, 3, 10),
            horas_trabalhadas=10.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/kpis/")
        assert float(response.data["total_hours_cost"]) == 200.0 * 10.0

    def test_filtro_por_programa_isola_dados(
        self, api_client, programa, projeto, pedido_compra, fornecedor
    ):
        # CTI-05 (adicional): ?program= → KPIs só do programa filtrado
        outro_programa = SilverPrograma.objects.create(
            id=200,
            codigo_programa="INFRA",
            nome_programa="Infraestrutura",
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        outro_projeto = SilverProjeto.objects.create(
            id=200,
            codigo_projeto="PROJ-200",
            nome_projeto="Projeto INFRA",
            programa=outro_programa,
            custo_hora=100.0,
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_outro = SilverPedidoCompra.objects.create(
            id=200,
            numero_pedido="PC-200",
            fornecedor=fornecedor,
            data_pedido=date(2024, 3, 15),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=10,
            projeto=projeto,
            valor_alocado=50_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=20,
            projeto=outro_projeto,
            valor_alocado=999_000.0,
            pedido_compra=pc_outro,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/kpis/?program=MANSUP")
        assert response.status_code == 200
        assert float(response.data["total_materials_cost"]) == 50_000.0


# ── CTI: MainDashboardView ────────────────────────────────────────────────────


class TestMainDashboardIntegration:
    """
    CTI-06 ao CTI-08
    Conjunto: get_projects_by_period + MainDashboardView + MainDashboardSerializer
    GET /api/dashboard/projects/

    Carga: 0–2 objetos SilverProjeto por teste.
    """

    def test_projects_retorna_200(self, api_client):
        # CTI-06 (mínimo): banco vazio → 200
        response = api_client.get("/api/dashboard/projects/")
        assert response.status_code == 200

    def test_projects_contem_campos_esperados(self, api_client, projeto):
        # CTI-07 (mínimo): campos id, nome_projeto, status presentes
        response = api_client.get("/api/dashboard/projects/")
        assert len(response.data) >= 1
        item = response.data[0]
        assert "id" in item
        assert "nome_projeto" in item
        assert "status" in item

    def test_projeto_inserido_aparece_na_response(self, api_client, projeto):
        # CTI-08 (mínimo): projeto real → aparece na lista
        response = api_client.get("/api/dashboard/projects/")
        nomes = [p["nome_projeto"] for p in response.data]
        assert "Conversor DC-DC" in nomes


# ── CTI: SummaryTableView ─────────────────────────────────────────────────────


class TestSummaryTableIntegration:
    """
    CTI-09 ao CTI-11
    Conjunto: get_program_summary + SummaryTableView + ProgramSummarySerializer
    GET /api/dashboard/summary/

    Carga: 0–2 objetos silver por teste.
    """

    def test_summary_retorna_200(self, api_client):
        # CTI-09 (mínimo): banco vazio → 200
        response = api_client.get("/api/dashboard/summary/")
        assert response.status_code == 200

    def test_summary_e_lista(self, api_client):
        # CTI-10 (mínimo): response é sempre lista
        response = api_client.get("/api/dashboard/summary/")
        assert isinstance(response.data, list)

    def test_summary_contem_campos_do_serializer(
        self, api_client, projeto, pedido_compra
    ):
        # CTI-11 (mínimo): campos corretos chegam do ProgramSummarySerializer
        SilverComprasProjeto.objects.create(
            id=30,
            projeto=projeto,
            valor_alocado=10_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/summary/")
        assert len(response.data) >= 1
        item = response.data[0]
        for campo in [
            "programa",
            "qtd_projetos",
            "custo_materiais",
            "custo_horas",
            "custo_total",
        ]:
            assert campo in item, f"Campo ausente: {campo}"


# ── CTI: CostCompositionView ──────────────────────────────────────────────────


class TestCostCompositionIntegration:
    """
    CTI-12 ao CTI-14
    Conjunto: get_cost_composition + CostCompositionView + CostCompositionSerializer
    GET /api/dashboard/composition/

    Carga: 0–2 objetos silver por teste.
    """

    def test_composition_retorna_200(self, api_client):
        # CTI-12 (mínimo): banco vazio → 200
        response = api_client.get("/api/dashboard/composition/")
        assert response.status_code == 200

    def test_composition_contem_campos_esperados(self, api_client):
        # CTI-13 (mínimo): campos do CostCompositionSerializer presentes
        response = api_client.get("/api/dashboard/composition/")
        for campo in [
            "custo_materiais",
            "custo_horas",
            "custo_total",
            "pct_materiais",
            "pct_horas",
        ]:
            assert campo in response.data, f"Campo ausente: {campo}"

    def test_composicao_com_dados_reais(
        self, api_client, projeto, pedido_compra, tarefa
    ):
        # CTI-14 (mínimo): custo real → pct_materiais + pct_horas = 100
        SilverComprasProjeto.objects.create(
            id=40,
            projeto=projeto,
            valor_alocado=60_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=40,
            tarefa=tarefa,
            usuario="dev@sca.com",
            data=date(2024, 3, 1),
            horas_trabalhadas=200.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/composition/")
        total_pct = float(response.data["pct_materiais"]) + float(
            response.data["pct_horas"]
        )
        assert abs(total_pct - 100.0) < 0.01


# ── CTI: TopProjectsView ──────────────────────────────────────────────────────


class TestTopProjectsIntegration:
    """
    CTI-15 ao CTI-17
    Conjunto: get_top_projects_by_cost + TopProjectsView + TopProjectSerializer
    GET /api/dashboard/top-projects/
    """

    def test_top_projects_retornam_200(self, api_client):
        # CTI-15 (mínimo): banco vazio → 200
        response = api_client.get("/api/dashboard/top-projects/")
        assert response.status_code == 200

    def test_top_projects_campos_do_serializer(
        self, api_client, projeto, pedido_compra
    ):
        # CTI-16 (mínimo): campos project_name e total_cost presentes
        SilverComprasProjeto.objects.create(
            id=50,
            projeto=projeto,
            valor_alocado=100_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/top-projects/")
        assert len(response.data) >= 1
        item = response.data[0]
        assert "project_name" in item
        assert "total_cost" in item

    def test_top_projects_ordenados_por_custo_decrescente(
        self, api_client, programa, fornecedor
    ):
        # CTI-17 (adicional): ordenação decrescente por custo
        proj_barato = SilverProjeto.objects.create(
            id=301,
            codigo_projeto="P301",
            nome_projeto="Projeto Barato",
            programa=programa,
            custo_hora=100.0,
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        proj_caro = SilverProjeto.objects.create(
            id=302,
            codigo_projeto="P302",
            nome_projeto="Projeto Caro",
            programa=programa,
            custo_hora=100.0,
            status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_301 = SilverPedidoCompra.objects.create(
            id=301,
            numero_pedido="PC-301",
            fornecedor=fornecedor,
            data_pedido=date(2024, 3, 15),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_302 = SilverPedidoCompra.objects.create(
            id=302,
            numero_pedido="PC-302",
            fornecedor=fornecedor,
            data_pedido=date(2024, 3, 15),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=301,
            projeto=proj_barato,
            valor_alocado=1_000.0,
            pedido_compra=pc_301,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=302,
            projeto=proj_caro,
            valor_alocado=900_000.0,
            pedido_compra=pc_302,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/dashboard/top-projects/")
        assert len(response.data) >= 2
        assert response.data[0]["project_name"] == "Projeto Caro"


# ── CTI: CostEvolutionView ────────────────────────────────────────────────────


class TestCostEvolutionIntegration:
    """
    CTI-18 ao CTI-20
    Conjunto: get_cost_evolution + CostEvolutionView + CostEvolutionSerializer
    GET /api/dashboard/cost-evolution/
    """

    def test_cost_evolution_retorna_200(self, api_client):
        # CTI-18 (mínimo): banco vazio → 200
        response = api_client.get("/api/dashboard/cost-evolution/")
        assert response.status_code == 200

    def test_cost_evolution_e_lista(self, api_client):
        # CTI-19 (mínimo): response é sempre lista
        response = api_client.get("/api/dashboard/cost-evolution/")
        assert isinstance(response.data, list)

    def test_filtro_por_data_retorna_apenas_periodo_correto(
        self, api_client, programa, projeto, fornecedor
    ):
        # CTI-20 (mínimo): dados em jan e dez → filtro jan retorna só jan
        pc_jan = SilverPedidoCompra.objects.create(
            id=501,
            numero_pedido="PC-501",
            fornecedor=fornecedor,
            data_pedido=date(2024, 1, 15),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_dez = SilverPedidoCompra.objects.create(
            id=502,
            numero_pedido="PC-502",
            fornecedor=fornecedor,
            data_pedido=date(2024, 12, 15),
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=501,
            projeto=projeto,
            valor_alocado=10_000.0,
            pedido_compra=pc_jan,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=502,
            projeto=projeto,
            valor_alocado=99_000.0,
            pedido_compra=pc_dez,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get(
            "/api/dashboard/cost-evolution/?start_date=2024-01-01&end_date=2024-03-31"
        )
        assert response.status_code == 200
        meses = [item["period"] for item in response.data]
        assert "2024-01" in meses
        assert "2024-12" not in meses
