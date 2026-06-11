from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

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
from imports.schemas import REQUIRED_COLUMNS


@pytest.fixture
def factory(monkeypatch):
    from users import permissions as perm_mod

    monkeypatch.setattr(perm_mod, "_get_permissao", lambda u: "super_admin")
    base = APIRequestFactory()
    user = get_user_model()(username="_test", is_active=True)

    class _AuthFactory:
        def get(self, *args, **kwargs):
            req = base.get(*args, **kwargs)
            force_authenticate(req, user=user)
            return req

        def post(self, *args, **kwargs):
            req = base.post(*args, **kwargs)
            force_authenticate(req, user=user)
            return req

    return _AuthFactory()


def _csv_bytes(csv_type, rows=2):
    cols = sorted(REQUIRED_COLUMNS[csv_type])
    header = ",".join(cols)
    row = ",".join(["val"] * len(cols))
    return "\n".join([header] + [row] * rows).encode()


def _csv_file(csv_type, rows=2, name=None):
    content = _csv_bytes(csv_type, rows=rows)
    filename = name or f"{csv_type}.csv"
    return SimpleUploadedFile(filename, content, content_type="text/csv")


class TestCSVUploadValidation:
    """Base validation logic exercised through ProgramasUploadView."""

    def test_no_file_returns_400(self, factory):
        view = ProgramasUploadView.as_view()
        request = factory.post("/api/import/programas/", {}, format="multipart")
        response = view(request)
        assert response.status_code == 400
        assert "error" in response.data

    def test_non_csv_extension_returns_400(self, factory):
        view = ProgramasUploadView.as_view()
        f = SimpleUploadedFile("data.txt", b"some content", content_type="text/plain")
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        assert response.status_code == 400
        assert "error" in response.data

    def test_file_over_50mb_returns_400(self, factory):
        view = ProgramasUploadView.as_view()
        large_content = b"x" * (51 * 1024 * 1024)
        f = SimpleUploadedFile("big.csv", large_content, content_type="text/csv")
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        assert response.status_code == 400
        assert "MB" in response.data["error"]

    def test_wrong_csv_type_returns_400(self, factory):
        view = ProgramasUploadView.as_view()
        # Upload fornecedores CSV to the programas endpoint
        f = _csv_file("fornecedores", name="fornecedores.csv")
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        assert response.status_code == 400
        assert response.data["tipo_esperado"] == "programas"
        assert "colunas_ausentes" in response.data

    def test_missing_columns_are_listed(self, factory):
        view = ProgramasUploadView.as_view()
        f = SimpleUploadedFile(
            "programas.csv", b"id,nome\nval,val", content_type="text/csv"
        )
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        assert response.status_code == 400
        missing = response.data["colunas_ausentes"]
        assert isinstance(missing, list)
        assert len(missing) > 0

    def test_missing_columns_are_sorted(self, factory):
        view = ProgramasUploadView.as_view()
        f = SimpleUploadedFile(
            "programas.csv", b"id,nome\nval,val", content_type="text/csv"
        )
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        missing = response.data["colunas_ausentes"]
        assert missing == sorted(missing)

    def test_error_message_present_for_missing_columns(self, factory):
        view = ProgramasUploadView.as_view()
        f = SimpleUploadedFile(
            "programas.csv", b"id,nome\nval,val", content_type="text/csv"
        )
        request = factory.post(
            "/api/import/programas/", {"file": f}, format="multipart"
        )
        response = view(request)
        assert "error" in response.data


class TestCSVUploadSuccess:
    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_correct_upload_returns_200(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = ProgramasUploadView.as_view()
        request = factory.post(
            "/api/import/programas/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        response = view(request)
        assert response.status_code == 200

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_response_contains_run_id(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = ProgramasUploadView.as_view()
        request = factory.post(
            "/api/import/programas/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        response = view(request)
        assert "run_id" in response.data

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_response_contains_tabela_and_row_count(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = ProgramasUploadView.as_view()
        request = factory.post(
            "/api/import/programas/",
            {"file": _csv_file("programas", rows=5)},
            format="multipart",
        )
        response = view(request)
        assert response.data["tabela"] == "programas"
        assert response.data["linhas_recebidas"] == 5

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch(
        "sca_data.db.bronze.ingestion._create_table", side_effect=Exception("DB error")
    )
    def test_bronze_failure_returns_500(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = ProgramasUploadView.as_view()
        request = factory.post(
            "/api/import/programas/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        response = view(request)
        assert response.status_code == 500
        assert "error" in response.data

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    def test_silver_failure_still_returns_200(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        failing_silver_fn = MagicMock(side_effect=Exception("Silver error"))
        with patch(
            "sca_data.db.silver.ingestion_silver.PIPELINE",
            [("programas", failing_silver_fn)],
        ):
            with patch("sca_data.db.silver.ingestion_silver._ensure_schema"):
                view = ProgramasUploadView.as_view()
                request = factory.post(
                    "/api/import/programas/",
                    {"file": _csv_file("programas")},
                    format="multipart",
                )
                response = view(request)
        assert response.status_code == 200

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    def test_silver_fn_called_when_in_pipeline(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        silver_fn = MagicMock()
        with patch(
            "sca_data.db.silver.ingestion_silver.PIPELINE", [("programas", silver_fn)]
        ):
            with patch("sca_data.db.silver.ingestion_silver._ensure_schema"):
                view = ProgramasUploadView.as_view()
                request = factory.post(
                    "/api/import/programas/",
                    {"file": _csv_file("programas")},
                    format="multipart",
                )
                view(request)
        silver_fn.assert_called_once()

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_bronze_create_called_with_correct_table_name(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = MateriaisUploadView.as_view()
        request = factory.post(
            "/api/import/materiais/",
            {"file": _csv_file("materiais")},
            format="multipart",
        )
        view(request)
        _, _, table_name = mock_bronze_create.call_args[0]
        assert table_name == "materiais"

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_audit_success_logged_on_ingest(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = ProgramasUploadView.as_view()
        request = factory.post(
            "/api/import/programas/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        view(request)
        mock_audit.log_exec.assert_called()


class TestViewCsvTypes:
    def test_programas(self):
        assert ProgramasUploadView.csv_type == "programas"

    def test_projetos(self):
        assert ProjetosUploadView.csv_type == "projetos"

    def test_materiais(self):
        assert MateriaisUploadView.csv_type == "materiais"

    def test_empenho_materiais(self):
        assert EmpenhoMateriaisUploadView.csv_type == "empenho_materiais"

    def test_estoque_materiais_projeto(self):
        assert EstoqueMateriaisProjetoUploadView.csv_type == "estoque_materiais_projeto"

    def test_fornecedores(self):
        assert FornecedoresUploadView.csv_type == "fornecedores"

    def test_pedidos_compra(self):
        assert PedidosCompraUploadView.csv_type == "pedidos_compra"

    def test_solicitacoes_compra(self):
        assert SolicitacoesCompraUploadView.csv_type == "solicitacoes_compra"

    def test_compras_projeto(self):
        assert ComprasProjetoUploadView.csv_type == "compras_projeto"

    def test_tarefas_projeto(self):
        assert TarefasProjetoUploadView.csv_type == "tarefas_projeto"

    def test_tempo_tarefas(self):
        assert TempoTarefasUploadView.csv_type == "tempo_tarefas"


class TestEachEndpointAcceptsItsOwnType:
    """Spot-check that each endpoint correctly accepts its own CSV type."""

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_fornecedores_accepts_fornecedores_csv(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = FornecedoresUploadView.as_view()
        request = factory.post(
            "/api/import/fornecedores/",
            {"file": _csv_file("fornecedores")},
            format="multipart",
        )
        response = view(request)
        assert response.status_code == 200

    def test_fornecedores_rejects_programas_csv(self, factory):
        view = FornecedoresUploadView.as_view()
        request = factory.post(
            "/api/import/fornecedores/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        response = view(request)
        assert response.status_code == 400
        assert response.data["tipo_esperado"] == "fornecedores"

    @patch("imports.views._get_engine")
    @patch("imports.views.audit_mod")
    @patch("sca_data.db.bronze.ingestion._ensure_schema")
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.silver.ingestion_silver.PIPELINE", [])
    def test_tempo_tarefas_accepts_its_own_csv(
        self, mock_bronze_create, mock_bronze_schema, mock_audit, mock_engine, factory
    ):
        mock_engine.return_value = MagicMock()
        view = TempoTarefasUploadView.as_view()
        request = factory.post(
            "/api/import/tempo-tarefas/",
            {"file": _csv_file("tempo_tarefas")},
            format="multipart",
        )
        response = view(request)
        assert response.status_code == 200


class TestPerfilImportRestriction:
    """Profile-based CSV upload restrictions (lines 112-114 of views.py)."""

    def test_perfil_sem_permissao_para_csv_type_retorna_403(self, monkeypatch):
        import imports.views as imports_views_mod
        from users import permissions as perm_mod

        monkeypatch.setattr(perm_mod, "_get_permissao", lambda u: "almoxarifado")
        monkeypatch.setattr(
            imports_views_mod, "_get_permissao", lambda u: "almoxarifado"
        )

        user = get_user_model()(username="_almox", is_active=True)
        base = APIRequestFactory()
        req = base.post("/api/import/programas/", {}, format="multipart")
        force_authenticate(req, user=user)

        view = ProgramasUploadView.as_view()
        response = view(req)

        assert response.status_code == 403

    def test_perfil_com_permissao_nao_e_bloqueado(self, monkeypatch):
        import imports.views as imports_views_mod
        from users import permissions as perm_mod

        monkeypatch.setattr(perm_mod, "_get_permissao", lambda u: "financeiro")
        monkeypatch.setattr(imports_views_mod, "_get_permissao", lambda u: "financeiro")

        user = get_user_model()(username="_fin", is_active=True)
        base = APIRequestFactory()
        req = base.post(
            "/api/import/programas/",
            {"file": _csv_file("programas")},
            format="multipart",
        )
        force_authenticate(req, user=user)

        with (
            patch("imports.views._get_engine"),
            patch("imports.views.audit_mod"),
            patch("sca_data.db.bronze.ingestion._ensure_schema"),
            patch("sca_data.db.bronze.ingestion._create_table"),
            patch("sca_data.db.silver.ingestion_silver.PIPELINE", []),
        ):
            view = ProgramasUploadView.as_view()
            response = view(req)

        assert response.status_code == 200
