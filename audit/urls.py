from django.urls import path
from audit.views import AuditExecutionLogTableView


urlpatterns = [
    path("audit/", AuditExecutionLogTableView.as_view(), name="audit-log-list"),
]
