"""Phase-3 downloads: NSO holders/land, full RID irrigation polygons."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_more import get, RAW, log  # noqa: E402
import json


def main():
    for t in ("AGC_0506_11_0301", "AGC_0506_11_0602"):
        get("https://catalogapi.nso.go.th/api/index", RAW / "D03" / f"nso_{t}.csv", params={"table": t, "format": "csv", "div": "1"})
    get("http://gis.rid.go.th/geoserver/riddata/ows", RAW / "D04" / "rid_irrarea_all.json", timeout=600, params={
        "service": "WFS", "version": "1.0.0", "request": "GetFeature", "typeName": "riddata:virrarea_all",
        "outputFormat": "application/json", "srsName": "EPSG:4326"})
    (RAW / "fetch_more2_manifest.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
