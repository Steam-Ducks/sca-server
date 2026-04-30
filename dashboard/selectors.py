# dashboard/selectors.py
from django.db import connection
from django.db.models import Count, ExpressionWrapper, F, FloatField, Q, Sum
from django.db.models.functions import Coalesce

from sca_data.models import SilverProjeto


# ── KPI Cards ─────────────────────────────────────────────────────────────────


def build_filters(params):
    """
    Builds WHERE clauses and values dict from query params.

    Accepted filters (all English, all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (e.g. "MANSUP", "MAX 1.2 AC")
        project    — project name (e.g. "Conversor DC-DC Isolado")
        status     — project status (e.g. "Em andamento", "Concluído")
    """
    materials_where = []
    hours_where = []
    projects_where = []
    values = {}

    if params.get("start_date"):
        materials_where.append("pc.data_pedido >= %(start_date)s")
        hours_where.append("tt.data >= %(start_date)s")
        values["start_date"] = params["start_date"]

    if params.get("end_date"):
        materials_where.append("pc.data_pedido <= %(end_date)s")
        hours_where.append("tt.data <= %(end_date)s")
        values["end_date"] = params["end_date"]

    if params.get("program"):
        materials_where.append("prog.codigo_programa = %(program)s")
        hours_where.append("prog.codigo_programa = %(program)s")
        projects_where.append("prog.codigo_programa = %(program)s")
        values["program"] = params["program"]

    if params.get("project"):
        materials_where.append("p.nome_projeto = %(project)s")
        hours_where.append("p.nome_projeto = %(project)s")
        projects_where.append("p.nome_projeto = %(project)s")
        values["project"] = params["project"]

    if params.get("status"):
        materials_where.append("p.status = %(status)s")
        hours_where.append("p.status = %(status)s")
        projects_where.append("p.status = %(status)s")
        values["status"] = params["status"]

    def _join(clauses):
        return ("WHERE " + " AND ".join(clauses)) if clauses else ""

    return _join(materials_where), _join(hours_where), _join(projects_where), values


def get_dashboard_kpis(params):
    """
    Executes SQL queries for dashboard indicators and returns a dict
    with the 5 consolidated KPIs.

    Materials cost source: compras_projeto.valor_alocado
    (consistent with get_program_summary and get_cost_composition)
    """
    materials_where, hours_where, projects_where, values = build_filters(params)

    # FIX: use compras_projeto.valor_alocado (same source as ORM-based selectors)
    sql_materials = f"""
        SELECT COALESCE(SUM(cp.valor_alocado), 0) AS materials_cost
        FROM silver.compras_projeto cp
        JOIN silver.projetos   p    ON p.id    = cp.projeto_id
        LEFT JOIN silver.programas prog ON prog.id = p.programa_id
        LEFT JOIN silver.pedidos_compra pc ON pc.id = cp.pedido_compra_id
        {materials_where}
    """

    sql_hours = f"""
        SELECT COALESCE(SUM(tt.horas_trabalhadas * p.custo_hora), 0) AS hours_cost
        FROM silver.tempo_tarefas   tt
        JOIN silver.tarefas_projeto tp   ON tp.id  = tt.tarefa_id
        JOIN silver.projetos        p    ON p.id   = tp.projeto_id
        LEFT JOIN silver.programas  prog ON prog.id = p.programa_id
        {hours_where}
    """

    sql_projects = f"""
        SELECT COUNT(DISTINCT p.id) AS total_projects
        FROM silver.projetos   p
        LEFT JOIN silver.programas prog ON prog.id = p.programa_id
        {projects_where}
    """

    sql_programs = f"""
        SELECT COUNT(DISTINCT prog.id) AS total_programs
        FROM silver.programas prog
        JOIN silver.projetos  p ON p.programa_id = prog.id
        {projects_where}
    """

    with connection.cursor() as cursor:
        cursor.execute(sql_materials, values)
        materials_cost = float(cursor.fetchone()[0])

        cursor.execute(sql_hours, values)
        hours_cost = float(cursor.fetchone()[0])

        cursor.execute(sql_projects, values)
        total_projects = cursor.fetchone()[0]

        cursor.execute(sql_programs, values)
        total_programs = cursor.fetchone()[0]

    return {
        "total_consolidated_cost": round(materials_cost + hours_cost, 2),
        "total_materials_cost": round(materials_cost, 2),
        "total_hours_cost": round(hours_cost, 2),
        "total_projects": total_projects,
        "total_programs": total_programs,
    }


# ── Main Dashboard Charts ─────────────────────────────────────────────────────


def get_projects_by_period(start_date=None, end_date=None):
    """
    Filter projects by a given date range using silver_ingested_at.
    """
    date_filter = Q()

    if start_date:
        date_filter &= Q(silver_ingested_at__date__gte=start_date)

    if end_date:
        date_filter &= Q(silver_ingested_at__date__lte=end_date)

    return SilverProjeto.objects.filter(date_filter)


def _build_cost_filters(params):
    """
    Shared helper: builds Q filters for materials and hours from params dict.

    Accepted filters (all English):
        start_date, end_date, program, project, status
    """
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    compras_filter = Q()
    tempo_filter = Q()

    if start_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__gte=start_date
        )
        tempo_filter &= Q(tarefas__tempos__data__gte=start_date)

    if end_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__lte=end_date
        )
        tempo_filter &= Q(tarefas__tempos__data__lte=end_date)

    return compras_filter, tempo_filter


def get_program_summary(params):
    """
    Returns aggregated cost data grouped by program.

    Accepted params (all English, all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (case-insensitive)
        project    — project name (case-insensitive)
        status     — project status (case-insensitive)

    Returns a list of dicts sorted by custo_materiais descending.
    """
    compras_filter, tempo_filter = _build_cost_filters(params)

    qs = SilverProjeto.objects.select_related("programa")

    if params.get("program"):
        qs = qs.filter(programa__nome_programa__iexact=params["program"])

    if params.get("project"):
        qs = qs.filter(nome_projeto__iexact=params["project"])

    if params.get("status"):
        qs = qs.filter(status__iexact=params["status"])

    rows = (
        qs.values("programa__nome_programa")
        .annotate(
            qtd_projetos=Count("id", distinct=True),
            custo_materiais=Coalesce(
                Sum("silvercomprasprojeto__valor_alocado", filter=compras_filter),
                0.0,
                output_field=FloatField(),
            ),
            custo_horas=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                        output_field=FloatField(),
                    ),
                    filter=tempo_filter,
                ),
                0.0,
                output_field=FloatField(),
            ),
        )
        .order_by("-custo_materiais")
    )

    return [
        {
            "programa": row["programa__nome_programa"] or "Sem Programa",
            "qtd_projetos": row["qtd_projetos"],
            "custo_materiais": round(row["custo_materiais"], 2),
            "custo_horas": round(row["custo_horas"], 2),
            "custo_total": round(row["custo_materiais"] + row["custo_horas"], 2),
        }
        for row in rows
    ]


def get_cost_composition(params):
    """
    Returns the overall cost composition split between materials and hours.

    Accepted params (all English, all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (case-insensitive)
        project    — project name (case-insensitive)
        status     — project status (case-insensitive)

    Returns a dict with absolute values and percentage breakdown.
    """
    compras_filter, tempo_filter = _build_cost_filters(params)

    qs = SilverProjeto.objects.select_related("programa")

    if params.get("program"):
        qs = qs.filter(programa__nome_programa__iexact=params["program"])
    if params.get("project"):
        qs = qs.filter(nome_projeto__iexact=params["project"])
    if params.get("status"):
        qs = qs.filter(status__iexact=params["status"])

    result = qs.aggregate(
        custo_materiais=Coalesce(
            Sum("silvercomprasprojeto__valor_alocado", filter=compras_filter),
            0.0,
            output_field=FloatField(),
        ),
        custo_horas=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                    output_field=FloatField(),
                ),
                filter=tempo_filter,
            ),
            0.0,
            output_field=FloatField(),
        ),
    )

    custo_materiais = round(result["custo_materiais"], 2)
    custo_horas = round(result["custo_horas"], 2)
    custo_total = round(custo_materiais + custo_horas, 2)

    if custo_total > 0:
        pct_materiais = round(custo_materiais / custo_total * 100, 1)
        pct_horas = round(custo_horas / custo_total * 100, 1)
    else:
        pct_materiais = 0.0
        pct_horas = 0.0

    return {
        "custo_materiais": custo_materiais,
        "custo_horas": custo_horas,
        "custo_total": custo_total,
        "pct_materiais": pct_materiais,
        "pct_horas": pct_horas,
    }


# ── Top 10 Projects by Total Cost ─────────────────────────────────────────────


def get_top_projects_by_cost(params):
    """
    Returns the top 10 projects ranked by total consolidated cost.

    Uses correlated subqueries to avoid cartesian product between
    compras_projeto and tempo_tarefas joins.

    Accepted params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (case-insensitive)
        project    — project name (case-insensitive)
        status     — project status (case-insensitive)

    Returns a list of dicts: [{"project_name": str, "total_cost": float}]
    """
    values = {}
    outer_where = []
    mat_sub_and = []
    hrs_sub_and = []

    if params.get("start_date"):
        mat_sub_and.append("pc.data_pedido >= %(start_date)s")
        hrs_sub_and.append("tt.data >= %(start_date)s")
        values["start_date"] = params["start_date"]

    if params.get("end_date"):
        mat_sub_and.append("pc.data_pedido <= %(end_date)s")
        hrs_sub_and.append("tt.data <= %(end_date)s")
        values["end_date"] = params["end_date"]

    if params.get("program"):
        outer_where.append("prog.nome_programa ILIKE %(program)s")
        values["program"] = params["program"]

    if params.get("project"):
        outer_where.append("p.nome_projeto ILIKE %(project)s")
        values["project"] = params["project"]

    if params.get("status"):
        outer_where.append("p.status ILIKE %(status)s")
        values["status"] = params["status"]

    def _and(clauses):
        return ("AND " + " AND ".join(clauses)) if clauses else ""

    def _where(clauses):
        return ("WHERE " + " AND ".join(clauses)) if clauses else ""

    sql = f"""
        SELECT
            p.nome_projeto,
            COALESCE((
                SELECT SUM(cp.valor_alocado)
                FROM silver.compras_projeto cp
                JOIN silver.pedidos_compra pc ON pc.id = cp.pedido_compra_id
                WHERE cp.projeto_id = p.id
                  {_and(mat_sub_and)}
            ), 0)
            +
            COALESCE((
                SELECT SUM(tt.horas_trabalhadas) * p.custo_hora
                FROM silver.tempo_tarefas tt
                JOIN silver.tarefas_projeto tp ON tp.id = tt.tarefa_id
                WHERE tp.projeto_id = p.id
                  {_and(hrs_sub_and)}
            ), 0) AS total_cost
        FROM silver.projetos p
        LEFT JOIN silver.programas prog ON p.programa_id = prog.id
        {_where(outer_where)}
        ORDER BY total_cost DESC
        LIMIT 10
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, values)
        rows = cursor.fetchall()

    return [
        {
            "project_name": row[0],
            "total_cost": round(float(row[1]), 2),
        }
        for row in rows
    ]
