import uuid
import datetime
from unittest.mock import MagicMock

from audit.serializers import AuditExecutionLogSerializer


def _make_log(**kwargs):
    log = MagicMock()
    log.id = kwargs.get("id", 1)
    log.run_id = kwargs.get("run_id", uuid.uuid4())
    log.operation = kwargs.get("operation", "INGEST")
    log.status = kwargs.get("status", "SUCCESS")
    log.table_schema = kwargs.get("table_schema", "bronze")
    log.table_name = kwargs.get("table_name", "programas")
    log.affected_rows = kwargs.get("affected_rows", 100)
    log.started_at = kwargs.get("started_at", datetime.datetime(2024, 1, 1, 10, 0, 0))
    log.finalized_at = kwargs.get(
        "finalized_at", datetime.datetime(2024, 1, 1, 10, 0, 5)
    )
    log.operation_duration = kwargs.get("operation_duration", 5)
    log.operation_metadata = kwargs.get(
        "operation_metadata", {"endpoint": "http://api/files/programas.parquet"}
    )
    return log


class TestAuditExecutionLogSerializer:
    def test_run_id_is_returned_as_string(self):
        uid = uuid.uuid4()
        log = _make_log(run_id=uid)
        serializer = AuditExecutionLogSerializer(log)
        assert serializer.data["run_id"] == str(uid)

    def test_run_id_none_returns_none(self):
        log = _make_log(run_id=None)
        serializer = AuditExecutionLogSerializer(log)
        assert serializer.data["run_id"] is None

    def test_operation_metadata_returned_when_present(self):
        metadata = {
            "endpoint": "http://api/files/programas.parquet",
            "columns": ["id", "nome"],
        }
        log = _make_log(operation_metadata=metadata)
        serializer = AuditExecutionLogSerializer(log)
        assert serializer.data["operation_metadata"] == metadata

    def test_operation_metadata_none_returns_none(self):
        log = _make_log(operation_metadata=None)
        serializer = AuditExecutionLogSerializer(log)
        assert serializer.data["operation_metadata"] is None
