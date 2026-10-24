import unittest

from app import app
from data import (
    AREAS,
    COST_MATRIX,
    CURRENT_DISTRIBUTION,
    DEMAND,
    OPTIMAL_DISTRIBUTION,
    REFERENCE_CURRENT_COST,
    REFERENCE_OPTIMAL_COST,
    STATIONS,
    SUPPLY,
    calculate_distribution_cost,
    validate_data,
    validate_distribution,
)


class TestAmbulanceData(unittest.TestCase):
    def test_default_data_is_valid(self):
        self.assertEqual(validate_data(), [])

    def test_total_supply_equals_total_demand(self):
        self.assertEqual(sum(SUPPLY), 78)
        self.assertEqual(sum(DEMAND), 78)
        self.assertEqual(sum(SUPPLY), sum(DEMAND))

    def test_cost_matrix_dimensions(self):
        self.assertEqual(len(COST_MATRIX), len(STATIONS))
        self.assertTrue(all(len(row) == len(AREAS) for row in COST_MATRIX))

    def test_current_distribution_cost_is_2097(self):
        self.assertEqual(calculate_distribution_cost(CURRENT_DISTRIBUTION), 2097)
        self.assertEqual(REFERENCE_CURRENT_COST, 2097)

    def test_optimal_reference_cost_is_1111(self):
        self.assertEqual(calculate_distribution_cost(OPTIMAL_DISTRIBUTION), 1111)
        self.assertEqual(REFERENCE_OPTIMAL_COST, 1111)

    def test_closed_route_has_zero_allocation(self):
        self.assertEqual(CURRENT_DISTRIBUTION[1][6], 0)
        self.assertEqual(OPTIMAL_DISTRIBUTION[1][6], 0)

    def test_route_capacity_is_respected(self):
        self.assertLessEqual(CURRENT_DISTRIBUTION[4][8], 5)
        self.assertLessEqual(OPTIMAL_DISTRIBUTION[4][8], 5)

    def test_data_is_marked_as_synthetic(self):
        from data import DATA_IS_SYNTHETIC
        self.assertTrue(DATA_IS_SYNTHETIC)

    def test_negative_allocation_is_rejected(self):
        bad_distribution = [row[:] for row in CURRENT_DISTRIBUTION]
        bad_distribution[0][0] = -1
        self.assertTrue(validate_distribution(bad_distribution))

    def test_flask_api_endpoints(self):
        client = app.test_client()
        self.assertEqual(client.get("/api/data").status_code, 200)
        self.assertEqual(client.get("/api/validate").status_code, 200)
        self.assertEqual(client.get("/api/distribution/current").status_code, 200)
        self.assertEqual(client.get("/api/cost/current").json["cost"], 2097)


if __name__ == "__main__":
    unittest.main()
