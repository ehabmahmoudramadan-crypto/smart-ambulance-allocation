import copy
import sys
import types

import pytest

import data
import solver
from algorithms.modi import modi_method, solve_constrained_transport
from algorithms.vam import vogel_approximation
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def use_algorithms(monkeypatch):
    def apply(vam, modi=modi_method, constrained=solve_constrained_transport):
        monkeypatch.setattr(solver, "load_algorithms", lambda: (vam, modi, constrained))

    return apply


def start_from_current(supply, demand, costs, closed_routes=None, route_capacities=None):
    return copy.deepcopy(data.CURRENT_DISTRIBUTION), 2097, []


def no_start(supply, demand, costs, closed_routes=None, route_capacities=None):
    return None, None, []


def small_payload(**extra):
    payload = {
        "supply": [10, 20],
        "demand": [15, 15],
        "cost_matrix": [[1, 4], [3, 2]],
    }
    payload.update(extra)
    return payload


def default_request():
    return {"use_default_data": True}


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_existing_endpoints_still_work(client):
    assert client.get("/api/data").status_code == 200
    assert client.get("/api/validate").status_code == 200
    assert client.get("/api/cost/current").get_json()["cost"] == 2097
    assert client.get("/api/cost/optimal-reference").get_json()["cost"] == 1111
    assert client.get("/").get_json()["message"] == "Smart Ambulance Allocation API"


def test_unknown_api_path(client):
    response = client.get("/api/unknown")
    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_get_on_solve_is_not_allowed(client):
    response = client.get("/api/solve")
    assert response.status_code == 405
    assert "error" in response.get_json()


def test_default_problem_reaches_reference_optimum(client, use_algorithms):
    use_algorithms(start_from_current)
    response = client.post("/api/solve")
    assert response.status_code == 200
    body = response.get_json()
    assert body["data_source"] == "default"
    assert body["initial"]["cost"] == 2097
    assert body["optimal"]["cost"] == 1111
    assert body["current"]["cost"] == 2097
    assert body["comparison"]["saving"] == 986
    assert body["comparison"]["saving_percent"] == 47.02
    assert body["warnings"] == []


def test_default_solution_respects_both_restrictions(client, use_algorithms):
    use_algorithms(start_from_current)
    body = client.post("/api/solve").get_json()
    allocation = body["optimal"]["allocation"]
    stations = body["problem"]["stations"]
    areas = body["problem"]["areas"]
    assert allocation[stations.index("S2")][areas.index("A7")] == 0
    assert allocation[stations.index("S5")][areas.index("A9")] <= 5
    assert body["constraints"]["closed_routes"] == [{"from": "S2", "to": "A7"}]
    capacity = body["constraints"]["route_capacities"][0]
    assert (capacity["from"], capacity["to"], capacity["max"]) == ("S5", "A9", 5)
    assert capacity["used"] == 5


def test_default_solution_satisfies_supply_and_demand(client, use_algorithms):
    use_algorithms(start_from_current)
    allocation = client.post("/api/solve").get_json()["optimal"]["allocation"]
    assert [sum(row) for row in allocation] == data.SUPPLY
    assert [sum(row[j] for row in allocation) for j in range(12)] == data.DEMAND


def test_use_default_data_flag(client, use_algorithms):
    use_algorithms(start_from_current)
    body = client.post("/api/solve", json=default_request()).get_json()
    assert body["data_source"] == "default"
    assert body["optimal"]["cost"] == 1111


def test_missing_initial_solution_falls_back_with_warning(client, use_algorithms):
    use_algorithms(no_start)
    body = client.post("/api/solve").get_json()
    assert body["initial"] is None
    assert body["optimal"]["cost"] == 1111
    assert body["optimal"]["improvement"] is None
    assert len(body["warnings"]) == 1


def test_custom_problem_without_restrictions(client, use_algorithms):
    use_algorithms(no_start)
    body = client.post("/api/solve", json=small_payload()).get_json()
    assert body["data_source"] == "user"
    assert body["optimal"]["cost"] == 55
    assert body["current"] is None
    assert body["comparison"] is None
    assert body["problem"]["stations"] == ["S1", "S2"]


def test_custom_names_and_restrictions(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload(
        stations=["North", "South"],
        areas=["Old Town", "Harbor"],
        closed_routes=[{"from": "North", "to": "Old Town"}],
    )
    body = client.post("/api/solve", json=payload).get_json()
    assert body["optimal"]["allocation"][0][0] == 0
    assert body["constraints"]["closed_routes"] == [{"from": "North", "to": "Old Town"}]
    assert body["optimal"]["cost"] > 55


def test_capacity_limit_changes_the_cost(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload(route_capacities=[{"from": "S1", "to": "A1", "max": 4}])
    body = client.post("/api/solve", json=payload).get_json()
    assert body["optimal"]["allocation"][0][0] <= 4
    assert body["constraints"]["route_capacities"][0]["used"] == 4
    assert body["optimal"]["cost"] == 79


def test_closed_route_overrides_capacity(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload(
        closed_routes=[{"from": "S1", "to": "A1"}],
        route_capacities=[{"from": "S1", "to": "A1", "max": 5}],
    )
    body = client.post("/api/solve", json=payload).get_json()
    assert body["optimal"]["allocation"][0][0] == 0


def test_impossible_restrictions_return_clear_error(client, use_algorithms):
    use_algorithms(no_start)
    payload = {
        "supply": [2],
        "demand": [2],
        "cost_matrix": [[1]],
        "closed_routes": [{"from": "S1", "to": "A1"}],
    }
    response = client.post("/api/solve", json=payload)
    assert response.status_code == 422
    assert response.get_json()["code"] == "NO_FEASIBLE_SOLUTION"


def test_current_allocation_breaking_a_restriction_gives_warning(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload(
        current_distribution=[[10, 0], [5, 15]],
        closed_routes=[{"from": "S1", "to": "A1"}],
    )
    body = client.post("/api/solve", json=payload).get_json()
    assert any("Current allocation" in w for w in body["warnings"])
    assert body["comparison"]["saving"] == -40


def test_old_current_allocation_key_is_accepted(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload(current_allocation=[[10, 0], [5, 15]])
    assert client.post("/api/solve", json=payload).get_json()["current"]["cost"] == 55


def test_changes_list_only_contains_changed_cells(client, use_algorithms):
    use_algorithms(start_from_current)
    comparison = client.post("/api/solve").get_json()["comparison"]
    assert comparison["changes"]
    for change in comparison["changes"]:
        assert change["delta"] == change["proposed"] - change["current"]
        assert change["delta"] != 0


def test_whole_number_floats_are_accepted(client, use_algorithms):
    use_algorithms(no_start)
    payload = small_payload()
    payload["supply"] = [10.0, 20.0]
    assert client.post("/api/solve", json=payload).status_code == 200


def test_algorithm_cannot_change_request_data(client, use_algorithms):
    def vam(supply, demand, costs, closed_routes=None, route_capacities=None):
        supply[0] = 999
        costs[0][0] = 999
        return None, None, []

    use_algorithms(vam)
    body = client.post("/api/solve", json=small_payload()).get_json()
    assert body["problem"]["supply"] == [10, 20]
    assert body["optimal"]["cost"] == 55


def mutate(edit, base=None):
    payload = base if base is not None else small_payload(current_distribution=[[10, 0], [5, 15]])
    edit(payload)
    return payload


BAD_INPUTS = [
    ("missing_costs", mutate(lambda p: p.pop("cost_matrix")), "MISSING_FIELDS"),
    ("unbalanced", mutate(lambda p: p.update(demand=[16, 15])), "UNBALANCED"),
    ("negative_supply", mutate(lambda p: p["supply"].__setitem__(0, -1)), "NEGATIVE_VALUE"),
    ("fractional_supply", mutate(lambda p: p["supply"].__setitem__(0, 8.5)), "NOT_AN_INTEGER"),
    ("text_supply", mutate(lambda p: p["supply"].__setitem__(0, "8")), "NOT_A_NUMBER"),
    ("boolean_supply", mutate(lambda p: p["supply"].__setitem__(0, True)), "NOT_A_NUMBER"),
    ("empty_supply", mutate(lambda p: p.update(supply=[])), "INVALID_VECTOR"),
    ("supply_not_a_list", mutate(lambda p: p.update(supply=8)), "INVALID_VECTOR"),
    ("negative_cost", mutate(lambda p: p["cost_matrix"][1].__setitem__(1, -5)), "NEGATIVE_VALUE"),
    ("text_cost", mutate(lambda p: p["cost_matrix"][1].__setitem__(1, "x")), "NOT_A_NUMBER"),
    ("missing_cost_row", mutate(lambda p: p["cost_matrix"].pop()), "INVALID_COST_MATRIX"),
    ("short_cost_row", mutate(lambda p: p["cost_matrix"][0].pop()), "INVALID_COST_MATRIX"),
    ("current_row_total", mutate(lambda p: p["current_distribution"][0].__setitem__(0, 9)), "CURRENT_ALLOCATION_MISMATCH"),
    ("current_shape", mutate(lambda p: p.update(current_distribution=[[1, 2]])), "INVALID_CURRENT_ALLOCATION"),
    ("too_many_stations", {"supply": [1] * 21, "demand": [21], "cost_matrix": [[1]] * 21}, "TOO_LARGE"),
    ("no_vehicles", {"supply": [0], "demand": [0], "cost_matrix": [[1]]}, "EMPTY_PROBLEM"),
    ("body_is_list", [1, 2, 3], "INVALID_BODY"),
    ("labels_wrong_size", mutate(lambda p: p.update(stations=["A"])), "INVALID_LABELS"),
    ("labels_not_text", mutate(lambda p: p.update(stations=["A", 5])), "INVALID_LABELS"),
    ("labels_duplicate", mutate(lambda p: p.update(areas=["X", "X"])), "DUPLICATE_LABELS"),
    ("closed_route_not_a_list", mutate(lambda p: p.update(closed_routes="S1")), "INVALID_ROUTE"),
    ("closed_route_bad_shape", mutate(lambda p: p.update(closed_routes=[["S1", "A1"]])), "INVALID_ROUTE"),
    ("closed_route_unknown_station", mutate(lambda p: p.update(closed_routes=[{"from": "S9", "to": "A1"}])), "INVALID_ROUTE"),
    ("closed_route_unknown_area", mutate(lambda p: p.update(closed_routes=[{"from": "S1", "to": "A9"}])), "INVALID_ROUTE"),
    ("closed_route_twice", mutate(lambda p: p.update(closed_routes=[{"from": "S1", "to": "A1"}] * 2)), "DUPLICATE_ROUTE"),
    ("capacity_negative", mutate(lambda p: p.update(route_capacities=[{"from": "S1", "to": "A1", "max": -1}])), "NEGATIVE_VALUE"),
    ("capacity_fractional", mutate(lambda p: p.update(route_capacities=[{"from": "S1", "to": "A1", "max": 0.5}])), "NOT_AN_INTEGER"),
    ("capacity_boolean", mutate(lambda p: p.update(route_capacities=[{"from": "S1", "to": "A1", "max": True}])), "NOT_A_NUMBER"),
    ("capacity_missing_max", mutate(lambda p: p.update(route_capacities=[{"from": "S1", "to": "A1"}])), "NOT_A_NUMBER"),
    ("capacity_twice", mutate(lambda p: p.update(route_capacities=[{"from": "S1", "to": "A1", "max": 1}] * 2)), "DUPLICATE_ROUTE"),
]


@pytest.mark.parametrize("payload,code", [b[1:] for b in BAD_INPUTS], ids=[b[0] for b in BAD_INPUTS])
def test_bad_input_is_rejected(client, use_algorithms, payload, code):
    use_algorithms(no_start)
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
    payload = small_payload(demand=[16, 15])
    body = client.post("/api/solve", json=payload).get_json()
    assert body["details"] == {"total_supply": 30, "total_demand": 31}


def test_unavailable_algorithms_return_501(client, monkeypatch):
    monkeypatch.setitem(sys.modules, "algorithms.vam", types.ModuleType("algorithms.vam"))
    response = client.post("/api/solve")
    assert response.status_code == 501
    assert response.get_json()["code"] == "ALGORITHMS_UNAVAILABLE"


def test_algorithm_exception_is_reported(client, use_algorithms):
    def crash(*args, **kwargs):
        raise ZeroDivisionError("division by zero")

    use_algorithms(crash)
    response = client.post("/api/solve")
    assert response.status_code == 500
    assert response.get_json()["code"] == "ALGORITHM_FAILED"


def test_infeasible_vam_result_is_rejected(client, use_algorithms):
    def broken(*args, **kwargs):
        allocation = copy.deepcopy(data.CURRENT_DISTRIBUTION)
        allocation[0][0] += 1
        return allocation, None, []

    use_algorithms(broken)
    response = client.post("/api/solve")
    assert response.status_code == 500
    assert response.get_json()["code"] == "ALGORITHM_INFEASIBLE"


def test_vam_result_using_a_closed_route_is_rejected(client, use_algorithms):
    def bad_but_balanced(*args, **kwargs):
        allocation = copy.deepcopy(data.CURRENT_DISTRIBUTION)
        allocation[1][8] -= 1
        allocation[1][6] += 1
        allocation[6][6] -= 1
        allocation[6][8] += 1
        return allocation, None, []

    use_algorithms(bad_but_balanced)
    response = client.post("/api/solve")
    assert response.status_code == 500
    assert response.get_json()["code"] == "ALGORITHM_VIOLATES_RESTRICTIONS"


def test_fractional_modi_result_is_rejected(client, use_algorithms):
    def fractional(*args, **kwargs):
        allocation = [[float(v) for v in row] for row in data.OPTIMAL_DISTRIBUTION]
        allocation[0][8] -= 0.5
        allocation[4][8] += 0.5
        return {"allocation": allocation}

    use_algorithms(start_from_current, modi=fractional)
    assert client.post("/api/solve").get_json()["code"] == "ALGORITHM_INFEASIBLE"


def test_epsilon_values_are_treated_as_zero(client, use_algorithms):
    def with_epsilon(*args, **kwargs):
        allocation = [[float(v) for v in row] for row in data.OPTIMAL_DISTRIBUTION]
        allocation[0][0] = 1e-9
        return {"allocation": allocation, "method": "stub"}

    use_algorithms(start_from_current, modi=with_epsilon)
    body = client.post("/api/solve").get_json()
    assert body["optimal"]["allocation"][0][0] == 0
    assert body["optimal"]["cost"] == 1111


def test_modi_worse_than_vam_is_rejected(client, use_algorithms):
    def optimal_start(*args, **kwargs):
        return copy.deepcopy(data.OPTIMAL_DISTRIBUTION), None, []

    def worse(*args, **kwargs):
        return {"allocation": copy.deepcopy(data.CURRENT_DISTRIBUTION)}

    use_algorithms(optimal_start, modi=worse)
    assert client.post("/api/solve").get_json()["code"] == "ALGORITHM_WORSE_THAN_INITIAL"


def test_wrong_reported_cost_creates_warning(client, use_algorithms):
    def wrong_cost(*args, **kwargs):
        return {"allocation": copy.deepcopy(data.OPTIMAL_DISTRIBUTION), "cost": 1000}

    use_algorithms(start_from_current, modi=wrong_cost)
    body = client.post("/api/solve").get_json()
    assert body["optimal"]["cost"] == 1111
    assert len(body["warnings"]) == 1


def test_real_algorithms_on_default_data(client):
    response = client.post("/api/solve")
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["initial"]["method"] == "VAM"
    assert body["initial"]["cost"] == 1257
    assert len(body["initial"]["steps"]) == 18
    assert body["optimal"]["cost"] == 1111
    assert body["optimal"]["solver"] == "MODI (u-v method)"
    assert body["optimal"]["is_optimal"] is True
    assert body["optimal"]["iterations"] > 0
    assert body["optimal"]["improvement"] == 146
    assert len(body["optimal"]["potentials_u"]) == 8
    assert len(body["optimal"]["potentials_v"]) == 12
    assert len(body["optimal"]["reduced_costs"]) == 8
    assert body["current"]["cost"] == 2097
    assert body["comparison"]["saving"] == 986
    assert body["warnings"] == []


def test_real_algorithms_without_restrictions(client):
    payload = {
        "supply": [8, 6, 7, 9],
        "demand": [5, 7, 6, 6, 6],
        "cost_matrix": [
            [24, 45, 37, 18, 19],
            [28, 36, 37, 13, 23],
            [45, 39, 31, 42, 15],
            [26, 42, 19, 19, 18],
        ],
    }
    body = client.post("/api/solve", json=payload).get_json()
    assert body["initial"]["cost"] == 702
    assert body["optimal"]["cost"] == 690
    assert body["constraints"] == {"closed_routes": [], "route_capacities": []}


def test_real_algorithms_when_vam_cannot_start(client):
    payload = {
        "supply": [8, 6, 7, 9],
        "demand": [5, 7, 6, 6, 6],
        "cost_matrix": [
            [24, 45, 37, 18, 19],
            [28, 36, 37, 13, 23],
            [45, 39, 31, 42, 15],
            [26, 42, 19, 19, 18],
        ],
        "closed_routes": [{"from": "S2", "to": "A4"}],
        "route_capacities": [{"from": "S1", "to": "A4", "max": 1}],
    }
    body = client.post("/api/solve", json=payload).get_json()
    assert body["initial"] is None
    assert len(body["warnings"]) == 1
    allocation = body["optimal"]["allocation"]
    assert allocation[1][3] == 0
    assert allocation[0][3] <= 1
    expected = solve_constrained_transport(
        payload["supply"], payload["demand"], payload["cost_matrix"],
        [(1, 3)], {(0, 3): 1},
    )
    assert body["optimal"]["cost"] == expected["cost"]
