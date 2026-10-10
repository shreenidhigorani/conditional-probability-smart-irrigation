"""
decision.py  -  IrrigAI (Group 6), Member 3: reusable decision engine.
Member 4 (FastAPI) imports this file:   from decision import decide

Decision rule (Group 6 guide, Section 4 "Shared contract"):
    t     = c_irr / c_stress
    upper = max(0.75, t)
    p >= upper       -> "IRRIGATE NOW"
    t <= p < upper   -> "DELAY & RE-CHECK"
    p < t            -> "DON'T IRRIGATE"
Where p = P(soil_next_dry = 1 | soil, rain), estimated from n matching days.

Notes
  * If t > 0.75 then upper = t, so the DELAY band is empty (no overlap).
  * If t > 1 (irrigation costs more than the stress it prevents) no probability
    can reach `upper`, so the answer is always DON'T IRRIGATE.
  * Bad input raises ValueError (Member 4 can turn this into an HTTP 422).
  * decide() needs n >= 1. For a soil/rain combination with n = 0 days use decide_from_counts(),
    which returns decision "NO DATA" and p_dry_tomorrow None (JSON null) instead of raising.
  * This is an exploratory rule on one location's data, NOT a validated
    agricultural recommendation.
"""
import math
import numbers

MIN_SUPPORT = 10        # fewer matching days than this -> low-support warning
UPPER_DEFAULT = 0.75    # lower edge of the IRRIGATE NOW band (before max with t)
DEFAULT_C_IRR = 1.0     # default costs from the guide
DEFAULT_C_STRESS = 3.0


def _real(x):
    """True for a real, finite number that is not a bool."""
    return (isinstance(x, numbers.Real) and not isinstance(x, bool)
            and math.isfinite(x))


def decide(p, c_irr, c_stress, n):
    """Apply the cost-loss decision rule.

    p        : P(soil_next_dry = 1 | soil, rain), a number from 0 to 1
    c_irr    : cost of irrigating (> 0)
    c_stress : cost of crop stress if the soil is Dry tomorrow (> 0)
    n        : number of matching days used to estimate p (whole number >= 1)

    Returns a dict with the four agreed API keys
        p_dry_tomorrow, threshold, decision, reason
    plus the optional extra keys the guide allows: n, low_support.
    """
    if not _real(c_irr) or not _real(c_stress) or c_irr <= 0 or c_stress <= 0:
        raise ValueError("c_irr and c_stress must both be numbers greater than 0")
    if not _real(p) or not (0 <= p <= 1):
        raise ValueError("p must be a number between 0 and 1")
    if (not isinstance(n, numbers.Integral) or isinstance(n, bool) or n < 1):
        raise ValueError("n must be a whole number >= 1 (no matching days means p is undefined)")

    t = c_irr / c_stress
    upper = max(UPPER_DEFAULT, t)
    low_support = n < MIN_SUPPORT

    if p >= upper:
        decision = "IRRIGATE NOW"
        reason = (f"P(Dry tomorrow) = {p:.3f} is at least the upper limit {upper:.3f}, "
                  f"and at or above the break-even threshold {t:.3f}, so irrigation is clearly worthwhile.")
    elif p >= t:
        decision = "DELAY & RE-CHECK"
        reason = (f"P(Dry tomorrow) = {p:.3f} is between the threshold {t:.3f} and the upper limit "
                  f"{upper:.3f}, so stress is possible but not near-certain; wait and re-check soil moisture.")
    else:
        decision = "DON'T IRRIGATE"
        reason = (f"P(Dry tomorrow) = {p:.3f} is below the threshold {t:.3f}; expected stress cost "
                  f"({c_stress:g} x {p:.3f} = {c_stress * p:.3f}) is less than the irrigation cost ({c_irr:g}).")
    if low_support:
        reason += f" WARNING: only {int(n)} matching days (< {MIN_SUPPORT}), so this estimate is unreliable."

    return {"p_dry_tomorrow": round(float(p), 4), "threshold": round(t, 4),
            "decision": decision, "reason": reason,
            "n": int(n), "low_support": bool(low_support)}


def decide_from_counts(k, n, c_irr, c_stress):
    """Convenience wrapper for the backend and the analysis script.

    k : number of matching days that were followed by a Dry day (soil_next_dry == 1)
    n : number of matching days with a known next-day outcome

    p = k / n is passed to decide(). If n == 0 the probability is UNDEFINED (not zero),
    so no cost-based decision is made: the result has decision "NO DATA",
    p_dry_tomorrow = None and low_support = True. (The guide's issue #3 suggests falling back
    to P(Dry tomorrow | soil only) for such cells; that choice is NOT made here because the
    group has not approved it. The caller can show the soil-only value separately.)
    """
    for name, v in (("k", k), ("n", n)):
        if (not isinstance(v, numbers.Integral) or isinstance(v, bool) or v < 0):
            raise ValueError(f"{name} must be a whole number >= 0")
    if k > n:
        raise ValueError("k (next-day Dry days) cannot be larger than n (matching days)")
    if n == 0:
        if (not _real(c_irr) or not _real(c_stress) or c_irr <= 0 or c_stress <= 0):
            raise ValueError("c_irr and c_stress must both be numbers greater than 0")
        t = c_irr / c_stress
        return {"p_dry_tomorrow": None, "threshold": round(t, 4), "decision": "NO DATA",
                "reason": (f"No matching days in the dataset (n = 0), so P(Dry tomorrow) is undefined; "
                           f"no decision can be made from this combination. WARNING: low support (n = 0 < {MIN_SUPPORT})."),
                "n": 0, "low_support": True}
    return decide(int(k) / int(n), c_irr, c_stress, int(n))


if __name__ == "__main__":
    # tiny demo with made-up p values (NOT data results)
    for p_demo in (0.9, 0.5, 0.1):
        print(p_demo, "->", decide(p_demo, DEFAULT_C_IRR, DEFAULT_C_STRESS, 50)["decision"])
