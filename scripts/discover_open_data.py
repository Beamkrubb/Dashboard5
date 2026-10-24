"""
Search Thai open-data CKAN portals for datasets the dashboard objectives still need.
Writes data/raw/discovery/*.json (one file per portal/query) and a compact summary.txt.

    python scripts/discover_open_data.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "discovery"
OUT.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "Dashboard5-data-pipeline/1.0 (academic project)"}

PORTALS = {
    "oae": "https://catalog.oae.go.th",
    "datagoth": "https://data.go.th",
    "nso": "https://catalog.nso.go.th",
    "ddpm": "https://catalog.disaster.go.th",
    "ldd": "https://lddcatalog.ldd.go.th",
    "rid": "https://catalog.rid.go.th",
    "tmd": "https://catalog.tmd.go.th",
    "doae": "https://catalog.doae.go.th",
}
QUERIES = {
    "oae": ["*:*"],                       # whole OAE catalog (≈200 datasets)
    "datagoth": ["ต้นทุนการผลิต สศก", "ต้นทุนการผลิตสินค้าเกษตร", "พื้นที่ชลประทาน", "ชลประทาน รายจังหวัด",
                 "tmdclimatemonthly", "สถิติภูมิอากาศ รายเดือน", "อุณหภูมิ รายจังหวัด", "เครื่องจักรกลการเกษตร",
                 "ข้าวนาปี รายจังหวัด", "ข้าวนาปรัง", "ภัยพิบัติด้านพืช", "พื้นที่ประสบภัย การเกษตร"],
    "nso": ["สำมะโนการเกษตร", "เครื่องจักร", "ชลประทาน", "ข้าว", "ต้นทุน"],
    "ddpm": ["*:*"],
    "ldd": ["ชลประทาน", "*:*"],
    "rid": ["*:*"],
    "tmd": ["*:*"],
    "doae": ["*:*"],
}


def search(base, q, rows=500):
    url = f"{base}/api/3/action/package_search"
    try:
        r = requests.get(url, params={"q": q, "rows": rows}, headers=HDR, timeout=60)
        r.raise_for_status()
        return r.json()["result"]
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:300]}


def slim(pkg):
    return {"name": pkg.get("name"), "title": pkg.get("title"),
            "org": (pkg.get("organization") or {}).get("title"),
            "notes": (pkg.get("notes") or "")[:300],
            "resources": [{"name": r.get("name"), "format": r.get("format"), "url": r.get("url")} for r in pkg.get("resources", [])]}


def main():
    lines = []
    for key, base in PORTALS.items():
        for q in QUERIES[key]:
            res = search(base, q)
            tag = re.sub(r"[^\w]+", "_", q)[:40]
            if "error" in res:
                lines.append(f"[{key}] {q}: ERROR {res['error'][:120]}")
                continue
            pk = [slim(p) for p in res.get("results", [])]
            (OUT / f"{key}__{tag}.json").write_text(json.dumps({"count": res.get("count"), "results": pk}, ensure_ascii=False, indent=1), encoding="utf-8")
            lines.append(f"[{key}] {q}: {res.get('count')} datasets")
            for p in pk[:500]:
                fmts = ",".join(sorted({(r['format'] or '?') for r in p['resources']}))
                lines.append(f"    {p['name']} | {p['title']} | {p['org']} | {fmts} | {len(p['resources'])} res")
            print(lines[-1 - min(len(pk), 500)], flush=True)
    # HII temperature: the tmax-tmin resource points at a directory listing; save it
    try:
        lst = requests.get("https://tiservice.hii.or.th/forecast/projects/bot/Observed/Temperature/", headers=HDR, timeout=60)
        (OUT / "hii_temperature_index.html").write_text(lst.text, encoding="utf-8")
        lines.append(f"[hii] temperature index: HTTP {lst.status_code}, {len(lst.text)} bytes")
    except Exception as e:  # noqa: BLE001
        lines.append(f"[hii] temperature index ERROR {e}")
    (OUT / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
