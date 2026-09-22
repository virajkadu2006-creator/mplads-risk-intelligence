# MPLADS Risk Intelligence System — UI/UX Transformation Blueprint & Antigravity Master Prompt

**Scope:** Frontend/UX only. Backend (`backend/main.py`), ML pipeline (`ml/*`), database schema, and API contracts are **preserved as-is** — this document changes how the existing data is *presented*, not what data exists or how it's computed.

**Grounding:** This blueprint is based on a direct clone and inspection of `github.com/virajkadu2006-creator/mplads-risk-intelligence` (not assumption). Section 1 states exactly what was found.

---

## 1. Repository Audit (Real Findings)

### 1.1 What actually exists

| Layer | Reality |
|---|---|
| Frontend | **Single file**, `frontend/app.py` (594 lines) — a Streamlit app with Plotly charts. Not React, not Dash. Sidebar radio navigation across 5 pages: Overview, Risk Monitor, Project Investigation, Geo Analysis, ML Insights. |
| Backend | FastAPI (`backend/main.py`, 362 lines), SQLite (`mplads.db`), endpoints: `/health`, `/filters`, `/statistics`, `/projects`, `/projects/{id}`, `/projects/{id}/notes` (POST), `/states`, `/anomalies`, `/export/csv`. |
| Data | `projects` table: **1,001 rows**, 5 distinct states. Current risk distribution: **High = 64, Medium = 350, Low = 587, Critical = 0** — there are no Critical-category examples in the current seeded/demo data. Not a UI problem, but worth knowing: the most dramatic "wow" story in a live demo currently tops out at High, not Critical. |
| Alerts | `alerts` table: 2,091 rows across 6 types — `COST_OVERRUN, UNDER_UTILIZED, DELAYED, POSSIBLE_DUPLICATE, TRUST_COMPLIANCE, ML_OUTLIER`. |
| Styling | Theme colors are set twice — once in `.streamlit/config.toml`, once again as hardcoded hex values inside an f-string CSS block in `app.py` (lines ~99–178) that re-derives colors from a `is_dark` boolean. Two sources of truth for the same palette. |
| Explanations | Rule engine (`ml/rules.py`) and ML explainer (`ml/risk_scoring.py`) already produce clean, non-accusatory text ("Cost exceeded the sanctioned amount by X%…", "This project is statistically unusual…"). A test (`tests/unit/test_banned_words.py`) already enforces no `fraud/guilty/corrupt/criminal` language in alert text or source code. **This wording is correct and must not be reworded** — only its visual container changes. |
| Risk decomposition | **`projects` already stores `cost_contribution`, `delay_contribution`, `ml_contribution`, `compliance_contribution`, `under_utilization_contribution` as columns** — the exact per-component breakdown a "why was this flagged" visualization needs. **None of these five columns are currently rendered anywhere in the UI.** This is the single biggest available upgrade that requires zero backend work. |
| Dependencies | `pandas, scikit-learn, fastapi, uvicorn, gunicorn, SQLAlchemy, pydantic, joblib, rapidfuzz, pytest, python-dotenv, pyarrow, streamlit, plotly, requests`. No component library, no mapping library beyond Plotly itself, no custom Streamlit components. |

### 1.2 Concrete inconsistencies found (not opinions — observed in the code)

1. **The design system already half-exists but isn't applied consistently.** CSS classes `.metric-card`, `.card-label`, `.card-value`, `.badge-critical/high/medium/low` are defined once (lines 108–178) but only actually *used* on the Project Investigation screen's risk-score display. The Overview screen's 5 KPIs use plain `st.metric()` instead of the same card system — so the two most important screens currently look like two different apps.
2. **The risk-score breakdown is computed but invisible.** The alert box lists *which* rules fired as plain warning banners, but never shows *how much* each contributed to the final number — even though the data for that exact chart already sits in the row.
3. **The Overview screen is missing three sections the product logic implies it should have:** a "Top Risk Projects" list, a "Recent Anomalies" feed, and an "Actionable Insights" translation layer. Right now Overview is KPIs + 2 charts + one static info box — it doesn't yet answer "what should I look at first," it just shows totals.
4. **Geo Analysis is a state-ranked bar chart + table, not a map** — a reasonable MVP fallback (and consistent with the original build spec's documented fallback), but Plotly (already a dependency) can render a genuine India state choropleth if a states GeoJSON is available — a real upgrade path, not a new dependency.
5. **`load_name_lookup()`/`apply_name_lookup()` read `data/raw/recommended_works.csv` directly from the frontend, bypassing the API**, specifically because (per the code's own comment) the backend DB can go stale. This is a legitimate, intentional workaround — **do not remove it** — but it's a signal that MP name/constituency display has a data-freshness quirk worth being visually unremarkable about (i.e., don't build any UI feature that assumes `mp_name` in the API response is authoritative).
6. **`frontend/app.py` is a single 594-line file** already mixing page routing, CSS, data-fetching, and rendering logic. Adding the new visual blocks below on top of that structure as more inline code would make it worse, not better.

### 1.3 KEEP / IMPROVE / REBUILD / ADD / DO NOT TOUCH

| Decision | Item |
|---|---|
| **DO NOT TOUCH** | `backend/main.py`, all API routes/contracts, `ml/*.py`, `config/thresholds.yaml`, DB schema, `tests/unit/test_banned_words.py` and the alert/explanation text it protects, the `data/raw` CSV name-lookup workaround |
| **KEEP** | 5-screen IA (Overview / Risk Monitor / Project Investigation / Geo Analysis / ML Insights) — it already matches a sound judge journey and every screen is backed by real data; dark/light theme toggle; CSV export; investigation-notes workflow; sidebar navigation pattern |
| **IMPROVE** | Apply one real design-token system consistently everywhere (kill the duplicate color source); table styling in Risk Monitor (native `st.dataframe` is visually flat); chart theming consistency; spacing/hierarchy on Project Investigation; badge/typography polish |
| **REBUILD** | The KPI card rendering on Overview (from `st.metric()` to the existing `.metric-card` system, extended); the alert-list rendering (from stacked `st.warning()` banners to structured evidence cards) |
| **ADD** | Risk score breakdown visualization on Project Investigation (data already exists); "Top Risk Projects" + "Recent Anomalies" + "Actionable Insights" sections on Overview (all servable from data already returned by `/projects` and `/anomalies`); an India state choropleth on Geo Analysis (conditional on sourcing a lightweight GeoJSON; bar+table remains the fallback); a small internal module split (`frontend/theme.py`, `frontend/components.py`, `frontend/charts.py`) so `app.py` stays a thin router |

---

## 2. Product Experience Direction

**Positioning:** "Mission-control interface for a government risk analyst" — closer to a Bloomberg Terminal screen or a Palantir case workspace than a college dashboard. The product already has the right analytical *bones* (real evidence, real scores, real provenance); the visual layer needs to stop undercutting that with default-widget styling.

**Feel:** dense but legible, restrained color (color = meaning, not decoration), numbers treated as first-class typography, evidence-first layout. **Avoid:** gradients, glassmorphism, rounded-everything, decorative icons with no data behind them, celebratory/gamified visual language (no confetti, no "achievement unlocked" tone) — this is an audit tool, and it should look like one a District Magistrate would trust.

**Streamlit-specific reality check:** a from-scratch bespoke design system (custom fonts, arbitrary shadows, full layout control) is not achievable the way it would be in React — Streamlit renders inside its own component chrome. The right ambition level is: **push Streamlit's CSS-override surface as far as it goes** (it goes fairly far — card layout, typography, spacing, table cell rendering via `column_config`, chart theming) without fighting the framework by hacking in raw HTML/JS component replacements for things Streamlit already does natively (buttons, selects, tabs, expanders). That's the difference between "premium analytical tool built well in Streamlit" and "Streamlit app straining to look like something it isn't."

---

## 3. Design System

### 3.1 Color tokens (single source of truth — replace the current dual-source setup)

Create **one** token dictionary (Section 15 puts this in `frontend/theme.py`) that both `.streamlit/config.toml` and the injected CSS read from conceptually, so a color only ever needs to change in one place:

| Token | Dark value | Light value | Usage |
|---|---|---|---|
| `bg` | `#0f172a` | `#f8fafc` | App background |
| `surface` | `#1e293b` | `#ffffff` | Cards, table zebra |
| `surface-elevated` | `#243146` | `#f1f5f9` | Hovered/active card, popovers |
| `border` | `#334155` | `#e2e8f0` | All dividers/card borders |
| `text` | `#f8fafc` | `#1e293b` | Primary text |
| `text-muted` | `#94a3b8` | `#64748b` | Labels, captions, secondary numbers |
| `primary` | `#3b82f6` | `#3b82f6` | Navigation active state, primary buttons, links |
| `risk-critical` | `#ef4444` / bg `rgba(185,28,28,.25)` | `#991b1b` / bg `#fee2e2` | Critical badges, chart series |
| `risk-high` | `#f97316` / bg `rgba(234,88,12,.25)` | `#9a3412` / bg `#ffedd5` | High badges, chart series |
| `risk-medium` | `#eab308` / bg `rgba(234,179,8,.25)` | `#854d0e` / bg `#fef9c3` | Medium badges, chart series |
| `risk-low` | `#22c55e` / bg `rgba(22,163,74,.25)` | `#166534` / bg `#dcfce7` | Low badges, chart series |

These are the *existing* values already in `app.py` — carried forward exactly, just centralized. No palette invention needed; the current palette is already reasonable and accessible (dark badge text on translucent backgrounds passes WCAG AA at the sizes used). Risk colors keep their existing exact hex mapping so no chart/badge anywhere silently shifts meaning.

### 3.2 Typography
- Numeric KPIs (risk score, ₹ amounts): tabular/monospaced-leaning numerals, largest weight in the UI (existing `.card-value` at 42px/800 is close — keep, extend to all KPI cards).
- Section headers: one consistent scale (`##`-equivalent via a single `.section-header` class), replacing the current mix of `st.subheader()`, `st.markdown("#### …")`, and `.main-header` used inconsistently across screens.
- Body/labels: existing `.card-label` (14px, muted) — reuse everywhere a label sits above a value, including new components.
- Table headers: sentence case, muted color, no ALL CAPS (matches existing convention — keep).

### 3.3 Spacing & radius
- 4/8/12/16/24/32px scale. Current cards use 18px padding / 8px radius — keep as the base card token; apply the *same* radius (8px) to every card-like surface introduced (currently badges use 12px radius while cards use 8px — harmonize to 8px for cards/containers and keep 12px only for pill-shaped badges, which is a deliberate, meaningful distinction between "container" and "status pill," not an inconsistency to remove).

### 3.4 Icons
Current approach is emoji-as-icon (🏛️ 📊 🔍 🗺️ 🧠 💰 ⏱️ 🚨). This is a reasonable low-dependency choice for Streamlit (no icon font/SVG sprite needed) and reads fine on a projector — **keep it**, but apply a rule: one emoji per section header, never decorative emoji inside body text or table cells (currently mostly followed; enforce it in the new components too).

### 3.5 Buttons, inputs, tables, charts
- Buttons: Streamlit's native `type="primary"`/`type="secondary"` — keep, don't reskin (fighting Streamlit's own button chrome causes more visual bugs than it's worth at this scope).
- Inputs (`selectbox`, `text_input`): native, styled only via the global CSS block for border-color/background to match the surface tokens above.
- Tables: move from bare `st.dataframe(display_df, ...)` to `st.dataframe(..., column_config={...})` using Streamlit's built-in `ProgressColumn` for `risk_score` (renders an inline bar, not just a number) and `NumberColumn` with `format="₹%d"`-style formatting for currency columns, instead of pre-formatting currency into strings (which currently breaks numeric sort). This is a real, concrete, zero-dependency table upgrade.
- Charts: one shared `apply_chart_theme(fig)` helper (Section 15) instead of repeating `fig.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')` seven separate times across the file — same visual result, far less duplication, and it's the single place to add a shared font/margin/hover-style standard.

---

## 4. Information Architecture

**Keep the existing 5 pages exactly.** Per the audit, every one of them is backed by real, existing API data, and together they already trace a sound judge journey (overview → ranked risk → single-project evidence → geography → model diagnostics). Adding pages like "Financial Intelligence" or "Data Explorer" from the original wishlist would not be justified by anything the API currently returns, and Phase 4's own rule is to only recommend screens the repository's real data supports. No new pages are added; all improvements below happen *inside* the 5 existing pages.

| Page | Purpose (unchanged) | Primary question |
|---|---|---|
| Overview | Executive summary | "What's the state of the portfolio, and where should I look first?" |
| Risk Monitor | Ranked/filterable project list | "Which projects are riskiest, filtered to what I care about?" |
| Project Investigation | Single-project evidence dossier | "Why was this specific project flagged, exactly?" |
| Geo Analysis | State-level concentration | "Where is risk concentrated geographically?" |
| ML Insights | Model transparency | "Is the AI component doing real, inspectable work?" |

---

## 5. Executive Dashboard (Overview) Redesign

**Current:** header → 5 `st.metric()` KPIs → risk pie + funds bar → one static info box.
**Target layout (top to bottom):**

1. **Identity strip** (unchanged) — title + PS-26102 caption.
2. **KPI row**, rebuilt on the existing `.metric-card` system (not `st.metric()`) so Overview visually matches Project Investigation: Total Works, Total Sanctioned, Total Expenditure, High+Critical count, Data Quality Score — same 5 metrics, same data, new consistent container.
3. **Risk Overview row** (unchanged charts, shared theme helper): risk donut + funds bar, side by side.
4. **NEW — Top Risk Projects.** A compact 5–8 row table (reuse the same `column_config` pattern as Risk Monitor) pulled from `/projects?sort=risk_score&order=desc&page_size=8` — already exactly what the API supports, no new endpoint. Each row clickable straight into Project Investigation (same `st.session_state.selected_project` pattern already used elsewhere in the file).
5. **NEW — Recent Anomalies feed.** A short list from `/anomalies?limit=6` (endpoint already exists, unused by the frontend today) rendered as compact evidence lines: alert type badge + `reason_text` + project link — turns the existing, currently-unsurfaced `/anomalies` endpoint into a real feature.
6. **NEW — Actionable Insights strip.** 2–3 auto-generated, data-derived sentences (not new AI, just simple aggregation already available from `/statistics` + `/states`), e.g. "X% of flagged works are concentrated in {state}" / "{category} works show the highest average cost overrun." Computed client-side from data already being fetched — no backend change, no invented numbers.
7. Existing workflow hint box (unchanged).

This directly answers Phase 5's four questions ("what's happening / where's the risk / why care / what to investigate") — items 4–6 are exactly what closes the current gap between "here are totals" and "here's what to do next."

---

## 6. Project Investigation Redesign

**Current layout is already close to right** (identity header → risk score card → alert list → financial/timeline → peer/ML → duplicates → provenance → notes) — this is not a rebuild, it's a targeted insert plus polish:

1. Identity header + risk score card — **keep**, minor polish: align typography with the centralized token set (Section 3).
2. **NEW, inserted directly under the alert list:** a **Risk Score Breakdown** chart — a horizontal stacked/segmented bar using the five already-stored columns (`cost_contribution, delay_contribution, ml_contribution, compliance_contribution, under_utilization_contribution`) against their max weights (25/25/25/25/15), so a user sees at a glance *which* factor drove the number, not just the final total and a text list. This is the single highest-value addition in the whole redesign and needs zero backend work.
3. Financial panel / Timeline panel — **keep** the two-column layout; apply the shared progress-bar/badge styling.
4. Peer comparison / ML panel — **keep**; consider replacing the two `st.metric()` percentile displays with a small horizontal "you are here" marker on a 0–100 scale bar, since "62nd percentile" is harder to place mentally than a visual position on a scale — optional polish, not essential.
5. Similar/duplicate works — **keep** as-is.
6. Provenance expander — **keep** as-is; it already does exactly what Part 28 of the original build spec asked for.
7. Investigation notes — **keep**; swap `st.success()` on save for `st.toast()` (Streamlit's non-blocking toast) so adding a note doesn't push the whole page layout down with a persistent success banner.

---

## 7. Risk Intelligence UX

The underlying *language* is already correct and protected by a test — this section is purely about the container, not the words:

- Replace the stacked `st.warning()` banners (one per alert) with structured evidence cards: severity badge (reusing the existing `.badge-*` classes) + alert type label + the exact existing `reason_text`, laid out consistently with the new Risk Score Breakdown chart directly above them so evidence and score-contribution visually reinforce each other.
- Every card keeps the existing "flagged for investigation / statistical anomaly detected" register verbatim — **no copy changes**, only layout.
- Confidence/severity is already present (`severity` field on alerts, `duplicate_confidence` on projects) — surface both explicitly on their respective cards rather than only implicitly through badge color, so severity is never color-only (accessibility, Section 11).

---

## 8. Data Visualization Plan

| Chart | Screen | Data source (existing) | Change |
|---|---|---|---|
| Risk severity donut | Overview | `/statistics` → `kpis.risk_counts` | Keep, apply shared theme helper |
| Sanctioned vs Spent bar | Overview | `/statistics` → `kpis` | Keep, apply shared theme helper |
| **Top Risk Projects table** | Overview | `/projects?sort=risk_score&page_size=8` | **New** — reuses Risk Monitor's `column_config` table pattern |
| **Recent Anomalies feed** | Overview | `/anomalies?limit=6` | **New** — first frontend use of this existing endpoint |
| Ranked/filterable table | Risk Monitor | `/projects` | Keep, upgrade to `column_config` (progress bar for score, proper numeric currency columns) |
| **Risk Score Breakdown bar** | Project Investigation | Already-fetched `/projects/{id}` fields (`*_contribution`) | **New**, zero backend work |
| Peer percentile display | Project Investigation | Already-fetched `peer_comparison` | Keep; optional visual-scale polish |
| State bar / ranked table | Geo Analysis | `/states` | Keep as fallback; **candidate upgrade** to India choropleth (below) |
| Outlier scatter (cost vs delay) | ML Insights | `/projects` | Keep, apply shared theme helper |

**Geo Analysis choropleth (conditional ADD):** Plotly supports `px.choropleth` with a state-level GeoJSON + `featureidkey`. This needs a boundaries file (e.g. a public India-states GeoJSON keyed by state name) bundled into `data/` or `frontend/assets/`. If a suitable GeoJSON can be sourced and the state-name keys reconciled against the 5 distinct state names actually in `projects.state` within the build session, implement the choropleth as the primary view with the existing bar+table kept as a secondary "Ranked State Statistics" panel underneath (both, not a replacement) — this preserves the documented fallback exactly as the original build spec intended. If reconciling the GeoJSON proves time-consuming, **do not block on it** — the existing bar+table already satisfies the requirement and should ship as-is rather than risk a broken map.

**Chart discipline (per the brief's own instruction):** no chart is added above that doesn't map to a real column already in `projects`/`alerts`. Nothing here is decorative.

---

## 9. Microinteractions

Kept deliberately restrained, and scoped to what Streamlit can actually do well:

- **Loading:** `st.spinner("Loading risk data…")` around each `fetch_api()` call site (currently: a failed/slow fetch just silently returns `None` and the page shows a bare warning — add the spinner so the *waiting* state is visible, not just the failure state).
- **Hover:** CSS `:hover` transitions (subtle border/shadow shift, ~120ms) added to the `.metric-card` and new evidence-card classes only — not applied to native Streamlit widgets.
- **Save feedback:** `st.toast()` instead of `st.success()` for note-saving (non-blocking, auto-dismisses — matches a "logged and moving on" investigator workflow better than a persistent banner).
- **Table row → detail:** keep the existing explicit "Open Investigation Dossier" button pattern (Streamlit tables don't support true row-click navigation without a custom component; forcing that in would add a dependency for marginal gain) — but make the same pattern available from the new Top Risk Projects and Recent Anomalies blocks on Overview, so every entry point into a project follows one consistent interaction, not several different ones.
- **Theme toggle:** already instant (full CSS re-injection on rerun) — keep.
- No page-transition animation, no skeleton shimmer libraries, no confetti/celebration states anywhere — deliberately excluded per Phase 9's own "tasteful, not decorative" instruction.

---

## 10. Responsive Strategy

Streamlit has no native JS viewport breakpoints, so "responsive" here means: CSS that degrades gracefully, and column layouts that don't strictly assume desktop width.

- Replace the fixed `st.columns(5)` KPI row with a CSS flexbox wrapper (`display:flex; flex-wrap:wrap; gap:16px`) around individually-rendered card divs, instead of Streamlit's fixed-width column grid — flex-wrap lets cards reflow onto two rows on a narrow window instead of squeezing five columns into an unreadable width, which is the current KPI row's real failure mode on a laptop at less than full-screen or on a tablet.
- Sidebar navigation: Streamlit already auto-collapses the sidebar into a hamburger below its own breakpoint — no action needed, just don't fight it with a fixed-width sidebar override.
- Tables: keep `use_container_width`/`width='stretch'` (already used) so tables scale to the viewport; on genuinely narrow screens, prioritize hiding lower-priority columns (e.g. `Constituency`) over shrinking font size, via a simple width check (`st.session_state` doesn't expose viewport width natively, so this is a "design for it, verify manually across a couple of sizes" item, not something Streamlit can fully automate).
- Charts: Plotly figures are already responsive within their container via `width='stretch'` — keep.

---

## 11. Accessibility

- Non-color risk indicators: **already satisfied** — every badge pairs color with a text label (`CRITICAL RISK`, etc.) and section headers already pair icons with words; extend the same pairing to every *new* component (breakdown chart segments get a text legend, not color-only).
- Contrast: the existing dark-mode badge palette (light text on ~25%-opacity colored background, bordered) passes typical AA contrast at UI-label sizes — keep the values exactly as-is (Section 3.1); don't introduce new ad-hoc colors for new components, reuse these tokens so contrast is inherited, not re-derived.
- Keyboard/focus: native Streamlit widgets already carry reasonable focus states — the only place this needs explicit attention is the new custom HTML card/badge components, which need `tabindex`/`role` only if they become independently clickable (the plan above keeps click actions on native `st.button()` elements, so this risk is avoided by design).
- Screen-reader labels: charts get a one-line `st.caption()` text summary immediately below them (a few already exist, e.g. Geo Analysis; extend the pattern to every chart) so the chart's takeaway isn't visual-only.

---

## 12. Hackathon Judge Journey

The existing page order **already matches** the ideal judge journey almost exactly: Overview → (judge sees scale + risk framing) → Risk Monitor → (judge filters to High) → Project Investigation → (judge sees exact evidence) → Geo Analysis → ML Insights. The redesign doesn't need to reorder anything — it needs to make step 1 (Overview) close the "why should I care" gap faster (Section 5's new Top Risk Projects + Actionable Insights blocks are exactly that), and make step 3 (Project Investigation) show the score breakdown visually instead of requiring the judge to read a bulleted alert list to reconstruct how 0–100 was derived (Section 6, item 2). Those two additions are the highest-leverage changes for the 30–60 second judge-comprehension window specifically.

---

## 13. Performance

- 1,001 rows is small; `st.dataframe` and Plotly render it comfortably — no pagination/virtualization work needed beyond what already exists (`page_size` param).
- `st.cache_data(ttl=15)` on `fetch_api()` and `ttl=3600` on the CSV name-lookup are already sensible and should be kept unchanged.
- The new Overview additions (Top Risk Projects, Recent Anomalies) reuse the *same* cached `fetch_api()` — they do not add new network calls beyond what a normal page load already needs, since `/projects` and `/anomalies` are cheap, already-indexed-by-SQLite queries.
- Chart re-render on theme toggle is already a full script rerun (Streamlit's normal model) — acceptable at this data scale; no special-casing needed.

---

## 14. Implementation Strategy

**Stack stays exactly as-is: Streamlit + Plotly + FastAPI + SQLite.** No new heavy dependency is required for anything in this blueprint:

- Table upgrades → `st.dataframe(column_config=...)`, built into Streamlit already.
- Risk breakdown chart, choropleth → `plotly.express`, already a dependency.
- Toast feedback → `st.toast()`, built into Streamlit already.
- Flex-wrap KPI cards → plain CSS, no library.

**The one optional new asset** (not a package) is a bundled India-states GeoJSON file for the choropleth (Section 8) — this is a static data file, not a dependency, and the feature has an explicit, already-shipping fallback if it doesn't fit the timeline.

**Do not add:** a component library, a JS charting library, streamlit-extras, streamlit-aggrid, or any custom Streamlit component package — none are necessary for anything specified above, and introducing one would violate the repository's own "prefer the existing architecture" constraint for no real gain at this data scale.

---

## 15. File-by-File Changes

`frontend/app.py` is currently the *only* frontend file, and it's already 594 lines before any of the above is added. Split it now rather than let it keep growing as one file:

```
frontend/
├── app.py            # page routing + st.set_page_config + sidebar nav only (~80-100 lines)
├── theme.py           # NEW — the color token dict (3.1), CSS injection block, apply_chart_theme() helper
├── components.py      # NEW — render_metric_card(), render_badge(), render_evidence_card(),
│                       #        render_risk_breakdown_chart() — reusable across Overview + Project Investigation
├── charts.py           # NEW — one function per chart in Section 8's table, each taking already-fetched
│                        #        data and returning a themed Plotly figure
├── api_client.py        # NEW — fetch_api()/post_api()/load_name_lookup()/apply_name_lookup(), moved
│                         #        verbatim out of app.py (logic unchanged, just relocated)
```

This is a pure refactor of existing logic plus the additive pieces described above — **no function's actual behavior changes** during the move, so there is no risk to `backend/main.py` or `ml/*` compatibility. `frontend/app.py` after the split becomes small enough to read in one pass, and every new component in Sections 5–8 has an obvious, single home instead of getting bolted onto an already-large file.

---

## 16. Validation / Final QA Checklist

- [ ] Every existing page still loads and shows the same underlying data as before the redesign (spot-check each of the 5 screens against the pre-redesign version)
- [ ] No API route, request shape, or response shape in `backend/main.py` was changed
- [ ] No file under `ml/` was changed
- [ ] `config/thresholds.yaml` was not changed
- [ ] `tests/unit/test_banned_words.py` still passes unmodified — no new UI copy introduces `fraud/guilty/corrupt/criminal`
- [ ] All existing tests (`tests/backend`, `tests/unit`, `tests/data`) still pass
- [ ] Dark and light theme both render every new component correctly (cards, breakdown chart, evidence cards, toast)
- [ ] Risk Score Breakdown chart's five segments sum to the same number as the displayed `risk_score` for at least 3 spot-checked projects across different risk categories
- [ ] Top Risk Projects / Recent Anomalies blocks on Overview both link correctly into Project Investigation for the same project
- [ ] KPI card row reflows (doesn't clip/overflow) at a narrower browser width
- [ ] No new pip dependency was added unless explicitly justified in this document (GeoJSON asset is data, not a dependency)
- [ ] CSV export and investigation-notes POST still function exactly as before

---

## 17. FINAL MASTER PROMPT FOR ANTIGRAVITY

Paste this as a message in your **existing** `mplads-risk-intelligence` Antigravity workspace (the repo is already cloned/open — this is not a fresh-project kickoff like Part 33 of the build spec). If you also keep this whole blueprint file in the repo (e.g. `docs/UIUX_Transformation_Blueprint.md`), reference it with `@docs/UIUX_Transformation_Blueprint.md` in the prompt instead of relying on the inline summary below.

```
You are redesigning the frontend of the MPLADS Risk Intelligence System. This is a
UI/UX transformation, not a rebuild. Read this entire prompt before touching any file.

SCOPE LOCK — read this first:
- Only frontend/app.py (and the new files you create under frontend/) may change.
- Do NOT modify backend/main.py, anything under ml/, config/thresholds.yaml, the
  database schema, or any existing test file. Do NOT change any API route, request
  parameter, or response shape.
- Do NOT reword any alert/explanation text produced by ml/rules.py or
  ml/risk_scoring.py's Explainer — that text is verified accurate and is protected
  by tests/unit/test_banned_words.py, which must still pass unmodified after your
  changes. You are changing how that text is displayed, never what it says.
- Do NOT add new pip dependencies. Everything in this task is achievable with the
  existing stack: streamlit, plotly, fastapi (untouched), pandas. The one allowed
  exception is a static GeoJSON data file for the map feature below (data, not a
  package) — and that feature has an explicit fallback if it doesn't fit.

STEP 1 — Re-verify the current state before changing anything:
- Read frontend/app.py in full.
- Query the live projects/alerts tables (or read data/processed/projects_analytical.parquet)
  to confirm current row counts, risk-category distribution, and that these five
  columns exist and are populated: cost_contribution, delay_contribution,
  ml_contribution, compliance_contribution, under_utilization_contribution.
- Confirm the /anomalies and /states endpoints in backend/main.py and their exact
  response shapes — you will consume both without modifying either.
- If anything here has changed since this prompt was written, adapt the plan below
  to the real current state rather than to what's described here, and note the
  difference back to me before proceeding.

STEP 2 — Refactor frontend/ into these files (behavior-preserving move, not a rewrite
of logic):
  frontend/app.py         → page routing, st.set_page_config, sidebar nav only
  frontend/theme.py        → NEW: one color-token dict (dark+light), the CSS
                              injection block (moved verbatim from app.py, then
                              parameterized off the token dict instead of inline
                              hex ternaries), and an apply_chart_theme(fig) helper
                              that every chart calls instead of repeating
                              fig.update_layout(...) inline
  frontend/api_client.py    → NEW: fetch_api(), post_api(), load_name_lookup(),
                               apply_name_lookup() moved verbatim from app.py — do
                               not change their internal logic, only their location
  frontend/components.py    → NEW: render_metric_card(label, value, sublabel=None),
                               render_badge(risk_category), render_evidence_card(alert),
                               render_risk_breakdown_chart(project_row) — reusable
                               render functions used by more than one page
  frontend/charts.py         → NEW: one function per existing chart (risk donut, funds
                                bar, geo bar, outlier scatter) taking already-fetched
                                data and returning a themed Plotly figure via
                                theme.apply_chart_theme()

Verify after this step: every one of the 5 existing pages still renders identically
to before the refactor. This is a structural move first — do not add any new visual
feature until this step is verified working.

STEP 3 — Apply the design-token system consistently (see design system spec below):
- Overview's 5 KPIs currently use st.metric() — replace with render_metric_card()
  from components.py so Overview visually matches Project Investigation's existing
  risk-score card treatment.
- Replace every repeated fig.update_layout(template=..., paper_bgcolor=..., ...)
  call across the file with theme.apply_chart_theme(fig).
- Risk Monitor's st.dataframe(display_df) → add column_config: ProgressColumn for
  the Score column, NumberColumn with a currency format for Sanction/Spent (so
  currency stays numerically sortable instead of pre-formatted into strings).

STEP 4 — Add the Risk Score Breakdown visualization to Project Investigation
(insert directly below the existing alert list, above the Financial/Timeline panels):
- A horizontal segmented/stacked bar showing cost_contribution, delay_contribution,
  ml_contribution, compliance_contribution, under_utilization_contribution against
  their configured max weights (25/25/25/25/15 — read the actual weights from
  config/thresholds.yaml's risk_scoring.weights at render time, never hardcode them
  in the frontend).
- Each segment labeled with its name and point value, using the same risk-category
  color tokens as the rest of the app.
- Add a one-line st.caption() under the chart summarizing it in words for
  screen-reader/accessibility purposes (e.g. "Cost overrun contributed 15 of the
  35-point score").
- Sanity check: the five contribution values for a given project must sum to that
  project's displayed risk_score (within rounding) — verify this against at least
  3 real projects spanning different risk categories before considering this done.

STEP 5 — Add three new blocks to the Overview page, in this order, below the
existing risk-donut/funds-bar row:
a) "Top Risk Projects" — a compact table (reuse the Step 3 column_config pattern)
   from GET /projects?sort=risk_score&order=desc&page_size=8. Each row must open
   Project Investigation for that project using the same st.session_state.selected_project
   pattern already used elsewhere in the file — do not invent a second navigation
   mechanism.
b) "Recent Anomalies" — a short list from GET /anomalies?limit=6 (this endpoint
   exists and currently has no frontend consumer — this is its first use). Render
   each as: severity badge + alert_type + the alert's own reason_text (verbatim,
   never reworded) + a link into that project's Investigation page.
c) "Actionable Insights" — 2-3 sentences computed client-side from data already
   fetched via /statistics and /states in this same page load (e.g. concentration
   of flagged works in the top state, category with highest average cost-overrun
   ratio). Every number in these sentences must be computed from real fetched data
   — never invented, estimated, or hardcoded as a placeholder.

STEP 6 — Microinteraction polish:
- Wrap every fetch_api() call site with st.spinner() so loading is visible, not
  just failure states.
- Replace st.success() with st.toast() after a successful investigation-note save.
- Add a subtle CSS :hover transition (~120ms) to .metric-card and the new evidence
  card class only — do not touch native Streamlit widget styling.

STEP 7 — Responsive pass:
- Replace the fixed st.columns(5) KPI row with a CSS flex-wrap container around
  individually rendered card divs so cards reflow at narrower widths instead of
  compressing into unreadable columns.
- Verify Risk Monitor's table and every Plotly chart still use width='stretch'
  (already the pattern in most places — extend anywhere it's missing).

STEP 8 (conditional) — Geo Analysis choropleth:
- Attempt to source a lightweight India state-boundaries GeoJSON and render an
  actual px.choropleth keyed to the 5 distinct state names present in the real
  data, placed above the existing bar chart + ranked table (which stay, unchanged,
  as a secondary panel underneath — this is additive, not a replacement).
- If the state-name keys don't clean-match the GeoJSON's naming within a reasonable
  effort, or no suitable GeoJSON is available, SKIP this step entirely and leave
  Geo Analysis exactly as it is today. Do not ship a broken or empty map. Tell me
  which outcome happened.

STEP 9 — Accessibility pass:
- Confirm every risk indicator anywhere in the app pairs color with a text label
  (already true almost everywhere — verify the two new chart/card types from Steps
  4-5 follow the same rule).
- Add a one-line st.caption() summary under every chart that doesn't already have one.

STEP 10 — Validation (run before declaring done):
- All existing tests in tests/ pass unmodified, including test_banned_words.py.
- Manually click through all 5 pages in both dark and light theme.
- Confirm no API call shape changed (diff your new frontend/api_client.py's request
  URLs/params against the original app.py's — they must be identical).
- Confirm the Risk Score Breakdown sums correctly (Step 4's sanity check).
- Report back a short summary: what was built, what was skipped (and why, if Step 8
  was skipped), and confirmation that backend/ml/tests/config were untouched.

Work through these steps in order. Stop and tell me if you hit something that would
require touching backend/main.py, ml/*, or the database schema to accomplish — that
means the step needs to be rescoped, not routed around by quietly touching a file
outside the scope lock above.
```
