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
