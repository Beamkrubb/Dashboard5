"""
Analytical helpers for the four tabs. Every function works on the cleaned tables from
src/data_cleaning.py and returns empty results (not invented numbers) when data is missing.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .feature_engineering import aggregate_by

ALL = "ทั้งหมด"


def _product_rows(df_ag: pd.DataFrame, product: Optional[str], year: Optional[int] = None) -> pd.DataFrame:
    d = df_ag
    if product and product != ALL:
        d = d[d["product"] == product]
    if year is not None:
        d = d[d["year"] == int(year)]
    return d


# ---------------------------------------------------------------------------
# Tab 1
# ---------------------------------------------------------------------------
def get_top_provinces(df: pd.DataFrame, metric: str, top_n: int = 10, ascending: bool = False) -> pd.DataFrame:
    """Province ranking. Rows for several crops are summed first and ratios recomputed.
    Bottom rankings only include provinces with a value > 0."""
    g = aggregate_by(df, ["province"])
    if metric not in g.columns:
        return pd.DataFrame(columns=["province", metric])
    g = g.dropna(subset=[metric])
    if ascending:
        g = g[g[metric] > 0]
    return g.sort_values(metric, ascending=ascending).head(top_n).reset_index(drop=True)


def get_top_crops(df: pd.DataFrame, metric: str = "production_ton", top_n: int = 10) -> pd.DataFrame:
    g = aggregate_by(df, ["product"])
    return g.sort_values(metric, ascending=False).head(top_n).reset_index(drop=True)


def classify_area_yield_quadrants(df: pd.DataFrame) -> pd.DataFrame:
    """Scale (planted area) vs efficiency (yield) quadrants split at the medians."""
    g = aggregate_by(df, ["province"]).dropna(subset=["area_plant_rai", "calc_yield_per_rai"])
    if g.empty:
        return g.assign(quadrant=pd.Series(dtype=str))
    a_med, y_med = g["area_plant_rai"].median(), g["calc_yield_per_rai"].median()
    g["quadrant"] = np.select(
        [(g.area_plant_rai >= a_med) & (g.calc_yield_per_rai >= y_med),
         (g.area_plant_rai >= a_med) & (g.calc_yield_per_rai < y_med),
         (g.area_plant_rai < a_med) & (g.calc_yield_per_rai >= y_med)],
        ["พื้นที่มาก-ผลผลิตต่อไร่สูง", "พื้นที่มาก-ผลผลิตต่อไร่ต่ำ", "พื้นที่น้อย-ผลผลิตต่อไร่สูง"],
        default="พื้นที่น้อย-ผลผลิตต่อไร่ต่ำ")
    return g


# ---------------------------------------------------------------------------
# Tab 2: climate x production
# ---------------------------------------------------------------------------
def join_climate_agriculture_nationwide(df_ag, df_rain_annual, df_temp_annual, year, product) -> pd.DataFrame:
    """Province-level join on province + year only (handoff_n.md). Empty if either side is missing."""
    ag = aggregate_by(_product_rows(df_ag, product, year), ["province"])
    if ag.empty or df_rain_annual is None or df_rain_annual.empty:
        return pd.DataFrame()
    rain = df_rain_annual[df_rain_annual["year"] == int(year)][["province", "rainfall_annual_mm"]]
    out = ag.merge(rain, on="province", how="inner")
    if df_temp_annual is not None and not df_temp_annual.empty:
        temp = df_temp_annual[df_temp_annual["year"] == int(year)][["province", "temp_annual_mean"]]
        out = out.merge(temp, on="province", how="left")
    return out.dropna(subset=["rainfall_annual_mm", "calc_yield_per_rai"]).reset_index(drop=True)


def calculate_bivariate_stats(x: pd.Series, y: pd.Series) -> Dict:
    d = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    n = len(d)
    res = {"is_valid": False, "n": n, "pearson_r": np.nan, "pearson_p": np.nan,
           "spearman_r": np.nan, "spearman_p": np.nan}
    if n < 5 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return res
    from scipy import stats
    pr = stats.pearsonr(d["x"], d["y"])
    sr = stats.spearmanr(d["x"], d["y"])
    res.update(is_valid=True, pearson_r=float(pr[0]), pearson_p=float(pr[1]),
               spearman_r=float(sr[0]), spearman_p=float(sr[1]))
    return res


def _strength(r: float) -> str:
    a = abs(r)
    return "สูง" if a >= 0.7 else "ปานกลาง" if a >= 0.4 else "ต่ำ" if a >= 0.2 else "แทบไม่มี"


def generate_climate_interpretation(bivariate_result: Dict, crop_name: str, climate_var_name: str,
                                    ag_var_name: str, geo_scope: str, year_range: str) -> str:
    r = bivariate_result
    if not r.get("is_valid"):
        return (f"ข้อมูลไม่พอสำหรับทดสอบทางสถิติ (n = {r.get('n', 0)} จังหวัด, ต้องการอย่างน้อย 5) "
                f"สำหรับ **{crop_name}** — ไม่สรุปความสัมพันธ์")
    direction = "ทางบวก" if r["pearson_r"] > 0 else "ทางลบ"
    sig = "มีนัยสำคัญทางสถิติ (p < 0.05)" if r["pearson_p"] < 0.05 else "ไม่มีนัยสำคัญทางสถิติ (p ≥ 0.05)"
    return (f"- **{climate_var_name}** กับ **{ag_var_name}** ของ **{crop_name}** มีความสัมพันธ์{direction}"
            f"ระดับ{_strength(r['pearson_r'])} (Pearson r = {r['pearson_r']:.2f}, p = {r['pearson_p']:.3f}; "
            f"Spearman ρ = {r['spearman_r']:.2f})\n"
            f"- ผลทดสอบ{sig} จากกลุ่มตัวอย่าง n = {r['n']} จังหวัด ({geo_scope})\n"
            f"- เป็นข้อมูลภาคตัดขวางปีเดียว ({year_range}) จึงสะท้อนความแตกต่างระหว่างจังหวัด ไม่ใช่ผลของฝนต่อผลผลิตตามเวลา")


def analyze_growing_season_rainfall(df_rain_monthly, df_ag, crop, year) -> pd.DataFrame:
    """Growing-season (May–Oct) vs annual rain per province, joined with yield."""
    cols = ["province", "season_rain_mm", "annual_rain_mm", "season_share_pct", "calc_yield_per_rai"]
    if df_rain_monthly is None or df_rain_monthly.empty:
        return pd.DataFrame(columns=cols)
    m = df_rain_monthly[df_rain_monthly["year"] == int(year)]
    g = m.groupby("province").agg(
        annual_rain_mm=("rainfall_mm", "sum"), n=("rainfall_mm", "count"),
        season_rain_mm=("rainfall_mm", lambda s: s[m.loc[s.index, "month"].between(5, 10)].sum())).reset_index()
    g = g[g["n"] == 12]
    g["season_share_pct"] = np.where(g["annual_rain_mm"] > 0, g["season_rain_mm"] / g["annual_rain_mm"] * 100, np.nan)
    ag = aggregate_by(_product_rows(df_ag, crop, year), ["province"])[["province", "calc_yield_per_rai"]]
    return g.merge(ag, on="province", how="left")[cols].reset_index(drop=True)


THRESHOLDS = {"drought_mm": 1000.0, "dry_mm": 1200.0, "wet_mm": 2000.0, "very_wet_mm": 2500.0,
              "hot_c": 29.0, "warm_c": 28.0}


def calculate_climate_risk_status(rain_val: Optional[float], temp_val: Optional[float],
                                  disaster_val: Optional[float]) -> Dict:
    """Simple, transparent screening rules (thresholds in THRESHOLDS). Not a forecast."""
    na = {"level": "ไม่มีข้อมูล", "color": "grey", "desc": "ไม่มีข้อมูลสำหรับจังหวัด/ปีที่เลือก"}
    t = THRESHOLDS
    if rain_val is None or pd.isna(rain_val):
        drought = flood = dict(na)
    else:
        if rain_val < t["drought_mm"]:
            drought = {"level": "สูง", "color": "red", "desc": f"ฝนทั้งปี {rain_val:,.0f} มม. (< {t['drought_mm']:,.0f})"}
        elif rain_val < t["dry_mm"]:
            drought = {"level": "ปานกลาง", "color": "grey", "desc": f"ฝนทั้งปี {rain_val:,.0f} มม. ({t['drought_mm']:,.0f}–{t['dry_mm']:,.0f})"}
        else:
            drought = {"level": "ต่ำ", "color": "green", "desc": f"ฝนทั้งปี {rain_val:,.0f} มม. (≥ {t['dry_mm']:,.0f})"}
        if rain_val >= t["very_wet_mm"] or (disaster_val is not None and not pd.isna(disaster_val) and disaster_val > 0):
            flood = {"level": "สูง", "color": "red", "desc": f"ฝน {rain_val:,.0f} มม." + (
                f" · พื้นที่ประสบภัย {disaster_val:,.0f} ไร่" if disaster_val else "")}
        elif rain_val >= t["wet_mm"]:
            flood = {"level": "ปานกลาง", "color": "grey", "desc": f"ฝน {rain_val:,.0f} มม. ({t['wet_mm']:,.0f}–{t['very_wet_mm']:,.0f})"}
        else:
            flood = {"level": "ต่ำ", "color": "green", "desc": f"ฝน {rain_val:,.0f} มม. (< {t['wet_mm']:,.0f})"}
    if temp_val is None or pd.isna(temp_val):
        heat = dict(na)
    elif temp_val >= t["hot_c"]:
        heat = {"level": "สูง", "color": "red", "desc": f"อุณหภูมิเฉลี่ย {temp_val:.1f}°C (≥ {t['hot_c']})"}
    elif temp_val >= t["warm_c"]:
        heat = {"level": "ปานกลาง", "color": "grey", "desc": f"อุณหภูมิเฉลี่ย {temp_val:.1f}°C"}
    else:
        heat = {"level": "ต่ำ", "color": "green", "desc": f"อุณหภูมิเฉลี่ย {temp_val:.1f}°C (< {t['warm_c']})"}
    return {"drought": drought, "flood": flood, "heat": heat}


# General agronomic calendar (Department of Agriculture / Rice Department public guidance).
CROP_CALENDAR = {
    "ข้าวนาปี": {"planting_window": "พ.ค.–ส.ค. (ต้นฤดูฝน)", "growth_duration_days": "ประมาณ 110–150 วัน ตามพันธุ์และความไวแสง",
                 "water_soil_req": "ต้องการน้ำขังในระยะแตกกอถึงออกรวง ดินเหนียว/ร่วนเหนียว", "source_agency": "กรมการข้าว"},
    "ข้าวนาปรัง": {"planting_window": "พ.ย.–ก.พ. (นอกฤดูฝน ต้องมีน้ำชลประทาน)", "growth_duration_days": "ประมาณ 100–120 วัน",
                   "water_soil_req": "ต้องพึ่งน้ำชลประทานตลอดฤดู", "source_agency": "กรมการข้าว / กรมชลประทาน"},
    "มันสำปะหลังโรงงาน": {"planting_window": "ต้นฤดูฝน (เม.ย.–มิ.ย.) หรือปลายฤดูฝน (ต.ค.–พ.ย.)", "growth_duration_days": "ประมาณ 8–12 เดือน",
                          "water_soil_req": "ทนแล้งได้ดี ดินร่วนปนทรายระบายน้ำดี", "source_agency": "กรมวิชาการเกษตร"},
    "ข้าวโพดเลี้ยงสัตว์": {"planting_window": "ต้นฤดูฝน (พ.ค.–ก.ค.)", "growth_duration_days": "ประมาณ 110–120 วัน",
                           "water_soil_req": "ต้องการน้ำสม่ำเสมอช่วงออกดอก ดินร่วนระบายน้ำดี", "source_agency": "กรมวิชาการเกษตร"},
    "ยางพารา": {"planting_window": "ต้นฤดูฝน (พ.ค.–ก.ค.)", "growth_duration_days": "เริ่มกรีดได้เมื่ออายุประมาณ 6–7 ปี",
                "water_soil_req": "ฝนกระจายตลอดปี ดินลึกระบายน้ำดี", "source_agency": "การยางแห่งประเทศไทย"},
    "ปาล์มน้ำมัน": {"planting_window": "ต้นฤดูฝน", "growth_duration_days": "เริ่มให้ผลผลิตเมื่ออายุประมาณ 30 เดือน",
                    "water_soil_req": "ต้องการฝนสม่ำเสมอ ไม่มีช่วงแล้งยาว", "source_agency": "กรมวิชาการเกษตร"},
}
_DEFAULT_CAL = {"planting_window": "ดูปฏิทินเพาะปลูกของกรมส่งเสริมการเกษตรในพื้นที่", "growth_duration_days": "ขึ้นกับพันธุ์",
                "water_soil_req": "ดูคำแนะนำ Agri-Map ของกรมพัฒนาที่ดิน", "source_agency": "กรมส่งเสริมการเกษตร"}


def get_crop_calendar_guide(crop_name: str) -> Dict[str, str]:
    return CROP_CALENDAR.get(crop_name, _DEFAULT_CAL)


def generate_farmer_decision_advisory(crop_name, province_name, rainfall_val, temp_val, disaster_val, year) -> Dict:
    risk = calculate_climate_risk_status(rainfall_val, temp_val, disaster_val)
    cal = get_crop_calendar_guide(crop_name)
    facts = []
    if rainfall_val is not None and not pd.isna(rainfall_val):
        facts.append(f"ฝนสะสมทั้งปี {rainfall_val:,.0f} มม.")
    if temp_val is not None and not pd.isna(temp_val):
        facts.append(f"อุณหภูมิเฉลี่ย {temp_val:.1f}°C")
    if disaster_val is not None and not pd.isna(disaster_val):
        facts.append(f"พื้นที่ประสบภัย {disaster_val:,.0f} ไร่")
    situation = (f"**{province_name} · ปี พ.ศ. {year} · {crop_name}:** " +
                 (", ".join(facts) if facts else "ยังไม่มีข้อมูลภูมิอากาศรายจังหวัดสำหรับปีนี้ (เลือกจังหวัดและปีที่มีข้อมูล)"))
    risks = [f"ภัยแล้ง/ฝนทิ้งช่วง: {risk['drought']['level']} — {risk['drought']['desc']}",
             f"น้ำท่วม: {risk['flood']['level']} — {risk['flood']['desc']}",
             f"ความร้อน: {risk['heat']['level']} — {risk['heat']['desc']}"]
    prep = ["วางแผนแหล่งน้ำสำรอง (สระน้ำในไร่นา) ก่อนเข้าฤดูเพาะปลูก" if risk["drought"]["color"] == "red"
            else "ตรวจสอบระบบระบายน้ำและคันนาก่อนฤดูฝน",
            "เตรียมพันธุ์ที่เหมาะกับพื้นที่ตามคำแนะนำ Agri-Map",
            "ขึ้นทะเบียนเกษตรกรและติดตามประกาศเขตภัยพิบัติเพื่อสิทธิ์รับการช่วยเหลือ"]
    practices = [f"ปลูกในช่วง {cal['planting_window']}", f"ความต้องการน้ำและดิน: {cal['water_soil_req']}",
                 "ตรวจวิเคราะห์ดินและใส่ปุ๋ยตามค่าวิเคราะห์เพื่อลดต้นทุน"]
    signals = ["พยากรณ์อากาศ 7 วันของกรมอุตุนิยมวิทยา", "ปริมาณน้ำในเขื่อนและประกาศจัดสรรน้ำของกรมชลประทาน",
               "ราคารับซื้อรายสัปดาห์ของ สศก.", "ประกาศเตือนภัยของ ปภ."]
    return {"current_situation": situation, "risks_to_watch": risks, "preparations_needed": prep,
            "recommended_practices": practices, "signals_to_monitor": signals, **cal,
            "disclaimer": "คำแนะนำทั่วไปจากเกณฑ์อย่างง่ายและข้อมูลสาธารณะ ไม่ใช่คำแนะนำเฉพาะแปลง ควรปรึกษาเกษตรอำเภอ"}


# ---------------------------------------------------------------------------
# Tab 3: prices
# ---------------------------------------------------------------------------
def compute_price_summary_metrics(price_sub: pd.DataFrame, crop: str, unit_mode: str = "native") -> Dict:
    if price_sub is None or price_sub.empty:
        return {"has_data": False, "message": f"ไม่พบข้อมูลราคาสำหรับ '{crop}'"}
    p = price_sub.sort_values(["year", "month", "week"])
    native = unit_mode == "native" and "native_price" in p.columns
    col = "native_price" if native else "price_baht_per_kg"
    unit = str(p["native_unit"].iloc[-1]) if native else "บาท/กก."
    s = p[col].astype(float)
    latest, prev = s.iloc[-1], (s.iloc[-2] if len(s) > 1 else np.nan)
    last = p.iloc[-1]
    return {"has_data": True, "unit": unit, "latest_price": latest, "mean_price": s.mean(),
            "max_price": s.max(), "min_price": s.min(),
            "wow_change": latest - prev if pd.notna(prev) else np.nan,
            "wow_pct": (latest - prev) / prev * 100 if pd.notna(prev) and prev else np.nan,
            "latest_period": f"พ.ศ. {int(last['year'])} เดือน {int(last['month'])} สัปดาห์ {int(last['week'])}",
            "n_weeks": int(len(s))}


def compare_production_cost_and_price(df_cost: pd.DataFrame, df_prices: pd.DataFrame, crop: str, year: int) -> Dict:
    """Cost vs farm-gate price. has_data=False unless a real OAE cost row exists for the crop."""
    if df_cost is None or df_cost.empty or "crop" not in df_cost.columns:
        return {"has_data": False}
    c = df_cost[df_cost["crop"] == crop]
    if c.empty:
        return {"has_data": False}
    row = c[c["year"] == year].iloc[0] if (c["year"] == year).any() else c.sort_values("year").iloc[-1]
    parts = {"ค่าแรงงาน": row.get("labour_cost_rai"), "ค่าวัสดุ": row.get("material_cost_rai"),
             "ค่าเครื่องจักร": row.get("machinery_cost_rai"), "อื่น ๆ": row.get("other_cost_rai")}
    breakdown = {k: float(v) for k, v in parts.items() if v is not None and pd.notna(v)}
    total = float(row["total_cost_rai"]) if pd.notna(row["total_cost_rai"]) else np.nan
    mech = breakdown.get("ค่าเครื่องจักร", np.nan)
    avg_price = np.nan
    if df_prices is not None and not df_prices.empty and "product" in df_prices.columns:
        pp = df_prices[df_prices["product"] == crop]
        avg_price = float(pp["price_baht_per_kg"].mean()) if not pp.empty else np.nan
    cost_kg = float(row["cost_per_kg"]) if pd.notna(row.get("cost_per_kg")) else np.nan
    return {"has_data": True, "crop": crop, "year": int(row["year"]) if pd.notna(row["year"]) else year,
            "total_cost_rai": total, "cost_breakdown": breakdown, "cost_per_kg": cost_kg,
            "avg_price_kg": avg_price, "margin_kg": avg_price - cost_kg if pd.notna(avg_price) and pd.notna(cost_kg) else np.nan,
            "mechanization_share_pct": mech / total * 100 if pd.notna(mech) and total else np.nan}


# ---------------------------------------------------------------------------
# Tab 4: production drivers & farm economics
# ---------------------------------------------------------------------------
def join_irrigation_and_yield(df_ag, df_irrig, crop, year) -> pd.DataFrame:
    ag = aggregate_by(_product_rows(df_ag, crop, year), ["province"])
    if df_irrig is None or df_irrig.empty or ag.empty:
        return pd.DataFrame(columns=["province", "irrigated_area_rai", "calc_yield_per_rai"])
    ir = df_irrig[df_irrig["year"] == int(year)][["province", "irrigated_area_rai"]]
    return ag.merge(ir, on="province", how="inner")


def join_soil_suitability_and_yield(df_ag, df_soil, crop, year) -> pd.DataFrame:
    ag = aggregate_by(_product_rows(df_ag, crop, year), ["province"])
    if df_soil is None or df_soil.empty or ag.empty:
        return pd.DataFrame()
    return ag.merge(df_soil[df_soil["crop"] == crop], on="province", how="inner")


def join_disaster_and_yield(df_ag, df_disaster, crop, year) -> pd.DataFrame:
    ag = aggregate_by(_product_rows(df_ag, crop, year), ["province"])
    if df_disaster is None or df_disaster.empty or ag.empty:
        return pd.DataFrame()
    return ag.merge(df_disaster[df_disaster["year"] == int(year)], on="province", how="inner")


def calculate_farm_budget(area_rai: float, yield_kg_rai: float, cost_rai: float, price_kg: float) -> Dict:
    cost = area_rai * cost_rai
    output = area_rai * yield_kg_rai
    revenue = output * price_kg
    return {"total_cost": cost, "total_yield_kg": output, "revenue": revenue, "profit": revenue - cost,
            "breakeven_yield": cost / (area_rai * price_kg) if area_rai * price_kg else np.nan,
            "breakeven_price": cost / output if output else np.nan}


def calculate_enhanced_farm_profit(area_rai, yield_kg_rai, cost_rai, price_kg,
                                   yield_shocks=(-0.2, 0.0, 0.2), price_shocks=(-0.2, 0.0, 0.2)) -> pd.DataFrame:
    """Profit under combined yield / price scenarios."""
    rows = []
    for ys in yield_shocks:
        for ps in price_shocks:
            b = calculate_farm_budget(area_rai, yield_kg_rai * (1 + ys), cost_rai, price_kg * (1 + ps))
            rows.append({"yield_change_pct": ys * 100, "price_change_pct": ps * 100, **b})
    return pd.DataFrame(rows)
