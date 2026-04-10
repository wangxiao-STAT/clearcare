"""Load and query the processed Indiana prices Parquet file."""

import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "processed" / "indiana_prices.parquet"


def load_data(path: str | None = None) -> pd.DataFrame:
    """Load the processed Parquet file."""
    p = path or str(DATA_PATH)
    return pd.read_parquet(p)


def get_providers_for_service(
    df: pd.DataFrame,
    service_name: str,
    hcpcs_code: str | None = None,
    city: str | None = None,
    sort_by: str = "Avg_Sbmtd_Chrg",
) -> pd.DataFrame:
    """Filter providers for a given service, optionally by HCPCS code and city."""
    mask = df["service_name"] == service_name
    if hcpcs_code:
        mask = mask & (df["HCPCS_Cd"] == hcpcs_code)
    if city:
        mask = mask & (df["Rndrng_Prvdr_City"] == city)
    return df[mask].sort_values(sort_by, ascending=True).reset_index(drop=True)


def get_statewide_stats(df: pd.DataFrame, hcpcs_code: str) -> dict:
    """Get precomputed p10/median/p90 stats for a HCPCS code."""
    row = df[df["HCPCS_Cd"] == hcpcs_code].iloc[0]
    return {
        "charge_p10": row["charge_p10"],
        "charge_median": row["charge_median"],
        "charge_p90": row["charge_p90"],
        "allowed_p10": row["allowed_p10"],
        "allowed_median": row["allowed_median"],
        "allowed_p90": row["allowed_p90"],
    }
