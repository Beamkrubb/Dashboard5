"""
Build tidy CSVs in data/clean/ from data/raw/ (handoff_n.md steps 2–3).

    python scripts/build_clean_data.py

Outputs (all in the shared schema, joined on province_code = pro_code):
    production.csv        D01
    farmgate_weekly.csv   D02
    suitability.csv       D05
    climate_monthly.csv   D07 (+ ERA5 2018 rows, source_id D07-ERA5)
    rain_annual.csv       derived from climate_monthly (only complete years)
    cleaning_report.json  unmatched province names / unmapped columns / row counts
Datasets whose raw files are missing are skipped and listed in the report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline import sources, transform as T  # noqa: E402
from pipeline.province import lookup_frame  # noqa: E402

RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"

CROP_FROM_FILENAME = {
    "cassava": "cassava", "maize": "maize", "para_rubber": "rubber", "rubber": "rubber",
    "oil_palm": "oil_palm", "rice": "rice", "sugarcane": "sugarcane",
}


def _crop_for(path: Path) -> str:
    stem = path.stem.lower()
    for key, crop in CROP_FROM_FILENAME.items():
        if stem.startswith(key):
            return crop
    return stem.split("_production")[0]


def _write(df: pd.DataFrame, name: str, report: dict) -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN / name, index=False, encoding="utf-8-sig")
    report["outputs"][name] = int(len(df))
    print(f"  {name}: {len(df):,} rows")


def build_production(report: dict) -> None:
    files = sorted((RAW / "D01").glob("*_production_province*.*")) + sorted((RAW / "D01").glob("*_product_province*.*"))
    urls = {r.filename: r.url for r in sources.get("D01").resources}
    parts = []
    for f in files:
        rep: dict = {}
        try:
            parts.append(T.tidy_production(T.read_table(f), _crop_for(f), "D01", urls.get(f.name, sources.get("D01").page), rep))
        except Exception as e:  # keep going; record the problem
            rep["error"] = str(e)
        report["D01"][f.name] = {k: sorted(v) if isinstance(v, set) else v for k, v in rep.items()}
    if parts:
        _write(pd.concat(parts, ignore_index=True), "production.csv", report)
    else:
        report["skipped"].append("D01")


def build_prices(report: dict) -> None:
    parts = []
    for f in sorted((RAW / "D02").glob("weekly_*.json")):
        body = json.loads(f.read_text(encoding="utf-8"))
        crop = f.stem.replace("weekly_", "")
        try:
            parts.append(T.tidy_weekly_prices(body.get("records", []), crop, sources.NABC_WEEKLY_URL))
        except ValueError as e:
            report["D02"][f.name] = {"error": str(e)}
    if parts:
        _write(pd.concat([p for p in parts if not p.empty], ignore_index=True), "farmgate_weekly.csv", report)
    else:
        report["skipped"].append("D02")


def build_suitability(report: dict) -> None:
    ds = sources.get("D05")
    parts = []
    for res in ds.resources:
        f = RAW / "D05" / res.filename
        if not res.crop or not f.exists():
            continue
        rep: dict = {}
        try:
            parts.append(T.tidy_suitability(T.read_table(f), res.crop, "D05", res.url, rep))
        except Exception as e:
            rep["error"] = str(e)
        report["D05"][f.name] = {k: sorted(v) if isinstance(v, set) else v for k, v in rep.items()}
    if parts:
        _write(pd.concat(parts, ignore_index=True), "suitability.csv", report)
    else:
        report["skipped"].append("D05")


def build_climate(report: dict) -> None:
    parts = []
    for fname, metric, unit, url in [
        ("spatial_rain.csv", "rain", "mm", "https://data.go.th/dataset/spatial-rain"),
    ]:
        f = RAW / "D07" / fname
        if f.exists():
            try:
                parts.append(T.tidy_monthly_climate(T.read_table(f), metric, unit, "D07", url))
            except ValueError as e:
                report["D07"][fname] = {"error": str(e)}
    tf = RAW / "D07" / "tmax_tmin.csv"
    if tf.exists():
        raw = T.read_table(tf)
        for col in raw.columns:
            low = str(col).lower()
            metric = "tmax" if ("max" in low or "สูงสุด" in low) else ("tmin" if ("min" in low or "ต่ำสุด" in low) else None)
            if metric:
                try:
                    parts.append(T.tidy_monthly_climate(raw, metric, "°C", "D07",
                                                        "https://data.go.th/dataset/tmax-tmin", value_col=col))
                except ValueError as e:
                    report["D07"][f"tmax_tmin.csv:{col}"] = {"error": str(e)}
    th = dict(zip(lookup_frame()["pro_code"], lookup_frame()["province_th"]))
    era5_files = [f for d in sorted((RAW / "ERA5").glob("[12][0-9][0-9][0-9]")) for f in sorted(d.glob("*.json"))]
    for f in era5_files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        parts.append(T.tidy_open_meteo_daily(payload, f.stem, th.get(f.stem), sources.OPEN_METEO_ARCHIVE))
    if parts:
        monthly = pd.concat(parts, ignore_index=True)
        _write(monthly, "climate_monthly.csv", report)
        _write(T.annual_rain_from_monthly(monthly), "rain_annual.csv", report)
    else:
        report["skipped"].append("D07")


def main() -> int:
    report = {"outputs": {}, "skipped": [], "D01": {}, "D02": {}, "D05": {}, "D07": {}}
    lk = CLEAN / "province_lookup.csv"
    if not lk.exists():
        CLEAN.mkdir(parents=True, exist_ok=True)
        lookup_frame().to_csv(lk, index=False, encoding="utf-8-sig")
    print("Building clean data")
    build_production(report)
    build_prices(report)
    build_suitability(report)
    build_climate(report)
    (CLEAN / "cleaning_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Skipped (no raw files): {report['skipped'] or 'none'} -> data/clean/cleaning_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
