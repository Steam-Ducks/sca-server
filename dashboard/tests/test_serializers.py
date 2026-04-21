# dashboard/tests/test_serializers.py
from dashboard.serializers import DashboardKPIsSerializer


def test_serializer_validates_correct_data():
    data = {
        "total_consolidated_cost": 750000.00,
        "total_materials_cost":    450000.00,
        "total_hours_cost":        300000.00,
        "total_projects":          8,
        "total_programs":          3,
    }
    serializer = DashboardKPIsSerializer(data)

    assert serializer.data["total_consolidated_cost"] == 750000.00
    assert serializer.data["total_materials_cost"]    == 450000.00
    assert serializer.data["total_hours_cost"]        == 300000.00
    assert serializer.data["total_projects"]          == 8
    assert serializer.data["total_programs"]          == 3


def test_serializer_contains_all_fields():
    data = {
        "total_consolidated_cost": 0.0,
        "total_materials_cost":    0.0,
        "total_hours_cost":        0.0,
        "total_projects":          0,
        "total_programs":          0,
    }
    serializer = DashboardKPIsSerializer(data)
    fields = serializer.data.keys()

    assert "total_consolidated_cost" in fields
    assert "total_materials_cost" in fields
    assert "total_hours_cost" in fields
    assert "total_projects" in fields
    assert "total_programs" in fields


def test_serializer_cost_fields_are_float():
    data = {
        "total_consolidated_cost": 123456.78,
        "total_materials_cost":    100000.00,
        "total_hours_cost":        23456.78,
        "total_projects":          5,
        "total_programs":          2,
    }
    serializer = DashboardKPIsSerializer(data)

    assert isinstance(serializer.data["total_consolidated_cost"], float)
    assert isinstance(serializer.data["total_materials_cost"], float)
    assert isinstance(serializer.data["total_hours_cost"], float)


def test_serializer_count_fields_are_integer():
    data = {
        "total_consolidated_cost": 0.0,
        "total_materials_cost":    0.0,
        "total_hours_cost":        0.0,
        "total_projects":          4,
        "total_programs":          2,
    }
    serializer = DashboardKPIsSerializer(data)

    assert isinstance(serializer.data["total_projects"], int)
    assert isinstance(serializer.data["total_programs"], int)
    