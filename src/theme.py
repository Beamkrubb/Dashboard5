"""
Neon Night theme for the Thai Agriculture & Climate Intelligence Dashboard.

Single source of truth for the visual style described in STYLE_HANDOFF.md:
  * design tokens (colours, gradients, fonts)               -> NEON, GRADIENTS
  * colour constants imported by app.py via visualizations  -> COLOR_*
  * Plotly colour scales and the global "neon_night" template
  * the global CSS injected into Streamlit                  -> THEME_CSS
  * small helpers to restyle Plotly figures per chart type   -> style_*()

Usage in app.py:
    from src.theme import inject_theme_css, register_plotly_template
    inject_theme_css()
    register_plotly_template()

Usage in src/visualizations.py:
    from src.theme import (COLOR_FOREST_DARK, COLOR_FOREST_MED, COLOR_SAGE, COLOR_MINT,
                           COLOR_WARNING, COLOR_DANGER, COLOR_GOLD, NEON,
                           MAP_SCALE, BAR_SCALE, BAR_SCALE_MAGENTA, DIVERGING_SCALE,
                           DONUT_COLORS, RISK_SCALE, style_line_glow, style_bars,
                           style_donut, style_map)

This module only changes appearance. It must never touch data or calculations.
"""
from __future__ import annotations

from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# 1. Design tokens (STYLE_HANDOFF.md §2)
# ---------------------------------------------------------------------------
NEON = {
    "bg_app": "#0F1330",
    "bg_sidebar": "#0A0D24",
    "bg_card": "#181D45",
    "bg_card_hover": "#1F2554",
    "bg_input": "#12163A",
    "border": "rgba(255,255,255,0.06)",
    "grid": "rgba(255,255,255,0.06)",
    "text": "#FFFFFF",
    "text_secondary": "#B4B9DA",
    "muted": "#7C82AD",
    "magenta": "#E040FB",
    "violet": "#7C4DFF",
    "cyan": "#00E5FF",
    "blue": "#2979FF",
    "sky": "#4FC3F7",
    "pink": "#FF6EC7",
    "success": "#00E5A0",
    "warning": "#FFB547",
    "danger": "#FF4D6D",
    "gold": "#FFD166",
}

GRADIENTS = {
    "magenta": "linear-gradient(135deg, #E040FB 0%, #7C4DFF 100%)",
    "cyan": "linear-gradient(135deg, #00E5FF 0%, #2979FF 100%)",
    "bar": "linear-gradient(180deg, #00E5FF 0%, #7C4DFF 100%)",
}

FONT_FAMILY = "Kanit, Sarabun, sans-serif"

COLORWAY = [
    NEON["cyan"], NEON["magenta"], NEON["violet"], NEON["blue"],
    NEON["sky"], NEON["pink"], NEON["success"], NEON["warning"],
]

# Legacy constant names kept so existing imports keep working (STYLE §5.1).
COLOR_FOREST_DARK = NEON["violet"]
COLOR_FOREST_MED = NEON["magenta"]
COLOR_SAGE = NEON["cyan"]
COLOR_MINT = NEON["sky"]
COLOR_WARNING = NEON["warning"]
COLOR_DANGER = NEON["danger"]
COLOR_GOLD = NEON["gold"]

# Plotly colour scales (STYLE §5.2)
MAP_SCALE = [[0.0, "#1A1F4D"], [0.35, NEON["blue"]], [0.7, NEON["violet"]], [1.0, NEON["magenta"]]]
BAR_SCALE = [[0.0, NEON["violet"]], [1.0, NEON["cyan"]]]          # cyan -> purple bars
BAR_SCALE_CYAN = [[0.0, NEON["blue"]], [1.0, NEON["cyan"]]]       # top-10 ranking
BAR_SCALE_MAGENTA = [[0.0, NEON["violet"]], [1.0, NEON["magenta"]]]  # bottom-10 ranking
DIVERGING_SCALE = [[0.0, NEON["danger"]], [0.5, NEON["bg_card"]], [1.0, NEON["cyan"]]]
RISK_SCALE = [[0.0, NEON["success"]], [0.5, NEON["warning"]], [1.0, NEON["danger"]]]
DONUT_COLORS = [NEON["cyan"], NEON["blue"], NEON["sky"], "#1A237E", NEON["violet"], NEON["magenta"]]

# Callout variants used by app.py (STYLE §4.10)
CALLOUT_VARIANTS = ("warning", "success", "danger", "info", "note")


# ---------------------------------------------------------------------------
# 2. Global CSS (STYLE §2, §4)
# ---------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&family=Sarabun:wght@300;400;500;600;700&display=swap');

:root {
  --bg-app:#0F1330; --bg-sidebar:#0A0D24; --bg-card:#181D45; --bg-card-hover:#1F2554; --bg-input:#12163A;
  --border-subtle:rgba(255,255,255,0.06); --grid:rgba(255,255,255,0.06);
  --text-primary:#FFFFFF; --text-secondary:#B4B9DA; --text-muted:#7C82AD;
  --accent-magenta:#E040FB; --accent-violet:#7C4DFF; --accent-cyan:#00E5FF; --accent-blue:#2979FF; --accent-sky:#4FC3F7;
  --success:#00E5A0; --warning:#FFB547; --danger:#FF4D6D;
  --grad-magenta:linear-gradient(135deg,#E040FB 0%,#7C4DFF 100%);
  --grad-cyan:linear-gradient(135deg,#00E5FF 0%,#2979FF 100%);
  --grad-bar:linear-gradient(180deg,#00E5FF 0%,#7C4DFF 100%);
  --shadow-card:0 8px 24px rgba(0,0,0,0.35);
  --glow-magenta:0 8px 28px rgba(224,64,251,0.35);
  --glow-cyan:0 8px 28px rgba(0,229,255,0.30);
  --radius-card:16px; --radius-input:10px;
}

/* ---------- App shell (4.1) ---------- */
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: 'Kanit', 'Sarabun', sans-serif;
}
.stApp {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(124,77,255,0.18), transparent 60%),
    var(--bg-app);
  color: var(--text-secondary);
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppViewContainer"] .main .block-container,
[data-testid="stMainBlockContainer"] { padding-top: 2rem; }
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
  color: var(--text-primary) !important; font-weight: 500; letter-spacing: -0.2px;
}
.stMarkdown h3 { font-size: 18px; }
.stMarkdown h4 { font-size: 16px; }
p, li, label, .stMarkdown { color: var(--text-secondary); }
.stMarkdown strong, .stMarkdown b { color: var(--text-primary); }
[data-testid="stCaptionContainer"], .stCaption { color: var(--text-muted) !important; }
hr { border-color: var(--border-subtle) !important; }
a { color: var(--accent-cyan); }

/* ---------- Sidebar (4.2) ---------- */
section[data-testid="stSidebar"] {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] h3 { color: var(--text-primary) !important; font-size: 16px; }
section[data-testid="stSidebar"] h4 {
  color: var(--accent-magenta) !important; font-size: 12px !important; font-weight: 600;
  letter-spacing: .06em;
}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] li { color: var(--text-secondary); font-size: 13.5px; }

/* ---------- Main header (4.3) ---------- */
.main-header {
  position: relative; overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  padding: 24px 28px 22px; border-radius: var(--radius-card);
  margin-bottom: 20px; box-shadow: var(--shadow-card);
}
.main-header::before {
  content: ""; position: absolute; left: 0; top: 0; right: 0; height: 3px; background: var(--grad-magenta);
}
.main-header h1 { margin: 0; font-size: 24px; font-weight: 600; color: var(--text-primary) !important; line-height: 1.35; }
.main-header p { margin: 6px 0 0; font-size: 13.5px; color: var(--text-muted); }

/* ---------- KPI cards (4.4) ---------- */
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-left: 4px solid var(--accent-cyan);
  border-radius: var(--radius-card);
  padding: 18px 20px;
  box-shadow: var(--shadow-card);
  transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
  height: 100%;
}
.kpi-card:hover { transform: translateY(-3px); background: var(--bg-card-hover); }
.kpi-card.kpi-compact { padding: 12px 16px; }
.kpi-card.kpi-magenta, .kpi-card.kpi-cyan { border: 0; }
.kpi-card.kpi-magenta { background: var(--grad-magenta); box-shadow: var(--glow-magenta); }
.kpi-card.kpi-cyan    { background: var(--grad-cyan);    box-shadow: var(--glow-cyan); }
.kpi-card.kpi-magenta:hover { background: var(--grad-magenta); box-shadow: 0 12px 36px rgba(224,64,251,0.5); }
.kpi-card.kpi-cyan:hover    { background: var(--grad-cyan);    box-shadow: 0 12px 36px rgba(0,229,255,0.45); }
.kpi-label { font-size: 13px; font-weight: 500; color: var(--text-muted); margin-bottom: 8px; }
.kpi-value { font-size: 32px; font-weight: 600; color: var(--text-primary); line-height: 1.2; font-variant-numeric: tabular-nums; }
.kpi-value.kpi-value-sm { font-size: 20px; }
.kpi-unit { font-size: 14px; font-weight: 400; opacity: .85; margin-left: 6px; color: inherit; }
.kpi-sub { font-size: 12px; margin-top: 8px; font-weight: 500; }
.kpi-status { font-weight: 600; font-size: 14px; }
.kpi-desc { font-size: 11.5px; color: var(--text-muted); margin-top: 6px; line-height: 1.5; }
.kpi-magenta .kpi-label, .kpi-cyan .kpi-label { color: rgba(255,255,255,0.9); }
.kpi-magenta .kpi-value, .kpi-cyan .kpi-value, .kpi-magenta .kpi-unit, .kpi-cyan .kpi-unit { color: #FFFFFF; }

/* ---------- Delta badges (4.5) ---------- */
.delta-badge-pos, .delta-badge-neg, .delta-badge-neutral {
  display: inline-block; padding: 2px 10px; border-radius: 999px; font-weight: 600; font-size: 11.5px;
  background: rgba(255,255,255,0.06);
}
.delta-badge-pos { color: var(--success); background: rgba(0,229,160,0.12); }
.delta-badge-neg { color: var(--danger); background: rgba(255,77,109,0.14); }
.delta-badge-neutral { color: var(--text-muted); font-weight: 500; }
.kpi-magenta .delta-badge-pos, .kpi-magenta .delta-badge-neg, .kpi-magenta .delta-badge-neutral,
.kpi-cyan .delta-badge-pos, .kpi-cyan .delta-badge-neg, .kpi-cyan .delta-badge-neutral {
  background: rgba(0,0,0,0.28); color: #FFFFFF;
}
/* on gradients, semantic colour moves to a dot so text keeps >= 4.5:1 contrast */
.kpi-magenta .delta-badge-pos::before, .kpi-cyan .delta-badge-pos::before,
.kpi-magenta .delta-badge-neg::before, .kpi-cyan .delta-badge-neg::before {
  content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  margin-right: 6px; vertical-align: 1px; background: var(--success);
}
.kpi-magenta .delta-badge-neg::before, .kpi-cyan .delta-badge-neg::before { background: var(--danger); }
.kpi-magenta .delta-badge-neutral, .kpi-cyan .delta-badge-neutral { color: rgba(255,255,255,0.88); }

/* ---------- Filter bar & inputs (4.6) ---------- */
.filter-box, .advisory-card {
  background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-card);
  padding: 16px 20px 10px; margin-bottom: 14px; box-shadow: var(--shadow-card);
}
.advisory-header { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"],
.stTextInput input, .stNumberInput input, .stDateInput input, textarea {
  background: var(--bg-input) !important; color: var(--text-primary) !important;
  border-color: var(--border-subtle) !important; border-radius: var(--radius-input) !important;
}
[data-baseweb="select"] > div:focus-within, [data-baseweb="input"]:focus-within { border-color: var(--accent-magenta) !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--bg-card) !important; }
[data-baseweb="menu"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: rgba(224,64,251,0.12) !important; }
[data-baseweb="tag"] { background: var(--grad-magenta) !important; color: #fff !important; border-radius: 999px !important; }
.stSlider [role="slider"] { background: #FFFFFF !important; box-shadow: 0 0 0 4px rgba(0,229,255,0.25); }
.stSlider [data-baseweb="slider"] div[style*="background"] { border-radius: 999px; }
.stButton > button, .stDownloadButton > button {
  border-radius: var(--radius-input); border: 1px solid var(--border-subtle);
  background: transparent; color: var(--text-primary);
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--accent-magenta); color: var(--text-primary); }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background: var(--grad-magenta); border: 0; color: #fff; box-shadow: var(--glow-magenta);
}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label { color: var(--text-secondary); }

/* ---------- Active filter strip (4.7) ---------- */
.filter-chips {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  background: rgba(0,229,255,0.08); border: 1px solid rgba(0,229,255,0.25);
  border-radius: 12px; padding: 8px 14px; margin-bottom: 20px;
  font-size: 12.5px; color: var(--accent-cyan);
}
.filter-chips .chip-label { font-weight: 600; }
.filter-chips .chip {
  background: rgba(255,255,255,0.06); border-radius: 999px; padding: 2px 10px; color: var(--text-secondary);
}
.filter-chips .chip b { color: var(--text-primary); }
.accent-text { font-size: 16px; font-weight: 600; color: var(--accent-cyan); }

/* ---------- Tabs (4.8) ---------- */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid var(--border-subtle); gap: 4px; }
.stTabs [data-baseweb="tab"] {
  color: var(--text-muted); background: transparent; border-radius: 10px 10px 0 0; padding: 10px 14px;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary); }
.stTabs [aria-selected="true"] { color: var(--text-primary) !important; background: rgba(224,64,251,0.12); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--grad-magenta) !important; height: 3px; }
.stTabs [data-baseweb="tab-border"] { background: transparent; }

/* ---------- Chart containers (4.9) ---------- */
[data-testid="stPlotlyChart"] {
  background: var(--bg-card); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card); padding: 12px; box-shadow: var(--shadow-card);
}

/* ---------- Callouts (4.10) ---------- */
.callout {
  border-left: 4px solid var(--border-subtle); border-radius: 10px;
  padding: 12px 16px; margin: 10px 0 16px; font-size: 13px; line-height: 1.6;
  color: var(--text-secondary); background: rgba(255,255,255,0.04);
}
.callout .callout-title { display: inline-block; font-weight: 600; font-size: 13.5px; margin-bottom: 4px; color: var(--text-primary); }
.callout .callout-body { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.callout .callout-foot { font-size: 11.5px; color: var(--text-muted); margin-top: 6px; font-style: italic; }
.callout .callout-row { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.callout.small { font-size: 12px; }
.callout-warning { background: rgba(255,181,71,0.10); border-left-color: var(--warning); }
.callout-warning .callout-title { color: var(--warning); }
.callout-success { background: rgba(0,229,160,0.08); border-left-color: var(--success); }
.callout-success .callout-title { color: var(--success); }
.callout-danger { background: rgba(255,77,109,0.10); border-left-color: var(--danger); }
.callout-danger .callout-title { color: var(--danger); }
.callout-info { background: rgba(41,121,255,0.12); border-left-color: var(--accent-blue); }
.callout-info .callout-title { color: var(--accent-sky); }
.callout-note { background: rgba(255,255,255,0.04); border-left-color: rgba(255,255,255,0.12); color: var(--text-muted); }

/* Streamlit native alerts (st.info / st.warning / st.success / st.error) */
[data-testid="stAlert"], .stAlert { background: rgba(41,121,255,0.12) !important; border-radius: 12px; color: var(--text-secondary); }

/* ---------- Data table (4.12) ---------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--border-subtle); border-radius: var(--radius-card); overflow: hidden;
}

/* ---------- Expanders & metrics ---------- */
[data-testid="stExpander"] { background: var(--bg-card); border: 1px solid var(--border-subtle) !important; border-radius: 12px; }
[data-testid="stMetricValue"] { color: var(--text-primary); }
[data-testid="stMetricLabel"] { color: var(--text-muted); }

/* ---------- Scrollbars (4.13) ---------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 999px; }
::-webkit-scrollbar-track { background: transparent; }
</style>
"""


def inject_theme_css() -> None:
    """Inject THEME_CSS into the running Streamlit page."""
    import streamlit as st  # local import keeps this module importable without Streamlit

    st.markdown(THEME_CSS, unsafe_allow_html=True)


def kpi_variant(index: int) -> str:
    """Alternating gradient class for a row of KPI cards: 0,2 -> magenta; 1,3 -> cyan."""
    return "kpi-magenta" if index % 2 == 0 else "kpi-cyan"


# ---------------------------------------------------------------------------
# 3. Plotly template (STYLE §5.1)
# ---------------------------------------------------------------------------
TEMPLATE_NAME = "neon_night"


def build_plotly_template():
    """Return the neon_night plotly Template object."""
    import plotly.graph_objects as go

    axis = dict(
        gridcolor=NEON["grid"], zeroline=False, linecolor="rgba(0,0,0,0)",
        tickfont=dict(color=NEON["muted"]), title=dict(font=dict(color=NEON["muted"])),
    )
    return go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_FAMILY, color=NEON["text_secondary"], size=13),
            title=dict(font=dict(color=NEON["text"], size=15)),
            colorway=COLORWAY,
            xaxis=axis,
            yaxis=axis,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=NEON["text_secondary"]),
                        orientation="h", y=1.1),
            hoverlabel=dict(bgcolor=NEON["magenta"], bordercolor=NEON["magenta"],
                            font=dict(color="#FFFFFF", family=FONT_FAMILY)),
            coloraxis=dict(colorscale=MAP_SCALE,
                           colorbar=dict(outlinewidth=0, tickfont=dict(color=NEON["muted"]),
                                         title=dict(font=dict(color=NEON["muted"])))),
            geo=dict(bgcolor="rgba(0,0,0,0)", landcolor=NEON["bg_app"], oceancolor=NEON["bg_app"],
                     showocean=True, lakecolor=NEON["bg_app"], showframe=False,
                     subunitcolor="rgba(255,255,255,0.15)", countrycolor="rgba(255,255,255,0.15)"),
            margin=dict(l=10, r=10, t=40, b=10),
        )
    )


def register_plotly_template(make_default: bool = True) -> None:
    """Register neon_night with plotly.io and (by default) make it the default template."""
    import plotly.io as pio

    pio.templates[TEMPLATE_NAME] = build_plotly_template()
    if make_default:
        pio.templates.default = TEMPLATE_NAME


# ---------------------------------------------------------------------------
# 4. Per-chart helpers (STYLE §5.2). Each one mutates and returns the figure.
# ---------------------------------------------------------------------------
def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def style_line_glow(fig, primary_index: int = 0, dashed_indices: Iterable[int] = ()):
    """Spline lines, primary series cyan with a soft glow underlay, others dashed white."""
    import plotly.graph_objects as go

    dashed = set(dashed_indices)
    glows = []
    for i, tr in enumerate(fig.data):
        if getattr(tr, "type", None) != "scatter":
            continue
        tr.update(line_shape="spline", mode="lines")
        if i == primary_index:
            tr.update(line=dict(color=NEON["cyan"], width=3))
            glows.append(go.Scatter(x=tr.x, y=tr.y, mode="lines", line_shape="spline",
                                    line=dict(color=NEON["cyan"], width=10), opacity=0.15,
                                    hoverinfo="skip", showlegend=False))
        elif i in dashed:
            tr.update(line=dict(color="#FFFFFF", width=2, dash="dash"))
    for g in glows:  # draw glow underneath
        fig.add_trace(g)
        fig.data = (fig.data[-1],) + fig.data[:-1]
    return fig


def style_area(fig, colors: Optional[list] = None):
    """Spline area chart with translucent violet/cyan fills."""
    colors = colors or [NEON["violet"], NEON["cyan"], NEON["magenta"]]
    for i, tr in enumerate(fig.data):
        c = colors[i % len(colors)]
        tr.update(line_shape="spline", fill="tozeroy", line=dict(color=c, width=2),
                  fillcolor=_hex_to_rgba(c, 0.35 if i == 0 else 0.25))
    return fig


def style_bars(fig, scale=None, horizontal: bool = False, label_outside: bool = False):
    """Thin, rounded bars coloured by value with a neon gradient scale."""
    scale = scale or BAR_SCALE
    for tr in fig.data:
        if getattr(tr, "type", None) != "bar":
            continue
        vals = tr.x if horizontal else tr.y
        upd = dict(marker_line_width=0)
        if vals is not None and len(vals) and all(isinstance(v, (int, float)) for v in vals if v is not None):
            upd.update(marker=dict(color=list(vals), colorscale=scale, line=dict(width=0)))
        if label_outside:
            upd.update(textposition="outside", textfont=dict(color="#FFFFFF"))
        tr.update(**upd)
    try:  # marker cornerradius needs plotly >= 5.19
        fig.update_layout(barcornerradius=6)
    except ValueError:
        pass
    fig.update_layout(bargap=0.45, coloraxis_showscale=False)
    return fig


def style_donut(fig, center_text: Optional[str] = None, colors: Optional[list] = None):
    """Donut with cyan/blue slices, card-coloured separators and an optional centre label."""
    for tr in fig.data:
        if getattr(tr, "type", None) != "pie":
            continue
        tr.update(hole=0.65, marker=dict(colors=colors or DONUT_COLORS,
                                         line=dict(color=NEON["bg_card"], width=3)),
                  textfont=dict(color="#FFFFFF"))
    if center_text:
        fig.add_annotation(text=center_text, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper",
                           font=dict(size=16, color="#FFFFFF", family=FONT_FAMILY))
    fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5))
    return fig


def style_map(fig, scale=None, risk: bool = False):
    """Dark choropleth: neon sequential scale (or semantic risk scale), thin light borders."""
    scale = RISK_SCALE if risk else (scale or MAP_SCALE)
    for tr in fig.data:
        t = getattr(tr, "type", None)
        if t in ("choropleth", "choroplethmapbox", "choroplethmap"):
            tr.update(colorscale=scale, marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.5)
    fig.update_layout(coloraxis_colorscale=scale)
    if any(getattr(tr, "type", "") in ("choroplethmapbox", "scattermapbox") for tr in fig.data):
        fig.update_layout(mapbox_style="carto-darkmatter")
    if any(getattr(tr, "type", "") in ("choroplethmap", "scattermap") for tr in fig.data):
        fig.update_layout(map_style="carto-darkmatter")
    fig.update_geos(bgcolor="rgba(0,0,0,0)", landcolor=NEON["bg_app"], showocean=True,
                    oceancolor=NEON["bg_app"], showframe=False)
    return fig


def style_heatmap(fig):
    for tr in fig.data:
        if getattr(tr, "type", None) == "heatmap":
            tr.update(colorscale=DIVERGING_SCALE, textfont=dict(color="#FFFFFF"))
    fig.update_layout(coloraxis_colorscale=DIVERGING_SCALE)
    return fig


def style_scatter(fig):
    for tr in fig.data:
        if getattr(tr, "type", None) == "scatter" and "markers" in (tr.mode or "markers"):
            tr.update(marker=dict(opacity=0.8, line=dict(color="#FFFFFF", width=0.5)))
    return fig


__all__ = [
    "NEON", "GRADIENTS", "FONT_FAMILY", "COLORWAY",
    "COLOR_FOREST_DARK", "COLOR_FOREST_MED", "COLOR_SAGE", "COLOR_MINT",
    "COLOR_WARNING", "COLOR_DANGER", "COLOR_GOLD",
    "MAP_SCALE", "BAR_SCALE", "BAR_SCALE_CYAN", "BAR_SCALE_MAGENTA", "DIVERGING_SCALE",
    "RISK_SCALE", "DONUT_COLORS", "CALLOUT_VARIANTS", "THEME_CSS", "TEMPLATE_NAME",
    "inject_theme_css", "kpi_variant", "build_plotly_template", "register_plotly_template",
    "style_line_glow", "style_area", "style_bars", "style_donut", "style_map",
    "style_heatmap", "style_scatter",
]
