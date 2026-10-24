# Web dashboard (published artifact)

Static, single-file version of the dashboard (4 tabs) built from real open data.

- `build_web_data.py` – builds the embedded data bundle from `data/clean/*` and `data/raw/*`
  (OAE production, NABC prices, HII rain, DDPM flood/drought 2562, LDD Agri-Map, ERA5 temperature).
  Run it from a folder that contains `src/`, `pipeline/`, `data/clean/`, `raw/` (copy of `data/raw/`).
- `head.html`, `body.html`, `app.js` – page parts; `thai_agri_dashboard.html` – assembled page (Plotly 2.35.2 from cdnjs).
- Fetch extra sources first with `fetch_extra.bat` (`scripts/fetch_extra.py`).
