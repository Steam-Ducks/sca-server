"""
Conjunto de integração: Audit

Funções do conjunto:
    AuditExecutionLog (sca_data.models)    — tabela audit."execution_logs"
    AuditExecutionLogTableView (views.py)  — GET /api/audit/
    AuditExecutionLogSerializer            — serializa campos de log
    CanAccessAudit                         — super_admin acessa tudo

SITUAÇÃO: AuditExecutionLog tem managed = False.
A tabela audit."execution_logs" é criada pelo pipeline ETL, não pelas
migrations do Django. No ambiente de teste ela não existe.

CTI-01 e CTI-03: xfail — endpoint consulta tabela inexistente no teste.
CTI-02: passa — 403 é verificado antes de qualquer query ao banco.
CTI-04 e CTI-05: xfail — dependem da tabela existir com dados reais.

Quando a tabela for provisionada no ambiente de teste (via SQL no CI),
remova os xfail e atualize os campos conforme o modelo:
    run_id (UUID), operation, status, table_schema, table_name,
    affected_rows, started_at, finalized_at, operation_metadata.
"""

import uuid
import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient


_XFAIL_UNMANAGED = pytest.mark.xfail(
    reason=(
        "audit.execution_logs é managed=False — tabela não existe no banco de teste. "
        "Para ativar: provisionar a tabela via SQL no CI antes de rodar os testes."
    ),
    strict=False,
)


@pytest.mark.integration
@pytest.mark.django_db
class TestAuditAuthIntegration:
    """
    CTI-01 ao CTI-02
    Valida controle de acesso ao endpoint — não depende de dados na tabela.
    """

    @_XFAIL_UNMANAGED
    def test_retorna_200_para_super_admin(self, api_client):
        # CTI-01 — xfail: view consulta tabela não existente no teste
        response = api_client.get("/api/audit/")
        assert response.status_code == 200

    def test_retorna_403_sem_autenticacao(self):
        # CTI-02 — passa: 403 é verificado antes de qualquer query ao banco
        response = APIClient().get("/api/audit/")
        assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.django_db
class TestAuditDataIntegration:
    """
    CTI-03 ao CTI-05
    Dependem da tabela audit."execution_logs" existir no banco de teste.
    Todos marcados como xfail até o provisionamento da tabela no CI.

    Campos corretos do modelo AuditExecutionLog:
        run_id (UUID, obrigatório)
        operation (CharField, obrigatório)
        status (CharField, obrigatório)
        started_at (DateTimeField, obrigatório)
        table_schema (nullable), table_name (nullable)
        affected_rows (nullable), finalized_at (nullable)
        operation_metadata (JSONField, nullable)

    Filtros disponíveis na view:
        ?status=      ?operation=    ?periodo=YYYY-MM
        ?data_inicio= ?data_fim=     ?started_at_gte=  ?finalized_at_lte=
    """

    @_XFAIL_UNMANAGED
    def test_retorna_lista_vazia_com_tabela_existente(self, api_client):
        # CTI-03
        response = api_client.get("/api/audit/")
        assert response.status_code == 200
        assert isinstance(response.data, list)

    @_XFAIL_UNMANAGED
    def test_log_real_aparece_na_resposta(self, api_client, db):
        # CTI-04
        from sca_data.models import AuditExecutionLog

        AuditExecutionLog.objects.create(
            run_id=uuid.uuid4(),
            operation="INSERT",
            status="success",
            table_name="projetos",
            table_schema="silver",
            started_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/audit/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    @_XFAIL_UNMANAGED
    def test_filtro_por_status(self, api_client, db):
        # CTI-05 — filtro correto é ?status= (não ?tabela=)
        from sca_data.models import AuditExecutionLog

        AuditExecutionLog.objects.create(
            run_id=uuid.uuid4(),
            operation="INSERT",
            status="success",
            started_at=datetime.now(tz=timezone.utc),
        )
        AuditExecutionLog.objects.create(
            run_id=uuid.uuid4(),
            operation="UPDATE",
            status="failed",
            started_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/audit/?status=success")
        assert response.status_code == 200
        for item in response.data:
            assert item["status"] == "success"
