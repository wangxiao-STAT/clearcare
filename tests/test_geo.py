import math
import csv
import tempfile
import os
import pandas as pd
from app.geo import load_zip_coords, haversine_miles, filter_by_radius


def make_test_zips_csv(path: str):
    """Create a small test ZIP CSV."""
    rows = [
        {"zip5": "46202", "lat": "39.7684", "lon": "-86.1581"},  # Indianapolis
        {"zip5": "46802", "lat": "41.0793", "lon": "-85.1393"},  # Fort Wayne
        {"zip5": "47901", "lat": "40.4167", "lon": "-86.8753"},  # Lafayette
        {"zip5": "46131", "lat": "39.4806", "lon": "-86.0531"},  # Franklin
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["zip5", "lat", "lon"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_load_zip_coords_returns_dict():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        make_test_zips_csv(f.name)
        coords = load_zip_coords(f.name)
        os.unlink(f.name)
    assert isinstance(coords, dict)
    assert len(coords) == 4
    assert "46202" in coords
    lat, lon = coords["46202"]
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert math.isclose(lat, 39.7684, abs_tol=1e-4)
    assert math.isclose(lon, -86.1581, abs_tol=1e-4)


def test_haversine_same_point_zero():
    d = haversine_miles(39.7684, -86.1581, 39.7684, -86.1581)
    assert math.isclose(d, 0.0, abs_tol=1e-6)


def test_haversine_symmetric():
    d1 = haversine_miles(39.7684, -86.1581, 41.0793, -85.1393)
    d2 = haversine_miles(41.0793, -85.1393, 39.7684, -86.1581)
    assert math.isclose(d1, d2, abs_tol=1e-9)


def test_haversine_indianapolis_to_fort_wayne():
    # Indianapolis (46202) to Fort Wayne (46802) is about 105-110 miles straight line
    d = haversine_miles(39.7684, -86.1581, 41.0793, -85.1393)
    assert 95 < d < 125


def _sample_providers_df():
    return pd.DataFrame(
        [
            {"Rndrng_NPI": "1001", "Rndrng_Prvdr_Zip5": "46202", "service_name": "MRI Knee"},
            {"Rndrng_NPI": "1002", "Rndrng_Prvdr_Zip5": "46131", "service_name": "MRI Knee"},  # Franklin, ~22 mi from Indy
            {"Rndrng_NPI": "1003", "Rndrng_Prvdr_Zip5": "46802", "service_name": "MRI Knee"},  # Fort Wayne, ~100+ mi
            {"Rndrng_NPI": "1004", "Rndrng_Prvdr_Zip5": "47901", "service_name": "MRI Knee"},  # Lafayette, ~55 mi
            {"Rndrng_NPI": "1005", "Rndrng_Prvdr_Zip5": "99999", "service_name": "MRI Knee"},  # missing ZIP
        ]
    )


def _zip_coords_for_tests():
    return {
        "46202": (39.7684, -86.1581),
        "46802": (41.0793, -85.1393),
        "47901": (40.4167, -86.8753),
        "46131": (39.4806, -86.0531),
    }


def test_filter_by_radius_basic():
    providers = _sample_providers_df()
    coords = _zip_coords_for_tests()
    result = filter_by_radius(providers, "46202", 25.0, coords)
    zips = result["Rndrng_Prvdr_Zip5"].tolist()
    assert "46202" in zips  # 0 mi
    assert "46131" in zips  # ~22 mi
    assert "46802" not in zips  # >25 mi
    assert "47901" not in zips  # >25 mi
    assert "99999" not in zips  # unknown ZIP


def test_filter_by_radius_sorts_by_distance():
    providers = _sample_providers_df()
    coords = _zip_coords_for_tests()
    result = filter_by_radius(providers, "46202", 200.0, coords)
    distances = result["distance_miles"].tolist()
    assert distances == sorted(distances)
    assert result.iloc[0]["Rndrng_Prvdr_Zip5"] == "46202"


def test_filter_by_radius_unknown_user_zip_returns_empty():
    providers = _sample_providers_df()
    coords = _zip_coords_for_tests()
    result = filter_by_radius(providers, "12345", 25.0, coords)
    assert result.empty
    assert "distance_miles" in result.columns


def test_filter_by_radius_provider_zip_missing_excluded():
    providers = _sample_providers_df()
    coords = _zip_coords_for_tests()
    result = filter_by_radius(providers, "46202", 500.0, coords)
    zips = result["Rndrng_Prvdr_Zip5"].tolist()
    assert "99999" not in zips
    # The other 4 known ZIPs should be present
    assert len(result) == 4
