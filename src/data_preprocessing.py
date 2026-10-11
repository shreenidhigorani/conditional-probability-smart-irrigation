# Data loading and preprocessing
"""Data loading and preprocessing module."""
import pandas as pd

def load_and_preprocess(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, keep_default_na=False, na_values=[""])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)