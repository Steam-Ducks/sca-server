import logging

from sqlalchemy import text

from sca_data.db.connection import getOrCreate

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

ENGINE = getOrCreate()

_SQL_MATERIALS_INDICATORS = """
    TRUNCATE TABLE gold."indicators_materiais";

    INSERT INTO gold."indicators_materiais"
        (categoria, custo_total, total_itens, custo_medio, gold_updated_at)
    SELECT
        m.categoria,
        SUM(pc.valor_total)                                  AS custo_total,
        COUNT(emp.id) FILTER (WHERE m.status = 'Ativo')     AS total_itens,
        AVG(pc.valor_total)                                  AS custo_medio,
        NOW()                                                AS gold_updated_at
    FROM silver.materiais m
    LEFT JOIN silver.estoque_materiais_projeto emp ON emp.material_id = m.id
    LEFT JOIN silver.solicitacoes_compra       sc  ON sc.material_id  = m.id
    LEFT JOIN silver.pedidos_compra            pc  ON pc.solicitacao_id = sc.id
    GROUP BY m.categoria;
"""

_SQL_COSTS = """
    TRUNCATE TABLE gold.costs;

    INSERT INTO gold.costs
        (data, nome_programa, gerente_programa, nome_projeto, responsavel_projeto, custo, gold_updated_at)
    SELECT
        pc.data_pedido      AS data,
        po.nome_programa,
        po.gerente_programa,
        p.nome_projeto,
        p.responsavel       AS responsavel_projeto,
        SUM(pc.valor_total) AS custo,
        NOW()               AS gold_updated_at
    FROM silver.compras_projeto cp
    LEFT JOIN silver.pedidos_compra pc ON pc.id = cp.pedido_compra_id
    LEFT JOIN silver.projetos       p  ON cp.projeto_id  = p.id
    LEFT JOIN silver.programas      po ON p.programa_id  = po.id
    GROUP BY 1, 2, 3, 4, 5
    ORDER BY 1;
"""

_SQL_BUDGET_SNAPSHOT = """
    TRUNCATE TABLE gold."budget_snapshot";

    INSERT INTO gold."budget_snapshot"
        (projeto_id, nome_projeto, nome_programa, gerente_programa,
         responsavel_projeto, budget, custo_materiais, custo_horas,
         custo_real, desvio_percent, saude_financeira, projecao_estouro,
         periodo, status, gold_updated_at)
    SELECT
        p.id,
        p.nome_projeto,
        po.nome_programa,
        po.gerente_programa,
        p.responsavel                                                                AS responsavel_projeto,
        ROUND(CAST(
            COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0)
        AS NUMERIC), 2)                                                              AS budget,
        ROUND(CAST(COALESCE(real_mat.custo_materiais, 0) AS NUMERIC), 2)            AS custo_materiais,
        ROUND(CAST(COALESCE(real_h.custo_horas, 0) AS NUMERIC), 2)                 AS custo_horas,
        ROUND(CAST(
            COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0)
        AS NUMERIC), 2)                                                              AS custo_real,
        CASE
            WHEN (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0)) > 0
            THEN ROUND(CAST(
                (COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0))
                / (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0))
                * 100
            AS NUMERIC), 1)
            ELSE 0
        END                                                                          AS desvio_percent,
        CASE
            WHEN (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0)) > 0
                 AND ROUND(CAST(
                     (COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0))
                     / (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0))
                     * 100
                 AS NUMERIC), 1) >= 90
            THEN 'Crítico'
            WHEN (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0)) > 0
                 AND ROUND(CAST(
                     (COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0))
                     / (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0))
                     * 100
                 AS NUMERIC), 1) >= 70
            THEN 'Atenção'
            ELSE 'Saudável'
        END                                                                          AS saude_financeira,
        CASE
            WHEN (COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0))
               > (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0))
            THEN ROUND(CAST(
                (COALESCE(real_mat.custo_materiais, 0) + COALESCE(real_h.custo_horas, 0))
                - (COALESCE(est_mat.budget_materiais, 0) + COALESCE(est_h.budget_horas, 0))
            AS NUMERIC), 2)
            ELSE NULL
        END                                                                          AS projecao_estouro,
        TO_CHAR(p.data_inicio, 'YYYY-MM')                                           AS periodo,
        p.status,
        NOW()                                                                        AS gold_updated_at
    FROM silver.projetos p
    LEFT JOIN silver.programas po ON p.programa_id = po.id
    LEFT JOIN (
        SELECT sc.projeto_id,
               SUM(sc.quantidade * m.custo_estimado) AS budget_materiais
        FROM silver.solicitacoes_compra sc
        JOIN silver.materiais m ON m.id = sc.material_id
        GROUP BY sc.projeto_id
    ) est_mat ON est_mat.projeto_id = p.id
    LEFT JOIN (
        SELECT t.projeto_id,
               SUM(t.estimativa_horas * p2.custo_hora) AS budget_horas
        FROM silver.tarefas_projeto t
        JOIN silver.projetos p2 ON p2.id = t.projeto_id
        GROUP BY t.projeto_id
    ) est_h ON est_h.projeto_id = p.id
    LEFT JOIN (
        SELECT cp.projeto_id,
               SUM(cp.valor_alocado) AS custo_materiais
        FROM silver.compras_projeto cp
        GROUP BY cp.projeto_id
    ) real_mat ON real_mat.projeto_id = p.id
    LEFT JOIN (
        SELECT t.projeto_id,
               SUM(tt.horas_trabalhadas * p2.custo_hora) AS custo_horas
        FROM silver.tempo_tarefas tt
        JOIN silver.tarefas_projeto t ON t.id = tt.tarefa_id
        JOIN silver.projetos p2 ON p2.id = t.projeto_id
        GROUP BY t.projeto_id
    ) real_h ON real_h.projeto_id = p.id
    ORDER BY p.nome_projeto;
"""


def _run_materials_indicators(engine):
    try:
        logging.info("--- Processing: materials_indicators ---")
        with engine.connect() as conn:
            conn.execute(text(_SQL_MATERIALS_INDICATORS))
            conn.commit()
        logging.info("Table indicators_materiais wrote in schema 'gold'!")
    except Exception as e:
        logging.error(
            f"It was not possible to build 'materials_indicators'. Error: {e}"
        )


def _run_costs(engine):
    try:
        logging.info("--- Processing: costs ---")
        with engine.connect() as conn:
            conn.execute(text(_SQL_COSTS))
            conn.commit()
        logging.info("Table costs rote in schema 'gold'!")
    except Exception as e:
        logging.error(f"It was not possible to build costs. Error: {e}")


def _run_budget_snapshot(engine):
    try:
        logging.info("--- Processing: budget_snapshot ---")
        with engine.connect() as conn:
            conn.execute(text(_SQL_BUDGET_SNAPSHOT))
            conn.commit()
        logging.info("Table budget_snapshot wrote in schema 'gold'!")
    except Exception as e:
        logging.error(f"It was not possible to build budget_snapshot. Error: {e}")


def _run_pipeline(engine):
    logging.info("=== Starting ETL Silver → Gold ===")
    _run_materials_indicators(engine)
    _run_costs(engine)
    _run_budget_snapshot(engine)
    logging.info("=== ETL Gold completed ===")


if __name__ == "__main__":
    _run_pipeline(ENGINE)
