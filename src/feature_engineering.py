"""Aggregations that avoid double counting: totals are summed, ratios are recomputed from totals."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def _sum(df: pd.DataFrame, col: str) -> float:
    return float(df[col].sum(min_count=1)) if col in df.columns and df[col].notna().any() else np.nan


def calculate_weighted_yield(df: pd.DataFrame) -> float:
    """kg/rai = total production (t) * 1000 / total harvested area (rai)."""
    prod, harv = _sum(df, "production_ton"), _sum(df, "area_harvest_rai")
    return prod * 1000.0 / harv if harv and harv > 0 and not np.isnan(prod) else np.nan


def calculate_aggregated_harvest_ratio(df: pd.DataFrame) -> float:
    plant, harv = _sum(df, "area_plant_rai"), _sum(df, "area_harvest_rai")
    return harv / plant * 100.0 if plant and plant > 0 and not np.isnan(harv) else np.nan


def calculate_unharvested_area(df: pd.DataFrame) -> float:
    plant, harv = _sum(df, "area_plant_rai"), _sum(df, "area_harvest_rai")
    return max(plant - harv, 0.0) if not (np.isnan(plant) or np.isnan(harv)) else np.nan


def aggregate_agricultural_kpis(df: pd.DataFrame) -> Dict[str, float]:
    return {
        "total_plant_rai": _sum(df, "area_plant_rai"),
        "total_harvest_rai": _sum(df, "area_harvest_rai"),
        "total_production_ton": _sum(df, "production_ton"),
        "weighted_yield_kg_rai": calculate_weighted_yield(df),
        "harvest_ratio_pct": calculate_aggregated_harvest_ratio(df),
        "unharvested_rai": calculate_unharvested_area(df),
        "n_provinces": int(df["province"].nunique()) if "province" in df.columns else 0,
    }


def aggregate_by(df: pd.DataFrame, keys) -> pd.DataFrame:
    """Sum additive columns by keys and recompute yield / harvest ratio."""
    if df.empty:
        return pd.DataFrame(columns=list(keys) + ["area_plant_rai", "area_harvest_rai", "production_ton",
                                                   "calc_yield_per_rai", "calc_harvest_ratio"])
    g = df.groupby(list(keys), as_index=False).agg(
        area_plant_rai=("area_plant_rai", lambda s: s.sum(min_count=1)),
        area_harvest_rai=("area_harvest_rai", lambda s: s.sum(min_count=1)),
        production_ton=("production_ton", lambda s: s.sum(min_count=1)))
    g["calc_yield_per_rai"] = np.where(g["area_harvest_rai"] > 0, g["production_ton"] * 1000.0 / g["area_harvest_rai"], np.nan)
    g["calc_harvest_ratio"] = np.where(g["area_plant_rai"] > 0, g["area_harvest_rai"] / g["area_plant_rai"] * 100.0, np.nan)
    return g


def compute_yoy_dataframe(df: pd.DataFrame, metric: str = "production_ton", by: str = "year") -> pd.DataFrame:
    g = aggregate_by(df, [by]).sort_values(by)
    g["yoy_change"] = g[metric].diff()
    g["yoy_pct"] = g[metric].pct_change() * 100.0
    return g


def compute_cv_summary(df: pd.DataFrame, metric: str = "calc_yield_per_rai") -> pd.DataFrame:
    """Coefficient of variation of a metric across years, per province."""
    g = aggregate_by(df, ["province", "year"])
    s = g.groupby("province")[metric].agg(["mean", "std", "count"]).reset_index()
    s["cv_pct"] = np.where(s["mean"] > 0, s["std"] / s["mean"] * 100.0, np.nan)
    return s.sort_values("cv_pct", ascending=False)
