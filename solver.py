import copy

from algorithms.modi import modi_optimize
from algorithms.vam import vogel_approximation
from errors import SolverError
from validation import area_name, station_name

EPS = 1e-6


def clean_number(value):
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def total_cost(allocation, costs):
    return clean_number(
        sum(
            allocation[i][j] * costs[i][j]
            for i in range(len(allocation))
            for j in range(len(allocation[i]))
        )
    )


def run_stage(stage, func, *args):
    try:
        return func(*copy.deepcopy(args))
    except Exception as exc:
        raise SolverError(
            f"Failed to run {stage}.",
            "ALGORITHM_FAILED",
            details={"reason": str(exc)},
        ) from exc


def check_allocation(stage, allocation, supply, demand):
    m, n = len(supply), len(demand)
    if not isinstance(allocation, list) or len(allocation) != m:
        raise SolverError(f"The {stage} result has invalid dimensions.", "ALGORITHM_INFEASIBLE")

    clean = []
    for i, row in enumerate(allocation):
        if len(row) != n:
            raise SolverError(f"The {stage} result has invalid dimensions.", "ALGORITHM_INFEASIBLE")
        clean_row = []
        for j, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
                raise SolverError(
                    f"The {stage} result contains a non-numeric value.", "ALGORITHM_BAD_OUTPUT"
                )
            if abs(value - round(value)) > EPS:
                raise SolverError(
                    f"The {stage} result contains a non-integer value at {station_name(i)}, {area_name(j)}.",
                    "ALGORITHM_INFEASIBLE",
                )
            value = int(round(value))
            if value < 0:
                raise SolverError(
                    f"The {stage} result contains a negative value at {station_name(i)}, {area_name(j)}.",
                    "ALGORITHM_INFEASIBLE",
                )
            clean_row.append(value)
        clean.append(clean_row)

    for i in range(m):
        if sum(clean[i]) != supply[i]:
            raise SolverError(
                f"The {stage} result: row {station_name(i)} does not add up to its supply.",
                "ALGORITHM_INFEASIBLE",
            )
    for j in range(n):
        if sum(clean[i][j] for i in range(m)) != demand[j]:
            raise SolverError(
                f"The {stage} result: column {area_name(j)} does not add up to its demand.",
                "ALGORITHM_INFEASIBLE",
            )
    return clean


def finish_stage(stage, result, supply, demand, costs, warnings):
    if not isinstance(result, dict) or "allocation" not in result:
        raise SolverError(f"The {stage} result is incomplete.", "ALGORITHM_BAD_OUTPUT")
    allocation = check_allocation(stage, result["allocation"], supply, demand)
    cost = total_cost(allocation, costs)
    reported = result.get("total_cost")
    if isinstance(reported, (int, float)) and abs(reported - cost) > EPS:
        warnings.append(
            f"The {stage} reported cost ({reported}) differs from the cost computed from the matrix ({cost})."
        )
    return allocation, cost


def round_matrix(matrix):
    return [[clean_number(v) for v in row] for row in matrix]


def compare(current, proposed):
    m, n = len(proposed), len(proposed[0])
    delta = [[proposed[i][j] - current[i][j] for j in range(n)] for i in range(m)]
    changes = [
        {
            "station": station_name(i),
            "area": area_name(j),
            "current": current[i][j],
            "proposed": proposed[i][j],
            "delta": delta[i][j],
        }
        for i in range(m)
        for j in range(n)
        if delta[i][j] != 0
    ]
    return delta, changes


def solve(problem):
    supply = problem["supply"]
    demand = problem["demand"]
    costs = problem["cost_matrix"]
    warnings = []

    vam_result = run_stage("VAM", vogel_approximation, supply, demand, costs)
    initial_allocation, initial_cost = finish_stage(
        "VAM", vam_result, supply, demand, costs, warnings
    )

    modi_result = run_stage("MODI", modi_optimize, supply, demand, costs, initial_allocation)
    final_allocation, final_cost = finish_stage(
        "MODI", modi_result, supply, demand, costs, warnings
    )

    if final_cost > initial_cost + EPS:
        raise SolverError(
            "The MODI result costs more than the initial solution.", "ALGORITHM_WORSE_THAN_INITIAL"
        )

    steps = [
        {
            "step": k + 1,
            "station": station_name(s["row"]),
            "area": area_name(s["column"]),
            "quantity": s["quantity"],
            "unit_cost": clean_number(s["unit_cost"]),
        }
        for k, s in enumerate(vam_result.get("steps", []))
    ]

    result = {
        "problem": {
            "supply": supply,
            "demand": demand,
            "cost_matrix": costs,
            "stations": [station_name(i) for i in range(len(supply))],
            "areas": [area_name(j) for j in range(len(demand))],
            "total_vehicles": sum(supply),
        },
        "initial": {
            "method": "VAM",
            "allocation": initial_allocation,
            "cost": initial_cost,
            "steps": steps,
        },
        "optimal": {
            "method": "MODI",
            "allocation": final_allocation,
            "cost": final_cost,
            "iterations": modi_result.get("iterations"),
            "is_optimal": bool(modi_result.get("is_optimal", False)),
            "potentials_u": [clean_number(v) for v in modi_result.get("potentials_u", [])],
            "potentials_v": [clean_number(v) for v in modi_result.get("potentials_v", [])],
            "reduced_costs": round_matrix(modi_result.get("reduced_costs", [])),
        },
        "current": None,
        "comparison": None,
        "warnings": warnings,
    }

    current = problem.get("current_allocation")
    if current is not None:
        current_cost = total_cost(current, costs)
        saving = clean_number(current_cost - final_cost)
        percent = round(saving / current_cost * 100, 2) if current_cost else 0.0
        delta, changes = compare(current, final_allocation)
        result["current"] = {"allocation": current, "cost": current_cost}
        result["comparison"] = {
            "saving": saving,
            "saving_percent": percent,
            "delta_matrix": delta,
            "changes": changes,
        }
    return result
