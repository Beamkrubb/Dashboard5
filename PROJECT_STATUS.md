# Project Status

Legend: ✅ done · 🔄 in progress · ⏳ pending · ⛔ blocked

_Last updated: 2026-10-23_

## Step log

| # | Step | Spec | Status | Notes |
|---|---|---|---|---|
| 0 | Project README + status file, initial commit | both | ✅ | README built from `handoff_n.md` + `STYLE_HANDOFF.md` |
| 1 | Streamlit dark theme (`.streamlit/config.toml`) | STYLE §3 | ⏳ | |
| 2 | Design tokens + global CSS (Kanit, cards, sidebar, tabs, inputs) | STYLE §2, §4 | ⏳ | |
| 3 | KPI cards → gradient cards, delta badges | STYLE §4.4–4.5 | ⏳ | |
| 4 | Inline light styles → dark callout classes | STYLE §4.7, §4.10 | ⏳ | |
| 5 | Plotly `neon_night` template + colour constants | STYLE §5 | ⏳ | |
| 6 | Province lookup from GeoJSON (`pro_code`) | handoff D10 | ⏳ | |
| 7 | Download script for D01–D10 | handoff steps 1 | ⏳ | |
| 8 | Raw → tidy cleaning pipeline (`data/clean/*.csv`) | handoff step 2 | ⏳ | |
| 9 | Verify app run + acceptance checklist | STYLE §7 | ⏳ | |

## Open issues
- `src/` package imported by `app.py` is **not in the repo** (`src.data_loader`, `src.visualizations`, …). The app cannot run until it is restored or rebuilt.
