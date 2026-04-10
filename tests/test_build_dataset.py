import pandas as pd
import tempfile
import os
from pathlib import Path
from scripts.build_dataset import (
    filter_physician_data,
    add_service_names,
    compute_statewide_stats,
    build_dataset,
    TARGET_HCPCS,
)


def make_sample_physician_csv(path: str):
    """Create a minimal physician CSV for testing."""
    rows = [
        {
            "Rndrng_NPI": "1001",
            "Rndrng_Prvdr_Last_Org_Name": "Smith",
            "Rndrng_Prvdr_First_Name": "John",
            "Rndrng_Prvdr_Ent_Cd": "I",
            "Rndrng_Prvdr_St1": "100 Main St",
            "Rndrng_Prvdr_City": "Indianapolis",
            "Rndrng_Prvdr_State_Abrvtn": "IN",
            "Rndrng_Prvdr_Zip5": "46202",
            "Rndrng_Prvdr_Type": "Diagnostic Radiology",
            "HCPCS_Cd": "73721",
            "HCPCS_Desc": "Mri scan of leg joint without contrast",
            "Place_Of_Srvc": "F",
            "Tot_Benes": "50",
            "Tot_Srvcs": "55",
            "Avg_Sbmtd_Chrg": "300.00",
            "Avg_Mdcr_Alowd_Amt": "60.00",
            "Avg_Mdcr_Pymt_Amt": "48.00",
        },
        {
            "Rndrng_NPI": "1002",
            "Rndrng_Prvdr_Last_Org_Name": "Jones",
            "Rndrng_Prvdr_First_Name": "Jane",
            "Rndrng_Prvdr_Ent_Cd": "I",
            "Rndrng_Prvdr_St1": "200 Oak Ave",
            "Rndrng_Prvdr_City": "Fort Wayne",
            "Rndrng_Prvdr_State_Abrvtn": "IN",
            "Rndrng_Prvdr_Zip5": "46801",
            "Rndrng_Prvdr_Type": "Diagnostic Radiology",
            "HCPCS_Cd": "73721",
            "HCPCS_Desc": "Mri scan of leg joint without contrast",
            "Place_Of_Srvc": "F",
            "Tot_Benes": "30",
            "Tot_Srvcs": "32",
            "Avg_Sbmtd_Chrg": "500.00",
            "Avg_Mdcr_Alowd_Amt": "65.00",
            "Avg_Mdcr_Pymt_Amt": "52.00",
        },
        {
            "Rndrng_NPI": "2001",
            "Rndrng_Prvdr_Last_Org_Name": "Davis",
            "Rndrng_Prvdr_First_Name": "Bob",
            "Rndrng_Prvdr_Ent_Cd": "I",
            "Rndrng_Prvdr_St1": "300 Elm St",
            "Rndrng_Prvdr_City": "Chicago",
            "Rndrng_Prvdr_State_Abrvtn": "IL",
            "Rndrng_Prvdr_Zip5": "60601",
            "Rndrng_Prvdr_Type": "Diagnostic Radiology",
            "HCPCS_Cd": "73721",
            "HCPCS_Desc": "Mri scan of leg joint without contrast",
            "Place_Of_Srvc": "F",
            "Tot_Benes": "40",
            "Tot_Srvcs": "42",
            "Avg_Sbmtd_Chrg": "400.00",
            "Avg_Mdcr_Alowd_Amt": "62.00",
            "Avg_Mdcr_Pymt_Amt": "50.00",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


def test_filter_physician_data():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        make_sample_physician_csv(f.name)
        df = filter_physician_data(f.name)
        os.unlink(f.name)
    # Should only have Indiana rows with target HCPCS
    assert len(df) == 2
    assert set(df["Rndrng_Prvdr_State_Abrvtn"]) == {"IN"}
    assert set(df["HCPCS_Cd"]) == {"73721"}


def test_add_service_names():
    df = pd.DataFrame({"HCPCS_Cd": ["73721", "73723", "85025"]})
    result = add_service_names(df)
    assert "service_name" in result.columns
    assert "service_category" in result.columns
    assert "variant" in result.columns
    assert result.loc[result["HCPCS_Cd"] == "73721", "service_name"].iloc[0] == "MRI Knee"
    assert result.loc[result["HCPCS_Cd"] == "73721", "variant"].iloc[0] == "without contrast"


def test_compute_statewide_stats():
    df = pd.DataFrame(
        {
            "HCPCS_Cd": ["73721", "73721", "73721"],
            "Avg_Sbmtd_Chrg": [300.0, 400.0, 500.0],
            "Avg_Mdcr_Alowd_Amt": [60.0, 62.0, 65.0],
        }
    )
    stats = compute_statewide_stats(df)
    row = stats[stats["HCPCS_Cd"] == "73721"].iloc[0]
    assert row["charge_p10"] <= row["charge_median"] <= row["charge_p90"]
    assert row["allowed_p10"] <= row["allowed_median"] <= row["allowed_p90"]
    assert row["charge_median"] == 400.0


def test_target_hcpcs_has_24_codes():
    assert len(TARGET_HCPCS) == 24


def test_build_dataset_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        physician_csv = os.path.join(tmpdir, "physician.csv")
        make_sample_physician_csv(physician_csv)
        output_parquet = os.path.join(tmpdir, "output.parquet")
        build_dataset(physician_csv, output_parquet)
        assert os.path.exists(output_parquet)
        df = pd.read_parquet(output_parquet)
        assert len(df) == 2
        assert "service_name" in df.columns
        assert "charge_p10" in df.columns
        assert df["Avg_Sbmtd_Chrg"].dtype == float
