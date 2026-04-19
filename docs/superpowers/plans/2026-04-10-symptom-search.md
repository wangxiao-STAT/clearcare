# Symptom Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users search by symptom ("knee pain", "heartburn") or condition and see matched services, plus a friendly out-of-scope message for things ClearCare doesn't cover (primary care, ER, urgent care).

**Architecture:** Extend `SERVICE_CATALOG` with a new `symptoms` field per service. Add an `OUT_OF_SCOPE_TERMS` dict. Change `search_services()` to return a `SearchResult` dataclass with `services`, `matched_symptom`, and `out_of_scope` fields. Wire the UI to render a symptom caption or an out-of-scope info box as appropriate.

**Tech Stack:** Python stdlib `dataclasses`, existing streamlit/pytest. No new dependencies.

---

## File Structure

| File | Action | What |
|------|--------|------|
| `app/search.py` | Modify | Add `SearchResult` dataclass, `OUT_OF_SCOPE_TERMS`; extend all 16 services with `symptoms`; rewrite `search_services()`; extract existing scoring into `_score_procedure_match()` |
| `tests/test_search.py` | Modify | Update 14 existing tests to use `result.services`; add 5 new symptom/out-of-scope tests |
| `app/streamlit_app.py` | Modify | Update `render_search()` to unpack `SearchResult`, render out-of-scope info box + early return, render symptom caption |
| All other files | No change | |

---

### Task 1: Add `SearchResult`, `OUT_OF_SCOPE_TERMS`, and `symptoms` Catalog

**Files:**

- Modify: `app/search.py`

- [ ] **Step 1: Add imports and `SearchResult` dataclass at the top of `app/search.py`**

Open `app/search.py`. At the VERY top of the file (before the existing `SERVICE_CATALOG = [...]` line), add:

```python
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    services: list[dict]
    matched_symptom: str | None = None
    out_of_scope: str | None = None
```

- [ ] **Step 2: Add a `symptoms` list to every service in `SERVICE_CATALOG`**

For each service entry, add a `"symptoms": [...]` field right after `"synonyms": [...]`. The complete updated catalog should look like this (replace the entire existing `SERVICE_CATALOG = [...]` list):

```python
SERVICE_CATALOG = [
    {
        "name": "MRI Brain",
        "category": "Imaging",
        "hcpcs_codes": ["70551", "70553"],
        "variants": {"70551": "without contrast", "70553": "with contrast"},
        "synonyms": ["mri brain", "brain mri", "brain scan", "head mri", "mri head"],
        "symptoms": [
            "headache",
            "migraine",
            "dizziness",
            "memory problems",
            "stroke symptoms",
            "numbness",
            "tingling",
        ],
    },
    {
        "name": "MRI Knee",
        "category": "Imaging",
        "hcpcs_codes": ["73721", "73723"],
        "variants": {"73721": "without contrast", "73723": "with contrast"},
        "synonyms": ["mri knee", "knee mri", "knee scan", "leg mri", "mri leg joint"],
        "symptoms": [
            "knee pain",
            "knee injury",
            "knee swelling",
            "meniscus",
            "acl",
            "torn ligament",
        ],
    },
    {
        "name": "CT Head",
        "category": "Imaging",
        "hcpcs_codes": ["70450"],
        "variants": {"70450": "without contrast"},
        "synonyms": ["ct head", "head ct", "ct brain", "cat scan head", "head scan", "brain ct"],
        "symptoms": [
            "head injury",
            "concussion",
            "severe headache",
            "head trauma",
        ],
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
        "symptoms": [
            "belly pain",
            "abdominal pain",
            "stomach pain",
            "kidney stone",
            "appendicitis",
            "pelvic pain",
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
        "symptoms": [
            "cough",
            "shortness of breath",
            "chest pain",
            "pneumonia",
            "lung problem",
            "bronchitis",
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
        "symptoms": [
            "gallbladder pain",
            "gallstones",
            "liver problem",
            "belly ultrasound",
            "abdominal swelling",
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
        "symptoms": [
            "breast cancer screening",
            "breast exam",
            "yearly mammogram",
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
        "symptoms": [
            "heart check",
            "heart murmur",
            "shortness of breath",
            "heart failure",
            "irregular heartbeat",
            "chest pain",
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
        "symptoms": [
            "colon cancer screening",
            "rectal bleeding",
            "blood in stool",
            "bowel problem",
            "polyps",
            "change in bowel habits",
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
        "symptoms": [
            "heartburn",
            "acid reflux",
            "gerd",
            "trouble swallowing",
            "stomach pain",
            "ulcer",
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
        "symptoms": [
            "fatigue",
            "tiredness",
            "anemia check",
            "infection check",
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
        "symptoms": [
            "cholesterol check",
            "heart disease risk",
            "annual cholesterol",
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
        "symptoms": [
            "diabetes check",
            "kidney function",
            "liver function",
            "annual blood work",
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
        "symptoms": [
            "diabetes check",
            "diabetes monitoring",
            "blood sugar",
            "prediabetes",
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
        "symptoms": [
            "fatigue",
            "weight change",
            "thyroid check",
            "thyroid symptoms",
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
        "symptoms": [
            "knee pain",
            "back pain",
            "shoulder pain",
            "neck pain",
            "injury recovery",
            "rehab",
            "sports injury",
        ],
    },
]
```

- [ ] **Step 3: Add the `OUT_OF_SCOPE_TERMS` constant**

Immediately after the `SERVICE_CATALOG = [...]` list definition and BEFORE the existing `def search_services(...)` function, add:

```python
OUT_OF_SCOPE_TERMS = {
    "primary care": "primary care",
    "pcp": "primary care",
    "family doctor": "primary care",
    "annual physical": "primary care",
    "checkup": "primary care",
    "urgent care": "urgent care",
    "walk in clinic": "urgent care",
    "er": "emergency",
    "emergency room": "emergency",
    "emergency": "emergency",
    "dermatologist": "specialist visit",
    "allergist": "specialist visit",
    "mental health": "mental health",
    "therapy": "mental health",
    "dentist": "dental",
    "eye doctor": "vision",
}
```

- [ ] **Step 4: Syntax check**

```bash
python3 -c "from app.search import SERVICE_CATALOG, OUT_OF_SCOPE_TERMS, SearchResult; print(f'{len(SERVICE_CATALOG)} services, {len(OUT_OF_SCOPE_TERMS)} out-of-scope terms'); print(SearchResult(services=[]))"
```

Expected output:

```
16 services, 16 out-of-scope terms
SearchResult(services=[], matched_symptom=None, out_of_scope=None)
```

- [ ] **Step 5: Commit**

```bash
git add app/search.py
git commit -m "feat: add SearchResult, OUT_OF_SCOPE_TERMS, symptoms field to catalog"
```

---

### Task 2: Rewrite `search_services()` to Return `SearchResult`

**Files:**

- Modify: `app/search.py`

- [ ] **Step 1: Replace the existing `search_services` function**

Find this existing function (at the bottom of `app/search.py`):

```python
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

Replace it with a helper `_score_procedure_match` plus a new `search_services` that returns `SearchResult`:

```python
def _score_procedure_match(query_lower: str) -> list[dict]:
    """Existing procedure-name + synonym scoring. Returns the top-tier matches, or full catalog if none."""
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


def search_services(query: str) -> SearchResult:
    """Match a plain-English query to services.

    Returns a SearchResult with:
    - services: matched services (empty if out of scope; full catalog if query is empty or no match)
    - matched_symptom: the symptom the user typed, if recognized
    - out_of_scope: category label if the query is something ClearCare doesn't cover
    """
    if not query or not query.strip():
        return SearchResult(services=list(SERVICE_CATALOG))

    q = query.lower().strip()

    # 1. Out-of-scope check FIRST
    for term, category in OUT_OF_SCOPE_TERMS.items():
        if term == q or term in q or q in term:
            return SearchResult(services=[], out_of_scope=category)

    # 2. Symptom match
    matched_symptom: str | None = None
    symptom_hits: list[dict] = []
    seen_names: set[str] = set()
    for svc in SERVICE_CATALOG:
        for symptom in svc.get("symptoms", []):
            s = symptom.lower()
            if q == s or q in s or s in q:
                if svc["name"] not in seen_names:
                    symptom_hits.append(svc)
                    seen_names.add(svc["name"])
                if matched_symptom is None:
                    matched_symptom = symptom
                break
    if symptom_hits:
        return SearchResult(services=symptom_hits, matched_symptom=matched_symptom)

    # 3. Existing procedure-name + synonym scoring
    services = _score_procedure_match(q)
    return SearchResult(services=services)
```

- [ ] **Step 2: Syntax check**

```bash
python3 -c "from app.search import search_services; r = search_services('knee pain'); print(f'services={len(r.services)} matched_symptom={r.matched_symptom!r} oos={r.out_of_scope!r}')"
```

Expected output:

```
services=2 matched_symptom='knee pain' oos=None
```

- [ ] **Step 3: Commit**

```bash
git add app/search.py
git commit -m "feat: rewrite search_services to return SearchResult with symptom/oos support"
```

---

### Task 3: Update Existing Tests to Use `result.services`

**Files:**

- Modify: `tests/test_search.py`

- [ ] **Step 1: Rewrite the whole `tests/test_search.py` file**

Replace the entire contents of `tests/test_search.py` with:

```python
from app.search import search_services, SERVICE_CATALOG


def test_exact_service_name():
    result = search_services("MRI Knee")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"
    assert set(result.services[0]["hcpcs_codes"]) == {"73721", "73723"}


def test_synonym_match():
    result = search_services("knee scan")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"


def test_partial_match():
    result = search_services("colonoscopy")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Colonoscopy"


def test_broad_term_returns_multiple():
    result = search_services("MRI")
    names = {r["name"] for r in result.services}
    assert "MRI Brain" in names
    assert "MRI Knee" in names


def test_no_match_returns_all():
    result = search_services("xyz nonsense")
    assert len(result.services) == len(SERVICE_CATALOG)


def test_case_insensitive():
    result = search_services("mri knee")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "MRI Knee"


def test_cbc_synonym():
    result = search_services("cbc")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "CBC (Complete Blood Count)"


def test_catalog_has_sixteen_services():
    assert len(SERVICE_CATALOG) == 16


def test_each_service_has_required_fields():
    for svc in SERVICE_CATALOG:
        assert "name" in svc
        assert "category" in svc
        assert "hcpcs_codes" in svc
        assert "synonyms" in svc
        assert "symptoms" in svc
        assert len(svc["hcpcs_codes"]) > 0


def test_a1c_synonym():
    result = search_services("a1c")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "HbA1c (Diabetes Test)"


def test_thyroid_synonym():
    result = search_services("thyroid")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "TSH (Thyroid Test)"


def test_echo_synonym():
    result = search_services("echo")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Echocardiogram"


def test_egd_synonym():
    result = search_services("egd")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Upper GI Endoscopy (EGD)"


def test_chest_xray_synonym():
    result = search_services("chest xray")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Chest X-ray"


def test_symptom_knee_pain_returns_mri_and_pt():
    result = search_services("knee pain")
    names = {s["name"] for s in result.services}
    assert "MRI Knee" in names
    assert "Physical Therapy Evaluation" in names


def test_symptom_heartburn_returns_egd():
    result = search_services("heartburn")
    assert len(result.services) == 1
    assert result.services[0]["name"] == "Upper GI Endoscopy (EGD)"


def test_symptom_sets_matched_symptom_field():
    result = search_services("knee pain")
    assert result.matched_symptom is not None
    assert "knee pain" in result.matched_symptom.lower()


def test_out_of_scope_primary_care():
    result = search_services("primary care")
    assert result.services == []
    assert result.out_of_scope == "primary care"
    assert result.matched_symptom is None


def test_out_of_scope_emergency_room():
    result = search_services("emergency room")
    assert result.services == []
    assert result.out_of_scope == "emergency"
```

- [ ] **Step 2: Run all search tests**

```bash
python3 -m pytest tests/test_search.py -v
```

Expected: 19 tests PASS (14 updated + 5 new).

- [ ] **Step 3: Run the full test suite to confirm nothing else regressed**

```bash
python3 -m pytest tests/ -q
```

Expected: 41 total PASS (36 prior + 5 new search tests; note existing test_each_service_has_required_fields now also asserts `symptoms` is present, which is the only behavioral change for existing tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_search.py
git commit -m "test: update search tests for SearchResult, add symptom and oos tests"
```

---

### Task 4: Wire UI to `SearchResult`

**Files:**

- Modify: `app/streamlit_app.py`

- [ ] **Step 1: Find the existing search-to-dropdown block in `render_search`**

In `app/streamlit_app.py`, find this block inside `render_search(df)`:

```python
    # Search input (main area, prominent)
    query = st.text_input(
        "What procedure are you looking for?",
        placeholder="e.g. knee MRI, colonoscopy, blood test, a1c",
        key="main_search",
    )

    # Service selection
    if query:
        matches = search_services(query)
    else:
        matches = SERVICE_CATALOG

    service_names = [s["name"] for s in matches]
    selected_name = st.selectbox("Select a service", service_names)
```

- [ ] **Step 2: Replace the search-to-dropdown block**

Replace the block from Step 1 with:

```python
    # Search input (main area, prominent)
    query = st.text_input(
        "What procedure are you looking for?",
        placeholder="e.g. knee MRI, heartburn, cholesterol check, a1c",
        key="main_search",
    )

    # Service selection — unpack SearchResult
    result = search_services(query)

    if result.out_of_scope:
        st.info(
            "ClearCare currently covers imaging, GI procedures, labs, and physical therapy "
            f"in Indiana. We don't have **{result.out_of_scope}** pricing yet — "
            "please check back as we expand."
        )
        st.divider()
        st.warning(
            "**Important:**\n"
            "- Prices shown are based on Medicare billing data (2023). Actual cash or self-pay prices may differ.\n"
            "- Estimates do not include separate charges for anesthesia, pathology, facility fees, or additional services.\n"
            "- This tool provides estimates only — contact the provider for a quote before scheduling."
        )
        return

    if result.matched_symptom and result.services:
        matched_names = ", ".join(s["name"] for s in result.services)
        st.caption(
            f"Showing services for **{result.matched_symptom}**: {matched_names}"
        )

    matches = result.services if result.services else list(SERVICE_CATALOG)
    service_names = [s["name"] for s in matches]
    selected_name = st.selectbox("Select a service", service_names)
```

Notes:

- The placeholder changes from "knee MRI, colonoscopy, blood test, a1c" to "knee MRI, heartburn, cholesterol check, a1c" to teach users that symptom search is supported.
- The `return` inside the out-of-scope branch ends `render_search` early; the rest of the function (variant radio, stats, cards, etc.) doesn't run. The caveats footer is rendered BEFORE the return so users still see it.

- [ ] **Step 3: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('app/streamlit_app.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 4: Run the full test suite to confirm nothing broke**

```bash
python3 -m pytest tests/ -q
```

Expected: 41 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat: render symptom caption and out-of-scope info box in search UI"
```

---

### Task 5: Smoke Test and Push

**Files:** None modified — verification only.

- [ ] **Step 1: Launch the app locally**

```bash
pkill -f "streamlit run" || true
python3 -m streamlit run app/streamlit_app.py
```

Expected: app launches at `http://localhost:8501`.

- [ ] **Step 2: Desktop verification**

In the browser:

1. Landing page loads as before. Click **Get Started →**.
2. On the search page, clear any text and verify all 16 services are in the dropdown.
3. Type **"knee pain"**. Expected: caption "Showing services for **knee pain**: MRI Knee, Physical Therapy Evaluation" appears above the dropdown; dropdown has those 2 options.
4. Type **"heartburn"**. Expected: caption mentions heartburn, dropdown shows only "Upper GI Endoscopy (EGD)".
5. Type **"chest pain"**. Expected: caption mentions chest pain, dropdown shows Chest X-ray and Echocardiogram.
6. Type **"fatigue"**. Expected: caption shown, dropdown shows CBC and TSH.
7. Type **"cholesterol check"**. Expected: caption shown, dropdown shows Lipid Panel.
8. Type **"primary care"**. Expected: blue info box appears ("ClearCare currently covers imaging, GI procedures, labs, and physical therapy in Indiana. We don't have **primary care** pricing yet…"); no service dropdown, no metrics, no cards; caveats footer visible; nothing else on the page.
9. Type **"urgent care"**. Expected: same info box pattern with "urgent care".
10. Type **"emergency room"**. Expected: info box with "emergency".
11. Type **"MRI Knee"** (procedure name). Expected: NO caption (procedure match, not symptom match); dropdown shows MRI Knee.
12. Clear the search and select a service normally. Expected: entire rest of the page (stats, explanation, cards, caveats) works unchanged.

- [ ] **Step 3: Mobile verification**

Open the app on your phone or in Chrome DevTools mobile emulation. Repeat key flows from Step 2: "knee pain" shows caption + two services; "primary care" shows info box.

- [ ] **Step 4: Stop Streamlit**

Press `Ctrl+C` in the terminal running the app.

- [ ] **Step 5: Push to GitHub**

```bash
git push
```

Expected: 4 new commits (one per earlier task) pushed to `main`. Streamlit Cloud auto-redeploys in 1-2 minutes.

- [ ] **Step 6: Verify the deployed app**

Open the Streamlit Cloud URL. Verify "knee pain" returns MRI Knee + PT Eval with caption, and "primary care" shows the out-of-scope info box.

---
