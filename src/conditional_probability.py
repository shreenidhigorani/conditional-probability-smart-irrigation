# Conditional probability calculations
import pandas as pd
import numpy as np

def compute_joint_probability(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """
    Computes normalized joint probability distribution table for two categorical variables.
    
    Example:
        P(Soil_Moisture = 'Dry' AND Rainfall = 'No')
    """
    joint_counts = pd.crosstab(df[col1], df[col2])
    joint_prob = joint_counts / len(df)
    return joint_prob


def compute_marginal_probability(df: pd.DataFrame, column_name: str) -> pd.Series:
    """
    Computes marginal probability distribution for a single variable.
    
    Example:
        P(Soil_Moisture = 'Dry') across all conditions.
    """
    marginal_counts = df[column_name].value_counts()
    marginal_prob = marginal_counts / len(df)
    return marginal_prob


def calculate_conditional_probability(
    df: pd.DataFrame, target_col: str, target_val: str, given_conditions: dict
) -> float:
    """
    Calculates P(Target = target_val | Given Conditions).
    
    Formula:
        P(A | B) = P(A ∩ B) / P(B)
        
    Parameters:
        df (pd.DataFrame): Input sensor dataset.
        target_col (str): Column name for target event (e.g., 'Irrigation_Needed').
        target_val (str): Specific target value (e.g., 'Yes').
        given_conditions (dict): Key-value pairs representing observed conditions 
                                  e.g., {'Soil_Moisture': 'Dry', 'Rainfall': 'No'}.
                                  
    Returns:
        float: Calculated conditional probability value (0.0 to 1.0).
    """
    if df.empty:
        raise ValueError("Provided DataFrame is empty.")

    # Filter dataset for given conditions (Event B)
    condition_mask = pd.Series([True] * len(df), index=df.index)
    for col, val in given_conditions.items():
        if col not in df.columns:
            raise KeyError(f"Column '{col}' not found in dataset.")
        condition_mask &= df[col] == val

    count_B = condition_mask.sum()

    # Handle division by zero if event B never occurred in dataset
    if count_B == 0:
        return 0.0

    # Filter dataset for given conditions AND target value (Event A ∩ B)
    target_mask = condition_mask & (df[target_col] == target_val)
    count_A_and_B = target_mask.sum()

    # P(A | B) = count(A ∩ B) / count(B)
    prob_A_given_B = count_A_and_B / count_B

    return float(prob_A_given_B)


if __name__ == "__main__":
    # Internal module test script
    sample_data = pd.DataFrame({
        'Soil_Moisture': ['Dry', 'Dry', 'Wet', 'Dry', 'Wet', 'Dry', 'Moderate', 'Dry'],
        'Rainfall': ['No', 'No', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No'],
        'Irrigation_Needed': ['Yes', 'Yes', 'No', 'No', 'No', 'Yes', 'No', 'Yes']
    })

    print("--- Joint Probability Distribution ---")
    print(compute_joint_probability(sample_data, 'Soil_Moisture', 'Rainfall'))

    print("\n--- Marginal Probability (Soil Moisture) ---")
    print(compute_marginal_probability(sample_data, 'Soil_Moisture'))

    # Calculate P(Irrigation_Needed = 'Yes' | Soil_Moisture = 'Dry', Rainfall = 'No')
    cond_prob = calculate_conditional_probability(
        sample_data,
        target_col='Irrigation_Needed',
        target_val='Yes',
        given_conditions={'Soil_Moisture': 'Dry', 'Rainfall': 'No'}
    )
    print(f"\nP(Irrigation = Yes | Soil = Dry, Rain = No) = {cond_prob:.4f}")