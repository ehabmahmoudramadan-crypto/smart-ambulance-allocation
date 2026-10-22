from data import (
    SUPPLY,
    DEMAND,
    COST_MATRIX,
    DATA_IS_SYNTHETIC,
    validate_data,
    calculate_current_cost
)


def test_default_data():
    assert validate_data() is True


def test_supply_equals_demand():
    assert sum(SUPPLY) == sum(DEMAND)


def test_cost_matrix_dimensions():
    assert len(COST_MATRIX) == 4
    assert all(len(row) == 5 for row in COST_MATRIX)


def test_current_allocation_cost():
    assert calculate_current_cost() == 846


def test_data_is_synthetic():
    assert DATA_IS_SYNTHETIC is True
