"""
Plotly figures for app.py, styled with the Neon Night theme (src/theme.py, STYLE_HANDOFF.md §5).
Every function returns a figure; when data is missing it returns a labelled empty figure.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .feature_engineering import aggregate_by
from .theme import (  # noqa: F401  (colour constants are re-exported for app.py)
    BAR_SCALE, BAR_SCALE_CYAN, BAR_SCALE_MAGENTA, COLOR_DANGER, COLOR_FOREST_DARK, COLOR_FOREST_MED,
    COLOR_GOLD, COLOR_MINT, COLOR_SAGE, COLOR_WARNING, DIVERGING_SCALE, DONUT_COLORS, MAP_SCALE, NEON,
    RISK_SCALE, style_area, style_bars, style_donut, style_heatmap, style_line_glow, style_map, style_scatter)

FEATURE_KEY = "properties.pro_th"
MAP_HEIGHT = 560
ALL = "ทั้งหมด"


def _empty(message: str, height: int = 360) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper",
                       font=dict(size=14, color=NEON["muted"]))
    fig.update_layout(height=height, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def _fmt(v: float, unit: str) -> str:
    if v is None or pd.isna(v):
        return "ไม่มีข้อมูล"
    return f"{v:,.1f} {unit}" if abs(v) < 1000 else f"{v:,.0f} {unit}"


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------
def _choropleth(geojson: dict, values: pd.DataFrame, value_col: str, title: str, unit: str,
                selected_province: Optional[str] = None, scale=None, risk: bool = False) -> go.Figure:
    """Base map: every province drawn; provinces without data shown dark (no data ≠ 0)."""
    provinces = [f["properties"].get("pro_th") for f in geojson.get("features", [])]
    base = pd.DataFrame({"province": provinces})
    d = base.merge(values[["province", value_col]], on="province", how="left") if not values.empty else base.assign(**{value_col: np.nan})
    has = d[d[value_col].notna()]
    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=geojson, featureidkey=FEATURE_KEY, locations=d["province"], z=np.zeros(len(d)),
        colorscale=[[0, "#1A1F4D"], [1, "#1A1F4D"]], showscale=False, hoverinfo="text",
        text=[f"{p}<br>ไม่มีข้อมูล" for p in d["province"]], marker_line_color="rgba(255,255,255,0.15)",
        marker_line_width=0.5))
    if not has.empty:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey=FEATURE_KEY, locations=has["province"], z=has[value_col],
            colorscale=RISK_SCALE if risk else (scale or MAP_SCALE), marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.5,
            colorbar=dict(title=dict(text=unit), thickness=12, len=0.7),
            hovertemplate="<b>%{location}</b><br>" + title + ": %{z:,.1f} " + unit + "<extra></extra>"))
    if selected_province and selected_province in provinces:
        fig.add_trace(go.Choropleth(
            geojson=geojson, featureidkey=FEATURE_KEY, locations=[selected_province], z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker_line_color="#FFFFFF", marker_line_width=2.5, hoverinfo="skip"))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=MAP_HEIGHT, margin=dict(l=0, r=0, t=40, b=0),
                      title=dict(text=title, x=0.01, font=dict(size=14)))
    fig.update_geos(bgcolor="rgba(0,0,0,0)", landcolor=NEON["bg_app"], showocean=False, showframe=False,
                    showcountries=False, showcoastlines=False)
    return fig


def create_thailand_map(df_data, geojson_data, metric_col, metric_label, unit, year, product_name,
                        selected_province=None) -> go.Figure:
    g = aggregate_by(df_data, ["province"]) if df_data is not None and not df_data.empty else pd.DataFrame()
    if g.empty or metric_col not in g.columns:
        return _empty(f"ไม่มีข้อมูล {metric_label} ปี พ.ศ. {year}", MAP_HEIGHT)
    return _choropleth(geojson_data, g, metric_col, f"{metric_label} · {product_name} · พ.ศ. {year}", unit,
                       selected_province)


def create_climate_disaster_map(df_rain, df_temp, df_disaster, df_agromet, geojson_data, layer_type, year,
                                selected_province=None) -> go.Figure:
    if layer_type == "rain":
        d = df_rain[df_rain["year"] == year] if df_rain is not None and not df_rain.empty else pd.DataFrame()
        if d.empty:
            return _empty(f"ไม่มีข้อมูลฝนรายจังหวัด ปี พ.ศ. {year}", MAP_HEIGHT)
        src = " (ERA5 reanalysis)" if str(d["source_id"].iloc[0]).endswith("ERA5") else " (สสน. IDW)"
        return _choropleth(geojson_data, d, "rainfall_annual_mm", f"ฝนสะสมทั้งปี พ.ศ. {year}{src}", "มม.",
                           selected_province, scale=[[0, "#1A1F4D"], [0.5, NEON["blue"]], [1, NEON["cyan"]]])
    if layer_type == "temp":
        d = df_temp[df_temp["year"] == year] if df_temp is not None and not df_temp.empty else pd.DataFrame()
        if d.empty:
            return _empty("ไม่มีข้อมูลอุณหภูมิรายจังหวัด (ดาวน์โหลด tmax-tmin ของ สสน.)", MAP_HEIGHT)
        return _choropleth(geojson_data, d, "temp_annual_mean", f"อุณหภูมิเฉลี่ย พ.ศ. {year}", "°C",
                           selected_province, risk=True)
    if layer_type == "disaster":
        d = df_disaster[df_disaster["year"] == year] if df_disaster is not None and not df_disaster.empty else pd.DataFrame()
        if d.empty:
            return _empty("ไม่มีข้อมูลพื้นที่ประสบภัย (ต้องดาวน์โหลดไฟล์ ปภ. ด้วยตนเอง)", MAP_HEIGHT)
        return _choropleth(geojson_data, d, "total_disaster_area_rai", f"พื้นที่ประสบภัย พ.ศ. {year}", "ไร่",
                           selected_province, risk=True)
    # stations
    if df_agromet is None or df_agromet.empty or "lat" not in df_agromet.columns:
        return _empty("ไม่มีข้อมูลสถานี TMD (ต้องตั้งค่า TMD_UID / TMD_UKEY)", MAP_HEIGHT)
    fig = _choropleth(geojson_data, pd.DataFrame(columns=["province", "v"]), "v", "สถานีตรวจวัด TMD", "", selected_province)
    fig.add_trace(go.Scattergeo(lat=df_agromet["lat"], lon=df_agromet["lon"], mode="markers",
                                marker=dict(size=8, color=NEON["cyan"], line=dict(color="#fff", width=0.5)),
                                text=df_agromet["station_name"], hoverinfo="text"))
    return fig


def create_market_price_map(df_ag, geojson_data, crop_name, year, selected_province=None) -> go.Figure:
    """Supply map: production share by province for the product family matching the price series."""
    keyword = "ข้าว" if crop_name.startswith("ข้าว") else crop_name
    d = df_ag[(df_ag["year"] == year) & (df_ag["product"].str.contains(keyword, regex=False))]
    if d.empty:
        return _empty(f"ไม่มีข้อมูลผลผลิตรายจังหวัดของ '{crop_name}' ปี พ.ศ. {year} ในชุดข้อมูล สศก. ที่ดาวน์โหลด", MAP_HEIGHT)
    g = aggregate_by(d, ["province"])
    g["share_pct"] = g["production_ton"] / g["production_ton"].sum() * 100
    return _choropleth(geojson_data, g, "share_pct", f"สัดส่วนผลผลิต {keyword} พ.ศ. {year}", "%", selected_province)


def create_production_driver_map(df_ag, df_irrig, df_soil, df_disaster, geojson_data, layer_type, crop_name, year,
                                 selected_province=None) -> go.Figure:
    if layer_type == "yield":
        d = aggregate_by(df_ag[(df_ag["product"] == crop_name) & (df_ag["year"] == year)], ["province"])
        if d.empty:
            return _empty(f"ไม่มีข้อมูลผลผลิตต่อไร่ของ {crop_name} ปี พ.ศ. {year}", MAP_HEIGHT)
        return _choropleth(geojson_data, d, "calc_yield_per_rai", f"ผลผลิตต่อไร่ {crop_name} พ.ศ. {year}", "กก./ไร่", selected_province)
    if layer_type == "soil":
        d = df_soil[df_soil["crop"] == crop_name] if df_soil is not None and not df_soil.empty else pd.DataFrame()
        if d.empty:
            return _empty(f"ไม่มีข้อมูล Agri-Map สำหรับ {crop_name}", MAP_HEIGHT)
        return _choropleth(geojson_data, d, "s1s2_pct", f"สัดส่วนพื้นที่เหมาะสม S1+S2: {crop_name}", "%", selected_province)
    if layer_type == "irrigation":
        d = df_irrig[df_irrig["year"] == year] if df_irrig is not None and not df_irrig.empty else pd.DataFrame()
        if d.empty:
            return _empty("ไม่มีข้อมูลพื้นที่ชลประทานรายจังหวัด (ต้องสกัดจากรายงาน กรมชลประทาน)", MAP_HEIGHT)
        return _choropleth(geojson_data, d, "irrigated_area_rai", f"พื้นที่ชลประทาน พ.ศ. {year}", "ไร่", selected_province)
    d = df_disaster[df_disaster["year"] == year] if df_disaster is not None and not df_disaster.empty else pd.DataFrame()
    if d.empty:
        return _empty("ไม่มีข้อมูลพื้นที่ประสบภัย (ต้องดาวน์โหลดไฟล์ ปภ. ด้วยตนเอง)", MAP_HEIGHT)
    return _choropleth(geojson_data, d, "total_disaster_area_rai", f"พื้นที่ประสบภัย พ.ศ. {year}", "ไร่", selected_province, risk=True)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def create_ranking_bar_chart(df, x_col, y_col, title, x_label, unit, selected_item=None, is_bottom=False) -> go.Figure:
    if df is None or df.empty or x_col not in df.columns:
        return _empty("ไม่มีข้อมูลสำหรับจัดอันดับ")
    d = df.sort_values(x_col, ascending=not is_bottom)
    fig = go.Figure(go.Bar(x=d[x_col], y=d[y_col], orientation="h", text=[_fmt(v, unit) for v in d[x_col]],
                           hovertemplate="%{y}: %{x:,.1f} " + unit + "<extra></extra>"))
    style_bars(fig, scale=BAR_SCALE_MAGENTA if is_bottom else BAR_SCALE_CYAN, horizontal=True, label_outside=True)
    if selected_item is not None and selected_item in set(d[y_col]):
        fig.data[0].marker.line = dict(color=["#FFFFFF" if p == selected_item else "rgba(0,0,0,0)" for p in d[y_col]], width=2)
    fig.update_layout(title=title, height=420, bargap=0.35, xaxis_title=f"{x_label} ({unit})",
                      margin=dict(l=10, r=60, t=50, b=10))
    return fig


def create_trend_line_chart(df, x_col, y_col, color_col=None, title="", y_label="", unit="") -> go.Figure:
    if df is None or df.empty or y_col not in df.columns:
        return _empty("ไม่มีข้อมูลอนุกรมเวลา")
    d = df.sort_values(x_col)
    fig = go.Figure(go.Scatter(x=d[x_col], y=d[y_col], name=y_label,
                               hovertemplate="พ.ศ. %{x}: %{y:,.1f} " + unit + "<extra></extra>"))
    style_line_glow(fig)
    fig.add_trace(go.Scatter(x=d[x_col], y=d[y_col], fill="tozeroy", mode="none",
                             fillcolor="rgba(0,229,255,0.08)", hoverinfo="skip", showlegend=False))
    fig.update_layout(title=title, height=420, yaxis_title=f"{y_label} ({unit})", xaxis_title="ปี พ.ศ.", showlegend=False)
    return fig


def create_bivariate_scatter_chart(df, x_col, y_col, title, x_label, y_label, x_unit, y_unit, text_col=None,
                                   correlation_val=None, p_val=None, n_samples=None) -> go.Figure:
    if df is None or df.empty:
        return _empty("ไม่มีข้อมูลสำหรับวิเคราะห์ความสัมพันธ์")
    fig = go.Figure(go.Scatter(x=df[x_col], y=df[y_col], mode="markers", text=df[text_col] if text_col else None,
                               marker=dict(size=10, color=NEON["cyan"]),
                               hovertemplate="<b>%{text}</b><br>" + x_label + ": %{x:,.0f} " + x_unit +
                                             "<br>" + y_label + ": %{y:,.0f} " + y_unit + "<extra></extra>"))
    d = df[[x_col, y_col]].dropna()
    if len(d) >= 3 and d[x_col].nunique() > 1:
        k, b = np.polyfit(d[x_col], d[y_col], 1)
        xs = np.linspace(d[x_col].min(), d[x_col].max(), 50)
        fig.add_trace(go.Scatter(x=xs, y=k * xs + b, mode="lines", line=dict(color=NEON["magenta"], width=2, dash="dash"),
                                 hoverinfo="skip", name="แนวโน้มเชิงเส้น"))
    style_scatter(fig)
    sub = f"r = {correlation_val:.2f}, p = {p_val:.3f}, n = {n_samples}" if correlation_val is not None else "ข้อมูลไม่พอทดสอบ"
    fig.update_layout(title=f"{title}<br><sup>{sub}</sup>", height=440, showlegend=False,
                      xaxis_title=f"{x_label} ({x_unit})", yaxis_title=f"{y_label} ({y_unit})")
    return fig


def create_correlation_heatmap(df: pd.DataFrame, columns=None, title="Correlation") -> go.Figure:
    cols = columns or df.select_dtypes("number").columns.tolist()
    if df is None or df.empty or len(cols) < 2:
        return _empty("ไม่มีข้อมูลพอสำหรับ heatmap")
    c = df[cols].corr()
    fig = go.Figure(go.Heatmap(z=c.values, x=cols, y=cols, zmin=-1, zmax=1, text=np.round(c.values, 2), texttemplate="%{text}"))
    style_heatmap(fig)
    fig.update_layout(title=title, height=420)
    return fig


def create_quadrant_scatter_chart(df: pd.DataFrame, title="Scale vs Efficiency") -> go.Figure:
    if df is None or df.empty:
        return _empty("ไม่มีข้อมูล")
    fig = go.Figure(go.Scatter(x=df["area_plant_rai"], y=df["calc_yield_per_rai"], mode="markers", text=df["province"],
                               hovertemplate="%{text}<extra></extra>"))
    style_scatter(fig)
    for v, axis in ((df["area_plant_rai"].median(), "x"), (df["calc_yield_per_rai"].median(), "y")):
        (fig.add_vline if axis == "x" else fig.add_hline)(v, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig.update_layout(title=title, height=420, xaxis_title="เนื้อที่เพาะปลูก (ไร่)", yaxis_title="ผลผลิตต่อไร่ (กก./ไร่)")
    return fig


def create_yoy_bar_chart(df: pd.DataFrame, x_col="year", y_col="yoy_pct", title="การเปลี่ยนแปลงรายปี (%)") -> go.Figure:
    if df is None or df.empty:
        return _empty("ไม่มีข้อมูล")
    fig = go.Figure(go.Bar(x=df[x_col], y=df[y_col],
                           marker_color=[NEON["success"] if v >= 0 else NEON["danger"] for v in df[y_col].fillna(0)]))
    fig.update_layout(title=title, height=380, bargap=0.45)
    return fig


def create_price_trend_chart(price_sub: pd.DataFrame, crop: str, unit_mode: str = "native") -> go.Figure:
    if price_sub is None or price_sub.empty:
        return _empty("ไม่มีข้อมูลราคา")
    p = price_sub.sort_values(["year", "month", "week"]).reset_index(drop=True)
    native = unit_mode == "native" and "native_price" in p.columns
    col, unit = ("native_price", str(p["native_unit"].iloc[0])) if native else ("price_baht_per_kg", "บาท/กก.")
    label = [f"{y}-{m:02d} ส.{w}" for y, m, w in zip(p["year"], p["month"], p["week"])]
    fig = go.Figure(go.Scatter(x=label, y=p[col], name=crop, hovertemplate="%{x}: %{y:,.2f} " + unit + "<extra></extra>"))
    style_line_glow(fig)
    if len(p) >= 8:
        ma = p[col].rolling(8).mean()
        fig.add_trace(go.Scatter(x=label, y=ma, name="ค่าเฉลี่ยเคลื่อนที่ 8 สัปดาห์", hoverinfo="skip", mode="lines",
                                 line=dict(color="#FFFFFF", width=2, dash="dash"), line_shape="spline"))
    fig.update_layout(title=f"ราคาที่เกษตรกรขายได้รายสัปดาห์: {crop}", height=400, yaxis_title=unit,
                      xaxis=dict(nticks=10), legend=dict(y=1.12))
    return fig


def create_cost_breakdown_pie(breakdown: Dict[str, float], title="โครงสร้างต้นทุน") -> go.Figure:
    if not breakdown:
        return _empty("ไม่มีข้อมูลต้นทุน")
    fig = go.Figure(go.Pie(labels=list(breakdown), values=list(breakdown.values())))
    style_donut(fig, center_text=f"{sum(breakdown.values()):,.0f}<br>บาท/ไร่")
    fig.update_layout(title=title, height=380)
    return fig


def create_scenario_bar_chart(df: pd.DataFrame, title="กำไรตามสถานการณ์") -> go.Figure:
    if df is None or df.empty:
        return _empty("ไม่มีข้อมูล")
    lab = [f"ผลผลิต {y:+.0f}% / ราคา {p:+.0f}%" for y, p in zip(df["yield_change_pct"], df["price_change_pct"])]
    fig = go.Figure(go.Bar(x=lab, y=df["profit"],
                           marker_color=[NEON["success"] if v >= 0 else NEON["danger"] for v in df["profit"]]))
    fig.update_layout(title=title, height=380)
    return fig


def create_irrigation_vs_yield_chart(df: pd.DataFrame, crop: str, year: int) -> go.Figure:
    if df is None or df.empty:
        return _empty("ยังไม่มีข้อมูลพื้นที่ชลประทานรายจังหวัด<br>(สกัดจากรายงานกรมชลประทานไปที่ data/raw/D04/)")
    return create_bivariate_scatter_chart(df, "irrigated_area_rai", "calc_yield_per_rai",
                                          f"พื้นที่ชลประทาน vs ผลผลิตต่อไร่: {crop} พ.ศ. {year}", "พื้นที่ชลประทาน",
                                          "ผลผลิตต่อไร่", "ไร่", "กก./ไร่", text_col="province")


def create_soil_suitability_bar_chart(df_soil: pd.DataFrame, crop: str, top_n: int = 12) -> go.Figure:
    if df_soil is None or df_soil.empty:
        return _empty("ไม่มีข้อมูล Agri-Map")
    d = df_soil[df_soil["crop"] == crop].sort_values("total_rai", ascending=False).head(top_n)
    if d.empty:
        return _empty(f"ไม่มีข้อมูล Agri-Map สำหรับ {crop}")
    d = d.iloc[::-1]
    fig = go.Figure()
    for col, name, color in (("s1_rai", "S1 เหมาะสมสูง", NEON["cyan"]), ("s2_rai", "S2 ปานกลาง", NEON["blue"]),
                             ("s3_rai", "S3 เล็กน้อย", NEON["violet"]), ("n_rai", "N ไม่เหมาะสม", NEON["magenta"])):
        fig.add_trace(go.Bar(y=d["province"], x=d[col], name=name, orientation="h", marker_color=color,
                             hovertemplate="%{y}: %{x:,.0f} ไร่<extra>" + name + "</extra>"))
    fig.update_layout(barmode="stack", title=f"ชั้นความเหมาะสมของที่ดิน: {crop} ({top_n} จังหวัดพื้นที่มากสุด)",
                      height=460, xaxis_title="ไร่", bargap=0.35)
    return fig


def create_cost_structure_breakdown_chart(breakdown: Dict[str, float], crop: str, total_cost: float, year: int) -> go.Figure:
    return create_cost_breakdown_pie(breakdown, title=f"โครงสร้างต้นทุน {crop} พ.ศ. {year} (รวม {total_cost:,.0f} บาท/ไร่)")


def create_disaster_impact_chart(df_disaster: pd.DataFrame, year: int, top_n: int = 10) -> go.Figure:
    if df_disaster is None or df_disaster.empty:
        return _empty("ยังไม่มีข้อมูลพื้นที่ประสบภัยรายจังหวัด<br>(ดาวน์โหลดไฟล์ ปภ. ไปที่ data/raw/D06/)")
    d = df_disaster[df_disaster["year"] == year].sort_values("total_disaster_area_rai", ascending=False).head(top_n)
    if d.empty:
        return _empty(f"ไม่มีข้อมูลพื้นที่ประสบภัย ปี พ.ศ. {year}")
    fig = go.Figure()
    for col, name, color in (("flood_area_rai", "อุทกภัย", NEON["blue"]), ("drought_area_rai", "ภัยแล้ง", NEON["warning"]),
                             ("storm_area_rai", "วาตภัย", NEON["magenta"])):
        fig.add_trace(go.Bar(x=d["province"], y=d[col], name=name, marker_color=color))
    fig.update_layout(barmode="stack", title=f"พื้นที่ประสบภัย {top_n} จังหวัดสูงสุด พ.ศ. {year}", height=420, yaxis_title="ไร่")
    return fig


def create_seasonal_rain_vs_yield_chart(df: pd.DataFrame, crop: str, year: int) -> go.Figure:
    if df is None or df.empty:
        return _empty(f"ไม่มีข้อมูลฝนรายเดือนครบ 12 เดือน ปี พ.ศ. {year}")
    d = df.sort_values("season_rain_mm", ascending=False).head(20).iloc[::-1]
    fig = go.Figure([
        go.Bar(y=d["province"], x=d["season_rain_mm"], orientation="h", name="ฝน พ.ค.–ต.ค.", marker_color=NEON["cyan"]),
        go.Bar(y=d["province"], x=d["annual_rain_mm"] - d["season_rain_mm"], orientation="h", name="ฝนนอกฤดู",
               marker_color=NEON["violet"])])
    fig.update_layout(barmode="stack", title=f"ฝนฤดูเพาะปลูก vs ฝนนอกฤดู (20 จังหวัดฝนฤดูสูงสุด) พ.ศ. {year}",
                      height=520, xaxis_title="มม.", bargap=0.3)
    return fig


def create_cost_price_margin_chart(summary: Dict) -> go.Figure:
    if not summary.get("has_data"):
        return _empty("ไม่มีข้อมูลต้นทุน")
    vals = {"ต้นทุนต่อ กก.": summary.get("cost_per_kg"), "ราคาเฉลี่ยต่อ กก.": summary.get("avg_price_kg"),
            "ส่วนต่าง": summary.get("margin_kg")}
    fig = go.Figure(go.Bar(x=list(vals), y=list(vals.values()),
                           marker_color=[NEON["magenta"], NEON["cyan"],
                                         NEON["success"] if (summary.get("margin_kg") or 0) >= 0 else NEON["danger"]],
                           text=[_fmt(v, "บาท") for v in vals.values()], textposition="outside"))
    fig.update_layout(title=f"ต้นทุน vs ราคา: {summary.get('crop')} (บาท/กก.)", height=380, bargap=0.45)
    return fig
