# Landing Page + Mobile Nav Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a landing page with logo/description/Get Started button, and move all sidebar inputs into the main area so mobile users can discover search without hunting for a hidden sidebar arrow.

**Architecture:** Split `main()` into `render_landing()` + `render_search(df)` dispatched by a simple `st.session_state.view` router. All inputs (search, service, variant, ZIP, radius, sort) move from the sidebar into the main area. ZIP/radius/sort go inside a collapsed `st.expander("Filters")`. Sidebar is disabled via `initial_sidebar_state="collapsed"`.

**Tech Stack:** Streamlit session state, no new dependencies, no new tests.

---

## File Structure

Only one file changes:

| File | Action | What |
|------|--------|------|
| `app/streamlit_app.py` | Rewrite `main()` body | Split into landing + search; move sidebar controls to main area; add Filters expander; set sidebar collapsed |

No new files, no deletions, no dependency changes, no test changes.

---

### Task 1: Full Rewrite of `app/streamlit_app.py`

This task replaces the entire `main()` body with the new landing + search structure. The imports, `st.set_page_config`, cached helpers, and `format_provider_name` all stay the same.

**Files:**
- Modify: `app/streamlit_app.py`

- [ ] **Step 1: Change the sidebar state in `st.set_page_config`**

Open `app/streamlit_app.py`. Find this block:

```python
st.set_page_config(
    page_title="ClearCare — Compare Healthcare Prices",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="auto",
)
```

Replace it with:

```python
st.set_page_config(
    page_title="ClearCare — Compare Healthcare Prices",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)
```

- [ ] **Step 2: Add two helper constants at module level**

Right below the existing `format_provider_name` function (around line 47) and BEFORE `def main():`, add these two module-level constants:

```python
LOGO_SVG_LARGE = (
    '<svg width="80" height="80" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" '
    'style="flex-shrink:0;display:block" aria-label="ClearCare logo">'
    '<path d="M22 2 L40 9 L40 22 Q40 33 22 42 Q4 33 4 22 L4 9 Z" '
    'fill="#0B3B5F" stroke="#0B3B5F" stroke-width="1" stroke-linejoin="round"/>'
    '<path d="M13 21 L19 27 L31 15" fill="none" stroke="#FFFFFF" '
    'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

LOGO_SVG_SMALL = (
    '<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" '
    'style="flex-shrink:0;display:block" aria-label="ClearCare logo">'
    '<path d="M22 2 L40 9 L40 22 Q40 33 22 42 Q4 33 4 22 L4 9 Z" '
    'fill="#0B3B5F" stroke="#0B3B5F" stroke-width="1" stroke-linejoin="round"/>'
    '<path d="M13 21 L19 27 L31 15" fill="none" stroke="#FFFFFF" '
    'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)


def _inject_css():
    st.markdown("""
<style>
.block-container { padding-top: 4rem; padding-bottom: 2rem; }
[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)
```

- [ ] **Step 3: Add the `render_landing` function**

Immediately after `_inject_css` and BEFORE `def main():`, add the landing page function:

```python
def render_landing():
    _inject_css()

    # Large logo + wordmark + tagline (centered visually by layout="centered")
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:18px;padding-top:1rem;padding-bottom:1rem;">'
        f'{LOGO_SVG_LARGE}'
        f'<div>'
        f'<div style="font-size:40px;font-weight:700;color:#0B3B5F;line-height:1.1;letter-spacing:-0.01em;">ClearCare</div>'
        f'<div style="font-size:16px;color:#6b7280;line-height:1.3;">Compare healthcare prices in Indiana</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "ClearCare helps patients and benefits navigators find and compare prices for "
        "common healthcare services across Indiana providers. We show you a realistic "
        "price range, what's typically included, and what questions to ask before "
        "scheduling care."
    )

    st.markdown("**What you'll find here:**")
    st.markdown("- 16 shoppable services (MRI, CT, colonoscopy, labs, and more)")
    st.markdown("- Real Indiana provider data from Medicare 2023")
    st.markdown("- Plain-English explanations of what's included and what may be billed separately")
    st.markdown("- ZIP code search to find providers near you")

    st.markdown(
        "<div style='color:#6b7280;font-size:0.85rem;padding-top:0.5rem;padding-bottom:0.5rem;'>"
        "This is an early prototype built for pilot feedback. Prices shown are estimates "
        "based on Medicare data; actual cash or self-pay prices may differ."
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button("Get Started →", type="primary", use_container_width=True):
        st.session_state.view = "search"
        st.rerun()

    st.divider()
    st.warning(
        "**Important:**\n"
        "- Prices shown are based on Medicare billing data (2023). Actual cash or self-pay prices may differ.\n"
        "- Estimates do not include separate charges for anesthesia, pathology, facility fees, or additional services.\n"
        "- This tool provides estimates only — contact the provider for a quote before scheduling."
    )
```

- [ ] **Step 4: Add the `render_search` function**

Immediately after `render_landing` and BEFORE `def main():`, add the search page function. This is the current search body restructured so all inputs live in the main area:

```python
def render_search(df):
    _inject_css()

    # Compact branded header
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;padding-bottom:0.75rem;">'
        f'{LOGO_SVG_SMALL}'
        f'<div>'
        f'<div style="font-size:28px;font-weight:700;color:#0B3B5F;line-height:1.1;letter-spacing:-0.01em;">ClearCare</div>'
        f'<div style="font-size:14px;color:#6b7280;line-height:1.2;">Compare healthcare prices in Indiana</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

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
    selected_service = next(s for s in SERVICE_CATALOG if s["name"] == selected_name)

    # Variant selection (HCPCS code)
    variant_options = {
        f"{code} — {selected_service['variants'][code]}": code
        for code in selected_service["hcpcs_codes"]
    }
    if len(variant_options) > 1:
        variant_label = st.radio("Variant", list(variant_options.keys()), horizontal=True)
        selected_hcpcs = variant_options[variant_label]
    else:
        selected_hcpcs = selected_service["hcpcs_codes"][0]

    # Filters expander (ZIP, radius, sort)
    with st.expander("Filters", expanded=False):
        user_zip = st.text_input(
            "Your ZIP code",
            max_chars=5,
            placeholder="e.g. 46202",
            key="filter_zip",
        )
        radius_miles = st.selectbox(
            "Radius",
            options=[5, 10, 25, 50, 100],
            index=2,  # default 25 miles
            format_func=lambda m: f"{m} miles",
            key="filter_radius",
        )
        sort_options = {
            "Distance (nearest first)": "distance_miles",
            "Price (low to high)": "Avg_Sbmtd_Chrg",
            "Medicare allowed (low to high)": "Avg_Mdcr_Alowd_Amt",
            "Patient volume (high to low)": "Tot_Benes",
        }
        # Default sort: Distance when ZIP is valid, else Price
        _zip_coords_for_default = cached_zip_coords()
        if (
            user_zip
            and user_zip.isdigit()
            and len(user_zip) == 5
            and user_zip in _zip_coords_for_default
        ):
            default_sort_index = 0
        else:
            default_sort_index = 1
        sort_label = st.selectbox(
            "Sort by",
            list(sort_options.keys()),
            index=default_sort_index,
            key="filter_sort",
        )
        sort_col = sort_options[sort_label]

    # --- Results area ---
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

    # Provider query
    effective_sort_col = sort_col if sort_col != "distance_miles" else "Avg_Sbmtd_Chrg"
    providers = get_providers_for_service(
        df, selected_name, hcpcs_code=selected_hcpcs, sort_by=effective_sort_col
    )

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
                ascending = sort_col != "Tot_Benes"
                providers = providers.sort_values(sort_col, ascending=ascending).reset_index(drop=True)

    if warning_message:
        st.warning(warning_message)

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
```

- [ ] **Step 5: Replace the body of `main()` with the router**

Find the existing `def main():` function. Replace the ENTIRE function body (everything inside `def main():`, from `st.markdown("""` on line 51 down through the existing `st.warning(...)` caveats block) with this tiny router:

```python
def main():
    if "view" not in st.session_state:
        st.session_state.view = "landing"

    if st.session_state.view == "landing":
        render_landing()
    else:
        df = cached_load()
        render_search(df)
```

The `if __name__ == "__main__": main()` block at the bottom stays unchanged.

- [ ] **Step 6: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('app/streamlit_app.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`

- [ ] **Step 7: Run all tests**

```bash
python3 -m pytest tests/ -q
```

Expected: `36 passed`.

- [ ] **Step 8: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat: add landing page and move all inputs to main area for mobile discoverability"
```

---

### Task 2: Smoke Test and Push

**Files:** None modified — verification only.

- [ ] **Step 1: Launch app locally**

```bash
pkill -f "streamlit run" || true
python3 -m streamlit run app/streamlit_app.py
```

Expected: App launches at `http://localhost:8501`.

- [ ] **Step 2: Desktop verification**

In the browser, verify:

1. **Landing page renders:**
   - Large logo (80px) + "ClearCare" wordmark (40px) + tagline
   - Description paragraph
   - Bullet list (16 services, real data, explanations, ZIP search)
   - Muted prototype disclaimer
   - Full-width "Get Started →" primary button
   - Divider
   - Yellow caveats warning box

2. **Click "Get Started" →** transitions to search page:
   - Compact header (smaller logo + wordmark)
   - Divider
   - Search input "What procedure are you looking for?"
   - Service dropdown
   - Variant radio (if applicable)
   - Filters expander (collapsed by default)
   - Service title + metrics below
   - "About this service" expander
   - Provider cards
   - Caveats footer
   - **No sidebar visible** at the left

3. **Type "a1c"** in search → dropdown filters to HbA1c; selecting it shows HbA1c results

4. **Click "Filters" expander** → ZIP, radius, sort appear

5. **Enter ZIP `46202`** + 10 miles → cards narrow, distance column appears, sort defaults to Distance

6. **Refresh browser** (F5) → returns to landing page

- [ ] **Step 3: Mobile verification**

Either use Chrome DevTools (F12 → Toggle device toolbar → iPhone 14 Pro) or open the Network URL on your phone.

Verify:

1. Landing page: logo, description, button all visible without zooming
2. "Get Started" button is tappable (full width)
3. Search page loads with search input at the top (immediately accessible)
4. **No hidden sidebar arrow** — there's no `<<` to hunt for
5. Tapping search brings up keyboard
6. Filters expander is tappable and its inputs are usable
7. Results scroll cleanly
8. Caveats footer readable

- [ ] **Step 4: Stop Streamlit**

Press `Ctrl+C` in the terminal running the app.

- [ ] **Step 5: Push to GitHub**

```bash
git push
```

Expected: 1 new commit pushed to `main`. Streamlit Cloud auto-redeploys in 1-2 minutes.

- [ ] **Step 6: Verify deployed app**

Open the Streamlit Cloud URL on your iPhone and verify the landing page appears, tapping "Get Started" brings up the search page with a clearly visible search input at the top, and no sidebar arrow is present.

---
