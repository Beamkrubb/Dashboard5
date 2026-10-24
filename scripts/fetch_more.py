"""
Phase-2 downloads chosen from data/raw/discovery (run scripts/discover_open_data.py first).

    python scripts/fetch_more.py
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
DISC = RAW / "discovery"
HDR = {"User-Agent": "Dashboard5-data-pipeline/1.0 (academic project)"}
log = []


def get(url, dest: Path, params=None, timeout=180):
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=HDR, timeout=timeout)
            r.raise_for_status()
            dest.write_bytes(r.content)
            log.append({"url": r.url, "file": str(dest.relative_to(ROOT)), "bytes": len(r.content), "status": "ok"})
            print(f"[ok] {dest.relative_to(ROOT)} {len(r.content):,} B", flush=True)
            return True
        except Exception as e:  # noqa: BLE001
            err = str(e)[:200]
            time.sleep(3)
    log.append({"url": url, "file": str(dest.relative_to(ROOT)), "status": "error", "error": err})
    print(f"[error] {dest.relative_to(ROOT)}: {err}", flush=True)
    return False


def safe(s):
    return re.sub(r"[^\w.\-ก-๙]+", "_", s)[:90]


def main():
    # 1. OAE "key crops" production 2550-2562 (data.go.th oae0001)
    base = "https://data.go.th/dataset/2ddb8a63-b7b3-43cb-ac8a-211de257db37/resource"
    get(f"{base}/08286028-3c4c-45a8-826f-d4ab79f1ff28/download/production_y_oae.csv", RAW / "D01x" / "production_y_oae.csv")
    get(f"{base}/01f74bc1-259d-49a6-9f23-f6c82ef766be/download/technical.xlsx", RAW / "D01x" / "technical.xlsx")

    # 2. every OAE province-level production file (backup / newer years)
    oae = json.loads((DISC / "oae____.json").read_text(encoding="utf-8")) if (DISC / "oae____.json").exists() else \
        json.loads(next(DISC.glob("oae__*.json")).read_text(encoding="utf-8"))
    for p in oae["results"]:
        if not (p["name"].endswith("_product") or re.fullmatch(r"dataoae1[1-5]04", p["name"] or "")):
            continue
        for r in p["resources"]:
            if r.get("name") and "จังหวัด" in r["name"] and r.get("url", "").startswith("http"):
                ext = Path(r["url"].split("?")[0]).suffix or ".csv"
                get(r["url"], RAW / "D01x" / "oae_province" / f"{p['name']}__{safe(r['name'])}{ext}")

    # 3. sugarcane by province (OCSB)
    get("https://catalog.ocsb.go.th/dataset/f6286643-632b-4be7-9656-0bd4e229e723/resource/ea16cd9d-e0e6-4850-bbbf-da915a85be9a/download/caneyield.csv",
        RAW / "D01x" / "ocsb_caneyield.csv")
    get("https://catalog.ocsb.go.th/dataset/f6286643-632b-4be7-9656-0bd4e229e723/resource/637ad3b7-355b-4385-8ab8-7adbb620e9aa/download/datadic-caneyield.xlsx",
        RAW / "D01x" / "ocsb_caneyield_datadict.xlsx")

    # 4. HII monthly provincial temperature 2018-2019
    for y in (2018, 2019):
        for m in range(1, 13):
            get(f"https://tiservice.hii.or.th/forecast/projects/bot/Observed/Temperature/o_th{y}{m:02d}_province.csv",
                RAW / "D07" / "temperature" / f"o_th{y}{m:02d}_province.csv", timeout=60)

    # 5. irrigation: RID GIS layer (attributes first), DOAE affected area in/out of irrigation zones, LDD farm ponds
    wfs = "http://gis.rid.go.th/geoserver/riddata/ows"
    get(wfs, RAW / "D04" / "rid_irrarea_sample.json", params={"service": "WFS", "version": "1.0.0", "request": "GetFeature",
        "typeName": "riddata:virrarea_all", "maxFeatures": "3", "outputFormat": "application/json"})
    get(wfs, RAW / "D04" / "rid_irrarea_describe.xml", params={"service": "WFS", "version": "1.0.0", "request": "DescribeFeatureType",
        "typeName": "riddata:virrarea_all"})
    get("http://catalog.doae.go.th/dataset/91edf316-3f31-4959-9db9-decec96e4dba/resource/ab68661c-52d7-4cdc-86b6-efdaf92a785e/download/untitled.csv",
        RAW / "D04" / "doae_disaster_in_irrigation.csv")
    get("http://catalog.doae.go.th/dataset/98d554c1-b180-4240-a378-40ccdab13cd0/resource/9e118afd-62fc-47ce-95b0-f47dcaee5721/download/untitled.csv",
        RAW / "D04" / "doae_disaster_outside_irrigation.csv")

    # 6. mechanization + input use by province (NSO agricultural census)
    for t in ("AGC_0506_11_1201", "AGC_0506_11_1202", "AGC_0506_11_1101", "AGC_0506_11_0801"):
        get("https://catalogapi.nso.go.th/api/index", RAW / "D03" / f"nso_{t}.csv", params={"table": t, "format": "csv", "div": "1"})
        get("https://catalogapi.nso.go.th/api/datadic", RAW / "D03" / f"nso_{t}_datadict.csv", params={"table": t, "format": "csv", "div": "1"})

    # 7. cost structure: OAE farm household economics (expenses) + commodity economics PDF
    hh = "https://catalog.oae.go.th/dataset/eb9e456c-875a-44ab-ad03-0ef5804d0d80/resource"
    get(f"{hh}/3a1f92e8-b357-4e82-9e12-531bdd04db08/download/expenses.csv", RAW / "D03" / "oae_household_expenses.csv")
    get(f"{hh}/41750602-f923-416b-9565-5d3447be993f/download/untitled.csv", RAW / "D03" / "oae_net_farm_cash_income.csv")
    get(f"{hh}/52c7790c-461a-4747-b96e-13a8c8959451/download/untitled.xlsx", RAW / "D03" / "oae_household_datadict.xlsx")
    get("https://catalog.oae.go.th/dataset/f99fa2a2-0db0-4a00-b141-0ec3b01c4a1a/resource/da4446a9-d4a3-4989-8b47-06a2deb1355d/download/13e8089a3f69ea96.pdf",
        RAW / "D03" / "oae_commodity_economics_2567.pdf")

    (RAW / "fetch_more_manifest.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
