# Member 3 Audit – IrrigAI (Group 6), second audit on the approved 2022–2025 dataset

**What was inspected:** the guide `IrrigAI_Group_6_-_Upgraded_Project_Guide_Prompts_and_Sources.docx` (read in full), the approved dataset `g6_irrigation_data_fixed.csv`, and everything in `IrrigAI_Member3_fixed.zip` (old 2025-only `data/g6_irrigation_data.csv`, `src/` ×5 files, 14 CSVs + 5 PNGs + 1 XLSX + run log in `results/`, the report and the first audit, `requirements_member3.txt`).
**What was NOT supplied:** the raw NASA file (`IrrigAI_Kolhapur_Combined_2022_2025.csv`), the group's root `requirements.txt`, Member 2's `probability.py`, any notebook, any README, any backend code.

Status labels: **CONFIRMED** (checked by running code on the files) · **CONFLICT** (guide and data/design disagree) · **FIXED** (changed in this pass) · **UNABLE TO VERIFY** (needed file not supplied).

Environment used for every run: Python 3.13.16, pandas 3.0.5, numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2, openpyxl 3.1.5, LibreOffice (headless) for the Excel recalculation.

---
## Top points to act on

1. **The approved CSV satisfies the guide.** 1,460 rows, 2022-01-01 → 2025-12-30 (the guide's 1,461 raw days minus the last day, which has no "tomorrow"). The old 2025-only dataset (364 rows) is replaced, and every output was regenerated from the new file.
2. **Dry + Heavy has 0 days in the new data.** `decide()` needs n ≥ 1, so this cell is now reported as **NO DATA** (p undefined, not 0) with a visible low-support warning. **Group decision needed:** the guide's issue #3 says to fall back to P(Dry tomorrow | soil only) for low-support cells (0.9880 → IRRIGATE NOW), while Member 3's prompt says only add a warning. I did not choose; the soil-only value is shown in a column labelled `fallback_decision_soil_only_NOT_APPROVED`. Member 4's backend must handle this cell (see `decide_from_counts`).
3. **The circular-shift permutation test is not significant (p = 0.348) while chi-square gives p ≈ 2.6 × 10⁻⁸⁶.** This is explained in the report (shared monsoon cycle; only 4 cycles) and is not a bug. It must not be presented as proof that rain and soil are unrelated, nor as a definitive test.
4. **Cost sensitivity flips nothing** (0 of 9 cells; the three required scenarios have p = 0.9979, 0, 0). Do not tell the examiner a decision flips; only the hypothetical p = 0.50 does.
5. **Old permutation code did not fail here.** The first audit's exhaustive test took 31 s on the new data in this environment (it ran, exit 0). It was still slow because it called `pd.crosstab` + scipy 1,400 times; the new version counts the 3×3 table with `np.bincount` and runs the whole script in about 3 s. If it "timed out" on your machine, the new version should fix it.
6. **A 20-row worked example no longer existed.** The old window rule (all 3 rain × all 3 soil classes) matches no window in the 2022–2025 data, so the script skipped the example. Rule relaxed and documented (see Audit 3).

---
## AUDIT 1 – Dataset (old vs approved)

| Check | Old (in ZIP) | New (approved CSV) | Result |
|---|---|---|---|
| Rows | 364 | **1,460** | CONFIRMED (as expected) |
| Date range | 2025-01-01 → 2025-12-30 | **2022-01-01 → 2025-12-30** | CONFIRMED; consecutive days, no duplicates, rows per year 365 / 365 / 366 / 364 |
| Columns | date, rain_mm, soil_wetness, rain_cat, soil_cat, soil_next_dry | same, same order | CONFIRMED |
| Missing values (reading with `keep_default_na=False`) | 0 | 0 | CONFIRMED |
| `"None"` rain category | 232 days | **993 days** | CONFIRMED; plain `pd.read_csv` would make these 993 NaN (the scripts use `keep_default_na=False`) |
| Data types | float / str / int | float / str / int (`soil_next_dry` is int64, only 0/1: 961 zeros, 499 ones) | CONFIRMED |
| rain_cat rule (None < 2.5, Light 2.5–15.5, Heavy > 15.5) | consistent | **0 mismatches in 1,460 rows**; None 0–2.49, Light 2.50–15.31, Heavy 15.53–94.61; the one row exactly on a boundary (2022-07-31, 2.5 mm) is Light, as the guide rule requires | CONFIRMED |
| soil_cat = tertiles of soil_wetness | cut points 0.288 / 0.441 | cut points **0.53 / 0.81** recomputed from the data; **0 mismatches**, same result as `pd.qcut` | CONFIRMED |
| Soil class balance | 123 / 120 / 121 | 499 / 485 / 476 (34.2 / 33.2 / 32.6 %) | CONFIRMED; not exactly one third because soil_wetness has 2 decimals and many days tie at a cut point (172 days sit at the minimum 0.50). This is now stated in the report |
| soil_next_dry = (tomorrow's soil_cat == Dry) | OK | **0 mismatches in rows 1–1,459** | CONFIRMED. The last row (30 Dec 2025) cannot be re-checked because 31 Dec is not in the file |
| Rows excluded from conditional probabilities | none | **none**: all 1,460 have a known next-day outcome | CONFIRMED. The exclusion code stays (self-test with a fake missing row passes) |
| Soil variable | 7–28 cm layer, 0.271–0.509 | values 0.50–0.99 (0–1 scale) | The CSV does not name its NASA variable and the raw file is not supplied, so **GWETROOT cannot be verified** (UNABLE TO VERIFY). The old "not GWETROOT" conflict is no longer visible in the file |
| Guide point on "Heavy" label | max 56.71 mm | max 94.61 mm; 3 days above 64.4 mm | Footnote rewritten from computed values (old text "no day reaches IMD Heavy" was true only for 2025 and is now false) |

**Old / inconsistent items inside the ZIP**
- `data/g6_irrigation_data.csv` (364 rows, 2025 only): **replaced** by the approved file (byte-identical to the supplied CSV; same filename).
- `src/build_dataset.py`: obsolete. It keeps only 2025, reads a raw file that is not in the repo, and would have **overwritten the approved dataset with the 2025-only file**. It is kept (it may belong to Member 1) but now stops with a message unless `--legacy-2025-only` is passed. It was not run.
- Old `results/` (2025 numbers) and the old report numbers: all regenerated or rewritten; `results/` was emptied before the final run, so no 2025-only file remains.
- The approved dataset was **not rebuilt**; no raw source was available.

---
## AUDIT 2 – Part A (independence), actual results on 1,460 rows

| Item | Result |
|---|---|
| H0 / H1, α = 0.05 | In script and report |
| Observed table (rain rows None/Light/Heavy; soil Dry/Moderate/Wet) | 466, 360, 167 / 33, 93, 201 / 0, 32, 108 |
| Expected table | 339.39, 329.87, 323.75 / 111.76, 108.63, 106.61 / 47.85, 46.51, 45.64 (hand formula = scipy) |
| Joint vs P(S)P(R), all 9 cells | `results/table_joint_vs_product_9cells.csv` (differences from −0.107 to +0.087) |
| Chi-square | χ² = 404.7609, df = 4, p = 2.6037 × 10⁻⁸⁶; scipy = hand sum = Excel CHIDIST |
| Cramér's V (guide asks for it) | 0.3723 |
| Expected-count check | smallest 45.64; 0% of cells below 5 (condition met) |
| Standardised residuals | −8.71 … +9.23 (largest: Wet with Heavy +9.23, Light +9.14; Wet with None −8.71) |
| Monte Carlo shuffle | 10,000 shuffles, seed 7: 0 reached the real χ², p = 1/10,001 = 0.0001 (the floor) |
| Circular-shift permutation | see below |
| Yearly χ² (`table_yearly_chi2.csv`) | 2022: 95.39; 2023: 68.31; 2024: 122.19; 2025: 116.05 (all df 4, p ≤ 6 × 10⁻¹⁴). 2023 has 1 of 9 cells with expected 3.92 (< 5) |
| Autocorrelation | lag-1: soil 0.999, rain 0.702; soil class unchanged on 98.1% of days |

**Permutation test – what was changed and why.**
- *Old:* exhaustive circular shifts, but each shift used `pd.crosstab` + `chi2_contingency` (slow); plain shuffle with 5,000 draws.
- *Method kept (valid and guide-compatible):* rotate `rain_cat` as one block (wrapping around) while `soil_cat` is fixed, for **every** shift from 30 to 1,429 days (1,400 shifts, no randomness). This keeps each series' own day-to-day pattern, which a day-by-day shuffle would destroy. p = (shifts with χ² ≥ real + 1) / (shifts + 1).
- *Made fast:* categories → integer codes, 3×3 table by `np.bincount`, χ² by NumPy; the fast function is asserted equal to scipy's χ² on the real data. (The fast result reproduced the same 487 of 1,400 as the old slow code on the new CSV, a consistency check.)
- *Result:* 487 of 1,400 shifts reached the real χ² → **p = 0.3483**. Median shifted χ² 296.5; 95th percentile 581.3. Sensitivity using only the 742 shifts ≥ 90 days from a whole number of years: 254 reached it, **p = 0.3432**.
- *Limitation:* soil and rain share one yearly monsoon cycle and the record has only 4 cycles, so shifted series still look strongly associated. The test is **exploratory**, cannot separate causation from shared seasonality, and a large p does not show independence.
- Monte Carlo shuffle: random numbers are seeded (7) and the p-value is reported as a floor, not as "exactly 0.0001". It treats days as independent, so it is no better than the textbook p-value on this point.

---
## AUDIT 3 – Part B (decision logic), actual results

| Condition (c_irr = 1, c_stress = 3, t = 1/3) | n | next-day Dry | p | 95% Wilson | Decision | Costs (2, 3), t = 2/3 |
|---|---|---|---|---|---|---|
| Dry + None | 466 | 465 | 0.9979 | 0.988–1.000 | IRRIGATE NOW | IRRIGATE NOW |
| Moderate + Light | 93 | 0 | 0.0000 | 0.000–0.040 | DON'T IRRIGATE | DON'T IRRIGATE |
| Wet + Heavy | 108 | 0 | 0.0000 | 0.000–0.034 | DON'T IRRIGATE | DON'T IRRIGATE |

All nine cells are in `results/partB_all_9_combinations.csv` (and the reasons in `partB_all_9_reasons.csv`). The only non-extreme probabilities are Dry + Light (28/33 = 0.8485) and Moderate + None (6/360 = 0.0167); **no decision in any cell changes between the two cost settings**. The only low-support cell is **Dry + Heavy (n = 0)** → NO DATA (see Top points).

| Requirement | Result |
|---|---|
| Rules and boundaries vs guide Section 2/4 (`upper = max(0.75, t)`; p ≥ upper IRRIGATE; t ≤ p < upper DELAY; p < t DON'T) | CONFIRMED in `decision.py`; boundary tests pass (p = t → DELAY, p = upper → IRRIGATE) |
| Costs > 0 validation, p in [0, 1], n whole number | CONFIRMED (invalid input raises `ValueError`) |
| Required keys `p_dry_tomorrow, threshold, decision, reason` (+ `n`, `low_support`) | CONFIRMED |
| Low-support flag (n < 10), visible in output | CONFIRMED: appears in the console log, in the `reason` text and in the `low_support` column. The three required conditions all have n ≥ 93, so none triggers it |
| Missing next-day rows excluded | CONFIRMED (self-test; none missing in this dataset) |
| 20-row worked example | **FIXED**: old rule matched no window. New rule (first window with all 3 rain classes, ≥ 1 Dry day, both soil_next_dry values) → 30 Apr – 19 May 2022. n(Dry) 19, n(None) 18, n(Dry∧None) 18, P(Dry) 0.95, P(None) 0.90, P(Dry)P(None) 0.855, P(next Dry \| Dry) = 18/19. Excel COUNTIFS matches (7 comparison cells MATCH). The old example counted "Dry + Heavy"; this window has none, so it counts "Dry + Light" (1 day) instead |
| Guide inconsistency (issue #3 vs Member 3 prompt on low-support fallback) | **CONFLICT, not resolved by me** (see Top points). Needs a group decision |

---
## AUDIT 4 – Code quality and integration

| Check | Result |
|---|---|
| `python src/irrigai_analysis_g6.py` from the repo root | CONFIRMED, exit 0, ~3 s |
| Same command from another working directory (`cd /tmp`) | CONFIRMED, exit 0 (paths start at the repo root) |
| `python src/test_decision.py` | CONFIRMED: **12 test groups passed** (6 existing + 6 added) |
| Tests added | numpy/pandas number types; exact boundaries when p = k/n (1/3, 3/4, 2/3, 0, 1); zero and one are not certainty; n = 0 "NO DATA" cell; k/n validation; low-support via counts |
| Tests existing and still passing | default costs and boundaries; cost sensitivity (2, 3); upper = max(0.75, t) incl. t > 1; low-support flag; required keys; invalid input (16 bad argument sets) |
| `decision.py` | Kept. `decide(p, c_irr, c_stress, n)` unchanged (guide signature). **Added** `decide_from_counts(k, n, c_irr, c_stress)`, which the analysis script now calls (so the backend and the analysis use the same code); it returns `NO DATA` / `p_dry_tomorrow: None` for n = 0 instead of raising |
| `pytest` | Not installed in this environment, so pytest itself was **not run**; the tests are plain functions and also run with `python src/test_decision.py` |
| Excel workbook | Rebuilt by `src/make_verification_xlsx.py`, recalculated with LibreOffice, then re-opened: 74 formulas, no error values, **17 MATCH / 0 CHECK**. Includes the Dry + Heavy n = 0 row (p "undefined" in both) |
| Graphs | Five PNGs regenerated and each opened and looked at. Graph 2's legend covered part of the Heavy bar; moved outside the plot and regenerated. Titles, axis labels and legends present. No visual check of the other graph details beyond that |
| Hard-coded results | None. Everything printed or saved comes from the CSV. The report text is static and was checked against the CSVs (see below) |
| Root `requirements.txt` | **UNABLE TO VERIFY** (not supplied). `requirements_member3.txt` lists pandas, numpy, scipy, matplotlib, openpyxl (with tested versions) to merge into the group's file. I did not create a root `requirements.txt` so I would not overwrite the group's |
| README / notebooks | None supplied; none changed |
| Not tested | the real raw NASA file; GWETROOT identity; Member 2's `probability.py`; any FastAPI call to `decide()` / `decide_from_counts()`; pytest; Python/library versions other than those above |

---
## Files changed or added (nothing outside Member 3's folder was touched)
- `data/g6_irrigation_data.csv` – **replaced** with the approved 1,460-row file.
- `src/irrigai_analysis_g6.py` – updated (new dataset text, tertile and boundary checks, fast permutation, Monte Carlo with seed, yearly tables, `decide_from_counts`, NO DATA handling, soil-only reference columns, new 20-row rule, graph fixes).
- `src/decision.py` – `decide_from_counts` added; `decide` untouched.
- `src/test_decision.py` – 6 test groups added.
- `src/make_verification_xlsx.py` – worked-example items now Dry + Light; Dry + Light and Dry + Heavy (n = 0) rows added; note text updated.
- `src/build_dataset.py` – guard added (obsolete 2025-only builder); logic untouched.
- `results/*` – all regenerated (28 files); new: `table_yearly_chi2.csv`, `table_yearly_counts.csv`, `table_permutation_chi2_by_shift.csv`.
- `docs/irrigai_report_and_viva_g6.md`, `docs/MEMBER3_AUDIT.md` – rewritten for the new dataset (23 viva questions).
- `requirements_member3.txt` – tested versions updated.

## Commands run (all from the repository root unless stated)
`python3 -I audit_data.py new.csv old.csv` (dataset audit, outside the repo) · old script on the new CSV in a scratch copy (`timeout 100`, exit 0, 31 s, worked example skipped) · `python src/irrigai_analysis_g6.py` (exit 0, ~3 s; run twice, the second time from `/tmp`) · `python src/make_verification_xlsx.py` · `soffice --headless --calc --convert-to xlsx` (recalculation) · `python src/test_decision.py` (12 groups passed; run from the repo root and from `/tmp`) · `python src/build_dataset.py` (confirms the guard exits without touching the data) · a small script outside the repo (`check_report.py`) that recomputes the key numbers from `results/*.csv` and the dataset and looks for them in the report and this audit.

## Report-versus-output check
The numbers in the report (counts, observed/expected/residual cells, joint-probability cells, χ², p-values, V, probabilities, Wilson upper limits, permutation counts, yearly χ² and V, autocorrelations, tertile cut points, worked-example counts) were recomputed from `results/*.csv` and the dataset and searched for in the report by `check_report.py`. Result: every number was found; the single flag was a wording difference ("487 of 1,400" is written "487 of the 1,400"), not a numeric mismatch. The check only proves the numbers match the outputs, not that the interpretation is right; the Wilson lower/upper pair and a few rounded sentences were also read by eye.
