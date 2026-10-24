"""
Fetch the extra real datasets needed by the 4-tab dashboard spec (run on a machine with internet).

    python scripts/fetch_extra.py

1. NABC weekly farm-gate prices for the production crops (OAE catalog product names)
2. ERA5 daily rain + mean temperature 2007–2019 at each province centroid (Open-Meteo)
3. HII spatial-rain and tmax-tmin resources via the data.go.th CKAN API
4. DDPM flood / drought / windstorm statistics via the catalog.disaster.go.th CKAN API
Everything is written under data/raw/ and logged to data/raw/fetch_extra_manifest.json.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
HDR = {"User-Agent": "Dashboard5-data-pipeline/1.0 (academic project)"}
log = []


def note(step, status, **kw):
    entry = {"step": step, "status": status, **kw}
    log.append(entry)
    print(f"[{status}] {step} {kw if kw else ''}", flush=True)


# 1 ---------------------------------------------------------------------------
NABC = "https://agriapi.nabc.go.th/api/weekly-prices/product"
PRODUCTS = {
    "cassava_fresh": "มันสำปะหลังสด คละ",
    "cassava_chips": "มันเส้น คละ",
    "maize": "ข้าวโพดเลี้ยงสัตว์เมล็ด ความชื้น 14.5",
    "rubber_sheet": "ยางแผ่นดิบ ชั้น 3",
    "rubber_cuplump": "ยางก้อน คละ",
    "rubber_latex": "น้ำยางสด คละ",
    "oil_palm": "ผลปาล์มน้ำมันทั้งทะลาย คละ",
}


def fetch_prices():
    for key, name in PRODUCTS.items():
        recs, page = [], 1
        while page < 400:
            try:
                r = requests.get(NABC, params={"product_name": name, "page": page}, headers=HDR, timeout=60)
                r.raise_for_status()
                body = r.json()
            except Exception as e:  # noqa: BLE001
                note(f"prices {key} p{page}", "error", error=str(e)[:200])
                break
            items = body.get("data") if isinstance(body, dict) else body
            last = None
            if isinstance(items, dict):
                last, items = items.get("last_page"), items.get("data", [])
            elif isinstance(body, dict):
                last = body.get("last_page") or (body.get("meta") or {}).get("last_page")
            if not items:
                break
            recs.extend(items)
            if last is not None and page >= int(last):
                break
            page += 1
            time.sleep(0.2)
        out = RAW / "D02" / f"weekly_{key}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"product_name": name, "records": recs}, ensure_ascii=False), encoding="utf-8")
        note(f"prices {key}", "ok" if recs else "empty", records=len(recs))


# 2 ---------------------------------------------------------------------------
def fetch_era5(start="2007-01-01", end="2019-12-31", tag="2007_2019"):
    import csv
    lk = ROOT / "data" / "clean" / "province_lookup.csv"
    rows = list(csv.DictReader(lk.open(encoding="utf-8-sig")))
    out_dir = RAW / "ERA5" / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for row in rows:
        dest = out_dir / f"{row['pro_code']}.json"
        if dest.exists() and dest.stat().st_size > 1000:
            done += 1
            continue
        for attempt in range(4):
            try:
                r = requests.get("https://archive-api.open-meteo.com/v1/archive", headers=HDR, timeout=120, params={
                    "latitude": row["centroid_lat"], "longitude": row["centroid_lon"], "start_date": start, "end_date": end,
                    "daily": "precipitation_sum,temperature_2m_mean,temperature_2m_max,temperature_2m_min",
                    "timezone": "Asia/Bangkok"})
                if r.status_code == 429:
                    time.sleep(30 * (attempt + 1))
                    continue
                r.raise_for_status()
                dest.write_text(r.text, encoding="utf-8")
                done += 1
                break
            except Exception as e:  # noqa: BLE001
                note(f"era5 {row['pro_code']}", "retry", error=str(e)[:150])
                time.sleep(10)
        time.sleep(4)  # stay inside Open-Meteo's free per-minute budget
    note("era5 2007-2019", "ok" if done == len(rows) else "partial", provinces=done)


# 3 + 4 -----------------------------------------------------------------------
def ckan_download(base, dataset_id, dest_dir, max_files=30):
    try:
        r = requests.get(f"{base}/api/3/action/package_show", params={"id": dataset_id}, headers=HDR, timeout=60)
        r.raise_for_status()
        res = r.json()["result"]["resources"]
    except Exception as e:  # noqa: BLE001
        note(f"ckan {dataset_id}", "error", error=str(e)[:200])
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / f"{dataset_id}_resources.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    n = 0
    for item in res[:max_files]:
        url = item.get("url") or ""
        fmt = (item.get("format") or "").lower()
        if not url.startswith("http"):
            continue
        name = re.sub(r"[^\w.\-ก-๙]+", "_", (item.get("name") or item.get("id") or "file"))[:80]
        ext = "." + fmt if fmt in ("csv", "xlsx", "xls", "json", "zip") else Path(url.split("?")[0]).suffix or ".bin"
        dest = dest_dir / f"{dataset_id}__{name}{ext}"
        try:
            f = requests.get(url, headers=HDR, timeout=120)
            f.raise_for_status()
            dest.write_bytes(f.content)
            n += 1
        except Exception as e:  # noqa: BLE001
            note(f"ckan file {dataset_id}/{name}", "error", url=url, error=str(e)[:150])
    note(f"ckan {dataset_id}", "ok" if n else "empty", files=n, resources=len(res))


def main():
    fetch_prices()
    ckan_download("https://data.go.th", "spatial-rain", RAW / "D07")
    ckan_download("https://data.go.th", "tmax-tmin", RAW / "D07")
    for ds in ("dpm-gd027", "dpm-gd028", "dpm-gd030"):
        ckan_download("https://catalog.disaster.go.th", ds, RAW / "D06")
    fetch_era5()
    (RAW / "fetch_extra_manifest.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
