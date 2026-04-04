import pytest
from django.utils import timezone

from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)
from materials.serializers import MaterialsTableSerializer


@pytest.mark.django_db
def test_materials_serializer_retorna_dados_corretos():
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
        valor_total=1500.00,
        silver_ingested_at=now,
    )

    pedido_com_relacionamentos = SilverPedidoCompra.objects.select_related(
        "solicitacao__material",
        "solicitacao__projeto__programa",
        "fornecedor",
    ).get(id=1)

    serializer = MaterialsTableSerializer(pedido_com_relacionamentos)

    assert serializer.data["material"] == "Cabo de aço"
    assert serializer.data["projeto"] == "Projeto Alpha"
    assert serializer.data["programa"] == "Programa Alpha"
    assert serializer.data["quantidade"] == 10
    assert serializer.data["valor_unitario"] == 150.00
    assert serializer.data["fornecedor"] == "Fornecedor Ltda"
    assert serializer.data["categoria"] == "Estrutural"
