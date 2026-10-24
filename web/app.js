(function () {
  const D = JSON.parse(document.getElementById('data').textContent);
  const P = D.provinces, R = D.regions, CODE = D.codes, PROD = D.products;
  const ALL = 'ทั้งหมด';
  const C = { fg: '#FFFFFF', fg2: '#B4B9DA', muted: '#7C82AD', grid: 'rgba(255,255,255,0.06)', none: '#232856',
    magenta: '#E040FB', violet: '#7C4DFF', cyan: '#00E5FF', blue: '#2979FF', sky: '#4FC3F7', ok: '#00E5A0', bad: '#FF4D6D', warn: '#FFB547' };
  const MAP_SCALE = [[0, '#2A2F6B'], [0.35, C.blue], [0.7, C.violet], [1, C.magenta]];
  const RAIN_SCALE = [[0, '#2A2F6B'], [0.5, C.blue], [1, C.cyan]];
  const DIV_SCALE = [[0, C.bad], [0.5, '#2A2F6B'], [1, C.cyan]];
  const RISK_SCALE = [[0, '#2A2F6B'], [0.5, C.warn], [1, C.bad]];
  const METRICS = {
    prod: { label: 'ปริมาณผลผลิตรวม', unit: 'ตัน', d: 0 },
    yield: { label: 'ผลผลิตต่อไร่แบบถ่วงน้ำหนัก', unit: 'กก./ไร่', d: 1 },
    plant: { label: 'เนื้อที่เพาะปลูก', unit: 'ไร่', d: 0 },
    harvest: { label: 'เนื้อที่เก็บเกี่ยว', unit: 'ไร่', d: 0 },
    ratio: { label: 'อัตราการเก็บเกี่ยว', unit: '%', d: 1 },
  };
  const BASIS = { 'planted/harvested': 'เพาะปลูก / เก็บเกี่ยว', 'standing/tapped': 'ยืนต้น / กรีดได้', 'standing/bearing': 'ยืนต้น / ให้ผล' };
  const PRICE_FOR = { 'มันสำปะหลังโรงงาน': 'มันสำปะหลังสด คละ', 'ยางพารา': 'ยางแผ่นดิบ ชั้น 3', 'ปาล์มน้ำมัน': 'ผลปาล์มน้ำมันทั้งทะลาย คละ' };
  const TREND_FROM = 2550, TREND_TO = 2562;
  const years = [...new Set(D.ag.map(r => r[0]))].sort((a, b) => a - b);
  const perYear = {}; D.ag.forEach(r => { (perYear[r[0]] = perYear[r[0]] || new Set()).add(r[1]); });
  const S = { product: -1, year: years.includes(2562) ? 2562 : years[years.length - 1], region: ALL, province: -1, metric: 'prod', tab: 'overview',
    rainView: 'total', disView: 'flood', sortKey: null, sortDir: -1 };

  // ---------- helpers ----------
  const $ = id => document.getElementById(id);
  const ok = v => v != null && isFinite(v);
  const fmt = (v, d = 0) => !ok(v) ? 'ไม่มีข้อมูล' : v.toLocaleString('th-TH', { minimumFractionDigits: d, maximumFractionDigits: d });
  const short = v => !ok(v) ? '–' : Math.abs(v) >= 1e6 ? (v / 1e6).toLocaleString('th-TH', { maximumFractionDigits: 2 }) + ' ล้าน' : fmt(v, Math.abs(v) < 100 ? 1 : 0);
  const opts = (sel, items, val) => { sel.innerHTML = items.map(([v, t]) => `<option value="${v}">${t}</option>`).join(''); sel.value = String(val); };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function rowsFor({ year = null, product = S.product, region = S.region, province = S.province } = {}) {
    return D.ag.filter(r => (year == null || r[0] === year) && (product < 0 || r[1] === product) &&
      (region === ALL || R[r[2]] === region) && (province < 0 || r[2] === province));
  }
  function totals(rows) {
    let plant = 0, harv = 0, prod = 0, np = 0, nh = 0, nq = 0;
    rows.forEach(r => { if (r[3] != null) { plant += r[3]; np++; } if (r[4] != null) { harv += r[4]; nh++; } if (r[5] != null) { prod += r[5]; nq++; } });
    plant = np ? plant : null; harv = nh ? harv : null; prod = nq ? prod : null;
    return { plant, harvest: harv, prod, yield: harv > 0 && prod != null ? prod * 1000 / harv : null, ratio: plant > 0 && harv != null ? harv / plant * 100 : null };
  }
  function byProvince(rows) {
    const g = {}; rows.forEach(r => (g[r[2]] = g[r[2]] || []).push(r));
    return Object.entries(g).map(([p, rs]) => ({ p: +p, ...totals(rs) }));
  }
  const axis = (title, extra = {}) => Object.assign({ gridcolor: C.grid, zeroline: false, linecolor: 'rgba(0,0,0,0)', tickfont: { color: C.muted }, automargin: true,
    title: title ? { text: title, font: { color: C.muted } } : undefined }, extra);
  const layout = (extra = {}) => Object.assign({
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { family: 'Sarabun, Kanit, sans-serif', color: C.fg2, size: 13 },
    margin: { l: 10, r: 14, t: 8, b: 36 }, hoverlabel: { bgcolor: C.magenta, bordercolor: C.magenta, font: { color: '#fff', family: 'Sarabun, sans-serif' } },
    xaxis: axis(), yaxis: axis(), showlegend: false,
  }, extra);
  const CFG = { displayModeBar: false, responsive: true };
  function empty(el, msg) {
    Plotly.react(el, [], layout({ xaxis: { visible: false }, yaxis: { visible: false },
      annotations: [{ text: msg, showarrow: false, x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', font: { color: C.muted, size: 14 } }] }), CFG);
  }
  function choropleth(el, values, { unit, label, scale = MAP_SCALE, highlight = -1, regionOnly = null, zmid = null, extraHover = null }) {
    const shown = P.map((_, i) => i).filter(i => !regionOnly || R[i] === regionOnly);
    const has = shown.filter(i => ok(values[i]));
    const base = { type: 'choropleth', geojson: D.geo, featureidkey: 'properties.n', marker: { line: { color: 'rgba(255,255,255,0.18)', width: 0.5 } } };
    const traces = [{ ...base, locations: P, z: P.map(() => 0), colorscale: [[0, C.none], [1, C.none]], showscale: false,
      customdata: P.map((_, i) => CODE[i]), hovertemplate: '<b>%{location}</b> (รหัส %{customdata})<br>ไม่มีข้อมูล<extra></extra>' }];
    if (has.length) traces.push({ ...base, locations: has.map(i => P[i]), z: has.map(i => values[i]), colorscale: scale,
      ...(zmid != null ? { zmid } : {}),
      customdata: has.map(i => [CODE[i], extraHover ? extraHover(i) : '']),
      colorbar: { thickness: 10, len: 0.6, x: 0.98, outlinewidth: 0, tickfont: { color: C.muted }, title: { text: unit, font: { color: C.muted } } },
      hovertemplate: '<b>%{location}</b> (รหัส %{customdata[0]})<br>' + label + ': %{z:,.1f} ' + unit + '%{customdata[1]}<extra></extra>' });
    if (highlight >= 0) traces.push({ ...base, locations: [P[highlight]], z: [1], colorscale: [[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], showscale: false,
      hoverinfo: 'skip', marker: { line: { color: '#FFFFFF', width: 2.5 } } });
    Plotly.react(el, traces, layout({ geo: { fitbounds: 'locations', visible: false, bgcolor: 'rgba(0,0,0,0)', projection: { type: 'mercator' } },
      margin: { l: 0, r: 0, t: 0, b: 0 } }), CFG);
  }
  function hbar(el, items, { unit, scale }) {
    if (!items.length) return empty(el, 'ไม่มีข้อมูล');
    const v = items.map(d => d.v);
    Plotly.react(el, [{ type: 'bar', orientation: 'h', y: items.map(d => d.name), x: v, text: v.map(short), textposition: 'outside', textfont: { color: C.fg },
      cliponaxis: false, marker: { color: v, colorscale: scale, line: { width: items.map(d => d.sel ? 2 : 0), color: '#fff' } },
      customdata: items.map(d => d.code), hovertemplate: '%{y} (รหัส %{customdata}): %{x:,.1f} ' + unit + '<extra></extra>' }],
      layout({ bargap: 0.35, margin: { l: 10, r: 56, t: 6, b: 34 }, yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2 }, gridcolor: 'rgba(0,0,0,0)' }), xaxis: axis(unit) }), CFG);
  }
  // statistics: Pearson / Spearman with exact two-sided p from Student t
  function lgamma(x) { const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    let y = x, t = x + 5.5; t -= (x + 0.5) * Math.log(t); let s = 1.000000000190015; for (const k of c) s += k / ++y; return -t + Math.log(2.5066282746310005 * s / x); }
  function betacf(a, b, x) { let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap; if (Math.abs(d) < 1e-30) d = 1e-30; d = 1 / d; let h = d;
    for (let m = 1; m <= 200; m++) { const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2)); d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2)); d = 1 + aa * d; if (Math.abs(d) < 1e-30) d = 1e-30; c = 1 + aa / c; if (Math.abs(c) < 1e-30) c = 1e-30; d = 1 / d; const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-12) break; } return h; }
  function ibeta(a, b, x) { if (x <= 0) return 0; if (x >= 1) return 1; const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b; }
  function corr(xs, ys) { const n = xs.length, mx = xs.reduce((a, b) => a + b) / n, my = ys.reduce((a, b) => a + b) / n; let sxy = 0, sxx = 0, syy = 0;
    for (let i = 0; i < n; i++) { const a = xs[i] - mx, b = ys[i] - my; sxy += a * b; sxx += a * a; syy += b * b; }
    const r = sxy / Math.sqrt(sxx * syy), df = n - 2, t = r * Math.sqrt(df / Math.max(1e-12, 1 - r * r));
    return { r, p: ibeta(df / 2, 0.5, df / (df + t * t)), slope: sxy / sxx, icept: my - sxy / sxx * mx }; }
  function ranks(a) { const idx = a.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]), out = new Array(a.length); let i = 0;
    while (i < idx.length) { let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++; const rk = (i + j) / 2 + 1; for (let k = i; k <= j; k++) out[idx[k][1]] = rk; i = j + 1; } return out; }
  function stats(xs, ys) { if (xs.length < 5) return null; const p = corr(xs, ys), s = corr(ranks(xs), ranks(ys)); return { n: xs.length, r: p.r, pr: p.p, rho: s.r, ps: s.p, slope: p.slope, icept: p.icept }; }

  // ---------- downloads capability (CSV) ----------
  let downloads = null;
  try { window.claude && window.claude.use && window.claude.use('downloads').then(d => { downloads = d; $('t-csv').hidden = !d; }).catch(() => {}); } catch (e) { /* no runtime */ }

  // ---------- global filters ----------
  opts($('f-product'), [[-1, ALL + ' (' + PROD.length + ' ชนิด)'], ...PROD.map((p, i) => [i, p])], S.product);
  opts($('f-year'), [...years].reverse().map(y => [y, y + (perYear[y].size < PROD.length ? ' (ข้อมูลบางพืช)' : '')]), S.year);
  opts($('f-region'), [[ALL, ALL], ...D.regionNames.map(r => [r, r])], S.region);
  opts($('f-metric'), Object.entries(METRICS).map(([k, m]) => [k, `${m.label} (${m.unit})`]), S.metric);
  function provinceOptions() {
    const list = P.map((p, i) => [i, p]).filter(([i]) => S.region === ALL || R[i] === S.region).sort((a, b) => a[1].localeCompare(b[1], 'th'));
    if (S.province >= 0 && S.region !== ALL && R[S.province] !== S.region) S.province = -1;
    opts($('f-province'), [[-1, ALL], ...list.map(([i, p]) => [i, `${p} (${CODE[i]})`])], S.province);
  }
  provinceOptions();
  $('f-product').onchange = e => { S.product = +e.target.value; syncCrops(); render(); };
  $('f-year').onchange = e => { S.year = +e.target.value; render(); };
  $('f-region').onchange = e => { S.region = e.target.value; provinceOptions(); render(); };
  $('f-province').onchange = e => { S.province = +e.target.value; render(); };
  $('f-metric').onchange = e => { S.metric = e.target.value; render(); };
  $('coverage').textContent = `${PROD.length} พืช · ${new Set(D.ag.map(r => r[2])).size} จังหวัด · พ.ศ. ${years[0]}–${years[years.length - 1]}`;
  const defaultCrop = () => S.product >= 0 ? S.product : Math.max(0, PROD.indexOf('มันสำปะหลังโรงงาน'));
  function syncCrops() { ['c-crop', 'k-crop'].forEach(id => { $(id).value = String(defaultCrop()); }); kTouched = {}; }

  // ---------- tabs ----------
  const TABS = ['overview', 'climate', 'factors', 'economics'];
  function setTab(t) {
    S.tab = TABS.includes(t) ? t : 'overview';
    TABS.forEach(k => { $('p-' + k).hidden = k !== S.tab; $('t-' + k).setAttribute('aria-selected', String(k === S.tab)); });
    try { history.replaceState(null, '', '#' + S.tab); } catch (e) { /* ignore */ }
    render();
  }
  document.querySelectorAll('.tab').forEach(b => b.onclick = () => setTab(b.dataset.tab));
  function seg(ids, key, val) { ids.forEach(([id, v]) => { $(id).onclick = () => { S[key] = v; ids.forEach(([i2, v2]) => $(i2).setAttribute('aria-pressed', String(v2 === v))); render(); }; }); }
  seg([['rv-total', 'total'], ['rv-anom', 'anom']], 'rainView');
  seg([['dv-flood', 'flood'], ['dv-drought', 'drought']], 'disView');

  // =================== TAB 1 ===================
  let tableRows = [];
  function renderOverview() {
    const m = METRICS[S.metric], cur = totals(rowsFor({ year: S.year })), prev = totals(rowsFor({ year: S.year - 1 }));
    const kpi = (cls, label, key, unit, d) => {
      const v = cur[key], pv = prev[key], has = ok(v) && ok(pv) && pv > 0, diff = has ? v - pv : null, pct = has ? diff / pv * 100 : null;
      return `<div class="kpi ${cls}"><div class="l">${label}</div><div class="v">${fmt(v, d)}${ok(v) ? `<small>${unit}</small>` : ''}</div>
        <span class="d ${has ? (diff >= 0 ? 'up' : 'dn') : ''}">${has ? `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}% YoY` : 'ไม่มีข้อมูลปี ' + (S.year - 1)}</span>
        <span class="d2">${has ? `${diff >= 0 ? '+' : ''}${fmt(diff, d)} ${unit} จาก พ.ศ. ${S.year - 1}` : '&nbsp;'}</span></div>`;
    };
    $('kpis').innerHTML = kpi('m', 'เนื้อที่เพาะปลูก', 'plant', 'ไร่', 0) + kpi('c', 'เนื้อที่เก็บเกี่ยว', 'harvest', 'ไร่', 0) +
      kpi('m', 'ปริมาณผลผลิตรวม', 'prod', 'ตัน', 0) + kpi('c', 'ผลผลิตต่อไร่แบบถ่วงน้ำหนัก', 'yield', 'กก./ไร่', 1);

    const provs = byProvince(rowsFor({ year: S.year, province: -1 })), vals = {}; provs.forEach(d => vals[d.p] = d[S.metric]);
    const cropLabel = S.product < 0 ? 'ทุกพืชรวมกัน' : PROD[S.product];
    $('map1-title').textContent = `${m.label} พ.ศ. ${S.year}`;
    $('map1-sub').textContent = `${cropLabel} · วางเมาส์เพื่อดูรหัสจังหวัดและค่า · สีเข้มสุด = ไม่มีข้อมูล`;
    const pv = {}; provs.forEach(d => pv[d.p] = d);
    choropleth($('map1'), vals, { unit: m.unit, label: m.label, highlight: S.province, regionOnly: S.region === ALL ? null : S.region,
      extraHover: i => pv[i] ? `<br>ผลผลิต ${short(pv[i].prod)} ตัน · ${fmt(pv[i].yield, 0)} กก./ไร่` : '' });

    const series = years.filter(y => y >= TREND_FROM && y <= TREND_TO).map(y => ({ y, ...totals(rowsFor({ year: y })) })).filter(d => ok(d[S.metric]));
    $('trend-title').textContent = `แนวโน้ม${m.label} พ.ศ. ${TREND_FROM}–${TREND_TO}`;
    $('trend-sub').textContent = (S.province >= 0 ? P[S.province] : S.region === ALL ? 'ทั้งประเทศ' : S.region) + ' · ' + cropLabel +
      (S.year < TREND_FROM || S.year > TREND_TO ? ` · ปี ${S.year} อยู่นอกช่วงกราฟ` : '');
    if (!series.length) empty($('trend'), 'ไม่มีข้อมูลในช่วง พ.ศ. 2550–2562'); else {
      const x = series.map(d => d.y), y = series.map(d => d[S.metric]), i = x.indexOf(S.year);
      Plotly.react($('trend'), [
        { x, y, mode: 'lines', line: { shape: 'spline', color: C.cyan, width: 10 }, opacity: 0.15, hoverinfo: 'skip' },
        { x, y, mode: 'lines+markers', line: { shape: 'spline', color: C.cyan, width: 3 }, marker: { size: 5, color: C.cyan }, fill: 'tozeroy', fillcolor: 'rgba(0,229,255,0.07)',
          hovertemplate: 'พ.ศ. %{x}: %{y:,.1f} ' + m.unit + '<extra></extra>' },
        ...(i >= 0 ? [{ x: [x[i]], y: [y[i]], mode: 'markers', marker: { size: 12, color: C.magenta, line: { color: '#fff', width: 2 } }, hoverinfo: 'skip' }] : []),
      ], layout({ xaxis: axis('ปี พ.ศ.', { dtick: 2 }), yaxis: axis(m.unit) }), CFG);
    }

    const inScope = provs.filter(d => (S.region === ALL || R[d.p] === S.region) && ok(d[S.metric]));
    const sorted = [...inScope].sort((a, b) => b[S.metric] - a[S.metric]);
    $('top-sub').textContent = `${cropLabel} · พ.ศ. ${S.year} · ${m.label}`;
    const item = d => ({ name: P[d.p], code: CODE[d.p], v: d[S.metric], sel: d.p === S.province });
    hbar($('top10'), sorted.slice(0, 10).map(item), { unit: m.unit, scale: [[0, C.blue], [1, C.cyan]] });
    hbar($('bot10'), sorted.filter(d => d[S.metric] > 0).slice(-10).reverse().map(item), { unit: m.unit, scale: [[0, C.violet], [1, C.magenta]] });

    // scale vs efficiency
    const sc = inScope.filter(d => ok(d.plant) && ok(d.yield) && d.plant > 0);
    $('scale-sub').textContent = `แต่ละจุด = 1 จังหวัด · ${cropLabel} · พ.ศ. ${S.year}`;
    if (sc.length < 3) { empty($('scale'), 'ข้อมูลไม่พอ'); $('scale-insight').innerHTML = '<b>ข้อสังเกต:</b> ข้อมูลไม่พอสำหรับเปรียบเทียบ'; }
    else {
      const medA = [...sc].map(d => d.plant).sort((a, b) => a - b)[Math.floor(sc.length / 2)], medY = [...sc].map(d => d.yield).sort((a, b) => a - b)[Math.floor(sc.length / 2)];
      Plotly.react($('scale'), [{ x: sc.map(d => d.plant), y: sc.map(d => d.yield), text: sc.map(d => P[d.p]), mode: 'markers',
        marker: { size: sc.map(d => 8 + 18 * Math.sqrt((d.prod || 0) / Math.max(...sc.map(z => z.prod || 0)))), color: sc.map(d => d.yield >= medY ? C.cyan : C.magenta), opacity: 0.8, line: { color: '#fff', width: 0.5 } },
        hovertemplate: '<b>%{text}</b><br>เนื้อที่ %{x:,.0f} ไร่<br>%{y:,.0f} กก./ไร่<extra></extra>' }],
        layout({ xaxis: axis('เนื้อที่เพาะปลูก (ไร่, log)', { type: 'log' }), yaxis: axis('กก./ไร่'),
          shapes: [{ type: 'line', xref: 'x', yref: 'paper', x0: medA, x1: medA, y0: 0, y1: 1, line: { dash: 'dash', color: 'rgba(255,255,255,0.25)' } },
                   { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: medY, y1: medY, line: { dash: 'dash', color: 'rgba(255,255,255,0.25)' } }] }), CFG);
      const byProd = [...sc].sort((a, b) => b.prod - a.prod), byYield = [...sc].sort((a, b) => b.yield - a.yield);
      const yRank = byYield.indexOf(byProd[0]) + 1, aRank = [...sc].sort((a, b) => b.plant - a.plant).indexOf(byYield[0]) + 1;
      const st = stats(sc.map(d => Math.log(d.plant)), sc.map(d => d.yield));
      $('scale-insight').innerHTML = `<b>ข้อสังเกต:</b> ${P[byProd[0].p]} ผลิตได้มากที่สุด (${short(byProd[0].prod)} ตัน) แต่ผลผลิตต่อไร่อยู่อันดับ ${yRank} จาก ${sc.length} จังหวัด
        ขณะที่ ${P[byYield[0].p]} มีผลผลิตต่อไร่สูงสุด (${fmt(byYield[0].yield, 0)} กก./ไร่) โดยมีเนื้อที่เพาะปลูกอันดับ ${aRank}.
        ${st ? `ความสัมพันธ์ระหว่างขนาดพื้นที่กับผลผลิตต่อไร่ ρ = ${st.rho.toFixed(2)} (p = ${st.ps < 0.001 ? '< 0.001' : st.ps.toFixed(3)}) แปลว่าพื้นที่ใหญ่${Math.abs(st.rho) < 0.2 ? 'แทบไม่ได้บอก' : st.rho > 0 ? 'มักมาพร้อม' : 'มักสวนทางกับ'}ประสิทธิภาพต่อไร่` : ''}
        ${S.product < 0 ? '<br>ตอนนี้รวมทุกพืช ควรเลือกพืชเดียวเพื่อเทียบผลผลิตต่อไร่ให้ถูกต้อง' : ''}`;
    }
    const basisList = (S.product < 0 ? PROD : [PROD[S.product]]).map(p => `${p}: ${BASIS[D.basis[p]] || D.basis[p]}`);
    $('basis-note').innerHTML = `<b>นิยามเนื้อที่ของ สศก.:</b> ${basisList.join(' · ')}. ข้อมูลความเสียหายในตารางมาจาก ปภ. ซึ่งมีเฉพาะปี 2562 และเป็นพื้นที่เกษตรที่น้ำท่วมรวมทุกพืช`;

    // detailed table: one row per province x crop
    tableRows = D.ag.filter(r => r[0] === S.year && (S.product < 0 || r[1] === S.product) && (S.region === ALL || R[r[2]] === S.region))
      .map(r => { const t = totals([r]), fl = S.year === 2562 && D.flood2562[r[2]] ? D.flood2562[r[2]].slice(0, 3).reduce((a, b) => a + (b || 0), 0) : null;
        return { region: R[r[2]], province: P[r[2]], code: CODE[r[2]], crop: PROD[r[1]], year: r[0], plant: t.plant, harvest: t.harvest, prod: t.prod, yield: t.yield, ratio: t.ratio, flood: fl, p: r[2] }; });
    drawTable();
  }
  const COLS = [['region', 'ภาค'], ['province', 'จังหวัด'], ['code', 'รหัส'], ['crop', 'ชนิดพืช'], ['year', 'ปี พ.ศ.'], ['plant', 'เนื้อที่เพาะปลูก (ไร่)', 0], ['harvest', 'เนื้อที่เก็บเกี่ยว (ไร่)', 0],
    ['prod', 'ผลผลิต (ตัน)', 0], ['yield', 'ผลผลิตต่อไร่ (กก.)', 1], ['ratio', 'อัตราเก็บเกี่ยว (%)', 1], ['flood', 'พื้นที่เกษตรน้ำท่วม ปภ. (ไร่)', 0]];
  function visibleRows() {
    const q = $('t-search').value.trim().toLowerCase();
    let rows = q ? tableRows.filter(r => [r.region, r.province, r.crop, r.code].join(' ').toLowerCase().includes(q)) : [...tableRows];
    const key = S.sortKey || ({ prod: 'prod', yield: 'yield', plant: 'plant', harvest: 'harvest', ratio: 'ratio' }[S.metric]);
    rows.sort((a, b) => { const x = a[key], y = b[key]; if (!ok(x) && typeof x !== 'string') return 1; if (!ok(y) && typeof y !== 'string') return -1;
      return (typeof x === 'string' ? x.localeCompare(y, 'th') : x - y) * S.sortDir; });
    return { rows, key };
  }
  function drawTable() {
    const { rows, key } = visibleRows();
    $('table-sub').textContent = `${rows.length} แถว (จังหวัด × ชนิดพืช) · พ.ศ. ${S.year} · คลิกหัวคอลัมน์เพื่อเรียงลำดับ`;
    $('table').innerHTML = '<thead><tr>' + COLS.map(([k, t]) => `<th class="sort" data-k="${k}" aria-sort="${k === key ? (S.sortDir > 0 ? 'ascending' : 'descending') : 'none'}">${t}</th>`).join('') + '</tr></thead><tbody>' +
      rows.map(r => `<tr class="${r.p === S.province ? 'sel' : ''}">` + COLS.map(([k, , d]) => `<td>${d == null ? esc(r[k]) : (ok(r[k]) ? fmt(r[k], d) : '–')}</td>`).join('') + '</tr>').join('') + '</tbody>';
    document.querySelectorAll('#table th.sort').forEach(th => th.onclick = () => { const k = th.dataset.k; S.sortDir = (S.sortKey === k) ? -S.sortDir : -1; S.sortKey = k; drawTable(); });
  }
  $('t-search').oninput = () => drawTable();
  $('t-csv').onclick = async () => {
    if (!downloads) return;
    const { rows } = visibleRows();
    const q = v => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const csv = '﻿' + [COLS.map(c => c[1]).join(','), ...rows.map(r => COLS.map(([k, , d]) => q(d == null ? r[k] : (ok(r[k]) ? +r[k].toFixed(d) : ''))).join(','))].join('\r\n');
    try { await downloads.save({ filename: `thai_agri_${S.year}${S.product >= 0 ? '_' + PROD[S.product] : ''}.csv`, data: csv }); } catch (e) { /* viewer declined or unavailable */ }
  };

  // =================== TAB 2 ===================
  const rainYears = Object.keys(D.rain).map(Number).filter(y => years.includes(y)).sort();
  opts($('c-year'), rainYears.map(y => [y, y]), rainYears.includes(S.year) ? S.year : (rainYears.includes(2562) ? 2562 : rainYears[0]));
  opts($('c-crop'), PROD.map((p, i) => [i, p]), defaultCrop());
  const XVARS = { rain: ['ฝนสะสมทั้งปี (สสน.)', 'มม.'], season: ['ฝนฤดูเพาะปลูก พ.ค.–ต.ค. (สสน.)', 'มม.'], temp: ['อุณหภูมิเฉลี่ยทั้งปี (ERA5)', '°C'] };
  opts($('c-x'), Object.entries(XVARS).filter(([k]) => k !== 'temp' || Object.keys(D.temp).length).map(([k, v]) => [k, v[0]]), 'rain');
  ['c-year', 'c-crop', 'c-x'].forEach(id => $(id).onchange = () => render());
  function renderClimate() {
    const y = +$('c-year').value, crop = +$('c-crop').value, rain = D.rain[y] || {};
    const rv = Object.entries(rain).filter(([, v]) => ok(v));
    const avg = rv.reduce((a, [, v]) => a + v, 0) / rv.length, normAvg = Object.values(D.provNormal).reduce((a, b) => a + b, 0) / Object.keys(D.provNormal).length;
    const wet = [...rv].sort((a, b) => b[1] - a[1]), nat = D.national[y];
    $('c-kpis').innerHTML = `<div class="kpi m"><div class="l">ฝนเฉลี่ย 77 จังหวัด พ.ศ. ${y}</div><div class="v">${fmt(avg)}<small>มม.</small></div><span class="d ${avg >= normAvg ? 'up' : 'dn'}">${((avg / normAvg - 1) * 100).toFixed(1)}% เทียบค่าปกติ 30 ปี</span></div>
      <div class="kpi c"><div class="l">ฝนเชิงพื้นที่ทั้งประเทศ (สสน.)</div><div class="v">${fmt(nat)}<small>มม.</small></div><span class="d">ค่าปกติ 2534–2563: ${fmt(D.nationalNormal)} มม.</span></div>
      <div class="kpi p"><div class="l">ฝนมากที่สุด</div><div class="v">${fmt(wet[0][1])}<small>มม. · ${P[wet[0][0]]}</small></div></div>
      <div class="kpi p"><div class="l">ฝนน้อยที่สุด</div><div class="v">${fmt(wet[wet.length - 1][1])}<small>มม. · ${P[wet[wet.length - 1][0]]}</small></div></div>`;
    const vals = {}; rv.forEach(([i, v]) => { vals[i] = S.rainView === 'total' ? v : (D.provNormal[i] ? (v / D.provNormal[i] - 1) * 100 : null); });
    $('rainmap-title').textContent = `ฝนเชิงพื้นที่ 77 จังหวัด พ.ศ. ${y}`;
    choropleth($('rainmap'), vals, S.rainView === 'total' ? { unit: 'มม.', label: 'ฝนสะสม', scale: RAIN_SCALE, highlight: S.province, extraHover: i => D.provNormal[i] ? `<br>ค่าปกติ 30 ปี ${fmt(D.provNormal[i])} มม.` : '' }
      : { unit: '%', label: 'ต่างจากค่าปกติ', scale: DIV_SCALE, zmid: 0, highlight: S.province, extraHover: i => `<br>ฝนจริง ${fmt(rain[i])} มม.` });

    // national long-term
    const ny = Object.keys(D.national).map(Number).filter(v => v >= TREND_FROM && v <= TREND_TO).sort();
    $('nat-sub').textContent = `สสน. ฝนเชิงพื้นที่ทั้งประเทศรายเดือน รวมเป็นรายปี · เส้นประ = ค่าเฉลี่ย พ.ศ. 2534–2563 (${fmt(D.nationalNormal)} มม.)`;
    Plotly.react($('national'), [
      { type: 'bar', x: ny, y: ny.map(v => D.national[v]), marker: { color: ny.map(v => D.national[v] >= D.nationalNormal ? C.cyan : C.violet) }, hovertemplate: 'พ.ศ. %{x}: %{y:,.0f} มม.<extra></extra>' },
      { x: [ny[0] - 0.5, ny[ny.length - 1] + 0.5], y: [D.nationalNormal, D.nationalNormal], mode: 'lines', line: { color: '#fff', dash: 'dash', width: 2 }, hoverinfo: 'skip' },
    ], layout({ bargap: 0.35, xaxis: axis('ปี พ.ศ.', { dtick: 2 }), yaxis: axis('มม.', { rangemode: 'tozero' }) }), CFG);

    // scatter
    const xk = $('c-x').value, src = xk === 'rain' ? rain : xk === 'season' ? (D.season[y] || {}) : (D.temp[y] || {});
    const pts = byProvince(rowsFor({ year: y, product: crop, region: ALL, province: -1 })).filter(d => ok(d.yield) && ok(src[d.p]));
    const [xl, xu] = XVARS[xk];
    $('scatter-title').textContent = `${xl} vs ผลผลิตต่อไร่: ${PROD[crop]}`;
    const st = stats(pts.map(d => src[d.p]), pts.map(d => d.yield));
    if (!st) { empty($('scatter'), xk === 'temp' && !Object.keys(D.temp).length ? 'ยังไม่มีข้อมูลอุณหภูมิ' : 'จังหวัดที่มีข้อมูลทั้งสองด้านไม่ถึง 5 จังหวัด'); $('stats').innerHTML = ''; $('scatter-sub').textContent = ''; }
    else {
      const xs = pts.map(d => src[d.p]), x0 = Math.min(...xs), x1 = Math.max(...xs);
      Plotly.react($('scatter'), [
        { x: xs, y: pts.map(d => d.yield), text: pts.map(d => `${P[d.p]} (${CODE[d.p]})`), mode: 'markers', marker: { size: 10, color: C.cyan, opacity: 0.85, line: { color: '#fff', width: 0.5 } },
          hovertemplate: '<b>%{text}</b><br>' + xl + ': %{x:,.1f} ' + xu + '<br>%{y:,.0f} กก./ไร่<extra></extra>' },
        { x: [x0, x1], y: [st.slope * x0 + st.icept, st.slope * x1 + st.icept], mode: 'lines', line: { color: C.magenta, width: 2.5, dash: 'dash' }, hoverinfo: 'skip' },
      ], layout({ xaxis: axis(`${xl} (${xu})`), yaxis: axis('กก./ไร่') }), CFG);
      const pf = p => p < 0.001 ? '< 0.001' : p.toFixed(3);
      $('scatter-sub').textContent = `เส้นประ = OLS trendline (ความชัน ${st.slope.toFixed(2)} กก./ไร่ ต่อ 1 ${xu}) · พ.ศ. ${y}`;
      $('stats').innerHTML = `<div><span>Pearson r</span><b>${st.r.toFixed(3)}</b></div><div><span>p-value (r)</span><b>${pf(st.pr)}</b></div>
        <div><span>Spearman ρ</span><b>${st.rho.toFixed(3)}</b></div><div><span>p-value (ρ)</span><b>${pf(st.ps)}</b></div><div><span>N (จังหวัด)</span><b>${st.n}</b></div>
        <div><span>สรุป</span><b style="font-size:14px">${st.pr < 0.05 ? 'มีนัยสำคัญ' : 'ไม่มีนัยสำคัญ'}</b></div>`;
    }
    // season chart
    const s = D.season[y] || {};
    const items = Object.keys(s).map(i => ({ p: +i, s: s[i], o: (rain[i] || 0) - s[i] })).sort((a, b) => b.s - a.s).slice(0, 20);
    if (!items.length) return empty($('season'), 'ไม่มีข้อมูลฝนรายเดือน');
    Plotly.react($('season'), [
      { type: 'bar', orientation: 'h', y: items.map(d => P[d.p]), x: items.map(d => d.s), name: 'ฤดูเพาะปลูก พ.ค.–ต.ค.', marker: { color: C.cyan }, hovertemplate: '%{y}: %{x:,.0f} มม. (พ.ค.–ต.ค.)<extra></extra>' },
      { type: 'bar', orientation: 'h', y: items.map(d => P[d.p]), x: items.map(d => d.o), name: 'นอกฤดู', marker: { color: C.violet }, hovertemplate: '%{y}: %{x:,.0f} มม. (นอกฤดู)<extra></extra>' },
    ], layout({ barmode: 'stack', bargap: 0.3, showlegend: true, legend: { orientation: 'h', y: 1.07, font: { color: C.fg2 } }, margin: { l: 10, r: 10, t: 30, b: 34 },
      yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2 }, gridcolor: 'rgba(0,0,0,0)' }), xaxis: axis('มม.') }), CFG);
  }

  // =================== TAB 3 ===================
  const soilCrops = Object.keys(D.soil).sort((a, b) => a.localeCompare(b, 'th'));
  opts($('s-crop'), soilCrops.map(c => [c, c]), soilCrops.includes('มันสำปะหลังโรงงาน') ? 'มันสำปะหลังโรงงาน' : soilCrops[0]);
  $('s-crop').onchange = () => render();
  function renderFactors() {
    const crop = $('s-crop').value, s = D.soil[crop] || {}, pct = {}, rows = [];
    Object.entries(s).forEach(([i, a]) => { const tot = a.reduce((x, y) => x + (y || 0), 0); if (tot > 0) { pct[i] = ((a[0] || 0) + (a[1] || 0)) / tot * 100; rows.push({ p: +i, a, tot }); } });
    $('soilmap-title').textContent = `ความเหมาะสมของดิน Agri-Map: ${crop}`;
    choropleth($('soilmap'), pct, { unit: '%', label: 'S1+S2', highlight: S.province, extraHover: i => s[i] ? `<br>S1 ${short(s[i][0])} · S2 ${short(s[i][1])} · S3 ${short(s[i][2])} · N ${short(s[i][3])} ไร่` : '' });
    const top = rows.sort((a, b) => b.tot - a.tot).slice(0, 15);
    const cls = [['S1 เหมาะสมสูง', C.cyan], ['S2 ปานกลาง', C.blue], ['S3 เล็กน้อย', C.violet], ['N ไม่เหมาะสม', C.magenta]];
    Plotly.react($('soilbar'), cls.map(([n, col], k) => ({ type: 'bar', orientation: 'h', name: n, y: top.map(d => P[d.p]), x: top.map(d => (d.a[k] || 0) / d.tot * 100),
      customdata: top.map(d => d.a[k] || 0), marker: { color: col }, hovertemplate: '%{y}: %{x:.1f}% (%{customdata:,.0f} ไร่)<extra>' + n + '</extra>' })),
      layout({ barmode: 'stack', bargap: 0.3, showlegend: true, legend: { orientation: 'h', y: 1.06, font: { color: C.fg2 } }, margin: { l: 10, r: 10, t: 34, b: 34 },
        yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2 }, gridcolor: 'rgba(0,0,0,0)' }), xaxis: axis('% ของพื้นที่ประเมิน', { range: [0, 100] }) }), CFG);

    // disasters 2562
    if (S.disView === 'flood') {
      const v = {}; Object.entries(D.flood2562).forEach(([i, a]) => { const t = (a[0] || 0) + (a[1] || 0) + (a[2] || 0); if (t > 0) v[i] = t; });
      const total = Object.values(v).reduce((a, b) => a + b, 0);
      $('dis-sub').textContent = `ปภ. สถิติอุทกภัย พ.ศ. 2562 · นาข้าว + พืชสวน + พืชไร่ที่เสียหาย · รวม ${fmt(total)} ไร่ ใน ${Object.keys(v).length} จังหวัด`;
      choropleth($('dismap'), v, { unit: 'ไร่', label: 'พื้นที่เกษตรเสียหาย', scale: RISK_SCALE, highlight: S.province,
        extraHover: i => `<br>นาข้าว ${fmt(D.flood2562[i][0])} · พืชสวน ${fmt(D.flood2562[i][1])} · พืชไร่ ${fmt(D.flood2562[i][2])} ไร่<br>มูลค่าความเสียหายภาคเกษตร ${fmt(D.flood2562[i][3])} บาท` });
      const top = Object.keys(v).map(Number).sort((a, b) => v[b] - v[a]).slice(0, 10);
      $('disbar-title').textContent = '10 จังหวัดพื้นที่เกษตรน้ำท่วมมากที่สุด พ.ศ. 2562'; $('disbar-sub').textContent = 'แยกตามประเภทพื้นที่ (ไร่)';
      Plotly.react($('disbar'), [['นาข้าว', 0, C.cyan], ['พืชสวน', 1, C.violet], ['พืชไร่', 2, C.magenta]].map(([n, k, col]) => ({ type: 'bar', orientation: 'h', name: n,
        y: top.map(i => P[i]), x: top.map(i => D.flood2562[i][k] || 0), marker: { color: col }, hovertemplate: '%{y}: %{x:,.0f} ไร่<extra>' + n + '</extra>' })),
        layout({ barmode: 'stack', bargap: 0.3, showlegend: true, legend: { orientation: 'h', y: 1.07, font: { color: C.fg2 } }, margin: { l: 10, r: 10, t: 30, b: 34 },
          yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2 }, gridcolor: 'rgba(0,0,0,0)' }), xaxis: axis('ไร่') }), CFG);
    } else {
      const v = {}; Object.entries(D.drought2562).forEach(([i, n]) => v[i] = n);
      $('dis-sub').textContent = `ปภ. สถิติภัยแล้ง พ.ศ. 2562 · หมู่บ้านที่ประกาศเขตการให้ความช่วยเหลือ · รวม ${fmt(Object.values(v).reduce((a, b) => a + b, 0))} หมู่บ้าน ใน ${Object.keys(v).length} จังหวัด`;
      choropleth($('dismap'), v, { unit: 'หมู่บ้าน', label: 'หมู่บ้านที่ประกาศภัยแล้ง', scale: RISK_SCALE, highlight: S.province });
      const top = Object.keys(v).map(Number).sort((a, b) => v[b] - v[a]).slice(0, 10);
      $('disbar-title').textContent = '10 จังหวัดที่ประกาศภัยแล้งมากที่สุด พ.ศ. 2562'; $('disbar-sub').textContent = 'จำนวนหมู่บ้าน';
      hbar($('disbar'), top.map(i => ({ name: P[i], code: CODE[i], v: v[i], sel: i === S.province })), { unit: 'หมู่บ้าน', scale: [[0, C.warn], [1, C.bad]] });
    }
  }

  // =================== TAB 4 ===================
  const priceNames = Object.keys(D.prices);
  opts($('m-product'), priceNames.map(p => [p, p]), priceNames[0]);
  opts($('m-range'), [['2561-2562', 'พ.ศ. 2561–2562'], ['52', '52 สัปดาห์ล่าสุด'], ['all', 'ทั้งหมด'], ...[...new Set(Object.values(D.prices).flat().map(r => r[0]))].sort().reverse().map(y => [y, 'พ.ศ. ' + y])], '2561-2562');
  ['m-product', 'm-range'].forEach(id => $(id).onchange = () => render());
  function priceRows(name, rng) {
    const all = D.prices[name] || [];
    return rng === '52' ? all.slice(-52) : rng === 'all' ? all : rng === '2561-2562' ? all.filter(r => r[0] === 2561 || r[0] === 2562) : all.filter(r => r[0] === +rng);
  }
  function renderEconomics() {
    const name = $('m-product').value, rng = $('m-range').value, rows = priceRows(name, rng);
    const total2 = Object.values(D.prices).flat().filter(r => r[0] === 2561 || r[0] === 2562).length;
    $('price-title').textContent = `แนวโน้มราคารายสัปดาห์: ${name}`;
    if (!rows.length) { $('m-kpis').innerHTML = `<div class="kpi p"><div class="l">ไม่มีข้อมูลในช่วงที่เลือก</div><div class="v">–</div><span class="d">ชุดนี้มีข้อมูล พ.ศ. ${D.prices[name][0][0]}–${D.prices[name][D.prices[name].length - 1][0]}</span></div>`; empty($('price'), 'ไม่มีข้อมูลราคาในช่วงที่เลือก'); }
    else {
      const v = rows.map(r => r[3]), mean = v.reduce((a, b) => a + b) / v.length, last = v[v.length - 1], prev = v.length > 1 ? v[v.length - 2] : null;
      const lab = r => `${r[0]}-${String(r[1]).padStart(2, '0')} ส.${r[2]}`, wow = prev ? (last - prev) / prev * 100 : null;
      $('m-kpis').innerHTML = `<div class="kpi m"><div class="l">ราคาเฉลี่ยช่วงที่เลือก</div><div class="v">${fmt(mean, 2)}<small>บาท/กก.</small></div><span class="d">${rows.length} สัปดาห์ · ทุกสินค้ารวม ${fmt(total2)} รายการในปี 2561–2562</span></div>
        <div class="kpi c"><div class="l">ราคาล่าสุดของช่วง (${lab(rows[rows.length - 1])})</div><div class="v">${fmt(last, 2)}<small>บาท/กก.</small></div><span class="d ${wow == null ? '' : wow >= 0 ? 'up' : 'dn'}">${wow == null ? '–' : (wow >= 0 ? '+' : '') + wow.toFixed(1) + '% จากสัปดาห์ก่อน'}</span></div>
        <div class="kpi p"><div class="l">สูงสุด</div><div class="v">${fmt(Math.max(...v), 2)}<small>บาท/กก.</small></div><span class="d">${lab(rows[v.indexOf(Math.max(...v))])}</span></div>
        <div class="kpi p"><div class="l">ต่ำสุด</div><div class="v">${fmt(Math.min(...v), 2)}<small>บาท/กก.</small></div><span class="d">${lab(rows[v.indexOf(Math.min(...v))])}</span></div>`;
      const x = rows.map(lab), ma = v.map((_, i) => i >= 7 ? v.slice(i - 7, i + 1).reduce((a, b) => a + b) / 8 : null);
      Plotly.react($('price'), [
        { x, y: v, mode: 'lines', line: { shape: 'spline', color: C.cyan, width: 10 }, opacity: 0.15, hoverinfo: 'skip' },
        { x, y: v, mode: 'lines', line: { shape: 'spline', color: C.cyan, width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(0,229,255,0.06)', hovertemplate: '%{x}: %{y:,.2f} บาท/กก.<extra></extra>' },
        { x, y: ma, mode: 'lines', line: { shape: 'spline', color: '#FFFFFF', width: 2, dash: 'dash' }, hovertemplate: 'เฉลี่ย 8 สัปดาห์: %{y:,.2f}<extra></extra>' },
      ], layout({ xaxis: axis(null, { nticks: 10 }), yaxis: axis('บาท/กก.', { rangemode: 'tozero' }) }), CFG);
    }
    calcRefs(); calc();
  }
  opts($('k-crop'), PROD.map((p, i) => [i, p]), defaultCrop());
  let kTouched = {};
  ['k-area', 'k-yield', 'k-cost', 'k-price'].forEach(id => $(id).oninput = () => { kTouched[id] = true; calc(); });
  $('k-crop').onchange = () => { kTouched = {}; calcRefs(); calc(); };
  let REF = {};
  function calcRefs() {
    const k = +$('k-crop').value, crop = PROD[k], nat = totals(rowsFor({ year: S.year, product: k, region: ALL, province: -1 }));
    const pname = PRICE_FOR[crop], pr = pname ? (D.prices[pname] || []) : [];
    const sameYear = pr.filter(r => r[0] === S.year), use = sameYear.length ? sameYear : pr.slice(-52);
    const price = use.length ? use.reduce((a, r) => a + r[3], 0) / use.length : null;
    REF = { yield: nat.yield, price, pname, priceNote: !pname ? 'ไม่มีราคาของพืชนี้ใน API' : sameYear.length ? `เฉลี่ย พ.ศ. ${S.year} (${sameYear.length} สัปดาห์)` : 'ไม่มีราคาปีที่เลือก ใช้ 52 สัปดาห์ล่าสุด' };
    $('k-ref').innerHTML = `<div><span>ผลผลิตต่อไร่ถ่วงน้ำหนักทั้งประเทศ พ.ศ. ${S.year}</span><b>${fmt(nat.yield, 0)} กก./ไร่</b></div>
      <div><span>ราคาที่เกษตรกรขายได้${pname ? ` (${pname})` : ''}<br><span class="muted">${REF.priceNote}</span></span><b>${ok(price) ? fmt(price, 2) + ' บาท/กก.' : 'ไม่มีข้อมูล'}</b></div>
      <div><span>ต้นทุนการผลิตต่อไร่ (สศก.)</span><b><span class="chip">ไม่มีข้อมูลเปิด</span></b></div>`;
    if (!kTouched['k-yield'] && ok(nat.yield)) $('k-yield').value = Math.round(nat.yield);
    if (!kTouched['k-price'] && ok(price)) $('k-price').value = price.toFixed(2);
  }
  $('k-use').onclick = () => { if (ok(REF.yield)) $('k-yield').value = Math.round(REF.yield); if (ok(REF.price)) $('k-price').value = REF.price.toFixed(2); calc(); };
  function calc() {
    const num = id => $(id).value === '' ? null : +$(id).value;
    const a = num('k-area'), yl = num('k-yield'), c = num('k-cost'), p = num('k-price');
    const cost = ok(a) && ok(c) ? a * c : null, out = ok(a) && ok(yl) ? a * yl : null, rev = ok(out) && ok(p) ? out * p : null, profit = ok(rev) && ok(cost) ? rev - cost : null;
    const beY = ok(cost) && ok(a) && p ? cost / (a * p) : null, beP = ok(cost) && out ? cost / out : null;
    const box = (l, v, u, cls = '') => `<div><span>${l}</span><b class="${cls}">${ok(v) ? fmt(v, u === 'บาท/กก.' ? 2 : 0) + ' ' + u : 'กรอกข้อมูลก่อน'}</b></div>`;
    $('k-out').innerHTML = box('Total Cost', cost, 'บาท') + box('Total Yield', out, 'กก.') + box('Revenue', rev, 'บาท') +
      box('Estimated Profit', profit, 'บาท', !ok(profit) ? '' : profit >= 0 ? 'pos' : 'neg') + box('Break-even Yield', beY, 'กก./ไร่') + box('Break-even Price', beP, 'บาท/กก.');
    // cost per unit vs sale price
    if (!ok(beP) || !ok(p)) { empty($('margin'), 'กรอกต้นทุนต่อไร่ ผลผลิต และราคา เพื่อดูส่วนต่างต่อ กก.'); return; }
    const m = p - beP, mk = ok(REF.price) ? REF.price : null;
    const xs = ['ต้นทุนต่อ กก.', 'ราคาขายที่กรอก', ...(mk ? ['ราคาตลาดเฉลี่ย (สศก.)'] : []), 'ส่วนต่างต่อ กก.'];
    const ys = [beP, p, ...(mk ? [mk] : []), m];
    Plotly.react($('margin'), [{ type: 'bar', x: xs, y: ys, text: ys.map(v => fmt(v, 2)), textposition: 'outside', textfont: { color: C.fg }, cliponaxis: false,
      marker: { color: [C.magenta, C.cyan, ...(mk ? [C.sky] : []), m >= 0 ? C.ok : C.bad] }, hovertemplate: '%{x}: %{y:,.2f} บาท/กก.<extra></extra>' }],
      layout({ bargap: 0.45, margin: { l: 10, r: 10, t: 20, b: 30 }, yaxis: axis('บาท/กก.') }), CFG);
  }

  // ---------- render ----------
  function render() {
    $('f-year').value = String(S.year); $('f-region').value = S.region; $('f-province').value = String(S.province);
    if (S.tab === 'overview') renderOverview(); else if (S.tab === 'climate') renderClimate(); else if (S.tab === 'factors') renderFactors(); else renderEconomics();
  }
  const start = (location.hash || '').replace('#', '');
  setTab(TABS.includes(start) ? start : 'overview');
})();
