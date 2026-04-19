# ClearCare Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit price comparison app for 6 shoppable healthcare services in Indiana, deployed to Streamlit Cloud.

**Architecture:** Pre-process CMS Physician CSV into a clean Parquet file (Indiana-only, 12 HCPCS codes). Streamlit reads the Parquet directly — no database. A hardcoded synonym lookup handles plain-English search across 6 services.

**Tech Stack:** Python 3.11, pandas, pyarrow, streamlit, pytest

---

## File Structure

```
├── data/
│   ├── raw/                       # CMS CSVs (gitignored, already downloaded)
│   └── processed/                 # Output Parquet (committed)
├── scripts/
│   └── build_dataset.py           # Data pipeline: filter, map, compute stats, output Parquet
├── app/
│   ├── streamlit_app.py           # Main Streamlit UI
│   ├── search.py                  # Service synonym lookup + fuzzy matching
│   └── data_loader.py             # Load/cache Parquet, compute statewide stats
├── tests/
│   ├── test_build_dataset.py      # Pipeline tests
│   ├── test_search.py             # Search/synonym tests
│   └── test_data_loader.py        # Data loader tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py`
- Create: `app/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
pandas>=2.0
pyarrow>=14.0
streamlit>=1.30
pytest>=7.0
```

- [ ] **Step 2: Create .gitignore**

```
data/raw/
__pycache__/
*.pyc
.superpowers/
.venv/
.env
```

- [ ] **Step 3: Create empty __init__.py files**

```bash
mkdir -p tests app
touch tests/__init__.py app/__init__.py
```

- [ ] **Step 4: Install dependencies**

```bash
python3 -m pip install -r requirements.txt
```

Expected: all packages install successfully.

- [ ] **Step 5: Verify pytest runs**

```bash
python3 -m pytest --co
```

Expected: "no tests ran" or empty collection — no errors.

- [ ] **Step 6: Initialize git and commit**

```bash
git init
git add requirements.txt .gitignore tests/__init__.py app/__init__.py
git commit -m "chore: scaffold project with dependencies and gitignore"
```

---

### Task 2: Service Mapping and Search

**Files:**
- Create: `app/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write failing tests for search**

Create `tests/test_search.py`:

```python
from app.search import search_services, SERVICE_CATALOG


def test_exact_service_name():
    results = search_services("MRI Knee")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"
    assert set(results[0]["hcpcs_codes"]) == {"73721", "73723"}


def test_synonym_match():
    results = search_services("knee scan")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"


def test_partial_match():
    results = search_services("colonoscopy")
    assert len(results) == 1
    assert results[0]["name"] == "Colonoscopy"


def test_broad_term_returns_multiple():
    results = search_services("MRI")
    names = {r["name"] for r in results}
    assert "MRI Brain" in names
    assert "MRI Knee" in names


def test_no_match_returns_all():
    results = search_services("xyz nonsense")
    assert len(results) == len(SERVICE_CATALOG)


def test_case_insensitive():
    results = search_services("mri knee")
    assert len(results) == 1
    assert results[0]["name"] == "MRI Knee"


def test_blood_test_synonym():
    results = search_services("blood test")
    assert len(results) == 1
    assert results[0]["name"] == "Blood Work (CBC + Lipid Panel)"


def test_catalog_has_six_services():
    assert len(SERVICE_CATALOG) == 6


def test_each_service_has_required_fields():
    for svc in SERVICE_CATALOG:
        assert "name" in svc
        assert "category" in svc
        assert "hcpcs_codes" in svc
        assert "synonyms" in svc
        assert len(svc["hcpcs_codes"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_search.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.search'`

- [ ] **Step 3: Implement search.py**

Create `app/search.py`:

```python
SERVICE_CATALOG = [
    {
        "name": "MRI Brain",
        "category": "Imaging",
        "hcpcs_codes": ["70551", "70553"],
        "variants": {"70551": "without contrast", "70553": "with contrast"},
        "synonyms": ["mri brain", "brain mri", "brain scan", "head mri", "mri head"],
    },
    {
        "name": "MRI Knee",
        "category": "Imaging",
        "hcpcs_codes": ["73721", "73723"],
        "variants": {"73721": "without contrast", "73723": "with contrast"},
        "synonyms": ["mri knee", "knee mri", "knee scan", "leg mri", "mri leg joint"],
    },
    {
        "name": "CT Abdomen & Pelvis",
        "category": "Imaging",
        "hcpcs_codes": ["74177", "74178"],
        "variants": {"74177": "with contrast", "74178": "before and after contrast"},
        "synonyms": [
            "ct abdomen",
            "ct pelvis",
            "ct scan abdomen",
            "ct scan pelvis",
            "abdominal ct",
            "cat scan abdomen",
            "cat scan",
        ],
    },
    {
        "name": "Screening Mammogram",
        "category": "Imaging",
        "hcpcs_codes": ["77067"],
        "variants": {"77067": "screening"},
        "synonyms": [
            "mammogram",
            "mammography",
            "breast screening",
            "breast scan",
            "screening mammogram",
        ],
    },
    {
        "name": "Colonoscopy",
        "category": "GI/Outpatient",
        "hcpcs_codes": ["45378", "45380", "45385"],
        "variants": {
            "45378": "diagnostic",
            "45380": "with biopsy",
            "45385": "with polyp removal",
        },
        "synonyms": [
            "colonoscopy",
            "colon scope",
            "scope",
            "colon screening",
            "colon exam",
        ],
    },
    {
        "name": "Blood Work (CBC + Lipid Panel)",
        "category": "Labs",
        "hcpcs_codes": ["85025", "80061"],
        "variants": {
            "85025": "CBC (complete blood count)",
            "80061": "lipid panel (cholesterol & triglycerides)",
        },
        "synonyms": [
            "blood test",
            "blood work",
            "bloodwork",
            "cbc",
            "lipid panel",
            "cholesterol test",
            "cholesterol",
            "lab work",
            "labs",
        ],
    },
]


def search_services(query: str) -> list[dict]:
    """Match a plain-English query to services. Returns all services if no match."""
    query_lower = query.lower().strip()
    scored = []
    for svc in SERVICE_CATALOG:
        name_lower = svc["name"].lower()
        # Exact name match
        if query_lower == name_lower:
            scored.append((100, svc))
            continue
        # Name contains query or query contains name
        if query_lower in name_lower or name_lower in query_lower:
            scored.append((80, svc))
            continue
        # Synonym match
        synonym_matched = False
        for syn in svc["synonyms"]:
            if query_lower == syn or query_lower in syn or syn in query_lower:
                scored.append((60, svc))
                synonym_matched = True
                break
        if synonym_matched:
            continue
        # Word overlap
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        synonym_words = set()
        for syn in svc["synonyms"]:
            synonym_words.update(syn.split())
        overlap = query_words & (name_words | synonym_words)
        if overlap:
            scored.append((len(overlap) * 20, svc))

    if not scored:
        return list(SERVICE_CATALOG)
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0]
    return [svc for score, svc in scored if score >= top_score]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_search.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/search.py tests/test_search.py
git commit -m "feat: add service catalog and synonym search"
```

---

### Task 3: Data Pipeline

**Files:**
- Create: `scripts/build_dataset.py`
- Create: `tests/test_build_dataset.py`

- [ ] **Step 1: Write failing tests for data pipeline**

Create `tests/test_build_dataset.py`:

```python
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


def test_target_hcpcs_has_12_codes():
    assert len(TARGET_HCPCS) == 12


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_build_dataset.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.build_dataset'`

- [ ] **Step 3: Create scripts package init**

```bash
touch scripts/__init__.py
```

- [ ] **Step 4: Implement build_dataset.py**

Create `scripts/build_dataset.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_build_dataset.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Run the pipeline on real data**

```bash
python3 -m scripts.build_dataset
```

Expected: prints "Saved ~3500 rows to data/processed/indiana_prices.parquet"

- [ ] **Step 7: Verify the output**

```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data/processed/indiana_prices.parquet')
print(f'Rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print(f'Services: {df[\"service_name\"].value_counts().to_dict()}')
print(f'Cities: {df[\"Rndrng_Prvdr_City\"].nunique()} unique')
print(f'Charge range: \${df[\"Avg_Sbmtd_Chrg\"].min():.0f} - \${df[\"Avg_Sbmtd_Chrg\"].max():.0f}')
"
```

- [ ] **Step 8: Commit**

```bash
git add scripts/__init__.py scripts/build_dataset.py tests/test_build_dataset.py data/processed/indiana_prices.parquet
git commit -m "feat: add data pipeline, build Indiana price dataset"
```

---

### Task 4: Data Loader

**Files:**
- Create: `app/data_loader.py`
- Create: `tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_data_loader.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_data_loader.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.data_loader'`

- [ ] **Step 3: Implement data_loader.py**

Create `app/data_loader.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_data_loader.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/data_loader.py tests/test_data_loader.py
git commit -m "feat: add data loader with filtering and statewide stats"
```

---

### Task 5: Streamlit App

**Files:**
- Create: `app/streamlit_app.py`

- [ ] **Step 1: Implement streamlit_app.py**

Create `app/streamlit_app.py`:

```python
"""ClearCare Prototype — Indiana Healthcare Price Comparison."""

import streamlit as st
import pandas as pd
from app.data_loader import load_data, get_providers_for_service, get_statewide_stats
from app.search import search_services, SERVICE_CATALOG

st.set_page_config(page_title="ClearCare — Compare Healthcare Prices", layout="wide")


@st.cache_data
def cached_load():
    return load_data()


def format_provider_name(row: pd.Series) -> str:
    """Format provider name from last/first or org name."""
    if row["Rndrng_Prvdr_Ent_Cd"] == "I":
        first = row.get("Rndrng_Prvdr_First_Name", "")
        last = row.get("Rndrng_Prvdr_Last_Org_Name", "")
        return f"{first} {last}".strip() if first else last
    return row.get("Rndrng_Prvdr_Last_Org_Name", "Unknown")


def main():
    df = cached_load()

    # --- Sidebar ---
    st.sidebar.title("ClearCare")
    st.sidebar.markdown("Compare healthcare prices across Indiana providers")

    query = st.sidebar.text_input(
        "Search for a procedure",
        placeholder="e.g. knee MRI, colonoscopy, blood test",
    )

    # Service selection
    if query:
        matches = search_services(query)
    else:
        matches = SERVICE_CATALOG

    service_names = [s["name"] for s in matches]
    selected_name = st.sidebar.selectbox("Select a service", service_names)
    selected_service = next(s for s in SERVICE_CATALOG if s["name"] == selected_name)

    # Variant selection (HCPCS code)
    variant_options = {
        f"{code} — {selected_service['variants'][code]}": code
        for code in selected_service["hcpcs_codes"]
    }
    if len(variant_options) > 1:
        variant_label = st.sidebar.radio("Variant", list(variant_options.keys()))
        selected_hcpcs = variant_options[variant_label]
    else:
        selected_hcpcs = selected_service["hcpcs_codes"][0]

    # City filter
    service_df = df[df["service_name"] == selected_name]
    cities = sorted(service_df["Rndrng_Prvdr_City"].dropna().unique())
    city_filter = st.sidebar.selectbox("Filter by city", ["All cities"] + list(cities))
    city = None if city_filter == "All cities" else city_filter

    # Sort
    sort_options = {
        "Price (low to high)": "Avg_Sbmtd_Chrg",
        "Medicare allowed (low to high)": "Avg_Mdcr_Alowd_Amt",
        "Patient volume (high to low)": "Tot_Benes",
    }
    sort_label = st.sidebar.selectbox("Sort by", list(sort_options.keys()))
    sort_col = sort_options[sort_label]

    # --- Main area ---
    st.title(f"{selected_name}")
    st.caption(f"{selected_service['category']} · {selected_service['variants'][selected_hcpcs]}")

    # Statewide summary
    stats = get_statewide_stats(df, selected_hcpcs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Low (10th percentile)", f"${stats['charge_p10']:,.0f}")
    col2.metric("Typical (median)", f"${stats['charge_median']:,.0f}")
    col3.metric("High (90th percentile)", f"${stats['charge_p90']:,.0f}")
    st.caption("Statewide billed charges — Indiana providers, Medicare data 2023")

    st.divider()

    # Provider table
    providers = get_providers_for_service(df, selected_name, hcpcs_code=selected_hcpcs, city=city, sort_by=sort_col)
    if sort_col == "Tot_Benes":
        providers = providers.sort_values(sort_col, ascending=False).reset_index(drop=True)

    if providers.empty:
        st.warning("No providers found for this selection.")
    else:
        st.subheader(f"{len(providers)} providers found")

        display_df = pd.DataFrame(
            {
                "Provider": providers.apply(format_provider_name, axis=1),
                "City": providers["Rndrng_Prvdr_City"],
                "ZIP": providers["Rndrng_Prvdr_Zip5"],
                "Avg Billed Charge": providers["Avg_Sbmtd_Chrg"].apply(lambda x: f"${x:,.0f}"),
                "Medicare Allowed": providers["Avg_Mdcr_Alowd_Amt"].apply(lambda x: f"${x:,.0f}"),
                "Medicare Patients": providers["Tot_Benes"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "N/A"),
            }
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Caveats
    st.divider()
    st.markdown(
        """
        <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; font-size: 0.85rem;">
        <strong>Important:</strong>
        <ul style="margin-bottom: 0;">
        <li>Prices shown are based on Medicare billing data (2023). Actual cash or self-pay prices may differ.</li>
        <li>Estimates do not include separate charges for anesthesia, pathology, facility fees, or additional services.</li>
        <li>This tool provides estimates only — contact the provider for a quote before scheduling.</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the app locally**

```bash
python3 -m streamlit run app/streamlit_app.py
```

Expected: opens browser at `http://localhost:8501` showing the ClearCare interface.

- [ ] **Step 3: Manual smoke test**

Verify in the browser:
1. Search "knee MRI" — should show MRI Knee with variant selector
2. Select "without contrast" — should show statewide p10/median/p90 and provider table
3. Filter by city "Indianapolis" — table narrows
4. Search "blood test" — should show Blood Work
5. Caveats footer is visible on every view

- [ ] **Step 4: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat: add Streamlit price comparison UI"
```

---

### Task 6: README and Deployment Prep

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

```markdown
# ClearCare — Indiana Healthcare Price Comparison

Compare healthcare prices across Indiana providers for common shoppable services.

## Services Available

- MRI Brain (with/without contrast)
- MRI Knee (with/without contrast)
- CT Abdomen & Pelvis (with/before+after contrast)
- Screening Mammogram
- Colonoscopy (diagnostic/biopsy/polyp removal)
- Blood Work — CBC + Lipid Panel

## Data Source

Medicare Physician & Other Practitioners by Provider and Service (2023), published by CMS.

Prices shown are Medicare billing data. Actual cash or self-pay prices may differ.

## Setup

```bash
pip install -r requirements.txt
```

### Rebuild data (optional — processed data is included)

```bash
# Download CMS data to data/raw/ first (see CLAUDE.md for URLs)
python3 -m scripts.build_dataset
```

### Run locally

```bash
streamlit run app/streamlit_app.py
```

## Deployment

Deployed on [Streamlit Cloud](https://streamlit.io/cloud). Connect this repo and set the main file to `app/streamlit_app.py`.
```

- [ ] **Step 2: Verify all tests pass**

```bash
python3 -m pytest tests/ -v
```

Expected: all 18 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and deployment instructions"
```

- [ ] **Step 4: Run full app one more time to confirm everything works end-to-end**

```bash
python3 -m streamlit run app/streamlit_app.py
```

Verify the app loads, search works, prices display, caveats show.

---
