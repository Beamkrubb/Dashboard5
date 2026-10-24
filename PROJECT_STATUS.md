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
| 6 | Province lookup from GeoJSON (`pro_code`) | handoff D10 | ✅ | `pipeline/province.py`: 77 DOPA codes, OAE 4-region split, Thai/English alias matching, GeoJSON `crs` cleanup + centroids. Static `data/clean/province_lookup.csv` committed; centroids are added when the GeoJSON is downloaded |
| 7 | Download script for D01–D10 | handoff steps 1 | ✅ | `scripts/download_data.py` (+ `pipeline/sources.py` registry). Auto: D01 (4 crops), D02 NABC API, D05 (15 files), D10, ERA5 via flags, D09 with TMD key. Manual steps printed for D01 rest/rice, D03, D04, D06, D07, D08. Writes `data/raw/manifest.json` |
| 8 | Raw → tidy cleaning pipeline (`data/clean/*.csv`) | handoff step 2 | ✅ | Run on real downloads 2026-10-23: production.csv 33,726 rows (cassava, maize, rubber, oil palm · 1980–2025 · 76 provinces), farmgate_weekly.csv 1,658 rows (Hom Mali + white rice, 2011-01 → 2026-10), suitability.csv 1,997 rows (14 crops), climate_monthly.csv 924 rows (ERA5 2018), rain_annual.csv 77. Check: cassava 2019 = 31,079,966 t (matches OAE national total). D03/D04/D06/D07-HII/D08 still need manual files |
| 9 | Verify app run + acceptance checklist | STYLE §7 | ⛔ | `run_dashboard.bat` installs deps, downloads, builds and serves Streamlit at http://127.0.0.1:8050 ✅ — app stops at `ModuleNotFoundError: src.data_loader` (src/ missing) |

## Verification log
- 2026-10-23 · Phase 1: `python -m py_compile app.py src/theme.py` ✅ · `tests/test_theme.py` 4 pass, 2 skipped (Plotly not installable in build sandbox) · CSS rendered on a static mock of the app's HTML (header, filter chips, KPI rows, risk cards, 5 callouts) ✅. **Not yet verified inside a running Streamlit app.**
- 2026-10-23 · Phase 2: `tests/test_pipeline.py` 10/10 pass (Python 3.13 sandbox and Python 3.10 on the project machine) · end-to-end `build_clean_data.py` run on synthetic raw files ✅ · `download_data.py` dry run offline: all failures recorded in manifest, no crash ✅. Fixed during testing: CSVs with title rows above the header crashed the pandas reader; unmatched province names were not reported.

- 2026-10-23 · Real run on project PC (Windows, Python 3.12): pip install ✅, download 107 files / 1 error (RID 2566 PDF moved, 404) ✅, build ✅, Streamlit up on 127.0.0.1:8050 ✅. Parsers fixed for the real OAE attribute/value layout and NABC weekly price fields (`year_th, month, week, value` in THB/ton → THB/kg). D02 glutinous rice product name returns 0 records. 12/12 tests pass.

## Next steps
1. On a machine with internet: `pip install -r requirements.txt` → `python scripts/download_data.py --era5-2018` → do the printed manual downloads → `python scripts/build_clean_data.py`.
2. Read `data/clean/cleaning_report.json`; tighten `METRIC_KEYWORDS` / province aliases for any unmatched names or columns.
3. Restore or rebuild `src/` (data_loader, data_cleaning, feature_engineering, analytics, visualizations, filters) and point the loaders at `data/clean/*.csv`.
4. In `src/visualizations.py`, use `src/theme.py` (`COLOR_*`, scales, `style_*` helpers), then run `streamlit run app.py` and walk the STYLE §7 checklist (step 9).

## Open issues
- `src/` package imported by `app.py` is **not in the repo** (`src.data_loader`, `src.visualizations`, …). The app cannot run until it is restored or rebuilt. When restored, `src/visualizations.py` should `from src.theme import COLOR_*, MAP_SCALE, style_*` and drop its own colour constants / `plotly_white` templates.
- Build sandbox had no network (PyPI, GitHub, gov portals blocked): Streamlit run, Plotly tests and data download must be done on a machine with internet.

## Web dashboard v4 — objectives 1–7 (2026-10-24)
| Objective | Status | Data used |
|---|---|---|
| 1. 77 provinces × 26 crops, shortcuts | ✅ | OAE `production_y_oae.csv` (data.go.th oae0001) 2550–2562, 10,656 province rows; rubber/oil palm 2562 filled from OAE Catalog province files (145 rows, flagged on page) |
| 2–3. Shared global filters, Reset, active-filter badges | ✅ | Region → Province (dynamic), Crop (26, grouped + 4 shortcut chips), Year 2550–2562, Metric; × on each badge resets that filter |
| 4. Choropleth + trend | ✅ | Overview map + 2550–2562 trend follow all filters |
| 5. Climate vs yield | ✅ | HII IDW rain 2561–2562 (77), May–Oct season rain, HII monthly temperature 2561–2562 (64–65 provinces), ERA5 2550–2562; Pearson/Spearman/p/N + OLS. TMD stations: registration required → empty state |
| 6. Production drivers | ✅ | RID GIS `virrarea_all` (599 large/medium projects) rasterised per province (`web/rid_grid.py`, 23.9 M rai); NSO census machinery/fertiliser/holding land; Agri-Map; DDPM 2562; DOAE in vs out irrigation-zone affected area (year not stated in source) |
| 7. Farm economics | ✅ | NABC weekly prices; OAE cost/price/net per ton 2565–2567 for 21 of 26 crops (transcribed from the OAE 2567 commodity PDF, `data/interim/oae_cost_2567.json`, every row checked net = price − cost); OAE household cash-expense structure (labelled as household, not per-crop); calculator separates farmer inputs from government benchmarks |

Known gaps (shown as "ไม่มีข้อมูล"): OAE cost for มะนาว, มะเขือเทศ, หน่อไม้ฝรั่ง, ข้าวโพดหวาน, ข้าวโพดฝักอ่อน; per-crop cost breakdown (fertiliser/labour) is not published as open data; HII temperature misses ~12 provinces; OCSB sugarcane download failed (not in the 26-crop set).
