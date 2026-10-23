# Thai Agriculture & Climate Intelligence Dashboard
ระบบสนับสนุนการตัดสินใจเพื่อเกษตรกรไทย — interactive dashboard of Thai agricultural production, prices, costs, irrigation, soil suitability, disasters and rainfall at province level (77 provinces).

This README is built from the two working specs in this repo:

| Spec | What it governs |
|---|---|
| [`handoff_n.md`](handoff_n.md) | **Data**: the 10 open datasets (D01–D10), where to get them, their status, substitutes, the shared tidy schema and data conventions |
| [`STYLE_HANDOFF.md`](STYLE_HANDOFF.md) | **Look & feel**: the "Neon Night" dark theme (reference: [`docs/style_reference.png`](docs/style_reference.png)) |

Progress is tracked step by step in [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

---

## Stack
- Python 3.10+ · Streamlit ≥1.30 · Pandas · NumPy · Plotly ≥5.19 · openpyxl · SciPy
- Entry point: `app.py` (4 tabs: Overview · Climate & Advisory · Market & Prices · Production Economics)

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py    # needs internet access to Thai gov portals
python scripts/build_clean_data.py # raw -> data/clean/*.csv (tidy schema)
streamlit run app.py
```

## Repository layout
```
app.py                     Streamlit app (UI + layout)
src/                       data_loader, data_cleaning, feature_engineering,
                           analytics, visualizations, filters, theme
.streamlit/config.toml     Streamlit dark theme (Neon Night)
scripts/                   download + cleaning pipeline
data/raw/                  files exactly as downloaded (not committed)
data/clean/                tidy CSVs used by the app
docs/                      style reference image
handoff_n.md               data handoff spec
STYLE_HANDOFF.md           style handoff spec
PROJECT_STATUS.md          step-by-step progress log
BRD.md                     business requirements
```

## Data sources (summary of `handoff_n.md`)

| ID | Dataset | Owner | Status | Primary source |
|---|---|---|---|---|
| D01 | Annual crop production, by province | OAE (สศก.) | ✅ usable | catalog.oae.go.th `dataoaeXX04` |
| D02 | Weekly farm-gate prices | OAE (สศก.) | ⚠️ partial (JSON API) | catalog.oae.go.th `weekly_price_*` → agriapi.nabc.go.th |
| D03 | Production cost & machinery | OAE (สศก.) | 🔁 substitute | NSO agricultural census 2023 / manual OAE tables |
| D04 | Irrigated area by province | RID & OAE | 🔁 substitute | RID annual report PDFs |
| D05 | Soil suitability (Agri-Map S1/S2/S3/N) | LDD | ✅ usable | lddcatalog.ldd.go.th `lpd` |
| D06 | Disaster-affected farm area | DOAE & DDPM | 🔁 substitute | catalog.disaster.go.th `dpm-gd027/028/030` |
| D07 | Monthly provincial rainfall (IDW) | HII (สสน.) | ⚠️ partial (from 2019) | data.go.th `spatial-rain` |
| D08 | Long-term national rainfall | HII (สสน.) | 🔁 substitute | World Bank CCKP (CRU) / Open-Meteo ERA5 |
| D09 | Agro-met station observations | TMD | ⚠️ partial (registration) | data.tmd.go.th API |
| D10 | Province boundaries | DOPA / GISTDA | ✅ usable | OpenGISData-Thailand `provinces.geojson` |

### Data conventions
- **Years:** Thai sources use B.E.; `year_ce = year_be − 543`. Crop years such as `2562/63` keep both `crop_year_label` and `year_ce` (start year).
- **Province key:** `pro_code` (2-digit DOPA code) everywhere; names are normalized via `data/clean/province_lookup.csv`. Bueng Kan (บึงกาฬ) exists only from 2011.
- **Units:** area = rai, production = ton, yield = kg/rai, price = THB/kg, cost = THB/rai, rain = mm.
- **Encodings:** Thai CSVs may be UTF-8 (BOM) or TIS-620/cp874.
- **Trust files, not catalog metadata** (the "latest year" field is often wrong).
- **Provenance:** every clean row carries `source_id` and `source_url`. Missing values stay missing (never zero, never copied between provinces).

### Tidy schema (`data/clean/*.csv`)
```
province_code,province_th,year_ce,period,crop,metric,value,unit,source_id,source_url
```

## Visual style (summary of `STYLE_HANDOFF.md`)
- Dark navy canvas `#0F1330`, cards `#181D45`, sidebar `#0A0D24`
- Signature gradients: magenta→violet `#E040FB→#7C4DFF`, cyan→blue `#00E5FF→#2979FF`
- Font: Kanit (fallback Sarabun)
- KPI cards alternate magenta/cyan gradients with white values
- Global Plotly template `neon_night` with a transparent background, faint grid and neon colorway; maps use a navy→blue→violet→magenta scale
- Styling only: no changes to data logic, filters, labels or tab structure

## Known limitations
- Several government portals block automated download (robots.txt, ThaiD login, API registration). Some files must be downloaded manually in a browser into `data/raw/`; see `handoff_n.md` › ข้อจำกัด.
- Substitute sources (D03, D04, D06, D08) are labelled as such in the dashboard.

## License & attribution
Code: see repository owner. Data remains under each provider's terms (e.g. LDD CC BY-ND, HII CC BY-NC, Open-Meteo/ERA5 attribution). Cite sources as listed in `handoff_n.md`.
