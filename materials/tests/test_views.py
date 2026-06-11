import pytest
from unittest.mock import MagicMock, patch

from django.utils import timezone

from materials.views import (
    MaterialsIndicatorsView,
    MaterialsTableView,
)
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


def test_materials_table_returns_200(api_client):
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        response = api_client.get("/api/compras/")
        assert response.status_code == 200


def test_materials_table_returns_list(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_materials_table_retorna_campos_corretos(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/")
        item = response.data[0]
        assert item["material"] == "Cabo de aço"
        assert item["projeto"] == "Projeto Alpha"
        assert item["programa"] == "Programa Alpha"
        assert item["quantidade"] == 10
        assert item["valor_unitario"] == pytest.approx(150.00)
        assert item["valor_total"] == pytest.approx(1500.00)
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


def test_materials_indicators_returns_200(api_client):
    with patch.object(
        MaterialsIndicatorsView,
        "_build_materiais_queryset",
        return_value=_mock_materiais_qs(),
    ):
        response = api_client.get("/api/materials/indicators/")
        assert response.status_code == 200


def test_materials_indicators_retorna_campos_corretos(api_client):
    mock_qs = _mock_materiais_qs(
        custo_total=4500.53, total_itens=3, custo_medio=1500.27
    )
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = api_client.get("/api/materials/indicators/")
        assert response.data["custo_total"] == pytest.approx(4500.53)
        assert response.data["total_itens"] == 3
        assert response.data["custo_medio"] == pytest.approx(1500.27)


def test_materials_indicators_sem_dados_retorna_nulos(api_client):
    mock_qs = _mock_materiais_qs(custo_total=None, total_itens=0, custo_medio=None)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = api_client.get("/api/materials/indicators/")
        assert response.data["custo_total"] is None
        assert response.data["total_itens"] == 0
        assert response.data["custo_medio"] is None


def test_materials_indicators_filtra_por_categoria(api_client):
    mock_qs = _mock_materiais_qs(custo_total=1000.0, total_itens=2, custo_medio=500.0)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = api_client.get("/api/materials/indicators/?categoria=LED")
        assert response.status_code == 200
        assert response.data["total_itens"] == 2


def test_materials_indicators_filtra_por_programa(api_client):
    mock_qs = _mock_materiais_qs(custo_total=800.0, total_itens=1, custo_medio=800.0)
    with patch.object(
        MaterialsIndicatorsView, "_build_materiais_queryset", return_value=mock_qs
    ):
        response = api_client.get("/api/materials/indicators/?programa=Cloud")
        assert response.status_code == 200
        assert response.data["total_itens"] == 1


# ─── Filtros por período na view base ────────────────────────────────────────


def test_filtro_por_periodo_yyyy_mm_retorna_200(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/?periodo=2024-03")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_inicio_retorna_200(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/?data_inicio=2024-03-01")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_fim_retorna_200(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/?data_fim=2024-03-31")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_inicio_e_fim_retorna_200(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get(
            "/api/compras/?data_inicio=2024-03-01&data_fim=2024-03-31"
        )
        assert response.status_code == 200
        assert len(response.data) == 1


def test_periodo_invalido_retorna_400(api_client):
    response = api_client.get("/api/compras/?periodo=invalido")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_com_mes_invalido_retorna_400(api_client):
    response = api_client.get("/api/compras/?periodo=2024-13")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_data_inicio_invalida_retorna_400(api_client):
    response = api_client.get("/api/compras/?data_inicio=nao-e-data")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_data_inicio_posterior_a_data_fim_retorna_400(api_client):
    response = api_client.get(
        "/api/compras/?data_inicio=2024-03-31&data_fim=2024-03-01"
    )
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_sem_filtro_retorna_todos_registros(api_client):
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        response = api_client.get("/api/compras/")
        assert response.status_code == 200
        assert len(response.data) == 1


# ─── TopMaterialsView ─────────────────────────────────────────────────────────


def _mock_top_materials(data=None):
    if data is None:
        data = [{"material": "Cabo de aço", "total_cost": 9000.00}]
    mock = MagicMock()
    mock.__iter__ = MagicMock(return_value=iter(data))
    return mock


def test_top_materials_retorna_200(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = [{"material": "Cabo de aço", "total_cost": 9000.00}]
        response = api_client.get("/api/top-materials/")
    assert response.status_code == 200


def test_top_materials_retorna_lista_vazia(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get("/api/top-materials/")
    assert response.status_code == 200
    assert response.data == []


def test_top_materials_retorna_campos_corretos(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = [{"material": "Cabo de aço", "total_cost": 9000.50}]
        response = api_client.get("/api/top-materials/")
    assert response.data[0]["material"] == "Cabo de aço"
    assert response.data[0]["total_cost"] == 9000.50


def test_top_materials_aceita_filtro_periodo(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get("/api/top-materials/?periodo=2024-03")
    assert response.status_code == 200
    call_params = mock_fn.call_args[0][0]
    assert call_params.get("periodo") == "2024-03"


def test_top_materials_aceita_filtro_data_inicio_e_fim(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get(
            "/api/top-materials/?data_inicio=2024-03-01&data_fim=2024-03-31"
        )
    assert response.status_code == 200
    call_params = mock_fn.call_args[0][0]
    assert call_params.get("data_inicio") == "2024-03-01"
    assert call_params.get("data_fim") == "2024-03-31"


def test_top_materials_limit_customizado(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = []
        api_client.get("/api/top-materials/?limit=5")
    assert mock_fn.call_args[1]["limit"] == 5


def test_top_materials_limit_invalido_retorna_400(api_client):
    response = api_client.get("/api/top-materials/?limit=abc")
    assert response.status_code == 400
    assert "limit" in response.data


def test_top_materials_aceita_filtro_programa(api_client):
    with patch("materials.views.get_top_materials_by_financial_impact") as mock_fn:
        mock_fn.return_value = []
        api_client.get("/api/top-materials/?programa=Programa+Alpha")
    call_params = mock_fn.call_args[0][0]
    assert call_params.get("programa") == "Programa Alpha"


# ─── CostByProjectView ────────────────────────────────────────────────────────


def test_cost_by_project_retorna_200(api_client):
    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get("/api/cost-by-project/")
    assert response.status_code == 200


def test_cost_by_project_retorna_lista_vazia(api_client):
    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get("/api/cost-by-project/")
    assert response.data == []


def test_cost_by_project_retorna_campos_corretos(api_client):
    from decimal import Decimal

    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = [
            {"projeto": "Projeto Alpha", "total_cost": Decimal("5000.75")}
        ]
        response = api_client.get("/api/cost-by-project/")
    assert response.data[0]["projeto"] == "Projeto Alpha"
    assert response.data[0]["total_cost"] == 5000.75


def test_cost_by_project_converte_decimal_para_float(api_client):
    from decimal import Decimal

    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = [{"projeto": "Proj X", "total_cost": Decimal("1234.56")}]
        response = api_client.get("/api/cost-by-project/")
    assert isinstance(response.data[0]["total_cost"], float)


def test_cost_by_project_aceita_filtro_periodo(api_client):
    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get("/api/cost-by-project/?periodo=2024-03")
    assert response.status_code == 200
    call_params = mock_fn.call_args[0][0]
    assert call_params.get("periodo") == "2024-03"


def test_cost_by_project_aceita_filtro_data_inicio_e_fim(api_client):
    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = []
        response = api_client.get(
            "/api/cost-by-project/?data_inicio=2024-01-01&data_fim=2024-03-31"
        )
    assert response.status_code == 200
    call_params = mock_fn.call_args[0][0]
    assert call_params.get("data_inicio") == "2024-01-01"
    assert call_params.get("data_fim") == "2024-03-31"


def test_cost_by_project_total_cost_none_retorna_zero(api_client):
    with patch("materials.views.get_cost_by_project") as mock_fn:
        mock_fn.return_value = [{"projeto": "Proj Y", "total_cost": None}]
        response = api_client.get("/api/cost-by-project/")
    assert response.data[0]["total_cost"] == 0.0


# ─── FilterOptionsView ────────────────────────────────────────────────────────

_FILTER_OPTIONS_FIXTURE = {
    "periodos": ["2024-03", "2024-02", "2024-01"],
    "programas": ["Programa Alpha", "Programa Beta"],
    "projetos": [
        {"nome": "Projeto Alpha", "programa": "Programa Alpha"},
        {"nome": "Projeto Beta", "programa": "Programa Beta"},
    ],
    "categorias": ["Elétrico", "Estrutural"],
    "fornecedores": ["Distribuidora SA", "Metalúrgica SA"],
}


def test_filter_options_retorna_200(api_client):
    with patch(
        "materials.views.get_filter_options", return_value=_FILTER_OPTIONS_FIXTURE
    ):
        response = api_client.get("/api/materials/filter-options/")
    assert response.status_code == 200


def test_filter_options_retorna_todas_as_chaves(api_client):
    with patch(
        "materials.views.get_filter_options", return_value=_FILTER_OPTIONS_FIXTURE
    ):
        response = api_client.get("/api/materials/filter-options/")
    assert set(response.data.keys()) == {
        "periodos",
        "programas",
        "projetos",
        "categorias",
        "fornecedores",
    }


def test_filter_options_periodos_sao_strings_yyyy_mm(api_client):
    with patch(
        "materials.views.get_filter_options", return_value=_FILTER_OPTIONS_FIXTURE
    ):
        response = api_client.get("/api/materials/filter-options/")
    for p in response.data["periodos"]:
        assert len(p) == 7 and p[4] == "-", f"Período inválido: {p}"


def test_filter_options_projetos_tem_nome_e_programa(api_client):
    with patch(
        "materials.views.get_filter_options", return_value=_FILTER_OPTIONS_FIXTURE
    ):
        response = api_client.get("/api/materials/filter-options/")
    for proj in response.data["projetos"]:
        assert "nome" in proj
        assert "programa" in proj


def test_filter_options_retorna_listas_vazias_sem_dados(api_client):
    vazio = {
        "periodos": [],
        "programas": [],
        "projetos": [],
        "categorias": [],
        "fornecedores": [],
    }
    with patch("materials.views.get_filter_options", return_value=vazio):
        response = api_client.get("/api/materials/filter-options/")
    assert response.status_code == 200
    assert response.data["periodos"] == []
    assert response.data["projetos"] == []
