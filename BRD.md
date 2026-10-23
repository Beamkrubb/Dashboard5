# Business Requirements Document (BRD)
## Thai Agriculture & Climate Intelligence Dashboard

- Version: 2.0
- Status: Implementation specification
- Primary users: นักศึกษา/นักวิเคราะห์ข้อมูล, ผู้สนใจการผลิตสินค้าเกษตร, ผู้วางแผนการผลิต
- Language: Thai-first
- Suggested stack: Python, Streamlit, Pandas, Plotly

## 1. Business Objective
พัฒนา Dashboard เพื่อสำรวจการผลิตสินค้าเกษตรไทย ความแตกต่างระหว่างจังหวัด ประสิทธิภาพการใช้พื้นที่ แนวโน้ม ความผันผวน และความสัมพันธ์กับสภาพอากาศ โดยมี 3 Tabs ที่ตอบโจทย์แยกกันแต่ใช้ data model และ filters ที่เชื่อมโยงกัน

## 2. Data Inputs
### Dataset A: สถิติการผลิตสินค้าเกษตรรายปี 2550–2562
- File: `สถิติการผลิตสินค้าเกษตรรายปี 2550-2562.xlsx`
- ตรวจสอบเบื้องต้น: 11,914 rows, 10 columns
- Fields: `crop_year`, `year`, `product`, `province`, `area_plant_rai`, `area_harvest_rai`, `production_ton`, `yield_per_rai`, `harvest_ratio`, `damaged_area`
- มีหลายระดับพื้นที่และหลายชนิดพืช ต้องป้องกันการรวมซ้ำ

### Dataset B: สถิติปริมาณฝนและอุณหภูมิ
- File: `สถิติปริมาณฝนและอุณหภูมิ(1).xlsx`
- ตรวจสอบเบื้องต้น: 19 rows, 15 columns, ปี 2550–2568
- Fields สำคัญ: `ปี`, `ปริมาณน้ำฝน`, `จำนวนวันที่ฝนตก`, `อุณหภูมิสูงสุด`, `อุณหภูมิต่ำสุด`, `อุณหภูมิเฉลี่ยทั้งปี`, `RH Max`, `RH Min`, `RH Avg`
- หน่วยงานในไฟล์ระบุสถานีอุตุนิยมวิทยาจังหวัดสุพรรณบุรี
- ชุดนี้ไม่ใช่ climate data ระดับประเทศไทย จึงต้องแสดงขอบเขตอย่างชัดเจน


## 2A. Required Nationwide Climate Open Data
The implementation must evaluate and, where the actual resources are accessible and suitable, integrate these sources:

1. **HII — Spatial rainfall, monthly by province:** https://data.go.th/dataset/spatial-rain  
   Monthly provincial rainfall estimated from TMD station observations using IDW. Use for province-level rainfall maps and annual/monthly rainfall trends. Clearly label values as spatially interpolated estimates.

2. **HII — Maximum/minimum temperature, monthly by province:** https://data.go.th/dataset/tmax-tmin  
   Provincial monthly maximum/minimum temperatures analyzed from station data. Use only fields actually present in the downloaded resource; do not invent mean temperature.

3. **TMD — Climate monitoring and monthly climate statistics:** https://data.go.th/dataset/tmdclimatemonthly  
   Use as supplementary climate context or validation after inspecting its resource format and data coverage.

The existing user-provided weather spreadsheet remains a Suphan Buri station dataset, not a national dataset.

### Acceptance criteria for climate data
- Actual resources are downloaded/accessed and schema, units, province coverage, time coverage and license/terms are checked.
- Annual rainfall is calculated by summing monthly rainfall only when the source definition supports that operation. Temperatures are summarized using a documented, source-compatible method and never summed.
- Climate and agricultural data are joined by normalized province and common year only.
- Production comparisons stop at the last overlapping year unless an additional compatible agricultural dataset is integrated.
- Station observations, IDW estimates, forecasts and long-term climate normals are clearly distinguished.
- `data_sources.md` records exact resource links, source agency, license/terms, access date, data period, geography, variables and transformations.
- Missing values are displayed as no data, not zero; no weather data is fabricated or copied from Suphan Buri to other provinces.

## 3. Dashboard Information Architecture — 3 Tabs

## Tab 1: Thailand Overview (ภาพรวมประเทศไทย)
### Business question
**การผลิตสินค้าเกษตรกระจายตัวอย่างไรในประเทศไทย และจังหวัดใดมีผลผลิต/ประสิทธิภาพสูง?**

### Required components
1. KPI cards: total production (ตัน), planted area (ไร่), weighted yield (กก./ไร่), harvest ratio (%)
2. Interactive Thailand provincial choropleth map
3. Map metric selector: production, planted area, weighted yield, harvest ratio
4. Year and crop selectors
5. Top 10 provinces chart for selected metric
6. Top 10 crops by total production
7. National production time-series
8. Province detail table
9. Hover tooltip with province, selected metric, year, product, units
10. Province click cross-filters related charts, cards and tables; reset selection available
11. Legend distinguishes missing data from zero
12. Display source and coverage information

### Map requirements
- Obtain province boundaries from a credible open source with suitable license; document source URL and access date.
- Join province geometry to agricultural records using normalized province names or standard province codes.
- Exclude national/region aggregate rows from provincial mapping.
- Do not double-count national, regional and provincial rows.
- Do not fabricate values for provinces with no records.
- If geography name matching fails, report unmatched names and resolve them; do not silently drop data.
- Climate layers must not be presented province-by-province from the single Suphan Buri station dataset.
- If provincial climate data is added, validate spatial coverage, time coverage, units and license first.

### Success criteria
- Map shows province-level real values and clear no-data state.
- Selecting a province updates relevant KPIs, rankings, trends and tables.
- User can identify what the colors mean from legend and units.
- All metrics respect the current filter state.

## Tab 2: Climate Impact (สภาพอากาศกับผลผลิต)
### Business question
**ปริมาณน้ำฝนและอุณหภูมิสัมพันธ์กับ Yield หรือปริมาณผลผลิตของพืชอย่างไร?**

### Required components
1. KPI: rainfall, rainy days, average temperature, selected crop weighted yield
2. Separate time-series charts for climate and production/yield
3. Scatter plots: rainfall vs yield and temperature vs yield
4. Correlation heatmap for climate variables and yield
5. Display coefficient, method, number of paired years, year range and geographic coverage
6. Filters for product and period; geographic filter only where matched climate data supports it
7. A small joined-data table for traceability
8. Explain that correlation does not establish causation
9. Empty state if observations are insufficient

### Data join constraint
The supplied climate file describes a meteorological station in Suphan Buri. With this file alone, join it only to compatible agricultural data for Suphan Buri, and only for common years. Agriculture ends in 2562; climate years 2563–2568 cannot be paired with this agriculture dataset without a new agricultural source. If reliable province-level climate open data is found, it may extend spatial coverage, but all sources and transformations must be documented.

### Success criteria
- Correlation is calculated only from matched year/geography observations.
- Observation count and time coverage are visible.
- No climate value is falsely assigned to other provinces.
- The user can switch crop and period without stale charts.

## Tab 3: Production & Risk (ประสิทธิภาพและความเสี่ยง)
### Business question
**พืชชนิดใดมีประสิทธิภาพการผลิตสูง มีแนวโน้มเติบโต และมีความผันผวนหรือสัญญาณความเสี่ยงอย่างไร?**

### Required components
1. KPI: production, planted area, harvested area, weighted yield, harvest ratio
2. Rankings: top crops by production, planted area, weighted yield
3. Annual line charts for production, yield and harvest ratio
4. Heatmap by crop/year for YoY or harvest ratio
5. Scatter plot: planted area vs weighted yield, with quadrants based on stated median/percentile thresholds
6. CV ranking with observation count and period
7. Flag harvest ratio below 90% as “สัญญาณที่ควรตรวจสอบ”
8. Unharvested area and annual change
9. Filters by geography, product and period
10. Avoid double-counting across national, region and province rows

### Metric definitions
- Weighted Yield (kg/rai) = `sum(production_ton) * 1000 / sum(area_harvest_rai)`
- Harvest Ratio (%) = `sum(area_harvest_rai) / sum(area_plant_rai) * 100`
- Unharvested Area (rai) = `sum(area_plant_rai) - sum(area_harvest_rai)`
- YoY (%) = `(current - previous) / previous * 100`; if previous is zero/missing, show N/A
- CV (%) = `standard_deviation / mean * 100`; disclose time span and number of years
- Recalculate and validate supplied `yield_per_rai` and `harvest_ratio`

## 4. Global UX and Interaction
- Visual direction inspired by supplied reference: premium agricultural-tech, forest green/sage/off-white, lime accents, rounded cards, sidebar and subtle borders
- Do not copy the reference brand/logo
- Responsive desktop/tablet/mobile layout
- Thai labels first; English metric labels in parentheses where helpful
- Global year and crop filters; geography filters only where valid
- All relevant charts, KPIs, map and tables must share the same filter state
- Add clear reset filters and map-selection reset
- Include units, data source, coverage, observation count and short “How to read this” descriptions
- Avoid clutter: prioritize 4–6 KPI cards, one main visualization, and supporting charts per view
- Provide tooltips and explanatory legends
- No mock values or fabricated insights in production

## 5. Data Quality and Open Data
- Normalize Thai province names and years
- Audit missing values, duplicates, units, invalid numbers and aggregation level
- Preserve raw files unchanged
- Document all additional open data in `data_sources.md`: dataset title, agency, URL, license, access date, period, geographic coverage, transformations
- Potential official sources include Thai Meteorological Department, Office of Agricultural Economics, data.go.th, and an open administrative boundary source; verify actual dataset access and license before use
- If suitable provincial climate data cannot be verified, keep supplied climate data clearly labeled as Suphan Buri only

## 6. Non-functional Requirements
- Python 3.11+, Streamlit, Pandas, NumPy, Plotly
- Map geometry from a verified GeoJSON/TopoJSON source
- Modular code for loading, cleaning, aggregation, metrics, mapping, charts and UI
- Relative paths/configuration; no machine-specific absolute paths
- `requirements.txt`, `README.md`, `handoff.md`, `BRD.md`, `data_sources.md`
- Automated tests for formulas, joins, and double-count prevention
- Accessible contrast, responsive design and meaningful empty/error states

## 7. Acceptance Criteria
- Exactly 3 primary tabs: Thailand Overview, Climate Impact, Production & Risk
- Thailand map has real province-level data, legend, hover details and missing-data state
- Clicking a province updates connected visualizations
- All charts and KPIs react to relevant filters
- Climate analysis uses only compatible spatial/time observations
- No fabricated values, false causal claims, or double-counting
- Key metrics are unit-tested or independently validated
- App runs according to README and tests pass
- Sources and data limitations are visible to users

## 8. GitHub and Delivery
- Inspect existing repo, branch, status and remote first
- Preserve unrelated work; no force push and no visibility changes
- Do not commit secrets, tokens or environment files
- Run tests and launch the app before reporting completion
- Commit with a descriptive message and push to the existing remote/appropriate branch
- Deploy only if authorized access/integration is available; verify the actual URL
- Final report must include repository URL, branch, commit hash, tests, run command, and verified deployment URL if applicable

## 9. Deliverables
- Working 3-tab dashboard
- Interactive Thailand map
- `handoff.md`, `BRD.md`, `README.md`, `data_sources.md`, `requirements.txt`
- Automated tests and verified run instructions
- GitHub push status and deployment status (only when actually completed)
