import copy
import os

import pytest

import data
import solver
from app import app

OPTIMAL = [
    [5, 0, 0, 3, 0],
    [0, 6, 0, 0, 0],
    [0, 1, 0, 0, 6],
    [0, 0, 6, 3, 0],
]

NORTHWEST = [
    [5, 3, 0, 0, 0],
    [0, 4, 2, 0, 0],
    [0, 0, 4, 3, 0],
    [0, 0, 0, 3, 6],
]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def fake_algorithms(monkeypatch):
    monkeypatch.setattr(
        solver,
        "vogel_approximation",
        lambda supply, demand, costs: {"allocation": NORTHWEST, "steps": []},
    )
    monkeypatch.setattr(
        solver,
        "modi_optimize",
        lambda supply, demand, costs, initial: {
            "allocation": OPTIMAL,
            "iterations": 3,
            "is_optimal": True,
        },
    )


def valid_payload():
    return {
        "supply": list(data.SUPPLY),
        "demand": list(data.DEMAND),
        "cost_matrix": copy.deepcopy(data.COST_MATRIX),
        "current_allocation": copy.deepcopy(data.CURRENT_ALLOCATION),
    }


def changed(edit):
    payload = valid_payload()
    edit(payload)
    return payload


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_api_data(client):
    body = client.get("/api/data").get_json()
    assert body["current_cost"] == 846
    assert body["stations"] == ["S1", "S2", "S3", "S4"]
    assert body["areas"] == ["A1", "A2", "A3", "A4", "A5"]
    assert body["data_is_synthetic"] is True


def test_home_returns_json_for_programs(client):
    assert client.get("/").get_json()["current_cost"] == 846


@pytest.mark.skipif(
    not os.path.exists(os.path.join(app.root_path, "templates", "index.html")),
    reason="index.html not found",
)
def test_home_returns_html_for_browsers(client):
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "text/html" in response.content_type


def test_unknown_api_path(client):
    response = client.get("/api/unknown")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_get_on_solve_is_not_allowed(client):
    response = client.get("/api/solve")
    assert response.status_code == 405
    assert "error" in response.get_json()


def test_solve_default_data_with_real_algorithms(client):
    response = client.post("/api/solve")
    assert response.status_code == 200
    body = response.get_json()
    assert body["data_source"] == "default"
    assert body["initial"]["cost"] == 702
    assert body["optimal"]["cost"] == 690
    assert body["optimal"]["is_optimal"] is True
    assert body["current"]["cost"] == 846
    assert body["comparison"]["saving"] == 156
    assert body["comparison"]["saving_percent"] == 18.44
    assert body["warnings"] == []
    assert len(body["initial"]["steps"]) > 0
    assert len(body["optimal"]["potentials_u"]) == 4
    assert len(body["optimal"]["potentials_v"]) == 5


def test_real_solution_satisfies_supply_and_demand(client):
    body = client.post("/api/solve").get_json()
    allocation = body["optimal"]["allocation"]
    assert [sum(row) for row in allocation] == data.SUPPLY
    assert [sum(row[j] for row in allocation) for j in range(5)] == data.DEMAND


def test_solve_with_custom_data(client):
    payload = {
        "supply": [10, 20],
        "demand": [15, 15],
        "cost_matrix": [[1, 4], [3, 2]],
    }
    body = client.post("/api/solve", json=payload).get_json()
    assert body["data_source"] == "user"
    assert body["optimal"]["cost"] == 55
    assert body["current"] is None
    assert body["comparison"] is None


def test_use_default_data_flag(client):
    body = client.post("/api/solve", json={"use_default_data": True}).get_json()
    assert body["data_source"] == "default"
    assert body["optimal"]["cost"] == 690


def test_solve_with_fake_algorithms(client, fake_algorithms):
    body = client.post("/api/solve").get_json()
    assert body["initial"]["cost"] == 888
    assert body["optimal"]["cost"] == 690
    assert body["optimal"]["iterations"] == 3


def test_changes_list_only_contains_changed_cells(client, fake_algorithms):
    comparison = client.post("/api/solve").get_json()["comparison"]
    assert comparison["changes"]
    for change in comparison["changes"]:
        assert change["delta"] == change["proposed"] - change["current"]
        assert change["delta"] != 0
    assert comparison["delta_matrix"][0][0] == 2


def test_whole_number_floats_are_accepted(client):
    payload = valid_payload()
    payload["supply"] = [8.0, 6.0, 7.0, 9.0]
    assert client.post("/api/solve", json=payload).status_code == 200


def test_algorithm_cannot_change_request_data(client, monkeypatch):
    def vam(supply, demand, costs):
        supply[0] = 999
        costs[0][0] = 999
        return {"allocation": NORTHWEST}

    monkeypatch.setattr(solver, "vogel_approximation", vam)
    monkeypatch.setattr(
        solver, "modi_optimize", lambda s, d, c, i: {"allocation": OPTIMAL}
    )
    body = client.post("/api/solve").get_json()
    assert body["problem"]["supply"] == [8, 6, 7, 9]
    assert body["optimal"]["cost"] == 690


BAD_INPUTS = [
    ("missing_costs", changed(lambda p: p.pop("cost_matrix")), "MISSING_FIELDS"),
    ("unbalanced", changed(lambda p: p.update(demand=[6, 7, 6, 6, 6])), "UNBALANCED"),
    ("negative_supply", changed(lambda p: p["supply"].__setitem__(0, -1)), "NEGATIVE_VALUE"),
    ("fractional_supply", changed(lambda p: p["supply"].__setitem__(0, 8.5)), "NOT_AN_INTEGER"),
    ("text_supply", changed(lambda p: p["supply"].__setitem__(0, "8")), "NOT_A_NUMBER"),
    ("boolean_supply", changed(lambda p: p["supply"].__setitem__(0, True)), "NOT_A_NUMBER"),
    ("empty_supply", changed(lambda p: p.update(supply=[])), "INVALID_VECTOR"),
    ("supply_not_a_list", changed(lambda p: p.update(supply=8)), "INVALID_VECTOR"),
    ("negative_cost", changed(lambda p: p["cost_matrix"][1].__setitem__(2, -5)), "NEGATIVE_VALUE"),
    ("text_cost", changed(lambda p: p["cost_matrix"][1].__setitem__(2, "x")), "NOT_A_NUMBER"),
    ("missing_cost_row", changed(lambda p: p["cost_matrix"].pop()), "INVALID_COST_MATRIX"),
    ("short_cost_row", changed(lambda p: p["cost_matrix"][0].pop()), "INVALID_COST_MATRIX"),
    ("current_row_total", changed(lambda p: p["current_allocation"][0].__setitem__(0, 4)), "CURRENT_ALLOCATION_MISMATCH"),
    ("current_shape", changed(lambda p: p.update(current_allocation=[[1, 2]])), "INVALID_CURRENT_ALLOCATION"),
    ("too_many_stations", {"supply": [1] * 21, "demand": [21], "cost_matrix": [[1]] * 21}, "TOO_LARGE"),
    ("no_vehicles", {"supply": [0], "demand": [0], "cost_matrix": [[1]]}, "EMPTY_PROBLEM"),
    ("body_is_list", [1, 2, 3], "INVALID_BODY"),
]


@pytest.mark.parametrize("payload,code", [b[1:] for b in BAD_INPUTS], ids=[b[0] for b in BAD_INPUTS])
def test_bad_input_is_rejected(client, payload, code):
    response = client.post("/api/solve", json=payload)
    assert response.status_code == 400
    body = response.get_json()
    assert body["code"] == code
    assert body["error"]


def test_nan_cost_is_rejected(client):
    raw = '{"supply":[1],"demand":[1],"cost_matrix":[[NaN]]}'
    response = client.post("/api/solve", data=raw, content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["code"] == "NOT_A_NUMBER"


def test_invalid_json_is_rejected(client):
    response = client.post("/api/solve", data="{broken", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["code"] == "INVALID_JSON"


def test_unbalanced_error_includes_totals(client):
    payload = changed(lambda p: p.update(demand=[6, 7, 6, 6, 6]))
    body = client.post("/api/solve", json=payload).get_json()
    assert body["details"] == {"total_supply": 30, "total_demand": 31}


def test_algorithm_exception_is_reported(client, monkeypatch):
    def crash(supply, demand, costs):
        raise ZeroDivisionError("division by zero")

    monkeypatch.setattr(solver, "vogel_approximation", crash)
    response = client.post("/api/solve")
    assert response.status_code == 500
    assert response.get_json()["code"] == "ALGORITHM_FAILED"


def test_infeasible_algorithm_result_is_rejected(client, monkeypatch):
    broken = copy.deepcopy(NORTHWEST)
    broken[0][0] += 1
    monkeypatch.setattr(
        solver, "vogel_approximation", lambda s, d, c: {"allocation": broken}
    )
    response = client.post("/api/solve")
    assert response.status_code == 500
    assert response.get_json()["code"] == "ALGORITHM_INFEASIBLE"


def test_fractional_algorithm_result_is_rejected(client, monkeypatch):
    fractional = [[float(v) for v in row] for row in NORTHWEST]
    fractional[0][0] -= 0.5
    fractional[1][0] += 0.5
    monkeypatch.setattr(
        solver, "vogel_approximation", lambda s, d, c: {"allocation": fractional}
    )
    assert client.post("/api/solve").get_json()["code"] == "ALGORITHM_INFEASIBLE"


def test_epsilon_values_are_treated_as_zero(client, monkeypatch):
    values = [[float(v) for v in row] for row in OPTIMAL]
    values[0][1] = 1e-9
    monkeypatch.setattr(
        solver, "vogel_approximation", lambda s, d, c: {"allocation": NORTHWEST}
    )
    monkeypatch.setattr(
        solver, "modi_optimize", lambda s, d, c, i: {"allocation": values}
    )
    body = client.post("/api/solve").get_json()
    assert body["optimal"]["allocation"][0][1] == 0
    assert body["optimal"]["cost"] == 690


def test_modi_worse_than_vam_is_rejected(client, monkeypatch):
    monkeypatch.setattr(
        solver, "vogel_approximation", lambda s, d, c: {"allocation": OPTIMAL}
    )
    monkeypatch.setattr(
        solver, "modi_optimize", lambda s, d, c, i: {"allocation": NORTHWEST}
    )
    assert client.post("/api/solve").get_json()["code"] == "ALGORITHM_WORSE_THAN_INITIAL"


def test_wrong_reported_cost_creates_warning(client, monkeypatch):
    monkeypatch.setattr(
        solver, "vogel_approximation", lambda s, d, c: {"allocation": NORTHWEST}
    )
    monkeypatch.setattr(
        solver,
        "modi_optimize",
        lambda s, d, c, i: {"allocation": OPTIMAL, "total_cost": 702},
    )
    body = client.post("/api/solve").get_json()
    assert body["optimal"]["cost"] == 690
    assert len(body["warnings"]) == 1
