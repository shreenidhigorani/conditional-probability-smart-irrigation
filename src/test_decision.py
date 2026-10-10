"""Boundary and validation tests for decision.py.
Run:  python src/test_decision.py      (also works with pytest)"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decision import decide, decide_from_counts


def d(p, ci, cs, n=50):
    return decide(p, ci, cs, n)["decision"]


def test_default_costs_and_boundaries():
    t = 1 / 3
    assert d(1.0, 1, 3) == "IRRIGATE NOW"
    assert d(0.75, 1, 3) == "IRRIGATE NOW"           # p == upper -> IRRIGATE
    assert d(0.7499, 1, 3) == "DELAY & RE-CHECK"
    assert d(t, 1, 3) == "DELAY & RE-CHECK"          # p == t -> DELAY (t <= p)
    assert d(0.3333, 1, 3) == "DON'T IRRIGATE"       # just below t
    assert d(0.0, 1, 3) == "DON'T IRRIGATE"
    assert decide(0.5, 1, 3, 50)["threshold"] == 0.3333


def test_cost_sensitivity_2_3():
    assert d(0.5, 1, 3) == "DELAY & RE-CHECK"        # hypothetical p
    assert d(0.5, 2, 3) == "DON'T IRRIGATE"          # t = 2/3 now above p
    assert d(2 / 3, 2, 3) == "DELAY & RE-CHECK"      # p == t
    assert d(0.75, 2, 3) == "IRRIGATE NOW"


def test_upper_is_max_of_075_and_t():
    # t = 0.8 > 0.75 -> upper = t, DELAY band disappears
    assert d(0.8, 4, 5) == "IRRIGATE NOW"
    assert d(0.79, 4, 5) == "DON'T IRRIGATE"
    assert d(0.76, 4, 5) == "DON'T IRRIGATE"         # would be IRRIGATE if upper were fixed at 0.75
    # t > 1: irrigation never worth it
    assert d(1.0, 5, 3) == "DON'T IRRIGATE"


def test_low_support_flag():
    r = decide(1.0, 1, 3, 9)
    assert r["low_support"] is True and "WARNING" in r["reason"]
    r = decide(1.0, 1, 3, 10)
    assert r["low_support"] is False and "WARNING" not in r["reason"]


def test_keys():
    assert {"p_dry_tomorrow", "threshold", "decision", "reason"} <= set(decide(0.5, 1, 3, 20))


def test_validation():
    bad = [(0.5, 0, 3, 20), (0.5, 1, 0, 20), (0.5, -1, 3, 20), (0.5, 1, -3, 20),
           (0.5, "1", 3, 20), (0.5, float("nan"), 3, 20), (0.5, float("inf"), 3, 20),
           (-0.1, 1, 3, 20), (1.1, 1, 3, 20), (float("nan"), 1, 3, 20), (None, 1, 3, 20),
           (0.5, 1, 3, 0), (0.5, 1, 3, -5), (0.5, 1, 3, 2.5), (0.5, 1, 3, None),
           (0.5, True, 3, 20)]
    for args in bad:
        try:
            decide(*args)
        except ValueError:
            continue
        raise AssertionError(f"decide{args} should have raised ValueError")


def test_numpy_and_pandas_numbers_are_accepted():
    # the analysis script / backend may pass numpy numbers
    import numpy as np
    r = decide(np.float64(0.9), np.float64(1.0), np.int64(3), np.int64(50))
    assert r["decision"] == "IRRIGATE NOW" and isinstance(r["n"], int)


def test_exact_boundaries_from_counts():
    # p = k/n lands exactly on t = 1/3 and on 0.75 without rounding trouble
    assert decide_from_counts(1, 3, 1, 3)["decision"] == "DELAY & RE-CHECK"     # p = 1/3 = t
    assert decide_from_counts(3, 4, 1, 3)["decision"] == "IRRIGATE NOW"         # p = 0.75 = upper
    assert decide_from_counts(2, 3, 2, 3)["decision"] == "DELAY & RE-CHECK"     # p = 2/3 = t (c_irr=2)
    assert decide_from_counts(0, 50, 1, 3)["decision"] == "DON'T IRRIGATE"      # p = 0
    assert decide_from_counts(50, 50, 1, 3)["decision"] == "IRRIGATE NOW"       # p = 1


def test_zero_and_one_are_not_certainty():
    # observed 0/20 is reported as p = 0 but is not proof the true probability is 0
    r = decide_from_counts(0, 20, 1, 3)
    assert r["p_dry_tomorrow"] == 0.0 and r["decision"] == "DON'T IRRIGATE" and r["n"] == 20


def test_no_data_cell():
    r = decide_from_counts(0, 0, 1, 3)
    assert r["decision"] == "NO DATA" and r["p_dry_tomorrow"] is None
    assert r["low_support"] is True and "WARNING" in r["reason"] and r["n"] == 0
    assert {"p_dry_tomorrow", "threshold", "decision", "reason"} <= set(r)
    for bad in [(0, 0, 0, 3), (0, 0, 1, 0), (0, 0, -1, 3)]:
        try:
            decide_from_counts(*bad)
        except ValueError:
            continue
        raise AssertionError(f"decide_from_counts{bad} should have raised ValueError")


def test_counts_validation():
    for bad in [(5, 3, 1, 3), (-1, 3, 1, 3), (1, -3, 1, 3), (0.5, 3, 1, 3), (1, 3.0, 1, 3),
                (None, 3, 1, 3), (1, None, 1, 3), (True, 3, 1, 3)]:
        try:
            decide_from_counts(*bad)
        except ValueError:
            continue
        raise AssertionError(f"decide_from_counts{bad} should have raised ValueError")


def test_low_support_via_counts():
    r = decide_from_counts(2, 2, 1, 3)               # n = 2 < 10
    assert r["low_support"] is True and "WARNING" in r["reason"] and r["decision"] == "IRRIGATE NOW"
    assert decide_from_counts(9, 9, 1, 3)["low_support"] is True
    assert decide_from_counts(10, 10, 1, 3)["low_support"] is False


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"All {len(tests)} test groups passed.")
