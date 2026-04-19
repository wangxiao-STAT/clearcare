# ZIP Code / Radius Search

## Overview

Replace the current city dropdown filter with a ZIP code + radius search. Users enter their ZIP and select a radius (5/10/25/50/100 miles). The provider comparison table filters to providers within that distance and sorts by distance by default. This is strictly more powerful than the city filter and matches patterns patients expect from consumer tools like Zocdoc.

## Motivation

The current prototype filters providers by city dropdown. A user in Carmel (46032) who doesn't know which suburb their target provider is in has to manually scan the city list. With ZIP + radius, they enter their own ZIP and see every provider within a chosen distance, sorted by proximity. This also makes the app more useful for pilot users (benefits navigators) who want to help patients find care near a specific address.

## User Experience

**Sidebar inputs:**

```
Your ZIP code
[46202        ]

Radius
[25 miles   ▼]   (options: 5, 10, 25, 50, 100)
```

**Behavior:**

- **Empty ZIP** = show all Indiana providers (statewide default)
- **Valid Indiana ZIP** = filter to providers within selected radius, sort by distance ascending
- **Invalid ZIP format** (not 5 digits) = warning banner + statewide results
- **Out-of-state or unknown ZIP** = warning banner + statewide results
- **No providers in radius** = warning: "No providers found within N miles of ZIP. Try expanding the radius."

**Results view:**

- New "Distance" column showing "X.X mi" (e.g., "12.4 mi")
- Header reads "Showing N providers within 25 miles of 46202" when ZIP is active
- Default sort becomes "Distance (nearest first)" when ZIP is set; remains "Price (low to high)" otherwise
- Sort dropdown gains a "Distance (nearest first)" option for manual selection

## Architecture

Three components with clear boundaries:

1. **`scripts/build_zip_data.py`** — One-time data prep. Downloads the US Census 2020 ZCTA Gazetteer, filters to Indiana (state FIPS 18), outputs `data/processed/indiana_zips.csv`.
2. **`app/geo.py`** — Runtime geographic utilities. Loads ZIP coordinates, computes Haversine distance, filters providers by radius.
3. **`app/streamlit_app.py`** — Updated sidebar inputs and results view. Orchestrates: data load → service filter → radius filter → display.

The data loader (`app/data_loader.py`) stays geography-agnostic. Radius filtering is applied in the Streamlit layer by chaining the geo filter onto the existing provider query.

## Data: Indiana ZIP Reference Table

**Source:** US Census 2020 ZCTA Gazetteer (public domain). Tab-delimited file with columns: `GEOID` (ZIP), `INTPTLAT`, `INTPTLONG`, plus land area fields we ignore.

**Script (`scripts/build_zip_data.py`):**

- Downloads the Gazetteer file via HTTP
- Parses the tab-delimited content
- Filters to rows where ZIP starts with 46 or 47 (Indiana ZIP prefix range)
- Writes `data/processed/indiana_zips.csv` with columns: `zip5`, `lat`, `lon`
- Expected output: ~774 rows, ~30 KB

**Fallback:** If the Census URL is unreachable at build time, the script reports the error and exits non-zero. The generated CSV is committed to the repo, so Streamlit Cloud never needs to run the script — only the developer runs it once (or when Census publishes new data).

## Geo Module (`app/geo.py`)

Three functions, all pure (no side effects beyond caching):

```python
def load_zip_coords(path: str = None) -> dict[str, tuple[float, float]]:
    """Load Indiana ZIP → (lat, lon) dict from CSV.
    Default path: data/processed/indiana_zips.csv."""

def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two points using the Haversine formula."""

def filter_by_radius(
    providers: pd.DataFrame,
    user_zip: str,
    radius_miles: float,
    zip_coords: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Return providers within radius_miles of user_zip, sorted by distance ascending.
    Adds a 'distance_miles' column.
    Returns empty DataFrame if user_zip is not in zip_coords.
    Providers whose ZIPs are not in zip_coords are excluded from results."""
```

**Key design choices:**

- **Haversine over Vincenty/geodesic** — sub-1% accuracy at ≤100 mile scale, no external dependencies
- **ZIP lookup dict over DataFrame join** — O(1) lookup for user ZIP, and per-row map for provider ZIPs
- **In-memory caching via Streamlit's `@st.cache_data`** — applied at call site, not inside the module, to keep `geo.py` framework-agnostic and testable
- **Missing provider ZIPs silently excluded** — a provider whose ZIP isn't in our Indiana table (rare edge case) simply doesn't appear in radius results

## UI Changes (`app/streamlit_app.py`)

### Sidebar

Replace the current city filter block:

```python
# REMOVE
cities = sorted(service_df["Rndrng_Prvdr_City"].dropna().unique())
city_filter = st.sidebar.selectbox("Filter by city", ["All cities"] + list(cities))
city = None if city_filter == "All cities" else city_filter
```

With a ZIP + radius block:

```python
# ADD
user_zip = st.sidebar.text_input(
    "Your ZIP code",
    max_chars=5,
    placeholder="e.g. 46202",
)
radius_miles = st.sidebar.selectbox(
    "Radius",
    options=[5, 10, 25, 50, 100],
    index=2,  # default 25 miles
    format_func=lambda m: f"{m} miles",
)
```

### Main area

After calling `get_providers_for_service(...)`:

```python
zip_coords = load_zip_coords_cached()
warning_message = None

if user_zip:
    if not user_zip.isdigit() or len(user_zip) != 5:
        warning_message = "Please enter a valid 5-digit ZIP code."
    elif user_zip not in zip_coords:
        warning_message = "This prototype covers Indiana only. Please enter an Indiana ZIP code."
    else:
        providers = filter_by_radius(providers, user_zip, radius_miles, zip_coords)
        if providers.empty:
            warning_message = f"No providers found within {radius_miles} miles of {user_zip}. Try expanding the radius."

if warning_message:
    st.warning(warning_message)
```

### Results table

Add a Distance column when `distance_miles` is present:

```python
if "distance_miles" in providers.columns:
    display_df["Distance"] = providers["distance_miles"].apply(lambda d: f"{d:.1f} mi")
```

### Sort dropdown

Add a new option:

```python
sort_options = {
    "Distance (nearest first)": "distance_miles",  # new; only effective when ZIP is set
    "Price (low to high)": "Avg_Sbmtd_Chrg",
    "Medicare allowed (low to high)": "Avg_Mdcr_Alowd_Amt",
    "Patient volume (high to low)": "Tot_Benes",
}
```

Default sort is "Distance" when ZIP is set and coordinates resolved; "Price" otherwise.

## Testing Strategy

### Unit tests (`tests/test_geo.py`, ~6 tests)

1. `test_haversine_indianapolis_to_fort_wayne` — Indianapolis (46202, 39.7684, -86.1581) to Fort Wayne (46802, 41.0793, -85.1393) ≈ 100-130 miles
2. `test_haversine_same_point_zero` — distance from a point to itself is 0
3. `test_haversine_symmetric` — `distance(A, B) == distance(B, A)`
4. `test_load_zip_coords_returns_dict` — loads the CSV and returns a non-empty dict with string keys and float tuple values
5. `test_filter_by_radius_basic` — providers beyond radius are excluded, providers within are included
6. `test_filter_by_radius_sorts_by_distance` — results are sorted ascending by distance_miles
7. `test_filter_by_radius_unknown_user_zip_returns_empty` — user ZIP not in coords table returns empty DataFrame
8. `test_filter_by_radius_provider_zip_missing_excluded` — provider with ZIP not in coords is dropped without error

### Manual smoke test

1. Load the app — city filter is replaced with ZIP + radius inputs
2. Select MRI Knee, leave ZIP empty — all ~247 providers shown (statewide default preserved)
3. Enter `46202` + 25 miles — see only providers near Indianapolis with a Distance column, sorted by distance
4. Enter `46202` + 5 miles — list narrows further
5. Enter `99999` — warning: "This prototype covers Indiana only"
6. Enter `abc` — warning: "Please enter a valid 5-digit ZIP code"
7. Enter `47901` (Lafayette) + 5 miles — see only Lafayette-area providers
8. Switch service to HbA1c with same ZIP/radius — filter persists
9. Change sort to "Price" — results re-sort while keeping radius filter
10. Caveats footer still visible

## Risks

- **Census Gazetteer format changes** — unlikely for 2020 data but possible. Since the generated CSV is committed, this only affects future regenerations. The committed CSV acts as a stable snapshot.
- **Provider ZIP mismatches** — some providers may have ZIPs that don't appear in the 2020 Census ZCTA list (e.g., new ZIPs, PO box ZIPs). These providers will be excluded from radius results but still appear in statewide (empty ZIP) view. Acceptable for prototype.
- **Haversine accuracy on larger radii** — at 100 miles, Haversine underestimates by <0.5% vs geodesic. Immaterial for a price comparison UX.

## Non-Goals

- No map visualization (just the filtered list)
- No multi-ZIP input or "ZIP + nearby ZIPs" expansion
- No drive-time distance (straight-line miles only)
- No out-of-state provider support
- No reverse geocoding (address → ZIP)
- No ZIP autocomplete/suggestions in the input
