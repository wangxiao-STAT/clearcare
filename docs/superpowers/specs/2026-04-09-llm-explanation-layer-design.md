# Service Explanation Layer

## Overview

Add plain-English explanations for each of the 16 services in the ClearCare prototype. Explanations are **hand-curated** as a static JSON file committed to the repo. The Streamlit app reads the JSON at runtime and shows explanations in an expandable "About this service" section below the price stats bar. No runtime LLM calls, no API keys, no cost, zero latency.

**Note on naming:** The project name "LLM explanation layer" was the original idea, but after weighing API costs we chose to hand-author the content. The file and module names use "explanations" without "llm" to reflect this.

## Motivation

CLAUDE.md promises to "translate billing language into plain English" and help patients "know what questions to ask." Right now, users see a service name and a price table but have no context about what the procedure involves, what's in the base price, what might appear as a surprise line item on their bill, or what to ask before scheduling. The explanation layer closes this gap using curated, editorial content.

## User Experience

When a user selects a service (e.g., "Colonoscopy"), they see:

1. Service title + category caption (existing)
2. Statewide Low / Typical / High price metrics (existing)
3. **NEW:** Collapsed expander labeled "About this service"
4. Divider (existing)
5. Provider comparison table (existing)
6. Caveats footer (existing)

Clicking the expander reveals 5 sections:

- **What it is** — 2-3 sentences, 8th-grade reading level
- **Typically included** — 3-5 bullets
- **May be billed separately** — 3-5 bullets (anesthesia, pathology, facility fees, etc.)
- **What to expect** — 2-3 sentences on prep, duration, recovery
- **Questions to ask before scheduling** — 3-5 specific, price-transparency-focused questions

If the JSON file is missing or the service has no entry, the expander is silently omitted. The app still works without explanations.

## Architecture

Two components with clear boundaries:

1. **`data/processed/service_explanations.json`** — Hand-curated JSON file committed to the repo. The single source of truth for explanation content. Shape: `{service_name: {description, typically_included, billed_separately, what_to_expect, questions_to_ask}}`.
2. **`app/explanations.py`** — Runtime module. Pure loader and getter functions. No LLM calls, no network.

The UI layer (`app/streamlit_app.py`) wires the runtime module into a cached loader and renders the expander.

## Content

The JSON file contains one entry per service with 5 fields:

```json
{
  "MRI Knee": {
    "description": "An MRI scan of the knee takes detailed pictures of the bones, cartilage, ligaments, and tendons in your knee joint using a strong magnet. Doctors often order this to find the cause of knee pain, swelling, or an injury that didn't show up well on an X-ray.",
    "typically_included": [
      "Use of the MRI scanner for the scheduled time",
      "The scan images themselves",
      "A radiologist reading the scan and writing a report"
    ],
    "billed_separately": [
      "Facility fee if the scan is done at a hospital outpatient center",
      "Contrast dye if your doctor orders the scan 'with contrast'",
      "The referring physician's office visit (separate from the scan)"
    ],
    "what_to_expect": "You'll lie still on a table that slides into the scanner for about 30-45 minutes. No prep needed for most knee MRIs, but you'll need to remove any metal (jewelry, belts). Some people find the noise loud — ask for earplugs.",
    "questions_to_ask": [
      "Is this billed as a hospital outpatient procedure or at a freestanding imaging center? Freestanding centers are usually cheaper.",
      "Will there be a separate facility fee, and how much is it?",
      "Do I need contrast dye? If yes, what does that add to the cost?",
      "Is the radiologist who reads my scan in my insurance network?",
      "Can I get a Good Faith Estimate in writing before scheduling?"
    ]
  },
  "...": "..."
}
```

All 16 services will have entries following this structure. Content is drafted to be:

- **Patient-friendly** — 8th-grade reading level, no medical jargon
- **Practical** — focused on things patients can actually act on
- **Honest about uncertainty** — "Ask your provider whether..." framing
- **Price-transparency focused** — the "questions to ask" always include at least one question about separate fees or Good Faith Estimates
- **Not medical advice** — descriptions explain procedures without recommending them

## Runtime Module

`app/explanations.py`:

```python
"""Load and query pre-generated service explanations."""

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent / "data" / "processed" / "service_explanations.json"

REQUIRED_FIELDS = [
    "description",
    "typically_included",
    "billed_separately",
    "what_to_expect",
    "questions_to_ask",
]


def load_explanations(path: str | None = None) -> dict[str, dict]:
    """Load service explanations from JSON.

    Returns a dict mapping service_name to an explanation dict.
    Raises FileNotFoundError if the file is missing (fail loudly).
    """
    p = Path(path) if path else DEFAULT_PATH
    with p.open() as f:
        return json.load(f)


def get_explanation(explanations: dict, service_name: str) -> dict | None:
    """Return the explanation for a service, or None if not found."""
    return explanations.get(service_name)
```

**Design choices:**

- `load_explanations` raises on missing file instead of returning `{}` — the Streamlit layer catches this and gracefully hides the expander, but silent failures elsewhere would be bugs.
- `get_explanation` returns `None` (not raise) for missing services — allows the UI to simply skip rendering.
- No validation of field contents at load time. Validation happens in the test suite when the JSON is updated.

## UI Integration

### New cached helper

In `app/streamlit_app.py`, below the existing `cached_zip_coords`:

```python
@st.cache_data
def cached_explanations():
    try:
        return load_explanations()
    except FileNotFoundError:
        return {}
```

### Imports

Add to the import block in `streamlit_app.py`:

```python
from app.explanations import load_explanations, get_explanation
```

### Expander rendering

In `main()`, after this existing block:

```python
    # Statewide summary
    stats = get_statewide_stats(df, selected_hcpcs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Low (10th percentile)", f"${stats['charge_p10']:,.0f}")
    col2.metric("Typical (median)", f"${stats['charge_median']:,.0f}")
    col3.metric("High (90th percentile)", f"${stats['charge_p90']:,.0f}")
    st.caption("Statewide billed charges — Indiana providers, Medicare data 2023")
```

Insert the new expander block BEFORE `st.divider()`:

```python
    explanations = cached_explanations()
    explanation = get_explanation(explanations, selected_name)
    if explanation:
        with st.expander("About this service"):
            st.markdown("**What it is**")
            st.markdown(explanation["description"])

            st.markdown("**Typically included**")
            for item in explanation["typically_included"]:
                st.markdown(f"- {item}")

            st.markdown("**May be billed separately**")
            for item in explanation["billed_separately"]:
                st.markdown(f"- {item}")

            st.markdown("**What to expect**")
            st.markdown(explanation["what_to_expect"])

            st.markdown("**Questions to ask before scheduling**")
            for q in explanation["questions_to_ask"]:
                st.markdown(f"- {q}")
```

## Testing Strategy

### Unit tests (`tests/test_explanations.py`, 5 tests)

1. **`test_load_explanations_returns_dict`** — Create a temp JSON file with a minimal valid structure. `load_explanations(path)` returns a dict with the expected keys.

2. **`test_load_explanations_missing_file_raises`** — Call `load_explanations("/nonexistent/path.json")`. Expect `FileNotFoundError`.

3. **`test_get_explanation_found`** — Build an in-memory dict, call `get_explanation(d, "MRI Knee")`, verify correct entry returned.

4. **`test_get_explanation_not_found`** — Same dict, call with "Unknown Service", expect `None`.

5. **`test_committed_json_has_all_services_with_required_fields`** — Load the real `data/processed/service_explanations.json`. For every service in `SERVICE_CATALOG`, assert the entry exists and has all 5 required fields with the right types (strings for description/what_to_expect, lists of strings for the other three).

### Manual smoke test

1. Load the Streamlit app
2. Select "MRI Knee" → expander visible, labeled "About this service"
3. Click to expand → 5 sections render (what it is, typically included, billed separately, what to expect, questions to ask)
4. Content reads naturally, no JSON leakage, no medical jargon
5. Switch to "HbA1c (Diabetes Test)" → different explanation appears
6. Switch through all 16 services → each has an expander with distinct content
7. Close expander → clean collapse
8. Rest of page (stats, providers table, caveats) works unchanged

## File Changes Summary

| File | Action | Responsibility |
|---|---|---|
| `data/processed/service_explanations.json` | Create (committed) | 16 hand-curated entries |
| `app/explanations.py` | Create | Load and query explanations |
| `tests/test_explanations.py` | Create | 5 tests |
| `app/streamlit_app.py` | Modify | Add cached load + expander section |
| `requirements.txt` | No change | No new runtime deps |
| `app/search.py` | No change | |
| `app/data_loader.py` | No change | |
| `app/geo.py` | No change | |

**No new dependencies. No API keys. No scripts to run.** Just a JSON file, a runtime module, and a UI tweak.

## Risks

- **Content becomes stale if medical practice or billing norms change** — This is a prototype; acceptable. Update by editing the JSON file directly.
- **Accuracy concerns for patient safety** — Content is educational, not prescriptive. All entries avoid medical advice, frame recommendations as questions to verify with providers, and the caveats footer reinforces that users should confirm details with their provider.
- **Hand-written content is only as good as the writer** — The author (me, Claude) will use publicly known information about each procedure and focus on common sense price-transparency questions. A future iteration could have the content reviewed by a clinician or billing expert.

## Non-Goals

- No runtime LLM calls
- No personalization (same explanation for every user)
- No multi-language support
- No streaming or progressive display
- No variant-level explanations (one explanation per service covers all variants — e.g., colonoscopy explanation covers diagnostic, biopsy, and polyp removal)
- No explanation versioning or A/B testing
- No integration with the /feedback endpoint from CLAUDE.md (future work)
- No ANTHROPIC_API_KEY or generation script — content is hand-authored
