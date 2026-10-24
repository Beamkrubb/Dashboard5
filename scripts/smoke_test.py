"""
Headless smoke test of the Streamlit app: renders app.py, then exercises every product,
the main years, every map layer and every Tab 4 topic, and reports any exception.

    python scripts/smoke_test.py          (exit code 0 = no exceptions)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "app.py")
failures = []


def run(at: AppTest, label: str) -> AppTest:
    t0 = time.time()
    at.run(timeout=180)
    errs = [e.value for e in at.exception]
    status = "FAIL" if errs else "ok"
    print(f"[{status}] {label} ({time.time() - t0:.1f}s)")
    for e in errs:
        print("      ", str(e)[:800])
        failures.append((label, str(e)[:800]))
    return at


def select(at: AppTest, key: str, value):
    at.selectbox(key=key).set_value(value)


def main() -> int:
    at = AppTest.from_file(APP, default_timeout=180)
    run(at, "initial render")
    if failures:
        return 1
    products = at.selectbox(key="prod_select_key").options
    years = at.selectbox(key="year_select_key").options
    print(f"products: {products}\nyears: {years[:5]} ... {years[-3:]}")

    for prod in products:
        select(at, "prod_select_key", prod)
        run(at, f"product = {prod}")
    for yr in [y for y in years if str(y) in ("2561", "2562", "2550")]:
        select(at, "year_select_key", yr)
        run(at, f"year = {yr}")
    for metric in at.selectbox(key="metric_select_key").options:
        select(at, "metric_select_key", metric)
        run(at, f"metric = {metric}")
    select(at, "prov_select_key", "นครราชสีมา")
    run(at, "province = นครราชสีมา")
    for opt in at.radio(key="tab2_layer_select").options:
        at.radio(key="tab2_layer_select").set_value(opt)
        run(at, f"tab2 layer = {opt}")
    for opt in at.radio(key="tab4_driver_layer_select").options:
        at.radio(key="tab4_driver_layer_select").set_value(opt)
        run(at, f"tab4 layer = {opt}")
    for opt in at.selectbox(key="tab4_topic_select").options:
        select(at, "tab4_topic_select", opt)
        run(at, f"tab4 topic = {opt}")
    for opt in at.selectbox(key="tab3_price_year_select").options:
        select(at, "tab3_price_year_select", opt)
        run(at, f"tab3 price year = {opt}")
    select(at, "reg_select_key", "ภาคใต้")
    run(at, "region = ภาคใต้")

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
