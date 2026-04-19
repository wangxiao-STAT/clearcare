# ClearCare Pricing — Healthcare Price Transparency Startup

## Project Vision

Build a healthcare price navigation platform that estimates a realistic pre-care price range, translates billing language into plain English, and helps patients compare options before receiving care.

**Core promise:** "Before you schedule care, we show you a realistic price range, likely cash option, and what questions to ask."

**What this is NOT:** A universal exact-bill predictor. The exact final bill depends on too many unknowns (diagnosis changes, bundled services, insurer contracts, deductibles, out-of-network, coding). The product provides calibrated ranges with explanations.

## Current Status (2026-04-09)

**Prototype V2 is live on Streamlit Cloud.** Delivered in a single-day sprint: V1 shipped, then iteratively expanded with service breadth, ZIP/radius search, plain-English explanations, and UI polish.

- **Repo:** https://github.com/wangxiao-STAT/clearcare (public)
- **Deployed:** Streamlit Cloud (auto-deploys from `main`)
- **Tests:** 36 passing
- **Dataset:** 9,755 rows across 4,515 providers in 217 Indiana cities

### What's Built

| Component | File | Description |
|-----------|------|-------------|
| Service search | `app/search.py` | 16 services, synonym lookup, fuzzy keyword matching |
| Data pipeline | `scripts/build_dataset.py` | Filters 2.9 GB CMS Physician CSV → 9,755 Indiana rows → Parquet |
| ZIP reference data | `scripts/build_zip_data.py` | Downloads US Census ZCTA Gazetteer → Indiana ZIP lat/lon CSV |
| Data loader | `app/data_loader.py` | Query layer with provider filtering, sorting, statewide stats |
| Geo module | `app/geo.py` | ZIP → lat/lon lookup, Haversine distance, radius filtering |
| Explanations | `app/explanations.py` | Loads hand-curated plain-English service explanations |
| Streamlit UI | `app/streamlit_app.py` | Branded header, ZIP search, card-based provider display, explainer expander, caveats |

### Project Structure

```
├── .streamlit/
│   └── config.toml                        # Navy theme (primary #0B3B5F)
├── data/
│   ├── raw/                               # CMS CSVs (gitignored, ~3 GB total)
│   └── processed/
│       ├── indiana_prices.parquet         # Committed, ~500 KB
│       ├── indiana_zips.csv               # Committed, ~30 KB (775 ZIPs)
│       └── service_explanations.json      # Committed, ~50 KB (16 services)
├── scripts/
│   ├── build_dataset.py                   # Physician pricing pipeline
│   └── build_zip_data.py                  # One-time Census Gazetteer download
├── app/
│   ├── streamlit_app.py                   # Main Streamlit UI
│   ├── search.py                          # Service catalog + synonym search
│   ├── data_loader.py                     # Load/cache Parquet, query providers
│   ├── geo.py                             # ZIP/radius + Haversine
│   └── explanations.py                    # Load/query explanation JSON
├── tests/                                 # 36 tests total
│   ├── test_build_dataset.py              # 5 tests
│   ├── test_search.py                     # 14 tests
│   ├── test_data_loader.py                # 4 tests
│   ├── test_geo.py                        # 8 tests
│   └── test_explanations.py               # 5 tests
├── docs/superpowers/
│   ├── specs/                             # Design docs for each feature
│   └── plans/                             # Implementation plans
├── requirements.txt                       # pandas, pyarrow, streamlit, pytest
└── README.md
```

### Key Data Findings

- **Outpatient dataset (APC codes) is too coarse** for procedure-level comparison. APCs are payment groupings like "Level 3 Lower GI Procedures" that bundle multiple procedures.
- **Physician dataset (HCPCS codes) is the primary price source** — maps directly to specific procedures (e.g., 73721 = MRI knee without contrast).
- **Outpatient/Inpatient integration was deliberately dropped** — the published Indiana APCs only cover surgical/procedural services (no imaging, no labs, no PT), which would only add facility-fee context for Colonoscopy and Upper GI Endoscopy. Low value for the work.
- **Charge range: $9 – $11,247** across all services.

## V2 Prototype Scope

### 16 Services (24 HCPCS codes)

**Imaging (8):** MRI Brain, MRI Knee, CT Head, CT Abdomen & Pelvis, Chest X-ray, Ultrasound Abdomen, Screening Mammogram, Echocardiogram

**GI / Outpatient (2):** Colonoscopy, Upper GI Endoscopy (EGD)

**Labs (5):** CBC, Lipid Panel, CMP, HbA1c, TSH

**Rehab (1):** Physical Therapy Evaluation

Row count per service (Indiana): HbA1c (1,457), Physical Therapy Evaluation (1,158), Chest X-ray (1,089), Colonoscopy (915), CT Abdomen & Pelvis (843), Echocardiogram (622), MRI Brain (603), Upper GI Endoscopy (545), Ultrasound Abdomen (489), CT Head (471), Screening Mammogram (380), CBC (286), CMP (232), Lipid Panel (232), MRI Knee (247), TSH (186).

### Features Shipped

1. **Plain-English search** — "knee MRI", "colonoscopy", "a1c", "thyroid", "echo", "egd", "chest xray" all resolve to the right service
2. **Service catalog browsing** — If no search match, all 16 services are listed in the sidebar dropdown
3. **Variant toggle** — MRI/CT show with/without contrast; Colonoscopy shows diagnostic/biopsy/polyp; EGD shows diagnostic/with biopsy
4. **Statewide price summary** — Low (p10), Typical (median), High (p90) of Indiana billed charges for the selected HCPCS
5. **"About this service" expander** — Hand-curated plain-English content with 5 fields: description, typically included, may be billed separately, what to expect, questions to ask before scheduling. Price-transparency focused (anesthesiologist network status, Good Faith Estimates, freestanding vs hospital pricing, self-pay discounts).
6. **ZIP + radius search** — User enters a 5-digit Indiana ZIP and picks a radius (5/10/25/50/100 miles). Providers are filtered and sorted by distance. Invalid/out-of-state ZIPs show clear warnings but fall back to statewide results.
7. **Distance column** — Each provider card shows distance from user's ZIP (e.g., "2.3 mi") when radius filter is active.
8. **Mobile-friendly provider cards** — Replaced the dataframe with stacked bordered containers. Each card shows: provider name, distance chip, city · ZIP, and a 3-column stat row (avg billed, Medicare, patients). Cards auto-stack on mobile.
9. **Top-50 cap** — Large result sets (e.g., HbA1c with 1,457 providers) render the top 50 with a caption telling users to narrow their filters for more.
10. **Sort options** — Distance (default when ZIP active), Price, Medicare allowed, Patient volume
11. **Visual identity** — Inline SVG logo (navy shield with check mark) + "ClearCare" wordmark + tagline, navy theme (#0B3B5F), centered layout, 🏥 browser favicon
12. **Caveats footer** — Yellow warning box on every page with explicit disclaimers (Medicare data basis, separate charges not included, contact provider before scheduling)

### Tech Stack (Prototype)

- **Language:** Python 3.11
- **Data:** Parquet flat file + CSV + JSON (no database)
- **Frontend:** Streamlit (theme via `.streamlit/config.toml`, layout=centered, CSS injection for spacing)
- **Deployment:** Streamlit Cloud (free tier, auto-deploy from `main`)
- **Search:** Hardcoded synonym lookup (no LLM, no Elasticsearch)
- **Geo:** Stdlib-only Haversine distance + Census ZCTA Gazetteer for ZIP coords
- **Explanations:** Hand-curated JSON (no LLM runtime calls, no API keys, no ongoing costs)

### Data Sources in Use

**Medicare Physician & Other Practitioners by Provider & Service (2023)** — primary price source. Key fields:

| Field | Meaning | User-Facing Label |
|-------|---------|-------------------|
| `Avg_Sbmtd_Chrg` | Average amount billed by provider | "avg billed" — closest proxy for cash/self-pay |
| `Avg_Mdcr_Alowd_Amt` | Medicare-approved amount | "Medicare" — benchmark reference |
| `Tot_Benes` | Number of Medicare beneficiaries | "patients" — volume indicator |

**US Census 2020 ZCTA Gazetteer** — ZIP → lat/lon for radius search. Downloaded once via `scripts/build_zip_data.py`, committed as `indiana_zips.csv`.

### Explicit Non-Goals (V2)

- Insurance/deductible personalization
- User accounts or feedback collection
- Hospital MRF file parsing
- Outpatient (APC) or Inpatient (DRG) dataset integration (dropped after scope review)
- Episode bundling or component cost breakdown
- Runtime LLM calls (explanations are hand-curated static content)
- Map visualization
- Drive-time distance (straight-line Haversine only)
- Out-of-state providers
- Pagination beyond the 50-card cap

## Product Stages

1. **Price transparency search engine** — compare providers and prices for common shoppable procedures ← **V2 DONE**
2. **Personalized estimator** — incorporates insurance status, deductibles, provider network info
3. **Navigation assistant** — pre-visit questions, Good Faith Estimates, surprise billing flags

## Initial Wedge

- **Geography:** Indiana
- **User type:** Self-pay / uninsured patients first, insured later
- **Services:** ~20 shoppable outpatient services (16 live in V2)
- **Business model:** B2B2C — employers, benefits navigators, health-navigation platforms
- **Pilot audience:** Benefits navigators, employers, health-navigation platforms

## Next Steps

1. **Pilot outreach** — Share the deployed URL with benefits navigators and employers; gather feedback
2. **Insurance personalization** — Accept insurance carrier + plan; filter to in-network providers
3. **Hospital MRF parsing** — Pull actual cash prices from individual Indiana hospital transparency files
4. **Feedback endpoint** — `POST /feedback` for user corrections to drive future improvements
5. **FastAPI backend + PostgreSQL** — When prototype saturates, migrate to production architecture from the original CLAUDE.md plan
6. **Additional services** — Round out to the full ~20 target services (labs, urgent care, etc.)
7. **Clinician review of explanation content** — Hand-curated explanations should be validated by a clinician or billing expert before wider distribution

## Future Tech Stack (Post-Prototype)

- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **API:** FastAPI
- **Search:** PostgreSQL full-text first, Elasticsearch later
- **Frontend:** React
- **LLM:** Only for explanation and plain-language query mapping — never as source of truth for prices

## Data Sources

### Priority 1 — Downloaded (in `data/raw/`, gitignored)

| Dataset | File | Size | Use |
|---------|------|------|-----|
| Hospital General Information | `Hospital_General_Information.csv` | 1.4 MB | Indiana hospital list, addresses, star ratings (not used in V2) |
| Medicare Outpatient by Provider & Service (2023) | `MUP_OUT_RY25_Prov_Svc.csv` | 27 MB | APC pricing (dropped — too coarse) |
| Medicare Physician by Provider & Service (2023) | `MUP_PHY_R25_Prov_Svc.csv` | 2.9 GB | **Primary data source** — provider-level pricing by HCPCS code |
| Medicare Inpatient by Provider & Service (2023) | `MUP_INP_RY25_PrvSvc.csv` | 36 MB | DRG pricing (not used in V2) |

### Priority 2 — Enrich Later

| Dataset | Source | Notes |
|---------|--------|-------|
| Medicare Spending by Claim | CMS Provider Data Catalog | Episode-level cost benchmarks |
| DoltHub hospital-price-transparency | `dolthub/hospital-price-transparency` | Aggregated parsed hospital MRF files, SQL-queryable |
| Individual hospital MRF files | Hospital websites | IU Health, Franciscan, Community Health, Ascension St. Vincent, Parkview |

### Not Available

- **Indiana does NOT have a mandatory statewide APCD** (All-Payer Claims Database)
- Turquoise Health has parsed MRF data but requires paid subscription for bulk access

## Key Join Fields

- `Facility ID` / `Rndrng_Prvdr_CCN` — links Hospital General Info to inpatient/outpatient datasets
- `Rndrng_Prvdr_State_Abrvtn = "IN"` — filter all CMS datasets to Indiana
- `HCPCS_Cd` — procedure code for physician/outpatient services
- `DRG_Cd` — diagnosis group for inpatient stays
- `APC_Cd` — ambulatory payment classification for outpatient hospital services

## Key Risks

1. **File inconsistency** — different formats, weird hospital naming, payer name chaos, raw descriptions that don't cleanly map
2. **Episode bundling** — a single service (e.g., colonoscopy) may involve separate facility, physician, pathology, lab, anesthesia charges. Partially mitigated in V2 by the "May be billed separately" section of each service explanation.
3. **Liability** — must clearly label outputs as estimates with caveats; HIPAA-grade handling if storing identifiable health data later. Caveats footer and per-service caveats are present in V2.
4. **Medical content accuracy** — Hand-curated explanations reflect common knowledge but have not been clinician-reviewed. Future iteration should add expert review.

## Regulatory Context

- CMS hospital price transparency rules enforced as of April 1, 2026
- Hospitals must publish machine-readable files + consumer-friendly shoppable-service displays
- No Surprises Act: Good Faith Estimate framework for uninsured/self-pay
- HL7 Da Vinci Patient Cost Transparency standards building toward structured GFE/AEOB exchanges

## Design & Plan Docs

Each feature has a matching spec + plan pair in `docs/superpowers/`:

### V1 — Initial prototype

- `specs/2026-04-09-prototype-price-comparison-design.md`
- `plans/2026-04-09-prototype-price-comparison.md`

### Expand catalog to 16 services

- `specs/2026-04-09-expand-to-16-services-design.md`
- `plans/2026-04-09-expand-to-16-services.md`

### ZIP / radius search

- `specs/2026-04-09-zip-radius-search-design.md`
- `plans/2026-04-09-zip-radius-search.md`

### Plain-English explanation layer

- `specs/2026-04-09-llm-explanation-layer-design.md` (pivoted to hand-curated, no LLM runtime)
- `plans/2026-04-09-explanation-layer.md`

### UI polish (theme, logo, cards)

- `specs/2026-04-09-ui-polish-design.md`
- `plans/2026-04-09-ui-polish.md`

### Original idea

- `idea_ChatGPT.pdf` — 31-page ChatGPT conversation that seeded the project

## Lessons Learned This Session

- **Scope discipline matters.** Trying to tackle four features (datasets + ZIP + LLM + polish) in one plan would have bogged down. Decomposing into independent spec → plan → implementation cycles kept each piece shippable.
- **Data reality can kill a feature.** The "add outpatient/inpatient datasets" sub-project looked valuable on paper but only covered 2 of 16 services after data exploration. Dropping it was the right call.
- **Hand-curated beats LLM runtime for static content.** The explanation layer started as a Claude API call per service but pivoted to hand-written JSON after the cost/complexity tradeoff was discussed. Zero runtime cost, zero latency, same user value.
- **Streamlit quirks:** (1) Markdown with indented lines becomes a code block and will chop up inline SVG. Put SVG on a single line. (2) `.block-container` default top padding (~6rem) exists to clear Streamlit's fixed header bar — don't reduce it aggressively or the header overlaps your content. 4rem is safe, 1.5rem is not.
- **Subagent-driven execution works well** when the plan has complete code for every step. Subagents occasionally introduce unwanted changes (e.g., an SSL verification bypass in one task), so reviewing each task's commit briefly is worth the overhead.
