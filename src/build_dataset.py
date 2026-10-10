"""
build_dataset.py
Builds g6_irrigation_data.csv (the agreed Group 6 schema) from the uploaded
IrrigAI_Kolhapur_Combined_2022_2025.csv.

Group leader's instruction: use ONE year only (calendar year 2025: 1 Jan - 31 Dec 2025).
Guide rules applied:
  rain_cat : None (< 2.5 mm), Light (2.5 - 15.5 mm), Heavy (> 15.5 mm)
  soil_cat : Dry / Moderate / Wet = tertiles of soil_wetness (thresholds computed from the 2025 rows)
  soil_next_dry : 1 if tomorrow's soil_cat is Dry, else 0 (last row dropped)
Output columns: date, rain_mm, soil_wetness, rain_cat, soil_cat, soil_next_dry
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# AUDIT GUARD (Oct 2026): this script is OBSOLETE for the approved dataset. It keeps only calendar
# year 2025 and would OVERWRITE data/g6_irrigation_data.csv with the old 364-row file. The approved
# dataset is now the 1,460-row 2022-2025 CSV supplied by the group, and the raw source file this script
# reads is not in the repository. It only runs if you pass --legacy-2025-only on purpose.
if "--legacy-2025-only" not in sys.argv:
    sys.exit("build_dataset.py is obsolete (2025-only builder). The approved dataset is "
             "data/g6_irrigation_data.csv (2022-2025, 1,460 rows). Not running. "
             "Use --legacy-2025-only only if you really want the old behaviour.")

# Paths start at the repo root so the script works from any folder:  python src/build_dataset.py
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "IrrigAI_Kolhapur_Combined_2022_2025.csv"   # raw file (Member 1) - NOT included in the audit zip
OUT = ROOT / "data" / "g6_irrigation_data.csv"
YEAR = 2025
# AUDIT NOTE: the guide asks for NASA POWER GWETROOT (0-1) as soil_wetness. This script uses the
# 7-28 cm layer column below. If Member 1 supplies a GWETROOT column, change SOIL_COLUMN only.
SOIL_COLUMN = "soil_moisture_7_to_28cm_m3m3"

# keep_default_na=False so the old text "None" is not turned into missing
raw = pd.read_csv(SRC, keep_default_na=False, na_values=[""])
raw["date"] = pd.to_datetime(raw["date"])
print("Source rows:", len(raw), "| date range:", raw["date"].min().date(), "to", raw["date"].max().date())

d = raw[raw["date"].dt.year == YEAR].sort_values("date").reset_index(drop=True)
print(f"Rows kept for {YEAR}:", len(d), "| range:", d["date"].min().date(), "to", d["date"].max().date())

# Agreed schema names
out = pd.DataFrame({
    "date": d["date"],
    "rain_mm": d["rainfall_mm"],
    # ASSUMPTION: the 7-28 cm soil-moisture layer (m3/m3) is used as soil_wetness,
    # because it is the layer the original soil_cat was built from.
    "soil_wetness": d[SOIL_COLUMN],
})

# rain_cat (pd.cut with explicit bins; 2.5 belongs to Light, 15.5 belongs to Light)
out["rain_cat"] = pd.cut(out["rain_mm"], bins=[-np.inf, 2.5, 15.5, np.inf],
                         labels=["None", "Light", "Heavy"], right=False)
# right=False gives [-inf,2.5) [2.5,15.5) [15.5,inf): fix so 15.5 itself is Light
out.loc[out["rain_mm"] == 15.5, "rain_cat"] = "Light"
out["rain_cat"] = out["rain_cat"].astype(str)

# soil_cat from tertiles of soil_wetness
q1 = out["soil_wetness"].quantile(1 / 3)
q2 = out["soil_wetness"].quantile(2 / 3)
print(f"Soil tertile thresholds: q1 = {q1:.4f}, q2 = {q2:.4f}")
out["soil_cat"] = np.where(out["soil_wetness"] <= q1, "Dry",
                   np.where(out["soil_wetness"] <= q2, "Moderate", "Wet"))

# soil_next_dry = 1 if tomorrow's soil_cat is Dry; last row has no tomorrow -> dropped
out["soil_next_dry"] = (out["soil_cat"].shift(-1) == "Dry").astype(int)
out = out.iloc[:-1].copy()
out["date"] = out["date"].dt.strftime("%Y-%m-%d")

# Sanity checks
assert out[["date", "rain_mm", "soil_wetness", "rain_cat", "soil_cat", "soil_next_dry"]].notna().all().all()
assert set(out["soil_next_dry"].unique()) <= {0, 1}
assert set(out["rain_cat"].unique()) == {"None", "Light", "Heavy"}
print("Final rows:", len(out))
print("rain_cat counts:", out["rain_cat"].value_counts().to_dict())
print("soil_cat counts:", out["soil_cat"].value_counts().to_dict())
print(out.groupby("rain_cat")["rain_mm"].agg(["min", "max"]))

out.to_csv(OUT, index=False)
print("Saved", OUT)
