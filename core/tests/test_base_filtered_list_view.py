from unittest.mock import patch

from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from django.core.cache import cache
from django.test import override_settings

from core.views import BaseFilteredListView, build_cache_key

# settings_test usa DummyCache (no-op); para exercitar o caching real da base
# trocamos por LocMemCache nos testes que dependem de cache.get/cache.set.
_LOCMEM = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "base-filtered-list-view-tests",
    }
}


# ---------------------------------------------------------------------------
# build_cache_key — replica exata do helper _ck duplicado pelas views
# ---------------------------------------------------------------------------


class TestBuildCacheKey:
    def test_prefix_only_when_no_params(self):
        assert build_cache_key("prefix") == "prefix"
        assert build_cache_key("prefix", {}) == "prefix"

    def test_includes_sorted_params(self):
        assert build_cache_key("p", {"b": "2", "a": "1"}) == "p:a=1&b=2"

    def test_ignores_empty_values(self):
        assert build_cache_key("p", {"a": "1", "b": ""}) == "p:a=1"

    def test_appends_extra_after_params(self):
        assert (
            build_cache_key("p", {"a": "1"}, periodo="2024-03")
            == "p:a=1&periodo=2024-03"
        )

    def test_extra_only(self):
        assert build_cache_key("p", {}, periodo="2024-03") == "p:periodo=2024-03"

    def test_ignores_empty_extra(self):
        assert build_cache_key("p", {"a": "1"}, periodo="") == "p:a=1"


# ---------------------------------------------------------------------------
# BaseFilteredListView — classe base
# ---------------------------------------------------------------------------


class TestBaseFilteredListViewClass:
    def test_extends_list_api_view(self):
        assert issubclass(BaseFilteredListView, generics.ListAPIView)

    def test_default_cache_ttl(self):
        assert BaseFilteredListView.cache_ttl == 300

    def test_default_cache_key_extra_is_empty(self):
        assert BaseFilteredListView().get_cache_key_extra() == {}


class _StubView(BaseFilteredListView):
    cache_key_prefix = "stub"


def _request(params=None):
    factory = APIRequestFactory()
    url = "/stub/"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return Request(factory.get(url, params or {}))


class TestBaseFilteredListViewCaching:
    def test_get_cache_key_uses_prefix_and_params(self):
        view = _StubView()
        view.kwargs = {}
        assert view.get_cache_key(_request({"a": "1"})) == "stub:a=1"

    @override_settings(CACHES=_LOCMEM)
    def test_list_caches_and_serves_second_call_from_cache(self):
        cache.clear()
        view = _StubView()
        view.kwargs = {}
        request = _request()
        with patch(
            "rest_framework.generics.ListAPIView.list",
            return_value=Response({"x": 1}),
        ) as mocked_super:
            first = view.list(request)
            second = view.list(request)

        assert mocked_super.call_count == 1
        assert first.data == {"x": 1}
        assert second.data == {"x": 1}

    @override_settings(CACHES=_LOCMEM)
    def test_list_stores_response_data_under_cache_key(self):
        cache.clear()
        view = _StubView()
        view.kwargs = {}
        request = _request({"a": "1"})
        with patch(
            "rest_framework.generics.ListAPIView.list",
            return_value=Response([{"id": 1}]),
        ):
            view.list(request)
        assert cache.get("stub:a=1") == [{"id": 1}]
