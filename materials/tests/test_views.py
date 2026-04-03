import pytest
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


def criar_pedido_completo():
    now = timezone.now()

    programa = SilverPrograma.objects.create(
        id=1,
        codigo_programa="PROG-001",
        nome_programa="Programa Alpha",
        silver_ingested_at=now,
    )
    projeto = SilverProjeto.objects.create(
        id=1,
        codigo_projeto="PROJ-001",
        nome_projeto="Projeto Alpha",
        programa=programa,
        silver_ingested_at=now,
    )
    material = SilverMaterial.objects.create(
        id=1,
        codigo_material="MAT-001",
        descricao="Cabo de aço",
        categoria="Estrutural",
        custo_estimado=150.00,
        silver_ingested_at=now,
    )
    fornecedor = SilverFornecedor.objects.create(
        id=1,
        codigo_fornecedor="FORN-001",
        razao_social="Fornecedor Ltda",
        silver_ingested_at=now,
    )
    solicitacao = SilverSolicitacaoCompra.objects.create(
        id=1,
        numero_solicitacao="SC-001",
        projeto=projeto,
        material=material,
        quantidade=10,
        silver_ingested_at=now,
    )
    SilverPedidoCompra.objects.create(
        id=1,
        numero_pedido="PC-001",
        solicitacao=solicitacao,
        fornecedor=fornecedor,
        data_pedido=timezone.now().date(),
        valor_total=1500.00,
        silver_ingested_at=now,
    )


@pytest.mark.django_db
def test_materials_table_returns_200():
    client = APIClient()

    criar_pedido_completo()

    response = client.get("/api/compras/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_materials_table_returns_list():
    client = APIClient()

    criar_pedido_completo()

    response = client.get("/api/compras/")

    assert isinstance(response.data, list)
    assert len(response.data) == 1


@pytest.mark.django_db
def test_materials_table_retorna_campos_corretos():
    client = APIClient()

    criar_pedido_completo()

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
