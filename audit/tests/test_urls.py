from django.urls import resolve, reverse


class TestAuditUrls:
    def test_audit_url_resolves(self):
        resolver = resolve("/audit/")
        assert resolver.view_name == "audit-log-list"

    def test_audit_url_reverse(self):
        url = reverse("audit-log-list")
        assert url == "/audit/"