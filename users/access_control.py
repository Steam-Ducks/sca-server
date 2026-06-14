"""Centralized access control rules for profile-based authorization."""

# Maps each profile to the set of tables it can access.
# None means unrestricted (all tables allowed).
PROFILE_TABLES_ACCESS: dict[str, set[str] | None] = {
    "super_admin": None,
    "financeiro": {"programas", "projetos", "tarefas_projeto", "tempo_tarefas"},
    "compras": {
        "fornecedores",
        "pedidos_compra",
        "solicitacoes_compra",
        "compras_projeto",
    },
    "almoxarifado": {"materiais", "empenho_materiais", "estoque_materiais_projeto"},
    "projetos": {"projetos", "tarefas_projeto", "tempo_tarefas"},
}
