import pytest
from datetime import date, datetime, timezone

from costs.serializers import GoldCostsSerializer


@pytest.fixture
def valid_data():
    return {
        "data": date(2024, 1, 15),
        "nome_programa": "Programa Alpha",
        "gerente_programa": "João Silva",
        "nome_projeto": "Projeto X",
        "responsavel_projeto": "Maria Souza",
        "custo": 15000.0,
        "gold_updated_at": datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def serializer(valid_data):
    return GoldCostsSerializer(data=valid_data)


class TestGoldCostsSerializerFields:
    def test_contains_expected_fields(self, serializer):
        serializer.is_valid()
        assert set(serializer.fields.keys()) == {
            "id",
            "data",
            "nome_programa",
            "gerente_programa",
            "nome_projeto",
            "responsavel_projeto",
            "custo",
            "gold_updated_at",
        }

    def test_all_fields_are_present(self, serializer):
        serializer.is_valid()
        assert len(serializer.fields) > 0


class TestGoldCostsSerializerSerialize:
    def test_serializes_instance_correctly(self, valid_data):
        from sca_data.models import GoldCosts

        instance = GoldCosts(**valid_data, id=1)
        serializer = GoldCostsSerializer(instance)
        data = serializer.data

        assert data["nome_programa"] == valid_data["nome_programa"]
        assert data["gerente_programa"] == valid_data["gerente_programa"]
        assert data["nome_projeto"] == valid_data["nome_projeto"]
        assert data["responsavel_projeto"] == valid_data["responsavel_projeto"]
        assert data["custo"] == valid_data["custo"]

    def test_data_field_is_serialized_as_date_string(self, valid_data):
        from sca_data.models import GoldCosts

        instance = GoldCosts(**valid_data, id=1)
        data = GoldCostsSerializer(instance).data

        assert data["data"] == "2024-01-15"

    def test_id_is_included_in_output(self, valid_data):
        from sca_data.models import GoldCosts

        instance = GoldCosts(**valid_data, id=42)
        data = GoldCostsSerializer(instance).data

        assert data["id"] == 42
