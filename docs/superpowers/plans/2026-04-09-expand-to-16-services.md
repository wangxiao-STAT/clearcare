# Expand ClearCare to 16 Services Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the ClearCare prototype from 6 services (12 HCPCS codes) to 16 services (28 HCPCS codes) by updating the service catalog, test suite, and regenerating the Parquet dataset.

**Architecture:** The system is catalog-driven — `SERVICE_CATALOG` in `app/search.py` is the single source of truth. The data pipeline (`scripts/build_dataset.py`) imports it. The UI (`app/streamlit_app.py`) and data loader (`app/data_loader.py`) are service-name agnostic. No structural code changes needed.

**Tech Stack:** Python 3.11, pandas, pyarrow, streamlit, pytest (unchanged)

---

## File Structure (unchanged)

Only the following files will be modified:
- `app/search.py` — replace `SERVICE_CATALOG` contents
- `tests/test_search.py` — update catalog size assertion, update/remove blood test synonym test, add 5 new synonym tests
- `tests/test_build_dataset.py` — update HCPCS count assertion
- `data/processed/indiana_prices.parquet` — regenerated

No files created or deleted. No files added to the repo.

---

### Task 1: Replace Service Catalog

**Files:**
- Modify: `app/search.py` (replace `SERVICE_CATALOG` list, lines 1-80)

- [ ] **Step 1: Replace the SERVICE_CATALOG list with the 16-service version**

Open `app/search.py` and replace the entire `SERVICE_CATALOG = [...]` list (the one with 6 entries) with this 16-entry version. Keep the `search_services()` function below unchanged.

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
        "name": "CT Head",
        "category": "Imaging",
        "hcpcs_codes": ["70450"],
        "variants": {"70450": "without contrast"},
        "synonyms": ["ct head", "head ct", "ct brain", "cat scan head", "head scan", "brain ct"],
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
        "name": "Chest X-ray",
        "category": "Imaging",
        "hcpcs_codes": ["71046"],
        "variants": {"71046": "2 views"},
        "synonyms": [
            "chest xray",
            "chest x-ray",
            "x-ray chest",
            "chest xr",
            "lung xray",
            "chest radiograph",
        ],
    },
    {
        "name": "Ultrasound Abdomen",
        "category": "Imaging",
        "hcpcs_codes": ["76700", "76705"],
        "variants": {"76700": "complete", "76705": "limited"},
        "synonyms": [
            "ultrasound abdomen",
            "abdominal ultrasound",
            "belly ultrasound",
            "abdomen sonogram",
            "abdomen ultrasound",
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
        "name": "Echocardiogram",
        "category": "Imaging",
        "hcpcs_codes": ["93306"],
        "variants": {"93306": "complete with Doppler"},
        "synonyms": [
            "echo",
            "echocardiogram",
            "heart ultrasound",
            "heart echo",
            "cardiac ultrasound",
            "echocardiography",
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
            "colon screening",
            "colon exam",
            "lower endoscopy",
        ],
    },
    {
        "name": "Upper GI Endoscopy (EGD)",
        "category": "GI/Outpatient",
        "hcpcs_codes": ["43235", "43239"],
        "variants": {"43235": "diagnostic", "43239": "with biopsy"},
        "synonyms": [
            "egd",
            "upper endoscopy",
            "upper gi",
            "stomach scope",
            "esophagus scope",
            "upper gi scope",
            "esophagogastroduodenoscopy",
        ],
    },
    {
        "name": "CBC (Complete Blood Count)",
        "category": "Labs",
        "hcpcs_codes": ["85025"],
        "variants": {"85025": "automated with differential"},
        "synonyms": [
            "cbc",
            "complete blood count",
            "blood count",
            "white cell count",
            "blood cell count",
        ],
    },
    {
        "name": "Lipid Panel",
        "category": "Labs",
        "hcpcs_codes": ["80061"],
        "variants": {"80061": "cholesterol & triglycerides"},
        "synonyms": [
            "lipid panel",
            "cholesterol test",
            "cholesterol",
            "lipid",
            "triglycerides",
            "lipid profile",
        ],
    },
    {
        "name": "CMP (Comprehensive Metabolic Panel)",
        "category": "Labs",
        "hcpcs_codes": ["80053"],
        "variants": {"80053": "14-test panel"},
        "synonyms": [
            "cmp",
            "comprehensive metabolic panel",
            "metabolic panel",
            "chem 14",
            "metabolic test",
            "chemistry panel",
        ],
    },
    {
        "name": "HbA1c (Diabetes Test)",
        "category": "Labs",
        "hcpcs_codes": ["83036"],
        "variants": {"83036": "glycated hemoglobin"},
        "synonyms": [
            "a1c",
            "hba1c",
            "hemoglobin a1c",
            "diabetes test",
            "glycated hemoglobin",
            "sugar test",
            "blood sugar test",
        ],
    },
    {
        "name": "TSH (Thyroid Test)",
        "category": "Labs",
        "hcpcs_codes": ["84443"],
        "variants": {"84443": "thyroid stimulating hormone"},
        "synonyms": [
            "tsh",
            "thyroid",
            "thyroid test",
            "thyroid stimulating hormone",
            "thyroid panel",
            "thyroid function",
        ],
    },
    {
        "name": "Physical Therapy Evaluation",
        "category": "Rehab",
        "hcpcs_codes": ["97161", "97162"],
        "variants": {"97161": "low complexity (20 min)", "97162": "moderate complexity (30 min)"},
        "synonyms": [
            "pt eval",
            "physical therapy eval",
            "pt evaluation",
            "physical therapy evaluation",
            "pt assessment",
        ],
    },
]
```

- [ ] **Step 2: Verify the file is still importable**

Run:

```bash
python3 -c "from app.search import SERVICE_CATALOG; print(f'{len(SERVICE_CATALOG)} services')"
```

Expected output: `16 services`

- [ ] **Step 3: Commit**

```bash
git add app/search.py
git commit -m "feat: expand service catalog to 16 services with 28 HCPCS codes"
```

---

### Task 2: Update Search Tests

**Files:**
- Modify: `tests/test_search.py`

- [ ] **Step 1: Update `test_catalog_has_six_services`**

Open `tests/test_search.py`. Find the function `test_catalog_has_six_services` and replace it with:

```python
def test_catalog_has_sixteen_services():
    assert len(SERVICE_CATALOG) == 16
```

- [ ] **Step 2: Replace `test_blood_test_synonym`**

The old test was:

```python
def test_blood_test_synonym():
    results = search_services("blood test")
    assert len(results) == 1
    assert results[0]["name"] == "Blood Work (CBC + Lipid Panel)"
```

Replace it with:

```python
def test_cbc_synonym():
    results = search_services("cbc")
    assert len(results) == 1
    assert results[0]["name"] == "CBC (Complete Blood Count)"
```

- [ ] **Step 3: Add 5 new synonym tests**

Add these tests to the end of `tests/test_search.py`:

```python
def test_a1c_synonym():
    results = search_services("a1c")
    assert len(results) == 1
    assert results[0]["name"] == "HbA1c (Diabetes Test)"


def test_thyroid_synonym():
    results = search_services("thyroid")
    assert len(results) == 1
    assert results[0]["name"] == "TSH (Thyroid Test)"


def test_echo_synonym():
    results = search_services("echo")
    assert len(results) == 1
    assert results[0]["name"] == "Echocardiogram"


def test_egd_synonym():
    results = search_services("egd")
    assert len(results) == 1
    assert results[0]["name"] == "Upper GI Endoscopy (EGD)"


def test_chest_xray_synonym():
    results = search_services("chest xray")
    assert len(results) == 1
    assert results[0]["name"] == "Chest X-ray"
```

- [ ] **Step 4: Run search tests**

```bash
python3 -m pytest tests/test_search.py -v
```

Expected: all 14 tests PASS (9 original, minus `test_catalog_has_six_services` and `test_blood_test_synonym` which are replaced, plus 6 new tests = 14 total).

If any test fails, read the failure, check that the synonym is listed in the corresponding service's `synonyms` field in `app/search.py`, and adjust if needed. Do NOT weaken assertions to make tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_search.py
git commit -m "test: update search tests for 16-service catalog"
```

---

### Task 3: Update Build Dataset Test

**Files:**
- Modify: `tests/test_build_dataset.py`

- [ ] **Step 1: Update the HCPCS count assertion**

Open `tests/test_build_dataset.py`. Find the function `test_target_hcpcs_has_12_codes` and replace it with:

```python
def test_target_hcpcs_has_28_codes():
    assert len(TARGET_HCPCS) == 28
```

- [ ] **Step 2: Run build dataset tests**

```bash
python3 -m pytest tests/test_build_dataset.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_build_dataset.py
git commit -m "test: update HCPCS count assertion to 28 codes"
```

---

### Task 4: Regenerate Parquet Dataset

**Files:**
- Modify: `data/processed/indiana_prices.parquet` (regenerated)

- [ ] **Step 1: Run the pipeline**

```bash
python3 -m scripts.build_dataset
```

Expected: Prints "Saved N rows to data/processed/indiana_prices.parquet" where N is approximately 10,000–15,000 (much larger than the V1 count of 3,506 since we added 9 services with thousands of providers each — HbA1c alone has 1,457).

- [ ] **Step 2: Verify the output**

```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data/processed/indiana_prices.parquet')
print(f'Rows: {len(df)}')
print(f'Services: {df[\"service_name\"].nunique()}')
print()
print('Row count per service:')
print(df['service_name'].value_counts().to_string())
print()
print(f'Unique providers: {df[\"Rndrng_NPI\"].nunique()}')
print(f'Unique cities: {df[\"Rndrng_Prvdr_City\"].nunique()}')
print(f'Charge range: \${df[\"Avg_Sbmtd_Chrg\"].min():.0f} - \${df[\"Avg_Sbmtd_Chrg\"].max():.0f}')
"
```

Expected:
- `Services: 16`
- Each of the 16 services shows a non-zero row count
- Row count total matches the step 1 output

- [ ] **Step 3: Run all tests to confirm nothing regressed**

```bash
python3 -m pytest tests/ -v
```

Expected: all tests PASS (should be around 23 tests: 5 build_dataset + 4 data_loader + 14 search).

- [ ] **Step 4: Commit the new Parquet file**

```bash
git add data/processed/indiana_prices.parquet
git commit -m "data: regenerate Parquet with 16-service catalog"
```

---

### Task 5: Local Smoke Test and Push

**Files:** (none modified — this is verification only)

- [ ] **Step 1: Launch the Streamlit app locally**

```bash
python3 -m streamlit run app/streamlit_app.py
```

Expected: App opens at `http://localhost:8501` without errors.

- [ ] **Step 2: Manual verification in the browser**

In the browser, verify the following:

1. The **"Select a service"** dropdown in the sidebar shows 16 options including: MRI Brain, MRI Knee, CT Head, CT Abdomen & Pelvis, Chest X-ray, Ultrasound Abdomen, Screening Mammogram, Echocardiogram, Colonoscopy, Upper GI Endoscopy (EGD), CBC (Complete Blood Count), Lipid Panel, CMP (Comprehensive Metabolic Panel), HbA1c (Diabetes Test), TSH (Thyroid Test), Physical Therapy Evaluation.
2. Type **"a1c"** in the search box — the dropdown should narrow to "HbA1c (Diabetes Test)".
3. Select HbA1c — the main area should show a statewide price summary and a provider table.
4. Type **"echo"** — should narrow to "Echocardiogram".
5. Type **"chest xray"** — should narrow to "Chest X-ray".
6. Type **"egd"** — should narrow to "Upper GI Endoscopy (EGD)".
7. Clear the search box — dropdown should show all 16 services again.
8. The caveats warning box is visible at the bottom on every service view.

If any step fails, stop the app, check the logs, fix the issue, and re-run this task.

- [ ] **Step 3: Stop the Streamlit app**

Press `Ctrl+C` in the terminal running the app.

- [ ] **Step 4: Push to GitHub**

```bash
git push
```

Expected: All commits pushed to `main`. Streamlit Cloud will auto-redeploy within 1-2 minutes.

- [ ] **Step 5: Verify the deployed app**

Open the Streamlit Cloud URL in a browser and verify at least one new service (e.g., HbA1c or Echocardiogram) loads and shows provider data.

---
