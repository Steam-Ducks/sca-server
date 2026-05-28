"""
Conjunto de integração: Monitoring

Funções do conjunto:
    FatoExecucaoCarga (sca_data.models)  — tabela audit."fato_execucao_carga"
    get_execucoes_carga (selectors.py)   — filtra por status, data, tabela, fonte
    ExecucaoCargaView (views.py)         — GET /api/monitoring/execucoes/
    FatoExecucaoCargaSerializer          — serializa + computa duracao_segundos
    CanAccessMonitoring                  — super_admin acessa tudo

NOTA: FatoExecucaoCarga tem managed=True → tabela criada pelas migrations.
Nenhum xfail necessário — conjunto completo.

CTI-01 ao CTI-08
Referência Jira: SCA-356
"""

import uuid
import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import FatoExecucaoCarga


@pytest.fixture
def execucao_base(db):
    return FatoExecucaoCarga.objects.create(
        run_id=uuid.uuid4(),
        fonte="bronze_silver",
        tabela="projetos",
        tipo_processo="COMPLETA",
        status="SUCCESS",
        linhas_processadas=150,
        erros=0,
        avisos=0,
        iniciado_em=datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
        finalizado_em=datetime(2024, 3, 15, 10, 5, tzinfo=timezone.utc),
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestMonitoringListIntegration:
    """
    CTI-01 ao CTI-04
    Conjunto: ExecucaoCargaView + FatoExecucaoCargaSerializer + CanAccessMonitoring
    """

    def test_retorna_200_com_banco_vazio(self, api_client):
        # CTI-01
        response = api_client.get("/api/monitoring/execucoes/")
        assert response.status_code == 200

    def test_retorna_403_sem_autenticacao(self):
        # CTI-02
        response = APIClient().get("/api/monitoring/execucoes/")
        assert response.status_code == 403

    def test_retorna_campos_corretos(self, api_client, execucao_base):
        # CTI-03
        response = api_client.get("/api/monitoring/execucoes/")
        assert len(response.data) >= 1
        item = response.data[0]
        for campo in ["id", "run_id", "fonte", "tabela", "status",
                      "linhas_processadas", "erros", "duracao_segundos"]:
            assert campo in item, f"Campo ausente: {campo}"

    def test_duracao_segundos_calculada_pelo_serializer(self, api_client, execucao_base):
        # CTI-04 — campo computado: 10:05 - 10:00 = 300s
        response = api_client.get("/api/monitoring/execucoes/")
        item = next(
            i for i in response.data
            if str(i["run_id"]) == str(execucao_base.run_id)
        )
        assert item["duracao_segundos"] == 300


@pytest.mark.integration
@pytest.mark.django_db
class TestMonitoringFiltrosIntegration:
    """
    CTI-05 ao CTI-08
    Conjunto: get_execucoes_carga (filtros por status/tabela/data) + ExecucaoCargaView
    """

    def test_filtro_por_status_retorna_apenas_status_correto(self, api_client, db):
        # CTI-05
        FatoExecucaoCarga.objects.create(
            run_id=uuid.uuid4(), fonte="etl", tabela="projetos",
            status="SUCCESS", iniciado_em=datetime.now(tz=timezone.utc),
        )
        FatoExecucaoCarga.objects.create(
            run_id=uuid.uuid4(), fonte="etl", tabela="materiais",
            status="FAILED", iniciado_em=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/monitoring/execucoes/?status=SUCCESS")
        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            assert item["status"] == "SUCCESS"

    def test_filtro_status_invalido_retorna_400(self, api_client):
        # CTI-06
        response = api_client.get("/api/monitoring/execucoes/?status=INVALIDO")
        assert response.status_code == 400

    def test_filtro_por_tabela(self, api_client, db):
        # CTI-07
        FatoExecucaoCarga.objects.create(
            run_id=uuid.uuid4(), fonte="etl", tabela="projetos",
            status="SUCCESS", iniciado_em=datetime.now(tz=timezone.utc),
        )
        FatoExecucaoCarga.objects.create(
            run_id=uuid.uuid4(), fonte="etl", tabela="materiais",
            status="SUCCESS", iniciado_em=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/monitoring/execucoes/?tabela=projetos")
        assert response.status_code == 200
        for item in response.data:
            assert item["tabela"] == "projetos"

    def test_data_inicio_invalida_retorna_400(self, api_client):
        # CTI-08
        response = api_client.get(
            "/api/monitoring/execucoes/?data_inicio=nao-eh-data"
        )
        assert response.status_code == 400
