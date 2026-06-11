"""
Conjunto de integração: Imports (CSV Upload)

Funções do conjunto:
    CSVUploadView (base)            — valida arquivo, permissão, CSV
    ProgramasUploadView  POST /api/import/programas/
    ProjetosUploadView   POST /api/import/projetos/
    MateriaisUploadView  POST /api/import/materiais/
    ... (11 endpoints no total, todos POST com upload de arquivo CSV)

NOTA: Os testes CTI-01/02/03 cobrem o comportamento de borda do CSVUploadView
(sem arquivo, arquivo inválido, arquivo CSV válido) usando ProgramasUploadView
como representante. Os demais endpoints têm comportamento idêntico via herança.

CTI-01 ao CTI-05
"""

import io
import os
import pytest

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]

PROGRAMAS_URL = "/api/import/programas/"


def csv_file(content: str, filename: str = "test.csv"):
    f = io.BytesIO(content.encode("utf-8"))
    f.name = filename
    return f


class TestCSVUploadIntegration:
    """
    CTI-01 ao CTI-05
    Conjunto: CSVUploadView → ProgramasUploadView como representante.

    Carga: apenas arquivos CSV em memória — sem inserção no banco ORM.
    """

    def test_sem_arquivo_retorna_400(self, api_client):
        # CTI-01 (mínimo): POST sem arquivo → 400 com mensagem de erro
        response = api_client.post(PROGRAMAS_URL, data={}, format="multipart")
        assert response.status_code == 400
        assert "error" in response.data

    def test_arquivo_nao_csv_retorna_400(self, api_client):
        # CTI-02 (mínimo): arquivo .txt → 400 (somente .csv aceito)
        f = io.BytesIO(b"conteudo qualquer")
        f.name = "dados.txt"
        response = api_client.post(PROGRAMAS_URL, data={"file": f}, format="multipart")
        assert response.status_code == 400
        assert "error" in response.data

    def test_csv_com_colunas_erradas_retorna_400(self, api_client):
        # CTI-03 (mínimo): CSV com colunas incorretas → 400 de validação
        csv_errado = csv_file("coluna_errada,outra_errada\n1,2\n")
        response = api_client.post(
            PROGRAMAS_URL, data={"file": csv_errado}, format="multipart"
        )
        assert response.status_code == 400

    def test_csv_valido_retorna_200_ou_201(self, api_client):
        # CTI-04 (mínimo): CSV com colunas corretas → 200/201
        csv_valido = csv_file(
            "id,codigo_programa,nome_programa,gerente_programa,gerente_tecnico,data_inicio,data_fim_prevista,status\n"
            "1,PROG-001,Programa Teste,Gerente Teste,Técnico,2024-01-01,2025-12-31,Em andamento\n"
        )
        response = api_client.post(
            PROGRAMAS_URL, data={"file": csv_valido}, format="multipart"
        )
        assert response.status_code in (200, 201)

    def test_todos_endpoints_respondem_ao_post(self, api_client):
        # CTI-05 (adicional): todos os 11 endpoints existem (não retornam 404)
        endpoints = [
            "/api/import/programas/",
            "/api/import/projetos/",
            "/api/import/materiais/",
            "/api/import/empenho-materiais/",
            "/api/import/estoque-materiais-projeto/",
            "/api/import/fornecedores/",
            "/api/import/pedidos-compra/",
            "/api/import/solicitacoes-compra/",
            "/api/import/compras-projeto/",
            "/api/import/tarefas-projeto/",
            "/api/import/tempo-tarefas/",
        ]
        for url in endpoints:
            response = api_client.post(url, data={}, format="multipart")
            assert response.status_code != 404, f"Rota não encontrada: {url}"
