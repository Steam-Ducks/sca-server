import datetime
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from consolidated.consolidated_dashboard.views import ConsolidatedDashboardPeriodoView
from sca_data.models import SilverPrograma, SilverProjeto


def _make_projeto(
    id=1,
    nome_projeto="Migracao AWS",
    nome_programa="Cloud",
    status="Em Andamento",
    custo_hora=420.00,
    custo_materiais=1500.00,
    custo_horas=16800.00,
    qtd_materiais=10,
    total_horas=40.00,
):
    now = timezone.now()
    programa = SilverPrograma(
        id=id,
        codigo_programa=f"P-{id}",
        nome_programa=nome_programa,
        silver_ingested_at=now,
    )
    projeto = SilverProjeto(
        id=id,
        codigo_projeto=f"PR-{id}",
        nome_projeto=nome_projeto,
        custo_hora=custo_hora,
        status=status,
        silver_ingested_at=now,
    )
    projeto.programa = programa
    projeto.custo_materiais = custo_materiais
    projeto.custo_horas = custo_horas
    projeto.qtd_materiais = qtd_materiais
    projeto.total_horas = total_horas
    return projeto


def test_periodo_endpoint_retorna_200():
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView, "_get_last_updated_at", return_value=None
        ):
            client = APIClient()
            response = client.get("/api/consolidated/periodo/2024-03/")
            assert response.status_code == 200


def test_periodo_endpoint_retorna_lista():
    projeto = _make_projeto()
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[projeto]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView,
            "_get_last_updated_at",
            return_value=datetime.datetime(
                2026, 4, 26, 8, 15, tzinfo=datetime.timezone.utc
            ),
        ):
            client = APIClient()
            response = client.get("/api/consolidated/periodo/2024-03/")
            assert isinstance(response.data["data"], list)
            assert len(response.data["data"]) == 1
            assert response.data["last_updated_at"] == "2026-04-26T08:15:00+00:00"


def test_periodo_endpoint_retorna_campos_corretos():
    projeto = _make_projeto()
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[projeto]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView, "_get_last_updated_at", return_value=None
        ):
            client = APIClient()
            response = client.get("/api/consolidated/periodo/2024-03/")
            item = response.data["data"][0]
            assert item["nome_projeto"] == "Migracao AWS"
            assert item["programa"] == "Cloud"
            assert item["custo_materiais"] == 1500.00
            assert item["custo_horas"] == 16800.00
            assert item["custo_total"] == 18300.00
            assert item["total_horas"] == 40.00


def test_periodo_endpoint_periodo_invalido_retorna_400():
    client = APIClient()
    response = client.get("/api/consolidated/periodo/2024-13/")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_endpoint_formato_errado_retorna_400():
    client = APIClient()
    for bad in ["202403", "abcd-ef", "2024-3"]:
        response = client.get(f"/api/consolidated/periodo/{bad}/")
        assert response.status_code == 400, f"Esperado 400 para '{bad}'"


def test_periodo_endpoint_com_barra_retorna_404():
    client = APIClient()
    response = client.get("/api/consolidated/periodo/2024/03/")
    assert response.status_code == 404


def test_periodo_endpoint_dezembro_ultimo_dia_correto():
    view = ConsolidatedDashboardPeriodoView()
    inicio, fim = view._parse_periodo("2024-12")
    assert inicio == datetime.date(2024, 12, 1)
    assert fim == datetime.date(2024, 12, 31)


def test_periodo_endpoint_janeiro_ultimo_dia_correto():
    view = ConsolidatedDashboardPeriodoView()
    inicio, fim = view._parse_periodo("2024-01")
    assert inicio == datetime.date(2024, 1, 1)
    assert fim == datetime.date(2024, 1, 31)


def test_periodo_endpoint_com_filtro_programa():
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView, "_get_last_updated_at", return_value=None
        ):
            client = APIClient()
            response = client.get("/api/consolidated/periodo/2024-03/?programa=Cloud")
            assert response.status_code == 200


def test_periodo_endpoint_com_filtro_status():
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView, "_get_last_updated_at", return_value=None
        ):
            client = APIClient()
            response = client.get(
                "/api/consolidated/periodo/2024-03/?status=Em Andamento"
            )
            assert response.status_code == 200


def test_periodo_endpoint_lista_vazia():
    with patch.object(
        ConsolidatedDashboardPeriodoView, "get_queryset", return_value=[]
    ):
        with patch.object(
            ConsolidatedDashboardPeriodoView, "_get_last_updated_at", return_value=None
        ):
            client = APIClient()
            response = client.get("/api/consolidated/periodo/2024-03/")
            assert response.status_code == 200
            assert response.data == {"data": [], "last_updated_at": None}
