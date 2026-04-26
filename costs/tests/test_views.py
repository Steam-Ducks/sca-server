import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from costs.views import GoldCostsTableView
from costs.serializers import GoldCostsSerializer


def _make_request(params: dict = None):
    """Cria um GET request com query params opcionais."""
    factory = APIRequestFactory()
    url = "/costs/"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return factory.get(url, params or {})


def _make_view():
    view = GoldCostsTableView()
    view.kwargs = {}
    return view


def _attach_request(view, params: dict = None):
    request = _make_request(params)
    view.request = Request(request)
    return view


@pytest.fixture
def mock_queryset():
    qs = MagicMock()
    qs.filter.return_value = qs
    qs.order_by.return_value = qs
    return qs


class TestGoldCostsTableViewSetup:
    def test_uses_gold_costs_serializer(self):
        assert GoldCostsTableView.serializer_class is GoldCostsSerializer

    def test_extends_list_api_view(self):
        from rest_framework import generics

        assert issubclass(GoldCostsTableView, generics.ListAPIView)


class TestGetQuerysetNoFilters:
    @patch("costs.views.GoldCosts.objects")
    def test_returns_all_ordered_by_data(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view())
        result = view.get_queryset()

        mock_objects.all.assert_called_once()
        qs.order_by.assert_called_once_with("data")
        assert result == qs

    @patch("costs.views.GoldCosts.objects")
    def test_no_filter_called_without_params(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={})
        view.get_queryset()

        qs.filter.assert_not_called()


class TestGetQuerysetTextFilters:
    @pytest.mark.parametrize(
        "param,value",
        [
            ("nome_programa", "Programa Alpha"),
            ("gerente_programa", "João Silva"),
            ("nome_projeto", "Projeto X"),
            ("responsavel_projeto", "Maria Souza"),
        ],
    )
    @patch("costs.views.GoldCosts.objects")
    def test_filter_applied_for_param(self, mock_objects, param, value):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={param: value})
        view.get_queryset()

        qs.filter.assert_any_call(**{param: value})

    @patch("costs.views.GoldCosts.objects")
    def test_multiple_filters_applied(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        params = {"nome_programa": "Alpha", "gerente_programa": "João"}
        view = _attach_request(_make_view(), params=params)
        view.get_queryset()

        assert qs.filter.call_count == 2

    @patch("costs.views.GoldCosts.objects")
    def test_empty_string_param_is_ignored(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={"nome_programa": ""})
        view.get_queryset()

        qs.filter.assert_not_called()


class TestGetQuerysetDateFilters:
    @patch("costs.views.GoldCosts.objects")
    def test_data_gte_filter_applied(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={"data_gte": "2024-01-01"})
        view.get_queryset()

        qs.filter.assert_any_call(data__gte=date(2024, 1, 1))

    @patch("costs.views.GoldCosts.objects")
    def test_data_lte_filter_applied(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={"data_lte": "2024-12-31"})
        view.get_queryset()

        qs.filter.assert_any_call(data__lte=date(2024, 12, 31))

    @patch("costs.views.GoldCosts.objects")
    def test_both_date_filters_applied(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        params = {"data_gte": "2024-01-01", "data_lte": "2024-12-31"}
        view = _attach_request(_make_view(), params=params)
        view.get_queryset()

        qs.filter.assert_any_call(data__gte=date(2024, 1, 1))
        qs.filter.assert_any_call(data__lte=date(2024, 12, 31))

    @patch("costs.views.GoldCosts.objects")
    def test_invalid_date_format_is_ignored(self, mock_objects):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        mock_objects.all.return_value = qs

        view = _attach_request(_make_view(), params={"data_gte": "not-a-date"})
        view.get_queryset()

        called_kwargs = [str(c) for c in qs.filter.call_args_list]
        assert not any("data__gte" in kw for kw in called_kwargs)
