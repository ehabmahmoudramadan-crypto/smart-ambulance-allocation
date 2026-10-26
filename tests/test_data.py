"""Phase 1 - data checks (no solver needed)."""
from optimization.model import load_dataset, check_plan


def test_shapes():
    ds, _, _ = load_dataset()
    m, n = len(ds["stations"]), len(ds["areas"])
    assert (m, n) == (8, 12)
    assert len(ds["supply"]) == m and len(ds["demand"]) == n
    assert len(ds["cost_matrix"]) == m and all(len(r) == n for r in ds["cost_matrix"])
    assert len(ds["current_allocation"]) == m


def test_balanced_and_positive():
    ds, _, _ = load_dataset()
    assert sum(ds["supply"]) == sum(ds["demand"]) == 78
    assert all(isinstance(v, int) and v > 0 for v in ds["supply"] + ds["demand"])
    assert all(isinstance(c, int) and c > 0 for r in ds["cost_matrix"] for c in r)


def test_constraints_reference_real_cells():
    ds, closed, caps = load_dataset()
    assert closed == [(1, 6)]            # S2 -> A7 closed
    assert caps == [(4, 8, 5)]           # S5 -> A9 <= 5


def test_current_allocation_is_valid_and_respects_constraints():
    ds, closed, caps = load_dataset()
    check_plan(ds["current_allocation"], ds["supply"], ds["demand"], closed, caps)
