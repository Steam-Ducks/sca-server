import pytest
from django.urls import resolve, reverse


class TestImportUrls:
    @pytest.mark.parametrize(
        "url,name",
        [
            ("/api/import/programas/", "import-programas"),
            ("/api/import/projetos/", "import-projetos"),
            ("/api/import/materiais/", "import-materiais"),
            ("/api/import/empenho-materiais/", "import-empenho-materiais"),
            (
                "/api/import/estoque-materiais-projeto/",
                "import-estoque-materiais-projeto",
            ),
            ("/api/import/fornecedores/", "import-fornecedores"),
            ("/api/import/pedidos-compra/", "import-pedidos-compra"),
            ("/api/import/solicitacoes-compra/", "import-solicitacoes-compra"),
            ("/api/import/compras-projeto/", "import-compras-projeto"),
            ("/api/import/tarefas-projeto/", "import-tarefas-projeto"),
            ("/api/import/tempo-tarefas/", "import-tempo-tarefas"),
        ],
    )
    def test_url_resolves(self, url, name):
        resolver = resolve(url)
        assert resolver.view_name == name

    @pytest.mark.parametrize(
        "name,url",
        [
            ("import-programas", "/api/import/programas/"),
            ("import-projetos", "/api/import/projetos/"),
            ("import-materiais", "/api/import/materiais/"),
            ("import-empenho-materiais", "/api/import/empenho-materiais/"),
            (
                "import-estoque-materiais-projeto",
                "/api/import/estoque-materiais-projeto/",
            ),
            ("import-fornecedores", "/api/import/fornecedores/"),
            ("import-pedidos-compra", "/api/import/pedidos-compra/"),
            ("import-solicitacoes-compra", "/api/import/solicitacoes-compra/"),
            ("import-compras-projeto", "/api/import/compras-projeto/"),
            ("import-tarefas-projeto", "/api/import/tarefas-projeto/"),
            ("import-tempo-tarefas", "/api/import/tempo-tarefas/"),
        ],
    )
    def test_url_reverse(self, name, url):
        assert reverse(name) == url
