# UI Polish — Mobile + Visual Identity

## Overview

Polish the ClearCare prototype's look and mobile behavior. Add a hand-coded SVG logo, apply a healthcare-blue theme, replace the provider table with mobile-friendly stacked cards, and switch to a centered layout that reads well on both desktop and phones. No new dependencies, no new data files, no image assets.

## Motivation

Pilot users (benefits navigators, employers) often review prices on mobile devices. The current prototype uses the default Streamlit appearance: a generic red primary color, no logo, and a horizontally-scrolling `st.dataframe` that's cramped on phones. The earlier session already fixed an unreadable yellow caveats box. This spec addresses the remaining mobile-readability issues and establishes a basic visual identity so the app feels credible to share.

## Scope

Two goals, handled together because they affect the same file:

1. **Mobile readability** — cards instead of table, centered layout, responsive columns.
2. **Visual identity** — SVG logo + wordmark, navy theme, consistent typography.

Everything lives in `.streamlit/config.toml` and `app/streamlit_app.py`. All other modules are untouched. All 36 existing tests still pass.

## Theme (`.streamlit/config.toml`)

New file:

```toml
[theme]
primaryColor = "#0B3B5F"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F4F6FA"
textColor = "#1A2332"
font = "sans serif"
```

**Color palette rationale:**

- **#0B3B5F (deep navy)** — primary color; reads as clinical and trustworthy without being cold. Used for buttons, input focus, links, selected items, and the logo.
- **#FFFFFF** — main background, maximum contrast for text
- **#F4F6FA** — sidebar and subtle card fill, gives visual depth without noise
- **#1A2332** — body text, near-black for readability

Streamlit picks these up automatically on page load. No code changes needed to activate.

## Logo & Header

Replace the current sidebar title with a hand-coded inline SVG + wordmark rendered in the main area at the top of `main()`.

### SVG icon

A stylized "shield with a price tag" motif — represents protection + price transparency. ~40×40 px, navy color, hand-coded inline. No external file.

Example structure (final SVG goes in the implementation plan):

```html
<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <!-- Shield outline -->
  <path d="M20 2 L36 8 L36 20 Q36 30 20 38 Q4 30 4 20 L4 8 Z" fill="#0B3B5F"/>
  <!-- Price tag cutout (negative space using evenodd) -->
  <!-- ... -->
</svg>
```

### Header block

Rendered at the very top of `main()`, above everything else:

```html
<div style="display:flex;align-items:center;gap:12px;padding-bottom:0.5rem;">
  <div>{SVG}</div>
  <div>
    <div style="font-size:28px;font-weight:700;color:#0B3B5F;line-height:1.1">ClearCare</div>
    <div style="font-size:14px;color:#6b7280;line-height:1.2">Compare healthcare prices in Indiana</div>
  </div>
</div>
```

Followed by `st.divider()`.

### Sidebar cleanup

Remove the duplicate title and tagline from the sidebar (currently: `st.sidebar.title("ClearCare")` + `st.sidebar.markdown("Compare healthcare prices across Indiana providers")`). The logo in the main area replaces these. The sidebar's first element becomes the "Search for a procedure" input.

## Layout Switch

Change `st.set_page_config` from `layout="wide"` to `layout="centered"`:

```python
st.set_page_config(
    page_title="ClearCare — Compare Healthcare Prices",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="auto",
)
```

**Why centered:** With card-based provider display, wide layout wastes horizontal space. Centered caps content width (~730px), which reads better on both phones and wide monitors. Cards stack neatly within the centered column.

**`page_icon="🏥"`** sets the browser tab favicon to a hospital emoji — free, no file, universal.

## CSS Injection

Minimal inline CSS at the top of `main()` for vertical rhythm:

```python
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)
```

Two rules only:

- Tighter padding around the main block for a less sparse feel
- A little breathing room between bordered containers (card stacks)

## Provider Cards

Replace the `st.dataframe` provider rendering with a loop of `st.container(border=True)` cards. Cap at 50 providers.

### Card structure

```
┌────────────────────────────────────────────┐
│ Dr. John Smith                     12.4 mi │  ← row 1: name (bold) | distance chip (right, navy)
│ Indianapolis · 46202                        │  ← row 2: muted caption
│ ─────────────────────────────────────────── │
│ $317        Medicare: $61    42 patients   │  ← row 3: 3 columns of stats
│ avg billed                                  │     (small muted labels under each)
└────────────────────────────────────────────┘
```

### Rendering loop

```python
display = providers.head(50)
for _, row in display.iterrows():
    with st.container(border=True):
        top_cols = st.columns([4, 1])
        top_cols[0].markdown(f"**{format_provider_name(row)}**")
        if "distance_miles" in display.columns and pd.notna(row.get("distance_miles")):
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
```

### Mobile behavior

`st.columns` automatically stacks vertically on narrow screens (Streamlit's built-in responsive behavior). On mobile:

- Card top row (name | distance) stays side by side because it's a 4:1 ratio with short content
- Card bottom row (3 columns of stats) stacks vertically on very narrow phones

On desktop, cards take the centered column width (~730px) and stack top-to-bottom.

### Pagination limit

Hard-capped at 50 providers per service view. Reasons:

- Rendering hundreds of cards in Streamlit is slow (re-renders on every interaction)
- 50 cheapest (or nearest, or highest-volume) is enough for real comparison
- Users with >50 results can narrow by ZIP/radius

Below the cards, if the unfiltered list has more than 50, show a muted caption telling the user how to see more.

## What Stays the Same

- `st.warning()` caveats footer (already mobile-adaptive from earlier fix)
- "About this service" expander (already mobile-friendly)
- Statewide `st.columns(3)` price metrics (auto-stacks on mobile)
- Sidebar collapse on mobile (Streamlit default)
- Search input, variant radio, ZIP/radius inputs, sort dropdown — all unchanged
- Data pipeline, search, geo, explanations modules — no changes

## Testing Strategy

### Automated

All 36 existing tests must still pass. No new tests needed — this change is purely presentational with no new logic. The integration test for committed explanations JSON still passes (data unchanged).

```bash
python3 -m pytest tests/ -q
```

Expected: `36 passed`.

### Manual smoke test

1. **Desktop (laptop browser):**
   - Header renders: SVG logo, "ClearCare" wordmark, tagline, divider
   - Theme is navy throughout (buttons, selected sort option, input focus)
   - Service selection works
   - Stats metrics render in 3 columns
   - "About this service" expander opens
   - Provider cards render below the divider with name, distance, city, prices
   - Caveats footer visible at the bottom

2. **Mobile (iPhone or Chrome DevTools mobile emulation):**
   - Header renders cleanly, not cramped
   - Sidebar hidden behind hamburger
   - Tapping hamburger reveals sidebar with all inputs
   - Stats metrics stack vertically in a readable way
   - Provider cards are readable without horizontal scroll
   - Cards stack top-to-bottom; inner columns collapse on very narrow screens
   - Caveats box readable (no yellow background contrast issue)

3. **ZIP search:**
   - Enter ZIP 46202 + 10 miles → cards show distance, sorted nearest first
   - Invalid ZIP → warning banner, cards still render with statewide data

4. **Large result sets:**
   - Select HbA1c (1,457 providers statewide) → cards render in reasonable time, "Showing top 50 of 1457" caption visible below

## Risks

- **Streamlit DOM attribute change** — The CSS rule targeting `[data-testid="stVerticalBlockBorderWrapper"]` depends on Streamlit's internal HTML. If Streamlit renames it in a future version, the margin-bottom rule silently stops applying; cards still render, just with default spacing. Acceptable.
- **Rendering performance on huge lists** — Capped at 50 cards to avoid slowness.
- **SVG aesthetic** — Hand-coded SVG is my best effort without a designer. If it looks bad after deploy, iterate on it.
- **Mobile testing is manual** — Cannot automate Streamlit mobile testing. User verifies on their iPhone after deploy.

## Non-Goals

- No custom fonts (stay with Streamlit default sans-serif)
- No icon library (Font Awesome etc.)
- No dark mode
- No animations or transitions
- No React/Next.js migration
- No multi-page structure (`pages/` directory)
- No responsive breakpoint tuning beyond what Streamlit provides natively
- No pagination beyond the 50-card cap
- No A/B testing or feature flags
