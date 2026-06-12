from budget.serializers import BudgetIndicatorsSerializer


def _make_indicators(**overrides):
    base = {
        "budget_total": 15000.0,
        "custo_real_total": 10500.0,
        "desvio_percent_medio": 65.3,
        "projetos_saudaveis": 3,
        "projetos_atencao": 2,
        "projetos_criticos": 1,
    }
    base.update(overrides)
    return base


def test_serializer_maps_snake_case_to_camel_case():
    data = BudgetIndicatorsSerializer(_make_indicators()).data

    assert "budgetTotal" in data
    assert "custoRealTotal" in data
    assert "desvioPercentMedio" in data
    assert "projetosSaudaveis" in data
    assert "projetosAtencao" in data
    assert "projetosCriticos" in data


def test_serializer_returns_correct_values():
    data = BudgetIndicatorsSerializer(_make_indicators()).data

    assert data["budgetTotal"] == 15000.0
    assert data["custoRealTotal"] == 10500.0
    assert data["desvioPercentMedio"] == 65.3
    assert data["projetosSaudaveis"] == 3
    assert data["projetosAtencao"] == 2
    assert data["projetosCriticos"] == 1


def test_serializer_with_zero_values():
    indicators = _make_indicators(
        budget_total=0.0,
        custo_real_total=0.0,
        desvio_percent_medio=0.0,
        projetos_saudaveis=0,
        projetos_atencao=0,
        projetos_criticos=0,
    )
    data = BudgetIndicatorsSerializer(indicators).data

    assert data["budgetTotal"] == 0.0
    assert data["projetosSaudaveis"] == 0
    assert data["projetosCriticos"] == 0


def test_serializer_handles_float_precision():
    indicators = _make_indicators(
        budget_total=12345.678,
        desvio_percent_medio=72.123,
    )
    data = BudgetIndicatorsSerializer(indicators).data

    assert data["budgetTotal"] == 12345.678
    assert data["desvioPercentMedio"] == 72.123
