"""
Shared Excel import helpers: column normalization and validation.
"""
import pandas as pd
from typing import List


def normalize_excel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: strip, lower, replace spaces with underscore."""
    df = df.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    return df


def ensure_required_columns(df: pd.DataFrame, required: List[str]) -> List[str]:
    """Return list of missing column names. Empty if all present."""
    return [col for col in required if col not in df.columns]


def row_dicts_with_index(df: pd.DataFrame, start_row: int = 2):
    """
    Iterate over rows as dicts with 1-based Excel row index.
    More efficient than iterrows(); use for validation/insert loops.
    """
    records = df.to_dict(orient="records")
    for i, row in enumerate(records):
        row_num = start_row + i
        # Replace NaN with None for Pydantic/DB
        clean = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        yield row_num, clean
