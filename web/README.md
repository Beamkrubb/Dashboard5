# Web dashboard (published artifact)

Static single-file dashboard (4 tabs, shared filters) built only from downloaded open data.

1. `scripts/fetch_extra.py`, `scripts/fetch_more.py`, `scripts/fetch_more2.py` – download sources into `data/raw/`.
2. `build_web_data.py` – base bundle (`data2.json`): HII rain, DDPM, Agri-Map, NABC prices, ERA5.
3. `rid_grid.py data/raw/D04/rid_irrarea_all.json geo_simplified.json rid_irr_by_province.json` – irrigation-project area per province (0.01° grid).
4. `build_web_data_ext.py <data/raw>` – adds 26-crop production, HII temperature, NSO census, RID, DOAE, OAE household expenses and `data/interim/oae_cost_2567.json` → `data3.json`.
5. `assemble.py` – joins `head.html` + `body.html` + data + `app.js` into `thai_agri_dashboard.html` (Plotly 2.35.2 from cdnjs).
