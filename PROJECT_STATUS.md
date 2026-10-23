# Project Status

Legend: ✅ done · 🔄 in progress · ⏳ pending · ⛔ blocked

_Last updated: 2026-10-23_

## Step log

| # | Step | Spec | Status | Notes |
|---|---|---|---|---|
| 0 | Project README + status file, initial commit | both | ✅ | README built from `handoff_n.md` + `STYLE_HANDOFF.md` |
| 1 | Streamlit dark theme (`.streamlit/config.toml`) | STYLE §3 | ✅ | `base=dark`, primary `#E040FB`, bg `#0F1330` |
| 2 | Design tokens + global CSS (Kanit, cards, sidebar, tabs, inputs) | STYLE §2, §4 | ✅ | All CSS moved to `src/theme.py` → `inject_theme_css()`; old green `<style>` block removed from `app.py` |
| 3 | KPI cards → gradient cards, delta badges | STYLE §4.4–4.5 | ✅ | Tab 1 + Tab 3 KPI rows alternate `kpi-magenta`/`kpi-cyan`; risk cards = plain `kpi-compact`; badges use a coloured dot on gradients for contrast |
| 4 | Inline light styles → dark callout classes | STYLE §4.7, §4.10 | ✅ | 50 inline styles → `.filter-chips`, `.callout-{warning,success,danger,info,note}`; 0 light colours left in `app.py` |
| 5 | Plotly `neon_night` template + colour constants | STYLE §5 | 🔄 | Template, colour scales, `COLOR_*` remap and `style_*()` chart helpers done in `src/theme.py`; **wiring into `src/visualizations.py` blocked: file missing** |
| 6 | Province lookup from GeoJSON (`pro_code`) | handoff D10 | ⏳ | |
| 7 | Download script for D01–D10 | handoff steps 1 | ⏳ | |
| 8 | Raw → tidy cleaning pipeline (`data/clean/*.csv`) | handoff step 2 | ⏳ | |
| 9 | Verify app run + acceptance checklist | STYLE §7 | ⏳ | |

## Verification log
- 2026-10-23 · Phase 1: `python -m py_compile app.py src/theme.py` ✅ · `tests/test_theme.py` 4 pass, 2 skipped (Plotly not installable in build sandbox) · CSS rendered on a static mock of the app's HTML (header, filter chips, KPI rows, risk cards, 5 callouts) ✅. **Not yet verified inside a running Streamlit app.**

## Open issues
- `src/` package imported by `app.py` is **not in the repo** (`src.data_loader`, `src.visualizations`, …). The app cannot run until it is restored or rebuilt. When restored, `src/visualizations.py` should `from src.theme import COLOR_*, MAP_SCALE, style_*` and drop its own colour constants / `plotly_white` templates.
- Build sandbox had no network (PyPI, GitHub, gov portals blocked): Streamlit run, Plotly tests and data download must be done on a machine with internet.
