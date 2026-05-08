import logging
import time as _time
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

logger = logging.getLogger(__name__)

_SERVER_START = _time.time()

_GOLD_STALENESS_HOURS = 24
_SILVER_STALENESS_HOURS = 48


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


@api_view(["GET"])
def status_view(request):
    services = _check_services()
    processes = _get_recent_processes()
    last_updates = _get_last_updates()
    alerts = _get_alerts()
    integrity = _check_data_integrity()
    db_stats = _get_db_stats()

    overall = "ok"
    if any(s.get("status") == "error" for s in services.values()):
        overall = "degraded"
    elif alerts or integrity.get("inconsistencies"):
        overall = "warning"

    return Response(
        {
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": "development" if settings.DEBUG else "production",
            "uptime_seconds": round(_time.time() - _SERVER_START),
            "services": services,
            "processes": processes,
            "last_updates": last_updates,
            "alerts": alerts,
            "data_integrity": integrity,
            "db_stats": db_stats,
        }
    )


def _check_services():
    services = {}

    t0 = _time.time()
    try:
        connection.ensure_connection()
        services["database"] = {
            "status": "ok",
            "response_time_ms": round((_time.time() - t0) * 1000),
        }
    except Exception as e:
        services["database"] = {"status": "error", "error": str(e)}

    return services


def _get_recent_processes():
    from sca_data.models import AuditExecutionLog

    try:
        logs = AuditExecutionLog.objects.order_by("-started_at")[:20]
        return [
            {
                "run_id": str(log.run_id),
                "operation": log.operation,
                "status": log.status,
                "table": (
                    f"{log.table_schema}.{log.table_name}"
                    if log.table_schema
                    else log.table_name
                ),
                "affected_rows": log.affected_rows,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finalized_at": (
                    log.finalized_at.isoformat() if log.finalized_at else None
                ),
                "duration_seconds": (
                    round(log.operation_duration / 1000, 1)
                    if log.operation_duration
                    else None
                ),
            }
            for log in logs
        ]
    except Exception as e:
        return [{"error": str(e)}]


def _get_last_updates():
    from sca_data.models import (
        GoldCosts,
        GoldIndicadoresMateriais,
        SilverFornecedor,
        SilverMaterial,
        SilverPedidoCompra,
        SilverPrograma,
        SilverProjeto,
        SilverSolicitacaoCompra,
        SilverTarefaProjeto,
        SilverTempoTarefa,
    )

    entries = {
        "silver_programas": (SilverPrograma, "silver_ingested_at"),
        "silver_materiais": (SilverMaterial, "silver_ingested_at"),
        "silver_fornecedores": (SilverFornecedor, "silver_ingested_at"),
        "silver_projetos": (SilverProjeto, "silver_ingested_at"),
        "silver_tarefas": (SilverTarefaProjeto, "silver_ingested_at"),
        "silver_tempos": (SilverTempoTarefa, "silver_ingested_at"),
        "silver_solicitacoes": (SilverSolicitacaoCompra, "silver_ingested_at"),
        "silver_pedidos": (SilverPedidoCompra, "silver_ingested_at"),
        "gold_indicadores_materiais": (GoldIndicadoresMateriais, "gold_updated_at"),
        "gold_costs": (GoldCosts, "gold_updated_at"),
    }

    updates = {}
    for key, (model, field) in entries.items():
        try:
            obj = model.objects.latest(field)
            val = getattr(obj, field)
            updates[key] = val.isoformat() if val else None
        except Exception:
            updates[key] = None

    return updates


def _get_alerts():
    from sca_data.models import (
        AuditExecutionLog,
        GoldCosts,
        GoldIndicadoresMateriais,
        SilverFornecedor,
        SilverMaterial,
        SilverPedidoCompra,
        SilverPrograma,
        SilverProjeto,
        SilverSolicitacaoCompra,
        SilverTarefaProjeto,
        SilverTempoTarefa,
    )

    alerts = []
    now = datetime.now(timezone.utc)

    try:
        failed = AuditExecutionLog.objects.filter(status="failed").order_by(
            "-started_at"
        )[:10]
        for log in failed:
            alerts.append(
                {
                    "level": "error",
                    "source": "etl_pipeline",
                    "operation": log.operation,
                    "table": (
                        f"{log.table_schema}.{log.table_name}"
                        if log.table_schema
                        else log.table_name
                    ),
                    "timestamp": (
                        log.started_at.isoformat() if log.started_at else None
                    ),
                    "run_id": str(log.run_id),
                    "message": None,
                }
            )
    except Exception:
        pass

    gold_tables = {
        "gold_indicadores_materiais": (GoldIndicadoresMateriais, "gold_updated_at"),
        "gold_costs": (GoldCosts, "gold_updated_at"),
    }
    for key, (model, field) in gold_tables.items():
        try:
            obj = model.objects.latest(field)
            val = getattr(obj, field)
            if val and (now - val) > timedelta(hours=_GOLD_STALENESS_HOURS):
                hours_ago = round((now - val).total_seconds() / 3600)
                alerts.append(
                    {
                        "level": "warning",
                        "source": "data_staleness",
                        "operation": "etl_gold",
                        "table": key,
                        "timestamp": val.isoformat(),
                        "run_id": None,
                        "message": f"Sem atualização há {hours_ago}h (limite: {_GOLD_STALENESS_HOURS}h)",
                    }
                )
        except Exception:
            pass

    silver_tables = {
        "silver_programas": (SilverPrograma, "silver_ingested_at"),
        "silver_materiais": (SilverMaterial, "silver_ingested_at"),
        "silver_fornecedores": (SilverFornecedor, "silver_ingested_at"),
        "silver_projetos": (SilverProjeto, "silver_ingested_at"),
        "silver_tarefas": (SilverTarefaProjeto, "silver_ingested_at"),
        "silver_tempos": (SilverTempoTarefa, "silver_ingested_at"),
        "silver_solicitacoes": (SilverSolicitacaoCompra, "silver_ingested_at"),
        "silver_pedidos": (SilverPedidoCompra, "silver_ingested_at"),
    }
    for key, (model, field) in silver_tables.items():
        try:
            obj = model.objects.latest(field)
            val = getattr(obj, field)
            if val and (now - val) > timedelta(hours=_SILVER_STALENESS_HOURS):
                hours_ago = round((now - val).total_seconds() / 3600)
                alerts.append(
                    {
                        "level": "warning",
                        "source": "data_staleness",
                        "operation": "etl_silver",
                        "table": key,
                        "timestamp": val.isoformat(),
                        "run_id": None,
                        "message": f"Sem atualização há {hours_ago}h (limite: {_SILVER_STALENESS_HOURS}h)",
                    }
                )
        except Exception:
            pass

    return alerts


def _check_data_integrity():
    from sca_data.models import (
        SilverMaterial,
        SilverPrograma,
        SilverProjeto,
        SilverTarefaProjeto,
        SilverTempoTarefa,
    )

    issues = []
    counts = {}

    try:
        val = SilverTarefaProjeto.objects.filter(projeto__isnull=True).count()
        counts["tarefas_sem_projeto"] = val
        if val:
            issues.append(f"{val} tarefas sem projeto associado")

        val = SilverTempoTarefa.objects.filter(tarefa__isnull=True).count()
        counts["tempos_sem_tarefa"] = val
        if val:
            issues.append(f"{val} tempos sem tarefa associada")

        val = SilverTempoTarefa.objects.filter(horas_trabalhadas__isnull=True).count()
        counts["tempos_sem_horas"] = val
        if val:
            issues.append(f"{val} registros de tempo sem horas trabalhadas")

        val = SilverTempoTarefa.objects.filter(horas_trabalhadas__lt=0).count()
        counts["tempos_horas_negativas"] = val
        if val:
            issues.append(f"{val} registros com horas trabalhadas negativas")

        val = SilverProjeto.objects.filter(programa__isnull=True).count()
        counts["projetos_sem_programa"] = val
        if val:
            issues.append(f"{val} projetos sem programa associado")

        counts["total_programas"] = SilverPrograma.objects.count()
        counts["total_projetos"] = SilverProjeto.objects.count()
        counts["total_materiais"] = SilverMaterial.objects.count()
        counts["total_tarefas"] = SilverTarefaProjeto.objects.count()

    except Exception as e:
        issues.append(f"Erro na verificação: {str(e)}")

    return {
        "status": "ok" if not issues else "issues_found",
        "inconsistencies": issues,
        "counts": counts,
    }


def _get_db_stats():
    stats: dict = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    count(*)                                              AS total,
                    count(*) FILTER (WHERE state = 'active')             AS active,
                    count(*) FILTER (WHERE state = 'idle')               AS idle,
                    count(*) FILTER (WHERE wait_event_type = 'Lock')     AS waiting_lock
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)
            row = cursor.fetchone()
            stats["connections"] = {
                "total": row[0],
                "active": row[1],
                "idle": row[2],
                "waiting_lock": row[3],
            }
    except Exception as e:
        stats["connections"] = {"error": str(e)}

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                    pg_total_relation_size(schemaname||'.'||tablename)                 AS total_bytes,
                    n_live_tup                                                         AS row_estimate
                FROM pg_stat_user_tables
                WHERE schemaname IN ('silver', 'gold', 'public')
                ORDER BY total_bytes DESC
                LIMIT 15
            """)
            cols = [d[0] for d in cursor.description]
            stats["table_sizes"] = [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception:
        stats["table_sizes"] = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    LEFT(query, 120)                       AS query_snippet,
                    calls,
                    round(total_exec_time::numeric, 0)     AS total_ms,
                    round(mean_exec_time::numeric, 0)      AS mean_ms,
                    round(max_exec_time::numeric, 0)       AS max_ms,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > 300
                  AND query NOT LIKE '%pg_stat%'
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """)
            cols = [d[0] for d in cursor.description]
            stats["slow_queries"] = [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception:
        stats["slow_queries"] = []

    return stats
