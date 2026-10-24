import sys, json, glob, os; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from src import data_loader as L, data_cleaning as C
from pipeline.province import to_pro_code, PROVINCES
from pipeline import transform as T
ag = C.clean_agriculture_data(L.load_agriculture_data())
soil = C.clean_ldd_soil_suitability_data(L.load_ldd_soil_suitability_data())
provs = C.OFFICIAL_77_PROVINCES; pidx = {p:i for i,p in enumerate(provs)}
code_of = {th: c for c, th, _, _ in PROVINCES}
products = sorted(ag['product'].unique().tolist())
def r(v, d=0): return None if v is None or pd.isna(v) else round(float(v), d)
rows = [[int(x.year), products.index(x.product), pidx[x.province], r(x.area_plant_rai), r(x.area_harvest_rai), r(x.production_ton)] for x in ag.itertuples()]
basis = ag.groupby('product').area_basis.first().to_dict()
# HII provincial monthly rain (IDW)
h = pd.read_csv(glob.glob('raw/D07/*รายเดือน_รายจังหวัด_*')[0], encoding='utf-8-sig')
h['p'] = h.PROV_ID.astype(str).str.zfill(2).map({c: pidx[th] for c, th, _, _ in PROVINCES})
rain, season = {}, {}
for (y, p), g in h.groupby(['YEAR', 'p']):
    if len(g) == 12:
        rain.setdefault(str(y+543), {})[int(p)] = r(g.AvgRain.sum())
        season.setdefault(str(y+543), {})[int(p)] = r(g[g.MONTH.between(5,10)].AvgRain.sum())
# HII national monthly 1970-2025
n = pd.read_csv(glob.glob('raw/D07/*ทั้งประเทศไทย*')[0], encoding='utf-8-sig')
na = n.groupby('YEAR').agg(s=('MEAN','sum'), k=('MEAN','count'))
national = {str(y+543): r(v.s) for y, v in na.iterrows() if v.k == 12}
normal = r(na.loc[1991:2020].s.mean())
# HII 30-year provincial normal (2534-2563)
nm = pd.read_csv(glob.glob('raw/D07/*30_ปี*')[0], encoding='utf-8-sig')
nm['p'] = nm.PROV_CODE.astype(str).str.zfill(2).map({c: pidx[th] for c, th, _, _ in PROVINCES})
prov_normal = {int(p): r(g.MEAN.sum()) for p, g in nm.groupby('p') if len(g) == 12}
# DDPM 2562 flood (farm area flooded, rai) and drought (villages declared)
f = pd.read_csv(glob.glob('raw/D06/dpm-gd027__2562*')[0], encoding='utf-8-sig'); f.columns = [c.strip() for c in f.columns]
f = f[f.Province.map(lambda v: to_pro_code(v) is not None)]
num = lambda s: pd.to_numeric(s.astype(str).str.replace(',', ''), errors='coerce')
flood = {}
for x in f.itertuples(index=False):
    d = x._asdict() if hasattr(x, '_asdict') else None
for _, x in f.iterrows():
    p = pidx[C.CODE_TO_PROVINCE[to_pro_code(x.Province)]]
    flood[p] = [r(num(pd.Series([x['Rice Fields']]))[0]), r(num(pd.Series([x['Garden Crops']]))[0]),
                r(num(pd.Series([x['Field Crops']]))[0]), r(num(pd.Series([x['Agri. Damage (THB)']]))[0])]
dr = pd.read_csv(glob.glob('raw/D06/dpm-gd028__2562*')[0], encoding='utf-8-sig'); dr = dr[dr.Province.map(lambda v: to_pro_code(v) is not None)]
drought = {pidx[C.CODE_TO_PROVINCE[to_pro_code(p)]]: int(len(g)) for p, g in dr.groupby('Province')}
# prices (all NABC series)
NAMES = {'rice_hommali':'ข้าวเปลือกเจ้าหอมมะลิ ความชื้น 15%','rice_white':'ข้าวเปลือกเจ้า ความชื้น 15%','cassava_fresh':'มันสำปะหลังสด คละ',
         'cassava_chips':'มันเส้น คละ','rubber_sheet':'ยางแผ่นดิบ ชั้น 3','rubber_cuplump':'ยางก้อน คละ','rubber_latex':'น้ำยางสด คละ','oil_palm':'ผลปาล์มน้ำมันทั้งทะลาย คละ'}
prices = {}
for k, label in NAMES.items():
    fp = f'raw/D02/weekly_{k}.json'
    if not os.path.exists(fp): continue
    recs = json.load(open(fp, encoding='utf-8'))['records']
    t = T.tidy_weekly_prices(recs, k, 'https://agriapi.nabc.go.th/api/weekly-prices/product')
    if t.empty: continue
    parts = t.period.str.extract(r'^(\d{4})-(\d{2})-W(\d)$').astype(int)
    prices[label] = [[int(a)+543, int(b), int(c), r(v, 3)] for (a, b, c), v in zip(parts.values, t.value)]
soilj = {c: {pidx[x.province]: [r(x.s1_rai), r(x.s2_rai), r(x.s3_rai), r(x.n_rai)] for x in g.itertuples() if x.province in pidx} for c, g in soil.groupby('crop')}
# ERA5 temperature: annual mean of daily 2 m mean temperature per province centroid (pre-aggregated on the PC)
temp = {}
tp = 'raw/ERA5/era5_temp_annual.json'
if os.path.exists(tp):
    for ybe, d in json.load(open(tp)).items():
        temp[ybe] = {pidx[C.CODE_TO_PROVINCE[c]]: v for c, v in d.items() if c in C.CODE_TO_PROVINCE}
geo = json.load(open('geo_simplified.json')) if os.path.exists('geo_simplified.json') else json.load(open('data.json'))['geo']
json.dump(geo, open('geo_simplified.json', 'w'), ensure_ascii=False)
data = {"provinces": provs, "codes": [code_of[p] for p in provs], "regions": [C.PROVINCE_TO_REGION[p] for p in provs], "regionNames": C.REGION_NAMES,
        "products": products, "basis": basis, "ag": rows, "rain": rain, "season": season, "national": national, "nationalNormal": normal,
        "provNormal": prov_normal, "flood2562": flood, "drought2562": drought, "prices": prices, "soil": soilj, "temp": temp, "geo": geo}
s = json.dumps(data, ensure_ascii=False, separators=(',', ':')); open('data2.json', 'w').write(s)
print(round(len(s)/1e6, 2), 'MB | rain yrs', list(rain), '| national', min(national), max(national), 'normal', normal,
      '| flood provs', len(flood), 'drought provs', len(drought), '| prices', {k: len(v) for k, v in prices.items()}, '| temp yrs', list(temp)[:3], len(temp))
print('2561-2562 price records', sum(1 for v in prices.values() for x in v if x[0] in (2561, 2562)))
print('national 2550..2562', {k: national[k] for k in ['2550', '2556', '2562']})
