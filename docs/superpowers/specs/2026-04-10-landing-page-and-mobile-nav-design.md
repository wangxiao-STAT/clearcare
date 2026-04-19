# Landing Page + Mobile Nav Fix

## Overview

Add a landing page that introduces ClearCare when users first open the app, with a "Get Started" button that transitions to the search experience. Simultaneously fix the mobile discoverability problem where users can't find the sidebar `<<` arrow by moving all inputs (search, service selection, ZIP, radius, sort) out of the sidebar and into the main content area. After this change, the sidebar disappears entirely.

## Motivation

Two related UX problems surfaced during pilot-readiness review:

1. **No context for new users.** The current app drops users directly into the search interface with no introduction. Pilot users (benefits navigators, employers) don't know what the tool does, how it works, or what data backs it before they start clicking.

2. **Mobile search is hidden.** On phones, Streamlit collapses the sidebar into a small `<<` arrow in the top-left corner. Users frequently miss it entirely and think the app has no search — they see the empty content area and give up.

Both problems share the same root fix: stop relying on the sidebar for critical UI. A landing page gives new users context, and moving all inputs into the main area makes the app usable on any screen size without hunting for hidden controls.

## Architecture

Two functions plus a session-state router:

- **`render_landing()`** — Displays logo, tagline, description, features list, prototype disclaimer, "Get Started" button, and caveats footer.
- **`render_search(df)`** — The current search UI, restructured so all inputs live in the main area. No sidebar calls.
- **`main()`** — A thin router that checks `st.session_state.view` (defaulting to `"landing"`) and dispatches to the right render function.

State model:

```python
if "view" not in st.session_state:
    st.session_state.view = "landing"

if st.session_state.view == "landing":
    render_landing()
else:
    render_search(df)
```

The "Get Started" button sets `st.session_state.view = "search"` and triggers a rerun (Streamlit reruns the script on button clicks automatically). Refresh or new session returns to landing.

## Landing Page Content

### 1. Branded header

Reuse the existing inline SVG logo, but at larger size:

- SVG: 80×80 px (current search-page header uses 44×44)
- Wordmark "ClearCare": 40px, navy, bold
- Tagline: "Compare healthcare prices in Indiana" (16px, muted gray)

### 2. Description paragraph

> ClearCare helps patients and benefits navigators find and compare prices for common healthcare services across Indiana providers. We show you a realistic price range, what's typically included, and what questions to ask before scheduling care.

### 3. What it offers (bullet list)

- 16 shoppable services (MRI, CT, colonoscopy, labs, and more)
- Real Indiana provider data from Medicare 2023
- Plain-English explanations of what's included and what may be billed separately
- ZIP code search to find providers near you

### 4. Prototype disclaimer (small, muted)

> This is an early prototype built for pilot feedback. Prices shown are estimates based on Medicare data; actual cash or self-pay prices may differ.

### 5. "Get Started →" button

Full-width (or wide) Streamlit button. `type="primary"` to pick up the navy theme color. On click, sets `st.session_state.view = "search"`.

### 6. Caveats footer

The same `st.warning()` block used on the search page, for legal clarity.

### Layout

Centered column (inherited from page config `layout="centered"`). Content stacks vertically; looks good on both desktop and phones.

## Search Page Restructure

### New top-to-bottom layout

1. **Compact branded header** — SVG logo + "ClearCare" wordmark at current 44×44 size
2. **Divider**
3. **Search input (main area, prominent)**:

   ```python
   query = st.text_input(
       "What procedure are you looking for?",
       placeholder="e.g. knee MRI, colonoscopy, blood test, a1c",
       key="main_search",
   )
   ```

4. **Service selectbox** in main area (populated from `search_services(query)` or full catalog if query empty)
5. **Variant radio** in main area, only rendered when the selected service has multiple variants
6. **Filters expander** — `st.expander("Filters", expanded=False)` containing:
   - ZIP code text input (5-char max)
   - Radius selectbox (5, 10, 25, 50, 100 miles; default 25)
   - Sort selectbox (Distance, Price, Medicare allowed, Patient volume)
7. **Results area** (unchanged):
   - Service title + category caption
   - Statewide Low/Typical/High metrics
   - "About this service" expander
   - Divider
   - Provider cards (top 50, with "Showing top 50 of N" caption if more)
8. **Caveats footer** (unchanged)

### Sidebar removal

- Remove all `st.sidebar.*` calls
- Update `st.set_page_config`: `initial_sidebar_state="collapsed"` (was `"auto"`)
- Streamlit still reserves a thin toggle bar in some versions, but nothing useful lives there

### Filters expander default state

Closed by default (`expanded=False`). Rationale: the most common flow is "search → select service → view results." ZIP, radius, and sort are refinements that users reach for when they want to narrow results. Keeping filters closed keeps the main view uncluttered and matches how users expect an expander to work.

### Sort default

Same logic as today:

- When a valid Indiana ZIP is entered in the Filters expander, default sort is "Distance (nearest first)"
- Otherwise default is "Price (low to high)"

This is evaluated inside `render_search` after reading the expander inputs.

## File Changes

| File | Action | What |
|------|--------|------|
| `app/streamlit_app.py` | Modify | Split `main()` into `render_landing()` + `render_search(df)`; add session-state router; delete sidebar calls; add Filters expander; set sidebar state to collapsed |
| `.streamlit/config.toml` | No change | Theme already defined |
| `tests/*.py` | No change | All 36 tests still pass (no logic changes; only presentational rearrangement) |
| Data files | No change | |

### Estimated diff

- `render_landing()` — new function, ~50 lines
- `render_search(df)` — new function wrapping current search body with sidebar calls swapped for main-area equivalents, ~130 lines (mostly existing code relocated)
- `main()` — rewritten as ~10-line router
- CSS / page config — 1-line change to `initial_sidebar_state`
- Net: ~+70 lines in `streamlit_app.py`

## Testing Strategy

### Automated

All 36 existing tests must continue to pass. No new tests needed — this change is presentational with no new logic.

```bash
python3 -m pytest tests/ -q
```

Expected: `36 passed`.

### Manual smoke test

**Desktop:**

1. Open the app → landing page renders with large logo, description, bullet list, disclaimer, "Get Started" button, caveats footer
2. Click "Get Started" → page replaces with search interface
3. Compact header at top (smaller logo + wordmark)
4. Search input "What procedure are you looking for?" is the first thing below the divider
5. Typing "a1c" filters the service dropdown to HbA1c
6. Selecting HbA1c shows the statewide price metrics and provider cards
7. Click "Filters" expander → ZIP, radius, sort inputs appear
8. Enter ZIP 46202 + 10 miles → cards narrow, distance column appears
9. Refresh the browser → returns to landing page

**Mobile (iPhone or Chrome DevTools mobile emulation):**

1. Open the app → landing page readable on narrow screen, logo + text + button all visible without zooming
2. Tap "Get Started" → search page loads
3. No sidebar arrow visible
4. Search input is immediately accessible at the top of the screen
5. Tapping the search input brings up the keyboard
6. Selecting a service shows results
7. Tapping "Filters" expands the ZIP/radius/sort inputs
8. Results scroll cleanly
9. Caveats footer visible at the bottom

### Edge cases to verify

- **Empty search on search page** — service dropdown shows all 16 services
- **Search with a match** — service dropdown filters
- **No matching service** — dropdown falls back to all services (existing behavior)
- **Invalid ZIP** — warning appears (existing behavior)
- **Service with no variants** — variant radio doesn't render (existing behavior)
- **Filters collapsed by default** — user sees clean results first, opens Filters only when needed

## Risks

- **Bookmarked URLs land on landing, not search** — Session state is per-session. Users who bookmark the "deep" URL still see the landing page on return. Acceptable for a prototype.
- **Streamlit sidebar reservation** — Some Streamlit versions still render a thin edge bar even when `initial_sidebar_state="collapsed"`. If this is visually distracting, add a CSS rule to hide it. Start without the CSS hack and only add if necessary.
- **Filters expander on mobile** — Streamlit expanders work well on mobile; no known issues. Sanity-check during smoke test.
- **Layout shift when Filters opens** — The expander grows vertically; existing results shift down. Streamlit handles this smoothly; no scroll-jump fix needed.

## Non-Goals

- No URL routing or query parameters (`?view=search`)
- No "Back to Home" button on the search page
- No analytics on landing → search clickthrough rate
- No A/B testing of landing content
- No animations or transitions between pages
- No multi-page app structure (`pages/` directory)
- No persistence of landing-page-dismissed state across sessions
- No CSS hacks to force-hide the Streamlit sidebar toggle (add only if smoke test shows it's distracting)
