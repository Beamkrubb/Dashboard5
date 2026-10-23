"""
Download D01–D10 raw files into data/raw/<ID>/ (handoff_n.md step 1).

    python scripts/download_data.py               # everything that can be automated
    python scripts/download_data.py --only D05 D10
    python scripts/download_data.py --era5-2018   # Open-Meteo rain for 2018 (D07 gap)
    python scripts/download_data.py --era5-longterm  # 1970–2025 national ERA5 series (D08 fallback)

Writes data/raw/manifest.json (url, status, bytes, access date) and prints the
manual steps for portals that block automated download.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline import sources  # noqa: E402
from pipeline.province import clean_geojson, lookup_from_geojson  # noqa: E402

RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
HEADERS = {"User-Agent": "Dashboard5-data-pipeline/1.0 (academic project)"}
TODAY = dt.date.today().isoformat()


def fetch(url: str, dest: Path, params=None, timeout=60) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return {"url": r.url, "file": str(dest.relative_to(ROOT)), "status": "ok",
                "bytes": len(r.content), "accessed": TODAY}
    except requests.RequestException as e:
        return {"url": url, "file": str(dest.relative_to(ROOT)), "status": f"error: {e}", "accessed": TODAY}


def download_static(ds: sources.Dataset, manifest: list) -> None:
    for res in ds.resources:
        dest = RAW / ds.id / res.filename
        if not res.auto:
            manifest.append({"dataset": ds.id, "url": res.url, "file": str(dest.relative_to(ROOT)),
                             "status": "manual" + (" (present)" if dest.exists() else " (missing)"),
                             "accessed": TODAY})
            continue
        entry = fetch(res.url, dest)
        entry["dataset"] = ds.id
        manifest.append(entry)
        print(f"  {ds.id} {res.filename}: {entry['status']}")


def download_weekly_prices(manifest: list, max_pages: int = 500) -> None:
    for key, product in sources.WEEKLY_PRICE_PRODUCTS.items():
        records, page = [], 1
        while page <= max_pages:
            try:
                r = requests.get(sources.NABC_WEEKLY_URL, params={"product_name": product, "page": page},
                                 headers=HEADERS, timeout=60)
                r.raise_for_status()
                body = r.json()
            except (requests.RequestException, ValueError) as e:
                manifest.append({"dataset": "D02", "url": sources.NABC_WEEKLY_URL, "product": product,
                                 "status": f"error page {page}: {e}", "accessed": TODAY})
                break
            items = body.get("data") if isinstance(body, dict) else body
            if isinstance(items, dict):  # paginated envelope {data: {data: [...], last_page: n}}
                last = items.get("last_page")
                items = items.get("data", [])
            else:
                last = body.get("last_page") if isinstance(body, dict) else None
            if not items:
                break
            records.extend(items)
            if last is not None and page >= int(last):
                break
            page += 1
            time.sleep(0.3)
        dest = RAW / "D02" / f"weekly_{key}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({"product_name": product, "records": records}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        manifest.append({"dataset": "D02", "url": sources.NABC_WEEKLY_URL, "product": product,
                         "file": str(dest.relative_to(ROOT)), "status": "ok", "records": len(records),
                         "accessed": TODAY})
        print(f"  D02 {key}: {len(records)} records")


def build_lookup(manifest: list) -> None:
    gj_path = RAW / "D10" / "provinces.geojson"
    if not gj_path.exists():
        print("  D10 GeoJSON missing – province_lookup.csv will be written without centroids")
        from pipeline.province import lookup_frame
        CLEAN.mkdir(parents=True, exist_ok=True)
        lookup_frame().to_csv(CLEAN / "province_lookup.csv", index=False, encoding="utf-8-sig")
        return
    gj = clean_geojson(gj_path, CLEAN / "provinces.geojson")
    lk = lookup_from_geojson(gj)
    lk.to_csv(CLEAN / "province_lookup.csv", index=False, encoding="utf-8-sig")
    n = lk["centroid_lat"].notna().sum() if "centroid_lat" in lk else 0
    print(f"  province_lookup.csv: {len(lk)} provinces, {n} with centroids")


def download_era5(start: str, end: str, tag: str, manifest: list) -> None:
    lk_path = CLEAN / "province_lookup.csv"
    import pandas as pd
    lk = pd.read_csv(lk_path, dtype={"pro_code": str}) if lk_path.exists() else None
    if lk is None or "centroid_lat" not in lk:
        print("  ERA5 skipped: run D10 first so province centroids exist")
        return
    out_dir = RAW / "ERA5" / tag
    for _, row in lk.dropna(subset=["centroid_lat"]).iterrows():
        dest = out_dir / f"{row.pro_code}.json"
        if dest.exists():
            continue
        entry = fetch(sources.OPEN_METEO_ARCHIVE, dest, params={
            "latitude": row.centroid_lat, "longitude": row.centroid_lon, "start_date": start,
            "end_date": end, "daily": "precipitation_sum", "timezone": "Asia/Bangkok"}, timeout=120)
        entry["dataset"] = f"ERA5-{tag}"
        manifest.append(entry)
        time.sleep(0.5)
    print(f"  ERA5 {tag}: {len(list(out_dir.glob('*.json')))} province files")


def tmd_cache(manifest: list) -> None:
    uid, ukey = os.environ.get("TMD_UID"), os.environ.get("TMD_UKEY")
    if not (uid and ukey):
        print("  D09 skipped: set TMD_UID and TMD_UKEY to cache TMD observations")
        return
    for svc in ("Station/v1", "WeatherToday/V2"):
        dest = RAW.parent / "cache" / f"tmd_{svc.split('/')[0].lower()}_{TODAY.replace('-', '')}.json"
        entry = fetch(f"{sources.TMD_BASE}/{svc}/", dest, params={"uid": uid, "ukey": ukey, "format": "json"})
        entry["dataset"] = "D09"
        manifest.append(entry)
        print(f"  D09 {svc}: {entry['status']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="dataset IDs, e.g. D01 D05")
    ap.add_argument("--era5-2018", action="store_true", help="fetch 2018 daily rain per province (D07 gap)")
    ap.add_argument("--era5-longterm", action="store_true", help="fetch 1970–2025 daily rain per province (D08)")
    args = ap.parse_args(argv)
    wanted = set(args.only or [d.id for d in sources.DATASETS])
    manifest: list = []

    # D10 first: everything else joins on pro_code
    for ds in sorted(sources.DATASETS, key=lambda d: d.id != "D10"):
        if ds.id not in wanted:
            continue
        print(f"{ds.id} {ds.name_th} [{ds.status}]")
        if ds.id == "D02":
            download_weekly_prices(manifest)
        elif ds.id == "D09":
            tmd_cache(manifest)
        else:
            download_static(ds, manifest)
        if ds.id == "D10":
            build_lookup(manifest)
    if args.era5_2018:
        download_era5("2018-01-01", "2018-12-31", "2018", manifest)
    if args.era5_longterm:
        download_era5("1970-01-01", "2025-12-31", "1970_2025", manifest)

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\nManual downloads still needed:")
    for ds in sources.DATASETS:
        if ds.id in wanted and ds.manual_steps:
            print(f"- {ds.id}: {ds.manual_steps}")
    errors = [m for m in manifest if str(m.get("status", "")).startswith("error")]
    print(f"\n{len(manifest)} manifest entries, {len(errors)} errors -> data/raw/manifest.json")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
