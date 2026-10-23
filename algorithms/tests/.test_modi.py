import unittest
from modi import modi_optimize

SUPPLY = [8, 6, 7, 9]
DEMAND = [5, 7, 6, 6, 6]
COST = [[24,45,37,18,19], [28,36,37,13,23], [45,39,31,42,15], [26,42,19,19,18]]
INITIAL = [[5,3,0,0,0], [0,0,0,6,0], [0,1,0,0,6], [0,3,6,0,0]]

class TestMODI(unittest.TestCase):
    def test_optimal_cost_and_feasibility(self):
        result = modi_optimize(SUPPLY, DEMAND, COST, INITIAL)
        allocation = result["allocation"]
        self.assertEqual(result["total_cost"], 690)
        self.assertTrue(result["is_optimal"])
        self.assertEqual([sum(row) for row in allocation], SUPPLY)
        self.assertEqual([sum(allocation[i][j] for i in range(4)) for j in range(5)], DEMAND)

    def test_invalid_initial_solution_rejected(self):
        with self.assertRaises(ValueError):
            modi_optimize(SUPPLY, DEMAND, COST, [[0]*5 for _ in range(4)])

if __name__ == "__main__":
    unittest.main()

