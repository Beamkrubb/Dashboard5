"""Finish the ERA5 2007-2019 province download (resumable: skips provinces already saved).

    python scripts/fetch_era5_missing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_extra  # noqa: E402

if __name__ == "__main__":
    fetch_extra.fetch_era5()
    out = fetch_extra.RAW / "ERA5" / "2007_2019"
    n = len([p for p in out.glob("*.json") if p.stat().st_size > 1000])
    print(f"ERA5 provinces saved: {n}/77", flush=True)
    print("DONE", flush=True)
