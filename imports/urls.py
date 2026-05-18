from django.urls import path

from imports.views import (
    ComprasProjetoUploadView,
    EmpenhoMateriaisUploadView,
    EstoqueMateriaisProjetoUploadView,
    FornecedoresUploadView,
    MateriaisUploadView,
    PedidosCompraUploadView,
    ProgramasUploadView,
    ProjetosUploadView,
    SolicitacoesCompraUploadView,
    TarefasProjetoUploadView,
    TempoTarefasUploadView,
)

urlpatterns = [
    path("import/programas/", ProgramasUploadView.as_view(), name="import-programas"),
    path("import/projetos/", ProjetosUploadView.as_view(), name="import-projetos"),
    path("import/materiais/", MateriaisUploadView.as_view(), name="import-materiais"),
    path("import/empenho-materiais/", EmpenhoMateriaisUploadView.as_view(), name="import-empenho-materiais"),
    path("import/estoque-materiais-projeto/", EstoqueMateriaisProjetoUploadView.as_view(), name="import-estoque-materiais-projeto"),
    path("import/fornecedores/", FornecedoresUploadView.as_view(), name="import-fornecedores"),
    path("import/pedidos-compra/", PedidosCompraUploadView.as_view(), name="import-pedidos-compra"),
    path("import/solicitacoes-compra/", SolicitacoesCompraUploadView.as_view(), name="import-solicitacoes-compra"),
    path("import/compras-projeto/", ComprasProjetoUploadView.as_view(), name="import-compras-projeto"),
    path("import/tarefas-projeto/", TarefasProjetoUploadView.as_view(), name="import-tarefas-projeto"),
    path("import/tempo-tarefas/", TempoTarefasUploadView.as_view(), name="import-tempo-tarefas"),
]
