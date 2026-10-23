# Style Handoff: Restyle Dashboard to "Neon Night" Theme

**Target:** `app.py` (Streamlit ≥1.30) + `src/visualizations.py` (Plotly charts)
**Reference image:** `docs/style_reference.png` (dark navy CRM dashboard with magenta/cyan neon gradients)
**Scope:** Visual style only. Do not change data loading, calculations, filters, session state, tab structure, chart types, or any Thai/English label text.

---

## 1. Design intent

Move from the current light, forest-green "agri-tech" look to a dark, high-contrast "neon night" dashboard:

- Deep navy canvas, slightly lighter navy cards, no visible borders (use subtle 1px translucent borders only).
- Two signature gradients: **magenta → violet** and **cyan → blue**. Use them on hero KPI cards, bars, area fills, and donut rings.
- Charts glow: smooth (spline) lines, soft gradient fills, faint grid, no heavy axes.
- Text is white for values and muted lavender-grey for labels.
- Rounded cards (16px), generous padding, and a calm dark background so the colour is carried by the data.

---

## 2. Design tokens

Define these once as CSS variables in the existing `<style>` block (inside `st.markdown(..., unsafe_allow_html=True)` near line 165) and as Python constants in `src/visualizations.py`.

### 2.1 Colours

| Token | Hex | Use |
|---|---|---|
| `--bg-app` | `#0F1330` | Main page background |
| `--bg-sidebar` | `#0A0D24` | Sidebar background |
| `--bg-card` | `#181D45` | Cards, chart containers, filter box |
| `--bg-card-hover` | `#1F2554` | Card hover |
| `--bg-input` | `#12163A` | Selectbox, text input, slider track |
| `--border-subtle` | `rgba(255,255,255,0.06)` | Card and input borders |
| `--grid` | `rgba(255,255,255,0.06)` | Chart gridlines |
| `--text-primary` | `#FFFFFF` | KPI values, headings |
| `--text-secondary` | `#B4B9DA` | Body text |
| `--text-muted` | `#7C82AD` | Labels, axis ticks, captions |
| `--accent-magenta` | `#E040FB` | Primary accent, active nav, tooltips |
| `--accent-violet` | `#7C4DFF` | Gradient partner to magenta |
| `--accent-cyan` | `#00E5FF` | Secondary accent, line charts |
| `--accent-blue` | `#2979FF` | Gradient partner to cyan |
| `--accent-sky` | `#4FC3F7` | Third series |
| `--success` | `#00E5A0` | Positive delta |
| `--warning` | `#FFB547` | Warning/caution |
| `--danger` | `#FF4D6D` | Negative delta, high risk |

### 2.2 Gradients

```css
--grad-magenta: linear-gradient(135deg, #E040FB 0%, #7C4DFF 100%);
--grad-cyan:    linear-gradient(135deg, #00E5FF 0%, #2979FF 100%);
--grad-bar:     linear-gradient(180deg, #00E5FF 0%, #7C4DFF 100%); /* vertical bars */
```

### 2.3 Chart colour sequence (Plotly `colorway`)

`["#00E5FF", "#E040FB", "#7C4DFF", "#2979FF", "#4FC3F7", "#FF6EC7", "#00E5A0", "#FFB547"]`

### 2.4 Typography

- Thai + Latin: **Kanit** (Google Fonts, weights 300/400/500/600). Its geometric shapes match the reference. Fallback: `'Sarabun', sans-serif`.
- KPI value: 32–36px, weight 600, white. The unit (ไร่, ตัน, กก./ไร่) is 14px, weight 400, with `opacity: .85`. Reference style: "30 h 15 min".
- KPI label: 13px, weight 500, white at 90% opacity on gradient cards, `--text-muted` on plain cards. No uppercase for Thai text.
- Section headings (`###`, `####`): 16–18px, weight 500, white. Keep the existing emoji.
- Body: 14px, `--text-secondary`. Captions: 12px, `--text-muted`.

### 2.5 Shape and spacing

- Card radius 16px; input/button radius 10px; pills/badges radius 999px.
- Card padding 18–22px; gap between cards 16px.
- Shadow: `0 8px 24px rgba(0,0,0,0.35)`. Gradient cards also get a glow: `0 8px 28px rgba(224,64,251,0.35)` for magenta, `0 8px 28px rgba(0,229,255,0.30)` for cyan.

---

## 3. Streamlit theme

Create `.streamlit/config.toml`. Without it, widgets such as selectbox popovers, the dataframe, and tabs stay light.

```toml
[theme]
base = "dark"
primaryColor = "#E040FB"
backgroundColor = "#0F1330"
secondaryBackgroundColor = "#181D45"
textColor = "#FFFFFF"
font = "sans serif"
```

---

## 4. Component specifications

### 4.1 App shell
- `.stApp` background: `--bg-app`. Optionally add a faint radial glow at the top-left: `radial-gradient(1200px 600px at 10% -10%, rgba(124,77,255,0.18), transparent 60%)`.
- Hide Streamlit's default header bar background: `header[data-testid="stHeader"] { background: transparent; }`.

### 4.2 Sidebar (matches the reference's left nav)
- Background `--bg-sidebar`, right border `--border-subtle`.
- Section titles (e.g. "🛡️ ธรรมาภิบาลข้อมูล"): 11–12px, weight 600, colour `--accent-magenta`, letter-spacing .06em.
- Body text `--text-secondary`; `---` dividers become `--border-subtle`.
- Any active or highlighted item: pill with `--grad-magenta` background and white text.

### 4.3 Main header (`.main-header`)
- Replace the green gradient with `--bg-card` and add a 3px top accent bar using `--grad-magenta`, or use the whole `--grad-magenta` as the background.
- Title white, 24–26px, weight 600; subtitle `--text-muted`.

### 4.4 KPI cards (`.kpi-card`, Tab 1 has 4 of them; same pattern in other tabs)
- Style them like the reference's "Avg First Reply Time" cards:
  - KPI 1 and 3: background `--grad-magenta`; KPI 2 and 4: background `--grad-cyan`. Alternating keeps the row balanced.
  - Text is white on the gradient cards. `.kpi-value` is 32px/600; `.kpi-unit` is smaller and inline.
  - Remove the light border. Add the matching glow shadow.
  - Hover: `transform: translateY(-3px)` and a stronger glow.
- If a tab has more than 4 KPIs, render the extras as plain `--bg-card` cards with a 4px left border in the accent colour.

### 4.5 Delta badges (`.delta-badge-pos/neg/neutral`)
- Pill shape, `background: rgba(0,0,0,0.25)` on gradient cards or `rgba(255,255,255,0.06)` on plain cards. Reference: the "+22%" chips.
- Text colours: pos `--success`, neg `--danger`, neutral `--text-muted`.

### 4.6 Filter bar (`.filter-box`) and inputs
- Container `--bg-card`, radius 16px.
- Selectbox, multiselect, text input, number input: background `--bg-input`, border `--border-subtle`, text white; on focus the border is `--accent-magenta`.
- Multiselect tags: `--grad-magenta`, white text.
- Slider: track `--bg-input`, filled range `--grad-cyan`, thumb white with a cyan glow.
- Primary button (e.g. reset): `--grad-magenta`, white text, no border. Secondary: transparent with `--border-subtle`.

### 4.7 Active-filter summary strip (inline style around line 597, `#F0FDF4`)
- `background: rgba(0,229,255,0.08)`, `border: 1px solid rgba(0,229,255,0.25)`, text `--accent-cyan`; chips inside are pills with `rgba(255,255,255,0.06)`.

### 4.8 Tabs (`st.tabs`)
- Tab list background transparent with a bottom border in `--border-subtle`.
- Inactive tab text `--text-muted`. The active tab text is white with a 3px underline in `--grad-magenta` (override `[data-baseweb="tab-highlight"]`).
- Optional: the active tab gets a pill background `rgba(224,64,251,0.12)`.

### 4.9 Chart containers
- Wrap each `st.plotly_chart` area in a card look by targeting `[data-testid="stPlotlyChart"]`: background `--bg-card`, radius 16px, padding 12px.
- The chart title is the existing `####` heading above it. Keep it, styled white/500.

### 4.10 Callout and advisory boxes (inline styles: `#FEF3C7`, `#F0FDF4`, `#FEF2F2`, `#EFF6FF`, `#F8FAFC`)
Replace the light pastel boxes with dark translucent equivalents:

| Old meaning | New background | Border-left (4px) | Title colour | Body colour |
|---|---|---|---|---|
| Insight / warning (amber) | `rgba(255,181,71,0.10)` | `#FFB547` | `#FFB547` | `--text-secondary` |
| Positive / info (green) | `rgba(0,229,160,0.08)` | `#00E5A0` | `#00E5A0` | `--text-secondary` |
| Risk / danger (red) | `rgba(255,77,109,0.10)` | `#FF4D6D` | `#FF4D6D` | `--text-secondary` |
| Info (blue) | `rgba(41,121,255,0.12)` | `#2979FF` | `#4FC3F7` | `--text-secondary` |
| Neutral note (slate) | `rgba(255,255,255,0.04)` | `--border-subtle` | white | `--text-muted` |

Inline styles should be turned into reusable CSS classes (`.callout-warning`, `.callout-success`, `.callout-danger`, `.callout-info`, `.callout-note`) and then used.

### 4.11 Risk cards (Tab 2, `risk_status[...]["color"]`)
- Card `--bg-card`; risk level shown as a pill. Low uses `--success`, medium uses `--warning`, and high uses `--danger`. The pill background is the same colour at 15% alpha and the text is the full colour.

### 4.12 Data table (`st.dataframe`)
- With the dark theme from section 3 this mostly works. In addition, set the header row to `--bg-input` and use `--text-muted` uppercase-free headers. Row hover is `rgba(255,255,255,0.03)`.

### 4.13 Scrollbars
- 8px wide, thumb `rgba(255,255,255,0.12)`, track transparent.

---

## 5. Plotly chart styling (`src/visualizations.py`)

### 5.1 Register a global template
Add one template and apply it to every `create_*` function. Do not style each chart separately.

```python
import plotly.graph_objects as go
import plotly.io as pio

NEON = {
    "bg": "rgba(0,0,0,0)",
    "grid": "rgba(255,255,255,0.06)",
    "text": "#B4B9DA",
    "muted": "#7C82AD",
    "magenta": "#E040FB", "violet": "#7C4DFF",
    "cyan": "#00E5FF", "blue": "#2979FF", "sky": "#4FC3F7",
    "success": "#00E5A0", "warning": "#FFB547", "danger": "#FF4D6D",
}

pio.templates["neon_night"] = go.layout.Template(
    layout=dict(
        paper_bgcolor=NEON["bg"],
        plot_bgcolor=NEON["bg"],
        font=dict(family="Kanit, Sarabun, sans-serif", color=NEON["text"], size=13),
        title=dict(font=dict(color="#FFFFFF", size=15)),
        colorway=["#00E5FF", "#E040FB", "#7C4DFF", "#2979FF", "#4FC3F7", "#FF6EC7", "#00E5A0", "#FFB547"],
        xaxis=dict(gridcolor=NEON["grid"], zeroline=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=NEON["muted"])),
        yaxis=dict(gridcolor=NEON["grid"], zeroline=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=NEON["muted"])),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=NEON["text"]), orientation="h", y=1.1),
        hoverlabel=dict(bgcolor="#E040FB", bordercolor="#E040FB", font=dict(color="#FFFFFF")),
        margin=dict(l=10, r=10, t=40, b=10),
    )
)
pio.templates.default = "neon_night"
```

Replace the old constants (`COLOR_FOREST_DARK`, `COLOR_FOREST_MED`, `COLOR_SAGE`, `COLOR_MINT`, `COLOR_WARNING`, `COLOR_DANGER`, `COLOR_GOLD`). **Keep the same names** so `app.py` imports don't break, and remap their values:

| Constant | New value |
|---|---|
| `COLOR_FOREST_DARK` | `#7C4DFF` |
| `COLOR_FOREST_MED` | `#E040FB` |
| `COLOR_SAGE` | `#00E5FF` |
| `COLOR_MINT` | `#4FC3F7` |
| `COLOR_WARNING` | `#FFB547` |
| `COLOR_DANGER` | `#FF4D6D` |
| `COLOR_GOLD` | `#FFD166` |

Remove any hard-coded `template="plotly_white"`, `plot_bgcolor="white"`, or similar that would override the new default.

### 5.2 Per chart type

| Chart | Style rule (from reference) |
|---|---|
| **Trend line** (`create_trend_line_chart`, `create_price_trend_chart`) | `line_shape="spline"`, width 3. The primary series is cyan with a glow (draw the same trace underneath at width 10, opacity 0.15). The comparison series is white, dashed, width 2. Markers are hidden except on hover. |
| **Area** (seasonal / rain charts) | Spline line in violet with `fill="tozeroy"` and a semi-transparent fill `rgba(124,77,255,0.35)`. For a second layer, use cyan `rgba(0,229,255,0.25)`. Reference: "First Reply and Full Resolve Time". |
| **Vertical bar** (`create_yoy_bar_chart`, `create_scenario_bar_chart`, `create_soil_suitability_bar_chart`) | Rounded tops (`marker_cornerradius=6`, Plotly ≥5.19). Colour by value with the gradient scale `[[0,"#7C4DFF"],[1,"#00E5FF"]]` to imitate the cyan→purple bars. `bargap=0.45` (thin bars). |
| **Horizontal ranking bar** (`create_ranking_bar_chart`) | Top 10 uses the cyan→blue scale and bottom 10 uses the magenta→violet scale. Value labels go outside the bars in white. |
| **Donut / pie** (`create_cost_breakdown_pie`) | `hole=0.65`. Slices use cyan/blue shades: `#00E5FF, #2979FF, #4FC3F7, #1A237E, #7C4DFF`. White total in the centre via annotation. Slice border `#181D45`, width 3. Legend on the right with round markers. |
| **Single-value ring** (if a ratio KPI is shown) | Two-slice donut, magenta `#E040FB` vs `rgba(255,255,255,0.06)`, `hole=0.75`, with the centre label and value in white. Reference: "Returned Tickets 1,203". |
| **Scatter / quadrant** | Markers in cyan with 0.8 opacity and a white 0.5px outline. Quadrant lines dashed `rgba(255,255,255,0.2)`, quadrant labels `--text-muted`. |
| **Heatmap** (`create_correlation_heatmap`) | Diverging scale `[[0,"#FF4D6D"],[0.5,"#181D45"],[1,"#00E5FF"]]`. White cell text. |
| **Choropleth maps** (`create_thailand_map`, etc.) | Sequential scale `[[0,"#1A1F4D"],[0.35,"#2979FF"],[0.7,"#7C4DFF"],[1,"#E040FB"]]`. Province borders `rgba(255,255,255,0.15)`, width 0.5. `geo.bgcolor` transparent, land/ocean colour `#0F1330`. For mapbox use the `carto-darkmatter` style. Colorbar ticks in `--text-muted`, no outline. Risk maps keep the semantic scale `--success`/`--warning`/`--danger`. |
| **Cost/margin chart** | Cost in magenta, price in cyan, margin bar in `--success` (positive) or `--danger` (negative). |

---

## 6. Implementation notes

1. Put all CSS in the single existing `<style>` block. Add the Kanit import there: `@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');`.
2. Turn repeated inline styles (about 50 `style="..."` occurrences in `app.py`) into classes. Keep the HTML structure, and only swap colours and class names.
3. Use stable Streamlit selectors (`[data-testid="..."]`, `[data-baseweb="..."]`). Avoid auto-generated `.css-xxxx` class names, which change between Streamlit versions.
4. The design is dark-only. Do not add a light-mode toggle unless asked.
5. Keep emoji in headings and labels as they are.

---

## 7. Acceptance criteria

- [ ] No white or light-pastel backgrounds remain anywhere (check all 4 tabs, sidebar, popovers, dataframe, expanders).
- [ ] The KPI cards in each tab use the magenta/cyan gradients with white text.
- [ ] Every Plotly chart uses the `neon_night` template: transparent background, faint grid, neon colorway.
- [ ] Maps use the dark navy→blue→violet→magenta scale and a dark base.
- [ ] Text contrast is at least 4.5:1 for body text (`#B4B9DA` on `#181D45` passes) and at least 3:1 for large KPI numbers on gradients.
- [ ] Thai text renders in Kanit with correct vowel/tone marks (no clipping in KPI values or tabs).
- [ ] No change to numbers, filters, tab names, or behaviour. `pytest` still passes.
- [ ] Layout still works at 1280px and 1920px widths.

---

## 8. Prompt to paste into Antigravity

> Restyle my Streamlit dashboard (`app.py` and `src/visualizations.py`) to match `docs/style_reference.png`, following every rule in `STYLE_HANDOFF.md`. Only visual changes: do not modify data logic, filters, labels, or tab structure. Start by adding `.streamlit/config.toml` and the CSS tokens. Then register the `neon_night` Plotly template and remap the `COLOR_*` constants. Then update each component and chart type in the order listed. Finish by checking all 4 tabs against the acceptance checklist in section 7 and report anything you could not match.
