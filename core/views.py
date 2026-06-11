import time as _time
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.selectors import (
    compute_overall_status,
    get_alerts,
    get_data_integrity,
    get_db_stats,
    get_last_updates,
    get_recent_processes,
    get_service_status,
)

_SERVER_START = _time.time()

_DEFAULT_CACHE_TTL = 300


def build_cache_key(prefix, params=None, **extra):
    """Build a deterministic cache key from a prefix and request filters.

    Mirrors the ``_ck`` helper that was duplicated across the filtered list
    views: query params and ``extra`` pairs are sorted, empty values are
    dropped and the remaining ``key=value`` pairs are joined with ``&``.
    ``extra`` is appended after the query params (e.g. the ``periodo`` URL
    segment of the dedicated period endpoints).
    """
    parts = sorted((params or {}).items())
    extra_parts = sorted(extra.items())
    suffix = "&".join(f"{k}={v}" for k, v in parts + extra_parts if v)
    return f"{prefix}:{suffix}" if suffix else prefix


class BaseFilteredListView(generics.ListAPIView):
    """``ListAPIView`` that caches its serialized response per request filters.

    Subclasses set :attr:`cache_key_prefix` and implement ``get_queryset``.
    Endpoints that disambiguate the cache by URL kwargs (the ``periodo``
    views) override :meth:`get_cache_key_extra`.

    The cached value is exactly ``response.data`` from the standard DRF
    ``list`` flow, so migrating a view to this base preserves its response
    shape, status code and cache behavior.
    """

    cache_key_prefix = None
    cache_ttl = _DEFAULT_CACHE_TTL

    def get_cache_key_extra(self):
        """Extra key/value pairs appended to the cache key (e.g. URL kwargs)."""
        return {}

    def get_cache_key(self, request):
        return build_cache_key(
            self.cache_key_prefix,
            request.query_params,
            **self.get_cache_key_extra(),
        )

    def list(self, request, *args, **kwargs):
        key = self.get_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, self.cache_ttl)
        return response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


_STATUS_CACHE_KEY = "status_view"
_STATUS_CACHE_TTL = 300


@api_view(["GET"])
@permission_classes([AllowAny])
def status_view(request):
    cached = cache.get(_STATUS_CACHE_KEY)
    if cached is not None:
        return Response(cached)

    services = get_service_status()
    processes = get_recent_processes()
    last_updates = get_last_updates()
    alerts = get_alerts()
    integrity = get_data_integrity()
    db_stats = get_db_stats()

    data = {
        "status": compute_overall_status(services, alerts, integrity),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "development" if settings.DEBUG else "production",
        "uptime_seconds": round(_time.time() - _SERVER_START),
        "services": services,
        "processes": processes,
        "last_updates": last_updates,
        "alerts": alerts,
        "data_integrity": integrity,
        "db_stats": db_stats,
    }
    cache.set(_STATUS_CACHE_KEY, data, _STATUS_CACHE_TTL)
    return Response(data)
