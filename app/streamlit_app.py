"""ClearCare Prototype — Indiana Healthcare Price Comparison."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from app.data_loader import load_data, get_providers_for_service, get_statewide_stats
from app.search import search_services, SERVICE_CATALOG
from app.geo import load_zip_coords, filter_by_radius
from app.explanations import load_explanations, get_explanation

st.set_page_config(
    page_title="ClearCare — Compare Healthcare Prices",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="auto",
)


@st.cache_data
def cached_load():
    return load_data()


@st.cache_data
def cached_zip_coords():
    return load_zip_coords()


@st.cache_data
def cached_explanations():
    try:
        return load_explanations()
    except FileNotFoundError:
        return {}


def format_provider_name(row: pd.Series) -> str:
    """Format provider name from last/first or org name."""
    if row["Rndrng_Prvdr_Ent_Cd"] == "I":
        first = row.get("Rndrng_Prvdr_First_Name", "")
        last = row.get("Rndrng_Prvdr_Last_Org_Name", "")
        return f"{first} {last}".strip() if first else last
    return row.get("Rndrng_Prvdr_Last_Org_Name", "Unknown")


def main():
    st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

    # Branded header with inline SVG logo
    _logo_svg = (
        '<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" '
        'style="flex-shrink:0;display:block" aria-label="ClearCare logo">'
        '<path d="M22 2 L40 9 L40 22 Q40 33 22 42 Q4 33 4 22 L4 9 Z" '
        'fill="#0B3B5F" stroke="#0B3B5F" stroke-width="1" stroke-linejoin="round"/>'
        '<path d="M13 21 L19 27 L31 15" fill="none" stroke="#FFFFFF" '
        'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;padding-bottom:0.75rem;">'
        f'{_logo_svg}'
        f'<div>'
        f'<div style="font-size:28px;font-weight:700;color:#0B3B5F;line-height:1.1;letter-spacing:-0.01em;">ClearCare</div>'
        f'<div style="font-size:14px;color:#6b7280;line-height:1.2;">Compare healthcare prices in Indiana</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    df = cached_load()

    # --- Sidebar ---
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
        "Distance (nearest first)": "distance_miles",
        "Price (low to high)": "Avg_Sbmtd_Chrg",
        "Medicare allowed (low to high)": "Avg_Mdcr_Alowd_Amt",
        "Patient volume (high to low)": "Tot_Benes",
    }
    # Default sort: Distance when ZIP is valid and in the coords table, else Price
    _zip_coords_for_default = cached_zip_coords()
    if user_zip and user_zip.isdigit() and len(user_zip) == 5 and user_zip in _zip_coords_for_default:
        default_sort_index = 0  # Distance
    else:
        default_sort_index = 1  # Price
    sort_label = st.sidebar.selectbox(
        "Sort by",
        list(sort_options.keys()),
        index=default_sort_index,
    )
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

    # About this service (from pre-generated explanations)
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

    st.divider()

    # Provider table
    # If user selected Distance sort but no ZIP, fall back to Price for the initial query
    effective_sort_col = sort_col if sort_col != "distance_miles" else "Avg_Sbmtd_Chrg"
    providers = get_providers_for_service(df, selected_name, hcpcs_code=selected_hcpcs, sort_by=effective_sort_col)

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
            elif sort_col != "distance_miles":
                # User explicitly chose a non-distance sort
                ascending = sort_col != "Tot_Benes"
                providers = providers.sort_values(sort_col, ascending=ascending).reset_index(drop=True)

    if warning_message:
        st.warning(warning_message)

    # Non-ZIP: handle Tot_Benes descending; Price/Medicare already handled by get_providers_for_service;
    # distance_miles fallback to Price already handled by effective_sort_col
    if not radius_applied and not warning_message:
        if sort_col == "Tot_Benes":
            providers = providers.sort_values("Tot_Benes", ascending=False).reset_index(drop=True)

    if providers.empty:
        if not warning_message:
            st.warning("No providers found for this selection.")
    else:
        if radius_applied:
            st.subheader(f"{len(providers)} providers within {radius_miles} miles of {user_zip}")
        else:
            st.subheader(f"{len(providers)} providers found")

        display = providers.head(50)
        has_distance = "distance_miles" in display.columns
        for _, row in display.iterrows():
            with st.container(border=True):
                top_cols = st.columns([4, 1])
                top_cols[0].markdown(f"**{format_provider_name(row)}**")
                if has_distance and pd.notna(row.get("distance_miles")):
                    top_cols[1].markdown(
                        f"<div style='text-align:right;color:#0B3B5F;font-weight:600'>{row['distance_miles']:.1f} mi</div>",
                        unsafe_allow_html=True,
                    )
                st.caption(f"{row['Rndrng_Prvdr_City']} · {row['Rndrng_Prvdr_Zip5']}")

                bottom_cols = st.columns([2, 2, 2])
                bottom_cols[0].markdown(
                    f"**${row['Avg_Sbmtd_Chrg']:,.0f}**  \n"
                    f"<span style='font-size:0.75rem;color:#6b7280'>avg billed</span>",
                    unsafe_allow_html=True,
                )
                bottom_cols[1].markdown(
                    f"${row['Avg_Mdcr_Alowd_Amt']:,.0f}  \n"
                    f"<span style='font-size:0.75rem;color:#6b7280'>Medicare</span>",
                    unsafe_allow_html=True,
                )
                patient_count = f"{int(row['Tot_Benes']):,}" if pd.notna(row['Tot_Benes']) else "N/A"
                bottom_cols[2].markdown(
                    f"{patient_count}  \n"
                    f"<span style='font-size:0.75rem;color:#6b7280'>patients</span>",
                    unsafe_allow_html=True,
                )

        if len(providers) > 50:
            st.caption(
                f"Showing top 50 of {len(providers)} providers. "
                "Narrow your ZIP radius or change sort order to see others."
            )

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
