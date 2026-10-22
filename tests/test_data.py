
import pytest

from data import (
    SUPPLY,
    DEMAND,
    COST_MATRIX,
    CURRENT_ALLOCATION,
    DATA_IS_SYNTHETIC,
    validate_data,
    calculate_current_cost
)


def test_default_data():
    assert validate_data() is True


def test_supply_equals_demand():
    assert sum(SUPPLY) == sum(DEMAND) == 30


def test_cost_matrix_dimensions():
    assert len(COST_MATRIX) == 4
    assert all(len(row) == 5 for row in COST_MATRIX)


def test_current_allocation_dimensions():
    assert len(CURRENT_ALLOCATION) == len(SUPPLY)
    assert all(len(row) == len(DEMAND)
               for row in CURRENT_ALLOCATION)


def test_current_allocation_cost():
    assert calculate_current_cost() == 846


def test_data_is_synthetic():
    assert DATA_IS_SYNTHETIC is True


def test_invalid_allocation_dimensions(monkeypatch):
    import data

    monkeypatch.setattr(
        data, "CURRENT_ALLOCATION", [[1, 2]]
    )

    assert data.validate_data() is False


def test_negative_cost(monkeypatch):
    import data

    matrix = [row[:] for row in data.COST_MATRIX]
    matrix[0][0] = -1

    monkeypatch.setattr(data, "COST_MATRIX", matrix)

    assert data.validate_data() is False


def test_invalid_allocation_value(monkeypatch):
    import data

    allocation = [
        row[:] for row in data.CURRENT_ALLOCATION
    ]
    allocation[0][0] = -1

    monkeypatch.setattr(
        data, "CURRENT_ALLOCATION", allocation
    )

    assert data.validate_data() is False


def test_unbalanced_data(monkeypatch):
    import data

    monkeypatch.setattr(
        data, "DEMAND", [6, 7, 6, 6, 6]
    )

    assert data.validate_data() is False


def test_api_endpoints():
    from app import app

    client = app.test_client()

    response_home = client.get("/")
    response_data = client.get("/api/data")

    assert response_home.status_code == 200
    assert response_data.status_code == 200

    assert response_home.get_json()["current_cost"] == 846
    assert response_data.get_json()["current_cost"] == 846

    assert response_data.get_json()["data_is_synthetic"] is True
