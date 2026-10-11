# Vihan Patil - IrrigAI Member 1
# Data validation and preprocessing for g6_irrigation_data.csv

import pandas as pd

INPUT_FILE = "g6_irrigation_data.csv"
OUTPUT_FILE = "g6_irrigation_data_corrected.csv"

required_columns = [
    "date",
    "rain_mm",
    "soil_wetness",
    "rain_cat",
    "soil_cat",
    "soil_next_dry"
]

df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)
print("Original columns:", list(df.columns))

missing_columns = []
for column in required_columns:
    if column not in df.columns:
        missing_columns.append(column)

if len(missing_columns) > 0:
    raise ValueError("Missing required columns: " + str(missing_columns))

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["rain_mm"] = pd.to_numeric(df["rain_mm"], errors="coerce")
df["soil_wetness"] = pd.to_numeric(df["soil_wetness"], errors="coerce")
df["soil_next_dry"] = pd.to_numeric(df["soil_next_dry"], errors="coerce")

# Fill missing rainfall categories using the agreed rainfall thresholds.
# None: rainfall < 2.5 mm; Light: 2.5 to 15.5 mm; Heavy: > 15.5 mm.
def get_rain_category(rain):
    if pd.isna(rain):
        return pd.NA
    elif rain < 2.5:
        return "None"
    elif rain <= 15.5:
        return "Light"
    else:
        return "Heavy"

df["rain_cat"] = df["rain_cat"].fillna(df["rain_mm"].apply(get_rain_category))

# Check existing categories against the numeric rainfall values.
expected_rain_cat = df["rain_mm"].apply(get_rain_category)
wrong_rain_rows = df["rain_cat"].notna() & (df["rain_cat"] != expected_rain_cat)
if wrong_rain_rows.any():
    print("Correcting rainfall categories that do not match rain_mm.")
    df.loc[wrong_rain_rows, "rain_cat"] = expected_rain_cat[wrong_rain_rows]

# Convert the date back to a consistent format.
df["date"] = df["date"].dt.strftime("%Y-%m-%d")

# Check that the target column contains only 0 or 1.
if not df["soil_next_dry"].dropna().isin([0, 1]).all():
    raise ValueError("soil_next_dry must contain only 0 or 1.")

# Report missing values. Do not silently drop any records.
print("\nMissing values after rainfall-category repair:")
print(df[required_columns].isna().sum())

if df[required_columns].isna().any().any():
    raise ValueError(
        "Some required values are still missing. Review them before submission."
    )

if df["date"].duplicated().any():
    raise ValueError("Duplicate dates found. Review the dataset before submission.")

df = df.sort_values("date").reset_index(drop=True)

print("\nFinal dataset shape:", df.shape)
print("Date range:", df["date"].iloc[0], "to", df["date"].iloc[-1])
print("\nRain category counts:")
print(df["rain_cat"].value_counts())
print("\nSoil category counts:")
print(df["soil_cat"].value_counts())
print("\nJoint frequency table:")
print(pd.crosstab(df["soil_cat"], df["rain_cat"], margins=True))
print("\nTarget counts:")
print(df["soil_next_dry"].value_counts())

df.to_csv(OUTPUT_FILE, index=False)
print("\\nSaved corrected dataset to", OUTPUT_FILE)
print("Note: This script validates/fixes the supplied prepared CSV.")
print("For a fully reproducible source-to-output pipeline, retain the original")
print("NASA POWER download containing PRECTOTCORR and GWETROOT.")
