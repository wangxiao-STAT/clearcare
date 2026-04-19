# Symptom Search

## Overview

Extend ClearCare's search so users can type symptoms or conditions ("knee pain", "heartburn", "cholesterol check") and get matched services — not just procedure names. Add a small caption acknowledging the recognized symptom. For out-of-scope requests (primary care, ER, urgent care), show a friendly message explaining what ClearCare covers.

## Motivation

Patients think in symptoms (*what hurts*), not procedures (*what scan*). The current search requires users to already know the test they need ("MRI knee", "colonoscopy"). Zocdoc's biggest UX win is translating "back pain" → relevant specialties. ClearCare can do the same with minimal code: extend the curated synonym map to include symptoms, and surface multiple services when a symptom matches more than one (e.g., "knee pain" → MRI Knee + Physical Therapy Evaluation).

## Scope

One file of logic (`app/search.py`), one file of UI (`app/streamlit_app.py`), one file of tests (`tests/test_search.py`). No new dependencies, no new data files, no LLM. ~30 curated symptoms covering all 16 services plus ~10 out-of-scope terms.

## Data Model Changes

### 1. `SearchResult` dataclass

`search_services()` currently returns `list[dict]`. Change it to return a richer result object so the UI can distinguish "symptom recognized" from "out of scope" from "ordinary procedure match":

```python
from dataclasses import dataclass, field

@dataclass
class SearchResult:
    services: list[dict]
    matched_symptom: str | None = None
    out_of_scope: str | None = None
```

- `services` — list of matched service dicts (empty if out of scope or no matches)
- `matched_symptom` — the symptom the user typed, if recognized (e.g., "knee pain"). Used by UI to show the "Showing services for **knee pain**" caption.
- `out_of_scope` — category label if the query is something ClearCare doesn't cover (e.g., "primary care"). Mutually exclusive with the other fields.

### 2. Extend each service with a `symptoms` list

Add a new field per service in `SERVICE_CATALOG`. Distinct from `synonyms` (procedure aliases). Not all services need every possible symptom — curate the obvious ones.

Full symptom catalog:

| Service | Symptoms |
|---|---|
| MRI Brain | headache, migraine, dizziness, memory problems, stroke symptoms, numbness, tingling |
| MRI Knee | knee pain, knee injury, knee swelling, meniscus, acl, torn ligament |
| CT Head | head injury, concussion, severe headache, head trauma |
| CT Abdomen & Pelvis | belly pain, abdominal pain, stomach pain, kidney stone, appendicitis, pelvic pain |
| Chest X-ray | cough, shortness of breath, chest pain, pneumonia, lung problem, bronchitis |
| Ultrasound Abdomen | gallbladder pain, gallstones, liver problem, belly ultrasound, abdominal swelling |
| Screening Mammogram | breast cancer screening, breast exam, yearly mammogram |
| Echocardiogram | heart check, heart murmur, shortness of breath, heart failure, irregular heartbeat, chest pain |
| Colonoscopy | colon cancer screening, rectal bleeding, blood in stool, bowel problem, polyps, change in bowel habits |
| Upper GI Endoscopy (EGD) | heartburn, acid reflux, gerd, trouble swallowing, stomach pain, ulcer |
| CBC (Complete Blood Count) | fatigue, tiredness, anemia check, infection check |
| Lipid Panel | cholesterol check, heart disease risk, annual cholesterol |
| CMP (Comprehensive Metabolic Panel) | diabetes check, kidney function, liver function, annual blood work |
| HbA1c (Diabetes Test) | diabetes check, diabetes monitoring, blood sugar, prediabetes |
| TSH (Thyroid Test) | fatigue, weight change, thyroid check, thyroid symptoms |
| Physical Therapy Evaluation | knee pain, back pain, shoulder pain, neck pain, injury recovery, rehab, sports injury |

**Deliberate overlaps** (these help users see alternatives):

- "knee pain" → MRI Knee + Physical Therapy Evaluation
- "chest pain" → Chest X-ray + Echocardiogram
- "shortness of breath" → Chest X-ray + Echocardiogram
- "fatigue" → CBC + TSH
- "diabetes check" → CMP + HbA1c
- "stomach pain" → CT Abdomen & Pelvis + Upper GI Endoscopy

### 3. `OUT_OF_SCOPE_TERMS` dict

New module-level constant:

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

Keys are user-typed terms; values are friendly category labels shown in the UI message.

## Search Logic

Rewrite `search_services()` so it returns `SearchResult`:

```python
def search_services(query: str) -> SearchResult:
    if not query or not query.strip():
        return SearchResult(services=list(SERVICE_CATALOG))

    q = query.lower().strip()

    # 1. Out-of-scope check FIRST
    for term, category in OUT_OF_SCOPE_TERMS.items():
        if term == q or term in q or q in term:
            return SearchResult(services=[], out_of_scope=category)

    # 2. Symptom match — iterate services, check each service's symptoms list
    matched_symptom = None
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

    # 3. Fall back to existing procedure-name + synonym scoring
    services = _score_procedure_match(q)
    return SearchResult(services=services)
```

The existing scoring logic (exact name match, substring match, synonym match, word overlap) moves into a helper `_score_procedure_match(q) -> list[dict]` with the same scoring rules as today. No behavior change to procedure-name search.

**Order matters:**

1. Empty query → full catalog (preserves today's behavior)
2. Out-of-scope first so "urgent care" never accidentally matches "care" in a synonym word-overlap
3. Symptom match second so "knee pain" is treated as a symptom (not a fuzzy procedure match)
4. Existing procedure scoring last (backward compatible)

## UI Changes

In `app/streamlit_app.py`'s `render_search(df)`, replace the current search-to-dropdown block:

```python
# Service selection
if query:
    matches = search_services(query)
else:
    matches = SERVICE_CATALOG

service_names = [s["name"] for s in matches]
selected_name = st.selectbox("Select a service", service_names)
```

With:

```python
# Service selection
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

**Behavior:**

- Empty query: `search_services("")` returns full catalog → dropdown shows all 16 services
- Out-of-scope query: blue `st.info` box + caveats footer → `return` skips the rest of the page (no empty service picker, no misleading metrics)
- Symptom match: small caption above the dropdown tells the user what was recognized, then normal flow
- Procedure-name match or no match: silent, same as today

**Why `return` on out-of-scope:** rendering an empty dropdown + "service not found" metrics below would be noisy. A clean info box with a caveats footer below feels like an intentional dead-end rather than a bug.

## Tests

### Update existing tests (14)

Every existing `search_services()` call in `tests/test_search.py` currently treats the return value as a list. Change each to use `.services`:

```python
# Before
results = search_services("MRI Knee")
assert len(results) == 1

# After
result = search_services("MRI Knee")
assert len(result.services) == 1
```

The `test_catalog_has_sixteen_services` and `test_each_service_has_required_fields` tests stay unchanged (they don't call `search_services`).

### Add 5 new tests

```python
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

Total tests after: 14 existing + 5 new = **19 tests in `test_search.py`**, 41 total across the suite.

## Files Changed

| File | Action | What |
|------|--------|------|
| `app/search.py` | Modify | Add `SearchResult` dataclass; add `OUT_OF_SCOPE_TERMS`; add `symptoms` field to all 16 services in `SERVICE_CATALOG`; rewrite `search_services()` to return `SearchResult`; extract existing scoring into `_score_procedure_match()` helper |
| `app/streamlit_app.py` | Modify | Update `render_search()` to unpack `SearchResult`; add out-of-scope info-box path (with caveats footer + `return`); add symptom caption |
| `tests/test_search.py` | Modify | Update existing 14 tests to use `result.services`; add 5 new symptom/out-of-scope tests |
| Other files | No change | |

## Risks

- **Overlapping symptom matches become the primary UX.** If "knee pain" returns 2 services, users have to pick — that's by design per Q1, but some users may expect auto-routing to the "best" one. Accept and observe in pilot; iterate if needed.
- **Out-of-scope false positives.** "primary care" substring match could catch something we didn't anticipate. The term list is short enough to audit by eye.
- **`SearchResult` is a breaking change to the API.** Only `streamlit_app.py` and `test_search.py` import `search_services`; both updated in the same change. No other consumers.
- **`Echocardiogram` matches both "chest pain" and "heart check"** — multiple symptoms pointing to the same service is fine; dedup logic already handles it.

## Non-Goals

- No free-text LLM interpretation (all mappings are curated)
- No fuzzy spelling correction ("kne pain" won't match "knee pain")
- No symptom-to-specialty mapping for primary care (we don't have PCP pricing)
- No UI surface for the full symptom list (users still type queries)
- No analytics on which symptoms users search
- No "related services" chips — when multiple symptoms map to multiple services, the dropdown is the only surface
