from django.utils import timezone

from materials.serializers import (
    MaterialsIndicatorsSerializer,
    MaterialsTableSerializer,
)
from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)


def test_materials_serializer_retorna_dados_corretos():
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

    serializer = MaterialsTableSerializer(pedido)

    assert serializer.data["material"] == "Cabo de aço"
    assert serializer.data["projeto"] == "Projeto Alpha"
    assert serializer.data["programa"] == "Programa Alpha"
    assert serializer.data["quantidade"] == 10
    assert serializer.data["valor_unitario"] == 150.00
    assert serializer.data["fornecedor"] == "Fornecedor Ltda"
    assert serializer.data["categoria"] == "Estrutural"


def test_materials_indicators_serializer_retorna_campos_corretos():
    data = {"custo_total": 4500.53, "total_itens": 3, "custo_medio": 1500.27}
    serializer = MaterialsIndicatorsSerializer(data)

    assert serializer.data["custo_total"] == 4500.53
    assert serializer.data["total_itens"] == 3
    assert serializer.data["custo_medio"] == 1500.27


def test_materials_indicators_serializer_aceita_valores_nulos():
    data = {"custo_total": None, "total_itens": 0, "custo_medio": None}
    serializer = MaterialsIndicatorsSerializer(data)

    assert serializer.data["custo_total"] is None
    assert serializer.data["total_itens"] == 0
    assert serializer.data["custo_medio"] is None
