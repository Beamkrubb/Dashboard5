"""Pipeline tests on small synthetic tables shaped like the OAE / LDD / HII / NABC files."""
import json

import numpy as np
import pandas as pd

from pipeline import province as P
from pipeline import transform as T


# ---------------- province ----------------
def test_77_provinces_unique_codes_and_regions():
    df = P.lookup_frame()
    assert len(df) == 77 and df["pro_code"].is_unique
    assert df["region_oae"].value_counts().to_dict() == {"กลาง": 26, "ตะวันออกเฉียงเหนือ": 20, "เหนือ": 17, "ใต้": 14}


def test_name_normalisation():
    cases = {"กรุงเทพฯ": "10", "จ.เชียงใหม่": "50", "จังหวัด ขอนแก่น": "40", "Bueng Kan": "38",
             "Phra Nakhon Si Ayutthaya": "14", "nakhon ratchasima": "30", "56": "56", 72.0: "72"}
    for name, code in cases.items():
        assert P.to_pro_code(name) == code, name
    for not_prov in ("รวมทั้งประเทศ", "ภาคเหนือ", "", None, "99"):
        assert P.to_pro_code(not_prov) is None


def test_geojson_centroid_and_crs_drop(tmp_path):
    gj = {"type": "FeatureCollection", "crs": {"type": "name"},
          "features": [{"type": "Feature", "properties": {"pro_code": 56, "pro_th": "พะเยา"},
                        "geometry": {"type": "Polygon",
                                     "coordinates": [[[100, 19], [101, 19], [101, 20], [100, 20], [100, 19]]]}}]}
    src = tmp_path / "in.geojson"
    src.write_text(json.dumps(gj), encoding="utf-8")
    out = P.clean_geojson(src, tmp_path / "out.geojson")
    assert "crs" not in out and out["features"][0]["properties"]["pro_code"] == "56"
    lk = P.lookup_from_geojson(out).set_index("pro_code")
    assert abs(lk.loc["56", "centroid_lat"] - 19.5) < 1e-6 and abs(lk.loc["56", "centroid_lon"] - 100.5) < 1e-6


# ---------------- helpers ----------------
def test_year_and_number_parsing():
    assert T.parse_year(2562) == (2019, None)
    assert T.parse_year("2562/63") == (2019, "2562/63")
    assert T.parse_year("2019") == (2019, None)
    assert T.parse_year("ปี") == (None, None)
    s = T.to_number(pd.Series(["1,234.5", "-", "", "n.a.", "0"]))
    assert s.iloc[0] == 1234.5 and s.iloc[1:4].isna().all() and s.iloc[4] == 0


# ---------------- D01 ----------------
def test_production_long_layout(tmp_path):
    csv = ("หมายเหตุ: ข้อมูลจาก สศก.\n"
           "ปี,จังหวัด,เนื้อที่เพาะปลูก (ไร่),เนื้อที่เก็บเกี่ยว (ไร่),ผลผลิต (ตัน),ผลผลิตต่อไร่ (กก.)\n"
           "2562,นครราชสีมา,\"2,000,000\",\"1,900,000\",\"6,000,000\",\"3,158\"\n"
           "2562,รวมทั้งประเทศ,1,1,1,1\n"
           "2561,กำแพงเพชร,-,500,1500,3000\n")
    f = tmp_path / "cassava_production_province.csv"
    f.write_bytes(csv.encode("cp874"))  # Thai legacy encoding must be handled
    rep = {}
    out = T.tidy_production(T.read_table(f), "cassava", "D01", "u", rep)
    assert list(out.columns) == T.TIDY_COLUMNS
    korat = out[(out.province_code == "30") & (out.metric == "production")]
    assert korat.value.iloc[0] == 6_000_000 and korat.year_ce.iloc[0] == 2019 and korat.unit.iloc[0] == "ton"
    assert set(out.metric) == {"area_plant", "area_harvest", "production", "yield"}
    # "-" stays missing -> row dropped, not zero
    assert out[(out.province_code == "62") & (out.metric == "area_plant")].empty
    assert "รวมทั้งประเทศ" in rep["unmatched_provinces"]


def test_production_wide_layout():
    raw = pd.DataFrame({"จังหวัด": ["เชียงราย", "น่าน"], "รายการ": ["ผลผลิต (ตัน)", "ผลผลิต (ตัน)"],
                        "2560": ["10", "20"], "2561": ["11", "21"]})
    out = T.tidy_production(raw, "maize")
    assert len(out) == 4 and set(out.year_ce) == {2017, 2018} and set(out.metric) == {"production"}


# ---------------- D05 ----------------
def test_suitability():
    raw = pd.DataFrame({"จังหวัด": ["ขอนแก่น"], "S1 (ไร่)": ["100"], "S2 (ไร่)": ["200"],
                        "S3 (ไร่)": ["300"], "N (ไร่)": ["400"], "รวม": ["1000"]})
    out = T.tidy_suitability(raw, "rice")
    assert dict(zip(out.metric, out.value)) == {"suitability_s1": 100, "suitability_s2": 200,
                                                 "suitability_s3": 300, "suitability_n": 400}


# ---------------- D07 ----------------
def test_monthly_climate_and_annual_sum():
    rows = [{"จังหวัด": "ลำปาง", "ปี": "2562", "เดือน": m, "ฝน (มม.)": "10"} for m in range(1, 13)]
    rows += [{"จังหวัด": "แพร่", "ปี": "2562", "เดือน": "ม.ค.", "ฝน (มม.)": "5"}]  # incomplete year
    m = T.tidy_monthly_climate(pd.DataFrame(rows), "rain", "mm")
    assert m.period.iloc[0] == "2019-01"
    annual = T.annual_rain_from_monthly(m).set_index("province_code")
    assert annual.loc["52", "value"] == 120
    assert np.isnan(annual.loc["54", "value"])  # < 12 months -> missing, not partial sum


def test_open_meteo_monthly():
    payload = {"daily": {"time": ["2018-01-01", "2018-01-02", "2018-02-01"],
                         "precipitation_sum": [1.5, 2.0, None]}}
    out = T.tidy_open_meteo_daily(payload, "50", "เชียงใหม่", "u")
    assert out.period.tolist() == ["2018-01"] and out.value.iloc[0] == 3.5
    assert out.source_id.iloc[0] == "D07-ERA5"


# ---------------- D02 ----------------
def test_weekly_prices():
    recs = [{"date": "2019-04-01", "price": "1.95"}, {"date": "2019-04-08", "price": "2.05"}]
    out = T.tidy_weekly_prices(recs, "cassava", "u")
    assert out.period.tolist() == ["2019-W14", "2019-W15"] and out.province_code.eq("00").all()


# ---------------- real OAE / NABC layouts (seen in downloads 2026-10-23) ----------------
def test_production_attribute_value_layout():
    raw = pd.DataFrame({
        "year": [2562, 2562, 2562], "year_crop": ["2561/62"] * 3, "province_name": ["นครราชสีมา"] * 3,
        "commod": ["มันสำปะหลัง"] * 3, "attribute": ["ผลผลิต", "ผลผลิตต่อเนื้อที่เก็บเกี่ยว", "เนื้อที่เก็บเกี่ยว"],
        "values": ["6000000", "3158", "1900000"], "unit": ["ตัน", "กิโลกรัมต่อไร่", "ไร่"]})
    out = T.tidy_production(raw, "cassava").set_index("metric")
    assert out.loc["production", "value"] == 6_000_000 and out.loc["production", "year_ce"] == 2019
    assert out.loc["yield_harvested", "unit"] == "kg/rai" and out.loc["area_harvest", "value"] == 1_900_000
    assert out.loc["production", "period"] == "2561/62"


def test_weekly_prices_nabc_layout():
    recs = [{"year_th": 2562, "month": "10", "week": 3, "value": "16394.43", "unit": "บาท/ตัน"}]
    out = T.tidy_weekly_prices(recs, "rice_hommali", "u")
    assert out.period.iloc[0] == "2019-10-W3" and abs(out.value.iloc[0] - 16.39443) < 1e-9
