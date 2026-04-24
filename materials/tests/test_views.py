from unittest.mock import MagicMock, patch

from django.utils import timezone
from rest_framework.test import APIClient

from materials.views import MaterialsIndicatorsView, MaterialsTableView
from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)


def _criar_pedido_em_memoria():
    now = timezone.now()

    programa = SilverPrograma(
        id=1,
        codigo_programa="PROG-001",
        nome_programa="Programa Alpha",
        silver_ingested_at=now,
    )
    projeto = SilverProjeto(
        id=1,
        codigo_projeto="PROJ-001",
        nome_projeto="Projeto Alpha",
        silver_ingested_at=now,
    )
    projeto.programa = programa

    material = SilverMaterial(
        id=1,
        codigo_material="MAT-001",
        descricao="Cabo de aço",
        categoria="Estrutural",
        custo_estimado=150.00,
        silver_ingested_at=now,
    )
    fornecedor = SilverFornecedor(
        id=1,
        codigo_fornecedor="FORN-001",
        razao_social="Fornecedor Ltda",
        silver_ingested_at=now,
    )
    solicitacao = SilverSolicitacaoCompra(
        id=1,
        numero_solicitacao="SC-001",
        quantidade=10,
        silver_ingested_at=now,
    )
    solicitacao.projeto = projeto
    solicitacao.material = material

    pedido = SilverPedidoCompra(
        id=1,
        numero_pedido="PC-001",
        data_pedido=timezone.now().date(),
        valor_total=1500.00,
        silver_ingested_at=now,
    )
    pedido.solicitacao = solicitacao
    pedido.fornecedor = fornecedor
    return pedido


def test_materials_table_returns_200():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        response = APIClient().get("/api/compras/")
        assert response.status_code == 200


def test_materials_table_returns_list():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_materials_table_retorna_campos_corretos():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/")
        item = response.data[0]
        assert item["material"] == "Cabo de aço"
        assert item["projeto"] == "Projeto Alpha"
        assert item["programa"] == "Programa Alpha"
        assert item["quantidade"] == 10
        assert item["valor_unitario"] == 150.00
        assert item["valor_total"] == 1500.00
        assert item["fornecedor"] == "Fornecedor Ltda"
        assert item["categoria"] == "Estrutural"


# ── Materials indicators ──────────────────────────────────────────────────────


def _mock_materiais_qs(custo_total=4500.0, total_itens=3, custo_medio=1500.0):
    mock_qs = MagicMock()
    mock_qs.filter.return_value = mock_qs
    mock_qs.aggregate.return_value = {
        "custo_total": custo_total,
        "total_itens": total_itens,
        "custo_medio": custo_medio,
    }
    return mock_qs


def test_materials_indicators_returns_200():
    with patch.object(
        MaterialsIndicatorsView,
        "_build_materiais_queryset",
        return_value=_mock_materiais_qs(),
    ):
        response = APIClient().get("/api/materials/indicators/")
        assert response.status_code == 200


def test_materials_indicators_retorna_campos_corretos():
    mock_qs = _mock_materiais_qs(
        custo_total=4500.53, total_itens=3, custo_medio=1500.27
    )
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = APIClient().get("/api/materials/indicators/")
        assert response.data["custo_total"] == 4500.53
        assert response.data["total_itens"] == 3
        assert response.data["custo_medio"] == 1500.27


def test_materials_indicators_sem_dados_retorna_nulos():
    mock_qs = _mock_materiais_qs(custo_total=None, total_itens=0, custo_medio=None)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = APIClient().get("/api/materials/indicators/")
        assert response.data["custo_total"] is None
        assert response.data["total_itens"] == 0
        assert response.data["custo_medio"] is None


def test_materials_indicators_filtra_por_categoria():
    mock_qs = _mock_materiais_qs(custo_total=1000.0, total_itens=2, custo_medio=500.0)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = APIClient().get("/api/materials/indicators/?categoria=LED")
        assert response.status_code == 200
        assert response.data["total_itens"] == 2


def test_materials_indicators_filtra_por_programa():
    mock_qs = _mock_materiais_qs(custo_total=800.0, total_itens=1, custo_medio=800.0)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = APIClient().get("/api/materials/indicators/?programa=Cloud")
        assert response.status_code == 200
        assert response.data["total_itens"] == 1


# ─── Filtros por período na view base ────────────────────────────────────────


def test_filtro_por_periodo_yyyy_mm_retorna_200():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/?periodo=2024-03")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_inicio_retorna_200():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/?data_inicio=2024-03-01")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_fim_retorna_200():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/?data_fim=2024-03-31")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_inicio_e_fim_retorna_200():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/?data_inicio=2024-03-01&data_fim=2024-03-31")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_periodo_invalido_retorna_400():
    response = APIClient().get("/api/compras/?periodo=invalido")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_com_mes_invalido_retorna_400():
    response = APIClient().get("/api/compras/?periodo=2024-13")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_data_inicio_invalida_retorna_400():
    response = APIClient().get("/api/compras/?data_inicio=nao-e-data")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_data_inicio_posterior_a_data_fim_retorna_400():
    response = APIClient().get("/api/compras/?data_inicio=2024-03-31&data_fim=2024-03-01")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_sem_filtro_retorna_todos_registros():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = APIClient().get("/api/compras/")
        assert response.status_code == 200
        assert len(response.data) == 1
