from consolidated.consolidated_dashboard.serializers import (
    ConsolidatedDashboardSerializer,
)
from django.utils import timezone

from sca_data.models import SilverPrograma, SilverProjeto


def _make_projeto(
    custo_materiais=1500.00, custo_horas=16800.00, qtd_materiais=10, total_horas=40.00
):
    now = timezone.now()
    programa = SilverPrograma(
        id=1, codigo_programa="P-001", nome_programa="Cloud", silver_ingested_at=now
    )
    projeto = SilverProjeto(
        id=1,
        codigo_projeto="PR-001",
        nome_projeto="Migração AWS",
        custo_hora=420.00,
        status="Em Andamento",
        silver_ingested_at=now,
    )
    projeto.programa = programa
    projeto.custo_materiais = custo_materiais
    projeto.custo_horas = custo_horas
    projeto.qtd_materiais = qtd_materiais
    projeto.total_horas = total_horas
    return projeto


def test_serializer_retorna_campos_corretos():
    projeto = _make_projeto()
    serializer = ConsolidatedDashboardSerializer(projeto)
    data = serializer.data

    assert data["nome_projeto"] == "Migração AWS"
    assert data["programa"] == "Cloud"
    assert data["status"] == "Em Andamento"
    assert data["custo_materiais"] == 1500.00
    assert data["custo_horas"] == 16800.00
    assert data["custo_total"] == 18300.00
    assert data["qtd_materiais"] == 10
    assert data["total_horas"] == 40.00


def test_serializer_retorna_todos_os_campos():
    projeto = _make_projeto()
    serializer = ConsolidatedDashboardSerializer(projeto)
    expected = {
        "id",
        "nome_projeto",
        "programa",
        "custo_materiais",
        "custo_horas",
        "custo_total",
        "qtd_materiais",
        "total_horas",
        "status",
    }
    assert set(serializer.data.keys()) == expected


def test_serializer_custo_total_soma_materiais_e_horas():
    projeto = _make_projeto(custo_materiais=5000.00, custo_horas=3000.00)
    serializer = ConsolidatedDashboardSerializer(projeto)
    assert serializer.data["custo_total"] == 8000.00


def test_serializer_programa_none_quando_sem_programa():
    now = timezone.now()
    projeto = SilverProjeto(
        id=1,
        codigo_projeto="PR-001",
        nome_projeto="Sem Programa",
        custo_hora=100.00,
        silver_ingested_at=now,
    )
    projeto.programa = None
    projeto.custo_materiais = 0
    projeto.custo_horas = 0
    projeto.qtd_materiais = 0
    projeto.total_horas = 0
    serializer = ConsolidatedDashboardSerializer(projeto)
    assert serializer.data["programa"] is None


def test_serializer_custo_none_tratado_como_zero():
    projeto = _make_projeto(custo_materiais=None, custo_horas=None)
    serializer = ConsolidatedDashboardSerializer(projeto)
    assert serializer.data["custo_materiais"] == 0
    assert serializer.data["custo_horas"] == 0
    assert serializer.data["custo_total"] == 0
