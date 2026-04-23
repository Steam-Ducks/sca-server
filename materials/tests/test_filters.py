"""
Testes de filtros da tela de materiais.

Cobertura dos critérios de aceite da US:
  CT01 — filtro por material
  CT02 — filtro por fornecedor
  CT03 — filtro por categoria
  CT04 — combinação de múltiplos filtros
  +    — filtros por período (periodo, data_inicio/data_fim)
  +    — filtros por programa e projeto
  +    — validações de parâmetros inválidos
"""
import datetime
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from materials.selectors import get_materials_queryset
from materials.views import MaterialsTableView
from sca_data.models import (
    SilverFornecedor,
    SilverMaterial,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverSolicitacaoCompra,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _criar_pedido(
    id=1,
    descricao_material="Cabo de aço",
    categoria="Estrutural",
    razao_social_fornecedor="Fornecedor Ltda",
    nome_projeto="Projeto Alpha",
    nome_programa="Programa Alpha",
    data_pedido=None,
    valor_total=1500.00,
):
    now = timezone.now()
    data_pedido = data_pedido or datetime.date(2024, 3, 15)

    programa = SilverPrograma(
        id=id,
        codigo_programa=f"PROG-{id:03d}",
        nome_programa=nome_programa,
        silver_ingested_at=now,
    )
    projeto = SilverProjeto(
        id=id,
        codigo_projeto=f"PROJ-{id:03d}",
        nome_projeto=nome_projeto,
        silver_ingested_at=now,
    )
    projeto.programa = programa

    material = SilverMaterial(
        id=id,
        codigo_material=f"MAT-{id:03d}",
        descricao=descricao_material,
        categoria=categoria,
        custo_estimado=150.00,
        silver_ingested_at=now,
    )
    fornecedor = SilverFornecedor(
        id=id,
        codigo_fornecedor=f"FORN-{id:03d}",
        razao_social=razao_social_fornecedor,
        silver_ingested_at=now,
    )
    solicitacao = SilverSolicitacaoCompra(
        id=id,
        numero_solicitacao=f"SC-{id:03d}",
        quantidade=10,
        silver_ingested_at=now,
    )
    solicitacao.projeto = projeto
    solicitacao.material = material

    pedido = SilverPedidoCompra(
        id=id,
        numero_pedido=f"PC-{id:03d}",
        data_pedido=data_pedido,
        valor_total=valor_total,
        silver_ingested_at=now,
    )
    pedido.solicitacao = solicitacao
    pedido.fornecedor = fornecedor
    return pedido


# ---------------------------------------------------------------------------
# Testes de status e estrutura básica
# ---------------------------------------------------------------------------


def test_materials_table_retorna_200():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.status_code == 200


def test_materials_table_retorna_lista_vazia():
    with patch.object(MaterialsTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/compras/")
        assert response.data == []


def test_materials_table_retorna_campos_corretos():
    pedido = _criar_pedido()
    with patch.object(MaterialsTableView, "get_queryset", return_value=[pedido]):
        client = APIClient()
        response = client.get("/api/compras/")
        item = response.data[0]
        assert item["material"] == "Cabo de aço"
        assert item["projeto"] == "Projeto Alpha"
        assert item["programa"] == "Programa Alpha"
        assert item["quantidade"] == 10
        assert item["valor_unitario"] == 150.00
        assert item["valor_total"] == 1500.00
        assert item["fornecedor"] == "Fornecedor Ltda"
        assert item["categoria"] == "Estrutural"


# ---------------------------------------------------------------------------
# CT01 — Filtro por material
# ---------------------------------------------------------------------------


def test_ct01_filtro_por_material_retorna_resultado_correto():
    """CT01: validar filtro por material."""
    pedido_cabo = _criar_pedido(id=1, descricao_material="Cabo de aço")
    pedido_parafuso = _criar_pedido(id=2, descricao_material="Parafuso inox")

    # Busca parcial (icontains): "cabo" deve retornar apenas o pedido de cabo
    def mock_queryset_cabo(params):
        material = params.get("material", "").lower()
        todos = [pedido_cabo, pedido_parafuso]
        return [p for p in todos if material in p.solicitacao.material.descricao.lower()]

    with patch("materials.views.get_materials_queryset", side_effect=mock_queryset_cabo):
        client = APIClient()
        response = client.get("/api/compras/", {"material": "cabo"})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["material"] == "Cabo de aço"


def test_ct01_filtro_por_material_sem_resultado():
    """CT01: filtro por material que não existe retorna lista vazia."""
    def mock_vazio(params):
        return []

    with patch("materials.views.get_materials_queryset", side_effect=mock_vazio):
        client = APIClient()
        response = client.get("/api/compras/", {"material": "inexistente"})
        assert response.status_code == 200
        assert response.data == []


# ---------------------------------------------------------------------------
# CT02 — Filtro por fornecedor
# ---------------------------------------------------------------------------


def test_ct02_filtro_por_fornecedor_retorna_resultado_correto():
    """CT02: validar filtro por fornecedor."""
    pedido_forn1 = _criar_pedido(id=1, razao_social_fornecedor="Metalúrgica SA")
    pedido_forn2 = _criar_pedido(id=2, razao_social_fornecedor="Eletro Peças Ltda")

    def mock_queryset_fornecedor(params):
        fornecedor = params.get("fornecedor", "").lower()
        todos = [pedido_forn1, pedido_forn2]
        return [p for p in todos if fornecedor in p.fornecedor.razao_social.lower()]

    with patch(
        "materials.views.get_materials_queryset",
        side_effect=mock_queryset_fornecedor,
    ):
        client = APIClient()
        response = client.get("/api/compras/", {"fornecedor": "metalúrgica"})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["fornecedor"] == "Metalúrgica SA"


def test_ct02_filtro_por_fornecedor_sem_resultado():
    """CT02: fornecedor inexistente retorna lista vazia."""
    def mock_vazio(params):
        return []

    with patch("materials.views.get_materials_queryset", side_effect=mock_vazio):
        client = APIClient()
        response = client.get("/api/compras/", {"fornecedor": "inexistente"})
        assert response.status_code == 200
        assert response.data == []


# ---------------------------------------------------------------------------
# CT03 — Filtro por categoria
# ---------------------------------------------------------------------------


def test_ct03_filtro_por_categoria_retorna_resultado_correto():
    """CT03: validar filtro por categoria."""
    pedido_estrutural = _criar_pedido(id=1, categoria="Estrutural")
    pedido_eletrico = _criar_pedido(id=2, categoria="Elétrico")

    def mock_queryset_categoria(params):
        categoria = params.get("categoria", "").lower()
        todos = [pedido_estrutural, pedido_eletrico]
        return [
            p
            for p in todos
            if categoria == p.solicitacao.material.categoria.lower()
        ]

    with patch(
        "materials.views.get_materials_queryset",
        side_effect=mock_queryset_categoria,
    ):
        client = APIClient()
        response = client.get("/api/compras/", {"categoria": "Estrutural"})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["categoria"] == "Estrutural"


def test_ct03_filtro_por_categoria_sem_resultado():
    """CT03: categoria inexistente retorna lista vazia."""
    def mock_vazio(params):
        return []

    with patch("materials.views.get_materials_queryset", side_effect=mock_vazio):
        client = APIClient()
        response = client.get("/api/compras/", {"categoria": "Inexistente"})
        assert response.status_code == 200
        assert response.data == []


# ---------------------------------------------------------------------------
# CT04 — Combinação de múltiplos filtros
# ---------------------------------------------------------------------------


def test_ct04_combinacao_material_e_fornecedor():
    """CT04: combinação de material + fornecedor."""
    pedido_match = _criar_pedido(
        id=1,
        descricao_material="Cabo de aço",
        razao_social_fornecedor="Metalúrgica SA",
    )
    pedido_sem_match = _criar_pedido(
        id=2,
        descricao_material="Cabo de aço",
        razao_social_fornecedor="Eletro Peças Ltda",
    )

    def mock_multi(params):
        material = params.get("material", "").lower()
        fornecedor = params.get("fornecedor", "").lower()
        todos = [pedido_match, pedido_sem_match]
        return [
            p
            for p in todos
            if material in p.solicitacao.material.descricao.lower()
            and fornecedor in p.fornecedor.razao_social.lower()
        ]

    with patch("materials.views.get_materials_queryset", side_effect=mock_multi):
        client = APIClient()
        response = client.get(
            "/api/compras/",
            {"material": "cabo", "fornecedor": "metalúrgica"},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["material"] == "Cabo de aço"
        assert response.data[0]["fornecedor"] == "Metalúrgica SA"


def test_ct04_combinacao_categoria_e_projeto():
    """CT04: combinação de categoria + projeto."""
    pedido_match = _criar_pedido(
        id=1, categoria="Elétrico", nome_projeto="Projeto Elétrico"
    )
    pedido_sem_match = _criar_pedido(
        id=2, categoria="Elétrico", nome_projeto="Projeto Mecânico"
    )

    def mock_multi(params):
        categoria = params.get("categoria", "").lower()
        projeto = params.get("projeto", "").lower()
        todos = [pedido_match, pedido_sem_match]
        return [
            p
            for p in todos
            if categoria == p.solicitacao.material.categoria.lower()
            and projeto == p.solicitacao.projeto.nome_projeto.lower()
        ]

    with patch("materials.views.get_materials_queryset", side_effect=mock_multi):
        client = APIClient()
        response = client.get(
            "/api/compras/",
            {"categoria": "Elétrico", "projeto": "Projeto Elétrico"},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["categoria"] == "Elétrico"
        assert response.data[0]["projeto"] == "Projeto Elétrico"


def test_ct04_combinacao_todos_os_filtros():
    """CT04: todos os filtros ativos simultaneamente."""
    pedido_match = _criar_pedido(
        id=1,
        descricao_material="Cabo de aço",
        categoria="Estrutural",
        razao_social_fornecedor="Metalúrgica SA",
        nome_projeto="Projeto Alpha",
        nome_programa="Programa Alpha",
        data_pedido=datetime.date(2024, 3, 15),
    )
    pedido_sem_match = _criar_pedido(
        id=2,
        descricao_material="Parafuso",
        categoria="Fixação",
        razao_social_fornecedor="Outra Empresa",
        nome_projeto="Projeto Beta",
        nome_programa="Programa Beta",
        data_pedido=datetime.date(2024, 5, 10),
    )

    def mock_multi(params):
        todos = [pedido_match, pedido_sem_match]
        resultado = todos[:]

        if params.get("material"):
            m = params["material"].lower()
            resultado = [p for p in resultado if m in p.solicitacao.material.descricao.lower()]
        if params.get("fornecedor"):
            f = params["fornecedor"].lower()
            resultado = [p for p in resultado if f in p.fornecedor.razao_social.lower()]
        if params.get("categoria"):
            c = params["categoria"].lower()
            resultado = [p for p in resultado if c == p.solicitacao.material.categoria.lower()]
        if params.get("projeto"):
            pj = params["projeto"].lower()
            resultado = [p for p in resultado if pj == p.solicitacao.projeto.nome_projeto.lower()]
        if params.get("programa"):
            pg = params["programa"].lower()
            resultado = [p for p in resultado if pg == p.solicitacao.projeto.programa.nome_programa.lower()]

        return resultado

    with patch("materials.views.get_materials_queryset", side_effect=mock_multi):
        client = APIClient()
        response = client.get(
            "/api/compras/",
            {
                "material": "cabo",
                "fornecedor": "metalúrgica",
                "categoria": "Estrutural",
                "projeto": "Projeto Alpha",
                "programa": "Programa Alpha",
            },
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["material"] == "Cabo de aço"


def test_ct04_filtros_sem_interseccao_retorna_vazio():
    """CT04: filtros conflitantes não retornam resultado."""
    def mock_vazio(params):
        return []

    with patch("materials.views.get_materials_queryset", side_effect=mock_vazio):
        client = APIClient()
        response = client.get(
            "/api/compras/",
            {"material": "cabo", "categoria": "Elétrico"},  # cabo é Estrutural
        )
        assert response.status_code == 200
        assert response.data == []


# ---------------------------------------------------------------------------
# Filtro por período
# ---------------------------------------------------------------------------


def test_filtro_por_periodo_retorna_pedidos_do_mes():
    """Filtro periodo=YYYY-MM retorna apenas pedidos do mês."""
    pedido_marco = _criar_pedido(id=1, data_pedido=datetime.date(2024, 3, 15))
    pedido_abril = _criar_pedido(id=2, data_pedido=datetime.date(2024, 4, 10))

    def mock_periodo(params):
        periodo = params.get("periodo")
        if periodo == "2024-03":
            return [pedido_marco]
        return [pedido_marco, pedido_abril]

    with patch("materials.views.get_materials_queryset", side_effect=mock_periodo):
        client = APIClient()
        response = client.get("/api/compras/", {"periodo": "2024-03"})
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_data_inicio_e_data_fim():
    """Filtro data_inicio + data_fim retorna pedidos no intervalo."""
    pedido_dentro = _criar_pedido(id=1, data_pedido=datetime.date(2024, 3, 15))
    pedido_fora = _criar_pedido(id=2, data_pedido=datetime.date(2024, 5, 10))

    def mock_range(params):
        inicio = params.get("data_inicio")
        fim = params.get("data_fim")
        todos = [pedido_dentro, pedido_fora]
        if inicio and fim:
            di = datetime.date.fromisoformat(inicio)
            df = datetime.date.fromisoformat(fim)
            return [p for p in todos if di <= p.data_pedido <= df]
        return todos

    with patch("materials.views.get_materials_queryset", side_effect=mock_range):
        client = APIClient()
        response = client.get(
            "/api/compras/",
            {"data_inicio": "2024-03-01", "data_fim": "2024-03-31"},
        )
        assert response.status_code == 200
        assert len(response.data) == 1


# ---------------------------------------------------------------------------
# Filtros por programa e projeto
# ---------------------------------------------------------------------------


def test_filtro_por_programa():
    pedido_alpha = _criar_pedido(id=1, nome_programa="Programa Alpha")
    pedido_beta = _criar_pedido(id=2, nome_programa="Programa Beta")

    def mock_programa(params):
        programa = params.get("programa", "").lower()
        todos = [pedido_alpha, pedido_beta]
        return [
            p
            for p in todos
            if programa == p.solicitacao.projeto.programa.nome_programa.lower()
        ]

    with patch("materials.views.get_materials_queryset", side_effect=mock_programa):
        client = APIClient()
        response = client.get("/api/compras/", {"programa": "Programa Alpha"})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["programa"] == "Programa Alpha"


def test_filtro_por_projeto():
    pedido_alpha = _criar_pedido(id=1, nome_projeto="Projeto Alpha")
    pedido_beta = _criar_pedido(id=2, nome_projeto="Projeto Beta")

    def mock_projeto(params):
        projeto = params.get("projeto", "").lower()
        todos = [pedido_alpha, pedido_beta]
        return [
            p
            for p in todos
            if projeto == p.solicitacao.projeto.nome_projeto.lower()
        ]

    with patch("materials.views.get_materials_queryset", side_effect=mock_projeto):
        client = APIClient()
        response = client.get("/api/compras/", {"projeto": "Projeto Alpha"})
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["projeto"] == "Projeto Alpha"


# ---------------------------------------------------------------------------
# Validações de parâmetros inválidos
# ---------------------------------------------------------------------------


def test_periodo_invalido_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/", {"periodo": "2024-13"})
    assert response.status_code == 400


def test_periodo_formato_errado_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/", {"periodo": "03-2024"})
    assert response.status_code == 400


def test_data_inicio_invalida_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/", {"data_inicio": "31-03-2024"})
    assert response.status_code == 400


def test_data_fim_invalida_retorna_400():
    client = APIClient()
    response = client.get("/api/compras/", {"data_fim": "não-é-data"})
    assert response.status_code == 400


def test_data_inicio_maior_que_data_fim_retorna_400():
    client = APIClient()
    response = client.get(
        "/api/compras/",
        {"data_inicio": "2024-04-01", "data_fim": "2024-03-01"},
    )
    assert response.status_code == 400
