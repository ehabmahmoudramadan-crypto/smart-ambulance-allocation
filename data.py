"""Shared synthetic data for the Smart Ambulance Allocation project."""

STATIONS = [f"S{i}" for i in range(1, 9)]
AREAS = [f"A{i}" for i in range(1, 13)]

SUPPLY = [10, 10, 10, 10, 9, 10, 9, 10]
DEMAND = [4, 6, 7, 4, 7, 8, 7, 5, 12, 6, 8, 4]

# Rows correspond to S1..S8; columns correspond to A1..A12.
COST_MATRIX = [
    [17, 24, 31, 15, 47, 43, 32, 14, 11, 42, 33, 31],
    [24, 6, 15, 33, 24, 16, 5, 20, 26, 20, 43, 28],
    [31, 34, 40, 8, 56, 53, 26, 25, 17, 47, 28, 31],
    [31, 17, 10, 28, 28, 25, 25, 13, 19, 18, 28, 13],
    [37, 25, 9, 33, 23, 26, 30, 24, 1, 13, 29, 14],
    [30, 17, 9, 38, 17, 17, 40, 25, 28, 8, 38, 22],
    [33, 22, 8, 33, 20, 20, 30, 24, 23, 12, 29, 14],
    [15, 19, 25, 21, 39, 34, 32, 9, 13, 33, 36, 26],
]

# Current allocation supplied in large_dataset.json.
CURRENT_DISTRIBUTION = [
    [4, 0, 0, 0, 0, 1, 0, 5, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0],
    [0, 3, 0, 0, 0, 5, 0, 0, 0, 2, 0, 0],
    [0, 3, 0, 2, 0, 0, 0, 0, 0, 0, 5, 0],
    [0, 0, 7, 0, 0, 2, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 2, 4, 0, 4],
    [0, 0, 0, 2, 0, 0, 7, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 3, 0],
]

# Reference optimal allocation from the problem-definition PDF.
OPTIMAL_DISTRIBUTION = [
    [0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 3, 0],
    [0, 6, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 4, 0, 0, 1, 0, 0, 0, 5, 0],
    [0, 0, 1, 0, 0, 0, 5, 0, 0, 0, 0, 4],
    [0, 0, 4, 0, 0, 0, 0, 0, 5, 0, 0, 0],
    [0, 0, 0, 0, 0, 4, 0, 0, 0, 6, 0, 0],
    [0, 0, 2, 0, 7, 0, 0, 0, 0, 0, 0, 0],
    [4, 0, 0, 0, 0, 0, 1, 5, 0, 0, 0, 0],
]

CLOSED_ROUTES = [("S2", "A7")]
ROUTE_CAPACITIES = {("S5", "A9"): 5}

REFERENCE_CURRENT_COST = 2097
REFERENCE_OPTIMAL_COST = 1111
DATA_IS_SYNTHETIC = True


def calculate_distribution_cost(distribution):
    """Return total allocation cost: sum(allocation * travel-time cost)."""
    if len(distribution) != len(STATIONS):
        raise ValueError("Distribution must contain one row per station.")
    if any(len(row) != len(AREAS) for row in distribution):
        raise ValueError("Each distribution row must contain one value per area.")
    return sum(
        distribution[i][j] * COST_MATRIX[i][j]
        for i in range(len(STATIONS))
        for j in range(len(AREAS))
    )


def validate_distribution(distribution):
    """Validate dimensions, integer/nonnegative values, supply/demand, and route constraints."""
    errors = []

    if not isinstance(distribution, list) or len(distribution) != len(STATIONS):
        return ["Distribution must contain one row per station."]

    if any(not isinstance(row, list) or len(row) != len(AREAS) for row in distribution):
        return ["Each distribution row must contain one value per area."]

    for i, row in enumerate(distribution):
        for j, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"Allocation at {STATIONS[i]} to {AREAS[j]} must be a non-negative integer.")

    if errors:
        return errors

    row_totals = [sum(row) for row in distribution]
    column_totals = [
        sum(distribution[i][j] for i in range(len(STATIONS)))
        for j in range(len(AREAS))
    ]

    for i, total in enumerate(row_totals):
        if total != SUPPLY[i]:
            errors.append(f"{STATIONS[i]} allocation total is {total}; expected {SUPPLY[i]}.")

    for j, total in enumerate(column_totals):
        if total != DEMAND[j]:
            errors.append(f"{AREAS[j]} allocation total is {total}; expected {DEMAND[j]}.")

    for station, area in CLOSED_ROUTES:
        i, j = STATIONS.index(station), AREAS.index(area)
        if distribution[i][j] != 0:
            errors.append(f"Closed route {station} to {area} must have zero allocation.")

    for (station, area), maximum in ROUTE_CAPACITIES.items():
        i, j = STATIONS.index(station), AREAS.index(area)
        if distribution[i][j] > maximum:
            errors.append(f"Route {station} to {area} exceeds its maximum capacity of {maximum}.")

    return errors


def validate_data():
    """Validate the shared input data and the supplied current distribution."""
    errors = []

    if len(SUPPLY) != len(STATIONS):
        errors.append("Supply length does not match the number of stations.")
    if len(DEMAND) != len(AREAS):
        errors.append("Demand length does not match the number of areas.")
    if len(COST_MATRIX) != len(STATIONS) or any(
        len(row) != len(AREAS) for row in COST_MATRIX
    ):
        errors.append("Cost matrix dimensions are incorrect.")
    if any(not isinstance(value, (int, float)) or value < 0
           for row in COST_MATRIX for value in row):
        errors.append("Costs must be non-negative numbers.")
    if sum(SUPPLY) != sum(DEMAND):
        errors.append("Total supply must equal total demand.")

    errors.extend(validate_distribution(CURRENT_DISTRIBUTION))

    if not errors and calculate_distribution_cost(CURRENT_DISTRIBUTION) != REFERENCE_CURRENT_COST:
        errors.append("Current distribution cost does not match the reference cost.")

    if not errors and calculate_distribution_cost(OPTIMAL_DISTRIBUTION) != REFERENCE_OPTIMAL_COST:
        errors.append("Reference optimal distribution cost does not match the reference cost.")

    return errors
