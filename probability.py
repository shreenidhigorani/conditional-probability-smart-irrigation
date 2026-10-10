"""IrrigAI Probability Engine (Group 6, Member 2).

The functions in this module calculate empirical probabilities from the supplied
CSV. They do not establish that the input data is an independently verified
NASA dataset or that the output is agricultural advice.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

SOIL_ORDER = ["Dry", "Moderate", "Wet"]
RAIN_ORDER = ["None", "Light", "Heavy"]
REQUIRED_COLUMNS = [
    "date", "rain_mm", "soil_wetness", "rain_cat", "soil_cat", "soil_next_dry"
]


def load_data(path: str | Path = "g6_irrigation_data_fixed.csv") -> pd.DataFrame:
    """Load and validate the agreed six-column CSV schema."""
    df = pd.read_csv(path, keep_default_na=False)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.strftime("%Y-%m-%d")
    for col in ["rain_mm", "soil_wetness", "soil_next_dry"]:
        df[col] = pd.to_numeric(df[col], errors="raise")

    invalid_soil = sorted(set(df["soil_cat"]) - set(SOIL_ORDER))
    invalid_rain = sorted(set(df["rain_cat"]) - set(RAIN_ORDER))
    invalid_target = sorted(set(df["soil_next_dry"]) - {0, 1})
    if invalid_soil:
        raise ValueError(f"Unexpected soil_cat values: {invalid_soil}")
    if invalid_rain:
        raise ValueError(f"Unexpected rain_cat values: {invalid_rain}")
    if invalid_target:
        raise ValueError(f"soil_next_dry must contain only 0/1; got {invalid_target}")
    if df["date"].duplicated().any():
        raise ValueError("Duplicate dates found in CSV")
    return df


def _matches(df: pd.DataFrame, conditions: dict[str, Any]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col, value in conditions.items():
        if col not in df.columns:
            raise KeyError(f"Unknown column: {col}")
        mask &= df[col].eq(value)
    return mask


def joint_prob(df: pd.DataFrame, soil: str, rain: str) -> tuple[float | None, int]:
    """Return (P(soil_cat=soil AND rain_cat=rain), joint count)."""
    total = len(df)
    if total == 0:
        return None, 0
    count = int(((df["soil_cat"] == soil) & (df["rain_cat"] == rain)).sum())
    return count / total, count


def marginal_prob(df: pd.DataFrame, col: str, value: Any) -> tuple[float | None, int]:
    """Return (P(col=value), count)."""
    total = len(df)
    if total == 0:
        return None, 0
    count = int((df[col] == value).sum())
    return count / total, count


def conditional_prob(
    df: pd.DataFrame, target: dict[str, Any], given: dict[str, Any]
) -> tuple[float | None, int, int]:
    """Return (P(target | given), event count, support/denominator count).

    If no rows match `given`, probability is None (undefined), not zero.
    """
    given_mask = _matches(df, given)
    support_count = int(given_mask.sum())
    if support_count == 0:
        return None, 0, 0
    event_count = int((_matches(df, target) & given_mask).sum())
    return event_count / support_count, event_count, support_count


def build_probability_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build frequency, joint, marginal, P(soil|rain), and P(rain|soil) tables."""
    if len(df) == 0:
        raise ValueError("Cannot build probability tables from an empty dataset")
    counts = pd.crosstab(df["soil_cat"], df["rain_cat"]).reindex(
        index=SOIL_ORDER, columns=RAIN_ORDER, fill_value=0
    )
    joint = counts / len(df)
    marginal_soil = counts.sum(axis=1) / len(df)
    marginal_rain = counts.sum(axis=0) / len(df)
    soil_given_rain = counts.div(counts.sum(axis=0).replace(0, pd.NA), axis=1)
    rain_given_soil = counts.div(counts.sum(axis=1).replace(0, pd.NA), axis=0)
    return {
        "counts": counts,
        "joint": joint,
        "marginal_soil": marginal_soil.to_frame("probability"),
        "marginal_rain": marginal_rain.to_frame("probability"),
        "soil_given_rain": soil_given_rain,
        "rain_given_soil": rain_given_soil,
    }


def dry_tomorrow_table(df: pd.DataFrame, min_support: int = 10) -> pd.DataFrame:
    """Calculate P(soil_next_dry=1 | current soil_cat, rain_cat) for all 9 pairs."""
    rows = []
    for soil in SOIL_ORDER:
        for rain in RAIN_ORDER:
            p, event_count, support = conditional_prob(
                df,
                target={"soil_next_dry": 1},
                given={"soil_cat": soil, "rain_cat": rain},
            )
            status = "NO DATA" if support == 0 else ("LOW SUPPORT" if support < min_support else "OK")
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
    """Compare P(soil_next_dry=1 | current soil_cat), ignoring rainfall."""
    rows = []
    for soil in SOIL_ORDER:
        p, event_count, support = conditional_prob(
            df, target={"soil_next_dry": 1}, given={"soil_cat": soil}
        )
        rows.append({
            "soil_cat": soil,
            "dry_tomorrow_count": event_count,
            "support_count": support,
            "p_dry_tomorrow": p,
        })
    return pd.DataFrame(rows)


def irrigation_decision(
    p_dry_tomorrow: float | None, c_irr: float, c_stress: float
) -> dict[str, Any]:
    """Apply the team's proposed cost-threshold decision rule."""
    if c_irr < 0 or c_stress <= 0:
        raise ValueError("c_irr must be >= 0 and c_stress must be > 0")
    threshold = c_irr / c_stress
    upper = max(0.75, threshold)
    if p_dry_tomorrow is None:
        return {
            "threshold": threshold,
            "upper_threshold": upper,
            "decision": "INSUFFICIENT_DATA",
            "reason": "No observations support this soil/rainfall combination.",
        }
    if not 0 <= p_dry_tomorrow <= 1:
        raise ValueError("p_dry_tomorrow must be between 0 and 1")
    if p_dry_tomorrow >= upper:
        decision = "IRRIGATE NOW"
        reason = f"p={p_dry_tomorrow:.4f} is at or above upper threshold {upper:.4f}."
    elif p_dry_tomorrow >= threshold:
        decision = "DELAY & RE-CHECK"
        reason = f"p={p_dry_tomorrow:.4f} is between thresholds {threshold:.4f} and {upper:.4f}."
    else:
        decision = "DON'T IRRIGATE"
        reason = f"p={p_dry_tomorrow:.4f} is below threshold {threshold:.4f}."
    return {
        "threshold": threshold,
        "upper_threshold": upper,
        "decision": decision,
        "reason": reason,
    }


def verify_reference_values(df: pd.DataFrame) -> dict[str, Any]:
    """Return key counts/probabilities for cross-checking in Excel."""
    p_joint, n_joint = joint_prob(df, "Dry", "None")
    p_marginal, n_dry = marginal_prob(df, "soil_cat", "Dry")
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


def write_outputs(df: pd.DataFrame, output_dir: str | Path = "outputs") -> None:
    """Write all report tables and the 20-row worked example as CSV files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tables = build_probability_tables(df)
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=True)
    dry_tomorrow_table(df).to_csv(out / "dry_tomorrow_by_soil_and_rain.csv", index=False)
    dry_tomorrow_by_soil(df).to_csv(out / "dry_tomorrow_by_soil.csv", index=False)

    sample = df[(df["date"] >= "2022-05-03") & (df["date"] <= "2022-05-22")].copy()
    sample[["date", "rain_cat", "soil_cat", "soil_next_dry"]].to_csv(
        out / "worked_example_20_days.csv", index=False
    )

    pd.DataFrame([verify_reference_values(df)]).to_csv(
        out / "verification_reference_values.csv", index=False
    )


def main() -> None:
    df = load_data()
    print(f"Loaded {len(df)} rows; dates {df['date'].min()} to {df['date'].max()}")
    print("\nFrequency counts (soil rows x rainfall columns):")
    print(build_probability_tables(df)["counts"].to_string())
    print("\nP(soil_next_dry=1 | soil_cat, rain_cat):")
    print(dry_tomorrow_table(df).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nP(soil_next_dry=1 | soil_cat):")
    print(dry_tomorrow_by_soil(df).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nReference verification values:")
    for key, value in verify_reference_values(df).items():
        print(f"{key}: {value}")
    write_outputs(df)
    print("\nCSV tables written to ./outputs/")


if __name__ == "__main__":
    main()
