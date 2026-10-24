"""Extend data2.json -> data3.json with the objective-aligned datasets (26 crops, HII temperature, RID irrigation,
NSO mechanisation, DOAE in/out irrigation disaster area, OAE household expenses, OAE cost/price/net)."""
import json, sys, re
import pandas as pd
RAW = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Dashboard5/data/raw'
d = json.load(open('data2.json')); provs = d['provinces']; pidx = {p: i for i, p in enumerate(provs)}
codes = d['codes']; code_idx = {int(c): i for i, c in enumerate(codes)}
ALIAS = {'กรุงเทพฯ': 'กรุงเทพมหานคร', 'กทม.': 'กรุงเทพมหานคร', 'บึงกาฬ ': 'บึงกาฬ'}
def P(name):
    n = str(name).strip(); n = ALIAS.get(n, n); n = re.sub(r'^จังหวัด', '', n)
    return pidx.get(n)
def r(v, k=0):
    return None if v is None or pd.isna(v) else round(float(v), k)
# 1. production 26 crops 2550-2562
SHORT = ['ข้าวนาปี', 'ข้าวนาปรัง', 'มันสำปะหลัง', 'ข้าวโพดเลี้ยงสัตว์']
p = pd.read_csv(f'{RAW}/D01x/production_y_oae.csv', encoding='utf-8-sig')
p = p[p.province.map(lambda x: P(x) is not None)]
products = SHORT + sorted(set(p['product']) - set(SHORT))
rows = {(int(x.year), products.index(x.product), P(x.province)): [r(x.area_plant_rai), r(x.area_harvest_rai), r(x.production_ton)] for x in p.itertuples()}
fill = {}
OLD = {'ยางพารา': 'ยางพารา', 'ปาล์มน้ำมัน': 'ปาล์มน้ำมัน'}
oldP = d['products']
for y, k, pi, a, h, t in d['ag']:
    nm = oldP[k]
    if nm in OLD and y == 2562:
        key = (y, products.index(OLD[nm]), pi)
        if key not in rows or rows[key][2] is None:
            rows[key] = [a, h, t]; fill.setdefault(OLD[nm], 0); fill[OLD[nm]] += 1
ag = [[y, k, pi] + v for (y, k, pi), v in sorted(rows.items())]
# 2. HII monthly temperature 2018-2019 -> annual mean / max / min (12 months required)
t = pd.read_csv(f'{RAW}/../interim/hii_temp_2018_2019.csv')
t['yr'] = t.ym.astype(str).str[:4].astype(int) + 543
t['p'] = t.province_code.map(lambda c: code_idx.get(int(c)))
t['p'] = t['p'].fillna(t.province_name.map(P))
tempHII = {}
for (y, pi), g in t.dropna(subset=['p']).groupby(['yr', 'p']):
    if len(g) == 12:
        tempHII.setdefault(str(y), {})[int(pi)] = [r(g.temperature.mean(), 2), r(g.max_temperature.max(), 1), r(g.min_temperature.min(), 1)]
# 3. NSO 2556 agricultural census (tables 0301, 0602, 1101, 1201)
def nso(t):
    x = pd.read_csv(f'{RAW}/D03/nso_AGC_0506_11_{t}.csv', encoding='utf-8-sig'); x['p'] = x.PROVINCE.map(P); return x
h = nso('0301'); holders = {int(a): int(b) for a, b in zip(h.p, h.VALUE) if pd.notna(a)}
lu = nso('0602'); land = {}
for x in lu.itertuples():
    if pd.notna(x.p) and pd.notna(x.VALUE): land.setdefault(int(x.p), {})[x._1.strip()] = int(x.VALUE)
m = nso('1201'); mech = {}
for pi, g in m.dropna(subset=['p']).groupby('p'):
    v = {k.strip(): val for k, val in zip(g.MACHINERY, g.VALUE)}
    rep, use = v.get('ผู้ถือครองที่รายงานการใช้เครื่องจักร'), v.get('มีการใช้เครื่องจักร')
    mech[int(pi)] = [int(use), int(rep), r(100 * use / rep, 1)] if rep else None
fz = nso('1101'); fert = {}
for pi, g in fz.dropna(subset=['p']).groupby('p'):
    v = {k.strip(): val for k, val in zip(g.FERTILIZER, g.VALUE)}
    rep, use = v.get('รายงานการใช้ปุ๋ย'), v.get('มีการใช้ปุ๋ย')
    fert[int(pi)] = r(100 * use / rep, 1) if rep else None
# 4. RID irrigation-project area per province (rasterised, see rid_grid.py)
import os
rid = json.load(open('rid_irr_by_province.json')) if os.path.exists('rid_irr_by_province.json') else {}
irr = {}
for n, v in rid.items():
    pi = P(n)
    if pi is None: continue
    hold = land.get(pi, {}).get('เนื้อที่ถือครองทำการเกษตร')
    irr[pi] = [v['irr_rai'], v['irr_large_rai'], v['prov_rai'], hold, r(100 * v['irr_rai'] / v['prov_rai'], 1) if v['prov_rai'] else None,
               r(100 * v['irr_rai'] / hold, 1) if hold else None]
# 5. DOAE flood / drought affected farm area, inside vs outside irrigation zones (rai)
def num(s):
    s = str(s).replace(',', '').strip()
    try: return float(s)
    except ValueError: return 0.0
doae = {}
for f, j in (('doae_disaster_in_irrigation.csv', 0), ('doae_disaster_outside_irrigation.csv', 1)):
    x = pd.read_csv(f'{RAW}/D04/{f}', encoding='utf-8-sig', dtype=str); x.columns = [c.strip() for c in x.columns]
    for pv, g in x.groupby('จังหวัด'):
        pi = P(pv)
        if pi is None: print('DOAE unmatched', pv); continue
        e = doae.setdefault(pi, [0, 0, 0, 0])  # flood_in, drought_in, flood_out, drought_out
        e[2 * j] += sum(num(v) for v in g['อุทกภัย']); e[2 * j + 1] += sum(num(v) for v in g['ภัยแล้ง'])
doae = {k: [r(v) for v in vals] for k, vals in doae.items()}
# 6. OAE household cash expenses (national, บาท/ครัวเรือน)
hx = pd.read_csv(f'{RAW}/D03/oae_household_expenses.csv', encoding='utf-8-sig')
hh = {}
for x in hx.itertuples():
    hh.setdefault(x.year, []).append([x.subcatagory, x.list, r(x.value)])
# 7. OAE cost / price / net per ton
cost = json.load(open('oae_cost_2567.json'))
# Agri-Map soil names -> production names
SOILMAP = {'มันสำปะหลังโรงงาน': 'มันสำปะหลัง', 'สับปะรดโรงงาน': 'สับปะรด', 'กาแฟโรบัสตา': 'กาแฟ'}
soil = {SOILMAP.get(k, k): v for k, v in d['soil'].items() if k != 'กาแฟอาราบิกา'}
d.update(products=products, shortcuts=SHORT, ag=ag, agFill=fill, basis={}, tempHII=tempHII, holders=holders, land=land, mech=mech, fert=fert,
         irr=irr, doae=doae, household=hh, cost=cost, soil=soil)
s = json.dumps(d, ensure_ascii=False, separators=(',', ':')); open('data3.json', 'w').write(s)
yrs = sorted({a[0] for a in ag})
print(f'{len(s)/1e6:.2f} MB | products {len(products)} | years {yrs[0]}-{yrs[-1]} rows {len(ag)} | fill {fill}')
print('tempHII', {k: len(v) for k, v in tempHII.items()}, '| holders', len(holders), 'land', len(land), 'mech', len(mech), 'fert', len(fert), 'irr', len(irr), 'doae', len(doae))
print('household years', list(hh), '| cost crops', len(cost['crops']), '| soil', list(soil))
nat = sum(v[0] for v in irr.values()); print('irrigation rai', f'{nat:,}', 'sample', {provs[k]: v for k, v in list(irr.items())[:3]})
print('mech sample', {provs[k]: v for k, v in list(mech.items())[:3]}, 'doae sample', {provs[k]: v for k, v in list(doae.items())[:3]})

# 8. ERA5 (Open-Meteo archive) monthly per province centroid 2550-2562 -> complete 77-province climate series
import os as _os
ep = '/mnt/user-data/uploads/Dashboard5/data/interim/era5_monthly_2550_2562.json'
if _os.path.exists(ep):
    em = json.load(open(ep)); eRain, eSeason, eT = {}, {}, {}
    for c, months in em.items():
        pi = code_idx.get(int(c))
        if pi is None: continue
        by = {}
        for k, v in months.items():
            by.setdefault(k[:4], {})[int(k[5:])] = v
        for y, mm in by.items():
            if len(mm) != 12: continue
            eRain.setdefault(y, {})[pi] = r(sum(v[0] for v in mm.values()))
            eSeason.setdefault(y, {})[pi] = r(sum(mm[m][0] for m in range(5, 11)))
            eT.setdefault(y, {})[pi] = [r(sum(v[1] for v in mm.values()) / 12, 2), r(max(v[2] for v in mm.values()), 1), r(min(v[3] for v in mm.values()), 1)]
    eM = {}
    for c, months in em.items():
        pi = code_idx.get(int(c))
        if pi is None: continue
        for k, v in months.items():
            e = eM.setdefault(pi, {}).setdefault(k[:4], [[None] * 12, [None] * 12])
            e[0][int(k[5:]) - 1] = round(v[0]); e[1][int(k[5:]) - 1] = round(v[1], 1) if v[1] is not None else None
    d.update(eraRain=eRain, eraSeason=eSeason, eraT=eT, eraM=eM)
    s = json.dumps(d, ensure_ascii=False, separators=(',', ':')); open('data3.json', 'w').write(s)
    import statistics as st
    for y in ('2561', '2562'):
        h = d['rain'].get(y, {}); common = [k for k in h if int(k) in eRain[y] or k in eRain[y]]
        xs = [h[k] for k in h if int(k) in eRain[y]]; ys = [eRain[y][int(k)] for k in h if int(k) in eRain[y]]
        n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)); r_ = cov / (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** .5
        print('ERA5 vs HII rain', y, 'n', n, 'mean HII', round(mx), 'mean ERA5', round(my), 'r', round(r_, 2))
    print('ERA5 years', sorted(eRain), {y: len(v) for y, v in eT.items()}, f'{len(s)/1e6:.2f} MB')
