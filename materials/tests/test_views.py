import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)
from materials.views import MaterialsTableView


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------

def _criar_pedido_em_memoria(
    id=1,
    data_pedido=None,
    valor_total=1500.00,
    nome_programa="Programa Alpha",
    nome_projeto="Projeto Alpha",
    descricao_material="Cabo de aço",
    categoria="Estrutural",
    custo_estimado=150.00,
    quantidade=10,
    razao_social="Fornecedor Ltda",
):
    now = timezone.now()
    if data_pedido is None:
        data_pedido = datetime.date(2024, 3, 15)

    programa = SilverPrograma(id=id, codigo_programa=f"PROG-{id:03}", nome_programa=nome_programa, silver_ingested_at=now)
    projeto = SilverProjeto(id=id, codigo_projeto=f"PROJ-{id:03}", nome_projeto=nome_projeto, silver_ingested_at=now)
    projeto.programa = programa

    material = SilverMaterial(id=id, codigo_material=f"MAT-{id:03}", descricao=descricao_material, categoria=categoria, custo_estimado=custo_estimado, silver_ingested_at=now)
    fornecedor = SilverFornecedor(id=id, codigo_fornecedor=f"FORN-{id:03}", razao_social=razao_social, silver_ingested_at=now)

    solicitacao = SilverSolicitacaoCompra(id=id, numero_solicitacao=f"SC-{id:03}", quantidade=quantidade, silver_ingested_at=now)
    solicitacao.projeto = projeto
    solicitacao.material = material

    pedido = SilverPedidoCompra(id=id, numero_pedido=f"PC-{id:03}", data_pedido=data_pedido, valor_total=valor_total, silver_ingested_at=now)
    pedido.solicitacao = solicitacao
    pedido.fornecedor = fornecedor
    return pedido


def test_materials_table_returns_200():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.status_code == 200


def test_materials_table_returns_list():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_materials_table_retorna_campos_corretos():
    pedido = _criar_pedido_em_memoria()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/")

        item = response.data[0]
        assert item["material"] == "Cabo de aço"
        assert item["projeto"] == "Projeto Alpha"
        assert item["programa"] == "Programa Alpha"
        assert item["quantidade"] == 10
        assert item["valor_unitario"] == 150.00
        assert item["valor_total"] == 1500.00
        assert item["fornecedor"] == "Fornecedor Ltda"
        assert item["categoria"] == "Estrutural"


def test_materials_table_lista_vazia_retorna_200():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.status_code == 200
        assert response.data == []


def test_materials_table_retorna_multiplos_registros():
    pedido1 = _criar_pedido_em_memoria(id=1)
    pedido2 = _criar_pedido_em_memoria(id=2, razao_social="Outro Fornecedor", valor_total=800.00)

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido1, pedido2]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.status_code == 200
        assert len(response.data) == 2


# ---------------------------------------------------------------------------
# Filtro: ?periodo=YYYY-MM
# ---------------------------------------------------------------------------

def test_filter_periodo_retorna_registros_do_mes():
    pedido_marco = _criar_pedido_em_memoria(data_pedido=datetime.date(2024, 3, 15))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido_marco]):
        client = APIClient()
        response = client.get("/api/compras/?periodo=2024-03")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filter_periodo_sem_registros_retorna_lista_vazia():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/?periodo=2025-06")
        assert response.status_code == 200
        assert response.data == []


def test_filter_periodo_invalido_mes_inexistente_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/?periodo=2024-13")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_filter_periodo_formato_errado_retorna_400():
    client = APIClient()
    for bad in ["202403", "2024/03", "abcd-ef", "2024-3"]:
        response = client.get(f"/api/compras/?periodo={bad}")
        assert response.status_code == 400, f"Esperado 400 para '{bad}'"
        assert "periodo" in response.data


# ---------------------------------------------------------------------------
# Filtro: ?data_inicio e ?data_fim
# ---------------------------------------------------------------------------

def test_filter_data_inicio_retorna_200():
    pedido = _criar_pedido_em_memoria(data_pedido=datetime.date(2024, 3, 15))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/?data_inicio=2024-03-01")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filter_data_fim_retorna_200():
    pedido = _criar_pedido_em_memoria(data_pedido=datetime.date(2024, 1, 10))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/?data_fim=2024-01-31")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filter_data_inicio_e_fim_retorna_intervalo():
    pedido = _criar_pedido_em_memoria(data_pedido=datetime.date(2024, 3, 15))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/?data_inicio=2024-03-01&data_fim=2024-03-31")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filter_data_inicio_maior_que_data_fim_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/?data_inicio=2024-12-01&data_fim=2024-01-01")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_filter_data_inicio_formato_invalido_retorna_400():
    client = APIClient()
    for bad in ["15-03-2024", "2024/03/15", "abcdefgh", "2024-3-1"]:
        response = client.get(f"/api/compras/?data_inicio={bad}")
        assert response.status_code == 400, f"Esperado 400 para '{bad}'"
        assert "data_inicio" in response.data


def test_filter_data_fim_formato_invalido_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/?data_fim=data-invalida")
    assert response.status_code == 400
    assert "data_fim" in response.data


def test_filter_so_data_inicio_e_aceito():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/?data_inicio=2024-01-01")
        assert response.status_code == 200


def test_filter_so_data_fim_e_aceito():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/?data_fim=2024-12-31")
        assert response.status_code == 200


def test_sem_filtro_retorna_todos():
    pedido1 = _criar_pedido_em_memoria(id=1, data_pedido=datetime.date(2024, 1, 10))
    pedido2 = _criar_pedido_em_memoria(id=2, data_pedido=datetime.date(2024, 6, 20))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido1, pedido2]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.status_code == 200
        assert len(response.data) == 2


# ---------------------------------------------------------------------------
# Prioridade: data_inicio/data_fim tem prioridade sobre periodo
# ---------------------------------------------------------------------------

def test_data_inicio_tem_prioridade_sobre_periodo():
    pedido = _criar_pedido_em_memoria(data_pedido=datetime.date(2024, 3, 15))

    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        # periodo=2024-01 seria janeiro, mas data_inicio=2024-03-01 deve ter prioridade
        response = client.get("/api/compras/?data_inicio=2024-03-01&periodo=2024-01")
        assert response.status_code == 200
        assert isinstance(response.data, list)


# ---------------------------------------------------------------------------
# Verificação do ORM (unit — sem HTTP)
# ---------------------------------------------------------------------------

def test_get_queryset_aplica_filtro_data_inicio(rf):
    from rest_framework.request import Request
    request = rf.get("/api/compras/", {"data_inicio": "2024-03-01"})
    drf_request = Request(request)

    view = MaterialsTableView()
    view.request = drf_request
    view.kwargs = {}

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs

    with patch("materials.views.SilverPedidoCompra.objects", mock_qs):
        view.get_queryset()

    filter_calls = mock_qs.filter.call_args_list
    assert any(
        "data_pedido__gte" in str(call) for call in filter_calls
    ), "Esperado filtro data_pedido__gte"


def test_get_queryset_aplica_filtro_data_fim(rf):
    from rest_framework.request import Request
    request = rf.get("/api/compras/", {"data_fim": "2024-03-31"})
    drf_request = Request(request)

    view = MaterialsTableView()
    view.request = drf_request
    view.kwargs = {}

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs

    with patch("materials.views.SilverPedidoCompra.objects", mock_qs):
        view.get_queryset()

    filter_calls = mock_qs.filter.call_args_list
    assert any(
        "data_pedido__lte" in str(call) for call in filter_calls
    ), "Esperado filtro data_pedido__lte"


def test_get_queryset_sem_filtro_nao_aplica_date_range(rf):
    from rest_framework.request import Request
    request = rf.get("/api/compras/")
    drf_request = Request(request)

    view = MaterialsTableView()
    view.request = drf_request
    view.kwargs = {}

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs

    with patch("materials.views.SilverPedidoCompra.objects", mock_qs):
        view.get_queryset()

    filter_calls = mock_qs.filter.call_args_list
    date_filters = [c for c in filter_calls if "data_pedido__gte" in str(c) or "data_pedido__lte" in str(c)]
    assert len(date_filters) == 0, "Nenhum filtro de data deve ser aplicado sem parâmetros"


def test_get_queryset_periodo_expande_para_primeiro_e_ultimo_dia(rf):
    from rest_framework.request import Request
    request = rf.get("/api/compras/", {"periodo": "2024-03"})
    drf_request = Request(request)

    view = MaterialsTableView()
    view.request = drf_request
    view.kwargs = {}

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs

    with patch("materials.views.SilverPedidoCompra.objects", mock_qs):
        view.get_queryset()

    filter_calls = mock_qs.filter.call_args_list
    kwargs_aplicados = {k: v for call in filter_calls for k, v in call.kwargs.items()}
    assert kwargs_aplicados.get("data_pedido__gte") == datetime.date(2024, 3, 1), "Esperado primeiro dia do mês"
    assert kwargs_aplicados.get("data_pedido__lte") == datetime.date(2024, 3, 31), "Esperado último dia do mês"


def test_get_queryset_periodo_dezembro_expande_corretamente(rf):
    """Dezembro: último dia deve ser 31/12, não 01/01 do ano seguinte."""
    from rest_framework.request import Request
    request = rf.get("/api/compras/", {"periodo": "2024-12"})
    drf_request = Request(request)

    view = MaterialsTableView()
    view.request = drf_request
    view.kwargs = {}

    mock_qs = MagicMock()
    mock_qs.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs

    with patch("materials.views.SilverPedidoCompra.objects", mock_qs):
        view.get_queryset()

    filter_calls = mock_qs.filter.call_args_list
    kwargs_aplicados = {k: v for call in filter_calls for k, v in call.kwargs.items()}
    assert kwargs_aplicados.get("data_pedido__gte") == datetime.date(2024, 12, 1)
    assert kwargs_aplicados.get("data_pedido__lte") == datetime.date(2024, 12, 31)