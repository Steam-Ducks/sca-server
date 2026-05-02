import datetime
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from materials.views import MaterialsTablePeriodoView
from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)

URL = "/api/compras/periodo/"


def _make_pedido(
    id=1,
    descricao="Cabo de aço",
    categoria="Estrutural",
    custo_estimado=150.00,
    quantidade=10,
    valor_total=1500.00,
    data_pedido=datetime.date(2024, 3, 15),
    razao_social="Fornecedor Ltda",
    nome_projeto="Projeto Alpha",
    nome_programa="Programa Alpha",
):
    now = timezone.now()

    programa = SilverPrograma(
        id=id,
        codigo_programa=f"PROG-{id:03}",
        nome_programa=nome_programa,
        silver_ingested_at=now,
    )
    projeto = SilverProjeto(
        id=id,
        codigo_projeto=f"PROJ-{id:03}",
        nome_projeto=nome_projeto,
        silver_ingested_at=now,
    )
    projeto.programa = programa

    material = SilverMaterial(
        id=id,
        codigo_material=f"MAT-{id:03}",
        descricao=descricao,
        categoria=categoria,
        custo_estimado=custo_estimado,
        silver_ingested_at=now,
    )
    fornecedor = SilverFornecedor(
        id=id,
        codigo_fornecedor=f"FORN-{id:03}",
        razao_social=razao_social,
        silver_ingested_at=now,
    )
    solicitacao = SilverSolicitacaoCompra(
        id=id,
        numero_solicitacao=f"SC-{id:03}",
        quantidade=quantidade,
        silver_ingested_at=now,
    )
    solicitacao.projeto = projeto
    solicitacao.material = material

    pedido = SilverPedidoCompra(
        id=id,
        numero_pedido=f"PC-{id:03}",
        data_pedido=data_pedido,
        valor_total=valor_total,
        silver_ingested_at=now,
    )
    pedido.solicitacao = solicitacao
    pedido.fornecedor = fornecedor
    return pedido


# ---------------------------------------------------------------------------
# Testes do endpoint dedicado /api/compras/periodo/<YYYY-MM>/
# ---------------------------------------------------------------------------


def test_periodo_endpoint_retorna_200():
    with patch.object(MaterialsTablePeriodoView, "get_queryset", return_value=[]):
        response = APIClient().get(f"{URL}2024-03/")
        assert response.status_code == 200


def test_periodo_endpoint_retorna_lista_vazia():
    with patch.object(MaterialsTablePeriodoView, "get_queryset", return_value=[]):
        response = APIClient().get(f"{URL}2024-03/")
        assert response.data == []


def test_periodo_endpoint_retorna_lista():
    pedido = _make_pedido()
    with patch.object(MaterialsTablePeriodoView, "get_queryset", return_value=[pedido]):
        response = APIClient().get(f"{URL}2024-03/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_periodo_endpoint_retorna_campos_corretos():
    pedido = _make_pedido()
    with patch.object(MaterialsTablePeriodoView, "get_queryset", return_value=[pedido]):
        response = APIClient().get(f"{URL}2024-03/")
        item = response.data[0]
        assert item["material"] == "Cabo de aço"
        assert item["projeto"] == "Projeto Alpha"
        assert item["programa"] == "Programa Alpha"
        assert item["quantidade"] == 10
        assert item["valor_unitario"] == 150.00
        assert item["valor_total"] == 1500.00
        assert item["fornecedor"] == "Fornecedor Ltda"
        assert item["categoria"] == "Estrutural"
        assert item["periodo"] == "2024-03"


def test_periodo_endpoint_multiplos_registros():
    pedido1 = _make_pedido(id=1)
    pedido2 = _make_pedido(
        id=2,
        descricao="Tubo galvanizado",
        categoria="Hidráulico",
        custo_estimado=80.00,
        quantidade=25,
        valor_total=2000.00,
        data_pedido=datetime.date(2024, 3, 20),
        razao_social="Distribuidora SA",
        nome_projeto="Projeto Beta",
        nome_programa="Programa Beta",
    )
    with patch.object(
        MaterialsTablePeriodoView, "get_queryset", return_value=[pedido1, pedido2]
    ):
        response = APIClient().get(f"{URL}2024-03/")
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["material"] == "Cabo de aço"
        assert response.data[1]["material"] == "Tubo galvanizado"


def test_periodo_endpoint_periodo_invalido_retorna_400():
    response = APIClient().get(f"{URL}2024-13/")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_endpoint_formato_errado_retorna_400():
    for bad in ["202403", "abcd-ef", "2024-3"]:
        response = APIClient().get(f"{URL}{bad}/")
        assert response.status_code == 400, f"Esperado 400 para '{bad}'"


def test_periodo_endpoint_com_barra_retorna_404():
    response = APIClient().get("/api/compras/periodo/2024/03/")
    assert response.status_code == 404


def test_periodo_endpoint_dezembro_ultimo_dia_correto():
    view = MaterialsTablePeriodoView()
    inicio, fim = view._parse_periodo("2024-12")
    assert inicio == datetime.date(2024, 12, 1)
    assert fim == datetime.date(2024, 12, 31)


def test_periodo_endpoint_janeiro_ultimo_dia_correto():
    view = MaterialsTablePeriodoView()
    inicio, fim = view._parse_periodo("2024-01")
    assert inicio == datetime.date(2024, 1, 1)
    assert fim == datetime.date(2024, 1, 31)


def test_periodo_endpoint_fevereiro_ano_bissexto():
    view = MaterialsTablePeriodoView()
    inicio, fim = view._parse_periodo("2024-02")
    assert inicio == datetime.date(2024, 2, 1)
    assert fim == datetime.date(2024, 2, 29)


def test_periodo_endpoint_fevereiro_ano_nao_bissexto():
    view = MaterialsTablePeriodoView()
    inicio, fim = view._parse_periodo("2023-02")
    assert inicio == datetime.date(2023, 2, 1)
    assert fim == datetime.date(2023, 2, 28)
