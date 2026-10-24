"""
Loaders: read the outputs of scripts/build_clean_data.py (data/clean/) and the
manual raw files described in handoff_n.md. Missing optional datasets return an
empty DataFrame so the app can show "no data" instead of failing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"

_DTYPES = {"province_code": str}


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=_DTYPES, encoding="utf-8-sig")


def load_agriculture_data() -> pd.DataFrame:
    path = CLEAN / "production.csv"
    if not path.exists():
        raise FileNotFoundError(
            "data/clean/production.csv not found. Run `python scripts/download_data.py` and "
            "`python scripts/build_clean_data.py` (or run_dashboard.bat) first.")
    return _read(path)


def load_spatial_rain_data() -> pd.DataFrame:
    """Monthly provincial climate rows (HII IDW when present, ERA5 substitute otherwise)."""
    return _read(CLEAN / "climate_monthly.csv")


def load_national_rain_data() -> pd.DataFrame:
    """D08 substitute: CCKP/CRU annual national precipitation, if downloaded manually."""
    path = RAW / "D08" / "cckp_thailand_annual_precip.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig", comment="#")


def load_provincial_temp_data() -> pd.DataFrame:
    return _read(CLEAN / "climate_monthly.csv")


def load_oae_farmgate_prices() -> pd.DataFrame:
    return _read(CLEAN / "farmgate_weekly.csv")


def load_tmd_daily_agromet(use_live_api: bool = False) -> Optional[dict]:
    """Latest cached TMD WeatherToday payload (scripts/download_data.py with TMD_UID/TMD_UKEY).
    The dashboard never calls the TMD API live; `use_live_api` is accepted for compatibility."""
    files = sorted(CACHE.glob("tmd_weathertoday_*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def load_thailand_geojson() -> Optional[dict]:
    for path in (CLEAN / "provinces.geojson", RAW / "D10" / "provinces.geojson"):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def load_provincial_irrigation_data() -> pd.DataFrame:
    path = RAW / "D04" / "irrigated_area_province.csv"
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()


def load_ldd_soil_suitability_data() -> pd.DataFrame:
    return _read(CLEAN / "suitability.csv")


def load_oae_production_cost_data() -> pd.DataFrame:
    path = RAW / "D03" / "production_cost_manual.csv"
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()


def load_disaster_affected_data() -> pd.DataFrame:
    """Combined DDPM extract: data/raw/D06/disaster_area_province.csv (province,year_be,hazard,area_rai)."""
    path = RAW / "D06" / "disaster_area_province.csv"
    return pd.read_csv(path, encoding="utf-8-sig") if path.exists() else pd.DataFrame()
