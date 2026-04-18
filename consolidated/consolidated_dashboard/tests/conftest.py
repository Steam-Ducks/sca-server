import datetime

import pytest
from django.utils import timezone

from sca_data.models import (SilverFornecedor, SilverMaterial,
                             SilverPedidoCompra, SilverPrograma, SilverProjeto,
                             SilverSolicitacaoCompra, SilverTarefaProjeto,
                             SilverTempoTarefa)


@pytest.fixture
def rf():
    from django.test import RequestFactory
    return RequestFactory()


@pytest.fixture
def projeto_em_memoria():
    now = timezone.now()

    programa = SilverPrograma(
        id=1,
        codigo_programa="PROG-001",
        nome_programa="Cloud",
        silver_ingested_at=now,
    )

    projeto = SilverProjeto(
        id=1,
        codigo_projeto="PROJ-001",
        nome_projeto="Migração AWS",
        custo_hora=420.00,
        status="Em Andamento",
        silver_ingested_at=now,
    )
    projeto.programa = programa

    # Horas técnicas
    tarefa = SilverTarefaProjeto(
        id=1,
        codigo_tarefa="TAR-001",
        titulo="Arquitetura Cloud",
        responsavel="Cloud Architect",
        estimativa_horas=400,
        silver_ingested_at=now,
    )
    tarefa.projeto = projeto

    tempo = SilverTempoTarefa(
        id=1,
        usuario="Lucas Martins",
        data=datetime.date(2024, 3, 15),
        horas_trabalhadas=40.00,
        silver_ingested_at=now,
    )
    tempo.tarefa = tarefa

    # Materiais
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
        data_pedido=datetime.date(2024, 3, 10),
        valor_total=1500.00,
        silver_ingested_at=now,
    )
    pedido.solicitacao = solicitacao
    pedido.fornecedor = fornecedor

    # Attach annotations manually (as the ORM would)
    projeto.custo_materiais = 1500.00
    projeto.custo_horas = 40.00 * 420.00   # 16800.00
    projeto.qtd_materiais = 10
    projeto.total_horas = 40.00

    return projeto
