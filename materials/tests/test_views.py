from unittest.mock import patch

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
