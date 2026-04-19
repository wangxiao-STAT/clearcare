# ClearCare Prototype: Price Comparison Search Engine

## Overview

A Streamlit-based price comparison app for ~6 shoppable healthcare services in Indiana, powered by CMS Medicare public data, deployed to Streamlit Cloud for early pilot users (benefits navigators, employers).

**Core user flow:** User searches for a procedure in plain English, sees a ranked list of Indiana providers with prices and statewide context.

**Approach:** Flat-file Streamlit. Pre-process CMS CSVs into a single clean Parquet file. Streamlit reads this file directly — no database, no backend server.

## Audience

Early pilot users: benefits navigators, employers, and health-navigation platforms. The app must be intuitive and clearly communicate that prices are estimates with caveats.

## Data Pipeline

### Input Datasets

| Dataset | File | Size | Use |
|---------|------|------|-----|
| Medicare Physician & Other Practitioners by Provider & Service (2023) | `MUP_PHY_R25_Prov_Svc.csv` | 2.9 GB | Provider-level pricing by HCPCS code — primary price source |
| Hospital General Information | `Hospital_General_Information.csv` | 1.4 MB | Indiana hospital addresses, star ratings |

The Outpatient dataset (`MUP_OUT_RY25_Prov_Svc.csv`) uses APC payment groupings too coarse for procedure-level comparison. The Physician dataset has HCPCS procedure codes that map directly to our target services.

### Processing Steps

1. Filter Physician dataset to `Rndrng_Prvdr_State_Abrvtn == "IN"` and HCPCS codes in the target set (see Service Mapping below)
2. Map each HCPCS code to a plain-English service name and category
3. Join with Hospital General Info on ZIP / provider name for address enrichment and star ratings where available
4. Compute per-service statewide statistics: p10, median (p50), p90 of `Avg_Sbmtd_Chrg` and `Avg_Mdcr_Alowd_Amt`
5. Output a single clean Parquet file to `data/processed/indiana_prices.parquet`

### Key Price Fields

| Field | Meaning | User-Facing Label |
|-------|---------|-------------------|
| `Avg_Sbmtd_Chrg` | Average amount billed by provider | "Avg Billed Charge" — closest proxy for cash/self-pay price |
| `Avg_Mdcr_Alowd_Amt` | Medicare-approved amount | "Medicare Benchmark" — reference for fair pricing |
| `Tot_Benes` | Number of Medicare beneficiaries served | "# Medicare Patients" — volume/experience indicator |

### Data Volume

Filtering to Indiana + 12 target HCPCS codes yields ~3,500 rows across ~1,493 unique providers. The processed Parquet file will be a few hundred KB.

## Service Mapping

6 services mapped to 12 HCPCS codes, with a hardcoded synonym lookup for plain-English search:

| Service Name | Category | HCPCS Codes | Variants |
|---|---|---|---|
| MRI Brain | Imaging | 70551, 70553 | Without contrast, with contrast |
| MRI Knee | Imaging | 73721, 73723 | Without contrast, with contrast |
| CT Abdomen & Pelvis | Imaging | 74177, 74178 | With contrast, before+after contrast |
| Screening Mammogram | Imaging | 77067 | Single code |
| Colonoscopy | GI/Outpatient | 45378, 45380, 45385 | Diagnostic, biopsy, polyp removal |
| Blood Work (CBC + Lipid Panel) | Labs | 85025, 80061 | Grouped as common lab bundle |

### Search Matching

- Hardcoded lookup table mapping service names + common synonyms to HCPCS groups
- Examples: "knee scan" -> MRI Knee, "scope" -> Colonoscopy, "blood test" -> Blood Work
- Fuzzy keyword matching against synonym list — no LLM needed for 6 services
- If no match found, display all available services for the user to pick from

## UI Design

### Streamlit Layout

**Sidebar:**
- Service search/selection
- Contrast variant toggle (for MRI and CT)
- Sort by: price (default), volume, city
- City filter (dropdown of Indiana cities with providers)

**Main area:**

1. **Landing state:** Search box with tagline: "Compare healthcare prices across Indiana providers"
2. **After service selection:**
   - **Statewide summary bar:** "For MRI Knee in Indiana: Low $180 | Typical $320 | High $580" (p10/median/p90 of billed charges)
   - **Provider comparison table** sorted by price (low to high):
     - Provider Name
     - City
     - ZIP
     - Avg Billed Charge
     - Medicare Allowed Amount
     - # Medicare Patients
     - Statewide context indicator (where this provider falls vs. p10/median/p90)
3. **Caveats footer** (persistent on every results page):
   - "Prices shown are based on Medicare billing data (2023). Actual cash or self-pay prices may differ."
   - "Estimates do not include separate charges for anesthesia, pathology, facility fees, or additional services."
   - "This tool provides estimates only — contact the provider for a quote before scheduling."

## Project Structure

```
├── data/
│   ├── raw/                  # Downloaded CMS CSVs (gitignored)
│   └── processed/            # Clean Parquet file (committed, small)
├── scripts/
│   └── build_dataset.py      # Pipeline: filter, map, join, output Parquet
├── app/
│   ├── streamlit_app.py      # Main Streamlit app
│   ├── search.py             # Service name matching / synonym lookup
│   └── data_loader.py        # Load and cache Parquet data
├── requirements.txt          # pandas, pyarrow, streamlit
├── .gitignore                # data/raw/, .superpowers/
└── README.md                 # Setup + deployment instructions
```

## Deployment

- **Platform:** Streamlit Cloud (free tier)
- **Repo:** Push to GitHub, connect Streamlit Cloud
- **Data:** Processed Parquet file committed to repo (~few hundred KB)
- **Data refresh:** Re-run `build_dataset.py` when CMS publishes updates, commit new Parquet

## Explicit Non-Goals

These are future enhancements, not part of this prototype:

- ZIP code radius search (prototype shows all Indiana, filterable by city)
- Insurance or deductible personalization
- LLM-powered explanation layer
- User accounts or feedback collection
- Hospital MRF file parsing
- Outpatient (APC) or Inpatient (DRG) dataset integration
- Episode bundling or component cost breakdown
