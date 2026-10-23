"""
Raw -> tidy transforms (handoff_n.md step 2).

Output schema (every clean CSV):
    province_code, province_th, year_ce, period, crop, metric, value, unit, source_id, source_url

The real file layouts were not inspectable when this was written (portals blocked
automation), so parsers are schema-tolerant: they detect the province column, the
year column (B.E. or C.E.) or year-wide columns, and map Thai/English headers to
metrics by keyword. Every run writes a report of unmatched provinces/columns so
the mapping can be tightened against the real files.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .province import add_province_code, to_pro_code

TIDY_COLUMNS = ["province_code", "province_th", "year_ce", "period", "crop", "metric",
                "value", "unit", "source_id", "source_url"]

# keyword (lower-case, no spaces) -> (metric, unit). Order matters: specific first.
METRIC_KEYWORDS: List[Tuple[str, str, str]] = [
    ("harvest_ratio", "harvest_ratio", "%"),
    ("อัตราการเก็บเกี่ยว", "harvest_ratio", "%"),
    ("damage", "area_damaged", "rai"),
    # OAE attribute names (verified against real files 2026-10-23)
    ("ผลผลิตต่อเนื้อที่เก็บเกี่ยว", "yield_harvested", "kg/rai"),
    ("ผลผลิตต่อเนื้อที่เพาะปลูก", "yield_planted", "kg/rai"),
    ("ผลผลิตต่อเนื้อที่ให้ผล", "yield_bearing", "kg/rai"),
    ("ผลผลิตต่อเนื้อที่กรีด", "yield_tapped", "kg/rai"),
    ("ผลผลิตต่อไร่", "yield", "kg/rai"),
    ("yield", "yield", "kg/rai"),
    ("เนื้อที่เพาะปลูก", "area_plant", "rai"),
    ("เนื้อที่ปลูก", "area_plant", "rai"),
    ("plant", "area_plant", "rai"),
    ("เนื้อที่ยืนต้น", "area_standing", "rai"),
    ("เนื้อที่ให้ผล", "area_bearing", "rai"),
    ("เนื้อที่เก็บเกี่ยว", "area_harvest", "rai"),
    ("เนื้อที่กรีด", "area_tapped", "rai"),
    ("harvest", "area_harvest", "rai"),
    ("เสียหาย", "area_damaged", "rai"),
    ("ผลผลิต", "production", "ton"),
    ("production", "production", "ton"),
    ("product", "production", "ton"),
]

PROVINCE_HEADERS = ("จังหวัด", "province", "prov", "pro_th", "changwat", "ชื่อจังหวัด")
YEAR_HEADERS = ("ปี", "year", "ปีเพาะปลูก", "crop_year", "พ.ศ.", "ปีพ.ศ.")


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def read_table(path: Path, sheet=0) -> pd.DataFrame:
    """Read CSV (UTF-8/UTF-8-BOM/cp874) or Excel into a DataFrame of strings + numbers."""
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return _promote_header(pd.read_excel(path, sheet_name=sheet, header=None))
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp874", "tis-620"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"cannot decode {path}")
    # Government CSVs often have title/note rows above the header with fewer fields,
    # which pandas' C parser rejects; read ragged rows with the csv module instead.
    rows = list(csv.reader(io.StringIO(text)))
    width = max((len(r) for r in rows), default=0)
    rows = [r + [None] * (width - len(r)) for r in rows]
    df = pd.DataFrame(rows, dtype=object).replace({"": None})
    return _promote_header(df)


def _promote_header(df: pd.DataFrame) -> pd.DataFrame:
    """Use the first row that contains a province-like header as the header row."""
    df = df.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    for i in range(min(len(df), 15)):
        cells = [str(c).strip().lower() for c in df.iloc[i].tolist()]
        if any(any(h in c for h in PROVINCE_HEADERS) for c in cells):
            hdr = [str(c).strip() if pd.notna(c) else f"col{j}" for j, c in enumerate(df.iloc[i].tolist())]
            out = df.iloc[i + 1:].reset_index(drop=True)
            out.columns = _dedupe(hdr)
            return out
    df.columns = _dedupe([str(c) for c in df.columns])
    return df


def _dedupe(cols: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    out = []
    for c in cols:
        n = seen.get(c, 0)
        out.append(c if n == 0 else f"{c}_{n}")
        seen[c] = n + 1
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def to_number(s: pd.Series) -> pd.Series:
    """'1,234.5' -> 1234.5; '-', '', 'n.a.' -> NaN (missing stays missing, never 0)."""
    cleaned = (s.astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False)
               .str.strip().replace({"-": np.nan, "": np.nan, "n.a.": np.nan, "na": np.nan,
                                     "nan": np.nan, "None": np.nan, "…": np.nan}))
    return pd.to_numeric(cleaned, errors="coerce")


def parse_year(v) -> Tuple[Optional[int], Optional[str]]:
    """Return (year_ce, crop_year_label). Accepts 2562, '2562/63', 2019, '2019/20'."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None, None
    s = str(v).strip()
    m = re.match(r"^(\d{4})(?:\.0)?(?:\s*/\s*(\d{2,4}))?$", s)
    if not m:
        return None, None
    y = int(m.group(1))
    year_ce = y - 543 if y > 2400 else y
    label = s if m.group(2) else None
    return year_ce, label


def _find_col(cols, candidates) -> Optional[str]:
    low = {c: str(c).strip().lower().replace(" ", "") for c in cols}
    for c, l in low.items():
        if any(l == h.replace(" ", "") for h in candidates):
            return c
    for c, l in low.items():
        if any(h.replace(" ", "") in l for h in candidates):
            return c
    return None


def metric_for(header: str) -> Optional[Tuple[str, str]]:
    h = str(header).strip().lower().replace(" ", "")
    for kw, metric, unit in METRIC_KEYWORDS:
        if kw in h:
            return metric, unit
    return None


def _year_like(col) -> Optional[int]:
    y, _ = parse_year(col)
    return y if y and 1950 <= y <= 2100 else None


def _finish(df: pd.DataFrame, source_id: str, source_url: str) -> pd.DataFrame:
    df = df.dropna(subset=["province_code", "value"]).copy()
    df["source_id"] = source_id
    df["source_url"] = source_url
    df["year_ce"] = df["year_ce"].astype("Int64")
    return df[TIDY_COLUMNS].sort_values(["province_code", "year_ce", "crop", "metric", "period"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# D01 production (long or year-wide)
# ---------------------------------------------------------------------------
def tidy_production(raw: pd.DataFrame, crop: str, source_id: str = "D01", source_url: str = "",
                    report: Optional[dict] = None) -> pd.DataFrame:
    prov_col = _find_col(raw.columns, PROVINCE_HEADERS)
    if prov_col is None:
        raise ValueError("no province column found")
    year_col = _find_col(raw.columns, YEAR_HEADERS)
    df = add_province_code(raw, prov_col)
    rows = []
    attr_col = _find_col(raw.columns, ("attribute", "item", "รายการ"))
    val_col = _find_col(raw.columns, ("values", "value", "data", "ค่า"))
    label_col = _find_col(raw.columns, ("year_crop", "crop_year", "ปีเพาะปลูก"))
    if year_col is not None and attr_col is not None and val_col is not None and attr_col != val_col:
        # OAE "attribute/value" layout: one row per province-year-measure
        ycol = df[year_col].map(parse_year)
        mu = df[attr_col].map(metric_for)
        if report is not None:
            report.setdefault("unmapped_columns", set()).update(
                f"attribute:{a}" for a, m in zip(df[attr_col], mu) if m is None and pd.notna(a))
        label = df[label_col].astype(str) if label_col and label_col != year_col else None
        out = pd.DataFrame({
            "province_code": df["province_code"], "province_th": df["province_th"],
            "year_ce": ycol.map(lambda t: t[0]),
            "period": label.where(label.str.contains("/"), "annual") if label is not None else "annual",
            "crop": crop, "metric": mu.map(lambda t: t[0] if t else None),
            "value": to_number(df[val_col]), "unit": mu.map(lambda t: t[1] if t else None),
        })
        rows.append(out.dropna(subset=["metric"]))
    elif year_col is not None:  # long: one row per province-year, one column per metric
        metric_cols = {c: metric_for(c) for c in raw.columns if c not in (prov_col, year_col)}
        ycol = df[year_col].map(parse_year)
        df["_year_ce"] = ycol.map(lambda t: t[0])
        df["_label"] = ycol.map(lambda t: t[1])
        for c, mu in metric_cols.items():
            if mu is None:
                if report is not None:
                    report.setdefault("unmapped_columns", set()).add(str(c))
                continue
            part = pd.DataFrame({
                "province_code": df["province_code"], "province_th": df["province_th"],
                "year_ce": df["_year_ce"], "period": df["_label"].fillna("annual"),
                "crop": crop, "metric": mu[0], "value": to_number(df[c]), "unit": mu[1],
            })
            rows.append(part)
    else:  # wide: year columns, optional metric column
        metric_col = _find_col(raw.columns, ("รายการ", "metric", "ตัวชี้วัด", "item", "ประเภท"))
        for c in raw.columns:
            y = _year_like(c)
            if y is None:
                continue
            metrics = df[metric_col].map(metric_for) if metric_col else pd.Series([("production", "ton")] * len(df))
            part = pd.DataFrame({
                "province_code": df["province_code"], "province_th": df["province_th"],
                "year_ce": y, "period": "annual", "crop": crop,
                "metric": metrics.map(lambda t: t[0] if t else None),
                "unit": metrics.map(lambda t: t[1] if t else None),
                "value": to_number(df[c]),
            })
            rows.append(part.dropna(subset=["metric"]))
    if report is not None:
        report.setdefault("unmatched_provinces", set()).update(
            str(v) for v, code in zip(raw[prov_col], df["province_code"]) if pd.isna(code) and pd.notna(v))
    if not rows:
        return pd.DataFrame(columns=TIDY_COLUMNS)
    return _finish(pd.concat(rows, ignore_index=True), source_id, source_url)


# ---------------------------------------------------------------------------
# D05 soil suitability (S1/S2/S3/N per province, no year)
# ---------------------------------------------------------------------------
def tidy_suitability(raw: pd.DataFrame, crop: str, source_id: str = "D05", source_url: str = "",
                     report: Optional[dict] = None) -> pd.DataFrame:
    prov_col = _find_col(raw.columns, PROVINCE_HEADERS)
    if prov_col is None:
        raise ValueError("no province column found")
    df = add_province_code(raw, prov_col)
    rows = []
    for c in raw.columns:
        m = re.search(r"(?<![A-Za-z0-9])(S1|S2|S3|N)(?![A-Za-z0-9])", str(c).upper())
        if not m or c == prov_col:
            continue
        rows.append(pd.DataFrame({
            "province_code": df["province_code"], "province_th": df["province_th"], "year_ce": pd.NA,
            "period": "snapshot", "crop": crop, "metric": f"suitability_{m.group(1).lower()}",
            "value": to_number(df[c]), "unit": "rai",
        }))
    if report is not None:
        report.setdefault("unmatched_provinces", set()).update(
            str(v) for v, code in zip(raw[prov_col], df["province_code"]) if pd.isna(code) and pd.notna(v))
    if not rows:
        return pd.DataFrame(columns=TIDY_COLUMNS)
    out = pd.concat(rows, ignore_index=True)
    out = out.dropna(subset=["province_code", "value"]).copy()
    out["source_id"], out["source_url"] = source_id, source_url
    return out[TIDY_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# D07 provincial monthly climate (HII spatial-rain / tmax-tmin)
# ---------------------------------------------------------------------------
THAI_MONTHS = {"ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7,
               "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12}


def _month(v) -> Optional[int]:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    s = str(v).strip()
    if s in THAI_MONTHS:
        return THAI_MONTHS[s]
    for k, n in THAI_MONTHS.items():
        if s.replace(" ", "") == k.replace(".", ""):
            return n
    try:
        n = int(float(s))
        return n if 1 <= n <= 12 else None
    except ValueError:
        return None


def tidy_monthly_climate(raw: pd.DataFrame, metric: str, unit: str, source_id: str = "D07",
                         source_url: str = "", value_col: Optional[str] = None) -> pd.DataFrame:
    """Long table with province, year, month and a value column -> tidy monthly rows."""
    prov_col = _find_col(raw.columns, PROVINCE_HEADERS)
    year_col = _find_col(raw.columns, YEAR_HEADERS)
    month_col = _find_col(raw.columns, ("เดือน", "month"))
    if not (prov_col and year_col and month_col):
        raise ValueError(f"need province/year/month columns, got {list(raw.columns)}")
    if value_col is None:
        others = [c for c in raw.columns if c not in (prov_col, year_col, month_col)]
        numeric = [c for c in others if to_number(raw[c]).notna().mean() > 0.5]
        if len(numeric) != 1:
            raise ValueError(f"ambiguous value column, pass value_col= one of {numeric}")
        value_col = numeric[0]
    df = add_province_code(raw, prov_col)
    years = df[year_col].map(lambda v: parse_year(v)[0])
    months = df[month_col].map(_month)
    out = pd.DataFrame({
        "province_code": df["province_code"], "province_th": df["province_th"], "year_ce": years,
        "period": [f"{y}-{m:02d}" if pd.notna(y) and m else None for y, m in zip(years, months)],
        "crop": "all", "metric": metric, "value": to_number(df[value_col]), "unit": unit,
    })
    return _finish(out.dropna(subset=["period"]), source_id, source_url)


def annual_rain_from_monthly(monthly: pd.DataFrame) -> pd.DataFrame:
    """Annual rainfall = sum of 12 monthly values; years with < 12 months stay missing."""
    m = monthly[monthly["metric"] == "rain"]
    g = m.groupby(["province_code", "province_th", "year_ce"], as_index=False).agg(
        value=("value", "sum"), n=("value", "count"), source_id=("source_id", "first"),
        source_url=("source_url", "first"))
    g.loc[g["n"] < 12, "value"] = np.nan
    g["period"], g["crop"], g["metric"], g["unit"] = "annual", "all", "rain_annual", "mm"
    return g[TIDY_COLUMNS]


# ---------------------------------------------------------------------------
# D02 weekly prices (NABC JSON records)
# ---------------------------------------------------------------------------
def tidy_weekly_prices(records: List[dict], crop: str, source_url: str, source_id: str = "D02") -> pd.DataFrame:
    """National weekly farm-gate prices. Field names are detected because the API schema is undocumented."""
    if not records:
        return pd.DataFrame(columns=TIDY_COLUMNS)
    df = pd.json_normalize(records)
    cols = {c.lower(): c for c in df.columns}
    price_col = next((cols[c] for c in cols if "price" in c or "ราคา" in c), None)
    date_col = next((cols[c] for c in cols if any(k in c for k in ("date", "week_start", "start", "วันที่"))), None)
    year_col = next((cols[c] for c in cols if c in ("year", "ปี")), None)
    week_col = next((cols[c] for c in cols if c in ("week", "week_no", "สัปดาห์")), None)
    if price_col is None and "value" in cols:
        price_col = cols["value"]
    if price_col is None:
        raise ValueError(f"no price field in {list(df.columns)}")
    if "year_th" in cols and "month" in cols and "week" in cols:
        y = df[cols["year_th"]].map(lambda v: parse_year(v)[0])
        m = pd.to_numeric(df[cols["month"]], errors="coerce")
        w = pd.to_numeric(df[cols["week"]], errors="coerce")
        unit = df[cols["unit"]].astype(str) if "unit" in cols else pd.Series(["บาท/กก."] * len(df))
        factor = unit.map(lambda u: 0.001 if "ตัน" in u else 1.0)
        out = pd.DataFrame({
            "province_code": "00", "province_th": "ทั้งประเทศ", "year_ce": y,
            "period": [f"{a}-{int(b):02d}-W{int(c)}" if pd.notna(a) and pd.notna(b) and pd.notna(c) else None
                       for a, b, c in zip(y, m, w)],
            "crop": crop, "metric": "farmgate_price", "value": to_number(df[price_col]) * factor,
            "unit": "THB/kg", "source_id": source_id, "source_url": source_url,
        })
        out = out.dropna(subset=["period", "value"])
        out["year_ce"] = out["year_ce"].astype("Int64")
        return out[TIDY_COLUMNS].sort_values("period").reset_index(drop=True)
    if date_col is not None:
        d = pd.to_datetime(df[date_col], errors="coerce")
        iso = d.dt.isocalendar()
        year_ce = iso["year"].astype("Int64")
        period = [f"{y}-W{w:02d}" if pd.notna(y) else None for y, w in zip(iso["year"], iso["week"])]
    elif year_col and week_col:
        year_ce = df[year_col].map(lambda v: parse_year(v)[0])
        period = [f"{y}-W{int(w):02d}" for y, w in zip(year_ce, df[week_col])]
    else:
        raise ValueError(f"no date/week fields in {list(df.columns)}")
    out = pd.DataFrame({
        "province_code": "00", "province_th": "ทั้งประเทศ", "year_ce": year_ce, "period": period,
        "crop": crop, "metric": "farmgate_price", "value": to_number(df[price_col]), "unit": "THB/kg",
        "source_id": source_id, "source_url": source_url,
    })
    out = out.dropna(subset=["period", "value"])
    out["year_ce"] = out["year_ce"].astype("Int64")
    return out[TIDY_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Open-Meteo (D07 gap / D08 substitute)
# ---------------------------------------------------------------------------
def tidy_open_meteo_daily(payload: dict, province_code: str, province_th: str, source_url: str,
                          source_id: str = "D07-ERA5") -> pd.DataFrame:
    """Daily precipitation_sum -> monthly totals (months with missing days stay missing)."""
    daily = payload.get("daily", {})
    df = pd.DataFrame({"date": pd.to_datetime(daily.get("time", [])),
                       "rain": pd.to_numeric(pd.Series(daily.get("precipitation_sum", [])), errors="coerce")})
    if df.empty:
        return pd.DataFrame(columns=TIDY_COLUMNS)
    df["ym"] = df["date"].dt.to_period("M")
    g = df.groupby("ym").agg(value=("rain", lambda s: s.sum() if s.notna().all() else np.nan))
    g = g.reset_index()
    out = pd.DataFrame({
        "province_code": province_code, "province_th": province_th,
        "year_ce": g["ym"].dt.year.astype("Int64"), "period": g["ym"].astype(str),
        "crop": "all", "metric": "rain", "value": g["value"], "unit": "mm",
        "source_id": source_id, "source_url": source_url,
    })
    return out.dropna(subset=["value"])[TIDY_COLUMNS]
