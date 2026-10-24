"""Session-state defaults and the shared production filter."""
from __future__ import annotations

from typing import Optional

import pandas as pd

ALL = "ทั้งหมด"
DEFAULT_METRIC = "production_ton"

_STATE_DEFAULTS = {
    "selected_region": ALL,
    "selected_province": ALL,
    "selected_product": ALL,
    "selected_metric": DEFAULT_METRIC,
}
_WIDGET_KEYS = ["reg_select_key", "prov_select_key", "prod_select_key", "year_select_key",
                "metric_select_key", "global_search_input"]


def init_session_state(default_year: int) -> None:
    import streamlit as st

    for k, v in _STATE_DEFAULTS.items():
        st.session_state.setdefault(k, v)
    st.session_state.setdefault("selected_year", default_year)


def reset_filters(default_year: int) -> None:
    import streamlit as st

    for k, v in _STATE_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state["selected_year"] = default_year
    for k in _WIDGET_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def apply_ag_filters(df: pd.DataFrame, year: Optional[int] = None, region: Optional[str] = None,
                     province: Optional[str] = None, product: Optional[str] = None,
                     geo_level: str = "province") -> pd.DataFrame:
    """Filter production rows; None or 'ทั้งหมด' means no filter on that dimension."""
    if df is None or df.empty:
        return pd.DataFrame(columns=getattr(df, "columns", []))
    out = df
    if "geo_level" in out.columns and geo_level:
        out = out[out["geo_level"] == geo_level]
    if year is not None:
        out = out[out["year"] == int(year)]
    if region and region != ALL:
        out = out[out["region"] == region]
    if province and province != ALL:
        out = out[out["province"] == province]
    if product and product != ALL:
        out = out[out["product"] == product]
    return out.copy()
