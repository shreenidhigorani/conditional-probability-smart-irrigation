"""
IrrigAI - Should We Irrigate Today?
Member 3: Statistical Independence and Irrigation Decision Logic
Dataset: data/g6_irrigation_data.csv (agreed Group 6 schema). The approved version is
         Kolhapur, 2022-01-01 to 2025-12-30, 1,460 rows (31 Dec 2025 has no "tomorrow", so it
         is not in the file). Nothing about the dataset is hard-coded below: every number
         printed or saved is computed from the CSV.

Run from the repository root:
    python src/irrigai_analysis_g6.py                 (uses data/g6_irrigation_data.csv)
    python src/irrigai_analysis_g6.py path/to/other.csv   (optional: another dataset version)
Outputs go to results/.   Needs: pandas, numpy, scipy, matplotlib, openpyxl (see requirements_member3.txt)
The decision rule lives in src/decision.py (Member 4 imports the same function).
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # lets graphs be saved without opening a window
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency, chi2 as chi2_dist

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision import decide, decide_from_counts, MIN_SUPPORT, UPPER_DEFAULT   # noqa: E402

# ----------------------------------------------------------------------
# SETTINGS (paths work from any folder because they start at the repo root)
# ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "g6_irrigation_data.csv"
OUT_DIR = ROOT / "results"
ALPHA = 0.05
MIN_SHIFT = 30           # circular shifts smaller than this many days are skipped
N_MC = 10000             # random shuffles for the Monte Carlo p-value
MC_SEED = 7              # fixed seed -> the Monte Carlo result is repeatable
OUT_DIR.mkdir(exist_ok=True)

RAIN_ORDER = ["None", "Light", "Heavy"]
SOIL_ORDER = ["Dry", "Moderate", "Wet"]


def out(name):
    return str(OUT_DIR / name)


def title(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# ======================================================================
# PART A
# ======================================================================

# ----------------------------------------------------------------------
# A1. Load, inspect and validate the data
# ----------------------------------------------------------------------
title("A1. LOAD AND INSPECT")
print("Using file:", CSV_PATH)

# IMPORTANT: the word "None" in rain_cat is a real category (no rain),
# but pandas treats the text "None" as a missing value by default.
# keep_default_na=False stops that; only truly empty cells become NaN.
df = pd.read_csv(CSV_PATH, keep_default_na=False, na_values=[""])
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)

print("Shape (rows, columns):", df.shape)
print("Date range:", df["date"].min().date(), "to", df["date"].max().date())
print("\nColumn names and types:")
print(df.dtypes)
print("\nFirst 5 rows:")
print(df.head().to_string())
print("\nMissing values per column (after reading 'None' correctly):")
print(df.isna().sum())

wrong = pd.read_csv(CSV_PATH)       # what a plain read_csv would do
print("\nFor comparison, a plain pd.read_csv() would report",
      int(wrong["rain_cat"].isna().sum()),
      "missing values in rain_cat - these are all the 'None' (no rain) days.")
print("(Member 4: load the CSV with keep_default_na=False, otherwise 'None' becomes NaN.)")

print("\nrain_cat counts :\n", df["rain_cat"].value_counts().reindex(RAIN_ORDER))
print("\nsoil_cat counts :\n", df["soil_cat"].value_counts().reindex(SOIL_ORDER))
print("\nRainfall range (mm) inside each rain_cat:")
print(df.groupby("rain_cat")["rain_mm"].agg(["count", "min", "max"]).reindex(RAIN_ORDER))
print("\nsoil_wetness range inside each soil_cat (shows the tertile cut points):")
print(df.groupby("soil_cat")["soil_wetness"].agg(["count", "min", "max"]).reindex(SOIL_ORDER))

# ---- integrity checks (the script stops with an error if any fails) ----
assert df["date"].is_unique, "duplicate dates"
assert (df["date"].diff().dropna() == pd.Timedelta(days=1)).all(), "dates are not consecutive days"
assert set(df["rain_cat"]) <= set(RAIN_ORDER) and set(df["soil_cat"]) <= set(SOIL_ORDER)
rain_rule = np.where(df["rain_mm"] < 2.5, "None", np.where(df["rain_mm"] <= 15.5, "Light", "Heavy"))
assert (rain_rule == df["rain_cat"]).all(), "rain_cat does not follow the guide rule"
shifted_dry = (df["soil_cat"].shift(-1) == "Dry").astype(int)
assert (shifted_dry.iloc[:-1] == df["soil_next_dry"].iloc[:-1]).all(), "soil_next_dry is not tomorrow's soil_cat"
# soil_cat must be the tertiles of soil_wetness (Dry <= 1/3 quantile < Moderate <= 2/3 quantile < Wet)
q1 = df["soil_wetness"].quantile(1 / 3)
q2 = df["soil_wetness"].quantile(2 / 3)
soil_rule = np.where(df["soil_wetness"] <= q1, "Dry", np.where(df["soil_wetness"] <= q2, "Moderate", "Wet"))
assert (soil_rule == df["soil_cat"]).all(), "soil_cat is not the tertile split of soil_wetness"
print(f"\nSoil tertile cut points recomputed from soil_wetness: 1/3 quantile = {q1:.4f}, 2/3 quantile = {q2:.4f}")
print("soil_cat matches the tertile rule for every row.")
print("Because soil_wetness has only 2 decimals, many days tie at a cut point, so the three classes are")
print("close to, but not exactly, one third each:",
      (df["soil_cat"].value_counts(normalize=True).reindex(SOIL_ORDER) * 100).round(1).to_dict(), "(% of days)")
print("Rain boundary rows exactly on 2.5 mm or 15.5 mm:",
      df.loc[df["rain_mm"].isin([2.5, 15.5]), ["date", "rain_mm", "rain_cat"]].assign(
          date=lambda x: x["date"].dt.strftime("%Y-%m-%d")).to_dict("records"))
n_imd_heavy = int((df["rain_mm"] > 64.4).sum())
print(f"Days above 64.4 mm (the guide quotes IMD 'Heavy' as 64.5-115.5 mm): {n_imd_heavy}; "
      f"max rainfall = {df['rain_mm'].max():.2f} mm")
print("-> the group's 'Heavy' class means '> 15.5 mm' and so also contains IMD 'Moderate' days (guide issue #1).")
print("\nIntegrity checks passed: unique consecutive dates; rain_cat follows the guide rule "
      "(None < 2.5, Light 2.5-15.5, Heavy > 15.5); soil_cat follows the tertile rule; "
      "soil_next_dry = (tomorrow's soil_cat == Dry) for every row except the last.")
print("(The last row's soil_next_dry cannot be re-checked here because its 'tomorrow' (31 Dec 2025) is "
      "not in the file.)")
print("Rows with any missing value:", int(df.isna().any(axis=1).sum()))

# ----------------------------------------------------------------------
# A2. Observed frequency table (rain_cat vs soil_cat)
# ----------------------------------------------------------------------
title("A2. OBSERVED FREQUENCY TABLE")

observed = pd.crosstab(df["rain_cat"], df["soil_cat"]).reindex(index=RAIN_ORDER, columns=SOIL_ORDER).fillna(0).astype(int)
n = int(observed.values.sum())

obs_with_totals = observed.copy()
obs_with_totals["Row total"] = observed.sum(axis=1)
obs_with_totals.loc["Column total"] = obs_with_totals.sum()
print(obs_with_totals)

row_pct = (observed.div(observed.sum(axis=1), axis=0) * 100).round(1)
print("\nRow percentages (within each rain category, % of days in each soil class):")
print(row_pct)

obs_with_totals.to_csv(out("table_observed.csv"))
row_pct.to_csv(out("table_row_percentages.csv"))

# ----------------------------------------------------------------------
# A3. Expected frequencies by hand:  E = (row total * column total) / n
# ----------------------------------------------------------------------
title("A3. EXPECTED FREQUENCIES (by hand formula)")

row_tot = observed.sum(axis=1).values.reshape(-1, 1)
col_tot = observed.sum(axis=0).values.reshape(1, -1)
expected_manual = pd.DataFrame(row_tot * col_tot / n, index=observed.index, columns=observed.columns)
print("E = (row total x column total) / grand total")
print(expected_manual.round(2))

# ----------------------------------------------------------------------
# A3b. Compare joint probability P(S and R) with P(S) x P(R) for all 9 cells
# ----------------------------------------------------------------------
title("A3b. JOINT PROBABILITY vs P(S) x P(R)")
joint_p = observed / n                                   # P(S and R) = n(S and R) / N
p_rain = observed.sum(axis=1) / n                        # P(R)
p_soil = observed.sum(axis=0) / n                        # P(S)
product_p = pd.DataFrame(np.outer(p_rain, p_soil), index=observed.index, columns=observed.columns)
diff_p = joint_p - product_p
print("Joint P(S and R):\n", joint_p.round(4))
print("\nP(R):\n", p_rain.round(4).to_string())
print("\nP(S):\n", p_soil.round(4).to_string())
print("\nProduct P(S) x P(R) (what the joint would be if independent):\n", product_p.round(4))
print("\nDifference  P(S and R) - P(S)P(R)  (0 everywhere would mean independence):\n", diff_p.round(4))
joint_p.to_csv(out("table_joint_probability.csv"))
product_p.to_csv(out("table_product_of_marginals.csv"))
diff_p.to_csv(out("table_joint_minus_product.csv"))

# one tidy 9-row table (easy to paste into the report)
rows = []
for r_ in RAIN_ORDER:
    for s_ in SOIL_ORDER:
        rows.append({"rain_cat": r_, "soil_cat": s_, "count": int(observed.loc[r_, s_]),
                     "P(S and R)": joint_p.loc[r_, s_], "P(S)": p_soil[s_], "P(R)": p_rain[r_],
                     "P(S) x P(R)": product_p.loc[r_, s_], "difference": diff_p.loc[r_, s_]})
nine = pd.DataFrame(rows)
print("\nAll nine combinations in one table:")
print(nine.round(4).to_string(index=False))
nine.to_csv(out("table_joint_vs_product_9cells.csv"), index=False)

# ----------------------------------------------------------------------
# A4. Hypotheses
# ----------------------------------------------------------------------
title("A4. HYPOTHESES")
print("H0: rain_cat and soil_cat are independent (rain category does not")
print("    change the distribution of soil-moisture category).")
print("H1: rain_cat and soil_cat are NOT independent (they are associated).")
print(f"Significance level: alpha = {ALPHA}")

# ----------------------------------------------------------------------
# A5. Chi-square test of independence
# ----------------------------------------------------------------------
title("A5. CHI-SQUARE TEST OF INDEPENDENCE (scipy.stats.chi2_contingency)")

chi2, p, dof, expected = chi2_contingency(observed)
expected_df = pd.DataFrame(expected, index=observed.index, columns=observed.columns)

print(f"Chi-square statistic : {chi2:.4f}")
print(f"Degrees of freedom   : {dof}   (= (3-1) x (3-1))")
print(f"p-value              : {p:.4e}")
print(f"Significance level   : alpha = {ALPHA}")
print("\nExpected table from scipy:")
print(expected_df.round(2))
print("\nSame as my hand calculation?", np.allclose(expected, expected_manual.values))

chi2_manual = (((observed.values - expected) ** 2) / expected).sum()
print(f"Manual chi-square = sum((O-E)^2/E) = {chi2_manual:.4f}")
assert dof == 4 and np.isclose(chi2, chi2_manual)

decision = "REJECT H0" if p < ALPHA else "FAIL TO REJECT H0"
print(f"\nDecision at alpha={ALPHA}: {decision}")

# Strength of association: Cramer's V (0 = none, 1 = perfect)
k = min(observed.shape) - 1
cramers_v = np.sqrt(chi2 / (n * k))
print(f"Cramer's V (effect size) = {cramers_v:.3f}")

std_resid = pd.DataFrame((observed.values - expected) / np.sqrt(expected),
                         index=observed.index, columns=observed.columns)
print("\nStandardised residuals (|value| > 2 means that cell differs a lot from independence):")
print(std_resid.round(2))

min_exp = float(expected.min())
pct_below5 = float((expected < 5).mean() * 100)
expected_df.to_csv(out("table_expected.csv"))
std_resid.to_csv(out("table_std_residuals.csv"))
pd.DataFrame({"statistic": ["chi2", "dof", "p_value", "alpha", "cramers_v", "n",
                            "min_expected_count", "pct_cells_expected_below_5"],
              "value": [chi2, dof, p, ALPHA, cramers_v, n, min_exp, pct_below5]}).to_csv(
    out("table_chi2_summary.csv"), index=False)

# ----------------------------------------------------------------------
# A6. Assumption checks
# ----------------------------------------------------------------------
title("A6. ASSUMPTION CHECKS")
print(f"1) Expected counts: smallest = {min_exp:.2f}; cells with E<5 = {pct_below5:.0f}%")
print("   Rule of thumb: all E >= 5 (or at most 20% of cells below 5, none below 1).",
      "->", "OK" if (pct_below5 <= 20 and min_exp >= 1) else "CHECK")
print("2) Categories are mutually exclusive and exhaustive: each day has exactly",
      "one rain_cat and one soil_cat ->", "OK" if n == len(df) else "CHECK")
print(f"3) Counts (not percentages) used, n = {n} days ->  OK")
print("4) Independence of observations: this is the weak point (see A7).")

# ----------------------------------------------------------------------
# A7. Temporal dependence
# ----------------------------------------------------------------------
title("A7. TEMPORAL DEPENDENCE (days are not independent samples)")

for col in ["soil_wetness", "rain_mm"]:
    print(f"Lag-1 autocorrelation of {col:14s}: {df[col].autocorr(lag=1):.3f}")
same = (df["soil_cat"].iloc[:-1].values == df["soil_cat"].iloc[1:].values).mean()
print(f"\nSoil class unchanged from one day to the next: {same*100:.1f}% of days")
print("(if days were independent with 3 equal classes, we'd expect about 33%)")

monthly = df.groupby(df["date"].dt.month).agg(n_days=("rain_mm", "size"),
                                              total_rain_mm_all_years=("rain_mm", "sum"),
                                              mean_rain_mm_per_day=("rain_mm", "mean"),
                                              mean_soil_wetness=("soil_wetness", "mean")).round(3)
monthly.index.name = "month"
print("\nBy calendar month (all years pooled): rain total and mean soil wetness (shows the shared monsoon season cycle):")
print(monthly.T.to_string())
monthly.to_csv(out("table_monthly_rain_soil.csv"))

# ----------------------------------------------------------------------
# Fast chi-square for the resampling tests below.
# Categories are turned into numbers 0,1,2 and the 3x3 table is counted with np.bincount.
# This is much faster than pd.crosstab + scipy inside a loop (that was why the old
# exhaustive test was slow on 1,460 rows). It is checked against scipy first.
# ----------------------------------------------------------------------
rain_codes = pd.Categorical(df["rain_cat"], categories=RAIN_ORDER).codes.astype(int)
soil_codes = pd.Categorical(df["soil_cat"], categories=SOIL_ORDER).codes.astype(int)


def fast_chi2(r_codes, s_codes):
    tab = np.bincount(r_codes * 3 + s_codes, minlength=9).reshape(3, 3).astype(float)
    exp = np.outer(tab.sum(axis=1), tab.sum(axis=0)) / tab.sum()
    return float((((tab - exp) ** 2) / exp).sum())


assert np.isclose(fast_chi2(rain_codes, soil_codes), chi2), "fast_chi2 disagrees with scipy"
print("\nfast_chi2 (used for resampling) equals scipy's chi-square on the real data: OK")

# (c) Circular-shift permutation test - EXHAUSTIVE (no random numbers, so it is exactly repeatable).
#     WHAT IS KEPT FIXED: the soil_cat column, and the rain_cat column's own day-to-day pattern
#     (we only rotate it as one block, wrapping the end back to the start).
#     WHAT IS BROKEN: the day-by-day match between rain and soil.
#     Every shift s from MIN_SHIFT to n-MIN_SHIFT-1 days is used, and chi-square is recomputed.
#     p = (number of shifts with chi2 >= real + 1) / (number of shifts + 1)
#     (the "+1" counts the real alignment itself).
#     Unlike a plain shuffle, this respects autocorrelation: runs of rainy / dry days stay together.
n_days_total = len(df)
shifts = np.arange(MIN_SHIFT, n_days_total - MIN_SHIFT)
perm_chi2 = np.array([fast_chi2(np.roll(rain_codes, int(s_)), soil_codes) for s_ in shifts])
n_ge = int(np.sum(perm_chi2 >= chi2))
perm_p = (n_ge + 1) / (len(perm_chi2) + 1)
print(f"\nCircular-shift permutation test: {len(shifts)} distinct shifts "
      f"({shifts.min()} to {shifts.max()} days), all of them used")
print(f"  Real chi-square = {chi2:.2f}")
print(f"  Shifts with chi-square >= real: {n_ge} of {len(shifts)}")
print(f"  Median / 95th percentile of shifted chi-squares = "
      f"{np.median(perm_chi2):.2f} / {np.percentile(perm_chi2, 95):.2f}")
print(f"  Permutation p-value = ({n_ge} + 1) / ({len(shifts)} + 1) = {perm_p:.4f}")

# Sensitivity: with 4 years of data, a shift close to a whole number of years (365, 730, 1095 days)
# puts the rain series back onto (nearly) the same season, so the shifted series are still
# seasonally aligned with soil. Show the result using only shifts at least 90 days away from that.
YEAR_DAYS = 365.25
SEASON_GAP = 90
off_year = np.minimum(shifts % YEAR_DAYS, YEAR_DAYS - shifts % YEAR_DAYS)
far = off_year >= SEASON_GAP
n_ge_far = int(np.sum(perm_chi2[far] >= chi2))
perm_p_far = (n_ge_far + 1) / (int(far.sum()) + 1)
print(f"\nSensitivity (shifts at least {SEASON_GAP} days away from a whole number of years): "
      f"{int(far.sum())} shifts, {n_ge_far} reached the real chi-square, "
      f"p = ({n_ge_far} + 1) / ({int(far.sum())} + 1) = {perm_p_far:.4f}")
print(f"  Median shifted chi-square for the shifts near a whole year (< {SEASON_GAP} days away): "
      f"{np.median(perm_chi2[~far]):.2f}; for the far shifts: {np.median(perm_chi2[far]):.2f}")
print("  Interpretation limits:")
print("  - The circular shift keeps both series' own autocorrelation, so it is a fairer null than a")
print("    plain shuffle, but the soil and rain series also share a yearly monsoon cycle. A shift near")
print("    a whole year keeps that cycle aligned, which makes the shifted chi-squares large and the")
print("    p-value conservative (large). So a non-significant permutation p-value means the data cannot")
print("    separate the rain-soil link from shared seasonality in this short 4-year record; it does NOT")
print("    show the variables are unrelated, and a small p-value would not prove causation either.")
print("  - It is exploratory, not a definitive test: only 4 seasonal cycles are available.")

# (d) Ordinary Monte Carlo p-value: shuffle rain_cat completely at random
#     (treats days as independent, like the textbook test, so it is NOT corrected for autocorrelation).
rng2 = np.random.default_rng(MC_SEED)
mc_chi2 = np.array([fast_chi2(rng2.permutation(rain_codes), soil_codes) for _ in range(N_MC)])
mc_ge = int(np.sum(mc_chi2 >= chi2))
mc_p = (mc_ge + 1) / (N_MC + 1)
print(f"\nMonte Carlo (random shuffle, {N_MC} times, seed {MC_SEED}): {mc_ge} shuffles reached the real chi-square")
print(f"  p-value = ({mc_ge} + 1) / ({N_MC} + 1) = {mc_p:.6f}  "
      f"(smallest possible with {N_MC} shuffles is {1/(N_MC+1):.6f}; read a value at that floor as 'p < about {1/(N_MC+1):.4f}')")
pd.DataFrame({"test": ["chi-square (scipy)", "Monte Carlo shuffle", "circular-shift permutation (exhaustive, all shifts)",
                       f"circular-shift permutation (shifts >= {SEASON_GAP} days from a whole year)"],
              "p_value": [p, mc_p, perm_p, perm_p_far],
              "n_resamples": [np.nan, N_MC, len(shifts), int(far.sum())],
              "random_seed": [np.nan, MC_SEED, np.nan, np.nan],
              "treats_days_as_independent": [True, True, False, False]}).to_csv(
    out("table_p_values_compared.csv"), index=False)
pd.DataFrame({"shift_days": shifts, "chi2": perm_chi2, "days_from_whole_year": off_year.round(1)}).to_csv(
    out("table_permutation_chi2_by_shift.csv"), index=False)

# (e) Year-by-year check: the same chi-square test inside each calendar year
yr_rows = []
for yr, g in df.groupby(df["date"].dt.year):
    tab_y = pd.crosstab(g["rain_cat"], g["soil_cat"]).reindex(index=RAIN_ORDER, columns=SOIL_ORDER).fillna(0)
    c2y, py, dfy, ey = chi2_contingency(tab_y)
    yr_rows.append({"year": int(yr), "n_days": int(tab_y.values.sum()), "chi2": c2y, "dof": dfy, "p_value": py,
                    "cramers_v": float(np.sqrt(c2y / (tab_y.values.sum() * 2))),
                    "min_expected_count": float(ey.min()),
                    "pct_cells_expected_below_5": float((ey < 5).mean() * 100)})
yearly = pd.DataFrame(yr_rows)
print("\nChi-square inside each calendar year (same test, one year at a time):")
print(yearly.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
print("Years with expected counts < 5 in some cells should be read with care.")
yearly.to_csv(out("table_yearly_chi2.csv"), index=False)
yearly_counts = (df.groupby([df["date"].dt.year.rename("year"), "rain_cat", "soil_cat"]).size()
                 .rename("n_days").reset_index())
yearly_counts.to_csv(out("table_yearly_counts.csv"), index=False)

# ----------------------------------------------------------------------
# A8. Graphs
# ----------------------------------------------------------------------
title("A8. GRAPHS")

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, tab, name in zip(axes, [observed, expected_df], ["Observed", "Expected under H0"]):
    im = ax.imshow(tab.values, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_xticklabels(SOIL_ORDER)
    ax.set_yticks(range(3)); ax.set_yticklabels(RAIN_ORDER)
    ax.set_xlabel("soil_cat"); ax.set_ylabel("rain_cat"); ax.set_title(name)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{tab.values[i, j]:.0f}", ha="center", va="center",
                    color="white" if tab.values[i, j] > tab.values.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
plt.tight_layout()
plt.savefig(out("graph1_observed_vs_expected.png"), dpi=150)
plt.close()

row_pct.plot(kind="bar", stacked=True, figsize=(7, 4.5), color=["#d95f02", "#e6ab02", "#1b9e77"])
plt.ylabel("% of days"); plt.xlabel("rain_cat"); plt.xticks(rotation=0)
plt.title("Soil moisture class by rain category")
plt.legend(title="soil_cat", loc="upper left", bbox_to_anchor=(1.02, 1.0))   # outside, so it hides no bar
plt.tight_layout()
plt.savefig(out("graph2_soil_mix_by_rain.png"), dpi=150)
plt.close()

plt.figure(figsize=(6, 4.5))
plt.imshow(std_resid.values, cmap="coolwarm", vmin=-6, vmax=6)
plt.xticks(range(3), SOIL_ORDER); plt.yticks(range(3), RAIN_ORDER)
for i in range(3):
    for j in range(3):
        plt.text(j, i, f"{std_resid.values[i, j]:.1f}", ha="center", va="center")
plt.colorbar(label="standardised residual")
plt.xlabel("soil_cat"); plt.ylabel("rain_cat")
plt.title("Where observed differs from expected")
plt.tight_layout()
plt.savefig(out("graph3_std_residuals.png"), dpi=150)
plt.close()

plt.figure(figsize=(7, 4.5))
plt.hist(perm_chi2, bins=40, color="#9ecae1", label="chi-square after shifting rain_cat")
plt.axvline(chi2, color="red", label=f"real chi-square = {chi2:.1f}")
plt.xlabel(f"chi-square from circularly shifted rain_cat ({len(shifts)} shifts, unitless)")
plt.ylabel("number of shifts (days)")
plt.title(f"Circular-shift permutation check (p = {perm_p:.3f})")
plt.legend()
plt.tight_layout()
plt.savefig(out("graph4_permutation_check.png"), dpi=150)
plt.close()
print("Saved graphs 1-4 in", OUT_DIR)

# ----------------------------------------------------------------------
# A9. Association versus causation
# ----------------------------------------------------------------------
title("A9. ASSOCIATION VS CAUSATION")
print("The test shows rain_cat and soil_cat are statistically associated.")
print("It does not prove that rain alone causes soil to be wetter: season (monsoon),")
print("temperature, humidity, evaporation and soil memory all move together with rain.")
print("\n>>> PART A COMPLETE <<<")

# ======================================================================
# PART B: IRRIGATION DECISION LOGIC
# ======================================================================
title("B1. PREPARE DATA FOR PART B")


def exclude_missing_next_day(data):
    """Keep only rows whose next-day outcome is known (soil_next_dry not missing)."""
    keep = data[data["soil_next_dry"].notna()].copy()
    keep["soil_next_dry"] = keep["soil_next_dry"].astype(int)
    return keep


dfb = exclude_missing_next_day(df)
print("Rows before exclusion:", len(df))
print("Rows with soil_next_dry missing (excluded):", int(df["soil_next_dry"].isna().sum()))
print("Rows used in Part B:", len(dfb))
print(f"Overall P(soil_next_dry = 1) = {dfb['soil_next_dry'].mean():.4f}")

# Self-test of the exclusion step: add a fake row with a missing outcome; it must be dropped.
_fake = df.iloc[[-1]].copy()
_fake["soil_next_dry"] = np.nan
_test = exclude_missing_next_day(pd.concat([df, _fake], ignore_index=True))
assert len(_test) == len(dfb), "missing next-day rows were NOT excluded"
print("Self-test passed: a row with a missing next-day outcome is excluded.")

title("B2. EXPECTED-COST DERIVATION OF THE THRESHOLD")
print("Irrigate today      -> cost = c_irr (for sure)")
print("Do not irrigate     -> cost = p x c_stress on average (stress happens only if soil is Dry tomorrow)")
print("Irrigate is better when  c_irr < p x c_stress,  i.e.  p > t = c_irr / c_stress")
print(f"Decision bands (src/decision.py): p >= upper = max({UPPER_DEFAULT}, t) IRRIGATE NOW; "
      "t <= p < upper DELAY & RE-CHECK; p < t DON'T IRRIGATE.")


def wilson_ci(k_, n_obs, z=1.96):
    """95% Wilson interval for a proportion k_/n_obs. Assumes independent days,
    so with autocorrelated daily data it is too narrow."""
    if n_obs == 0:
        return (np.nan, np.nan)
    phat = k_ / n_obs
    denom = 1 + z**2 / n_obs
    centre = (phat + z**2 / (2 * n_obs)) / denom
    half = z * np.sqrt(phat * (1 - phat) / n_obs + z**2 / (4 * n_obs**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def condition_stats(soil_state, rain_state=None, data=dfb):
    """Count days matching the condition and how many were followed by a Dry day."""
    mask = data["soil_cat"] == soil_state
    if rain_state is not None:
        mask &= data["rain_cat"] == rain_state
    sub = data[mask]
    return len(sub), int(sub["soil_next_dry"].sum())


def run_condition(soil_state, rain_state, c_irr, c_stress):
    """Counts -> decide_from_counts() in src/decision.py (the same function the backend uses)."""
    n_cond, k_ = condition_stats(soil_state, rain_state)
    row = {"soil_cat": soil_state, "rain_cat": rain_state, "n_days": n_cond, "n_next_day_dry": k_}
    row.update(decide_from_counts(k_, n_cond, c_irr, c_stress))
    if n_cond == 0:
        row.update({"ci95_low": np.nan, "ci95_high": np.nan})
    else:
        lo, hi = wilson_ci(k_, n_cond)
        row.update({"ci95_low": round(lo, 4), "ci95_high": round(hi, 4)})
    return row


def show(row):
    print(f"\nCondition: soil_cat = {row['soil_cat']}, rain_cat = {row['rain_cat']}")
    print(f"  valid observations (days) : {row['n_days']}")
    print(f"  next-day Dry outcomes     : {row['n_next_day_dry']}")
    print(f"  p_dry_tomorrow            : {row['p_dry_tomorrow']}"
          + ("   (undefined: no matching days)" if row["n_days"] == 0 else ""))
    print(f"  95% Wilson interval       : ({row['ci95_low']}, {row['ci95_high']})")
    print(f"  threshold                 : {row['threshold']}")
    print(f"  decision                  : {row['decision']}")
    print(f"  reason                    : {row['reason']}")


conditions = [("Dry", "None"), ("Moderate", "Light"), ("Wet", "Heavy")]
COLS = ["soil_cat", "rain_cat", "n_days", "n_next_day_dry", "p_dry_tomorrow",
        "ci95_low", "ci95_high", "threshold", "decision", "low_support", "reason"]
# Any three-condition result that has n < MIN_SUPPORT is printed with a visible warning below.

title("B3. THREE REQUIRED CONDITIONS (c_irr = 1, c_stress = 3, t = 1/3)")
res1 = pd.DataFrame([run_condition(s_, r_, 1, 3) for s_, r_ in conditions])[COLS]
for _, r in res1.iterrows():
    show(r)
    if r["low_support"]:
        print(f"  *** LOW-SUPPORT WARNING: fewer than {MIN_SUPPORT} matching days ***")
print("\nSummary table:")
print(res1[["soil_cat", "rain_cat", "n_days", "n_next_day_dry",
            "p_dry_tomorrow", "threshold", "decision"]].to_string(index=False))
res1.to_csv(out("partB_decision_results.csv"), index=False)

title("B4. SAME CONDITIONS WITH DIFFERENT COSTS (c_irr = 2, c_stress = 3, t = 2/3)")
res2 = pd.DataFrame([run_condition(s_, r_, 2, 3) for s_, r_ in conditions])[COLS]
print(res2[["soil_cat", "rain_cat", "n_days", "n_next_day_dry",
            "p_dry_tomorrow", "threshold", "decision"]].to_string(index=False))
res2.to_csv(out("partB_decision_results_cost2.csv"), index=False)

compare = pd.DataFrame({"soil_cat": res1["soil_cat"], "rain_cat": res1["rain_cat"],
                        "decision_t_1/3": res1["decision"], "decision_t_2/3": res2["decision"]})
compare["changed"] = compare["decision_t_1/3"] != compare["decision_t_2/3"]
print("\nDid the decision change when t moved from 1/3 to 2/3?")
print(compare.to_string(index=False))
if not compare["changed"].any():
    ps = ", ".join(f"{r_['soil_cat']}+{r_['rain_cat']}: p = {r_['p_dry_tomorrow']:.4f}" for _, r_ in res1.iterrows())
    print(f"-> No decision changed. Observed probabilities: {ps}.")
    print("   None of them lies between t = 1/3 and t = 2/3 (the only region where the two cost settings")
    print("   disagree), so the cost change does not alter these three decisions. This is an honest result.")
else:
    print("-> The decision changed for the rows marked True above (p lies between 1/3 and 2/3).")

# Which of the nine cells would change at all? (any cell with an observed p between 1/3 and 2/3)
print("\nHYPOTHETICAL illustration only (p = 0.50 is NOT a data result): how the cost ratio moves the decision")
for ci_, cs_ in [(1, 3), (2, 3)]:
    r = decide(0.5, ci_, cs_, 50)
    print(f"  p = 0.50, c_irr = {ci_}, c_stress = {cs_}: t = {r['threshold']:.4f} -> {r['decision']}")

title("B5. ALL 9 SOIL x RAIN COMBINATIONS (both cost settings, low-support flag)")
rows9 = []
for s_ in SOIL_ORDER:
    n_s, k_s = condition_stats(s_, None)
    for r_ in RAIN_ORDER:
        a = run_condition(s_, r_, 1, 3)
        b = run_condition(s_, r_, 2, 3)
        a["decision_c_irr2_c_stress3"] = b["decision"]
        a["decision_changed_by_cost"] = a["decision"] != b["decision"]
        # Guide issue #3 says low-support cells could FALL BACK to P(dry tomorrow | soil only).
        # Member 3's own prompt says only ADD A WARNING. The group has not chosen, so the soil-only
        # numbers are given for reference and the official decision stays as computed from the cell.
        a["n_soil_only"] = n_s
        a["p_dry_given_soil_only"] = round(k_s / n_s, 4) if n_s else np.nan
        a["fallback_decision_soil_only_NOT_APPROVED"] = (
            decide_from_counts(k_s, n_s, 1, 3)["decision"] if a["low_support"] else "")
        rows9.append(a)
all9 = pd.DataFrame(rows9)
cols9 = ["soil_cat", "rain_cat", "n_days", "n_next_day_dry", "p_dry_tomorrow", "decision",
         "decision_c_irr2_c_stress3", "decision_changed_by_cost", "low_support", "p_dry_given_soil_only",
         "fallback_decision_soil_only_NOT_APPROVED"]
print(all9[cols9].to_string(index=False))
print("\nCells with fewer than", MIN_SUPPORT, "days (low support):", int(all9["low_support"].sum()))
for _, r_ in all9[all9["low_support"]].iterrows():
    print(f"  *** LOW-SUPPORT WARNING: {r_['soil_cat']} + {r_['rain_cat']} has only {r_['n_days']} matching days "
          f"-> decision = {r_['decision']}. Reference only (guide issue #3, not approved): "
          f"P(dry tomorrow | {r_['soil_cat']} only) = {r_['p_dry_given_soil_only']} would give "
          f"{r_['fallback_decision_soil_only_NOT_APPROVED']}.")
print("Cells whose decision changes between (1,3) and (2,3):", int(all9["decision_changed_by_cost"].sum()))
all9.drop(columns=["reason"]).to_csv(out("partB_all_9_combinations.csv"), index=False)
all9[["soil_cat", "rain_cat", "reason"]].to_csv(out("partB_all_9_reasons.csv"), index=False)

title("B6. DOES RAIN ADD ANYTHING BEYOND TODAY'S SOIL? (persistence check)")
rows_cmp = []
for s_ in SOIL_ORDER:
    n_s, k_s = condition_stats(s_, None)
    row = {"soil_cat": s_, "n_soil_only": n_s, "P_dry_tomorrow_given_soil": round(k_s / n_s, 4)}
    for r_ in RAIN_ORDER:
        n_c, k_c = condition_stats(s_, r_)
        row[f"P_given_soil_and_{r_}"] = round(k_c / n_c, 4) if n_c else np.nan
        row[f"n_{r_}"] = n_c
    rows_cmp.append(row)
cmp_df = pd.DataFrame(rows_cmp)
print(cmp_df.to_string(index=False))
print("If P(soil and rain) is close to P(soil only), today's soil already carries most of the")
print("information, because today's soil state already contains today's rain.")
cmp_df.to_csv(out("partB_soil_only_vs_soil_rain.csv"), index=False)

# ----------------------------------------------------------------------
# B6b. WORKED EXAMPLE: 20 real consecutive rows, counted by hand
# ----------------------------------------------------------------------
title("B6b. WORKED EXAMPLE FROM 20 CONSECUTIVE ROWS (demonstration only)")
# Rule used to pick the window (so the choice is not cherry-picked): the FIRST run of 20
# consecutive rows that contains all three rain_cat, at least one Dry day, and both
# soil_next_dry values (0 and 1). (A window with all 3 rain AND all 3 soil classes does not exist
# in this dataset: soil changes class slowly, so Dry and Wet days are far apart.)
win = None
for i0 in range(0, len(dfb) - 19):
    w = dfb.iloc[i0:i0 + 20]
    if (set(w["rain_cat"]) == set(RAIN_ORDER) and "Dry" in set(w["soil_cat"])
            and w["soil_next_dry"].nunique() == 2):
        win = w
        break
if win is None:
    print("No 20-row window meeting the rule found in this dataset; skipping worked example.")
else:
    show_cols = ["date", "rain_mm", "soil_wetness", "rain_cat", "soil_cat", "soil_next_dry"]
    w_out = win[show_cols].copy()
    w_out["date"] = w_out["date"].dt.strftime("%Y-%m-%d")
    print(w_out.to_string(index=False))
    N20 = len(win)
    # counted with plain Python loops so it is easy to repeat by hand / with COUNTIFS
    n_dry = sum(1 for s_ in win["soil_cat"] if s_ == "Dry")
    n_none = sum(1 for r_ in win["rain_cat"] if r_ == "None")
    n_dry_none = sum(1 for s_, r_ in zip(win["soil_cat"], win["rain_cat"]) if s_ == "Dry" and r_ == "None")
    k_dry = sum(1 for s_, y_ in zip(win["soil_cat"], win["soil_next_dry"]) if s_ == "Dry" and y_ == 1)
    n_dry_light = sum(1 for s_, r_ in zip(win["soil_cat"], win["rain_cat"]) if s_ == "Dry" and r_ == "Light")
    k_dry_light = sum(1 for s_, r_, y_ in zip(win["soil_cat"], win["rain_cat"], win["soil_next_dry"])
                      if s_ == "Dry" and r_ == "Light" and y_ == 1)
    print(f"\nN = {N20} rows ({w_out['date'].iloc[0]} to {w_out['date'].iloc[-1]})")
    print(f"n(Dry) = {n_dry};  n(None) = {n_none};  n(Dry and None) = {n_dry_none}")
    print(f"P(S=Dry) = {n_dry}/{N20} = {n_dry/N20:.4f};  P(R=None) = {n_none}/{N20} = {n_none/N20:.4f}")
    print(f"P(Dry and None) = {n_dry_none}/{N20} = {n_dry_none/N20:.4f};  "
          f"P(Dry) x P(None) = {n_dry/N20 * n_none/N20:.4f}   (equal would mean independent in this tiny sample)")
    print(f"P(soil_next_dry=1 | Dry) = n(Dry and next Dry) / n(Dry) = {k_dry}/{n_dry} = {k_dry/n_dry:.4f}")
    print(f"P(soil_next_dry=1 | Dry, Light) = {k_dry_light}/{n_dry_light} = {k_dry_light/n_dry_light:.4f}"
          if n_dry_light else "No Dry+Light rows in the window.")
    print("(20 rows are for demonstration only; the main tables use all rows.)")
    w_out.to_csv(out("worked_example_20rows.csv"), index=False)
    pd.DataFrame({"quantity": ["N", "n(Dry)", "n(None)", "n(Dry and None)", "n(Dry and next Dry)",
                               "n(Dry and Light)", "n(Dry and Light and next Dry)"],
                  "value": [N20, n_dry, n_none, n_dry_none, k_dry, n_dry_light, k_dry_light]}).to_csv(
        out("worked_example_20rows_counts.csv"), index=False)

# ----------------------------------------------------------------------
title("B7. GRAPH")
plt.figure(figsize=(7, 4.5))
labels = [f"{r['soil_cat']}+{r['rain_cat']}\n(n={r['n_days']})" for _, r in res1.iterrows()]
probs = res1["p_dry_tomorrow"].values
errs_low = probs - res1["ci95_low"].values
errs_high = res1["ci95_high"].values - probs
plt.bar(labels, probs, yerr=[errs_low, errs_high], capsize=6, color="#74a9cf")
t_default = float(res1["threshold"].iloc[0])
plt.axhline(t_default, color="red", linestyle="--", label=f"threshold t = {t_default:.3f}")
plt.axhline(max(UPPER_DEFAULT, t_default), color="green", linestyle="--",
            label=f"IRRIGATE NOW cut-off = {max(UPPER_DEFAULT, t_default):.2f}")
plt.ylim(0, 1.05)
plt.ylabel("P(soil_next_dry = 1)")
plt.title("Estimated chance of Dry soil tomorrow (with 95% interval)")
plt.legend()
plt.tight_layout()
plt.savefig(out("graph5_partB_decisions.png"), dpi=150)
plt.close()
print("Saved graph5_partB_decisions.png")

title("DONE")
print("All outputs are in the folder:", OUT_DIR)
print("Note: the decision rule is an exploratory statistical exercise on one location's")
print("data, not a validated agricultural recommendation.")
