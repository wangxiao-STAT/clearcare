"""Download US Census 2020 ZCTA Gazetteer, filter to Indiana, output CSV.

Run once: python3 -m scripts.build_zip_data
Output: data/processed/indiana_zips.csv with columns zip5, lat, lon
"""

import csv
import io
import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path

CENSUS_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_zcta_national.zip"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "indiana_zips.csv"

# Indiana bounding box (approximate, with small margin)
IN_LAT_MIN = 37.7
IN_LAT_MAX = 41.8
IN_LON_MIN = -88.2
IN_LON_MAX = -84.7


def download_gazetteer() -> str:
    """Download and extract the Census Gazetteer text file. Returns its contents."""
    print(f"Downloading {CENSUS_URL} ...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(CENSUS_URL, timeout=60, context=ctx) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        txt_name = next(n for n in names if n.endswith(".txt"))
        with zf.open(txt_name) as f:
            return f.read().decode("utf-8")


def parse_indiana_zips(content: str) -> list[dict]:
    """Parse gazetteer content, return list of dicts with zip5, lat, lon for Indiana."""
    reader = csv.reader(io.StringIO(content), delimiter="\t")
    header = [h.strip() for h in next(reader)]
    geoid_idx = header.index("GEOID")
    lat_idx = header.index("INTPTLAT")
    lon_idx = header.index("INTPTLONG")
    rows = []
    for row in reader:
        row = [c.strip() for c in row]
        zip5 = row[geoid_idx]
        if not (zip5.startswith("46") or zip5.startswith("47")):
            continue
        try:
            lat = float(row[lat_idx])
            lon = float(row[lon_idx])
        except ValueError:
            continue
        if not (IN_LAT_MIN <= lat <= IN_LAT_MAX and IN_LON_MIN <= lon <= IN_LON_MAX):
            continue
        rows.append({"zip5": zip5, "lat": lat, "lon": lon})
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["zip5", "lat", "lon"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    try:
        content = download_gazetteer()
    except Exception as e:
        print(f"ERROR: download failed: {e}", file=sys.stderr)
        return 1
    rows = parse_indiana_zips(content)
    if len(rows) < 500:
        print(f"ERROR: only {len(rows)} Indiana ZIPs found, expected ~775", file=sys.stderr)
        return 1
    write_csv(rows, OUTPUT_PATH)
    print(f"Saved {len(rows)} Indiana ZIPs to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
