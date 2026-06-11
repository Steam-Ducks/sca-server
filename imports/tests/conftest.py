"""
Mock sca_data.db modules before any imports are resolved.
Both ingestion_silver.py and imports/views.py import these at module level,
so mocks must exist in sys.modules before test collection begins.
"""

import sys
from unittest.mock import MagicMock

_mock_engine = MagicMock()

_mock_conn_module = MagicMock()
_mock_conn_module.get_or_create.return_value = _mock_engine
sys.modules["sca_data.db.connection"] = _mock_conn_module

# sca_data/db/audit/audit.py is not present on disk (only a .pyc leftover);
# mock it so imports/views.py can be collected without a ModuleNotFoundError.
_mock_audit_module = MagicMock()
sys.modules["sca_data.db.audit"] = MagicMock()
sys.modules["sca_data.db.audit.audit"] = _mock_audit_module
