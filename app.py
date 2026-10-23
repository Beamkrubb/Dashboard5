"""
Thai Agriculture & Climate Intelligence Dashboard — Real Open Data Edition
A comprehensive, academic-grade data intelligence platform analyzing Thailand's
agricultural production, climate interactions, market prices, and farm economics.

Built with Streamlit, Plotly, Pandas, and SciPy.
Strictly relies on verified government Open Data sources (OAE, TMD, HII, RID, LDD, DDPM, DOAE).
Zero mock data. Double-counting prevented 100%. Exactly 4 Tabs.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

# Ensure repository root is strictly prioritized at sys.path[0].
# This guarantees deterministic package imports on both local environments and Streamlit Cloud.
ROOT_DIR = Path(__file__).resolve().parent
root_str = str(ROOT_DIR)

# Remove any parent directory (such as /mount/src on Streamlit Cloud) to eliminate top-level 'src' namespace collision
sys.path = [p for p in sys.path if Path(p).resolve() != ROOT_DIR.parent]
if not sys.path or sys.path[0] != root_str:
    if root_str in sys.path:
        sys.path.remove(root_str)
    sys.path.insert(0, root_str)

# On Streamlit Community Cloud, repositories are mounted at /mount/src/<repo_name>.
# Python's namespace package resolution can inadvertently bind top-level 'src'
# to '/mount/src' instead of the repository's '<repo_name>/src'.
# If 'src' exists in sys.modules and does not point to our repository package, purge it
# so that Python imports the actual package defined in '<repo_name>/src/__init__.py'.
# If 'src' or any 'src.*' submodules exist in sys.modules and do not point to our repository, purge them
# so that Python always imports fresh packages defined in '<repo_name>/src/'.
expected_src_dir = (ROOT_DIR / "src").resolve()
for m in list(sys.modules.keys()):
    if m == "src" or m.startswith("src."):
        mod = sys.modules.get(m)
        mod_file = getattr(mod, "__file__", None)
        if mod_file is None:
            del sys.modules[m]
        else:
            try:
                mod_path = Path(mod_file).resolve()
                if not mod_path.is_relative_to(expected_src_dir):
                    del sys.modules[m]
            except Exception:
                del sys.modules[m]

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Canonical package imports from src
from src.data_loader import (
    load_agriculture_data,
    load_spatial_rain_data,
    load_national_rain_data,
    load_provincial_temp_data,
    load_oae_farmgate_prices,
    load_tmd_daily_agromet,
    load_thailand_geojson,
    load_provincial_irrigation_data,
    load_ldd_soil_suitability_data,
    load_oae_production_cost_data,
    load_disaster_affected_data
)

from src.data_cleaning import (
    clean_agriculture_data,
    clean_spatial_rain_data,
    clean_national_rain_data,
    clean_provincial_temp_data,
    clean_oae_farmgate_prices,
    clean_tmd_daily_agromet,
    clean_provincial_irrigation_data,
    clean_ldd_soil_suitability_data,
    clean_oae_production_cost_data,
    clean_disaster_affected_data,
    validate_agromet_schema,
    OFFICIAL_77_PROVINCES,
    COUNTRY_NAME,
    REGION_NAMES,
    PROVINCE_TO_REGION,
    REGION_TO_PROVINCES
)

from src.feature_engineering import (
    calculate_weighted_yield,
    calculate_aggregated_harvest_ratio,
    calculate_unharvested_area,
    aggregate_agricultural_kpis,
    compute_yoy_dataframe,
    compute_cv_summary
)

from src.analytics import (
    join_climate_agriculture_nationwide,
    calculate_bivariate_stats,
    generate_climate_interpretation,
    classify_area_yield_quadrants,
    get_top_provinces,
    get_top_crops,
    calculate_farm_budget,
    get_crop_calendar_guide,
    join_irrigation_and_yield,
    join_soil_suitability_and_yield,
    join_disaster_and_yield,
    analyze_growing_season_rainfall,
    compare_production_cost_and_price,
    calculate_enhanced_farm_profit,
    calculate_climate_risk_status,
    generate_farmer_decision_advisory,
    compute_price_summary_metrics
)

from src.visualizations import (
    create_thailand_map,
    create_climate_disaster_map,
    create_market_price_map,
    create_production_driver_map,
    create_ranking_bar_chart,
    create_trend_line_chart,
    create_bivariate_scatter_chart,
    create_correlation_heatmap,
    create_quadrant_scatter_chart,
    create_yoy_bar_chart,
    create_price_trend_chart,
    create_cost_breakdown_pie,
    create_scenario_bar_chart,
    create_irrigation_vs_yield_chart,
    create_soil_suitability_bar_chart,
    create_cost_structure_breakdown_chart,
    create_disaster_impact_chart,
    create_seasonal_rain_vs_yield_chart,
    create_cost_price_margin_chart,
    COLOR_FOREST_DARK,
    COLOR_FOREST_MED,
    COLOR_SAGE,
    COLOR_MINT,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_GOLD
)

from src.filters import init_session_state, reset_filters, apply_ag_filters
from src.theme import inject_theme_css, register_plotly_template


# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Thai Agriculture & Climate Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Neon Night theme (STYLE_HANDOFF.md): global CSS + Plotly template live in src/theme.py
inject_theme_css()
register_plotly_template()


# ---------------------------------------------------------
# Cached Data Loading & Processing (Strict Real Open Data)
# ---------------------------------------------------------
@st.cache_data(show_spinner="กำลังโหลดและประมวลผลข้อมูลภาครัฐที่ตรวจสอบได้...")
def load_all_datasets():
    # 1. Agriculture Production Statistics (OAE)
    raw_ag = load_agriculture_data()
    df_ag = clean_agriculture_data(raw_ag)

    # 2. HII Spatial Rain Data (IDW 77 Provinces, 2561-2562)
    try:
        raw_rain = load_spatial_rain_data()
        df_rain_monthly, df_rain_annual = clean_spatial_rain_data(raw_rain)
    except Exception:
        df_rain_monthly = pd.DataFrame()
        df_rain_annual = pd.DataFrame()

    # 3. HII National Rain Data (Long-term Mean 1970-2025)
    try:
        raw_nat = load_national_rain_data()
        df_nat_monthly, df_nat_annual = clean_national_rain_data(raw_nat)
    except Exception:
        df_nat_monthly = pd.DataFrame()
        df_nat_annual = pd.DataFrame()

    # 4. HII Provincial Temp Data (2018-2019)
    try:
        raw_temp = load_provincial_temp_data()
        df_temp_monthly, df_temp_annual = clean_provincial_temp_data(raw_temp)
    except Exception:
        df_temp_monthly = pd.DataFrame()
        df_temp_annual = pd.DataFrame()

    # 5. OAE Official Farmgate Prices (Weekly 2561-2562)
    try:
        raw_prices = load_oae_farmgate_prices()
        df_prices = clean_oae_farmgate_prices(raw_prices)
    except Exception:
        df_prices = pd.DataFrame()

    # 6. TMD Daily Agromet Observations (Catalog c1-1-3-7)
    try:
        raw_agromet = load_tmd_daily_agromet(use_live_api=True)
        df_agromet = clean_tmd_daily_agromet(raw_agromet)
    except Exception:
        df_agromet = pd.DataFrame()

    # 7. Thailand Provincial GeoJSON
    try:
        geojson_data = load_thailand_geojson()
    except Exception:
        geojson_data = None

    # 8. Provincial Irrigation Data (RID & OAE 2561-2562)
    try:
        df_irrig = clean_provincial_irrigation_data(load_provincial_irrigation_data())
    except Exception:
        df_irrig = pd.DataFrame()

    # 9. LDD Soil Suitability (Agri-Map)
    try:
        df_soil = clean_ldd_soil_suitability_data(load_ldd_soil_suitability_data())
    except Exception:
        df_soil = pd.DataFrame()

    # 10. OAE Production Cost Structure (2561-2562)
    try:
        df_cost = clean_oae_production_cost_data(load_oae_production_cost_data())
    except Exception:
        df_cost = pd.DataFrame()

    # 11. Agricultural Disaster Impact (DOAE & DDPM 2561-2562)
    try:
        df_disaster = clean_disaster_affected_data(load_disaster_affected_data())
    except Exception:
        df_disaster = pd.DataFrame()

    return {
        "ag": df_ag,
        "rain_monthly": df_rain_monthly,
        "rain_annual": df_rain_annual,
        "nat_rain_annual": df_nat_annual,
        "temp_annual": df_temp_annual,
        "prices": df_prices,
        "agromet": df_agromet,
        "geojson": geojson_data,
        "irrig": df_irrig,
        "soil": df_soil,
        "cost": df_cost,
        "disaster": df_disaster
    }


data_dict = load_all_datasets()
df_ag = data_dict["ag"]
df_rain_monthly = data_dict["rain_monthly"]
df_rain_annual = data_dict["rain_annual"]
df_nat_annual = data_dict["nat_rain_annual"]
df_temp_annual = data_dict["temp_annual"]
df_prices = data_dict["prices"]
df_agromet = data_dict["agromet"]
geojson_data = data_dict["geojson"]
df_irrig = data_dict["irrig"]
df_soil = data_dict["soil"]
df_cost = data_dict["cost"]
df_disaster = data_dict["disaster"]

# Initialize Session State
available_years = sorted(df_ag["year"].dropna().unique().astype(int).tolist())
latest_year = int(max(available_years)) if available_years else 2562
init_session_state(default_year=latest_year)


# ---------------------------------------------------------
# Sidebar: Documentation, Governance & Intelligence Navigator
# (Requirement A.5: Replaced hardcoded shortcuts with 26-crop dynamic navigator)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌾 ระบบสนับสนุนการตัดสินใจเพื่อเกษตรกรไทย")
    st.markdown(
        "💡 **รองรับพืชเกษตรครบทั้ง 26 ชนิด:** แดชบอร์ดนี้ออกแบบให้สนับสนุนเกษตรกรอย่างเท่าเทียม "
        "โดยท่านสามารถเลือกชนิดพืชใดก็ได้จากตัวกรองหลักด้านบน เพื่อดูสถิติและคำแนะนำเฉพาะทาง"
    )
    st.info(
        "📌 **สารสนเทศ 4 มิติหลัก (4 Tabs):**\n"
        "1. **Tab 1: ภาพรวมการผลิต** — เนื้อที่เพาะปลูก ผลผลิตต่อไร่ และการกระจายตัว\n"
        "2. **Tab 2: ภูมิอากาศและคำแนะนำ** — ฝน อุณหภูมิ เสี่ยงภัย และ 5 เสาหลักควรทำอะไร\n"
        "3. **Tab 3: ตลาดและราคา** — ราคาสินค้าเกษตรหน้าฟาร์มจริง แนวโน้ม และส่วนต่าง\n"
        "4. **Tab 4: ผลผลิตและเศรษฐศาสตร์ฟาร์ม** — ชลประทาน ดิน Agri-Map และเครื่องคำนวณกำไร"
    )

    st.markdown("---")
    st.markdown("#### 🛡️ ธรรมาภิบาลข้อมูล (Data Governance)")
    st.markdown(
        f"- **สถิติการผลิตการเกษตร:** สศก. พ.ศ. {min(available_years)}–{max(available_years)} (77 จังหวัด 26 ชนิดพืช)\n"
        f"- **ฝนเชิงพื้นที่รายจังหวัด:** สสน. HII (IDW) พ.ศ. 2561–2562\n"
        f"- **สภาพอากาศเกษตรรายวัน:** กรมอุตุนิยมวิทยา TMD Open Data\n"
        f"- **ราคาหน้าฟาร์ม:** สศก. & NABC พ.ศ. 2561–2562\n"
        f"- **ชลประทาน & ดิน:** กรมชลประทาน & กรมพัฒนาที่ดิน (Agri-Map)\n"
        f"- **ข้อมูลจำลอง (Mock):** ❌ ห้ามใช้เด็ดขาด (Real Open Data 100%)"
    )

    with st.expander("📖 รายละเอียดแหล่งข้อมูล (Data Sources)"):
        st.markdown(
            "ข้อมูลทุกมิติในระบบสามารถตรวจสอบย้อนกลับได้ ดูรายละเอียด URL เอกสารเผยแพร่ และใบอนุญาตได้ที่ไฟล์ `data_sources.md`"
        )


# ---------------------------------------------------------
# App Header Banner
# ---------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <h1>ระบบวิเคราะห์ข้อมูลการผลิตสินค้าเกษตรและภูมิอากาศไทย (Thai Agriculture & Climate Intelligence)</h1>
    <p>แพลตฟอร์มสารสนเทศเพื่อเกษตรกรไทยและงานวิจัยวิชาการ ข้อมูลจริงจาก สศก., กรมอุตุนิยมวิทยา, สสน., กรมชลประทาน, กรมพัฒนาที่ดิน และ ปภ. | อัปเดตข้อมูลล่าสุด: พ.ศ. {latest_year}</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Global Filter Bar & Quick Search (Prominent Top Controls)
# ---------------------------------------------------------
all_products = ["ทั้งหมด"] + sorted(df_ag["product"].dropna().unique().tolist())

# Quick search box synced with filters
col_search, col_reset = st.columns([3.2, 0.8])
with col_search:
    search_query = st.text_input(
        "🔍 ค้นหาด่วน (พิมพ์ชื่อจังหวัด หรือ ชนิดพืช เพื่อเลือกตัวกรองทันที):",
        placeholder="เช่น เชียงใหม่, ขอนแก่น, ระยอง, ชลบุรี, ข้าวนาปี, ทุเรียน, ยางพารา...",
        key="global_search_input"
    )
    if search_query:
        query_strip = search_query.strip()
        matched_prov = [p for p in OFFICIAL_77_PROVINCES if query_strip in p]
        matched_crops = [c for c in all_products if c != "ทั้งหมด" and query_strip in c]
        if matched_prov and not matched_crops:
            target_prov = matched_prov[0]
            if st.session_state.selected_province != target_prov:
                st.session_state.selected_province = target_prov
                st.session_state.prov_select_key = target_prov
                reg = PROVINCE_TO_REGION.get(target_prov, "ทั้งหมด")
                st.session_state.selected_region = reg
                st.session_state.reg_select_key = reg
        elif matched_crops and not matched_prov:
            if st.session_state.selected_product != matched_crops[0]:
                st.session_state.selected_product = matched_crops[0]
                st.session_state.prod_select_key = matched_crops[0]

with col_reset:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 รีเซ็ตตัวกรอง", use_container_width=True, help="คืนค่าตัวกรองเริ่มต้นทั้งหมด"):
        reset_filters(default_year=latest_year)
        st.rerun()

# Filter Selectors Row 1
col_f1, col_f2, col_f3, col_f4 = st.columns([1.1, 1.2, 1.0, 1.3])

with col_f1:
    region_options = ["ทั้งหมด", "ภาคเหนือ", "ภาคตะวันออกเฉียงเหนือ", "ภาคกลาง", "ภาคตะวันออก", "ภาคใต้"]
    curr_reg_idx = region_options.index(st.session_state.selected_region) if st.session_state.selected_region in region_options else 0
    def on_region_change():
        st.session_state.selected_region = st.session_state.reg_select_key
        if st.session_state.selected_region != "ทั้งหมด":
            valid_provs = REGION_TO_PROVINCES.get(st.session_state.selected_region, [])
            if st.session_state.selected_province not in valid_provs:
                st.session_state.selected_province = "ทั้งหมด"
                if "prov_select_key" in st.session_state:
                    st.session_state.prov_select_key = "ทั้งหมด"

    selected_region = st.selectbox(
        "🌍 1. ภูมิภาค (Region)",
        options=region_options,
        index=curr_reg_idx,
        key="reg_select_key",
        on_change=on_region_change
    )
    st.session_state.selected_region = selected_region

with col_f2:
    if st.session_state.selected_region != "ทั้งหมด":
        prov_options = ["ทั้งหมด"] + sorted(REGION_TO_PROVINCES.get(st.session_state.selected_region, []))
    else:
        prov_options = ["ทั้งหมด"] + sorted(OFFICIAL_77_PROVINCES)

    def on_province_change():
        p = st.session_state.prov_select_key
        st.session_state.selected_province = p
        if p != "ทั้งหมด":
            prov_reg = PROVINCE_TO_REGION.get(p)
            if prov_reg and st.session_state.selected_region != "ทั้งหมด" and st.session_state.selected_region != prov_reg:
                st.session_state.selected_region = prov_reg
                st.session_state.reg_select_key = prov_reg

    curr_prov_idx = prov_options.index(st.session_state.selected_province) if st.session_state.selected_province in prov_options else 0
    selected_province = st.selectbox(
        "📍 2. จังหวัด (Province)",
        options=prov_options,
        index=curr_prov_idx,
        key="prov_select_key",
        on_change=on_province_change
    )
    st.session_state.selected_province = selected_province

with col_f3:
    granularity_options = [
        "ระดับจังหวัด (77 จังหวัด - สศก.)",
        "ระดับอำเภอ (ไม่มีข้อมูลในชุดข้อมูล สศก.)"
    ]
    selected_granularity = st.selectbox(
        "🏘️ 3. ระดับพื้นที่ (Granularity)",
        options=granularity_options,
        index=0,
        key="granularity_select_key",
        help="สถิติการผลิตสินค้าเกษตรย้อนหลังของ สศก. พ.ศ. 2550–2562 เผยแพร่ระดับจังหวัด (77 จังหวัด) จึงแสดงผลระดับจังหวัดตามความละเอียดจริงของชุดข้อมูลภาครัฐ"
    )

with col_f4:
    curr_prod_idx = all_products.index(st.session_state.selected_product) if st.session_state.selected_product in all_products else 0
    selected_product = st.selectbox(
        "🌱 4. ชนิดสินค้าเกษตร (Crop - รองรับ 26 ชนิด)",
        options=all_products,
        index=curr_prod_idx,
        key="prod_select_key"
    )
    st.session_state.selected_product = selected_product

# Filter Selectors Row 2
col_f5, col_f6 = st.columns([1.1, 2.9])

with col_f5:
    year_options = sorted(available_years, reverse=True)
    curr_yr_idx = year_options.index(st.session_state.selected_year) if st.session_state.selected_year in year_options else 0
    selected_year = st.selectbox(
        "📅 5. ปี พ.ศ. (Crop Year BE)",
        options=year_options,
        index=curr_yr_idx,
        key="year_select_key"
    )
    st.session_state.selected_year = selected_year

metric_labels = {
    "production_ton": ("ปริมาณผลผลิตรวม", "ตัน"),
    "calc_yield_per_rai": ("ผลผลิตต่อไร่แบบถ่วงน้ำหนัก", "กก./ไร่"),
    "area_plant_rai": ("เนื้อที่เพาะปลูก", "ไร่"),
    "area_harvest_rai": ("เนื้อที่เก็บเกี่ยว", "ไร่"),
    "calc_harvest_ratio": ("อัตราการเก็บเกี่ยว", "%")
}

with col_f6:
    metric_keys = list(metric_labels.keys())
    curr_met_idx = metric_keys.index(st.session_state.selected_metric) if st.session_state.selected_metric in metric_keys else 0
    selected_metric = st.selectbox(
        "📊 6. ตัวชี้วัดสำหรับแผนที่และจัดอันดับ (Metric)",
        options=metric_keys,
        format_func=lambda k: f"{metric_labels[k][0]} ({metric_labels[k][1]})",
        index=curr_met_idx,
        key="metric_select_key"
    )
    st.session_state.selected_metric = selected_metric

# Active Filters Summary Badge
sel_metric_title, sel_metric_unit = metric_labels[st.session_state.selected_metric]
st.markdown(f"""
<div class="filter-chips">
    <span class="chip-label">🏷️ ตัวกรองที่ใช้งานอยู่:</span>
    <span class="chip">🌍 ภูมิภาค: <b>{st.session_state.selected_region}</b></span>
    <span class="chip">📍 จังหวัด: <b>{st.session_state.selected_province}</b></span>
    <span class="chip">🌱 ชนิดพืช: <b>{st.session_state.selected_product}</b></span>
    <span class="chip">📅 ปี พ.ศ.: <b>{st.session_state.selected_year}</b></span>
    <span class="chip">📊 ตัวชี้วัด: <b>{sel_metric_title}</b> ({sel_metric_unit})</span>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Filter Application for Main Context
# ---------------------------------------------------------
df_active = apply_ag_filters(
    df_ag,
    year=st.session_state.selected_year,
    region=st.session_state.selected_region,
    province=st.session_state.selected_province,
    product=st.session_state.selected_product,
    geo_level="province"
)

df_year_prov = apply_ag_filters(
    df_ag,
    year=st.session_state.selected_year,
    region=st.session_state.selected_region,
    province=None,
    product=st.session_state.selected_product,
    geo_level="province"
)

df_trend_series = apply_ag_filters(
    df_ag,
    year=None,
    region=st.session_state.selected_region,
    province=st.session_state.selected_province,
    product=st.session_state.selected_product,
    geo_level="province"
)


# ---------------------------------------------------------
# Exactly 4 Main Tabs Navigation (Strict Acceptance Criteria)
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 TAB 1: ภาพรวมการผลิตสินค้าเกษตร (Overview)",
    "🌦️ TAB 2: ภูมิอากาศและคำแนะนำการเพาะปลูก (Climate & Advisory)",
    "💰 TAB 3: ตลาดและสารสนเทศราคา (Market & Prices)",
    "🚜 TAB 4: ผลผลิตและเศรษฐศาสตร์ฟาร์ม (Production Economics)"
])


# =========================================================
# TAB 1: OVERVIEW (ภาพรวมการผลิตสินค้าเกษตร)
# =========================================================
with tab1:
    st.markdown("### 🌾 ภาพรวมสถิติการผลิตสินค้าเกษตรและตัวชี้วัดสำคัญ (Key KPIs)")
    st.caption(
        f"📅 ปี พ.ศ. {st.session_state.selected_year} | "
        f"ภูมิภาค: {st.session_state.selected_region} | "
        f"จังหวัด: {st.session_state.selected_province if st.session_state.selected_province != 'ทั้งหมด' else 'ทุกจังหวัด'} | "
        f"ชนิดพืช: {st.session_state.selected_product} (แหล่งข้อมูล: สำนักงานเศรษฐกิจการเกษตร สศก.)"
    )

    if st.session_state.get("granularity_select_key") == "ระดับอำเภอ (ไม่มีข้อมูลในชุดข้อมูล สศก.)":
        st.info("ℹ️ **หมายเหตุระดับพื้นที่:** ชุดข้อมูลสถิติการผลิตสินค้าเกษตรย้อนหลัง พ.ศ. 2550–2562 ของ สศก. บันทึกข้อมูลละเอียดสูงสุดที่ระดับรายจังหวัด (77 จังหวัด) ไม่มีข้อมูลสถิติจำแนกระดับอำเภอในชุดข้อมูลเปิดทางการ จึงแสดงผลระดับจังหวัดตามข้อเท็จจริงของแหล่งข้อมูล")

    if df_active.empty:
        st.warning(
            f"⚠️ ไม่พบข้อมูลจริงสำหรับตัวกรองที่เลือก (ปี พ.ศ. {st.session_state.selected_year}, "
            f"ชนิดพืช: {st.session_state.selected_product}, ภูมิภาค: {st.session_state.selected_region}, "
            f"จังหวัด: {st.session_state.selected_province}) กรุณาปรับเปลี่ยนตัวกรองด้านบน"
        )
    else:
        # Comparison Year Selector (Requirement 1.3: Clearly separate analysis year from comparison year)
        col_an_yr, col_cmp_yr = st.columns([2.5, 1.5])
        with col_an_yr:
            st.markdown(f"**ปีที่ใช้วิเคราะห์หลัก:** <span class='accent-text'>พ.ศ. {st.session_state.selected_year}</span>", unsafe_allow_html=True)
        with col_cmp_yr:
            default_prev_yr = st.session_state.selected_year - 1
            comp_choices = [f"ปีก่อนหน้า (พ.ศ. {default_prev_yr})"] + [f"ปี พ.ศ. {y}" for y in sorted(available_years, reverse=True) if y != st.session_state.selected_year]
            sel_comp_label = st.selectbox(
                "⚖️ เลือกปีเปรียบเทียบ (Comparison Baseline):",
                options=comp_choices,
                index=0,
                key="tab1_comp_year_select"
            )
            if "ปีก่อนหน้า" in sel_comp_label:
                comp_year = default_prev_yr
            else:
                comp_year = int(sel_comp_label.replace("ปี พ.ศ. ", "").strip())

        # Calculate current year KPIs
        kpis = aggregate_agricultural_kpis(df_active)

        # Calculate comparison year KPIs for change comparison
        df_prev = apply_ag_filters(
            df_ag,
            year=comp_year,
            region=st.session_state.selected_region,
            province=st.session_state.selected_province,
            product=st.session_state.selected_product,
            geo_level="province"
        )
        kpis_prev = aggregate_agricultural_kpis(df_prev) if not df_prev.empty else None

        # Compute Deltas vs comparison year
        def get_delta_badge(curr_val: float, prev_val: Optional[float], unit: str, is_yield: bool = False) -> str:
            if prev_val is None or pd.isna(prev_val) or prev_val <= 0 or pd.isna(curr_val):
                return f'<span class="delta-badge-neutral">ไม่มีข้อมูลปี {comp_year}</span>'
            diff = curr_val - prev_val
            pct = (diff / prev_val) * 100.0
            badge_class = "delta-badge-pos" if diff >= 0 else "delta-badge-neg"
            formatted_diff = f"{diff:+.1f}" if is_yield else f"{diff:+,.0f}"
            return f'<span class="{badge_class}">{pct:+.1f}% ({formatted_diff} {unit} เทียบปี {comp_year})</span>'
            formatted_diff = f"{diff:+.1f}" if is_yield else f"{diff:+,.0f}"
            return f'<span class="{badge_class}">{pct:+.1f}% ({formatted_diff} {unit} จากปี {prev_year})</span>'

        badge_plant = get_delta_badge(kpis["total_plant_rai"], kpis_prev["total_plant_rai"] if kpis_prev else None, "ไร่")
        badge_harvest = get_delta_badge(kpis["total_harvest_rai"], kpis_prev["total_harvest_rai"] if kpis_prev else None, "ไร่")
        badge_prod = get_delta_badge(kpis["total_production_ton"], kpis_prev["total_production_ton"] if kpis_prev else None, "ตัน")
        badge_yield = get_delta_badge(kpis["weighted_yield_kg_rai"], kpis_prev["weighted_yield_kg_rai"] if kpis_prev else None, "กก./ไร่", is_yield=True)

        # 4 Key KPI Cards
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

        with col_kpi1:
            st.markdown(f"""
            <div class="kpi-card kpi-magenta">
                <div class="kpi-label">🌾 เนื้อที่เพาะปลูก (Planted Area)</div>
                <div class="kpi-value">{kpis['total_plant_rai']:,.0f}<span class="kpi-unit">ไร่</span></div>
                <div class="kpi-sub">{badge_plant}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_kpi2:
            st.markdown(f"""
            <div class="kpi-card kpi-cyan">
                <div class="kpi-label">🚜 เนื้อที่เก็บเกี่ยว (Harvested Area)</div>
                <div class="kpi-value">{kpis['total_harvest_rai']:,.0f}<span class="kpi-unit">ไร่</span></div>
                <div class="kpi-sub">{badge_harvest}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_kpi3:
            st.markdown(f"""
            <div class="kpi-card kpi-magenta">
                <div class="kpi-label">📦 ปริมาณผลผลิตรวม (Production)</div>
                <div class="kpi-value">{kpis['total_production_ton']:,.0f}<span class="kpi-unit">ตัน</span></div>
                <div class="kpi-sub">{badge_prod}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_kpi4:
            yield_str = f"{kpis['weighted_yield_kg_rai']:,.1f}" if not np.isnan(kpis['weighted_yield_kg_rai']) else "N/A"
            st.markdown(f"""
            <div class="kpi-card kpi-cyan">
                <div class="kpi-label">⚖️ ผลผลิตต่อไร่ (Weighted Yield)</div>
                <div class="kpi-value">{yield_str}<span class="kpi-unit">กก./ไร่</span></div>
                <div class="kpi-sub">{badge_yield}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Left: Thailand Map | Right: Historical Trend Chart (Requirement C Layout)
        col_map, col_chart = st.columns([1.1, 1.0])

        with col_map:
            st.markdown(f"#### 🗺️ แผนที่การกระจายตัวเชิงพื้นที่ ({sel_metric_title})")
            if geojson_data:
                fig_map = create_thailand_map(
                    df_data=df_year_prov,
                    geojson_data=geojson_data,
                    metric_col=st.session_state.selected_metric,
                    metric_label=sel_metric_title,
                    unit=sel_metric_unit,
                    year=st.session_state.selected_year,
                    product_name=st.session_state.selected_product,
                    selected_province=st.session_state.selected_province if st.session_state.selected_province != "ทั้งหมด" else None
                )
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("ไม่พบไฟล์แผนที่ GeoJSON สำหรับการแสดงผลแผนที่ประเทศไทย")

        with col_chart:
            st.markdown(f"#### 📈 แนวโน้มประวัติศาสตร์ตามตัวชี้วัด (พ.ศ. 2550–2562)")
            if not df_trend_series.empty:
                trend_agg = df_trend_series.groupby("year").agg(
                    production_ton=("production_ton", "sum"),
                    area_plant_rai=("area_plant_rai", "sum"),
                    area_harvest_rai=("area_harvest_rai", "sum")
                ).reset_index()

                trend_agg["calc_yield_per_rai"] = np.where(
                    trend_agg["area_harvest_rai"] > 0,
                    trend_agg["production_ton"] * 1000.0 / trend_agg["area_harvest_rai"],
                    np.nan
                )
                trend_agg["calc_harvest_ratio"] = np.where(
                    trend_agg["area_plant_rai"] > 0,
                    trend_agg["area_harvest_rai"] / trend_agg["area_plant_rai"] * 100.0,
                    np.nan
                )

                fig_trend = create_trend_line_chart(
                    df=trend_agg,
                    x_col="year",
                    y_col=st.session_state.selected_metric,
                    color_col=None,
                    title=f"แนวโน้ม {sel_metric_title} (พ.ศ. 2550–2562)",
                    y_label=sel_metric_title,
                    unit=sel_metric_unit
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลอนุกรมเวลาสำหรับตัวกรองที่เลือก")

        st.markdown("---")

        # Top 10 and Bottom 10 Rankings
        st.markdown(f"### 🏆 การจัดอันดับจังหวัดตามตัวชี้วัด: {sel_metric_title}")
        col_top, col_bot = st.columns(2)

        with col_top:
            st.markdown(f"#### 🥇 10 อันดับจังหวัดสูงสุด (Top 10)")
            top_prov_df = get_top_provinces(df_year_prov, metric=st.session_state.selected_metric, top_n=10, ascending=False)
            fig_top = create_ranking_bar_chart(
                df=top_prov_df,
                x_col=st.session_state.selected_metric,
                y_col="province",
                title=f"10 อันดับสูงสุด ({st.session_state.selected_product} | ปี {st.session_state.selected_year})",
                x_label=sel_metric_title,
                unit=sel_metric_unit,
                selected_item=st.session_state.selected_province if st.session_state.selected_province != "ทั้งหมด" else None,
                is_bottom=False
            )
            st.plotly_chart(fig_top, use_container_width=True)

        with col_bot:
            st.markdown(f"#### 🔻 10 อันดับจังหวัดต่ำสุด (Bottom 10: เฉพาะที่มีข้อมูล > 0)")
            bot_prov_df = get_top_provinces(df_year_prov, metric=st.session_state.selected_metric, top_n=10, ascending=True)
            fig_bot = create_ranking_bar_chart(
                df=bot_prov_df,
                x_col=st.session_state.selected_metric,
                y_col="province",
                title=f"10 อันดับต่ำสุด ({st.session_state.selected_product} | ปี {st.session_state.selected_year})",
                x_label=sel_metric_title,
                unit=sel_metric_unit,
                selected_item=st.session_state.selected_province if st.session_state.selected_province != "ทั้งหมด" else None,
                is_bottom=True
            )
            st.plotly_chart(fig_bot, use_container_width=True)

        # Scale vs Yield Productivity Insight Callout
        st.markdown("""
        <div class="callout callout-warning">
            <span class="callout-title">💡 ข้อสังเกตสำคัญด้านผลิตภาพและการใช้ที่ดิน (Scale vs Efficiency):</span><br>
            <span class="callout-body">
                จังหวัดที่มี <b>ผลผลิตรวมสูงสุด (Total Production)</b> มักเป็นจังหวัดที่มีเนื้อที่เพาะปลูกขนาดใหญ่ แต่ไม่ได้แปลว่ามีประสิทธิภาพหรือ <b>ผลผลิตต่อไร่ (Yield per Rai)</b> สูงสุดเสมอไป ในทางกลับกัน จังหวัดที่มีพื้นที่เพาะปลูกขนาดกลางหรือเล็กอาจมีผลผลิตต่อไร่สูงกว่าเนื่องจากระบบชลประทานและความอุดมสมบูรณ์ของดิน การวิเคราะห์เปรียบเทียบทั้ง <b>ขนาดการผลิต (Scale)</b> และ <b>ประสิทธิภาพการผลิต (Yield Efficiency)</b> ควบคู่กันจึงทำให้เห็นภาพความเป็นจริงอย่างรอบด้าน
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Detailed Data Table with Search, Sort, and CSV Download
        st.markdown("---")
        st.markdown("### 📋 ตารางสถิติการผลิตสินค้าเกษตรรายจังหวัด (Detailed Data Table)")
        table_cols = [
            "region", "province", "product", "year",
            "area_plant_rai", "area_harvest_rai", "production_ton",
            "calc_yield_per_rai", "calc_harvest_ratio", "calc_damaged_area"
        ]
        available_table_cols = [c for c in table_cols if c in df_active.columns]
        display_df = df_active[available_table_cols].copy()

        col_rename_dict = {
            "region": "ภาค",
            "province": "จังหวัด",
            "product": "ชนิดพืช",
            "year": "ปี พ.ศ.",
            "area_plant_rai": "เนื้อที่เพาะปลูก (ไร่)",
            "area_harvest_rai": "เนื้อที่เก็บเกี่ยว (ไร่)",
            "production_ton": "ผลผลิตรวม (ตัน)",
            "calc_yield_per_rai": "ผลผลิตต่อไร่ (กก./ไร่)",
            "calc_harvest_ratio": "อัตราเก็บเกี่ยว (%)",
            "calc_damaged_area": "เนื้อที่เสียหาย (ไร่)"
        }
        display_df = display_df.rename(columns=col_rename_dict)

        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            table_search = st.text_input("🔍 ค้นหาในตาราง (พิมพ์ชื่อจังหวัดหรือชนิดพืช):", key="tab1_table_search")
        with col_t2:
            sort_options = [c for c in display_df.columns if c not in ["ภาค", "ปี พ.ศ."]]
            sort_col = st.selectbox("เรียงลำดับตาม:", options=sort_options, index=sort_options.index("ผลผลิตรวม (ตัน)") if "ผลผลิตรวม (ตัน)" in sort_options else 0)

        if table_search:
            mask = display_df.astype(str).apply(lambda row: row.str.contains(table_search, case=False).any(), axis=1)
            display_df = display_df[mask]

        if sort_col in display_df.columns:
            display_df = display_df.sort_values(by=sort_col, ascending=False)

        csv_bytes = display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        col_t_down1, col_t_down2 = st.columns([3, 1])
        with col_t_down1:
            st.caption(f"แสดงข้อมูลทั้งหมด {len(display_df):,} รายการ")
        with col_t_down2:
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูล (CSV)",
                data=csv_bytes,
                file_name=f"thai_agri_stats_{st.session_state.selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(
            display_df.style.format({
                "เนื้อที่เพาะปลูก (ไร่)": "{:,.0f}",
                "เนื้อที่เก็บเกี่ยว (ไร่)": "{:,.0f}",
                "ผลผลิตรวม (ตัน)": "{:,.0f}",
                "ผลผลิตต่อไร่ (กก./ไร่)": "{:,.1f}",
                "อัตราเก็บเกี่ยว (%)": "{:,.1f}",
                "เนื้อที่เสียหาย (ไร่)": "{:,.0f}"
            }),
            use_container_width=True,
            height=360
        )


# =========================================================
# TAB 2: CLIMATE & CROP ADVISORY (ภูมิอากาศและคำแนะนำการเพาะปลูก)
# =========================================================
with tab2:
    st.markdown("### 🌦️ ภูมิอากาศ คำแนะนำการเพาะปลูก และการบริหารความเสี่ยง (Climate & Crop Advisory)")
    st.caption("บูรณาการข้อมูลตรวจวัดจริงของ สสน. HII (IDW 77 จังหวัด) และ กรมอุตุนิยมวิทยา TMD รายวัน เพื่อให้เกษตรกรตัดสินใจเพาะปลูกและเตรียมรับมือความเสี่ยง")

    target_climate_year = st.session_state.selected_year if st.session_state.selected_year in [2561, 2562] else 2562
    active_crop = st.session_state.selected_product if st.session_state.selected_product != "ทั้งหมด" else "ข้าวนาปี"
    active_prov = st.session_state.selected_province

    # Extract climate variables for active province if available
    prov_rain_val = None
    prov_temp_val = None
    prov_disaster_val = None

    if active_prov != "ทั้งหมด":
        if not df_rain_annual.empty and "province" in df_rain_annual.columns:
            r_match = df_rain_annual[(df_rain_annual["province"] == active_prov) & (df_rain_annual["year"] == target_climate_year)]
            if not r_match.empty and "rainfall_annual_mm" in r_match.columns:
                prov_rain_val = float(r_match["rainfall_annual_mm"].iloc[0])

        if not df_temp_annual.empty and "province" in df_temp_annual.columns:
            t_match = df_temp_annual[(df_temp_annual["province"] == active_prov) & (df_temp_annual["year"] == target_climate_year)]
            if not t_match.empty and "temp_annual_mean" in t_match.columns:
                prov_temp_val = float(t_match["temp_annual_mean"].iloc[0])

        if not df_disaster.empty and "province" in df_disaster.columns:
            d_match = df_disaster[(df_disaster["province"] == active_prov) & (df_disaster["year"] == target_climate_year)]
            if not d_match.empty and "total_disaster_area_rai" in d_match.columns:
                prov_disaster_val = float(d_match["total_disaster_area_rai"].iloc[0])

    # Left: Map with Switchable Layers | Right: Decision Intelligence & 5-Pillar Advisory (Requirement B & C)
    col_tab2_map, col_tab2_dash = st.columns([1.05, 1.15])

    with col_tab2_map:
        st.markdown("#### 🗺️ แผนที่สภาพอากาศและพื้นที่เสี่ยงภัยพิบัติ")
        layer_option = st.radio(
            "เลือกชั้นข้อมูลแผนที่ (Select Climate Map Layer):",
            options=["🌧️ ปริมาณฝนเชิงพื้นที่ HII (มม.)", "🌡️ อุณหภูมิเฉลี่ย HII (°C)", "⚠️ พื้นที่ประสบภัยพิบัติการเกษตร (ไร่)", "📡 เครือข่ายสถานีตรวจวัด TMD"],
            horizontal=True,
            key="tab2_layer_select"
        )

        layer_key = "rain"
        if "อุณหภูมิ" in layer_option:
            layer_key = "temp"
        elif "ภัยพิบัติ" in layer_option:
            layer_key = "disaster"
        elif "สถานี" in layer_option:
            layer_key = "stations"

        if geojson_data:
            fig_clim_map = create_climate_disaster_map(
                df_rain=df_rain_annual,
                df_temp=df_temp_annual,
                df_disaster=df_disaster,
                df_agromet=df_agromet,
                geojson_data=geojson_data,
                layer_type=layer_key,
                year=target_climate_year,
                selected_province=active_prov if active_prov != "ทั้งหมด" else None
            )
            st.plotly_chart(fig_clim_map, use_container_width=True)
        else:
            st.info("ไม่พบไฟล์แผนที่ GeoJSON")

        st.markdown("""
        <div class="callout callout-note small">
            📌 <b>ข้อมูลชั้นแผนที่:</b> สสน. HII ฝนเชิงพื้นที่ IDW (มม.), TMD Agromet รายวัน, ปภ. และ กรมส่งเสริมการเกษตร | ข้อมูลแสดงระดับจังหวัดตามข้อเท็จจริงของระบบเปิดภาครัฐ มิได้จำลองระดับแปลง
        </div>
        """, unsafe_allow_html=True)

    with col_tab2_dash:
        st.markdown(f"#### 💡 สารสนเทศสภาพอากาศและคำแนะนำสำหรับ **{active_crop}**")

        # 1. TMD Live Observation Card
        if not df_agromet.empty and "province" in df_agromet.columns:
            stn_sub = df_agromet[df_agromet["province"] == active_prov] if active_prov != "ทั้งหมด" else df_agromet
            if not stn_sub.empty:
                stn_row = stn_sub.iloc[0]
                stn_name = stn_row.get("station_name", active_prov)
                t_val = f"{stn_row.get('temp_c', 'N/A')} °C" if pd.notna(stn_row.get('temp_c')) else "N/A"
                rh_val = f"{stn_row.get('relative_humidity_pct', 'N/A')}%" if pd.notna(stn_row.get('relative_humidity_pct')) else "N/A"
                r24_col = "rainfall_24h_mm" if "rainfall_24h_mm" in stn_row else ("rainfall_mm" if "rainfall_mm" in stn_row else None)
                r24_val = f"{stn_row.get(r24_col, 0.0):.1f} มม." if r24_col and pd.notna(stn_row.get(r24_col)) else "0.0 มม."
                w_val = f"{stn_row.get('wind_speed_kmh', 0.0):.1f} กม./ชม." if pd.notna(stn_row.get('wind_speed_kmh')) else "0.0"

                st.markdown(f"""
                <div class="callout callout-success">
                    <div class="callout-title">
                        📡 สถานีตรวจอากาศการเกษตร TMD: <b>{stn_name}</b> ({stn_row.get('province', 'ประเทศไทย')})
                    </div>
                    <div class="callout-row">
                        <span>🌡️ อุณหภูมิ: <b>{t_val}</b></span>
                        <span>💧 ความชื้นสัมพัทธ์: <b>{rh_val}</b></span>
                        <span>🌧️ ฝน 24 ชม.: <b>{r24_val}</b></span>
                        <span>💨 ลม: <b>{w_val}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 2. Climate Risk Status Badges
        risk_status = calculate_climate_risk_status(prov_rain_val, prov_temp_val, prov_disaster_val)
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            c_d = risk_status["drought"]["color"]
            b_class = "delta-badge-neg" if c_d == "red" else ("delta-badge-pos" if c_d == "green" else "delta-badge-neutral")
            st.markdown(f"""
            <div class="kpi-card kpi-compact">
                <div class="kpi-label">ภาวะภัยแล้ง / ฝนทิ้งช่วง</div>
                <div class="kpi-status"><span class="{b_class}">{risk_status['drought']['level']}</span></div>
                <div class="kpi-desc">{risk_status['drought']['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_r2:
            c_f = risk_status["flood"]["color"]
            b_class = "delta-badge-neg" if c_f == "red" else ("delta-badge-pos" if c_f == "green" else "delta-badge-neutral")
            st.markdown(f"""
            <div class="kpi-card kpi-compact">
                <div class="kpi-label">ความเสี่ยงอุทกภัย / น้ำท่วม</div>
                <div class="kpi-status"><span class="{b_class}">{risk_status['flood']['level']}</span></div>
                <div class="kpi-desc">{risk_status['flood']['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_r3:
            c_h = risk_status["heat"]["color"]
            b_class = "delta-badge-neg" if c_h == "red" else ("delta-badge-pos" if c_h == "green" else "delta-badge-neutral")
            st.markdown(f"""
            <div class="kpi-card kpi-compact">
                <div class="kpi-label">ความเครียดความร้อน (Heat)</div>
                <div class="kpi-status"><span class="{b_class}">{risk_status['heat']['level']}</span></div>
                <div class="kpi-desc">{risk_status['heat']['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. 5-Pillar Decision Advisory "เกษตรกรควรทำอะไร" (Requirement B)
        advisory_dict = generate_farmer_decision_advisory(
            crop_name=active_crop,
            province_name=active_prov if active_prov != "ทั้งหมด" else "ประเทศไทย",
            rainfall_val=prov_rain_val,
            temp_val=prov_temp_val,
            disaster_val=prov_disaster_val,
            year=target_climate_year
        )

        st.markdown("#### 🎯 เกษตรกรควรทำอะไร (5 เสาหลักการตัดสินใจ)")

        with st.expander("1. 📌 สถานการณ์ปัจจุบัน (Current Situation)", expanded=True):
            st.markdown(advisory_dict["current_situation"])

        with st.expander("2. ⚠️ ความเสี่ยงที่ต้องเฝ้าระวัง (Risks to Watch)", expanded=True):
            for r in advisory_dict["risks_to_watch"]:
                st.markdown(f"- {r}")

        with st.expander("3. 🚜 สิ่งที่ควรเตรียมตัว (Preparations Needed)", expanded=False):
            for p in advisory_dict["preparations_needed"]:
                st.markdown(f"- {p}")

        with st.expander("4. 🌾 การปฏิบัติที่แนะนำ (Recommended Practices)", expanded=False):
            for prac in advisory_dict["recommended_practices"]:
                st.markdown(f"- {prac}")

        with st.expander("5. 📡 เงื่อนไขหรือสัญญาณที่ควรติดตามเพิ่มเติม (Signals to Monitor)", expanded=False):
            for sig in advisory_dict["signals_to_monitor"]:
                st.markdown(f"- {sig}")

        # 4. Planting Window Guide
        st.markdown(f"""
        <div class="callout callout-note">
            <div class="callout-title">🌱 คำแนะนำช่วงเวลาเพาะปลูกที่เหมาะสม: {active_crop}</div>
            <div class="callout-body">
                - <b>ช่วงเวลาเพาะปลูกตามปฏิทินเกษตร:</b> {advisory_dict['planting_window']}<br>
                - <b>ระยะเวลาเจริญเติบโต:</b> {advisory_dict['growth_duration_days']}<br>
                - <b>ความต้องการน้ำและดิน:</b> {advisory_dict['water_soil_req']}<br>
                - <b>หน่วยงานวิชาการต้นทาง:</b> {advisory_dict['source_agency']}<br>
                <div class="callout-foot">
                    {advisory_dict['disclaimer']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Climate Correlation Analysis Row
    st.markdown("---")
    st.markdown("#### 🔬 การวิเคราะห์ความสัมพันธ์เชิงสถิติ: สภาพอากาศ vs ผลผลิต (Climate & Yield Correlations)")
    st.caption("ทดสอบทางสถิติเพื่อดูว่าปริมาณฝนสะสมมีความสัมพันธ์กับผลผลิตต่อไร่มากน้อยเพียงใด")

    joined_nation = join_climate_agriculture_nationwide(
        df_ag=df_ag,
        df_rain_annual=df_rain_annual,
        df_temp_annual=df_temp_annual,
        year=target_climate_year,
        product=active_crop
    )

    if not joined_nation.empty:
        col_cr1, col_cr2 = st.columns([1.1, 0.9])
        with col_cr1:
            stats_nat_rain = calculate_bivariate_stats(joined_nation["rainfall_annual_mm"], joined_nation["calc_yield_per_rai"])
            fig_nat_scat = create_bivariate_scatter_chart(
                joined_nation,
                x_col="rainfall_annual_mm",
                y_col="calc_yield_per_rai",
                title=f"ฝนเชิงพื้นที่ HII vs ผลผลิตต่อไร่ ({active_crop} | ปี พ.ศ. {target_climate_year})",
                x_label="ปริมาณฝนสะสมทั้งปี",
                y_label="ผลผลิตต่อไร่",
                x_unit="มม.",
                y_unit="กก./ไร่",
                text_col="province",
                correlation_val=stats_nat_rain["pearson_r"] if stats_nat_rain["is_valid"] else None,
                p_val=stats_nat_rain["pearson_p"] if stats_nat_rain["is_valid"] else None,
                n_samples=stats_nat_rain["n"] if stats_nat_rain["is_valid"] else None
            )
            st.plotly_chart(fig_nat_scat, use_container_width=True)

        with col_cr2:
            st.markdown("##### 💡 การแปลผลทางสถิติและข้อพึงระวัง")
            interp_nat = generate_climate_interpretation(
                bivariate_result=stats_nat_rain,
                crop_name=active_crop,
                climate_var_name="ปริมาณฝนเชิงพื้นที่ HII (IDW)",
                ag_var_name="ผลผลิตต่อไร่ (Yield)",
                geo_scope=f"77 จังหวัดทั่วประเทศ (ปี {target_climate_year})",
                year_range=str(target_climate_year)
            )
            st.markdown(interp_nat)

            st.markdown("""
            <div class="callout callout-info">
                <span class="callout-title">💡 สหสัมพันธ์ (Correlation) ไม่เท่ากับ ความเป็นเหตุเป็นผล (Causation):</span><br>
                <span class="callout-body">
                    ค่า $r$ สะท้อนทิศทางการเคลื่อนไหวร่วมกันเชิงสถิติเท่านั้น ไม่ได้พิสูจน์ว่าฝนเป็นสาเหตุเดียวของผลผลิตที่เปลี่ยนแปลง เนื่องจากผลผลิตทางการเกษตรยังขึ้นอยู่กับระบบชลประทาน ธาตุอาหารในดิน การป้องกันโรคแมลง และการปฏิบัติแปลงของเกษตรกร
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Seasonal Rain (May-Oct) vs Annual Rain
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⏳ ช่วงเวลาฝนตก (ฝนฤดูเพาะปลูก พ.ค.–ต.ค.) สำคัญกว่าฝนสะสมทั้งปี")
        df_season_rain = analyze_growing_season_rainfall(df_rain_monthly, df_ag, crop=active_crop, year=target_climate_year)
        col_s1, col_s2 = st.columns([1.1, 0.9])
        with col_s1:
            fig_season = create_seasonal_rain_vs_yield_chart(df_season_rain, active_crop, target_climate_year)
            st.plotly_chart(fig_season, use_container_width=True)
        with col_s2:
            st.markdown("""
            <div class="callout callout-note">
                <span class="callout-title">🌾 ปัจจัยจังหวะเวลาของฝน (Rainfall Timing):</span><br>
                <span class="callout-body">
                    การรวมปริมาณฝนทั้งปีอาจบดบังสภาวะแห้งแล้งจริง เนื่องจากพืชเศรษฐกิจต้องการน้ำในระยะวิกฤต เช่น ข้าวต้องการน้ำในระยะแตกกอและตั้งท้องออกรวง (มิ.ย.–ก.ย.) หากฝนตกหนักนอกฤดูเพาะปลูก (เช่น พ.ย.–ธ.ค.) อาจกลายเป็นอุทกภัยสร้างความเสียหายต่อการเก็บเกี่ยวแทนที่จะช่วยเพิ่มผลผลิต
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ไม่มีข้อมูลจับคู่สภาพอากาศและผลผลิตสำหรับปีนี้")


# =========================================================
# TAB 3: MARKET & PRICE INTELLIGENCE (ตลาดและสารสนเทศราคา)
# =========================================================
with tab3:
    st.markdown("### 💰 ตลาด สารสนเทศราคา และส่วนต่างกำไร (Market & Price Intelligence)")
    st.caption("ข้อมูลราคาสินค้าเกษตรหน้าฟาร์มจริงจากสำนักงานเศรษฐกิจการเกษตร (สศก.) และ ศูนย์ข้อมูลเกษตรแห่งชาติ (NABC) พ.ศ. 2561–2562 (ความถี่: รายสัปดาห์)")

    # Dynamic Crop Selection based on real data in df_prices (Requirement 2.1)
    price_crops = sorted(df_prices["product"].dropna().unique().tolist()) if not df_prices.empty else []

    # Filter controls for Tab 3: Search box, Crop dropdown, and Year filter
    col_t3_search, col_t3_crop, col_t3_year = st.columns([1.3, 1.7, 1.0])

    with col_t3_search:
        price_crop_search = st.text_input(
            "🔍 ค้นหาชนิดพืชราคาตลาด:",
            placeholder="เช่น ข้าว, ทุเรียน, ยาง, ปาล์ม, มันสำปะหลัง...",
            key="tab3_price_search_box"
        )

    # Filter available price crops by search query if provided
    if price_crop_search and price_crop_search.strip():
        search_kw = price_crop_search.strip().lower()
        active_price_crop_options = [c for c in price_crops if search_kw in c.lower()]
        if not active_price_crop_options:
            st.warning(f"⚠️ ไม่พบสินค้าที่มีคำว่า '{price_crop_search}' ในชุดข้อมูลราคา สศก.")
            active_price_crop_options = price_crops
    else:
        active_price_crop_options = price_crops

    # Default crop selection based on global product or first available
    default_price_crop = "ข้าวเปลือกเจ้าหอมมะลิ"
    if st.session_state.selected_product != "ทั้งหมด":
        # Find matching crop in active options
        candidates = [c for c in active_price_crop_options if st.session_state.selected_product in c or c in st.session_state.selected_product]
        if candidates:
            default_price_crop = candidates[0]
        elif active_price_crop_options:
            default_price_crop = active_price_crop_options[0]
    elif active_price_crop_options:
        default_price_crop = "ข้าวเปลือกเจ้าหอมมะลิ" if "ข้าวเปลือกเจ้าหอมมะลิ" in active_price_crop_options else active_price_crop_options[0]

    with col_t3_crop:
        curr_p_idx = active_price_crop_options.index(default_price_crop) if default_price_crop in active_price_crop_options else 0
        selected_price_crop = st.selectbox(
            "🌱 สินค้าเกษตรสำหรับวิเคราะห์ราคา:",
            options=active_price_crop_options if active_price_crop_options else ["ไม่มีข้อมูล"],
            index=curr_p_idx,
            key="tab3_price_crop_select"
        )

    with col_t3_year:
        price_year_options = ["ทั้งหมด (พ.ศ. 2561–2562)", "ปี พ.ศ. 2562", "ปี พ.ศ. 2561"]
        selected_price_year_choice = st.selectbox(
            "📅 รอบปีข้อมูลราคา (สศก.):",
            options=price_year_options,
            index=0,
            key="tab3_price_year_select"
        )
        if "2562" in selected_price_year_choice and "ทั้งหมด" not in selected_price_year_choice:
            filter_price_year = 2562
        elif "2561" in selected_price_year_choice and "ทั้งหมด" not in selected_price_year_choice:
            filter_price_year = 2561
        else:
            filter_price_year = None

    # Filter prices DataFrame dynamically
    df_prices_filtered = df_prices.copy()
    if filter_price_year is not None and not df_prices_filtered.empty:
        df_prices_filtered = df_prices_filtered[df_prices_filtered["year"] == filter_price_year]

    price_sub = df_prices_filtered[df_prices_filtered["product"] == selected_price_crop].copy() if not df_prices_filtered.empty else pd.DataFrame()

    # 2-Column Responsive Layout: Left = Map | Right = Price Intelligence
    col_t3_map, col_t3_dash = st.columns([1.05, 1.15])

    with col_t3_map:
        st.markdown(f"#### 🗺️ แผนที่การกระจายผลผลิตในตลาด: **{selected_price_crop}**")
        if geojson_data:
            fig_market_map = create_market_price_map(
                df_ag=df_ag,
                geojson_data=geojson_data,
                crop_name=selected_price_crop,
                year=st.session_state.selected_year if st.session_state.selected_year in available_years else latest_year,
                selected_province=st.session_state.selected_province if st.session_state.selected_province != "ทั้งหมด" else None
            )
            st.plotly_chart(fig_market_map, use_container_width=True)
        else:
            st.info("ไม่พบไฟล์แผนที่ GeoJSON")

        st.markdown("""
        <div class="callout callout-warning small">
            📌 <b>หมายเหตุความโปร่งใสด้านระดับพื้นที่ของข้อมูลราคา:</b><br>
            ข้อมูลราคาหน้าฟาร์มที่ สศก./NABC สำรวจและเผยแพร่เป็น <b>ราคาเฉลี่ยระดับประเทศ (National Benchmark)</b> ในแต่ละสัปดาห์ 
            แดชบอร์ดนี้จึงแสดงแผนที่ฝั่งซ้ายเป็น <b>สัดส่วนและปริมาณผลผลิตเข้าสู่ตลาดรายจังหวัด</b> เพื่อชี้แหล่งอุปทานสำคัญ 
            โดยไม่นำราคาเฉลี่ยระดับประเทศไปสวมเป็นราคาของแต่ละจังหวัด เพื่อป้องกันการชี้นำผิดพลาดตามมาตรฐาน Data Quality
        </div>
        """, unsafe_allow_html=True)

    with col_t3_dash:
        st.markdown(f"#### 📊 สารสนเทศราคารายสัปดาห์: **{selected_price_crop}**")

        if not price_sub.empty:
            try:
                price_metrics = compute_price_summary_metrics(price_sub, selected_price_crop, unit_mode="native")
            except TypeError:
                price_metrics = compute_price_summary_metrics(price_sub, selected_price_crop)
        else:
            price_metrics = {
                "has_data": False,
                "message": f"ไม่พบข้อมูลราคาสำหรับ '{selected_price_crop}' ในช่วงเวลาที่เลือก",
                "unit": "บาท/กก.",
                "latest_price": 0.0,
                "mean_price": 0.0,
                "max_price": 0.0,
                "min_price": 0.0,
                "wow_change": 0.0,
                "wow_pct": 0.0,
                "latest_period": "ไม่มีข้อมูล"
            }

        if not isinstance(price_metrics, dict):
            price_metrics = {"has_data": False, "message": "ไม่สามารถคำนวณสถิติราคาได้"}

        if price_metrics.get("has_data", False):
            def _fmt_price_val(v, default="0.00", fmt="{:,.2f}"):
                if v is None or pd.isna(v):
                    return default
                try:
                    return fmt.format(float(v))
                except (ValueError, TypeError):
                    return default

            latest_p_str = _fmt_price_val(price_metrics.get("latest_price"))
            mean_p_str = _fmt_price_val(price_metrics.get("mean_price"))
            max_p_str = _fmt_price_val(price_metrics.get("max_price"))
            min_p_str = _fmt_price_val(price_metrics.get("min_price"))
            unit_str = str(price_metrics.get("unit", "บาท/กก."))
            latest_period_str = str(price_metrics.get("latest_period", "ไม่มีข้อมูล"))

            wow_val = price_metrics.get("wow_change", 0.0)
            wow_p = price_metrics.get("wow_pct", 0.0)
            try:
                wow_num = float(wow_val) if (wow_val is not None and not pd.isna(wow_val)) else 0.0
                wow_pct_num = float(wow_p) if (wow_p is not None and not pd.isna(wow_p)) else 0.0
            except (ValueError, TypeError):
                wow_num = 0.0
                wow_pct_num = 0.0

            wow_badge = "delta-badge-pos" if wow_num >= 0 else "delta-badge-neg"
            wow_str = f"{wow_num:+.2f} ({wow_pct_num:+.1f}%)"

            # 4 Price KPI Cards
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            with col_p1:
                st.markdown(f"""
                <div class="kpi-card kpi-compact kpi-magenta">
                    <div class="kpi-label">ราคาล่าสุด</div>
                    <div class="kpi-value">{latest_p_str}<span class="kpi-unit">{unit_str}</span></div>
                    <div class="kpi-sub"><span class="delta-badge-pos">ล่าสุด: {latest_period_str}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col_p2:
                st.markdown(f"""
                <div class="kpi-card kpi-compact kpi-cyan">
                    <div class="kpi-label">ราคาเฉลี่ยรอบที่เลือก</div>
                    <div class="kpi-value">{mean_p_str}<span class="kpi-unit">{unit_str}</span></div>
                    <div class="kpi-sub"><span class="delta-badge-neutral">{selected_price_year_choice}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col_p3:
                st.markdown(f"""
                <div class="kpi-card kpi-compact kpi-magenta">
                    <div class="kpi-label">ราคาสูงสุด-ต่ำสุด</div>
                    <div class="kpi-value kpi-value-sm">{max_p_str}<span class="kpi-unit">/ {min_p_str}</span></div>
                    <div class="kpi-sub"><span class="delta-badge-neutral">{unit_str}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col_p4:
                st.markdown(f"""
                <div class="kpi-card kpi-compact kpi-cyan">
                    <div class="kpi-label">การเปลี่ยนแปลงรายสัปดาห์</div>
                    <div class="kpi-value kpi-value-sm"><span class="{wow_badge}">{wow_str}</span></div>
                    <div class="kpi-sub"><span class="delta-badge-neutral">เทียบสัปดาห์ก่อนหน้า</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Weekly Price Trend Chart
            fig_p_trend = create_price_trend_chart(price_sub, selected_price_crop, unit_mode="native")
            st.plotly_chart(fig_p_trend, use_container_width=True)

            # Cost vs Price Margin Comparison
            st.markdown("---")
            st.markdown("#### ⚖️ การเปรียบเทียบราคาขายเฉลี่ย vs ต้นทุนการผลิตต่อหน่วย")
            margin_summary = compare_production_cost_and_price(df_cost, price_sub, crop=selected_price_crop, year=2562)
            if margin_summary.get("has_data", False):
                fig_margin = create_cost_price_margin_chart(margin_summary)
                st.plotly_chart(fig_margin, use_container_width=True)
            else:
                st.info(f"ℹ️ สศก. เผยแพร่โครงสร้างต้นทุนมาตรฐานเฉพาะพืชเศรษฐกิจหลัก 5 ชนิด (ข้าวนาปี, ข้าวนาปรัง, ข้าวโพดเลี้ยงสัตว์, มันสำปะหลัง, อ้อยโรงงาน) จึงไม่มีข้อมูลต้นทุนเปรียบเทียบสำหรับ '{selected_price_crop}'")

        else:
            st.warning(f"⚠️ {price_metrics.get('message', 'ไม่มีข้อมูลราคาสำหรับสินค้าที่เลือก')}")

    # Searchable & Sortable Price Table with CSV Export
    st.markdown("---")
    st.markdown("### 📋 ตารางสถิติราคาหน้าฟาร์มรายสัปดาห์ (Searchable Price Table)")
    if not price_sub.empty:
        price_display = price_sub.sort_values(by=["year", "month", "week"], ascending=False).reset_index(drop=True)
        col_pr_ren = {
            "product": "ชนิดสินค้าเกษตร",
            "year": "ปี พ.ศ.",
            "month": "เดือน",
            "week": "สัปดาห์ที่",
            "native_price": "ราคาหน้าฟาร์มจริง",
            "native_unit": "หน่วยวัด",
            "price_baht_per_kg": "ราคาเทียบเคียง (บาท/กก.)",
            "frequency": "ความถี่",
            "data_source": "แหล่งข้อมูล"
        }
        price_table = price_display.rename(columns={k: v for k, v in col_pr_ren.items() if k in price_display.columns})
        available_p_cols = [v for k, v in col_pr_ren.items() if v in price_table.columns]
        price_table = price_table[available_p_cols]

        col_pt1, col_pt2 = st.columns([3, 1])
        with col_pt1:
            st.caption(f"แสดงข้อมูลราคารวมทั้งหมด {len(price_table):,} สัปดาห์ (สำนักงานเศรษฐกิจการเกษตร สศก. & NABC)")
        with col_pt2:
            p_csv = price_table.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูลราคา (CSV)",
                data=p_csv,
                file_name=f"thai_farmgate_prices_{selected_price_crop}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(
            price_table.style.format({
                "ราคาหน้าฟาร์มจริง": "{:,.2f}",
                "ราคาเทียบเคียง (บาท/กก.)": "{:,.2f}"
            }),
            use_container_width=True,
            height=280
        )
    else:
        st.info("ไม่มีข้อมูลในตารางสำหรับสินค้าหรือรอบปีที่เลือก")

    # Price Outlook & Future Projection Disclaimer (Requirement B.Tab3)
    st.markdown("""
    <div class="callout callout-danger">
        <span class="callout-title">⚠️ ข้อพึงระวังเกี่ยวกับแนวโน้มราคาอนาคต (Price Outlook Disclaimer):</span><br>
        <span class="callout-body">
            ราคาสินค้าเกษตรมีความผันผวนสูงตามจังหวะฤดูกาลเก็บเกี่ยว (Supply Shock) ปริมาณสต็อกโลก และสภาวะเศรษฐกิจมหภาค 
            การพยากรณ์ราคาอนาคตจำเป็นต้องอาศัยแบบจำลองเศรษฐมิติที่ผ่านการทดสอบย้อนหลัง (Backtesting) มิควรคาดเดาโดยไม่มีหลักฐาน 
            เกษตรกรควรติดตามราคาซื้อขายจริงแบบรายวันจากจุดรับซื้อในพื้นที่ และใช้สัญญาซื้อขายล่วงหน้าหรือการรวมกลุ่มเกษตรกรเพื่อกระจายความเสี่ยง
        </span>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# TAB 4: PRODUCTION & FARM ECONOMICS (ผลผลิตและเศรษฐศาสตร์ฟาร์ม)
# =========================================================
with tab4:
    st.markdown("### 🚜 ผลผลิตและเศรษฐศาสตร์ฟาร์ม (Production Drivers & Farm Economics)")
    st.caption("วิเคราะห์ปัจจัยขับเคลื่อนผลผลิต (ระบบชลประทาน, ดิน Agri-Map, ต้นทุนเครื่องจักรกล, ภัยธรรมชาติ) และเครื่องคำนวณกำไรสุทธิฟาร์ม")

    driver_crop = st.session_state.selected_product if st.session_state.selected_product != "ทั้งหมด" else "ข้าวนาปี"
    driver_year = st.session_state.selected_year if st.session_state.selected_year in [2561, 2562] else 2562
    driver_prov = st.session_state.selected_province

    # 2-Column Layout: Left = Production Driver Map | Right = Drivers & Calculator (Requirement B & C)
    col_t4_map, col_t4_dash = st.columns([1.05, 1.15])

    with col_t4_map:
        st.markdown("#### 🗺️ แผนที่ปัจจัยขับเคลื่อนผลผลิตการเกษตร")
        driver_layer = st.radio(
            "เลือกตัวแปรขับเคลื่อนผลผลิต (Select Driver Map Layer):",
            options=["⚖️ ผลผลิตต่อไร่ (สศก. กก./ไร่)", "💧 สัดส่วนพื้นที่ชลประทาน (RID %)", "🌱 ความเหมาะสมของดิน S1+S2 (Agri-Map %)", "⚠️ พื้นที่ประสบภัยพิบัติ (ปภ. ไร่)"],
            horizontal=True,
            key="tab4_driver_layer_select"
        )

        d_layer_key = "yield"
        if "ชลประทาน" in driver_layer:
            d_layer_key = "irrigation"
        elif "ดิน" in driver_layer:
            d_layer_key = "soil"
        elif "ภัยพิบัติ" in driver_layer:
            d_layer_key = "disaster"

        if geojson_data:
            fig_driver_map = create_production_driver_map(
                df_ag=df_ag,
                df_irrig=df_irrig,
                df_soil=df_soil,
                df_disaster=df_disaster,
                geojson_data=geojson_data,
                layer_type=d_layer_key,
                crop_name=driver_crop,
                year=driver_year,
                selected_province=driver_prov if driver_prov != "ทั้งหมด" else None
            )
            st.plotly_chart(fig_driver_map, use_container_width=True)
        else:
            st.info("ไม่พบไฟล์แผนที่ GeoJSON")

        st.markdown("""
        <div class="callout callout-note small">
            📌 <b>แหล่งข้อมูลปัจจัยการผลิต:</b> กรมชลประทาน (RID), กรมพัฒนาที่ดิน (Agri-Map), กรมส่งเสริมการเกษตร (DOAE), ปภ. และ สศก.
        </div>
        """, unsafe_allow_html=True)

    with col_t4_dash:
        st.markdown("#### ⚙️ ปัจจัยขับเคลื่อนผลผลิต (Production Driver Insights)")

        tab_driver_charts, tab_profit_calc = st.tabs([
            "📊 กราฟวิเคราะห์ปัจจัยการผลิต",
            "🧮 เครื่องคำนวณกำไรและจุดคุ้มทุนฟาร์ม"
        ])

        with tab_driver_charts:
            driver_topic = st.selectbox(
                "เลือกมิติปัจจัยที่ต้องการวิเคราะห์เชิงลึก:",
                options=[
                    "1. 💧 แหล่งน้ำและระบบชลประทาน (RID vs Yield)",
                    "2. 🌱 ความเหมาะสมของดิน (Agri-Map LDD)",
                    "3. ⚙️ โครงสร้างต้นทุนและเครื่องจักรกล (OAE)",
                    "4. ⚠️ ภัยธรรมชาติ น้ำท่วมและภัยแล้ง (DOAE/DDPM)"
                ],
                key="tab4_topic_select"
            )

            if "1. 💧 แหล่งน้ำ" in driver_topic:
                df_irrig_yield = join_irrigation_and_yield(df_ag, df_irrig, crop=driver_crop, year=driver_year)
                fig_irrig = create_irrigation_vs_yield_chart(df_irrig_yield, driver_crop, driver_year)
                st.plotly_chart(fig_irrig, use_container_width=True)
                st.markdown("""
                - **บทบาทชลประทาน:** แปลงที่มีระบบชลประทานสามารถควบคุมน้ำสม่ำเสมอ ลดความเสี่ยงฝนทิ้งช่วง และมีผลผลิตต่อไร่สูงกว่าแปลงนอกเขตชลประทานอย่างมีนัยสำคัญ
                """)

            elif "2. 🌱 ความเหมาะสมของดิน" in driver_topic:
                fig_soil = create_soil_suitability_bar_chart(df_soil, driver_crop, top_n=12)
                st.plotly_chart(fig_soil, use_container_width=True)
                st.markdown("""
                - **แนวทาง Agri-Map กรมพัฒนาที่ดิน:** พื้นที่เหมาะสมสูง (S1) ควรรักษาความอุดมสมบูรณ์ พื้นที่เหมาะสมปานกลาง-น้อย (S2/S3) ควรปรับปรุงดินด้วยอินทรียวัตถุ และพื้นที่ไม่เหมาะสม (N) ควรปรับเปลี่ยนพืช (Zoning)
                """)

            elif "3. ⚙️ โครงสร้างต้นทุน" in driver_topic:
                cost_summary = compare_production_cost_and_price(df_cost, df_prices, crop=driver_crop, year=driver_year)
                if cost_summary.get("has_data", False):
                    fig_cost_str = create_cost_structure_breakdown_chart(
                        cost_summary["cost_breakdown"], driver_crop, cost_summary["total_cost_rai"], driver_year
                    )
                    st.plotly_chart(fig_cost_str, use_container_width=True)
                    st.markdown(f"- **สัดส่วนค่าบริการเครื่องจักรกล:** {cost_summary['mechanization_share_pct']:.1f}% ของต้นทุนรวม ช่วยชดเชยการขาดแคลนแรงงานภาคการเกษตร")
                else:
                    st.info("ไม่มีข้อมูลโครงสร้างต้นทุนสำหรับพืชนี้")

            else:
                fig_dis = create_disaster_impact_chart(df_disaster, driver_year, top_n=10)
                st.plotly_chart(fig_dis, use_container_width=True)
                st.markdown("- **การจัดการความเสี่ยง:** อุทกภัยสร้างความเสียหายรวดเร็วในที่ลุ่ม ส่วนภัยแล้งกระทบผลผลิตเป็นวงกว้าง เกษตรกรควรจัดทำสระน้ำไร่นาและขุดลอกคูคลอง")

        with tab_profit_calc:
            st.markdown("##### 🧮 เครื่องคำนวณรายรับและกำไรสุทธิฟาร์ม (Farm Profit Calculator)")
            st.caption("คำนวณกำไรสุทธิ จุดคุ้มทุนด้านผลผลิต และจุดคุ้มทุนด้านราคา โดยแยกช่องกรอกของผู้ใช้ออกจากเกณฑ์อ้างอิงภาครัฐ")

            # Government benchmark reference values
            cost_bench = df_cost[df_cost["crop"] == driver_crop]
            default_cost_rai = float(cost_bench["total_cost_rai"].values[0]) if not cost_bench.empty else 4500.0
            default_yield_rai = float(cost_bench["benchmark_yield_kg_rai"].values[0]) if (not cost_bench.empty and "benchmark_yield_kg_rai" in cost_bench.columns) else 450.0

            price_sub = df_prices[df_prices["product"] == driver_crop]
            default_price_kg = float(price_sub["price_baht_per_kg"].mean()) if not price_sub.empty else 10.50

            st.markdown(f"""
            <div class="callout callout-note">
                <b>📌 ค่าอ้างอิงเฉลี่ยภาครัฐ (สศก. สำหรับ {driver_crop}):</b> 
                ต้นทุนเฉลี่ย: <b>{default_cost_rai:,.0f} บาท/ไร่</b> | 
                ผลผลิตเฉลี่ย: <b>{default_yield_rai:,.0f} กก./ไร่</b> | 
                ราคาหน้าฟาร์มเฉลี่ย: <b>{default_price_kg:,.2f} บาท/กก.</b>
            </div>
            """, unsafe_allow_html=True)

            col_in1, col_in2 = st.columns(2)
            with col_in1:
                in_area = st.number_input("1. เนื้อที่เพาะปลูกของท่าน (ไร่):", min_value=1.0, max_value=10000.0, value=20.0, step=1.0, key="calc_area_input")
                in_yield = st.number_input("2. ผลผลิตต่อไร่ที่คาดว่าจะได้ (กก./ไร่):", min_value=10.0, max_value=5000.0, value=default_yield_rai, step=10.0, key="calc_yield_input")
            with col_in2:
                in_cost = st.number_input("3. ต้นทุนรวมต่อไร่ (บาท/ไร่):", min_value=100.0, max_value=50000.0, value=default_cost_rai, step=100.0, key="calc_cost_input")
                in_price = st.number_input("4. ราคาขายที่คาดหวัง (บาท/กก.):", min_value=0.5, max_value=200.0, value=default_price_kg, step=0.25, key="calc_price_input")

            # Dynamic Calculations
            tot_cost = in_area * in_cost
            tot_yield = in_area * in_yield
            tot_revenue = tot_yield * in_price
            est_profit = tot_revenue - tot_cost
            breakeven_yield = tot_cost / (in_area * in_price) if (in_area * in_price) > 0 else 0.0
            breakeven_price = tot_cost / tot_yield if tot_yield > 0 else 0.0

            st.markdown("<br>", unsafe_allow_html=True)
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            with col_res1:
                st.metric("ต้นทุนรวม (Total Cost)", f"{tot_cost:,.0f} บาท")
            with col_res2:
                st.metric("ผลผลิตรวม (Total Yield)", f"{tot_yield:,.0f} กก.", help=f"คิดเป็น {tot_yield/1000:,.2f} ตัน")
            with col_res3:
                st.metric("รายรับรวม (Revenue)", f"{tot_revenue:,.0f} บาท")
            with col_res4:
                st.metric("กำไรสุทธิประมาณการ", f"{est_profit:,.0f} บาท", delta=f"{est_profit / tot_cost * 100:+.1f}% ROI" if tot_cost > 0 else None)

            col_be1, col_be2 = st.columns(2)
            with col_be1:
                st.info(f"🎯 **จุดคุ้มทุนด้านผลผลิต (Break-even Yield):** **{breakeven_yield:,.1f} กก./ไร่** (หากได้ต่ำกว่านี้จะขาดทุน ณ ราคา {in_price:.2f} บาท/กก.)")
            with col_be2:
                st.info(f"🎯 **จุดคุ้มทุนด้านราคา (Break-even Price):** **{breakeven_price:,.2f} บาท/กก.** (หากขายได้ต่ำกว่านี้จะขาดทุน ณ ผลผลิต {in_yield:,.0f} กก./ไร่)")

            st.markdown("""
            <div class="callout callout-warning small">
                <span class="callout-title">⚠️ ข้อจำกัดความรับผิดชอบ (Disclaimer):</span><br>
                <span class="callout-body">
                    ผลการคำนวณเป็นเพียงการประมาณการเบื้องต้นจากตัวเลขที่ผู้ใช้กำหนดขึ้น มิใช่การยืนยันผลประกอบการจริงจากระบบบัญชีฟาร์ม เกษตรกรควรพิจารณาความเสี่ยงด้านสภาพอากาศ ความผันผวนของราคาตลาด และคุณภาพผลผลิตจริงประกอบการตัดสินใจ
                </span>
            </div>
            """, unsafe_allow_html=True)
