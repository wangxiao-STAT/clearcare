"""ClearCare Prototype — Indiana Healthcare Price Comparison."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from app.data_loader import load_data, get_providers_for_service, get_statewide_stats
from app.search import search_services, SERVICE_CATALOG
from app.geo import load_zip_coords, filter_by_radius

st.set_page_config(page_title="ClearCare — Compare Healthcare Prices", layout="wide")


@st.cache_data
def cached_load():
    return load_data()


@st.cache_data
def cached_zip_coords():
    return load_zip_coords()


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

    # Location: ZIP + radius
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
    providers = get_providers_for_service(df, selected_name, hcpcs_code=selected_hcpcs, sort_by=sort_col)

    # Apply radius filter if user entered a ZIP
    zip_coords = cached_zip_coords()
    warning_message = None
    radius_applied = False

    if user_zip:
        if not user_zip.isdigit() or len(user_zip) != 5:
            warning_message = "Please enter a valid 5-digit ZIP code."
        elif user_zip not in zip_coords:
            warning_message = "This prototype covers Indiana only. Please enter an Indiana ZIP code."
        else:
            providers = filter_by_radius(providers, user_zip, radius_miles, zip_coords)
            radius_applied = True
            if providers.empty:
                warning_message = (
                    f"No providers found within {radius_miles} miles of {user_zip}. "
                    "Try expanding the radius."
                )

    if warning_message:
        st.warning(warning_message)

    if sort_col == "Tot_Benes":
        providers = providers.sort_values(sort_col, ascending=False).reset_index(drop=True)

    if providers.empty:
        if not warning_message:
            st.warning("No providers found for this selection.")
    else:
        if radius_applied:
            st.subheader(f"{len(providers)} providers within {radius_miles} miles of {user_zip}")
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
        st.dataframe(display_df, width="stretch", hide_index=True)

    # Caveats
    st.divider()
    st.warning(
        "**Important:**\n"
        "- Prices shown are based on Medicare billing data (2023). Actual cash or self-pay prices may differ.\n"
        "- Estimates do not include separate charges for anesthesia, pathology, facility fees, or additional services.\n"
        "- This tool provides estimates only — contact the provider for a quote before scheduling."
    )


if __name__ == "__main__":
    main()
