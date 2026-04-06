"""
Conftest: mocks the DB connection before any sca_data.db module is imported.
This prevents real DB connections during unit tests.
"""

import sys
from unittest.mock import MagicMock

# Inject mock BEFORE sca_data.db modules are collected/imported by pytest.
# Both ingestion.py files call `getOrCreate()` at module level, so the mock
# must exist in sys.modules before those imports are resolved.
_mock_engine = MagicMock()
_mock_conn_module = MagicMock()
_mock_conn_module.getOrCreate.return_value = _mock_engine
sys.modules["sca_data.db.connection"] = _mock_conn_module
