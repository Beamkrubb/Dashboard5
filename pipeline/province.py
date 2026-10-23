"""
Province reference table and name normalisation (handoff_n.md: "pro_code is the key").

The 77 provinces below use the 2-digit DOPA codes, which match `pro_code` in
OpenGISData-Thailand/provinces.geojson. `region_oae` is the 4-region grouping
used by OAE statistics (North 17, Northeast 20, Central incl. East/West 26, South 14).
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

NORTH, NORTHEAST, CENTRAL, SOUTH = "เหนือ", "ตะวันออกเฉียงเหนือ", "กลาง", "ใต้"

# (pro_code, Thai, English, OAE region)
PROVINCES: List[tuple] = [
    ("10", "กรุงเทพมหานคร", "Bangkok", CENTRAL),
    ("11", "สมุทรปราการ", "Samut Prakan", CENTRAL),
    ("12", "นนทบุรี", "Nonthaburi", CENTRAL),
    ("13", "ปทุมธานี", "Pathum Thani", CENTRAL),
    ("14", "พระนครศรีอยุธยา", "Phra Nakhon Si Ayutthaya", CENTRAL),
    ("15", "อ่างทอง", "Ang Thong", CENTRAL),
    ("16", "ลพบุรี", "Lop Buri", CENTRAL),
    ("17", "สิงห์บุรี", "Sing Buri", CENTRAL),
    ("18", "ชัยนาท", "Chai Nat", CENTRAL),
    ("19", "สระบุรี", "Saraburi", CENTRAL),
    ("20", "ชลบุรี", "Chon Buri", CENTRAL),
    ("21", "ระยอง", "Rayong", CENTRAL),
    ("22", "จันทบุรี", "Chanthaburi", CENTRAL),
    ("23", "ตราด", "Trat", CENTRAL),
    ("24", "ฉะเชิงเทรา", "Chachoengsao", CENTRAL),
    ("25", "ปราจีนบุรี", "Prachin Buri", CENTRAL),
    ("26", "นครนายก", "Nakhon Nayok", CENTRAL),
    ("27", "สระแก้ว", "Sa Kaeo", CENTRAL),
    ("30", "นครราชสีมา", "Nakhon Ratchasima", NORTHEAST),
    ("31", "บุรีรัมย์", "Buri Ram", NORTHEAST),
    ("32", "สุรินทร์", "Surin", NORTHEAST),
    ("33", "ศรีสะเกษ", "Si Sa Ket", NORTHEAST),
    ("34", "อุบลราชธานี", "Ubon Ratchathani", NORTHEAST),
    ("35", "ยโสธร", "Yasothon", NORTHEAST),
    ("36", "ชัยภูมิ", "Chaiyaphum", NORTHEAST),
    ("37", "อำนาจเจริญ", "Amnat Charoen", NORTHEAST),
    ("38", "บึงกาฬ", "Bueng Kan", NORTHEAST),
    ("39", "หนองบัวลำภู", "Nong Bua Lam Phu", NORTHEAST),
    ("40", "ขอนแก่น", "Khon Kaen", NORTHEAST),
    ("41", "อุดรธานี", "Udon Thani", NORTHEAST),
    ("42", "เลย", "Loei", NORTHEAST),
    ("43", "หนองคาย", "Nong Khai", NORTHEAST),
    ("44", "มหาสารคาม", "Maha Sarakham", NORTHEAST),
    ("45", "ร้อยเอ็ด", "Roi Et", NORTHEAST),
    ("46", "กาฬสินธุ์", "Kalasin", NORTHEAST),
    ("47", "สกลนคร", "Sakon Nakhon", NORTHEAST),
    ("48", "นครพนม", "Nakhon Phanom", NORTHEAST),
    ("49", "มุกดาหาร", "Mukdahan", NORTHEAST),
    ("50", "เชียงใหม่", "Chiang Mai", NORTH),
    ("51", "ลำพูน", "Lamphun", NORTH),
    ("52", "ลำปาง", "Lampang", NORTH),
    ("53", "อุตรดิตถ์", "Uttaradit", NORTH),
    ("54", "แพร่", "Phrae", NORTH),
    ("55", "น่าน", "Nan", NORTH),
    ("56", "พะเยา", "Phayao", NORTH),
    ("57", "เชียงราย", "Chiang Rai", NORTH),
    ("58", "แม่ฮ่องสอน", "Mae Hong Son", NORTH),
    ("60", "นครสวรรค์", "Nakhon Sawan", NORTH),
    ("61", "อุทัยธานี", "Uthai Thani", NORTH),
    ("62", "กำแพงเพชร", "Kamphaeng Phet", NORTH),
    ("63", "ตาก", "Tak", NORTH),
    ("64", "สุโขทัย", "Sukhothai", NORTH),
    ("65", "พิษณุโลก", "Phitsanulok", NORTH),
    ("66", "พิจิตร", "Phichit", NORTH),
    ("67", "เพชรบูรณ์", "Phetchabun", NORTH),
    ("70", "ราชบุรี", "Ratchaburi", CENTRAL),
    ("71", "กาญจนบุรี", "Kanchanaburi", CENTRAL),
    ("72", "สุพรรณบุรี", "Suphan Buri", CENTRAL),
    ("73", "นครปฐม", "Nakhon Pathom", CENTRAL),
    ("74", "สมุทรสาคร", "Samut Sakhon", CENTRAL),
    ("75", "สมุทรสงคราม", "Samut Songkhram", CENTRAL),
    ("76", "เพชรบุรี", "Phetchaburi", CENTRAL),
    ("77", "ประจวบคีรีขันธ์", "Prachuap Khiri Khan", CENTRAL),
    ("80", "นครศรีธรรมราช", "Nakhon Si Thammarat", SOUTH),
    ("81", "กระบี่", "Krabi", SOUTH),
    ("82", "พังงา", "Phangnga", SOUTH),
    ("83", "ภูเก็ต", "Phuket", SOUTH),
    ("84", "สุราษฎร์ธานี", "Surat Thani", SOUTH),
    ("85", "ระนอง", "Ranong", SOUTH),
    ("86", "ชุมพร", "Chumphon", SOUTH),
    ("90", "สงขลา", "Songkhla", SOUTH),
    ("91", "สตูล", "Satun", SOUTH),
    ("92", "ตรัง", "Trang", SOUTH),
    ("93", "พัทลุง", "Phatthalung", SOUTH),
    ("94", "ปัตตานี", "Pattani", SOUTH),
    ("95", "ยะลา", "Yala", SOUTH),
    ("96", "นราธิวาส", "Narathiwat", SOUTH),
]

BUENG_KAN_CODE = "38"
BUENG_KAN_FIRST_YEAR_CE = 2011  # split from Nong Khai on 23 Mar 2011 (B.E. 2554)

# Extra spellings seen across OAE / HII / DDPM / LDD files.
_ALIASES: Dict[str, str] = {
    "กรุงเทพ": "10", "กรุงเทพฯ": "10", "กทม": "10", "กรุงเทพมหานครฯ": "10", "bangkokmetropolis": "10",
    "อยุธยา": "14", "ayutthaya": "14", "phranakhonsiayutthaya": "14",
    "lopburi": "16", "singburi": "17", "chainat": "18", "chonburi": "20",
    "prachinburi": "25", "sakaeo": "27", "korat": "30", "โคราช": "30",
    "buriram": "31", "sisaket": "33", "srisaket": "33", "ubon": "34",
    "buengkan": "38", "bungkan": "38", "nongbualamphu": "39", "nongbualumphu": "39",
    "kalasin": "46", "nakhonphanom": "48", "phangnga": "82", "phang-nga": "82",
    "suphanburi": "72", "petchaburi": "76", "phetburi": "76", "prachuapkhirikhan": "77",
    "nakhonsithammarat": "80", "suratthani": "84", "uthaithani": "61",
    "kamphaengphet": "62", "phetchabun": "67", "phetchaboon": "67",
}

_PREFIXES = ("จังหวัด", "จ.", "changwat", "province")


def _key(name: str) -> str:
    """Normalise a province name for matching (Thai or English)."""
    s = unicodedata.normalize("NFC", str(name)).strip().lower()
    for p in _PREFIXES:
        if s.startswith(p):
            s = s[len(p):]
    s = re.sub(r"\(.*?\)", "", s)               # drop bracketed notes
    s = re.sub(r"[\s\.\-_'’]+", "", s)          # spaces, dots, dashes
    s = s.replace("province", "")
    return s


def _build_index() -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for code, th, en, _ in PROVINCES:
        idx[_key(th)] = code
        idx[_key(en)] = code
        idx[code] = code
    for alias, code in _ALIASES.items():
        idx[_key(alias)] = code
    return idx


_INDEX = _build_index()


def to_pro_code(name) -> Optional[str]:
    """Return the 2-digit pro_code for a province name/code, or None if it is not a province
    (e.g. 'รวมทั้งประเทศ', region subtotal rows)."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    s = str(name).strip()
    if re.fullmatch(r"\d{1,2}(\.0)?", s):
        s = s.split(".")[0].zfill(2)
        return s if any(s == c for c, *_ in PROVINCES) else None
    return _INDEX.get(_key(s))


def lookup_frame() -> pd.DataFrame:
    df = pd.DataFrame(PROVINCES, columns=["pro_code", "province_th", "province_en", "region_oae"])
    return df


def add_province_code(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    """Add pro_code + canonical province_th; rows that are not provinces get NaN."""
    out = df.copy()
    out["province_code"] = out[name_col].map(to_pro_code)
    th = dict((c, t) for c, t, *_ in PROVINCES)
    out["province_th"] = out["province_code"].map(th)
    return out


def unmatched_names(values: Iterable) -> List[str]:
    """Names that do not resolve to a province, for the cleaning report."""
    return sorted({str(v) for v in values if v is not None and str(v).strip() and to_pro_code(v) is None})


# ---------------------------------------------------------------------------
# GeoJSON helpers (D10)
# ---------------------------------------------------------------------------
def _ring_centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-12:
        xs, ys = zip(*ring)
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), abs(a)


def geometry_centroid(geom: dict):
    """Area-weighted centroid (lon, lat) of a Polygon/MultiPolygon using outer rings."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    tx = ty = tw = 0.0
    for poly in polys:
        x, y, w = _ring_centroid([tuple(p[:2]) for p in poly[0]])
        tx += x * w
        ty += y * w
        tw += w
    return (tx / tw, ty / tw) if tw else (x, y)


def clean_geojson(path_in: Path, path_out: Path) -> dict:
    """Drop the legacy 'crs' member (RFC 7946) and normalise pro_code to 2 digits."""
    gj = json.loads(Path(path_in).read_text(encoding="utf-8"))
    gj.pop("crs", None)
    for f in gj.get("features", []):
        props = f.setdefault("properties", {})
        if "pro_code" in props:
            props["pro_code"] = str(props["pro_code"]).zfill(2)
    Path(path_out).parent.mkdir(parents=True, exist_ok=True)
    Path(path_out).write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    return gj


def lookup_from_geojson(gj: dict) -> pd.DataFrame:
    """province_lookup.csv: static table + region names and centroids from the GeoJSON."""
    base = lookup_frame()
    rows = []
    for f in gj.get("features", []):
        p = f.get("properties", {})
        code = str(p.get("pro_code", "")).zfill(2)
        lon, lat = geometry_centroid(f["geometry"])
        rows.append({"pro_code": code, "reg_nesdb": p.get("reg_nesdb"), "reg_royin": p.get("reg_royin"),
                     "area_sqkm": p.get("area_sqkm"), "centroid_lat": round(lat, 5),
                     "centroid_lon": round(lon, 5)})
    geo = pd.DataFrame(rows)
    if geo.empty:
        return base
    return base.merge(geo, on="pro_code", how="left")
