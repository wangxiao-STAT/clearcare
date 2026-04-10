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
