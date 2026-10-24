"""
Cleaning layer: turns the tidy CSVs from the data pipeline (data/clean/*.csv, see
pipeline/ and handoff_n.md) into the wide tables app.py works with.

Conventions used by app.py
  * year      -> Buddhist Era (B.E.) integer, e.g. 2562
  * province  -> canonical Thai province name (77 provinces)
  * region    -> one of REGION_NAMES (5-region split used by the filter bar)
  * missing values stay NaN (never 0)
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from pipeline.province import PROVINCES, to_pro_code

COUNTRY_NAME = "ประเทศไทย"
BE_OFFSET = 543

# 5-region grouping used by the region selector in app.py
NORTH, NORTHEAST, CENTRAL, EAST, SOUTH = (
    "ภาคเหนือ", "ภาคตะวันออกเฉียงเหนือ", "ภาคกลาง", "ภาคตะวันออก", "ภาคใต้")
REGION_NAMES: List[str] = [NORTH, NORTHEAST, CENTRAL, EAST, SOUTH]
_EAST_CODES = {"20", "21", "22", "23", "24", "25", "27"}


def _region_for(code: str, region_oae: str) -> str:
    if code in _EAST_CODES:
        return EAST
    return {"เหนือ": NORTH, "ตะวันออกเฉียงเหนือ": NORTHEAST, "กลาง": CENTRAL, "ใต้": SOUTH}[region_oae]


OFFICIAL_77_PROVINCES: List[str] = [th for _, th, _, _ in PROVINCES]
CODE_TO_PROVINCE: Dict[str, str] = {c: th for c, th, _, _ in PROVINCES}
PROVINCE_TO_REGION: Dict[str, str] = {th: _region_for(c, r) for c, th, _, r in PROVINCES}
REGION_TO_PROVINCES: Dict[str, List[str]] = {
    reg: sorted(p for p, r in PROVINCE_TO_REGION.items() if r == reg) for reg in REGION_NAMES}

# pipeline crop code -> Thai product name shown in the app
CROP_NAMES_TH: Dict[str, str] = {
    "cassava": "มันสำปะหลังโรงงาน",
    "maize": "ข้าวโพดเลี้ยงสัตว์",
    "rubber": "ยางพารา",
    "oil_palm": "ปาล์มน้ำมัน",
    "rice": "ข้าวนาปี",
    "rice_dry": "ข้าวนาปรัง",
    "sugarcane": "อ้อยโรงงาน",
    "pineapple": "สับปะรดโรงงาน",
    "longan": "ลำไย",
    "rambutan": "เงาะ",
    "durian": "ทุเรียน",
    "mangosteen": "มังคุด",
    "coconut": "มะพร้าว",
    "coffee_robusta": "กาแฟโรบัสตา",
    "coffee_arabica": "กาแฟอาราบิกา",
}

PRICE_PRODUCT_NAMES_TH: Dict[str, str] = {
    "rice_hommali": "ข้าวเปลือกเจ้าหอมมะลิ",
    "rice_white": "ข้าวเปลือกเจ้า",
    "rice_glutinous": "ข้าวเปลือกเหนียว",
}

AG_COLUMNS = ["year", "product", "province", "region", "area_plant_rai", "area_harvest_rai",
              "production_ton", "yield_per_rai", "calc_yield_per_rai", "calc_harvest_ratio",
              "calc_damaged_area", "area_basis", "geo_level", "source"]


def _be(year_ce) -> pd.Series:
    return (pd.to_numeric(year_ce, errors="coerce") + BE_OFFSET).astype("Int64")


def _province_names(codes: pd.Series) -> pd.Series:
    return codes.astype(str).str.zfill(2).map(CODE_TO_PROVINCE)


# ---------------------------------------------------------------------------
# D01 production
# ---------------------------------------------------------------------------
# Perennial crops publish standing / tapped / bearing area instead of planted / harvested.
_PLANT_AREA = ["area_plant", "area_standing"]
_HARVEST_AREA = ["area_harvest", "area_tapped", "area_bearing"]
_SOURCE_YIELD = ["yield_harvested", "yield_tapped", "yield_bearing", "yield"]


def clean_agriculture_data(tidy: pd.DataFrame) -> pd.DataFrame:
    """Tidy production rows -> one row per (year, product, province)."""
    if tidy is None or tidy.empty:
        return pd.DataFrame(columns=AG_COLUMNS)
    t = tidy.copy()
    t["province_code"] = t["province_code"].astype(str).str.zfill(2)
    t = t[t["province_code"].isin(CODE_TO_PROVINCE)]
    wide = t.pivot_table(index=["year_ce", "crop", "province_code"], columns="metric", values="value",
                         aggfunc="first").reset_index()

    def first_available(cols):
        out = pd.Series(np.nan, index=wide.index)
        for c in cols:
            if c in wide.columns:
                out = out.fillna(wide[c])
        return out

    df = pd.DataFrame({
        "year": _be(wide["year_ce"]),
        "product": wide["crop"].map(lambda c: CROP_NAMES_TH.get(c, c)),
        "province": _province_names(wide["province_code"]),
        "area_plant_rai": first_available(_PLANT_AREA),
        "area_harvest_rai": first_available(_HARVEST_AREA),
        "production_ton": first_available(["production"]),
        "yield_per_rai": first_available(_SOURCE_YIELD),
    })
    # Record which area definitions were used (perennials: standing area / tapped or bearing area)
    basis = pd.Series("planted/harvested", index=wide.index)
    if "area_tapped" in wide.columns:
        basis = basis.mask(wide["area_tapped"].notna(), "standing/tapped")
    if "area_bearing" in wide.columns:
        basis = basis.mask(wide["area_bearing"].notna(), "standing/bearing")
    df["area_basis"] = basis.values
    df["region"] = df["province"].map(PROVINCE_TO_REGION)
    df["calc_yield_per_rai"] = np.where(df["area_harvest_rai"] > 0,
                                        df["production_ton"] * 1000.0 / df["area_harvest_rai"], np.nan)
    df["calc_harvest_ratio"] = np.where(df["area_plant_rai"] > 0,
                                        df["area_harvest_rai"] / df["area_plant_rai"] * 100.0, np.nan)
    df["calc_damaged_area"] = np.nan  # not published in the OAE files used
    df["geo_level"] = "province"
    df["source"] = "สศก. (OAE Catalog)"
    df = df.dropna(subset=["year", "province"]).astype({"year": int})
    return df[AG_COLUMNS].sort_values(["year", "product", "province"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# D07 rain / temperature (monthly by province)
# ---------------------------------------------------------------------------
def _monthly(tidy: pd.DataFrame, metric: str, value_name: str) -> pd.DataFrame:
    cols = ["province", "region", "year", "month", value_name, "source_id"]
    if tidy is None or tidy.empty:
        return pd.DataFrame(columns=cols)
    m = tidy[tidy["metric"] == metric].copy()
    if m.empty:
        return pd.DataFrame(columns=cols)
    m["province"] = _province_names(m["province_code"])
    m["year"] = _be(m["year_ce"])
    m["month"] = m["period"].astype(str).str[5:7].astype(int)
    m[value_name] = pd.to_numeric(m["value"], errors="coerce")
    m["region"] = m["province"].map(PROVINCE_TO_REGION)
    m = m.dropna(subset=["province", "year"])
    return m[cols].astype({"year": int}).reset_index(drop=True)


def clean_spatial_rain_data(tidy: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly + annual provincial rainfall. Annual = sum of 12 months; incomplete years dropped."""
    monthly = _monthly(tidy, "rain", "rainfall_mm")
    if monthly.empty:
        return monthly, pd.DataFrame(columns=["province", "region", "year", "rainfall_annual_mm", "source_id"])
    g = monthly.groupby(["province", "region", "year"], as_index=False).agg(
        rainfall_annual_mm=("rainfall_mm", "sum"), n=("rainfall_mm", "count"), source_id=("source_id", "first"))
    annual = g[g["n"] == 12].drop(columns="n").reset_index(drop=True)
    return monthly, annual


def clean_national_rain_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """National annual rainfall series (D08 substitute). Expects columns year/year_ce and rainfall."""
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame(columns=["year", "rainfall_annual_mm"])
    d = df.copy()
    ycol = next(c for c in d.columns if "year" in c.lower() or c == "ปี")
    vcol = next(c for c in d.columns if c != ycol and pd.to_numeric(d[c], errors="coerce").notna().mean() > 0.5)
    y = pd.to_numeric(d[ycol], errors="coerce")
    annual = pd.DataFrame({"year": np.where(y < 2400, y + BE_OFFSET, y).astype(int),
                           "rainfall_annual_mm": pd.to_numeric(d[vcol], errors="coerce")})
    return pd.DataFrame(), annual.dropna()


def clean_provincial_temp_data(tidy: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly tmax/tmin -> annual mean of monthly mid-range ((tmax+tmin)/2). Only complete years."""
    tmax = _monthly(tidy, "tmax", "tmax_c")
    tmin = _monthly(tidy, "tmin", "tmin_c")
    cols = ["province", "region", "year", "temp_annual_mean", "temp_annual_max", "temp_annual_min"]
    if tmax.empty or tmin.empty:
        return pd.DataFrame(), pd.DataFrame(columns=cols)
    m = tmax.merge(tmin[["province", "year", "month", "tmin_c"]], on=["province", "year", "month"])
    m["tmid_c"] = (m["tmax_c"] + m["tmin_c"]) / 2
    g = m.groupby(["province", "region", "year"], as_index=False).agg(
        temp_annual_mean=("tmid_c", "mean"), temp_annual_max=("tmax_c", "max"),
        temp_annual_min=("tmin_c", "min"), n=("tmid_c", "count"))
    return m, g[g["n"] == 12][cols].reset_index(drop=True)


# ---------------------------------------------------------------------------
# D02 prices
# ---------------------------------------------------------------------------
PRICE_COLUMNS = ["product", "year", "month", "week", "period", "native_price", "native_unit",
                 "price_baht_per_kg", "frequency", "data_source"]


def clean_oae_farmgate_prices(tidy: pd.DataFrame) -> pd.DataFrame:
    if tidy is None or tidy.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    p = tidy.copy()
    parts = p["period"].astype(str).str.extract(r"^(\d{4})-(\d{2})-W(\d)$")
    out = pd.DataFrame({
        "product": p["crop"].map(lambda c: PRICE_PRODUCT_NAMES_TH.get(c, c)),
        "year": _be(parts[0]),
        "month": pd.to_numeric(parts[1], errors="coerce"),
        "week": pd.to_numeric(parts[2], errors="coerce"),
        "period": p["period"],
        "price_baht_per_kg": pd.to_numeric(p["value"], errors="coerce"),
    })
    out["native_price"] = out["price_baht_per_kg"] * 1000.0
    out["native_unit"] = "บาท/ตัน"
    out["frequency"] = "รายสัปดาห์"
    out["data_source"] = "สศก. / NABC"
    out = out.dropna(subset=["year", "month", "week", "price_baht_per_kg"])
    return out.astype({"year": int, "month": int, "week": int})[PRICE_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# D09 TMD observations
# ---------------------------------------------------------------------------
AGROMET_COLUMNS = ["station_name", "province", "lat", "lon", "temp_c", "relative_humidity_pct",
                   "rainfall_24h_mm", "wind_speed_kmh", "observed_at"]


def validate_agromet_schema(df: pd.DataFrame) -> bool:
    return df is not None and not df.empty and {"station_name", "province", "lat", "lon"}.issubset(df.columns)


def clean_tmd_daily_agromet(payload) -> pd.DataFrame:
    """Parse a cached TMD WeatherToday JSON payload (Stations -> Station[] -> Observation)."""
    if not payload:
        return pd.DataFrame(columns=AGROMET_COLUMNS)
    stations = payload.get("Stations", {}).get("Station", []) if isinstance(payload, dict) else []
    rows = []
    for s in stations:
        obs = s.get("Observation", {}) or {}

        def num(v):
            v = v.get("Value") if isinstance(v, dict) else v
            try:
                return float(v)
            except (TypeError, ValueError):
                return np.nan
        prov_raw = s.get("Province") or s.get("ProvinceTh") or ""
        code = to_pro_code(prov_raw)
        wind = num(obs.get("WindSpeed"))
        rows.append({
            "station_name": s.get("StationNameThai") or s.get("StationNameEnglish"),
            "province": CODE_TO_PROVINCE.get(code, prov_raw),
            "lat": num(s.get("Latitude")), "lon": num(s.get("Longitude")),
            "temp_c": num(obs.get("Temperature") or obs.get("AirTemperature")),
            "relative_humidity_pct": num(obs.get("RelativeHumidity")),
            "rainfall_24h_mm": num(obs.get("Rainfall") or obs.get("Rain24Hr")),
            "wind_speed_kmh": wind * 3.6 if pd.notna(wind) else np.nan,  # TMD reports m/s
            "observed_at": obs.get("DateTime"),
        })
    return pd.DataFrame(rows, columns=AGROMET_COLUMNS)


# ---------------------------------------------------------------------------
# D04 irrigation, D05 soil, D03 cost, D06 disaster
# ---------------------------------------------------------------------------
IRRIG_COLUMNS = ["province", "region", "year", "irrigated_area_rai", "source_url"]
SOIL_COLUMNS = ["province", "region", "crop", "s1_rai", "s2_rai", "s3_rai", "n_rai", "total_rai", "s1s2_pct"]
COST_COLUMNS = ["crop", "year", "total_cost_rai", "cost_per_kg", "benchmark_yield_kg_rai",
                "labour_cost_rai", "material_cost_rai", "machinery_cost_rai", "other_cost_rai", "source_url"]
DISASTER_COLUMNS = ["province", "region", "year", "flood_area_rai", "drought_area_rai",
                    "storm_area_rai", "total_disaster_area_rai"]


def clean_provincial_irrigation_data(df: pd.DataFrame) -> pd.DataFrame:
    """Manual extract data/raw/D04/irrigated_area_province.csv: province,year_be,irrigated_area_rai,source_url."""
    if df is None or df.empty:
        return pd.DataFrame(columns=IRRIG_COLUMNS)
    d = df.copy()
    d["province"] = d["province"].map(to_pro_code).map(CODE_TO_PROVINCE)
    d["year"] = pd.to_numeric(d["year_be"], errors="coerce")
    d["irrigated_area_rai"] = pd.to_numeric(d["irrigated_area_rai"], errors="coerce")
    d["region"] = d["province"].map(PROVINCE_TO_REGION)
    d["source_url"] = d.get("source_url", "")
    return d.dropna(subset=["province", "year"]).astype({"year": int})[IRRIG_COLUMNS].reset_index(drop=True)


def clean_ldd_soil_suitability_data(tidy: pd.DataFrame) -> pd.DataFrame:
    if tidy is None or tidy.empty:
        return pd.DataFrame(columns=SOIL_COLUMNS)
    t = tidy.copy()
    t["province"] = _province_names(t["province_code"])
    w = t.pivot_table(index=["province", "crop"], columns="metric", values="value", aggfunc="sum").reset_index()
    for k in ("s1", "s2", "s3", "n"):
        col = f"suitability_{k}"
        w[f"{k}_rai"] = w[col] if col in w.columns else np.nan
    w["total_rai"] = w[["s1_rai", "s2_rai", "s3_rai", "n_rai"]].sum(axis=1, min_count=1)
    w["s1s2_pct"] = np.where(w["total_rai"] > 0, (w["s1_rai"].fillna(0) + w["s2_rai"].fillna(0)) / w["total_rai"] * 100, np.nan)
    w["crop"] = w["crop"].map(lambda c: CROP_NAMES_TH.get(c, c))
    w["region"] = w["province"].map(PROVINCE_TO_REGION)
    return w.dropna(subset=["province"])[SOIL_COLUMNS].reset_index(drop=True)


def clean_oae_production_cost_data(df: pd.DataFrame) -> pd.DataFrame:
    """Manual table data/raw/D03/production_cost_manual.csv (see pipeline/sources.py). Never estimated."""
    if df is None or df.empty:
        return pd.DataFrame(columns=COST_COLUMNS)
    d = df.copy()
    d["year"] = pd.to_numeric(d.get("year_be"), errors="coerce")
    d["total_cost_rai"] = pd.to_numeric(d.get("cost_baht_per_rai"), errors="coerce")
    d["cost_per_kg"] = pd.to_numeric(d.get("cost_baht_per_kg"), errors="coerce")
    for c in COST_COLUMNS:
        if c not in d.columns:
            d[c] = np.nan
    d["crop"] = d["crop"].map(lambda c: CROP_NAMES_TH.get(c, c))
    return d[COST_COLUMNS].reset_index(drop=True)


def clean_disaster_affected_data(df: pd.DataFrame) -> pd.DataFrame:
    """Manual DDPM extracts combined into province,year_be,hazard,area_rai rows."""
    if df is None or df.empty:
        return pd.DataFrame(columns=DISASTER_COLUMNS)
    d = df.copy()
    d["province"] = d["province"].map(to_pro_code).map(CODE_TO_PROVINCE)
    d["year"] = pd.to_numeric(d["year_be"], errors="coerce")
    d["area_rai"] = pd.to_numeric(d["area_rai"], errors="coerce")
    w = d.pivot_table(index=["province", "year"], columns="hazard", values="area_rai", aggfunc="sum").reset_index()
    for h in ("flood", "drought", "storm"):
        w[f"{h}_area_rai"] = w[h] if h in w.columns else np.nan
    w["total_disaster_area_rai"] = w[["flood_area_rai", "drought_area_rai", "storm_area_rai"]].sum(axis=1, min_count=1)
    w["region"] = w["province"].map(PROVINCE_TO_REGION)
    return w.dropna(subset=["province"]).astype({"year": int})[DISASTER_COLUMNS].reset_index(drop=True)
