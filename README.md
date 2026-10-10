# IrrigAI — Probability Engine (Group 6, Member 2)

This folder contains the probability engine, reproducible tables, tests, and an optional Flask API for the group project **“IrrigAI — Should We Irrigate Today?”**

## Important data note

The included `g6_irrigation_data_fixed.csv` is the corrected CSV used in our calculations. The file has 1,460 rows and the agreed six-column schema. Its provenance and soil-tertile construction have **not been independently verified by this code**. The unusually high persistence in the `soil_next_dry` target means the team should validate the source, soil category cutoffs, and next-day label alignment before treating outputs as real-world irrigation guidance. Do not describe the data as independently NASA-verified unless the team has confirmed the source and processing steps.

## Schema and category rules

Columns, in order:

`date, rain_mm, soil_wetness, rain_cat, soil_cat, soil_next_dry`

- `rain_cat`: `None` (<2.5 mm), `Light` (2.5–15.5 mm inclusive), `Heavy` (>15.5 mm).
- `soil_cat`: `Dry`, `Moderate`, or `Wet` according to the project's soil-wetness tertile definition. Confirm the exact cutoffs and method against the group's data-preparation script before final submission.
- `soil_next_dry`: 1 if the following day's `soil_cat` is `Dry`, otherwise 0. The final date should be dropped if no following day is available. The current CSV ends on 2025-12-30, so the team should confirm whether the date range was intended to include 2025-12-31.

## Setup

Python 3.10+ recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python probability.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python probability.py
```

Running `probability.py` prints the frequency counts, conditional dry-tomorrow probabilities, reference checks, and writes CSV tables to `outputs/`.

## Core functions

- `joint_prob(df, soil, rain)` returns `(probability, count)`.
- `marginal_prob(df, col, value)` returns `(probability, count)`.
- `conditional_prob(df, target, given)` returns `(probability, event_count, support_count)`. If the denominator/support is zero, probability is `None` (undefined), not zero.
- `build_probability_tables(df)` builds frequency, joint, marginal, `P(soil | rain)`, and `P(rain | soil)` tables.
- `dry_tomorrow_table(df)` calculates `P(soil_next_dry=1 | soil_cat, rain_cat)` for all nine combinations and flags low support (n < 10).
- `dry_tomorrow_by_soil(df)` compares the target probability by soil category only.
- `irrigation_decision(p, c_irr, c_stress)` applies the team's proposed threshold rule.

## Proposed decision rule

`t = c_irr / c_stress`; `upper = max(0.75, t)`.

- If `p >= upper`: `IRRIGATE NOW`
- If `t <= p < upper`: `DELAY & RE-CHECK`
- If `p < t`: `DON'T IRRIGATE`
- If there are no supporting rows: `INSUFFICIENT_DATA`

These thresholds are project assumptions, not validated agronomic recommendations. `c_stress` must be greater than zero.

## Expected reference checks for this exact CSV

These are reproducibility checks of the included file, not independent source validation:

- Total rows: 1,460
- `Dry` AND `None`: 466 / 1,460 = 0.3192
- `soil_cat == Dry`: 499 / 1,460 = 0.3418
- `soil_next_dry == 1` given `Dry` and `None`: 465 / 466 = 0.9979

Excel formulas, assuming the columns above are A:F and row 1 is the header:

- `=COUNTIFS(E:E,"Dry",D:D,"None")` → 466
- `=COUNTIF(E:E,"Dry")` → 499
- `=COUNTIFS(E:E,"Dry",D:D,"None",F:F,1)` → 465
- Conditional probability: `=465/466` → 0.9979

## Optional API

Start the API:

```bash
python app.py
```

It runs locally at `http://127.0.0.1:5000`.

- `GET /health`
- `GET /tables`
- `POST /predict` with JSON body, for example:

```json
{
  "soil": "Dry",
  "rain": "None",
  "c_irr": 2,
  "c_stress": 10
}
```

The response includes `p_dry_tomorrow`, `threshold`, `upper_threshold`, `decision`, and `reason`. Unsupported combinations return `INSUFFICIENT_DATA`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Suggested GitHub files

Commit this folder's Python files, `requirements.txt`, README, tests, the agreed CSV if your team permits datasets in the repository, and generated `outputs/`. Do not commit `.venv/`, `__pycache__/`, or machine-specific files.

## Report-ready formulas

Let `S` be today's soil category, `R` today's rainfall category, and `D` the event that the next day's soil category is Dry.

- **Joint:** `P(S=s, R=r) = count(S=s and R=r) / N`
- **Marginal:** `P(S=s) = count(S=s) / N`
- **Conditional:** `P(D | S=s, R=r) = count(D and S=s and R=r) / count(S=s and R=r)`
- If the conditional denominator is zero, the result is undefined and must be represented as `None`/`NO DATA`, not as probability zero.

## Worked example (20 consecutive rows)

The file `outputs/worked_example_20_days.csv` contains the sample from 2022-05-03 through 2022-05-22. For the condition `soil_cat=Dry` and `rain_cat=None`, the sample contains 15 matching rows, of which 14 have `soil_next_dry=1`; the sample conditional frequency is `14/15 = 0.9333`. This is a demonstration sample only; the main probability tables use the full CSV.

## Denominator mistakes to avoid

1. Joint probability denominator is all valid rows (`N`).
2. Marginal probability denominator is all valid rows (`N`).
3. Conditional probability denominator is only the rows satisfying the `given` condition.
4. `P(soil | rain)` and `P(rain | soil)` are different; their denominators differ.
5. If the denominator is zero, the conditional probability is undefined, not zero.
6. Check support counts. A probability from a very small sample may be unstable; this project flags support below 10 as `LOW SUPPORT`.

## Viva practice (12 questions)

1. **What is joint probability?** Probability that two events happen together.
2. **What is marginal probability?** Probability of one event without conditioning on another variable.
3. **What is conditional probability?** Probability of an event given that another condition is true.
4. **How is conditional probability calculated?** Count rows satisfying both target and condition, divided by rows satisfying the condition.
5. **Why is the conditional denominator not always N?** Because only observations matching the given condition are considered.
6. **Are `P(soil | rain)` and `P(rain | soil)` equal?** Not generally; they use different denominators.
7. **What if the denominator is zero?** Probability is undefined; report `None`/`NO DATA`.
8. **What is relative frequency?** An observed count divided by the relevant total count.
9. **Why show support count with a probability?** It shows how much data supports that estimate.
10. **What is Bayes' theorem?** `P(A|B) = P(B|A)P(A)/P(B)`, provided `P(B)>0`.
11. **Can this empirical probability guarantee tomorrow's soil condition?** No; it estimates a frequency from historical data and depends on data quality and representativeness.
12. **Why does Bayes' theorem require `P(B)>0`?** Because `P(B)` is the denominator; if it is zero, the conditional probability is undefined.
