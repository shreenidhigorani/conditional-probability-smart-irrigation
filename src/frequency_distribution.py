# Joint and marginal frequency distributions
"""Joint and marginal frequency distributions module."""
import pandas as pd

def get_frequency_tables(df: pd.DataFrame):
    observed = pd.crosstab(df["rain_cat"], df["soil_cat"])
    joint_prob = observed / len(df)
    return observed, joint_prob