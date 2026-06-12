import sys
from unittest.mock import MagicMock

# sca_data is excluded from INSTALLED_APPS in settings_test when DB_HOST is
# not set, so FatoExecucaoCarga is not available as a real model. Mock it so
# monitoring tests can be collected and run without a database.
_mock_fato = MagicMock()
_mock_sca_data_models = MagicMock()
_mock_sca_data_models.FatoExecucaoCarga = _mock_fato
sys.modules.setdefault("sca_data.models", _mock_sca_data_models)
