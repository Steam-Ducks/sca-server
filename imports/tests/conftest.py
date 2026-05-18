"""
Mock the DB connection before any sca_data.db module is imported.
ingestion_silver.py calls get_or_create() at module level, so the mock
must exist in sys.modules before those imports are resolved.
"""

import sys
from unittest.mock import MagicMock

_mock_engine = MagicMock()
_mock_conn_module = MagicMock()
_mock_conn_module.get_or_create.return_value = _mock_engine
sys.modules["sca_data.db.connection"] = _mock_conn_module
