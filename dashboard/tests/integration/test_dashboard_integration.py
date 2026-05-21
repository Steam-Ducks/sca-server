"""
Conjunto de integração: Dashboard

Funções do conjunto:
    build_filters (selectors.py)         — monta cláusulas WHERE para SQL raw
    get_dashboard_kpis (selectors.py)    — executa SQL e retorna dict de KPIs
    get_top_projects_by_cost (selectors) — ranking de projetos por custo
    get_cost_evolution (selectors)       — série temporal de custos por mês
    DashboardKPIsView (views.py)         — endpoint GET /api/dashboard/kpis/
    TopProjectsView (views.py)           — endpoint GET /api/dashboard/top-projects/
    CostEvolutionView (views.py)         — endpoint GET /api/dashboard/cost-evolution/
"""

import pytest
from datetime import date, datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverFornecedor,
    SilverPrograma,
    SilverProjeto,
    SilverComprasProjeto,
    SilverPedidoCompra,
    SilverSolicitacaoCompra,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=100,
        codigo_programa="MANSUP",
        nome_programa="Manutenção Supressores",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=100,
        codigo_projeto="PROJ-100",
        nome_projeto="Sensor Pressão Industrial",
        programa=programa,
        custo_hora=200.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def fornecedor(db):
    """FIX: fornecedor_id é NOT NULL em SilverPedidoCompra."""
    return SilverFornecedor.objects.create(
        id=100,
        codigo_fornecedor="FORN-100",
        razao_social="Fornecedor Teste Ltda",
        cidade="São Paulo",
        estado="SP",
        categoria="Eletrônicos",
        status="Ativo",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def pedido_compra(db, projeto, fornecedor):
    """FIX: passa fornecedor=fornecedor — campo obrigatório no modelo."""
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
        projeto=projeto,
        titulo="Tarefa Teste",
        estimativa_horas=40,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


# ── CT-INT-DASH-01: KPIs ──────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardKPIsIntegration:
    """
    CT-INT-DASH-01
    Conjunto: build_filters + get_dashboard_kpis + DashboardKPIsView + serializer
    """

    def test_kpis_retornam_200_com_banco_vazio(self):
        response = APIClient().get("/api/dashboard/kpis/")
        assert response.status_code == 200

    def test_kpis_contem_todos_os_campos_esperados(self):
        response = APIClient().get("/api/dashboard/kpis/")
        campos = [
            "total_consolidated_cost",
            "total_materials_cost",
            "total_hours_cost",
            "total_projects",
            "total_programs",
        ]
        for campo in campos:
            assert campo in response.data, f"Campo ausente: {campo}"

    def test_custo_materiais_reflete_soma_real_do_banco(self, projeto, pedido_compra):
        sol = SilverSolicitacaoCompra.objects.create(
            id=1,
            projeto=projeto,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=1,
            solicitacao=sol,
            valor_alocado=80_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=2,
            solicitacao=sol,
            valor_alocado=20_000.0,
            pedido_compra=pedido_compra,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/dashboard/kpis/")
        assert float(response.data["total_materials_cost"]) == 100_000.0

    def test_filtro_por_programa_isola_dados(self, programa, projeto, pedido_compra, fornecedor):
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

        sol_mansup = SilverSolicitacaoCompra.objects.create(
            id=10, projeto=projeto, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        sol_infra = SilverSolicitacaoCompra.objects.create(
            id=20, projeto=outro_projeto, silver_ingested_at=datetime.now(tz=timezone.utc)
        )

        SilverComprasProjeto.objects.create(
            id=10, solicitacao=sol_mansup, valor_alocado=50_000.0,
            pedido_compra=pedido_compra, silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=20, solicitacao=sol_infra, valor_alocado=999_000.0,
            pedido_compra=pc_outro, silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/dashboard/kpis/?program=MANSUP")
        assert response.status_code == 200
        assert float(response.data["total_materials_cost"]) == 50_000.0

    def test_custo_horas_reflete_horas_trabalhadas_reais(self, projeto, tarefa):
        SilverTempoTarefa.objects.create(
            id=1, tarefa=tarefa, usuario="dev1@sca.com",
            data=date(2024, 3, 10), horas_trabalhadas=10.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=2, tarefa=tarefa, usuario="dev2@sca.com",
            data=date(2024, 3, 11), horas_trabalhadas=8.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/dashboard/kpis/")
        assert float(response.data["total_hours_cost"]) == 200.0 * 18.0


# ── CT-INT-DASH-02: Top Projects ──────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.django_db
class TestTopProjectsIntegration:
    """
    CT-INT-DASH-02
    Conjunto: build_filters + get_top_projects_by_cost + TopProjectsView + serializer
    """

    def test_top_projects_retornam_200(self):
        response = APIClient().get("/api/dashboard/top-projects/")
        assert response.status_code == 200

    def test_top_projects_ordenados_por_custo_decrescente(self, programa, fornecedor):
        proj_barato = SilverProjeto.objects.create(
            id=301, codigo_projeto="P301", nome_projeto="Projeto Barato",
            programa=programa, custo_hora=100.0, status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        proj_caro = SilverProjeto.objects.create(
            id=302, codigo_projeto="P302", nome_projeto="Projeto Caro",
            programa=programa, custo_hora=100.0, status="Em andamento",
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_301 = SilverPedidoCompra.objects.create(
            id=301, numero_pedido="PC-301", fornecedor=fornecedor,
            data_pedido=date(2024, 3, 15), silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_302 = SilverPedidoCompra.objects.create(
            id=302, numero_pedido="PC-302", fornecedor=fornecedor,
            data_pedido=date(2024, 3, 15), silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        sol_barato = SilverSolicitacaoCompra.objects.create(
            id=301, projeto=proj_barato, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        sol_caro = SilverSolicitacaoCompra.objects.create(
            id=302, projeto=proj_caro, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        SilverComprasProjeto.objects.create(
            id=301, solicitacao=sol_barato, valor_alocado=1_000.0,
            pedido_compra=pc_301, silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=302, solicitacao=sol_caro, valor_alocado=900_000.0,
            pedido_compra=pc_302, silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/dashboard/top-projects/")
        assert len(response.data) >= 2
        assert response.data[0]["nome_projeto"] == "Projeto Caro"

    def test_top_projects_limita_a_10_resultados(self, programa, fornecedor):
        for i in range(15):
            proj = SilverProjeto.objects.create(
                id=400 + i, codigo_projeto=f"P4{i:02d}",
                nome_projeto=f"Projeto {i:02d}", programa=programa,
                custo_hora=100.0, status="Em andamento",
                silver_ingested_at=datetime.now(tz=timezone.utc),
            )
            pc = SilverPedidoCompra.objects.create(
                id=400 + i, numero_pedido=f"PC-4{i:02d}", fornecedor=fornecedor,
                data_pedido=date(2024, 3, 15), silver_ingested_at=datetime.now(tz=timezone.utc),
            )
            sol = SilverSolicitacaoCompra.objects.create(
                id=400 + i, projeto=proj, silver_ingested_at=datetime.now(tz=timezone.utc)
            )
            SilverComprasProjeto.objects.create(
                id=400 + i, solicitacao=sol, valor_alocado=float(i * 1000),
                pedido_compra=pc, silver_ingested_at=datetime.now(tz=timezone.utc),
            )

        response = APIClient().get("/api/dashboard/top-projects/")
        assert len(response.data) <= 10


# ── CT-INT-DASH-03: Cost Evolution ───────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.django_db
class TestCostEvolutionIntegration:
    """
    CT-INT-DASH-03
    Conjunto: get_cost_evolution + CostEvolutionView + CostEvolutionSerializer
    """

    def test_cost_evolution_retornam_200(self):
        response = APIClient().get("/api/dashboard/cost-evolution/")
        assert response.status_code == 200

    def test_cost_evolution_retorna_lista(self):
        response = APIClient().get("/api/dashboard/cost-evolution/")
        assert isinstance(response.data, list)

    def test_filtro_por_data_retorna_apenas_periodo_correto(
        self, programa, projeto, fornecedor
    ):
        sol = SilverSolicitacaoCompra.objects.create(
            id=501, projeto=projeto, silver_ingested_at=datetime.now(tz=timezone.utc)
        )
        pc_jan = SilverPedidoCompra.objects.create(
            id=501, numero_pedido="PC-501", fornecedor=fornecedor,
            data_pedido=date(2024, 1, 15), silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        pc_dez = SilverPedidoCompra.objects.create(
            id=502, numero_pedido="PC-502", fornecedor=fornecedor,
            data_pedido=date(2024, 12, 15), silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=501, solicitacao=sol, valor_alocado=10_000.0,
            pedido_compra=pc_jan, silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverComprasProjeto.objects.create(
            id=502, solicitacao=sol, valor_alocado=99_000.0,
            pedido_compra=pc_dez, silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get(
            "/api/dashboard/cost-evolution/?start_date=2024-01-01&end_date=2024-03-31"
        )
        assert response.status_code == 200
        meses = [item["periodo"] for item in response.data]
        assert "2024-12" not in meses
