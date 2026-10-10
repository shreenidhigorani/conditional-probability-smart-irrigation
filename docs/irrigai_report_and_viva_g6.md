# IrrigAI – Member 3 (approved 2022–2025 dataset, Group 6 guide definitions)
All numbers come from running `python src/irrigai_analysis_g6.py` on `data/g6_irrigation_data.csv`; outputs are in `results/` (full console log: `results/run_log.txt`).
Excel cross-check: `results/IrrigAI_member3_excel_verification.xlsx` (COUNTIFS / SUMPRODUCT / CHIDIST formulas; all 17 comparison cells show MATCH).
Decision rule code: `src/decision.py` (tests: `python src/test_decision.py`, 12 test groups pass).

## Data used
- [Our dataset result] **1,460 daily rows, 1 Jan 2022 – 30 Dec 2025** (2022: 365, 2023: 365, 2024: 366, 2025: 364 rows), no missing values, no duplicate dates, consecutive days. The guide expects 1,461 raw rows for 2022–2025; 31 Dec 2025 has no "tomorrow", so it is not in the file and 1,460 is the expected processed size. Columns follow the agreed schema: date, rain_mm, soil_wetness, rain_cat, soil_cat, soil_next_dry.
- [Published fact, from the guide] Source: NASA POWER daily data for Kolhapur, community AG; rainfall PRECTOTCORR (mm/day) and root-zone soil wetness GWETROOT (0–1). [Assumption] The CSV does not say which NASA variable `soil_wetness` is, and the raw NASA file was not supplied, so we could not verify that it is GWETROOT (its values run 0.50–0.99 on a 0–1 scale, which is consistent with it). These are modelled/satellite-derived estimates (MERRA-2), **not sensor data**.
- rain_cat (guide rule): None < 2.5 mm (993 days), Light 2.5–15.5 mm (327 days), Heavy > 15.5 mm (140 days). The one day exactly on a boundary (31 Jul 2022, 2.5 mm) is Light, as the guide rule requires. Footnote: the guide quotes the IMD scale as Light 2.5–15.5, Moderate 15.6–64.4, Heavy 64.5–115.5 mm/day [Published fact as stated in the guide; not re-checked on the IMD site]. Our "Heavy" therefore means "more than 15.5 mm" (IMD "moderate or heavier"). The wettest day was 94.61 mm; only 3 days exceed 64.4 mm.
- soil_cat: tertiles of soil_wetness computed from all 1,460 rows. Cut points: 1/3 quantile = 0.53, 2/3 quantile = 0.81 (Dry ≤ 0.53, Moderate 0.54–0.81, Wet ≥ 0.82). Counts: Dry 499 (34.2%), Moderate 485 (33.2%), Wet 476 (32.6%). The classes are not exactly one third each because soil_wetness has only 2 decimals and many days tie at a cut point (172 days sit at the minimum value 0.50). Tertiles force P(Dry) to be about 1/3 by construction; the interesting result is how P(Dry tomorrow) changes with today's conditions.
- soil_next_dry = 1 if tomorrow's soil_cat is Dry. Checked for every row except the last (the last row's tomorrow is not in the file). No row has a missing outcome, so all 1,460 rows are used in the Part B denominators; the code still excludes any row with a missing outcome (self-tested).
- The text "None" is a real category. A plain `pd.read_csv()` would turn all 993 "None" rain days into missing values; the code reads with `keep_default_na=False`.

## PART A – Report text
**Hypotheses.** H0: rain_cat and soil_cat are independent; H1: they are associated. Significance level α = 0.05.

**Observed and expected frequencies.** Observed (rows None, Light, Heavy; columns Dry, Moderate, Wet): None = 466, 360, 167; Light = 33, 93, 201; Heavy = 0, 32, 108 (row totals 993, 327, 140; column totals 499, 485, 476). Expected under independence, (row total × column total)/1460: None 339.39, 329.87, 323.75; Light 111.76, 108.63, 106.61; Heavy 47.85, 46.51, 45.64.

**Expected-frequency check.** The smallest expected count is 45.64 and 0% of cells have an expected count below 5, so the chi-square cell-size condition is met for the full data set. (Inside single years, 2023 has one cell with expected 3.92; see the yearly table below.)

**Joint probability versus P(S)P(R) (all nine cells).** Format: P(S∧R) vs P(S)P(R) (difference).

| rain \ soil | Dry | Moderate | Wet |
|---|---|---|---|
| None | 0.3192 vs 0.2325 (+0.087) | 0.2466 vs 0.2259 (+0.021) | 0.1144 vs 0.2217 (−0.107) |
| Light | 0.0226 vs 0.0765 (−0.054) | 0.0637 vs 0.0744 (−0.011) | 0.1377 vs 0.0730 (+0.065) |
| Heavy | 0.0000 vs 0.0328 (−0.033) | 0.0219 vs 0.0319 (−0.010) | 0.0740 vs 0.0313 (+0.043) |

If the variables were independent every difference would be about 0. They are not: Wet soil with Light or Heavy rain is far more common than independence predicts, and Dry soil with Heavy rain never occurred (0 of 140 Heavy days).

**Hypothesis test.** `chi2_contingency`: χ² = 404.76, df = 4, p ≈ 2.6 × 10⁻⁸⁶, so H0 is rejected at α = 0.05. Effect size Cramér's V = 0.372 (a moderate-to-strong association [Interpretation]). Standardised residuals (|value| > 2 = cell differs a lot from independence): None: Dry +6.87, Moderate +1.66, Wet −8.71; Light: Dry −7.45, Moderate −1.50, Wet +9.14; Heavy: Dry −6.92, Moderate −2.13, Wet +9.23.

**Year by year (`results/table_yearly_chi2.csv`).** The same test inside each calendar year gives χ² = 95.39 (2022), 68.31 (2023), 122.19 (2024), 116.05 (2025), all with df = 4 and p between 10⁻¹³ and 10⁻²⁵; Cramér's V = 0.361, 0.306, 0.409, 0.399. So the association appears in every year, not only in the pooled data. Caution: 2023 has 1 of 9 cells (11%) with expected count below 5 (smallest 3.92).

**Temporal dependence (why the p-value is optimistic).** Daily data are not independent: lag-1 autocorrelation is 0.999 for soil wetness and 0.702 for rainfall, and the soil class is unchanged from one day to the next on 98.1% of days. The soil and rain series also share one yearly monsoon cycle (monthly mean soil wetness is about 0.50–0.56 from January to May and about 0.87–0.93 from July to October; `results/table_monthly_rain_soil.csv`). Three p-values were computed (`results/table_p_values_compared.csv`):
- *Textbook chi-square:* p ≈ 2.6 × 10⁻⁸⁶ (treats the 1,460 days as independent).
- *Random shuffle Monte Carlo (10,000 shuffles, seed 7, treats days as independent):* 0 of 10,000 shuffles reached χ² = 404.76, so p = (0+1)/(10,000+1) = 0.0001, the smallest value this test can give; read it as "p below about 0.0001".
- *Circular-shift permutation (keeps each series' own time pattern):* the rain_cat column is rotated as one block by every shift from 30 to 1,429 days (all 1,400 shifts, no random numbers) while soil_cat stays fixed. 487 of the 1,400 shifted tables had χ² ≥ the real value, so p = (487+1)/(1400+1) = 0.348, **not significant**. The median shifted χ² is 296.5 (95th percentile 581.3) against a real value of 404.8. Sensitivity: using only the 742 shifts that are at least 90 days away from a whole number of years, 254 reached the real χ², p = (254+1)/(742+1) = 0.343, so the result does not depend on the shifts that re-align the seasons.

What the permutation result means: the circular shift is a fairer null than a plain shuffle because runs of wet and dry days stay together, but with only 4 monsoon cycles even misaligned series look strongly "associated" (median χ² ≈ 297). The data therefore cannot separate "rain wets the soil" from "both follow the same season". It does **not** show that rain and soil moisture are unrelated, and it is an exploratory check, not a definitive test (only 4 seasonal cycles are available). The association is large in this sample, but the textbook p-value must not be taken literally.

**Association vs causation.** Rain and soil moisture are associated; season, temperature, humidity, evaporation and soil memory all vary together with rain, and today's soil already includes today's rain. We do not claim rain causes wetness.

## PART A/B worked example – 20 consecutive real rows (demonstration only)
Rows 30 Apr – 19 May 2022 (`results/worked_example_20rows.csv`; rule: the first 20-row window that contains all three rain classes, at least one Dry day and both soil_next_dry values; a window with all three soil classes does not exist in this dataset because soil changes class slowly). Counting by hand: n(Dry) = 19, n(None) = 18, n(Dry and None) = 18, so P(Dry) = 19/20 = 0.95, P(None) = 18/20 = 0.90, P(Dry and None) = 18/20 = 0.90, while P(Dry)P(None) = 0.855. Of the 19 Dry days, 18 were followed by a Dry day: P(soil_next_dry = 1 | Dry) = 18/19 = 0.9474. Dry + Light occurred once (17 May, next day Dry): 1/1. These counts were repeated in Excel (COUNTIFS) and matched. Twenty rows are far too few for a test; the main tables use all 1,460 rows.

## PART B – Report text
Threshold: irrigating costs c_irr for sure; not irrigating costs p × c_stress on average, so irrigation is worthwhile when p > t = c_irr/c_stress (= 1/3 for costs 1 and 3). Rules (`src/decision.py`): upper = max(0.75, t); p ≥ upper IRRIGATE NOW; t ≤ p < upper DELAY & RE-CHECK; p < t DON'T IRRIGATE. Costs must be > 0; fewer than 10 matching days adds a low-support warning; zero matching days gives "NO DATA" (p is undefined, not 0).

| Condition | Valid days | Next-day Dry | p_dry_tomorrow | 95% interval | Threshold | Decision |
|---|---|---|---|---|---|---|
| Dry + None | 466 | 465 | 0.9979 | 0.988–1.000 | 0.333 | IRRIGATE NOW |
| Moderate + Light | 93 | 0 | 0.0000 | 0.000–0.040 | 0.333 | DON'T IRRIGATE |
| Wet + Heavy | 108 | 0 | 0.0000 | 0.000–0.034 | 0.333 | DON'T IRRIGATE |

None of the three has fewer than 10 days, so none carries a low-support warning.

**Why zero Dry outcomes does not mean "impossible".** "0 out of 93" only says none was seen in this sample. If the true chance were 3%, we would still see 0 in 93 days about 6% of the time (0.97⁹³). The 95% (Wilson) interval shows the plausible range: up to about 4.0% for Moderate + Light and 3.4% for Wet + Heavy. Both upper limits stay far below t = 1/3, so DON'T IRRIGATE does not change inside the interval, but the interval assumes independent days and is therefore too narrow for autocorrelated data.

**Different costs.** With c_irr = 2, c_stress = 3 (t = 2/3, upper = 0.75) the three decisions do not change: p = 0.9979, 0.0000 and 0.0000 are all outside the only region (1/3 ≤ p < 2/3) where the two cost settings disagree. Across all nine combinations no decision changes. A hypothetical p = 0.50 would flip (DELAY & RE-CHECK at t = 1/3, DON'T IRRIGATE at t = 2/3); this illustrates the rule and is **not** a data result.

**All nine combinations** (c_irr = 1, c_stress = 3; `results/partB_all_9_combinations.csv`):

| soil | rain | days | next-day Dry | p | decision | decision at costs 2,3 | low support |
|---|---|---|---|---|---|---|---|
| Dry | None | 466 | 465 | 0.9979 | IRRIGATE NOW | IRRIGATE NOW | no |
| Dry | Light | 33 | 28 | 0.8485 | IRRIGATE NOW | IRRIGATE NOW | no |
| Dry | Heavy | **0** | 0 | undefined | **NO DATA** | NO DATA | **yes (n = 0)** |
| Moderate | None | 360 | 6 | 0.0167 | DON'T IRRIGATE | DON'T IRRIGATE | no |
| Moderate | Light | 93 | 0 | 0.0000 | DON'T IRRIGATE | DON'T IRRIGATE | no |
| Moderate | Heavy | 32 | 0 | 0.0000 | DON'T IRRIGATE | DON'T IRRIGATE | no |
| Wet | None | 167 | 0 | 0.0000 | DON'T IRRIGATE | DON'T IRRIGATE | no |
| Wet | Light | 201 | 0 | 0.0000 | DON'T IRRIGATE | DON'T IRRIGATE | no |
| Wet | Heavy | 108 | 0 | 0.0000 | DON'T IRRIGATE | DON'T IRRIGATE | no |

**The empty cell (Dry + Heavy).** No day in the data combines Dry soil with Heavy rain, so P(Dry tomorrow | Dry, Heavy) cannot be computed (0/0). It is reported as NO DATA with a visible low-support warning. [Interpretation] The empty cell is plausible rather than a coding error: today's soil wetness already includes today's rain, and the data show no Heavy-rain day with Dry soil. **Open group decision:** the guide's issue #3 suggests falling back to P(Dry tomorrow | soil only) for low-support cells (0.9880 for Dry soil, which would give IRRIGATE NOW), but Member 3's own prompt only asks for a warning. The group has not chosen, so the official output stays NO DATA and the soil-only fallback is shown only as a labelled reference column (`fallback_decision_soil_only_NOT_APPROVED`).

**Does rain add information beyond soil?** P(Dry tomorrow | soil only) is 0.9880 (Dry), 0.0124 (Moderate), 0.0000 (Wet). Adding rain barely changes the picture, because today's soil already contains today's rain: Dry + None 0.9979, Dry + Light 0.8485, Moderate + None 0.0167, Moderate + Light/Heavy 0.0000. Note that tomorrow's soil class is almost fully predicted by today's (98.1% unchanged), so probabilities are close to 0 or 1 and decisions are almost forced by today's soil class. The one place rain matters is Dry soil: Dry + Light (0.8485) is lower than Dry + None (0.9979).

**Limitations.** One location; modelled (MERRA-2-type) soil and rain estimates on a coarse grid, not field sensors, and we could not verify the soil variable against the raw NASA file; only 4 years and strong monsoon seasonality; strongly dependent days (so the textbook p-value is optimistic and the permutation test is only exploratory); soil classes defined by tertiles of the same data (relative to this dataset, with ties at the cut points); rain classes use the guide's "Heavy > 15.5 mm" definition, which is wider than the IMD "Heavy"; one empty cell (Dry + Heavy); assumed costs (1, 3 and 2, 3); no validation against real irrigation outcomes; association is not causation. The rule is an exploratory statistical exercise, **not a validated agricultural recommendation**.

## Viva Q&A (numbers for the 2022–2025 dataset)
1. **H0 and H1?** H0: rain_cat and soil_cat are independent; H1: associated. Rejecting H0 means dependence in the data, not causation.
2. **How are the expected frequencies and df obtained?** E = row total × column total / 1460; df = (3−1)(3−1) = 4. Example: expected(None, Dry) = 993 × 499 / 1460 = 339.39.
3. **What was the result?** χ² = 404.76, df = 4, p ≈ 2.6 × 10⁻⁸⁶, Cramér's V = 0.372.
4. **What does the p-value mean?** The probability of a χ² at least this large if H0 were true *and days were independent*. Days are strongly dependent (lag-1 autocorrelation 0.999 for soil), so it is overstated; the circular-shift check gave p = 0.348.
5. **Why do the resampling p-values differ (0.0001 vs 0.348)?** Random shuffling destroys the time pattern, so it treats days as independent. Circular shifting keeps each series' pattern, including the shared monsoon cycle, so shifted series can look "associated" by chance (median shifted χ² = 296.5).
6. **Does p = 0.348 mean rain and soil are unrelated?** No. It means this 4-year sample cannot rule out a shared-season coincidence. Absence of significance is not evidence of independence, and with 4 cycles the test is weak.
7. **Is the circular-shift test definitive?** No. Shifts near a whole year re-align the seasons, so I also reported the 742 shifts at least 90 days from a whole year (p = 0.343). It is a sensitivity check on dependence, not a proof either way.
8. **Are the chi-square assumptions met?** Cell sizes: yes (smallest expected 45.64, 0% below 5). Categories are mutually exclusive: yes. Independence of days: no (autocorrelation), the weak point.
9. **Does the association hold in each year?** Yes: yearly χ² = 95.4, 68.3, 122.2, 116.0, all very small p; but the pooled test is still affected by dependence, and 2023 has one cell with expected 3.92 (< 5).
10. **Association vs causation?** Rain is associated with wetter soil, but season, humidity, temperature and evaporation vary together, so the test cannot prove cause.
11. **Conditional probability for Dry + None?** P(Dry tomorrow | Dry, None) = 465/466 = 0.9979, using only the 466 matching days (denominator n(B), not N = 1460).
12. **Where does t = 1/3 come from?** Irrigate when c_irr < p × c_stress, so t = c_irr/c_stress = 1/3.
13. **Why upper = max(0.75, t)?** If t were above 0.75 the DELAY band would vanish or the rules would overlap; this keeps the rules consistent. (If t > 1, irrigation is never worth it.)
14. **Why did costs (2, 3) not change any decision?** The observed probabilities (0.9979, 0.0000, 0.0000, and in the other cells 0.8485, 0.0167) are all outside 1/3 ≤ p < 2/3. Only a probability in that band can flip. A hypothetical p = 0.5 would flip.
15. **Dry + Heavy has no data. What do you report?** NO DATA with a low-support warning, because 0/0 is undefined, not zero. The guide's soil-only fallback (0.9880 → IRRIGATE NOW) is shown only for reference because the group has not approved it.
16. **What if a cell has only 3 observations?** The estimate is very noisy (one day changes p by 33 points). The code adds a low-support warning when n < 10; the guide also proposes the soil-only fallback.
17. **Zero Dry outcomes in 93 days: is the probability zero?** No. It is "none seen"; the 95% interval reaches about 4%. If the true chance were 3%, 0 in 93 would still occur about 6% of the time.
18. **Why are the tertile classes not exactly one third each?** soil_wetness has two decimals, so many days tie at a cut point (499 / 485 / 476 days); P(Dry) is 34.2%, not 33.3%.
19. **Is this sensor data?** No. NASA POWER soil wetness and rain are model/satellite-derived estimates; we also could not verify from the CSV alone that the soil column is GWETROOT.
20. **Why is "Heavy" misleading?** The guide's class is "> 15.5 mm", which includes IMD moderate rain (15.6–64.4 mm); only 3 days exceed 64.4 mm.
21. **Why 1,460 rows, not 1,461?** The raw 2022–2025 data has 1,461 days; 31 Dec 2025 has no "tomorrow", so its soil_next_dry is unknown and it is not in the file.
22. **Why was "None" a problem when reading the file?** Pandas converts the text "None" to missing; `keep_default_na=False` keeps it as a category (993 days would otherwise be lost).
23. **Why are these results exploratory?** One place, modelled data, assumed costs, dependent days, tertile classes from the same data, no validation.
