"""Geographic utilities: ZIP lookup, Haversine distance, radius filtering."""

import csv
import math
from pathlib import Path

import pandas as pd

DEFAULT_ZIP_PATH = Path(__file__).parent.parent / "data" / "processed" / "indiana_zips.csv"

EARTH_RADIUS_MILES = 3958.7613


def load_zip_coords(path: str | None = None) -> dict[str, tuple[float, float]]:
    """Load ZIP → (lat, lon) dict from CSV.

    Default path: data/processed/indiana_zips.csv.
    Returns a dict mapping 5-digit ZIP string to (lat, lon) floats.
    """
    p = path or str(DEFAULT_ZIP_PATH)
    coords: dict[str, tuple[float, float]] = {}
    with open(p, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords[row["zip5"]] = (float(row["lat"]), float(row["lon"]))
    return coords


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two points (Haversine formula)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_MILES * c


def filter_by_radius(
    providers: pd.DataFrame,
    user_zip: str,
    radius_miles: float,
    zip_coords: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Return providers within radius_miles of user_zip, sorted by distance ascending.

    Adds a 'distance_miles' column. Returns empty DataFrame if user_zip is not in zip_coords.
    Providers whose ZIPs are not in zip_coords are excluded from results.
    """
    if user_zip not in zip_coords:
        return providers.iloc[0:0].assign(distance_miles=pd.Series(dtype=float))
    user_lat, user_lon = zip_coords[user_zip]

    def _distance_for_row(zip5: str) -> float:
        coord = zip_coords.get(zip5)
        if coord is None:
            return float("inf")
        return haversine_miles(user_lat, user_lon, coord[0], coord[1])

    distances = providers["Rndrng_Prvdr_Zip5"].map(_distance_for_row)
    out = providers.assign(distance_miles=distances)
    out = out[out["distance_miles"] <= radius_miles]
    out = out.sort_values("distance_miles", ascending=True).reset_index(drop=True)
    return out
