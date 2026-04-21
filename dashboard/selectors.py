# dashboard/selectors.py
from django.db import connection


def build_filters(params):
    """
    Builds WHERE clauses and values dict from query params.

    Accepted filters:
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program numeric ID
        project    — project numeric ID
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
    """
    materials_where, hours_where, projects_where, values = build_filters(params)

    sql_materials = f"""
        SELECT COALESCE(SUM(pc.valor_total), 0) AS materials_cost
        FROM silver.pedidos_compra pc
        LEFT JOIN silver.solicitacoes_compra sc ON sc.id = pc.solicitacao_id
        LEFT JOIN silver.projetos             p  ON p.id  = sc.projeto_id
        LEFT JOIN silver.programas            prog ON prog.id = p.programa_id
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
        "total_materials_cost":    round(materials_cost, 2),
        "total_hours_cost":        round(hours_cost, 2),
        "total_projects":          total_projects,
        "total_programs":          total_programs,
    }
