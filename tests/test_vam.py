import unittest
from vam import vogel_approximation

SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COST = [[24,45,37,18,19], [28,36,37,13,23], [45,39,31,42,15], [26,42,19,19,18]]

class TestVAM(unittest.TestCase):
    def test_expected_cost_and_feasibility(self):
        result = vogel_approximation(SUPPLY, DEMAND, COST)
        allocation = result["allocation"]
        self.assertEqual(result["total_cost"], 702)
        self.assertEqual([sum(row) for row in allocation], SUPPLY)
        self.assertEqual([sum(allocation[i][j] for i in range(4)) for j in range(5)], DEMAND)

    def test_unbalanced_rejected(self):
        with self.assertRaises(ValueError):
            vogel_approximation([8, 6], [5, 8], [[1, 2], [3, 4]])

if __name__ == "__main__":
    unittest.main()
