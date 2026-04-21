import datetime
import logging

import pandas as pd
from sqlalchemy import text

from sca_data.db.connection import getOrCreate

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

ENGINE = getOrCreate()


def _read_bronze(engine, tb_name: str) -> pd.DataFrame:
    df = pd.read_sql(f'SELECT * FROM bronze."{tb_name}"', engine)
    logging.info(f"[bronze] {tb_name}: {len(df)} linhas lidas.")
    return df


def _write_silver(df: pd.DataFrame, engine, tb_name: str):
    logging.info(f"Writing {tb_name} ...")

    df["silver_ingested_at"] = datetime.datetime.now()

    with engine.connect() as conn:
        conn.execute(text(f'TRUNCATE TABLE silver."{tb_name}" CASCADE'))
        conn.commit()

    df.to_sql(
        tb_name,
        engine,
        schema="silver",
        if_exists="append",
        index=False,
    )

    logging.info(f"Table {tb_name} wrote in schema 'silver'!")


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _to_int(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.apply(lambda x: int(x) if pd.notna(x) else pd.NA).astype("Int64")


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _to_str(series: pd.Series, max_len: int = None) -> pd.Series:
    _nulls = frozenset({"nan", "None", "<NA>", "none", ""})

    def _convert(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        if s in _nulls:
            return None
        return s[:max_len] if max_len else s

    # List comprehension + dtype=object guarantees Python None is preserved
    return pd.Series([_convert(v) for v in series], dtype=object)


def _transform_programas(engine):
    try:
        df = _read_bronze(engine, "programas")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "codigo_programa": _to_str(df["codigo_programa"], 100),
                "nome_programa": _to_str(df["nome_programa"], 100),
                "gerente_programa": _to_str(df["gerente_programa"], 100),
                "gerente_tecnico": _to_str(df["gerente_tecnico"], 100),
                "data_inicio": _to_date(df["data_inicio"]),
                "data_fim_prevista": _to_date(df["data_fim_prevista"]),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "programas")

    except Exception as e:
        logging.error(f"It was not possible to transform 'programas'. Error: {e}")


def _transform_materiais(engine):
    try:
        df = _read_bronze(engine, "materiais")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "codigo_material": _to_str(df["codigo_material"], 50),
                "descricao": _to_str(df["descricao"], 100),
                "categoria": _to_str(df["categoria"], 100),
                "fabricante": _to_str(df["fabricante"], 100),
                "custo_estimado": _to_float(df["custo_estimado"]),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "materiais")

    except Exception as e:
        logging.error(f"It was not possible to transform 'materiais'. Error: {e}")


def _transform_fornecedores(engine):
    try:
        df = _read_bronze(engine, "fornecedores")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "codigo_fornecedor": _to_str(df["codigo_fornecedor"], 50),
                "razao_social": _to_str(df["razao_social"], 100),
                "cidade": _to_str(df["cidade"], 100),
                "estado": _to_str(df["estado"], 2),
                "categoria": _to_str(df["categoria"], 100),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "fornecedores")

    except Exception as e:
        logging.error(f"It was not possible to transform 'fornecedores'. Error: {e}")


def _transform_projetos(engine):
    try:
        df = _read_bronze(engine, "projetos")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "codigo_projeto": _to_str(df["codigo_projeto"], 50),
                "nome_projeto": _to_str(df["nome_projeto"], 100),
                "programa_id": _to_int(df["programa_id"]),
                "responsavel": _to_str(df["responsavel"], 100),
                "custo_hora": _to_float(df["custo_hora"]),
                "data_inicio": _to_date(df["data_inicio"]),
                "data_fim_prevista": _to_date(df["data_fim_prevista"]),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "projetos")

    except Exception as e:
        logging.error(f"It was not possible to transform 'projetos'. Error: {e}")


def _transform_tarefas_projeto(engine):
    try:
        df = _read_bronze(engine, "tarefas_projeto")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "codigo_tarefa": _to_str(df["codigo_tarefa"], 50),
                "projeto_id": _to_int(df["projeto_id"]),
                "titulo": _to_str(df["titulo"], 100),
                "responsavel": _to_str(df["responsavel"], 100),
                "estimativa_horas": _to_int(df["estimativa_horas"]),
                "data_inicio": _to_date(df["data_inicio"]),
                "data_fim_prevista": _to_date(df["data_fim_prevista"]),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "tarefas_projeto")

    except Exception as e:
        logging.error(f"It was not possible to transform 'tarefas_projeto'. Error: {e}")


def _transform_tempo_tarefas(engine):
    try:
        df = _read_bronze(engine, "tempo_tarefas")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "tarefa_id": _to_int(df["tarefa_id"]),
                "usuario": _to_str(df["usuario"], 100),
                "data": _to_date(df["data"]),
                "horas_trabalhadas": _to_float(df["horas_trabalhadas"]),
            }
        )

        _write_silver(out, engine, "tempo_tarefas")

    except Exception as e:
        logging.error(f"It was not possible to transform 'tempo_tarefas'. Error: {e}")


def _transform_solicitacoes_compra(engine):
    try:
        df = _read_bronze(engine, "solicitacoes_compra")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "numero_solicitacao": _to_str(df["numero_solicitacao"], 50),
                "projeto_id": _to_int(df["projeto_id"]),
                "material_id": _to_int(df["material_id"]),
                "quantidade": _to_int(df["quantidade"]),
                "data_solicitacao": _to_date(df["data_solicitacao"]),
                "prioridade": _to_str(df["prioridade"], 50),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "solicitacoes_compra")

    except Exception as e:
        logging.error(
            f"It was not possible to transform 'solicitacoes_compra'. Error: {e}"
        )


def _transform_pedidos_compra(engine):
    try:
        df = _read_bronze(engine, "pedidos_compra")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "numero_pedido": _to_str(df["numero_pedido"], 50),
                "solicitacao_id": _to_int(df["solicitacao_id"]),
                "fornecedor_id": _to_int(df["fornecedor_id"]),
                "data_pedido": _to_date(df["data_pedido"]),
                "data_previsao_entrega": _to_date(df["data_previsao_entrega"]),
                "valor_total": _to_float(df["valor_total"]),
                "status": _to_str(df["status"], 50),
            }
        )

        _write_silver(out, engine, "pedidos_compra")

    except Exception as e:
        logging.error(f"It was not possible to transform 'pedidos_compra'. Error: {e}")


def _transform_compras_projeto(engine):
    try:
        df = _read_bronze(engine, "compras_projeto")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "pedido_compra_id": _to_int(df["pedido_compra_id"]),
                "projeto_id": _to_int(df["projeto_id"]),
                "valor_alocado": _to_float(df["valor_alocado"]),
            }
        )

        _write_silver(out, engine, "compras_projeto")

    except Exception as e:
        logging.error(f"It was not possible to transform 'compras_projeto'. Error: {e}")


def _transform_empenho_materiais(engine):
    try:
        df = _read_bronze(engine, "empenho_materiais")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "projeto_id": _to_int(df["projeto_id"]),
                "material_id": _to_int(df["material_id"]),
                "quantidade_empenhada": _to_int(df["quantidade_empenhada"]),
                "data_empenho": _to_date(df["data_empenho"]),
            }
        )

        _write_silver(out, engine, "empenho_materiais")

    except Exception as e:
        logging.error(
            f"It was not possible to transform 'empenho_materiais'. Error: {e}"
        )


def _transform_estoque_materiais_projeto(engine):
    try:
        df = _read_bronze(engine, "estoque_materiais_projeto")

        out = pd.DataFrame(
            {
                "id": _to_int(df["id"]),
                "projeto_id": _to_int(df["projeto_id"]),
                "material_id": _to_int(df["material_id"]),
                "quantidade": _to_int(df["quantidade"]),
                "localizacao": _to_str(df["localizacao"], 100),
            }
        )

        _write_silver(out, engine, "estoque_materiais_projeto")

    except Exception as e:
        logging.error(
            f"It was not possible to transform 'estoque_materiais_projeto'. Error: {e}"
        )


PIPELINE = [
    ("programas", _transform_programas),
    ("materiais", _transform_materiais),
    ("fornecedores", _transform_fornecedores),
    ("projetos", _transform_projetos),
    ("tarefas_projeto", _transform_tarefas_projeto),
    ("tempo_tarefas", _transform_tempo_tarefas),
    ("solicitacoes_compra", _transform_solicitacoes_compra),
    ("pedidos_compra", _transform_pedidos_compra),
    ("compras_projeto", _transform_compras_projeto),
    ("empenho_materiais", _transform_empenho_materiais),
    ("estoque_materiais_projeto", _transform_estoque_materiais_projeto),
]


def _run_pipeline(engine):
    logging.info("=== Iniciando ETL Bronze → Silver ===")

    for name, fn in PIPELINE:
        logging.info(f"--- Processando: {name} ---")
        fn(engine)

    logging.info("=== ETL concluído ===")


if __name__ == "__main__":
    _run_pipeline(ENGINE)
