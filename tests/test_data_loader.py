import pandas as pd
import tempfile
import os
from app.data_loader import load_data, get_statewide_stats, get_providers_for_service


def make_test_parquet(path: str):
    """Create a minimal Parquet file matching pipeline output schema."""
    df = pd.DataFrame(
        [
            {
                "Rndrng_NPI": "1001",
                "Rndrng_Prvdr_Last_Org_Name": "Smith",
                "Rndrng_Prvdr_First_Name": "John",
                "Rndrng_Prvdr_Ent_Cd": "I",
                "Rndrng_Prvdr_City": "Indianapolis",
                "Rndrng_Prvdr_Zip5": "46202",
                "HCPCS_Cd": "73721",
                "service_name": "MRI Knee",
                "service_category": "Imaging",
                "variant": "without contrast",
                "Place_Of_Srvc": "F",
                "Tot_Benes": 50,
                "Avg_Sbmtd_Chrg": 300.0,
                "Avg_Mdcr_Alowd_Amt": 60.0,
                "charge_p10": 250.0,
                "charge_median": 350.0,
                "charge_p90": 500.0,
                "allowed_p10": 55.0,
                "allowed_median": 62.0,
                "allowed_p90": 70.0,
            },
            {
                "Rndrng_NPI": "1002",
                "Rndrng_Prvdr_Last_Org_Name": "Jones",
                "Rndrng_Prvdr_First_Name": "Jane",
                "Rndrng_Prvdr_Ent_Cd": "I",
                "Rndrng_Prvdr_City": "Fort Wayne",
                "Rndrng_Prvdr_Zip5": "46801",
                "HCPCS_Cd": "73721",
                "service_name": "MRI Knee",
                "service_category": "Imaging",
                "variant": "without contrast",
                "Place_Of_Srvc": "F",
                "Tot_Benes": 30,
                "Avg_Sbmtd_Chrg": 500.0,
                "Avg_Mdcr_Alowd_Amt": 65.0,
                "charge_p10": 250.0,
                "charge_median": 350.0,
                "charge_p90": 500.0,
                "allowed_p10": 55.0,
                "allowed_median": 62.0,
                "allowed_p90": 70.0,
            },
            {
                "Rndrng_NPI": "1003",
                "Rndrng_Prvdr_Last_Org_Name": "Lee",
                "Rndrng_Prvdr_First_Name": "Amy",
                "Rndrng_Prvdr_Ent_Cd": "I",
                "Rndrng_Prvdr_City": "Indianapolis",
                "Rndrng_Prvdr_Zip5": "46202",
                "HCPCS_Cd": "85025",
                "service_name": "Blood Work (CBC + Lipid Panel)",
                "service_category": "Labs",
                "variant": "CBC (complete blood count)",
                "Place_Of_Srvc": "O",
                "Tot_Benes": 100,
                "Avg_Sbmtd_Chrg": 36.0,
                "Avg_Mdcr_Alowd_Amt": 7.50,
                "charge_p10": 20.0,
                "charge_median": 36.0,
                "charge_p90": 50.0,
                "allowed_p10": 6.0,
                "allowed_median": 7.50,
                "allowed_p90": 9.0,
            },
        ]
    )
    df.to_parquet(path, index=False)


def test_load_data():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        make_test_parquet(f.name)
        df = load_data(f.name)
        os.unlink(f.name)
    assert len(df) == 3
    assert "service_name" in df.columns


def test_get_providers_for_service():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        make_test_parquet(f.name)
        df = load_data(f.name)
        os.unlink(f.name)
    providers = get_providers_for_service(df, "MRI Knee", hcpcs_code="73721")
    assert len(providers) == 2
    # Should be sorted by charge ascending
    assert providers.iloc[0]["Avg_Sbmtd_Chrg"] <= providers.iloc[1]["Avg_Sbmtd_Chrg"]


def test_get_providers_filters_by_city():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        make_test_parquet(f.name)
        df = load_data(f.name)
        os.unlink(f.name)
    providers = get_providers_for_service(df, "MRI Knee", hcpcs_code="73721", city="Indianapolis")
    assert len(providers) == 1
    assert providers.iloc[0]["Rndrng_Prvdr_City"] == "Indianapolis"


def test_get_statewide_stats():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        make_test_parquet(f.name)
        df = load_data(f.name)
        os.unlink(f.name)
    stats = get_statewide_stats(df, "73721")
    assert stats["charge_p10"] == 250.0
    assert stats["charge_median"] == 350.0
    assert stats["charge_p90"] == 500.0
