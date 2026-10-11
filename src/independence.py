# Independence of events / random variables
"""Independence of events / random variables module."""
from scipy.stats import chi2_contingency

def test_independence(observed_table):
    chi2, p_val, dof, expected = chi2_contingency(observed_table)
    return {"chi2": chi2, "p_value": p_val, "dof": dof, "expected": expected}
