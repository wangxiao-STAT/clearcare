# Expand ClearCare Prototype to 16 Services

## Overview

Extend the existing V1 prototype from 6 services (12 HCPCS codes) to 16 services (28 HCPCS codes) by updating the service catalog and regenerating the Parquet dataset. No architectural changes — the system is catalog-driven, so adding services is a matter of adding entries to `SERVICE_CATALOG` in `app/search.py`.

## Motivation

The initial prototype covers 6 shoppable services. The CLAUDE.md roadmap targets ~20 services across imaging, GI, and labs. Expanding the catalog makes the prototype more useful to pilot users (benefits navigators, employers) because they can compare prices for a broader set of common procedures — including high-volume tests like HbA1c, TSH, chest X-rays, and echocardiograms that patients frequently shop for.

## Final Service Catalog

### Imaging (8 services)

| Service | Category | HCPCS Codes | Variants |
|---------|----------|-------------|----------|
| MRI Brain | Imaging | 70551, 70553 | without contrast / with contrast |
| MRI Knee | Imaging | 73721, 73723 | without contrast / with contrast |
| CT Head | Imaging | 70450 | without contrast |
| CT Abdomen & Pelvis | Imaging | 74177, 74178 | with contrast / before+after contrast |
| Chest X-ray | Imaging | 71046 | 2 views |
| Ultrasound Abdomen | Imaging | 76700, 76705 | complete / limited |
| Screening Mammogram | Imaging | 77067 | screening |
| Echocardiogram | Imaging | 93306 | complete with Doppler |

### GI / Outpatient (2 services)

| Service | Category | HCPCS Codes | Variants |
|---------|----------|-------------|----------|
| Colonoscopy | GI/Outpatient | 45378, 45380, 45385 | diagnostic / with biopsy / with polyp removal |
| Upper GI Endoscopy (EGD) | GI/Outpatient | 43235, 43239 | diagnostic / with biopsy |

### Labs (5 services)

| Service | Category | HCPCS Codes | Variants |
|---------|----------|-------------|----------|
| CBC (Complete Blood Count) | Labs | 85025 | single code |
| Lipid Panel | Labs | 80061 | cholesterol & triglycerides |
| CMP (Comprehensive Metabolic Panel) | Labs | 80053 | single code |
| HbA1c (Diabetes Test) | Labs | 83036 | single code |
| TSH (Thyroid Test) | Labs | 84443 | single code |

### Rehab (1 service)

| Service | Category | HCPCS Codes | Variants |
|---------|----------|-------------|----------|
| Physical Therapy Evaluation | Rehab | 97161, 97162 | low complexity / moderate complexity |

**Total:** 16 services, 28 HCPCS codes.

## Synonyms for New Services

The search module uses hardcoded synonym lookup. New entries must include common patient-facing terms:

| Service | Synonyms |
|---------|----------|
| CT Head | "ct head", "head ct", "ct brain", "cat scan head", "head scan" |
| Chest X-ray | "chest xray", "chest x-ray", "x-ray chest", "chest xr", "lung xray" |
| Ultrasound Abdomen | "ultrasound abdomen", "abdominal ultrasound", "belly ultrasound", "abdomen sonogram" |
| Echocardiogram | "echo", "echocardiogram", "heart ultrasound", "heart echo", "cardiac ultrasound" |
| Upper GI Endoscopy (EGD) | "egd", "upper endoscopy", "upper gi", "stomach scope", "esophagus scope", "upper gi scope" |
| CBC | "cbc", "complete blood count", "blood count", "white cell count" |
| Lipid Panel | "lipid panel", "cholesterol test", "cholesterol", "lipid", "triglycerides" |
| CMP | "cmp", "comprehensive metabolic panel", "metabolic panel", "chem 14", "metabolic test" |
| HbA1c | "a1c", "hba1c", "hemoglobin a1c", "diabetes test", "glycated hemoglobin", "sugar test" |
| TSH | "tsh", "thyroid", "thyroid test", "thyroid stimulating hormone", "thyroid panel" |
| Physical Therapy Evaluation | "pt eval", "physical therapy eval", "pt evaluation", "physical therapy evaluation" |

## Changes Required

### 1. `app/search.py`

- Replace the existing `SERVICE_CATALOG` list with 16 entries matching the tables above
- Remove the combined "Blood Work (CBC + Lipid Panel)" entry
- Add CBC and Lipid Panel as separate entries
- Add 9 new service entries (CT Head, Chest X-ray, Ultrasound Abdomen, Echocardiogram, Upper GI Endoscopy, CMP, HbA1c, TSH, Physical Therapy Evaluation)
- Preserve the existing `search_services()` function — no code changes needed

### 2. `tests/test_search.py`

- Rename `test_catalog_has_six_services` → `test_catalog_has_sixteen_services`, update assertion
- Update `test_blood_test_synonym` — "blood test" no longer maps to a single service. Change to verify "cbc" returns the CBC service, or remove the test
- Add new tests:
  - `test_a1c_synonym` — "a1c" → HbA1c
  - `test_thyroid_synonym` — "thyroid" → TSH
  - `test_echo_synonym` — "echo" → Echocardiogram
  - `test_egd_synonym` — "egd" → Upper GI Endoscopy (EGD)
  - `test_chest_xray_synonym` — "chest xray" → Chest X-ray

### 3. `tests/test_build_dataset.py`

- Rename `test_target_hcpcs_has_12_codes` → `test_target_hcpcs_has_28_codes`, update assertion

### 4. Regenerate Data

Run `python3 -m scripts.build_dataset` to rebuild `data/processed/indiana_prices.parquet`. Expected row count: ~10-12k rows (based on provider counts in the data exploration).

### 5. No Changes Required

- `scripts/build_dataset.py` — catalog-driven, will pick up new entries automatically via `SERVICE_CATALOG` import
- `app/data_loader.py` — service-name agnostic
- `app/streamlit_app.py` — service-name agnostic, renders whatever is in the catalog
- `requirements.txt` — no new dependencies

## Testing Strategy

1. **Unit tests:** New synonym tests verify search correctly maps patient-facing terms to new services
2. **Integration test:** Existing `test_build_dataset_end_to_end` will fail if the new HCPCS codes aren't properly consumed by the pipeline — verifies catalog changes flow through correctly
3. **Manual smoke test:** Run the Streamlit app locally, verify:
   - Sidebar shows all 16 services
   - Searching "a1c" finds HbA1c
   - Searching "echo" finds Echocardiogram
   - Each new service shows providers with non-zero statewide stats
   - Caveats footer still appears

## Risks

- **HbA1c volume dominance** — 1,457 providers in Indiana. The default sort by price should still work, but the comparison table may be long. The existing city filter mitigates this.
- **Synonym collisions** — e.g., "scope" was a synonym for Colonoscopy in V1; with EGD added, "scope" could match both. The existing scoring logic returns all ties, which is acceptable behavior.
- **Breaking change for "Blood Work" users** — the old combined service no longer exists. Anyone with a bookmarked link or shared screenshot referencing "Blood Work" would need to find CBC or Lipid Panel separately. Acceptable for a pre-pilot prototype.

## Non-Goals

- No new UI features (the existing UI already supports any catalog size)
- No changes to data sources (still only the Physician dataset)
- No changes to the price fields displayed
- No insurance personalization
- No LLM integration
