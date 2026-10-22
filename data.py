
SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]

COST_MATRIX = [
    [24, 45, 37, 18, 19],
    [28, 36, 37, 13, 23],
    [45, 39, 31, 42, 15],
    [26, 42, 19, 19, 18]
]

CURRENT_ALLOCATION = [
    [3, 2, 1, 1, 1],
    [1, 2, 1, 1, 1],
    [0, 1, 2, 2, 2],
    [1, 2, 2, 2, 2]
]

DATA_IS_SYNTHETIC = True


def validate_data():
    if not isinstance(SUPPLY, list) or not isinstance(DEMAND, list):
        return False

    if len(SUPPLY) == 0 or len(DEMAND) == 0:
        return False

    if not isinstance(COST_MATRIX, list):
        return False

    if not isinstance(CURRENT_ALLOCATION, list):
        return False

    if len(COST_MATRIX) != len(SUPPLY):
        return False

    if len(CURRENT_ALLOCATION) != len(SUPPLY):
        return False

    if any(len(row) != len(DEMAND) for row in COST_MATRIX):
        return False

    if any(len(row) != len(DEMAND) for row in CURRENT_ALLOCATION):
        return False

    if any(type(x) is not int or x < 0 for x in SUPPLY):
        return False

    if any(type(x) is not int or x < 0 for x in DEMAND):
        return False

    if any(
        type(x) not in (int, float) or x < 0
        for row in COST_MATRIX for x in row
    ):
        return False

    if any(
        type(x) is not int or x < 0
        for row in CURRENT_ALLOCATION for x in row
    ):
        return False

    if sum(SUPPLY) != sum(DEMAND):
        return False

    if [sum(row) for row in CURRENT_ALLOCATION] != SUPPLY:
        return False

    for j in range(len(DEMAND)):
        total = sum(
            CURRENT_ALLOCATION[i][j]
            for i in range(len(SUPPLY))
        )

        if total != DEMAND[j]:
            return False

    return True


def calculate_current_cost():
    if not validate_data():
        raise ValueError("Invalid transportation data")

    total = 0

    for i in range(len(SUPPLY)):
        for j in range(len(DEMAND)):
            total += (
                CURRENT_ALLOCATION[i][j] * COST_MATRIX[i][j]
            )

    return total
