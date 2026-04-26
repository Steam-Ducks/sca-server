from django.urls import resolve, reverse


class TestCostsUrls:
    def test_audit_url_resolves(self):
        resolver = resolve("/api/costs/")
        assert resolver.view_name == "costs"

    def test_audit_url_reverse(self):
        url = reverse("costs")
        assert url == "/api/costs/"
