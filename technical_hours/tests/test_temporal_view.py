import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from rest_framework.test import APIClient

from technical_hours.views import TechnicalHoursTemporalView


@pytest.fixture(autouse=True)
def patch_permissao(monkeypatch):
    from users import permissions as perm_mod
    monkeypatch.setattr(perm_mod, "_get_permissao", lambda u: "super_admin")


def _auth_client():
    user = get_user_model()(username="_test", is_active=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client

URL = "/api/horas-tecnicas/temporal/"


def _make_row(
    year: int,
    month: int,
    total_horas: float | None,
    total_custo: float | None = None,
) -> dict:
    """Simula uma linha do queryset agregado por TruncMonth."""
    return {
        "mes": datetime.date(year, month, 1),
        "total_horas": total_horas,
        "total_custo": (
            total_custo if total_custo is not None else (total_horas or 0) * 420
        ),
    }


def _mock_qs(rows: list) -> MagicMock:
    """
    Configura um MagicMock que suporta a cadeia ORM:
    qs.annotate(...).values(...).annotate(...).order_by(...) → rows
    """
    mock = MagicMock()
    mock.annotate.return_value = mock
    mock.values.return_value = mock
    mock.order_by.return_value = rows
    return mock


# ── TC01: evolução temporal exibida corretamente ─────────────────────────────


def test_temporal_retorna_200():
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(URL).status_code == 200


def test_temporal_retorna_lista_vazia_quando_sem_dados():
    """TC01 / TC03: sem registros → lista vazia, status 200."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        response = _auth_client().get(URL)
        assert response.status_code == 200
        assert response.data == []


def test_temporal_retorna_lista_de_periodos():
    """TC01: retorna periodo e total_horas em ordem cronológica."""
    rows = [_make_row(2024, 1, 52.0), _make_row(2024, 3, 40.0)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        response = _auth_client().get(URL)

    assert isinstance(response.data, list)
    assert len(response.data) == 2
    assert response.data[0]["periodo"] == "2024-01"
    assert response.data[0]["total_horas"] == pytest.approx(52.0)
    assert response.data[1]["periodo"] == "2024-03"
    assert response.data[1]["total_horas"] == pytest.approx(40.0)


def test_temporal_campos_presentes():
    """TC01: cada item tem 'periodo', 'total_horas' e 'total_custo'."""
    rows = [_make_row(2024, 3, 70.0, 29400.0)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        item = _auth_client().get(URL).data[0]

    assert set(item.keys()) == {"periodo", "total_horas", "total_custo"}


def test_temporal_retorna_total_custo():
    """TC01: total_custo presente e correto na resposta."""
    rows = [_make_row(2024, 3, 40.0, 16800.0)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        response = _auth_client().get(URL)

    assert response.data[0]["total_custo"] == pytest.approx(16800.0)


def test_temporal_formato_periodo_yyyy_mm():
    """TC01: período formatado como YYYY-MM."""
    rows = [_make_row(2024, 1, 10.0)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        assert _auth_client().get(URL).data[0]["periodo"] == "2024-01"


def test_temporal_mes_formatado_com_zero_a_esquerda():
    """TC01: mês < 10 é formatado com zero à esquerda (ex: 2024-03)."""
    rows = [_make_row(2024, 3, 10.0)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        assert _auth_client().get(URL).data[0]["periodo"] == "2024-03"


def test_temporal_arredonda_para_duas_casas():
    """TC01: total_horas arredondado para 2 casas decimais."""
    rows = [_make_row(2024, 1, 33.333333)]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        assert _auth_client().get(URL).data[0]["total_horas"] == pytest.approx(33.33)


def test_temporal_multiplos_periodos_em_ordem():
    """TC01: períodos retornados em ordem cronológica."""
    rows = [
        _make_row(2024, 1, 52.0),
        _make_row(2024, 2, 0.0),
        _make_row(2024, 3, 70.0),
    ]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        response = _auth_client().get(URL)

    periodos = [item["periodo"] for item in response.data]
    assert periodos == ["2024-01", "2024-02", "2024-03"]


# ── TC02: filtros de dimensão respeitados ────────────────────────────────────


def test_temporal_ignora_filtro_periodo(rf):
    """TC02: ?periodo= na query string é ignorado — a série histórica é completa."""
    request = rf.get(URL, {"periodo": "2024-03"})
    view = TechnicalHoursTemporalView()
    view.request = Request(request)

    assert view._build_period_filters() == {}


def test_temporal_ignora_filtro_data_inicio(rf):
    """TC02: ?data_inicio= também é ignorado."""
    request = rf.get(URL, {"data_inicio": "2024-01-01"})
    view = TechnicalHoursTemporalView()
    view.request = Request(request)

    assert view._build_period_filters() == {}


def test_temporal_aceita_filtro_programa():
    """TC02: ?programa= não causa erro."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?programa=Cloud").status_code == 200


def test_temporal_aceita_filtro_projeto():
    """TC02: ?projeto= não causa erro."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?projeto=Migracao+AWS").status_code == 200


def test_temporal_aceita_filtros_combinados():
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert (
            _auth_client().get(f"{URL}?programa=Cloud&projeto=Migracao+AWS").status_code
            == 200
        )


# ── TC03: comportamento para períodos sem horas registradas ──────────────────


def test_temporal_trata_total_horas_none():
    """TC03: total_horas None é convertido para 0.0."""
    rows = [
        {"mes": datetime.date(2024, 2, 1), "total_horas": None, "total_custo": None}
    ]
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs(rows)
    ):
        data = _auth_client().get(URL).data[0]
        assert data["total_horas"] == pytest.approx(0.0)
        assert data["total_custo"] == pytest.approx(0.0)


def test_temporal_periodo_invalido_nao_afeta_endpoint():
    """TC03: ?periodo= inválido não causa 400 — o parâmetro é ignorado."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?periodo=invalido").status_code == 200


# ── Filtros de dimensão adicionais ────────────────────────────────────────────


def test_temporal_aceita_filtro_colaborador():
    """TC02: ?colaborador= não causa erro."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?colaborador=Lucas+Martins").status_code == 200


def test_temporal_aceita_filtro_tarefa():
    """TC02: ?tarefa= não causa erro."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?tarefa=Arquitetura+Cloud").status_code == 200


def test_temporal_aceita_filtro_funcao():
    """TC02: ?funcao= não causa erro."""
    with patch.object(
        TechnicalHoursTemporalView, "get_queryset", return_value=_mock_qs([])
    ):
        assert _auth_client().get(f"{URL}?funcao=Cloud+Architect").status_code == 200


def test_temporal_aplica_filtro_colaborador(rf):
    """TC02: filtro colaborador é repassado ao queryset via _apply_dimension_filters."""
    from unittest.mock import MagicMock
    from rest_framework.request import Request

    request = rf.get(URL, {"colaborador": "Lucas Martins"})
    view = TechnicalHoursTemporalView()
    view.request = Request(request)

    mock_qs = MagicMock()
    mock_qs.filter.return_value = mock_qs

    view._apply_dimension_filters(mock_qs)

    mock_qs.filter.assert_any_call(usuario__iexact="Lucas Martins")


def test_temporal_aplica_filtro_tarefa(rf):
    """TC02: filtro tarefa é repassado ao queryset via _apply_dimension_filters."""
    from unittest.mock import MagicMock
    from rest_framework.request import Request

    request = rf.get(URL, {"tarefa": "Arquitetura Cloud"})
    view = TechnicalHoursTemporalView()
    view.request = Request(request)

    mock_qs = MagicMock()
    mock_qs.filter.return_value = mock_qs

    view._apply_dimension_filters(mock_qs)

    mock_qs.filter.assert_any_call(tarefa__titulo__iexact="Arquitetura Cloud")
