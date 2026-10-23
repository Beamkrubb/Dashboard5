"""Checks for the Neon Night theme (STYLE_HANDOFF.md §7)."""
import re
from pathlib import Path

import pytest

from src import theme

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_no_light_inline_backgrounds_left_in_app():
    light = ["#FFFFFF", "#F8FAFC", "#F0FDF4", "#FEF3C7", "#FFFBEB", "#FEF2F2", "#EFF6FF", "#ECFDF5"]
    for colour in light:
        assert colour not in APP, f"light colour {colour} still hard-coded in app.py"


def test_every_class_used_in_app_is_styled():
    used = set()
    for attr in re.findall(r'class=["\']([^"\'{}]+)["\']', APP):
        used.update(attr.split())
    for cls in sorted(used):
        assert f".{cls}" in theme.THEME_CSS, f"class .{cls} used in app.py but not defined in THEME_CSS"


def test_kpi_variant_alternates():
    assert [theme.kpi_variant(i) for i in range(4)] == ["kpi-magenta", "kpi-cyan", "kpi-magenta", "kpi-cyan"]


def test_legacy_colour_constants_are_neon():
    assert theme.COLOR_FOREST_DARK == "#7C4DFF"
    assert theme.COLOR_FOREST_MED == "#E040FB"
    assert theme.COLOR_SAGE == "#00E5FF"
    assert theme.COLOR_DANGER == "#FF4D6D"


def test_plotly_template_registers():
    pio = pytest.importorskip("plotly.io")
    theme.register_plotly_template()
    assert pio.templates.default == theme.TEMPLATE_NAME
    layout = pio.templates[theme.TEMPLATE_NAME].layout
    assert layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert list(layout.colorway)[:2] == ["#00E5FF", "#E040FB"]


def test_chart_helpers_run():
    go = pytest.importorskip("plotly.graph_objects")
    fig = go.Figure([go.Scatter(x=[1, 2, 3], y=[3, 1, 2]), go.Scatter(x=[1, 2, 3], y=[2, 2, 3])])
    theme.style_line_glow(fig, primary_index=0, dashed_indices=[1])
    assert len(fig.data) == 3 and fig.data[0].opacity == 0.15
    bar = theme.style_bars(go.Figure([go.Bar(x=["a", "b"], y=[1, 2])]))
    assert bar.layout.bargap == 0.45
    pie = theme.style_donut(go.Figure([go.Pie(labels=["a", "b"], values=[1, 2])]), center_text="รวม")
    assert pie.data[0].hole == 0.65
