import math

from errors import ValidationError

MAX_SIZE = 20
MAX_QUANTITY = 100000
MAX_COST = 1000000000
MAX_LABEL_LENGTH = 40


def is_real_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def as_count(value, field, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} must be a number.", "NOT_A_NUMBER", field)
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        raise ValidationError(f"{label} must be a whole number.", "NOT_AN_INTEGER", field)
    value = int(value)
    if value < 0:
        raise ValidationError(f"{label} cannot be negative.", "NEGATIVE_VALUE", field)
    if value > MAX_QUANTITY:
        raise ValidationError(
            f"{label} exceeds the maximum allowed value ({MAX_QUANTITY}).",
            "VALUE_TOO_LARGE",
            field,
        )
    return value


def read_labels(payload, key, size, prefix):
    values = payload.get(key)
    if values is None:
        return [f"{prefix}{i + 1}" for i in range(size)]
    if not isinstance(values, list) or len(values) != size:
        raise ValidationError(
            f"{key} must be a list of {size} names.", "INVALID_LABELS", key
        )
    names = []
    for i, name in enumerate(values):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > MAX_LABEL_LENGTH:
            raise ValidationError(
                f"Each item in {key} must be a non-empty text of at most {MAX_LABEL_LENGTH} characters.",
                "INVALID_LABELS",
                f"{key}[{i}]",
            )
        names.append(name.strip())
    if len(set(names)) != len(names):
        raise ValidationError(f"Names in {key} must be unique.", "DUPLICATE_LABELS", key)
    return names


def read_counts(payload, key, label_of, title):
    values = payload[key]
    if not isinstance(values, list) or not values:
        raise ValidationError(
            f"{title} must be a non-empty list of numbers.", "INVALID_VECTOR", key
        )
    if len(values) > MAX_SIZE:
        raise ValidationError(
            f"{title} can contain at most {MAX_SIZE} items.", "TOO_LARGE", key
        )
    return [as_count(v, f"{key}[{i}]", label_of(i)) for i, v in enumerate(values)]


def read_costs(payload, stations, areas):
    m, n = len(stations), len(areas)
    matrix = payload["cost_matrix"]
    if not isinstance(matrix, list) or len(matrix) != m:
        raise ValidationError(
            f"The cost matrix must have {m} rows, one per station.",
            "INVALID_COST_MATRIX",
            "cost_matrix",
        )
    clean = []
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != n:
            raise ValidationError(
                f"Row {stations[i]} of the cost matrix must have {n} values, one per area.",
                "INVALID_COST_MATRIX",
                f"cost_matrix[{i}]",
            )
        clean_row = []
        for j, value in enumerate(row):
            field = f"cost_matrix[{i}][{j}]"
            label = f"Cost between {stations[i]} and {areas[j]}"
            if not is_real_number(value):
                raise ValidationError(f"{label} must be a number.", "NOT_A_NUMBER", field)
            if value < 0:
                raise ValidationError(f"{label} cannot be negative.", "NEGATIVE_VALUE", field)
            if value > MAX_COST:
                raise ValidationError(
                    f"{label} exceeds the maximum allowed value.", "VALUE_TOO_LARGE", field
                )
            clean_row.append(value)
        clean.append(clean_row)
    return clean


def read_route_ends(item, stations, areas, field):
    if not isinstance(item, dict) or "from" not in item or "to" not in item:
        raise ValidationError(
            "Each route must be an object with 'from' and 'to'.", "INVALID_ROUTE", field
        )
    if item["from"] not in stations:
        raise ValidationError(
            f"Unknown station '{item['from']}' in {field}.", "INVALID_ROUTE", field
        )
    if item["to"] not in areas:
        raise ValidationError(
            f"Unknown area '{item['to']}' in {field}.", "INVALID_ROUTE", field
        )
    return stations.index(item["from"]), areas.index(item["to"])


def read_closed_routes(payload, stations, areas):
    items = payload.get("closed_routes")
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValidationError(
            "closed_routes must be a list.", "INVALID_ROUTE", "closed_routes"
        )
    routes = []
    for k, item in enumerate(items):
        route = read_route_ends(item, stations, areas, f"closed_routes[{k}]")
        if route in routes:
            raise ValidationError(
                f"Route {stations[route[0]]} to {areas[route[1]]} is listed twice.",
                "DUPLICATE_ROUTE",
                f"closed_routes[{k}]",
            )
        routes.append(route)
    return routes


def read_route_capacities(payload, stations, areas):
    items = payload.get("route_capacities")
    if items is None:
        return {}
    if not isinstance(items, list):
        raise ValidationError(
            "route_capacities must be a list.", "INVALID_ROUTE", "route_capacities"
        )
    capacities = {}
    for k, item in enumerate(items):
        field = f"route_capacities[{k}]"
        route = read_route_ends(item, stations, areas, field)
        if route in capacities:
            raise ValidationError(
                f"Route {stations[route[0]]} to {areas[route[1]]} is listed twice.",
                "DUPLICATE_ROUTE",
                field,
            )
        label = f"Capacity of route {stations[route[0]]} to {areas[route[1]]}"
        capacities[route] = as_count(item.get("max"), f"{field}.max", label)
    return capacities


def read_current(payload, key, supply, demand, stations, areas):
    rows = payload[key]
    m, n = len(supply), len(demand)
    if not isinstance(rows, list) or len(rows) != m:
        raise ValidationError(
            f"The current allocation must have {m} rows, one per station.",
            "INVALID_CURRENT_ALLOCATION",
            key,
        )
    clean = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != n:
            raise ValidationError(
                f"Row {stations[i]} of the current allocation must have {n} values, one per area.",
                "INVALID_CURRENT_ALLOCATION",
                f"{key}[{i}]",
            )
        clean.append(
            [
                as_count(
                    v,
                    f"{key}[{i}][{j}]",
                    f"Current allocation between {stations[i]} and {areas[j]}",
                )
                for j, v in enumerate(row)
            ]
        )
    for i in range(m):
        if sum(clean[i]) != supply[i]:
            raise ValidationError(
                f"Current allocation total for station {stations[i]} ({sum(clean[i])}) "
                f"does not match its ambulance count ({supply[i]}).",
                "CURRENT_ALLOCATION_MISMATCH",
                f"{key}[{i}]",
            )
    for j in range(n):
        column = sum(clean[i][j] for i in range(m))
        if column != demand[j]:
            raise ValidationError(
                f"Current allocation total for area {areas[j]} ({column}) "
                f"does not match its demand ({demand[j]}).",
                "CURRENT_ALLOCATION_MISMATCH",
                key,
            )
    return clean


def parse_problem(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request format.", "INVALID_BODY")

    missing = [k for k in ("supply", "demand", "cost_matrix") if k not in payload]
    if missing:
        raise ValidationError(
            "Missing fields: " + ", ".join(missing),
            "MISSING_FIELDS",
            details={"missing": missing},
        )

    supply = read_counts(
        payload,
        "supply",
        lambda i: f"Ambulance count of station {i + 1}",
        "Supply list",
    )
    demand = read_counts(
        payload,
        "demand",
        lambda j: f"Demand of area {j + 1}",
        "Demand list",
    )
    stations = read_labels(payload, "stations", len(supply), "S")
    areas = read_labels(payload, "areas", len(demand), "A")
    costs = read_costs(payload, stations, areas)

    total_supply = sum(supply)
    total_demand = sum(demand)
    if total_supply == 0:
        raise ValidationError("At least one ambulance is required.", "EMPTY_PROBLEM", "supply")
    if total_supply != total_demand:
        raise ValidationError(
            f"Total supply ({total_supply}) does not equal total demand ({total_demand}).",
            "UNBALANCED",
            details={"total_supply": total_supply, "total_demand": total_demand},
        )

    closed_routes = read_closed_routes(payload, stations, areas)
    route_capacities = read_route_capacities(payload, stations, areas)

    current = None
    for key in ("current_distribution", "current_allocation"):
        if payload.get(key) is not None:
            current = read_current(payload, key, supply, demand, stations, areas)
            break

    return {
        "stations": stations,
        "areas": areas,
        "supply": supply,
        "demand": demand,
        "cost_matrix": costs,
        "closed_routes": closed_routes,
        "route_capacities": route_capacities,
        "current_allocation": current,
    }
