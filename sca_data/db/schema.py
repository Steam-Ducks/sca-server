SILVER = "silver"


class Silver:
    """Fully-qualified table references for use in raw SQL (schema.table)."""

    PROJETOS = f"{SILVER}.projetos"
    PROGRAMAS = f"{SILVER}.programas"
    TAREFAS_PROJETO = f"{SILVER}.tarefas_projeto"
    TEMPO_TAREFAS = f"{SILVER}.tempo_tarefas"
    COMPRAS_PROJETO = f"{SILVER}.compras_projeto"
    PEDIDOS_COMPRA = f"{SILVER}.pedidos_compra"
    SOLICITACOES_COMPRA = f"{SILVER}.solicitacoes_compra"
    MATERIAIS = f"{SILVER}.materiais"
    ESTOQUE_MATERIAIS_PROJETO = f"{SILVER}.estoque_materiais_projeto"
