import math

from errors import ValidationError

MAX_SIZE = 20
MAX_QUANTITY = 100000
MAX_COST = 1000000000


def station_name(i):
    return f"S{i + 1}"


def area_name(j):
    return f"A{j + 1}"


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
            f"{label} exceeds the maximum allowed value ({MAX_QUANTITY}).", "VALUE_TOO_LARGE", field
        )
    return value


def read_counts(payload, key, label_of, title):
    values = payload[key]
    if not isinstance(values, list) or not values:
        raise ValidationError(f"{title} must be a non-empty list of numbers.", "INVALID_VECTOR", key)
    if len(values) > MAX_SIZE:
        raise ValidationError(
            f"{title} can contain at most {MAX_SIZE} items.", "TOO_LARGE", key
        )
    return [as_count(v, f"{key}[{i}]", label_of(i)) for i, v in enumerate(values)]


def read_costs(payload, m, n):
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
                f"Row {station_name(i)} of the cost matrix must have {n} values, one per area.",
                "INVALID_COST_MATRIX",
                f"cost_matrix[{i}]",
            )
        clean_row = []
        for j, value in enumerate(row):
            field = f"cost_matrix[{i}][{j}]"
            label = f"Cost between {station_name(i)} and {area_name(j)}"
            if not is_real_number(value):
                raise ValidationError(f"{label} must be a number.", "NOT_A_NUMBER", field)
            if value < 0:
                raise ValidationError(f"{label} cannot be negative.", "NEGATIVE_VALUE", field)
            if value > MAX_COST:
                raise ValidationError(f"{label} exceeds the maximum allowed value.", "VALUE_TOO_LARGE", field)
            clean_row.append(value)
        clean.append(clean_row)
    return clean


def read_current(payload, supply, demand):
    rows = payload["current_allocation"]
    m, n = len(supply), len(demand)
    if not isinstance(rows, list) or len(rows) != m:
        raise ValidationError(
            f"The current allocation must have {m} rows, one per station.",
            "INVALID_CURRENT_ALLOCATION",
            "current_allocation",
        )
    clean = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != n:
            raise ValidationError(
                f"Row {station_name(i)} of the current allocation must have {n} values, one per area.",
                "INVALID_CURRENT_ALLOCATION",
                f"current_allocation[{i}]",
            )
        clean.append(
            [
                as_count(
                    v,
                    f"current_allocation[{i}][{j}]",
                    f"Current allocation between {station_name(i)} and {area_name(j)}",
                )
                for j, v in enumerate(row)
            ]
        )
    for i in range(m):
        if sum(clean[i]) != supply[i]:
            raise ValidationError(
                f"Current allocation total for station {station_name(i)} ({sum(clean[i])}) "
                f"does not match its ambulance count ({supply[i]}).",
                "CURRENT_ALLOCATION_MISMATCH",
                f"current_allocation[{i}]",
            )
    for j in range(n):
        column = sum(clean[i][j] for i in range(m))
        if column != demand[j]:
            raise ValidationError(
                f"Current allocation total for area {area_name(j)} ({column}) "
                f"does not match its demand ({demand[j]}).",
                "CURRENT_ALLOCATION_MISMATCH",
                "current_allocation",
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
        payload, "supply", lambda i: f"Ambulance count of station {station_name(i)}", "Supply list"
    )
    demand = read_counts(
        payload, "demand", lambda j: f"Demand of area {area_name(j)}", "Demand list"
    )
    costs = read_costs(payload, len(supply), len(demand))

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

    current = None
    if payload.get("current_allocation") is not None:
        current = read_current(payload, supply, demand)

    return {
        "supply": supply,
        "demand": demand,
        "cost_matrix": costs,
        "current_allocation": current,
    }
