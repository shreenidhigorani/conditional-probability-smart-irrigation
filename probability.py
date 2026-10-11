"""
IrrigAI Probability Engine (Group 6, Member 2).

Calculates empirical probabilities from the supplied CSV.
It does not independently verify the dataset's source or provide
validated agricultural advice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# --------------------------------------------------
# 1. PROJECT PATHS AND CONSTANTS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "g6_irrigation_data.csv"
OUTPUT_DIR = BASE_DIR / "results" / "tables" / "probability"

SOIL_ORDER = ["Dry", "Moderate", "Wet"]
RAIN_ORDER = ["None", "Light", "Heavy"]

REQUIRED_COLUMNS = [
    "date",
    "rain_mm",
    "soil_wetness",
    "rain_cat",
    "soil_cat",
    "soil_next_dry",
]

# 20 consecutive real days used for the worked numerical example.
# This window contains Dry+None, Dry+Light and Moderate days, so every
# probability in the report can be counted by hand from it.
EXAMPLE_START = "2022-05-03"
EXAMPLE_END = "2022-05-22"


# --------------------------------------------------
# 2. LOAD AND VALIDATE THE DATASET
# --------------------------------------------------

def load_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate the agreed six-column CSV schema."""

    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Expected: data/g6_irrigation_data.csv"
        )

    # keep_default_na=False: otherwise pandas reads the category "None" as NaN.
    df = pd.read_csv(path, keep_default_na=False)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {missing_columns}"
        )

    # Keep only the agreed columns, in the agreed order.
    df = df[REQUIRED_COLUMNS].copy()

    if df.empty:
        raise ValueError("The dataset contains no observations.")

    # Convert and validate dates.
    df["date"] = pd.to_datetime(
        df["date"], errors="raise"
    ).dt.normalize()

    if df["date"].duplicated().any():
        raise ValueError("Duplicate dates found in CSV.")

    if not df["date"].is_monotonic_increasing:
        raise ValueError(
            "Dates are not sorted. Sort the dataset chronologically."
        )

    # Convert numeric columns.
    numeric_columns = [
        "rain_mm",
        "soil_wetness",
        "soil_next_dry",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="raise")

    # Reject missing values and non-finite numbers.
    if df[numeric_columns].isna().any().any():
        raise ValueError(
            "Numeric columns contain missing values. "
            "Inspect and resolve them before analysis."
        )

    if not np.isfinite(df[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError(
            "Numeric columns contain infinite or invalid values."
        )

    # Detect NASA POWER missing-value sentinels.
    if (df[numeric_columns] == -999).any().any():
        raise ValueError(
            "Found -999 in numeric columns. This may be a missing-value "
            "sentinel. Inspect the raw source and clean it explicitly."
        )

    # Validate physical ranges where applicable.
    if (df["rain_mm"] < 0).any():
        raise ValueError("Rainfall cannot be negative.")

    if not df["soil_wetness"].between(0, 1).all():
        raise ValueError(
            "soil_wetness contains values outside 0 to 1. "
            "Verify the source parameter and units."
        )

    # Validate categories.
    if not df["soil_cat"].isin(SOIL_ORDER).all():
        invalid = sorted(set(df["soil_cat"]) - set(SOIL_ORDER))
        raise ValueError(
            f"Invalid or blank soil_cat values: {invalid}. "
            "Generate the categories from verified soil_wetness data."
        )

    if not df["rain_cat"].isin(RAIN_ORDER).all():
        invalid = sorted(set(df["rain_cat"]) - set(RAIN_ORDER))
        raise ValueError(
            f"Invalid or blank rain_cat values: {invalid}. "
            "Generate the categories from actual rain_mm values."
        )

    if not df["soil_next_dry"].isin([0, 1]).all():
        raise ValueError("soil_next_dry must contain only 0 or 1.")

    # A next-day target requires consecutive daily observations.
    expected_dates = pd.date_range(
        start=df["date"].iloc[0],
        end=df["date"].iloc[-1],
        freq="D",
    )

    if len(df) != len(expected_dates) or not (
        df["date"].to_numpy() == expected_dates.to_numpy()
    ).all():
        raise ValueError(
            "The dataset has missing calendar dates. "
            "Resolve the date gaps before calculating next-day targets."
        )

    # The agreed project uses tomorrow's soil category.
    # The final row should therefore have been dropped.
    if len(df) > 1:
        expected_target = (
            df["soil_cat"].shift(-1).eq("Dry").astype(int).iloc[:-1]
        )
        actual_target = df["soil_next_dry"].iloc[:-1].astype(int)

        if not expected_target.reset_index(drop=True).equals(
            actual_target.reset_index(drop=True)
        ):
            raise ValueError(
                "soil_next_dry does not match the following day's "
                "soil_cat. Rebuild the next-day target from the data."
            )

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df


# --------------------------------------------------
# 3. HELPER FUNCTION
# --------------------------------------------------

def _matches(df: pd.DataFrame, conditions: dict[str, Any]) -> pd.Series:
    """Return a Boolean mask matching every supplied condition."""

    mask = pd.Series(True, index=df.index)

    for col, value in conditions.items():
        if col not in df.columns:
            raise KeyError(f"Unknown column: {col}")

        mask &= df[col].eq(value)

    return mask


# --------------------------------------------------
# 4. JOINT AND MARGINAL PROBABILITIES
# --------------------------------------------------

def joint_prob(
    df: pd.DataFrame,
    *,
    soil: str,
    rain: str,
) -> tuple[float | None, int]:
    """Return (P(soil AND rain), joint observation count)."""

    total = len(df)

    if total == 0:
        return None, 0

    count = int(
        ((df["soil_cat"] == soil) & (df["rain_cat"] == rain)).sum()
    )

    return count / total, count


def marginal_prob(
    df: pd.DataFrame,
    *,
    col: str,
    value: Any,
) -> tuple[float | None, int]:
    """Return (P(column=value), observation count)."""

    if col not in df.columns:
        raise KeyError(f"Unknown column: {col}")

    total = len(df)

    if total == 0:
        return None, 0

    count = int(df[col].eq(value).sum())

    return count / total, count


# --------------------------------------------------
# 5. CONDITIONAL PROBABILITY
# --------------------------------------------------

def conditional_prob(
    df: pd.DataFrame,
    *,
    target: dict[str, Any],
    given: dict[str, Any],
) -> tuple[float | None, int, int]:
    """
    Return (probability, event count, support count).

    P(target | given) = n(target and given) / n(given)

    If no observations match the given conditions,
    the probability is undefined and returned as None (not zero).
    """

    given_mask = _matches(df, given)
    support_count = int(given_mask.sum())

    if support_count == 0:
        return None, 0, 0

    event_mask = _matches(df, target) & given_mask
    event_count = int(event_mask.sum())

    return event_count / support_count, event_count, support_count


# --------------------------------------------------
# 6. FREQUENCY AND PROBABILITY TABLES
# --------------------------------------------------

def build_probability_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build frequency, joint, marginal and conditional tables."""

    if df.empty:
        raise ValueError(
            "Cannot build probability tables from an empty dataset."
        )

    counts = pd.crosstab(
        df["soil_cat"],
        df["rain_cat"],
    ).reindex(
        index=SOIL_ORDER,
        columns=RAIN_ORDER,
        fill_value=0,
    )

    joint = counts / len(df)

    marginal_soil = counts.sum(axis=1) / len(df)
    marginal_rain = counts.sum(axis=0) / len(df)

    # A zero denominator gives an undefined probability (NaN), not zero.
    rain_totals = counts.sum(axis=0)
    soil_totals = counts.sum(axis=1)

    soil_given_rain = counts.div(rain_totals.where(rain_totals != 0), axis=1)
    rain_given_soil = counts.div(soil_totals.where(soil_totals != 0), axis=0)

    return {
        "counts": counts,
        "joint": joint,
        "marginal_soil": marginal_soil.to_frame("probability"),
        "marginal_rain": marginal_rain.to_frame("probability"),
        "soil_given_rain": soil_given_rain,
        "rain_given_soil": rain_given_soil,
    }


# --------------------------------------------------
# 7. PROBABILITY OF DRY SOIL TOMORROW
# --------------------------------------------------

def dry_tomorrow_table(
    df: pd.DataFrame,
    min_support: int = 10,
) -> pd.DataFrame:
    """
    Calculate P(soil_next_dry=1 | current soil, current rain)
    for all nine soil/rain combinations.
    """

    if min_support < 1:
        raise ValueError("min_support must be at least 1.")

    rows = []

    for soil in SOIL_ORDER:
        for rain in RAIN_ORDER:
            p, event_count, support = conditional_prob(
                df,
                target={"soil_next_dry": 1},
                given={"soil_cat": soil, "rain_cat": rain},
            )

            if support == 0:
                status = "NO DATA"
            elif support < min_support:
                status = "LOW SUPPORT"
            else:
                status = "OK"

            rows.append({
                "soil_cat": soil,
                "rain_cat": rain,
                "dry_tomorrow_count": event_count,
                "support_count": support,
                "p_dry_tomorrow": p,
                "status": status,
            })

    return pd.DataFrame(rows)


def dry_tomorrow_by_soil(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate P(soil_next_dry=1 | current soil), ignoring rainfall."""

    rows = []

    for soil in SOIL_ORDER:
        p, event_count, support = conditional_prob(
            df,
            target={"soil_next_dry": 1},
            given={"soil_cat": soil},
        )

        rows.append({
            "soil_cat": soil,
            "dry_tomorrow_count": event_count,
            "support_count": support,
            "p_dry_tomorrow": p,
        })

    return pd.DataFrame(rows)


# --------------------------------------------------
# 8. IRRIGATION DECISION RULE
# --------------------------------------------------

def irrigation_decision(
    p_dry_tomorrow: float | None,
    c_irr: float,
    c_stress: float,
) -> dict[str, Any]:
    """
    Apply the agreed project decision rule.

    t = c_irr / c_stress
    upper = max(0.75, t)

    p >= upper : IRRIGATE NOW
    p >= t     : DELAY & RE-CHECK
    otherwise  : DON'T IRRIGATE
    """

    if not np.isfinite(c_irr) or c_irr <= 0:
        raise ValueError("c_irr must be greater than zero.")

    if not np.isfinite(c_stress) or c_stress <= 0:
        raise ValueError("c_stress must be greater than zero.")

    threshold = c_irr / c_stress
    upper = max(0.75, threshold)

    if p_dry_tomorrow is None:
        return {
            "threshold": threshold,
            "upper_threshold": upper,
            "decision": "INSUFFICIENT_DATA",
            "reason": "No observations support this soil/rainfall combination.",
        }

    if not np.isfinite(p_dry_tomorrow) or not 0 <= p_dry_tomorrow <= 1:
        raise ValueError("p_dry_tomorrow must be between 0 and 1.")

    if p_dry_tomorrow >= upper:
        decision = "IRRIGATE NOW"
        reason = (
            f"p={p_dry_tomorrow:.4f} is at or above "
            f"upper threshold {upper:.4f}."
        )

    elif p_dry_tomorrow >= threshold:
        decision = "DELAY & RE-CHECK"
        reason = (
            f"p={p_dry_tomorrow:.4f} is between thresholds "
            f"{threshold:.4f} and {upper:.4f}."
        )

    else:
        decision = "DON'T IRRIGATE"
        reason = (
            f"p={p_dry_tomorrow:.4f} is below "
            f"threshold {threshold:.4f}."
        )

    return {
        "threshold": threshold,
        "upper_threshold": upper,
        "decision": decision,
        "reason": reason,
    }


# --------------------------------------------------
# 9. REFERENCE VALUES FOR MANUAL VERIFICATION
# --------------------------------------------------

def verify_reference_values(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate selected values for checking against Excel."""

    p_joint, n_joint = joint_prob(df, soil="Dry", rain="None")

    p_marginal, n_dry = marginal_prob(df, col="soil_cat", value="Dry")

    p_cond, n_event, n_support = conditional_prob(
        df,
        target={"soil_next_dry": 1},
        given={"soil_cat": "Dry", "rain_cat": "None"},
    )

    return {
        "total_rows": len(df),
        "joint_dry_none_count": n_joint,
        "joint_dry_none_probability": p_joint,
        "marginal_dry_count": n_dry,
        "marginal_dry_probability": p_marginal,
        "conditional_event_count": n_event,
        "conditional_support_count": n_support,
        "conditional_dry_tomorrow_probability": p_cond,
    }


# --------------------------------------------------
# 10. WRITE OUTPUT TABLES
# --------------------------------------------------

def worked_example(df: pd.DataFrame) -> pd.DataFrame:
    """Return the 20 consecutive real days used in the report example."""

    sample = df[(df["date"] >= EXAMPLE_START) & (df["date"] <= EXAMPLE_END)]

    if len(sample) != 20:
        raise ValueError(
            f"Expected 20 days between {EXAMPLE_START} and {EXAMPLE_END}, "
            f"found {len(sample)}."
        )

    return sample[["date", "rain_cat", "soil_cat", "soil_next_dry"]]


def write_outputs(
    df: pd.DataFrame,
    output_dir: str | Path = OUTPUT_DIR,
) -> None:
    """Write probability tables and the 20-row worked example."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    tables = build_probability_tables(df)

    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=True)

    dry_tomorrow_table(df).to_csv(
        out / "dry_tomorrow_by_soil_and_rain.csv", index=False
    )

    dry_tomorrow_by_soil(df).to_csv(
        out / "dry_tomorrow_by_soil.csv", index=False
    )

    worked_example(df).to_csv(out / "worked_example_20_days.csv", index=False)

    pd.DataFrame([verify_reference_values(df)]).to_csv(
        out / "verification_reference_values.csv", index=False
    )


# --------------------------------------------------
# 11. MAIN PROGRAM
# --------------------------------------------------

def main() -> None:
    df = load_data()

    print(f"Loaded {len(df)} validated rows.")
    print(f"First date: {df['date'].min()}")
    print(f"Last date: {df['date'].max()}")

    print("\nFrequency counts (soil rows x rainfall columns):")
    print(build_probability_tables(df)["counts"].to_string())

    print("\nP(soil_next_dry=1 | soil_cat, rain_cat):")
    print(
        dry_tomorrow_table(df).to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print("\nP(soil_next_dry=1 | soil_cat):")
    print(
        dry_tomorrow_by_soil(df).to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print("\nReference values for manual verification:")

    for key, value in verify_reference_values(df).items():
        print(f"{key}: {value}")

    write_outputs(df)

    print(f"\nOutput tables saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
