import copy

from errors import SolverError

EPS = 1e-6


def load_algorithms():
    try:
        from algorithms.modi import modi_method, solve_constrained_transport
        from algorithms.vam import vogel_approximation
    except ImportError as exc:
        raise SolverError(
            "The optimization algorithms are not available.",
            "ALGORITHMS_UNAVAILABLE",
            details={"reason": str(exc)},
            status=501,
        ) from exc
    return vogel_approximation, modi_method, solve_constrained_transport


def clean_number(value):
    value = round(float(value), 6)
    return int(value) if value.is_integer() else value


def clean_list(values):
    return None if values is None else [clean_number(v) for v in values]


def clean_matrix(matrix):
    return None if matrix is None else [clean_list(row) for row in matrix]


def total_cost(allocation, costs):
    return clean_number(
        sum(
            allocation[i][j] * costs[i][j]
            for i in range(len(allocation))
            for j in range(len(allocation[i]))
        )
    )


def route_limits(closed_routes, route_capacities):
    limits = dict(route_capacities)
    for route in closed_routes:
        limits[route] = 0
    return limits


def restriction_issues(allocation, limits, stations, areas):
    return [
        f"Route {stations[i]} to {areas[j]} carries {allocation[i][j]} ambulances "
        f"but its limit is {limit}."
        for (i, j), limit in sorted(limits.items())
        if allocation[i][j] > limit
    ]


def run_stage(stage, func, *args):
    try:
        return func(*copy.deepcopy(args))
    except Exception as exc:
        if isinstance(exc, RuntimeError) and "infeasible" in str(exc).lower():
            raise SolverError(
                "No feasible allocation exists under the given route restrictions.",
                "NO_FEASIBLE_SOLUTION",
                details={"reason": str(exc)},
                status=422,
            ) from exc
        raise SolverError(
            f"Failed to run {stage}.",
            "ALGORITHM_FAILED",
            details={"reason": str(exc)},
        ) from exc


def read_vam_result(raw):
    if isinstance(raw, dict):
        return raw.get("allocation"), raw.get("total_cost", raw.get("cost")), raw.get("steps") or []
    if isinstance(raw, (tuple, list)) and len(raw) == 3:
        return raw[0], raw[1], raw[2] or []
    raise SolverError("The VAM result has an unexpected format.", "ALGORITHM_BAD_OUTPUT")


def check_allocation(stage, allocation, supply, demand, stations, areas, limits):
    m, n = len(supply), len(demand)
    if not isinstance(allocation, list) or len(allocation) != m:
        raise SolverError(f"The {stage} result has invalid dimensions.", "ALGORITHM_INFEASIBLE")

    clean = []
    for i, row in enumerate(allocation):
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise SolverError(f"The {stage} result has invalid dimensions.", "ALGORITHM_INFEASIBLE")
        clean_row = []
        for j, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
                raise SolverError(
                    f"The {stage} result contains a non-numeric value.", "ALGORITHM_BAD_OUTPUT"
                )
            if abs(value - round(value)) > EPS:
                raise SolverError(
                    f"The {stage} result contains a non-integer value at {stations[i]}, {areas[j]}.",
                    "ALGORITHM_INFEASIBLE",
                )
            value = int(round(value))
            if value < 0:
                raise SolverError(
                    f"The {stage} result contains a negative value at {stations[i]}, {areas[j]}.",
                    "ALGORITHM_INFEASIBLE",
                )
            clean_row.append(value)
        clean.append(clean_row)

    for i in range(m):
        if sum(clean[i]) != supply[i]:
            raise SolverError(
                f"The {stage} result: row {stations[i]} does not add up to its supply.",
                "ALGORITHM_INFEASIBLE",
            )
    for j in range(n):
        if sum(clean[i][j] for i in range(m)) != demand[j]:
            raise SolverError(
                f"The {stage} result: column {areas[j]} does not add up to its demand.",
                "ALGORITHM_INFEASIBLE",
            )

    issues = restriction_issues(clean, limits, stations, areas)
    if issues:
        raise SolverError(
            f"The {stage} result violates a route restriction.",
            "ALGORITHM_VIOLATES_RESTRICTIONS",
            details={"issues": issues},
        )
    return clean


def finish_stage(stage, allocation, reported, problem, limits, warnings):
    allocation = check_allocation(
        stage,
        allocation,
        problem["supply"],
        problem["demand"],
        problem["stations"],
        problem["areas"],
        limits,
    )
    cost = total_cost(allocation, problem["cost_matrix"])
    if isinstance(reported, (int, float)) and not isinstance(reported, bool):
        if abs(reported - cost) > EPS:
            warnings.append(
                f"The {stage} reported cost ({reported}) differs from the cost "
                f"computed from the matrix ({cost})."
            )
    return allocation, cost


def format_steps(steps, stations, areas):
    keys = {"row", "column", "quantity", "unit_cost"}
    formatted = []
    for k, step in enumerate(steps):
        if not isinstance(step, dict) or not keys <= step.keys():
            return []
        formatted.append(
            {
                "step": k + 1,
                "station": stations[step["row"]],
                "area": areas[step["column"]],
                "quantity": step["quantity"],
                "unit_cost": clean_number(step["unit_cost"]),
            }
        )
    return formatted


def compare(current, proposed, stations, areas):
    m, n = len(proposed), len(proposed[0])
    delta = [[proposed[i][j] - current[i][j] for j in range(n)] for i in range(m)]
    changes = [
        {
            "station": stations[i],
            "area": areas[j],
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
    vam, modi, constrained = load_algorithms()

    supply = problem["supply"]
    demand = problem["demand"]
    costs = problem["cost_matrix"]
    stations = problem["stations"]
    areas = problem["areas"]
    closed = problem["closed_routes"]
    capacities = problem["route_capacities"]
    limits = route_limits(closed, capacities)
    warnings = []

    raw = run_stage("VAM", vam, supply, demand, costs, closed, capacities)
    vam_allocation, vam_reported, vam_steps = read_vam_result(raw)

    initial = None
    if vam_allocation is None:
        warnings.append(
            "VAM could not build a feasible initial allocation under the route restrictions."
        )
    else:
        allocation, cost = finish_stage(
            "VAM", vam_allocation, vam_reported, problem, limits, warnings
        )
        initial = {
            "method": "VAM",
            "allocation": allocation,
            "cost": cost,
            "steps": format_steps(vam_steps, stations, areas),
        }

    if initial:
        modi_result = run_stage(
            "MODI", modi, initial["allocation"], supply, demand, costs, closed, capacities
        )
    else:
        modi_result = run_stage(
            "MODI", constrained, supply, demand, costs, closed, capacities
        )
    if not isinstance(modi_result, dict) or "allocation" not in modi_result:
        raise SolverError("The MODI result is incomplete.", "ALGORITHM_BAD_OUTPUT")

    final_allocation, final_cost = finish_stage(
        "MODI",
        modi_result["allocation"],
        modi_result.get("cost"),
        problem,
        limits,
        warnings,
    )
    if initial and final_cost > initial["cost"] + EPS:
        raise SolverError(
            "The MODI result costs more than the initial solution.",
            "ALGORITHM_WORSE_THAN_INITIAL",
        )

    optimal = {
        "method": "MODI",
        "solver": modi_result.get("method"),
        "allocation": final_allocation,
        "cost": final_cost,
        "improvement": clean_number(initial["cost"] - final_cost) if initial else None,
        "iterations": modi_result.get("iterations"),
        "is_optimal": modi_result.get("is_optimal"),
        "potentials_u": clean_list(modi_result.get("potentials_u")),
        "potentials_v": clean_list(modi_result.get("potentials_v")),
        "reduced_costs": clean_matrix(modi_result.get("reduced_costs")),
    }

    result = {
        "problem": {
            "supply": supply,
            "demand": demand,
            "cost_matrix": costs,
            "stations": stations,
            "areas": areas,
            "total_vehicles": sum(supply),
        },
        "constraints": {
            "closed_routes": [
                {"from": stations[i], "to": areas[j]} for i, j in closed
            ],
            "route_capacities": [
                {
                    "from": stations[i],
                    "to": areas[j],
                    "max": cap,
                    "used": final_allocation[i][j],
                }
                for (i, j), cap in sorted(capacities.items())
            ],
        },
        "initial": initial,
        "optimal": optimal,
        "current": None,
        "comparison": None,
        "warnings": warnings,
    }

    current = problem.get("current_allocation")
    if current is not None:
        for issue in restriction_issues(current, limits, stations, areas):
            warnings.append(f"Current allocation: {issue}")
        current_cost = total_cost(current, costs)
        saving = clean_number(current_cost - final_cost)
        percent = round(saving / current_cost * 100, 2) if current_cost else 0.0
        delta, changes = compare(current, final_allocation, stations, areas)
        result["current"] = {"allocation": current, "cost": current_cost}
        result["comparison"] = {
            "saving": saving,
            "saving_percent": percent,
            "delta_matrix": delta,
            "changes": changes,
        }
    return result
