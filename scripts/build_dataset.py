"""Pipeline: filter CMS Physician CSV to Indiana target services, output Parquet."""

import pandas as pd
from pathlib import Path
from app.search import SERVICE_CATALOG

# Build HCPCS -> service info lookup from the catalog
_HCPCS_LOOKUP: dict[str, dict] = {}
for svc in SERVICE_CATALOG:
    for code in svc["hcpcs_codes"]:
        _HCPCS_LOOKUP[code] = {
            "service_name": svc["name"],
            "service_category": svc["category"],
            "variant": svc["variants"][code],
        }

TARGET_HCPCS = list(_HCPCS_LOOKUP.keys())

# Columns to keep from the physician CSV
KEEP_COLS = [
    "Rndrng_NPI",
    "Rndrng_Prvdr_Last_Org_Name",
    "Rndrng_Prvdr_First_Name",
    "Rndrng_Prvdr_Ent_Cd",
    "Rndrng_Prvdr_St1",
    "Rndrng_Prvdr_City",
    "Rndrng_Prvdr_State_Abrvtn",
    "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_Type",
    "HCPCS_Cd",
    "HCPCS_Desc",
    "Place_Of_Srvc",
    "Tot_Benes",
    "Tot_Srvcs",
    "Avg_Sbmtd_Chrg",
    "Avg_Mdcr_Alowd_Amt",
    "Avg_Mdcr_Pymt_Amt",
]


def filter_physician_data(csv_path: str) -> pd.DataFrame:
    """Read physician CSV, return only Indiana rows for target HCPCS codes."""
    chunks = pd.read_csv(
        csv_path,
        usecols=lambda c: c in KEEP_COLS,
        dtype=str,
        chunksize=100_000,
    )
    filtered = []
    for chunk in chunks:
        mask = (chunk["Rndrng_Prvdr_State_Abrvtn"] == "IN") & (
            chunk["HCPCS_Cd"].isin(TARGET_HCPCS)
        )
        if mask.any():
            filtered.append(chunk[mask])
    if not filtered:
        return pd.DataFrame(columns=KEEP_COLS)
    df = pd.concat(filtered, ignore_index=True)
    # Convert numeric columns
    for col in ["Tot_Benes", "Tot_Srvcs", "Avg_Sbmtd_Chrg", "Avg_Mdcr_Alowd_Amt", "Avg_Mdcr_Pymt_Amt"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def add_service_names(df: pd.DataFrame) -> pd.DataFrame:
    """Add service_name, service_category, and variant columns based on HCPCS code."""
    df = df.copy()
    df["service_name"] = df["HCPCS_Cd"].map(lambda c: _HCPCS_LOOKUP.get(c, {}).get("service_name", "Unknown"))
    df["service_category"] = df["HCPCS_Cd"].map(lambda c: _HCPCS_LOOKUP.get(c, {}).get("service_category", "Unknown"))
    df["variant"] = df["HCPCS_Cd"].map(lambda c: _HCPCS_LOOKUP.get(c, {}).get("variant", ""))
    return df


def compute_statewide_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute p10, median, p90 of charges and allowed amounts per HCPCS code."""
    stats = df.groupby("HCPCS_Cd").agg(
        charge_p10=("Avg_Sbmtd_Chrg", lambda x: x.quantile(0.1)),
        charge_median=("Avg_Sbmtd_Chrg", "median"),
        charge_p90=("Avg_Sbmtd_Chrg", lambda x: x.quantile(0.9)),
        allowed_p10=("Avg_Mdcr_Alowd_Amt", lambda x: x.quantile(0.1)),
        allowed_median=("Avg_Mdcr_Alowd_Amt", "median"),
        allowed_p90=("Avg_Mdcr_Alowd_Amt", lambda x: x.quantile(0.9)),
    ).reset_index()
    return stats


def build_dataset(physician_csv: str, output_path: str) -> None:
    """Full pipeline: filter -> enrich -> compute stats -> save Parquet."""
    df = filter_physician_data(physician_csv)
    df = add_service_names(df)
    stats = compute_statewide_stats(df)
    df = df.merge(stats, on="HCPCS_Cd", how="left")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")


if __name__ == "__main__":
    import sys

    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    out_dir = Path(__file__).parent.parent / "data" / "processed"
    physician_csv = str(raw_dir / "MUP_PHY_R25_Prov_Svc.csv")
    output_parquet = str(out_dir / "indiana_prices.parquet")
    build_dataset(physician_csv, output_parquet)
