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


def _run_pipeline(engine):
    logging.info("=== Starting ETL Silver → Gold ===")
    _run_materials_indicators(engine)
    logging.info("=== ETL Gold completed ===")


if __name__ == "__main__":
    _run_pipeline(ENGINE)
