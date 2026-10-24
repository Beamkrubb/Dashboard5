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
  const PRICE_FOR = { 'มันสำปะหลัง': 'มันสำปะหลังสด คละ', 'ยางพารา': 'ยางแผ่นดิบ ชั้น 3', 'ปาล์มน้ำมัน': 'ผลปาล์มน้ำมันทั้งทะลาย คละ',
    'ข้าวนาปี': 'ข้าวเปลือกเจ้า ความชื้น 15%', 'ข้าวนาปรัง': 'ข้าวเปลือกเจ้า ความชื้น 15%' };
  const TREND_FROM = 2550, TREND_TO = 2562;
  const years = [...new Set(D.ag.map(r => r[0]))].filter(y => y >= TREND_FROM && y <= TREND_TO).sort((a, b) => a - b);
  const DEF = { product: Math.max(0, PROD.indexOf(D.shortcuts[0])), year: years.includes(2562) ? 2562 : years[years.length - 1], region: ALL, province: -1, metric: 'prod' };
  const S = { ...DEF, tab: 'overview', rainView: 'total', disView: 'flood', fView: 'irr', sortKey: null, sortDir: -1 };

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
  // Choropleth drawn as filled polygons on cartesian lon/lat axes: no base-map / topojson download, works offline and under strict CSP.
  const GEO = P.map(n => {
    const f = D.geo.features.find(ft => ft.properties.n === n); const x = [], y = [];
    if (f) (f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates : [f.geometry.coordinates]).forEach(poly => poly.forEach(ring => {
      ring.forEach(([lo, la]) => { x.push(lo); y.push(la); }); x.push(null); y.push(null); }));
    return { x, y };
  });
  const hex = h => [1, 3, 5].map(k => parseInt(h.slice(k, k + 2), 16));
  function colorAt(scale, t) {
    t = Math.max(0, Math.min(1, t)); let k = 1; while (k < scale.length - 1 && scale[k][0] < t) k++;
    const [t0, c0] = scale[k - 1], [t1, c1] = scale[k], a = hex(c0), b = hex(c1), u = t1 > t0 ? (t - t0) / (t1 - t0) : 0;
    return `rgb(${a.map((v, j) => Math.round(v + (b[j] - v) * u)).join(',')})`;
  }
  function choropleth(el, values, { unit, label, scale = MAP_SCALE, highlight = -1, regionOnly = null, zmid = null, extraHover = null }) {
    const shown = P.map((_, i) => i).filter(i => !regionOnly || R[i] === regionOnly);
    const vs = shown.map(i => values[i]).filter(ok);
    let lo = vs.length ? Math.min(...vs) : 0, hi = vs.length ? Math.max(...vs) : 1;
    if (zmid != null) { const m = Math.max(Math.abs(hi - zmid), Math.abs(lo - zmid)) || 1; lo = zmid - m; hi = zmid + m; }
    if (hi === lo) hi = lo + 1;
    const nf = Math.max(...vs.map(v => Math.abs(v)), 0) >= 100 ? 0 : 1;
    const traces = shown.map(i => {
      const v = values[i], has = ok(v);
      return { type: 'scatter', mode: 'lines', x: GEO[i].x, y: GEO[i].y, fill: 'toself', meta: i, hoveron: 'fills',
        fillcolor: has ? colorAt(scale, (v - lo) / (hi - lo)) : C.none,
        line: { color: i === highlight ? '#FFFFFF' : 'rgba(255,255,255,0.22)', width: i === highlight ? 2.5 : 0.6 },
        text: `<b>${P[i]}</b> (รหัส ${CODE[i]})<br>${has ? `${label}: ${fmt(v, nf)} ${unit}` : 'ไม่มีข้อมูล'}${has && extraHover ? extraHover(i) : ''}`, hoverinfo: 'text' };
    });
    // keep the selected province outline on top
    if (highlight >= 0) { const j = traces.findIndex(t => t.meta === highlight); if (j >= 0) traces.push(traces.splice(j, 1)[0]); }
    if (vs.length) traces.push({ type: 'scatter', mode: 'markers', x: [null], y: [null], hoverinfo: 'skip', showlegend: false,
      marker: { size: 0, color: [lo, hi], cmin: lo, cmax: hi, colorscale: scale, showscale: true,
        colorbar: { thickness: 9, len: 0.55, x: 1, xanchor: 'right', y: 0.5, outlinewidth: 0, tickfont: { color: C.muted, size: 10 }, title: { text: unit, font: { color: C.muted, size: 11 } } } } });
    Plotly.react(el, traces, layout({ margin: { l: 0, r: 0, t: 0, b: 0 }, hovermode: 'closest', dragmode: false,
      xaxis: { visible: false, fixedrange: true }, yaxis: { visible: false, fixedrange: true, scaleanchor: 'x', scaleratio: 1.03 } }), CFG);
  }
  function hbar(el, items, { unit, scale }) {
    if (!items.length) return empty(el, 'ไม่มีข้อมูล');
    const v = items.map(d => d.v);
    Plotly.react(el, [{ type: 'bar', orientation: 'h', y: items.map(d => d.name), x: v, text: v.map(short), textposition: 'outside', textfont: { color: C.fg },
      cliponaxis: false, marker: { color: v, colorscale: scale, line: { width: items.map(d => d.sel ? 2 : 0), color: '#fff' } },
      customdata: items.map(d => d.code), hovertemplate: '%{y} (รหัส %{customdata}): %{x:,.1f} ' + unit + '<extra></extra>' }],
      layout({ bargap: 0.35, margin: { l: 10, r: 56, t: 6, b: 28 }, yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2, size: 11 }, gridcolor: 'rgba(0,0,0,0)', dtick: 1 }), xaxis: axis(unit) }), CFG);
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



  // ---------- state additions ----------
  Object.assign(S, { layer: { overview: 'metric', climate: 'rain', factors: 'irr', economics: 'yield' }, rankView: 'top', costView: 'crop' });
  const pf = p => p < 0.001 ? '< 0.001' : p.toFixed(3);
  const sumv = a => a.reduce((x, y) => x + (y || 0), 0);
  const scopeLabel = () => S.province >= 0 ? P[S.province] : S.region === ALL ? 'ทั้งประเทศ' : S.region;
  const inScope = i => (S.region === ALL || R[i] === S.region) && (S.province < 0 || i === S.province);
  const crop = () => S.product >= 0 ? S.product : 0;
  const cropLabel = () => S.product < 0 ? 'ทุกพืชรวมกัน' : PROD[S.product];
  const HII_YEARS = Object.keys(D.rain).map(Number);
  const hasHII = y => HII_YEARS.includes(y);
  const COST = D.cost.crops, CY = D.cost.years;
  const resizeAll = () => document.querySelectorAll('.chart').forEach(el => { if (el.data && window.Plotly && Plotly.Plots) try { Plotly.Plots.resize(el); } catch (e) { /* hidden */ } });
  try { new ResizeObserver(() => { clearTimeout(resizeAll.t); resizeAll.t = setTimeout(resizeAll, 80); }).observe($('main')); } catch (e) { window.addEventListener('resize', resizeAll); }

  // climate source: HII (official) for 2561-2562, ERA5 (complete) for every year
  function climate(y, src) {
    const s = src || (hasHII(y) ? 'hii' : 'era5');
    if (s === 'hii') return { src: 'hii', label: 'สสน.', rain: D.rain[y] || {}, season: D.season[y] || {}, temp: pick(D.tempHII[y], 0), tmax: pick(D.tempHII[y], 1), tmin: pick(D.tempHII[y], 2) };
    return { src: 'era5', label: 'ERA5', rain: D.eraRain[y] || {}, season: D.eraSeason[y] || {}, temp: pick(D.eraT[y], 0), tmax: pick(D.eraT[y], 1), tmin: pick(D.eraT[y], 2) };
  }
  function pick(obj, k) { const o = {}; Object.entries(obj || {}).forEach(([i, a]) => { if (a && ok(a[k])) o[i] = a[k]; }); return o; }

  // ---------- downloads capability (CSV) ----------
  let downloads = null;
  try { window.claude && window.claude.use && window.claude.use('downloads').then(d => { downloads = d; $('t-csv').hidden = !d; }).catch(() => {}); } catch (e) { /* no runtime */ }

  // ---------- global filters ----------
  const SHORT = D.shortcuts.map(n => PROD.indexOf(n)).filter(i => i >= 0);
  const others = PROD.map((p, i) => i).filter(i => !SHORT.includes(i)).sort((a, b) => PROD[a].localeCompare(PROD[b], 'th'));
  $('f-product').innerHTML = `<option value="-1">ทุกพืชรวมกัน</option><optgroup label="พืชหลัก">${SHORT.map(i => `<option value="${i}">${PROD[i]}</option>`).join('')}</optgroup>` +
    `<optgroup label="พืชอื่น ๆ (${others.length})">${others.map(i => `<option value="${i}">${PROD[i]}</option>`).join('')}</optgroup>`;
  opts($('f-year'), [...years].reverse().map(y => [y, String(y)]), S.year);
  opts($('f-region'), [[ALL, 'ทุกภาค'], ...D.regionNames.map(r => [r, r])], S.region);
  opts($('f-metric'), Object.entries(METRICS).map(([k, m]) => [k, `${m.label} (${m.unit})`]), S.metric);
  function provinceOptions() {
    const list = P.map((p, i) => [i, p]).filter(([i]) => S.region === ALL || R[i] === S.region).sort((a, b) => a[1].localeCompare(b[1], 'th'));
    if (S.province >= 0 && S.region !== ALL && R[S.province] !== S.region) S.province = -1;
    opts($('f-province'), [[-1, `ทุกจังหวัด (${list.length})`], ...list.map(([i, p]) => [i, `${p} (${CODE[i]})`])], S.province);
  }
  provinceOptions();
  function setFilter(k, v) {
    S[k] = v;
    if (k === 'region') provinceOptions();
    if (k === 'province' && v >= 0 && S.region !== ALL && R[v] !== S.region) { S.region = ALL; provinceOptions(); }
    if (k === 'product') syncCrops();
    render();
  }
  const selectProvince = i => setFilter('province', S.province === i ? -1 : i);
  $('f-product').onchange = e => setFilter('product', +e.target.value);
  $('f-year').onchange = e => setFilter('year', +e.target.value);
  $('f-region').onchange = e => setFilter('region', e.target.value);
  $('f-province').onchange = e => setFilter('province', +e.target.value);
  $('f-metric').onchange = e => setFilter('metric', e.target.value);
  $('f-reset').onclick = () => { Object.assign(S, DEF); provinceOptions(); syncCrops(); render(); };
  $('shortcuts').innerHTML = SHORT.map(i => `<button class="sc" type="button" data-p="${i}" aria-pressed="false">${PROD[i]}</button>`).join('');
  document.querySelectorAll('#shortcuts .sc').forEach(b => b.onclick = () => setFilter('product', +b.dataset.p));
  function drawBadges() {
    const items = [['region', S.region === ALL ? 'ทุกภาค' : S.region], ['province', S.province < 0 ? 'ทุกจังหวัด' : P[S.province]],
      ['product', cropLabel()], ['year', 'พ.ศ. ' + S.year], ['metric', METRICS[S.metric].label]];
    $('badges').innerHTML = items.filter(([k]) => S[k] !== DEF[k]).map(([k, v]) => `<span class="fb">${esc(v)}<button type="button" data-k="${k}" aria-label="ล้าง ${esc(v)}">×</button></span>`).join('') ||
      '';
    document.querySelectorAll('#badges button').forEach(b => b.onclick = () => setFilter(b.dataset.k, DEF[b.dataset.k]));
    document.querySelectorAll('#shortcuts .sc').forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.p === S.product)));
  }
  $('coverage').textContent = `ข้อมูลเปิดภาครัฐจริง · ${PROD.length} พืช × 77 จังหวัด · พ.ศ. ${years[0]}–${years[years.length - 1]}`;
  function syncCrops() { $('k-crop').value = String(crop()); kTouched = {}; ['k-yield', 'k-cost', 'k-price'].forEach(id => $(id).value = ''); const pn = PRICE_FOR[PROD[crop()]]; if (pn && D.prices[pn]) $('m-product').value = pn; }

  // ---------- tabs / expand / dialog ----------
  const TABS = ['overview', 'climate', 'factors', 'economics'];
  function setTab(t) {
    S.tab = TABS.includes(t) ? t : 'overview';
    TABS.forEach(k => { $('p-' + k).hidden = k !== S.tab; $('t-' + k).setAttribute('aria-selected', String(k === S.tab)); });
    try { history.replaceState(null, '', '#' + S.tab); } catch (e) { /* ignore */ }
    render();
  }
  document.querySelectorAll('.tab').forEach(b => b.onclick = () => setTab(b.dataset.tab));
  function seg(ids, set) { ids.forEach(([id, v]) => { $(id).onclick = () => { ids.forEach(([i2, v2]) => $(i2).setAttribute('aria-pressed', String(v2 === v))); set(v); render(); }; }); }
  seg([['rk-top', 'top'], ['rk-bot', 'bot']], v => S.rankView = v);
  seg([['dv-flood', 'flood'], ['dv-drought', 'drought'], ['dv-doae', 'doae']], v => S.disView = v);
  seg([['cv-crop', 'crop'], ['cv-all', 'all']], v => S.costView = v);
  let expanded = null;
  function collapse() { if (!expanded) return; expanded.classList.remove('expanded'); expanded.querySelector('[data-exp]').textContent = '⤢'; expanded = null; $('backdrop').hidden = true; setTimeout(resizeAll, 30); }
  document.querySelectorAll('[data-exp]').forEach(b => b.onclick = () => {
    const card = b.closest('.card'); if (expanded === card) return collapse(); collapse();
    card.classList.add('expanded'); b.textContent = '✕'; expanded = card; $('backdrop').hidden = false; setTimeout(resizeAll, 30);
  });
  $('backdrop').onclick = collapse;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { collapse(); document.querySelectorAll('details.info[open]').forEach(d => d.open = false); } });
  document.addEventListener('click', e => document.querySelectorAll('details.info[open]').forEach(d => { if (!d.contains(e.target)) d.open = false; }));
  $('open-src').onclick = () => { try { $('src').showModal(); } catch (e) { $('src').setAttribute('open', ''); } };
  $('src-close').onclick = () => { try { $('src').close(); } catch (e) { $('src').removeAttribute('open'); } };
  $('d-close').onclick = () => setFilter('province', -1);

  // ---------- map (left, layer depends on tab) ----------
  let mapBound = false;
  const LAYERS = {
    overview: [['metric', 'ตัวชี้วัดที่เลือก']],
    climate: [['rain', 'ฝนทั้งปี'], ['season', 'ฝน พ.ค.–ต.ค.'], ['anom', '% จากปกติ'], ['temp', 'อุณหภูมิ']],
    factors: [['irr', 'ชลประทาน'], ['mech', 'เครื่องจักร'], ['fert', 'ปุ๋ย'], ['soil', 'ดิน S1+S2'], ['flood', 'น้ำท่วม 62'], ['drought', 'แล้ง 62']],
    economics: [['yield', 'ผลผลิตต่อไร่'], ['profit', 'กำไรประมาณการ/ไร่']],
  };
  function drawLayerButtons() {
    const L = LAYERS[S.tab];
    $('map-layers').innerHTML = L.length > 1 ? L.map(([k, t]) => `<button type="button" data-l="${k}" aria-pressed="${S.layer[S.tab] === k}">${t}</button>`).join('') : '';
    $('map-layers').hidden = L.length < 2;
    document.querySelectorAll('#map-layers button').forEach(b => b.onclick = () => { S.layer[S.tab] = b.dataset.l; render(); });
  }
  function drawMap(title, sub, info, values, opt) {
    $('map-title').textContent = title; $('map-sub').textContent = sub; $('map-info').innerHTML = info;
    choropleth($('map'), values, { highlight: S.province, regionOnly: S.region === ALL ? null : S.region, ...opt });
    if (!mapBound && $('map').on) { mapBound = true; $('map').on('plotly_click', e => { const pt = e && e.points && e.points[0]; const i = pt && pt.data ? pt.data.meta : -1; if (i >= 0) selectProvince(i); }); }
  }
  function mapForTab() {
    const L = S.layer[S.tab], y = S.year, k = crop();
    if (S.tab === 'overview') {
      const m = METRICS[S.metric], v = {}, pv = {}; byProvince(rowsFor({ year: y, province: -1 })).forEach(d => { v[d.p] = d[S.metric]; pv[d.p] = d; });
      return drawMap(`${m.label} พ.ศ. ${y}`, `${cropLabel()} · ${m.unit}`, 'สศก. ข้อมูลการผลิตรายจังหวัด · สีเข้มสุด = ไม่มีข้อมูล (ไม่ใช่ 0)', v,
        { unit: m.unit, label: m.label, extraHover: i => pv[i] ? `<br>ผลผลิต ${short(pv[i].prod)} ตัน · ${fmt(pv[i].yield, 0)} กก./ไร่` : '' });
    }
    if (S.tab === 'climate') {
      const c = climate(y), v = {};
      if (L === 'temp') Object.assign(v, c.temp);
      else if (L === 'anom') { if (c.src === 'hii') Object.entries(c.rain).forEach(([i, r]) => { if (D.provNormal[i]) v[i] = (r / D.provNormal[i] - 1) * 100; }); }
      else Object.assign(v, L === 'season' ? c.season : c.rain);
      const names = { rain: 'ฝนสะสมทั้งปี', season: 'ฝน พ.ค.–ต.ค.', anom: 'ฝนต่างจากค่าปกติ 30 ปี', temp: 'อุณหภูมิเฉลี่ยทั้งปี' };
      return drawMap(`${names[L]} พ.ศ. ${y}`, `แหล่ง: ${c.src === 'hii' ? 'สสน. (ทางการ)' : 'ERA5 (ครบ 77 จังหวัด)'}${L === 'anom' && c.src !== 'hii' ? ' · ค่าปกติ 30 ปีมีเฉพาะ สสน. 2561–2562' : ''}`,
        c.src === 'hii' ? 'สสน. ฝนเชิงพื้นที่ IDW จากสถานีกรมอุตุฯ และอุณหภูมิรายจังหวัด (64–65 จังหวัด) ปี 2561–2562' : 'ERA5 reanalysis ที่จุดศูนย์กลางจังหวัด ใช้กับปีที่ สสน. ไม่มีข้อมูลรายจังหวัด (2550–2560) ค่าฝนสูงกว่า สสน. ราว 17–21%',
        v, L === 'temp' ? { unit: '°C', label: 'อุณหภูมิเฉลี่ย', scale: [[0, C.blue], [0.5, C.violet], [1, C.bad]], extraHover: i => ok(c.tmax[i]) ? `<br>สูงสุด ${c.tmax[i]} · ต่ำสุด ${c.tmin[i]} °C` : '' }
          : L === 'anom' ? { unit: '%', label: 'ต่างจากปกติ', scale: DIV_SCALE, zmid: 0, extraHover: i => `<br>ฝน ${fmt(c.rain[i])} · ปกติ ${fmt(D.provNormal[i])} มม.` }
          : { unit: 'มม.', label: names[L], scale: RAIN_SCALE });
    }
    if (S.tab === 'factors') {
      const F = factorDefs(), f = F[L];
      const v = {}; P.forEach((_, i) => { const x = f.get(i); if (ok(x)) v[i] = x; });
      return drawMap(f.name, f.sub, f.info, v, { unit: f.unit, label: f.short, scale: f.scale || MAP_SCALE, extraHover: f.hover });
    }
    // economics
    const pv = {}; byProvince(rowsFor({ year: y, product: k, region: ALL, province: -1 })).forEach(d => pv[d.p] = d);
    const c = COST[PROD[k]], last = CY.length - 1, v = {};
    if (L === 'profit' && c) Object.values(pv).forEach(d => { if (ok(d.yield)) v[d.p] = d.yield * (c.price[last] - c.cost[last]) / 1000; });
    else if (L !== 'profit') Object.values(pv).forEach(d => v[d.p] = d.yield);
    return drawMap(L === 'profit' ? `กำไรประมาณการต่อไร่: ${PROD[k]}` : `ผลผลิตต่อไร่: ${PROD[k]} พ.ศ. ${y}`,
      L === 'profit' ? (c ? `ผลผลิตจังหวัด ${y} × (ราคา − ต้นทุน สศก. ปี ${CY[last]}) ÷ 1,000` : 'สศก. ไม่ได้เผยแพร่ต้นทุนของพืชนี้') : 'กก./ไร่ · คลิกจังหวัดเพื่อใช้ผลผลิตของจังหวัดในเครื่องคำนวณ',
      'กำไรประมาณการสมมติว่าต้นทุนและราคาต่อตันเท่ากันทุกจังหวัด (ค่าเฉลี่ยประเทศของ สศก.) ส่วนที่ต่างกันมาจากผลผลิตต่อไร่ของแต่ละจังหวัดเท่านั้น',
      v, L === 'profit' ? { unit: 'บาท/ไร่', label: 'กำไรประมาณการ', scale: DIV_SCALE, zmid: 0 } : { unit: 'กก./ไร่', label: 'ผลผลิตต่อไร่' });
  }
  function factorDefs() {
    const k = PROD[crop()];
    const s12 = i => { const a = (D.soil[k] || {})[i]; if (!a) return null; const t = sumv(a); return t > 0 ? ((a[0] || 0) + (a[1] || 0)) / t * 100 : null; };
    return {
      irr: { name: 'พื้นที่โครงการชลประทาน (% ของพื้นที่จังหวัด)', short: 'ชลประทาน', unit: '%', scale: RAIN_SCALE, get: i => D.irr[i] && D.irr[i][4],
        sub: 'กรมชลประทาน GIS · โครงการใหญ่ + กลาง', info: 'ขอบเขตโครงการชลประทานขนาดใหญ่ 93 และกลาง 506 โครงการ ซ้อนกับขอบเขตจังหวัดบนกริด 0.01° (≈1.1 กม.) รวม 23.9 ล้านไร่ ไม่รวมโครงการขนาดเล็ก',
        hover: i => D.irr[i] ? `<br>${fmt(D.irr[i][0])} ไร่ · เทียบเนื้อที่ถือครองเกษตร ${fmt(D.irr[i][5], 1)}%` : '' },
      mech: { name: 'ผู้ถือครองที่ใช้เครื่องจักรการเกษตร (%)', short: 'ใช้เครื่องจักร', unit: '%', get: i => D.mech[i] && D.mech[i][2],
        sub: 'สสช. สำมะโนการเกษตร', info: 'ร้อยละของผู้ถือครองที่รายงานการใช้เครื่องจักร ปีสำมะโนไม่ระบุในไฟล์ (มีข้อมูลโดรน จึงน่าจะเป็นรอบ พ.ศ. 2566)',
        hover: i => D.mech[i] ? `<br>${fmt(D.mech[i][0])} จาก ${fmt(D.mech[i][1])} ราย` : '' },
      fert: { name: 'ผู้ถือครองที่ใช้ปุ๋ย (%)', short: 'ใช้ปุ๋ย', unit: '%', get: i => D.fert[i], sub: 'สสช. สำมะโนการเกษตร', info: 'ร้อยละของผู้ถือครองที่รายงานการใช้ปุ๋ย' },
      soil: { name: `ดินเหมาะสม S1+S2: ${k}`, short: 'S1+S2', unit: '%', get: s12, sub: D.soil[k] ? 'กรมพัฒนาที่ดิน Agri-Map' : 'Agri-Map ไม่มีพืชนี้ — ไม่มีข้อมูล',
        info: 'สัดส่วนพื้นที่ที่ประเมินว่าเหมาะสมสูง (S1) และปานกลาง (S2) ต่อพื้นที่ประเมินทั้งหมดของพืชนั้น' },
      flood: { name: 'พื้นที่เกษตรน้ำท่วม พ.ศ. 2562 (ไร่)', short: 'น้ำท่วม', unit: 'ไร่', scale: RISK_SCALE, get: i => D.flood2562[i] ? sumv(D.flood2562[i].slice(0, 3)) || null : null,
        sub: 'ปภ. นาข้าว + พืชสวน + พืชไร่', info: 'ปภ. สถิติอุทกภัยรายปี 2562', hover: i => D.flood2562[i] ? `<br>ความเสียหายภาคเกษตร ${fmt(D.flood2562[i][3])} บาท` : '' },
      drought: { name: 'หมู่บ้านที่ประกาศภัยแล้ง พ.ศ. 2562', short: 'หมู่บ้าน', unit: 'หมู่บ้าน', scale: RISK_SCALE, get: i => D.drought2562[i], sub: 'ปภ. สถิติภัยแล้ง 2562', info: 'ไฟล์ภัยแล้งของ ปภ. เป็นรายชื่อหมู่บ้านที่ประกาศเขตการให้ความช่วยเหลือ ไม่มีตัวเลขพื้นที่' },
    };
  }

  // =================== TAB 1 ===================
  let tableRows = [];
  const kpiBox = (cls, label, v, unit, d, sub, dir) => `<div class="kpi ${cls}"><div class="l">${label}</div><div class="v">${fmt(v, d)}${ok(v) ? `<small>${unit}</small>` : ''}</div><span class="d ${dir || ''}">${sub || '&nbsp;'}</span></div>`;
  function yoy(cur, prev, d, unit) { if (!ok(cur) || !ok(prev) || prev <= 0) return ['ไม่มีข้อมูลปีก่อน', '']; const p = (cur - prev) / prev * 100; return [`${p >= 0 ? '+' : ''}${p.toFixed(1)}% YoY (${cur - prev >= 0 ? '+' : ''}${fmt(cur - prev, d)} ${unit})`, p >= 0 ? 'up' : 'dn']; }
  function renderOverview() {
    const cur = totals(rowsFor({ year: S.year })), prev = totals(rowsFor({ year: S.year - 1 }));
    const k = (cls, l, key, unit, d) => { const [s, dir] = yoy(cur[key], prev[key], d, unit); return kpiBox(cls, `${l} · ${scopeLabel()}`, cur[key], unit, d, s, dir); };
    $('kpis').innerHTML = k('m', 'เนื้อที่เพาะปลูก', 'plant', 'ไร่', 0) + k('c', 'เนื้อที่เก็บเกี่ยว', 'harvest', 'ไร่', 0) + k('m', 'ผลผลิตรวม', 'prod', 'ตัน', 0) + k('c', 'ผลผลิตต่อไร่', 'yield', 'กก./ไร่', 1);
    const m = METRICS[S.metric];
    const series = years.map(y => ({ y, ...totals(rowsFor({ year: y })) })).filter(d => ok(d[S.metric]));
    $('trend-title').textContent = `แนวโน้ม${m.label}`;
    $('trend-sub').textContent = `${scopeLabel()} · ${cropLabel()} · ${m.unit} · จุดชมพู = ปีที่เลือก`;
    if (!series.length) empty($('trend'), 'ไม่มีข้อมูล'); else {
      const x = series.map(d => d.y), y = series.map(d => d[S.metric]), i = x.indexOf(S.year);
      Plotly.react($('trend'), [
        { x, y, mode: 'lines+markers', line: { shape: 'spline', color: C.cyan, width: 3 }, marker: { size: 5, color: C.cyan }, fill: 'tozeroy', fillcolor: 'rgba(0,229,255,0.07)', hovertemplate: 'พ.ศ. %{x}: %{y:,.1f} ' + m.unit + '<extra></extra>' },
        ...(i >= 0 ? [{ x: [x[i]], y: [y[i]], mode: 'markers', marker: { size: 12, color: C.magenta, line: { color: '#fff', width: 2 } }, hoverinfo: 'skip' }] : []),
      ], layout({ margin: { l: 10, r: 10, t: 6, b: 28 }, xaxis: axis(null, { dtick: 2 }), yaxis: axis(null) }), CFG);
    }
    const provs = byProvince(rowsFor({ year: S.year, province: -1 })).filter(d => (S.region === ALL || R[d.p] === S.region) && ok(d[S.metric]));
    const sorted = [...provs].sort((a, b) => b[S.metric] - a[S.metric]);
    const list = S.rankView === 'top' ? sorted.slice(0, 10) : sorted.filter(d => d[S.metric] > 0).slice(-10).reverse();
    $('rank-title').textContent = `${S.rankView === 'top' ? 'สูงสุด' : 'ต่ำสุด'} 10 จังหวัด`;
    $('rank-sub').textContent = `${m.label} · ${cropLabel()} · ${S.region === ALL ? 'ทั้งประเทศ' : S.region} · คลิกแท่งเพื่อดูจังหวัด`;
    hbar($('rank'), list.map(d => ({ name: P[d.p], code: CODE[d.p], v: d[S.metric], sel: d.p === S.province })), { unit: m.unit, scale: S.rankView === 'top' ? [[0, C.blue], [1, C.cyan]] : [[0, C.violet], [1, C.magenta]] });
    bindClick($('rank'), pt => P.indexOf(pt.y));
    const sc = provs.filter(d => ok(d.plant) && ok(d.yield) && d.plant > 0);
    $('scale-sub').textContent = `จุด = จังหวัด · ขนาด = ผลผลิต · ${cropLabel()} · ${S.year}`;
    if (sc.length < 3) { empty($('scale'), 'ข้อมูลไม่พอ'); $('scale-insight').innerHTML = 'ข้อมูลไม่พอสำหรับเปรียบเทียบ'; }
    else {
      const mx = Math.max(...sc.map(z => z.prod || 0)) || 1, medY = [...sc].map(d => d.yield).sort((a, b) => a - b)[Math.floor(sc.length / 2)];
      Plotly.react($('scale'), [{ x: sc.map(d => d.plant), y: sc.map(d => d.yield), text: sc.map(d => P[d.p]), mode: 'markers',
        marker: { size: sc.map(d => 7 + 16 * Math.sqrt((d.prod || 0) / mx)), color: sc.map(d => d.p === S.province ? C.magenta : d.yield >= medY ? C.cyan : C.violet), opacity: 0.85, line: { color: '#fff', width: sc.map(d => d.p === S.province ? 2.5 : 0.5) } },
        hovertemplate: '<b>%{text}</b><br>เนื้อที่ %{x:,.0f} ไร่<br>%{y:,.0f} กก./ไร่<extra></extra>' }],
        layout({ margin: { l: 10, r: 10, t: 6, b: 30 }, xaxis: axis('เนื้อที่เพาะปลูก (ไร่, log)', { type: 'log' }), yaxis: axis('กก./ไร่') }), CFG);
      bindClick($('scale'), pt => P.indexOf(pt.text));
      const byProd = [...sc].sort((a, b) => b.prod - a.prod), byYield = [...sc].sort((a, b) => b.yield - a.yield), st = stats(sc.map(d => Math.log(d.plant)), sc.map(d => d.yield));
      $('scale-insight').innerHTML = `<b>ข้อสังเกต:</b> ${P[byProd[0].p]} ผลิตได้มากที่สุด (${short(byProd[0].prod)} ตัน) แต่ผลผลิตต่อไร่อันดับ ${byYield.indexOf(byProd[0]) + 1}/${sc.length}; ${P[byYield[0].p]} ผลผลิตต่อไร่สูงสุด ${fmt(byYield[0].yield, 0)} กก./ไร่.` +
        (st ? ` ρ (ขนาดพื้นที่, ผลผลิตต่อไร่) = ${st.rho.toFixed(2)}, p = ${pf(st.ps)}` : '') + (S.product < 0 ? '<br>ตอนนี้รวมทุกพืช ควรเลือกพืชเดียว' : '');
    }
    const fillN = S.year === 2562 ? Object.keys(D.agFill || {}).filter(k => S.product < 0 || PROD[S.product] === k) : [];
    $('basis-note').innerHTML = '<b>นิยามเนื้อที่ สศก.:</b> พืชล้มลุก = เพาะปลูก/เก็บเกี่ยว · ไม้ยืนต้น = ยืนต้น/ให้ผล (กรีดได้)' + (fillN.length ? `<br><b>ปี 2562:</b> ${fillN.join(' และ ')} เติมจากไฟล์รายจังหวัดของ สศก.` : '') + '<br>คลิกแถวเพื่อเปิดรายละเอียดจังหวัด';
    tableRows = D.ag.filter(r => r[0] === S.year && (S.product < 0 || r[1] === S.product) && (S.region === ALL || R[r[2]] === S.region))
      .map(r => { const t = totals([r]); return { province: P[r[2]], code: CODE[r[2]], crop: PROD[r[1]], plant: t.plant, harvest: t.harvest, prod: t.prod, yield: t.yield, ratio: t.ratio, p: r[2] }; });
    drawTable();
  }
  function bindClick(el, getIdx) { if (el.__bound || !el.on) return; el.__bound = true; el.on('plotly_click', e => { const pt = e && e.points && e.points[0]; const i = pt ? getIdx(pt) : -1; if (i >= 0) selectProvince(i); }); }
  const COLS = [['province', 'จังหวัด'], ['code', 'รหัส'], ['crop', 'พืช'], ['plant', 'เพาะปลูก (ไร่)', 0], ['harvest', 'เก็บเกี่ยว (ไร่)', 0], ['prod', 'ผลผลิต (ตัน)', 0], ['yield', 'กก./ไร่', 0], ['ratio', 'เก็บเกี่ยว %', 1]];
  function visibleRows() {
    const q = $('t-search').value.trim().toLowerCase();
    const rows = q ? tableRows.filter(r => [r.province, R[r.p], r.crop, r.code].join(' ').toLowerCase().includes(q)) : [...tableRows];
    const key = S.sortKey || S.metric;
    rows.sort((a, b) => { const x = a[key], y = b[key]; if (!ok(x) && typeof x !== 'string') return 1; if (!ok(y) && typeof y !== 'string') return -1; return (typeof x === 'string' ? x.localeCompare(y, 'th') : x - y) * S.sortDir; });
    return { rows, key };
  }
  function drawTable() {
    const { rows, key } = visibleRows();
    $('table-sub').textContent = `${rows.length} แถว · พ.ศ. ${S.year}`;
    $('table').innerHTML = '<thead><tr>' + COLS.map(([k, t]) => `<th data-k="${k}" aria-sort="${k === key ? (S.sortDir > 0 ? 'ascending' : 'descending') : 'none'}">${t}</th>`).join('') + '</tr></thead><tbody>' +
      rows.map(r => `<tr data-p="${r.p}" class="${r.p === S.province ? 'sel' : ''}">` + COLS.map(([k, , d]) => `<td>${d == null ? esc(r[k]) : (ok(r[k]) ? fmt(r[k], d) : '–')}</td>`).join('') + '</tr>').join('') + '</tbody>';
    document.querySelectorAll('#table th').forEach(th => th.onclick = () => { const k = th.dataset.k; S.sortDir = (S.sortKey === k) ? -S.sortDir : -1; S.sortKey = k; drawTable(); });
    document.querySelectorAll('#table tbody tr').forEach(tr => tr.onclick = () => selectProvince(+tr.dataset.p));
  }
  $('t-search').oninput = () => drawTable();
  $('t-csv').onclick = async () => {
    if (!downloads) return;
    const { rows } = visibleRows(), q = v => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const head = ['ภาค', ...COLS.map(c => c[1])];
    const csv = '﻿' + [head.join(','), ...rows.map(r => [R[r.p], ...COLS.map(([k, , d]) => d == null ? r[k] : (ok(r[k]) ? +r[k].toFixed(d) : ''))].map(q).join(','))].join('\r\n');
    try { await downloads.save({ filename: `thai_agri_${S.year}${S.product >= 0 ? '_' + PROD[S.product] : ''}.csv`, data: csv }); } catch (e) { /* declined */ }
  };

  // =================== TAB 2 ===================
  const XV = { season: ['ฝน พ.ค.–ต.ค.', 'มม.', c => c.season], rain: ['ฝนทั้งปี', 'มม.', c => c.rain], temp: ['อุณหภูมิเฉลี่ย', '°C', c => c.temp], tmax: ['อุณหภูมิสูงสุดของปี', '°C', c => c.tmax] };
  opts($('c-x'), Object.entries(XV).map(([k, v]) => [k, v[0]]), 'season');
  $('c-x').onchange = () => render();
  function statLine(el, st) {
    el.innerHTML = !st ? '' : `<span>Pearson r <b>${st.r.toFixed(3)}</b> (p ${pf(st.pr)})</span><span>Spearman ρ <b>${st.rho.toFixed(3)}</b> (p ${pf(st.ps)})</span><span>N <b>${st.n}</b></span>` +
      `<span class="${st.pr < 0.05 || st.ps < 0.05 ? 'sig' : 'ns'}">${st.pr < 0.05 || st.ps < 0.05 ? 'มีนัยสำคัญ α 0.05' : 'ไม่มีนัยสำคัญ'}</span><span>· สหสัมพันธ์ ≠ เหตุและผล</span>`;
  }
  function scatterXY(el, pts, xl, xu, st, logx) {
    const xs = pts.map(d => d.x), x0 = Math.min(...xs), x1 = Math.max(...xs);
    Plotly.react(el, [
      { x: xs, y: pts.map(d => d.y), text: pts.map(d => P[d.p]), mode: 'markers',
        marker: { size: pts.map(d => d.p === S.province ? 15 : 9), color: pts.map(d => d.p === S.province ? C.magenta : S.region === ALL || R[d.p] === S.region ? C.cyan : 'rgba(124,130,173,0.4)'), line: { color: '#fff', width: pts.map(d => d.p === S.province ? 2 : 0.5) } },
        hovertemplate: '<b>%{text}</b><br>' + xl + ': %{x:,.1f} ' + xu + '<br>%{y:,.0f} กก./ไร่<extra></extra>' },
      ...(st && !logx ? [{ x: [x0, x1], y: [st.slope * x0 + st.icept, st.slope * x1 + st.icept], mode: 'lines', line: { color: C.magenta, width: 2, dash: 'dash' }, hoverinfo: 'skip' }] : []),
    ], layout({ margin: { l: 10, r: 10, t: 6, b: 30 }, xaxis: axis(`${xl} (${xu})`, logx ? { type: 'log' } : {}), yaxis: axis('กก./ไร่') }), CFG);
    bindClick(el, pt => P.indexOf(pt.text));
  }
  function renderClimate() {
    const y = S.year, c = climate(y), k = crop();
    const rv = Object.entries(c.rain).filter(([i, v]) => ok(v) && inScope(+i)), tv = Object.entries(c.temp).filter(([i, v]) => ok(v) && inScope(+i));
    const avg = rv.length ? sumv(rv.map(a => a[1])) / rv.length : null, tavg = tv.length ? sumv(tv.map(a => a[1])) / tv.length : null;
    const sv = Object.entries(c.season).filter(([i]) => inScope(+i)), savg = sv.length ? sumv(sv.map(a => a[1])) / sv.length : null;
    const norm = c.src === 'hii' ? rv.map(([i]) => D.provNormal[i]).filter(ok) : [], nAvg = norm.length ? sumv(norm) / norm.length : null;
    const e = c.src === 'era5' ? null : climate(y, 'era5');
    $('kpis').innerHTML = kpiBox('m', `ฝนเฉลี่ยทั้งปี · ${scopeLabel()} (${c.label})`, avg, 'มม.', 0, nAvg ? `${((avg / nAvg - 1) * 100).toFixed(1)}% เทียบปกติ 30 ปี` : `${rv.length} จังหวัด`, nAvg ? (avg >= nAvg ? 'up' : 'dn') : '') +
      kpiBox('c', `ฝน พ.ค.–ต.ค. · ${scopeLabel()}`, savg, 'มม.', 0, avg ? `${(savg / avg * 100).toFixed(0)}% ของฝนทั้งปี` : '') +
      kpiBox('m', `อุณหภูมิเฉลี่ย · ${scopeLabel()} (${c.label})`, tavg, '°C', 1, `${tv.length} จังหวัดที่มีข้อมูล${c.src === 'hii' && tv.length < rv.length ? ' · ส่วนที่ขาดดูได้จาก ERA5' : ''}`) +
      kpiBox('p', 'ฝนทั้งประเทศ (สสน.)', D.national[y], 'มม.', 0, `ปกติ 2534–2563: ${fmt(D.nationalNormal)} มม.`, D.national[y] >= D.nationalNormal ? 'up' : 'dn');
    // scatter
    const [xl, xu, get] = XV[$('c-x').value], src = get(c);
    const pts = byProvince(rowsFor({ year: y, product: k, region: ALL, province: -1 })).filter(d => ok(d.yield) && ok(src[d.p])).map(d => ({ p: d.p, x: src[d.p], y: d.yield }));
    const st = stats(pts.map(d => d.x), pts.map(d => d.y));
    $('scatter-title').textContent = `${xl} vs ผลผลิตต่อไร่: ${PROD[k]}`;
    $('scatter-sub').textContent = `จุด = จังหวัด · พ.ศ. ${y} · ${c.src === 'hii' ? 'สสน.' : 'ERA5'} · เส้นประ = OLS`;
    if (!st) { empty($('scatter'), `มีจังหวัดที่มีข้อมูลทั้งสองด้าน ${pts.length} จังหวัด (ต้อง ≥ 5)`); $('stats').innerHTML = ''; }
    else { scatterXY($('scatter'), pts, xl, xu, st); statLine($('stats'), st); }
    // national
    const ny = Object.keys(D.national).map(Number).filter(v => v >= TREND_FROM && v <= TREND_TO).sort();
    $('nat-sub').textContent = `ค่าปกติ ${fmt(D.nationalNormal)} มม. (เส้นประ)`;
    Plotly.react($('national'), [
      { type: 'bar', x: ny, y: ny.map(v => D.national[v]), marker: { color: ny.map(v => v === y ? C.magenta : D.national[v] >= D.nationalNormal ? C.cyan : C.violet) }, hovertemplate: 'พ.ศ. %{x}: %{y:,.0f} มม.<extra></extra>' },
      { x: [ny[0] - 0.5, ny[ny.length - 1] + 0.5], y: [D.nationalNormal, D.nationalNormal], mode: 'lines', line: { color: '#fff', dash: 'dash', width: 1.5 }, hoverinfo: 'skip' },
    ], layout({ bargap: 0.3, margin: { l: 10, r: 10, t: 6, b: 26 }, xaxis: axis(null, { dtick: 2 }), yaxis: axis('มม.', { rangemode: 'tozero' }) }), CFG);
    // season stacked bars (top 15 in scope)
    const items = Object.keys(c.season).map(Number).filter(i => S.region === ALL || R[i] === S.region).map(i => ({ p: i, s: c.season[i], o: Math.max(0, (c.rain[i] || 0) - c.season[i]) })).sort((a, b) => b.s - a.s).slice(0, 10);
    if (S.province >= 0 && !items.some(d => d.p === S.province) && ok(c.season[S.province])) items.push({ p: S.province, s: c.season[S.province], o: Math.max(0, (c.rain[S.province] || 0) - c.season[S.province]) });
    $('season-sub').textContent = `10 จังหวัดฝนฤดูเพาะปลูกสูงสุด${S.region !== ALL ? 'ใน' + S.region : ''} · ${c.label} · ${y}`;
    if (!items.length) empty($('season'), 'ไม่มีข้อมูล'); else
    Plotly.react($('season'), [
      { type: 'bar', orientation: 'h', y: items.map(d => P[d.p]), x: items.map(d => d.s), name: 'พ.ค.–ต.ค.', marker: { color: items.map(d => d.p === S.province ? C.magenta : C.cyan) }, hovertemplate: '%{y}: %{x:,.0f} มม.<extra>พ.ค.–ต.ค.</extra>' },
      { type: 'bar', orientation: 'h', y: items.map(d => P[d.p]), x: items.map(d => d.o), name: 'นอกฤดู', marker: { color: C.violet }, hovertemplate: '%{y}: %{x:,.0f} มม.<extra>นอกฤดู</extra>' },
    ], layout({ barmode: 'stack', bargap: 0.25, showlegend: true, legend: { orientation: 'h', y: 1.0, yanchor: 'bottom', x: 0, font: { color: C.fg2, size: 11 } }, margin: { l: 10, r: 10, t: 26, b: 26 },
      yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2, size: 11 }, gridcolor: 'rgba(0,0,0,0)', dtick: 1 }), xaxis: axis('มม.') }), CFG);
    bindClick($('season'), pt => P.indexOf(pt.y));
    // station substitute: monthly ERA5 profile for province (or scope average)
    const idx = S.province >= 0 ? [S.province] : P.map((_, i) => i).filter(inScope);
    const mon = [...Array(12)].map((_, m) => { const r = idx.map(i => ((D.eraM[i] || {})[y] || [[], []])[0][m]).filter(ok), t = idx.map(i => ((D.eraM[i] || {})[y] || [[], []])[1][m]).filter(ok);
      return [r.length ? sumv(r) / r.length : null, t.length ? sumv(t) / t.length : null]; });
    const MN = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
    $('station-title').textContent = `ภูมิอากาศรายเดือน: ${scopeLabel()} พ.ศ. ${y}`;
    $('station-sub').textContent = `ทดแทนสถานีกรมอุตุฯ ด้วย ERA5 · ${S.province >= 0 ? 'จุดศูนย์กลางจังหวัด' : 'เฉลี่ย ' + idx.length + ' จังหวัด'} · แถบเขียว = ฤดูเพาะปลูก`;
    Plotly.react($('station'), [
      { type: 'bar', x: MN, y: mon.map(v => v[0]), name: 'ฝน (มม.)', marker: { color: MN.map((_, m) => m >= 4 && m <= 9 ? C.cyan : 'rgba(0,229,255,0.35)') }, hovertemplate: '%{x}: %{y:,.0f} มม.<extra></extra>' },
      { x: MN, y: mon.map(v => v[1]), name: 'อุณหภูมิ (°C)', yaxis: 'y2', mode: 'lines+markers', line: { color: C.magenta, width: 2.5, shape: 'spline' }, marker: { size: 5 }, hovertemplate: '%{x}: %{y:.1f} °C<extra></extra>' },
    ], layout({ showlegend: true, legend: { orientation: 'h', y: 1.0, yanchor: 'bottom', x: 0, font: { color: C.fg2, size: 11 } }, margin: { l: 10, r: 10, t: 26, b: 26 }, bargap: 0.25,
      shapes: [{ type: 'rect', xref: 'x', yref: 'paper', x0: 3.5, x1: 9.5, y0: 0, y1: 1, fillcolor: 'rgba(0,229,160,0.06)', line: { width: 0 } }],
      xaxis: axis(null, { tickangle: 0, tickfont: { size: 10, color: C.muted } }), yaxis: axis('มม.', { rangemode: 'tozero' }), yaxis2: axis('°C', { overlaying: 'y', side: 'right', showgrid: false, tickformat: '.0f' }) }), CFG);
  }

  // =================== TAB 3 ===================
  const FXK = { irr: 'ชลประทาน (% พื้นที่จังหวัด)', mech: 'ใช้เครื่องจักร (%)', fert: 'ใช้ปุ๋ย (%)', soil: 'ดิน S1+S2 ของพืชนี้ (%)', flood: 'น้ำท่วม 2562 (ไร่)' };
  opts($('f-x'), Object.entries(FXK), 'irr');
  $('f-x').onchange = () => render();
  const soilCrops = Object.keys(D.soil).sort((a, b) => a.localeCompare(b, 'th'));
  opts($('s-crop'), soilCrops.map(c => [c, c]), soilCrops.includes('ข้าวนาปี') ? 'ข้าวนาปี' : soilCrops[0]);
  $('s-crop').onchange = () => render();
  const hhYears = Object.keys(D.household || {}).sort();
  opts($('h-year'), hhYears.map(y => [y, y]), hhYears[hhYears.length - 1]);
  $('h-year').onchange = () => render();
  function renderFactors() {
    const k = crop(), F = factorDefs(), idx = P.map((_, i) => i).filter(inScope);
    const sum = f => sumv(idx.map(f));
    const irr = sum(i => D.irr[i] && D.irr[i][0]), area = sum(i => D.irr[i] && D.irr[i][2]), hold = sum(i => D.land[i] && D.land[i]['เนื้อที่ถือครองทำการเกษตร']);
    const mu = sum(i => D.mech[i] && D.mech[i][0]), mr = sum(i => D.mech[i] && D.mech[i][1]);
    const dIn = sum(i => D.doae[i] && D.doae[i][0] + D.doae[i][1]), dOut = sum(i => D.doae[i] && D.doae[i][2] + D.doae[i][3]);
    const fl = sum(i => D.flood2562[i] && sumv(D.flood2562[i].slice(0, 3)));
    $('kpis').innerHTML = kpiBox('m', `พื้นที่โครงการชลประทาน · ${scopeLabel()}`, irr, 'ไร่', 0, area ? `${(irr / area * 100).toFixed(1)}% ของพื้นที่ · ${hold ? (irr / hold * 100).toFixed(0) + '% ของเนื้อที่ถือครอง' : ''}` : '') +
      kpiBox('c', 'ผู้ถือครองที่ใช้เครื่องจักร', mr ? mu / mr * 100 : null, '%', 1, `${fmt(mu)} จาก ${fmt(mr)} ราย (สสช.)`) +
      kpiBox('m', 'พื้นที่เกษตรน้ำท่วม 2562 (ปภ.)', fl || null, 'ไร่', 0, fl ? 'นาข้าว + พืชสวน + พืชไร่' : 'ไม่มีจังหวัดที่น้ำท่วมในขอบเขตนี้') +
      kpiBox('p', 'ประสบภัยนอกเขตชลประทาน (กสก.)', dIn + dOut ? dOut / (dIn + dOut) * 100 : null, '%', 0, `ใน ${short(dIn)} · นอก ${short(dOut)} ไร่`);
    // factor scatter
    const fk = $('f-x').value, f = F[fk];
    const pts = byProvince(rowsFor({ year: S.year, product: k, region: ALL, province: -1 })).filter(d => ok(d.yield) && ok(f.get(d.p))).map(d => ({ p: d.p, x: f.get(d.p), y: d.yield }));
    const st = stats(pts.map(d => d.x), pts.map(d => d.y));
    $('fsc-title').textContent = `${f.short} vs ผลผลิตต่อไร่: ${PROD[k]}`;
    $('fsc-sub').textContent = `จุด = จังหวัด · ผลผลิต พ.ศ. ${S.year} · ปัจจัยเป็นค่าคงที่ของจังหวัด`;
    if (!st) { empty($('fsc'), `มีจังหวัดที่มีข้อมูลทั้งสองด้าน ${pts.length} จังหวัด (ต้อง ≥ 5)`); $('fstats').innerHTML = ''; }
    else { scatterXY($('fsc'), pts, f.short, f.unit, st, f.unit === 'ไร่'); statLine($('fstats'), st); }
    // soil bars
    if (D.soil[PROD[k]] && $('s-crop').dataset.auto !== PROD[k]) { $('s-crop').value = PROD[k]; $('s-crop').dataset.auto = PROD[k]; }
    const sc = $('s-crop').value, s = D.soil[sc] || {};
    let rows = Object.entries(s).map(([i, a]) => ({ p: +i, a, tot: sumv(a) })).filter(d => d.tot > 0 && (S.region === ALL || R[d.p] === S.region)).sort((a, b) => b.tot - a.tot).slice(0, 10);
    if (S.province >= 0 && s[S.province] && !rows.some(d => d.p === S.province)) rows.push({ p: S.province, a: s[S.province], tot: sumv(s[S.province]) });
    $('soil-title').textContent = `ความเหมาะสมของดิน: ${sc}`;
    $('soil-sub').textContent = `10 จังหวัดพื้นที่ประเมินมากสุด${S.region !== ALL ? 'ใน' + S.region : ''} · % ของพื้นที่ประเมิน · กรมพัฒนาที่ดิน`;
    const cls = [['S1', C.cyan], ['S2', C.blue], ['S3', C.violet], ['N', C.magenta]];
    if (!rows.length) empty($('soilbar'), 'ไม่มีข้อมูล Agri-Map'); else
    Plotly.react($('soilbar'), cls.map(([n, col], j) => ({ type: 'bar', orientation: 'h', name: n, y: rows.map(d => P[d.p]), x: rows.map(d => (d.a[j] || 0) / d.tot * 100), customdata: rows.map(d => d.a[j] || 0),
      marker: { color: col }, hovertemplate: '%{y}: %{x:.1f}% (%{customdata:,.0f} ไร่)<extra>' + n + '</extra>' })),
      layout({ barmode: 'stack', bargap: 0.25, showlegend: true, legend: { orientation: 'h', y: 1.0, yanchor: 'bottom', x: 0, font: { color: C.fg2, size: 11 } }, margin: { l: 10, r: 10, t: 26, b: 26 },
        yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2, size: 11 }, gridcolor: 'rgba(0,0,0,0)', dtick: 1 }), xaxis: axis('%', { range: [0, 100] }) }), CFG);
    bindClick($('soilbar'), pt => P.indexOf(pt.y));
    // disasters
    const reg = i => S.region === ALL || R[i] === S.region;
    const LEG = { orientation: 'h', y: 1.0, yanchor: 'bottom', x: 0, font: { color: C.fg2, size: 11 } }, YA = axis(null, { autorange: 'reversed', tickfont: { color: C.fg2, size: 11 }, gridcolor: 'rgba(0,0,0,0)', dtick: 1 });
    if (S.disView === 'flood') {
      const keys = Object.keys(D.flood2562).map(Number).filter(reg).filter(i => sumv(D.flood2562[i].slice(0, 3)) > 0).sort((a, b) => sumv(D.flood2562[b].slice(0, 3)) - sumv(D.flood2562[a].slice(0, 3))).slice(0, 10);
      $('dis-title').textContent = 'พื้นที่เกษตรน้ำท่วม 2562'; $('dis-sub').textContent = 'ปภ. · 10 จังหวัดสูงสุด · ไร่'; $('dis-info').innerHTML = 'ปภ. สถิติอุทกภัยรายปี 2562 (dpm-gd027) แยกนาข้าว พืชสวน พืชไร่';
      if (!keys.length) empty($('disbar'), 'ไม่มีจังหวัดที่น้ำท่วมในขอบเขตนี้'); else
      Plotly.react($('disbar'), [['นาข้าว', 0, C.cyan], ['พืชสวน', 1, C.violet], ['พืชไร่', 2, C.magenta]].map(([n, j, col]) => ({ type: 'bar', orientation: 'h', name: n, y: keys.map(i => P[i]), x: keys.map(i => D.flood2562[i][j] || 0), marker: { color: col }, hovertemplate: '%{y}: %{x:,.0f} ไร่<extra>' + n + '</extra>' })),
        layout({ barmode: 'stack', bargap: 0.25, showlegend: true, legend: LEG, margin: { l: 10, r: 10, t: 26, b: 26 }, yaxis: YA, xaxis: axis('ไร่') }), CFG);
    } else if (S.disView === 'drought') {
      const keys = Object.keys(D.drought2562).map(Number).filter(reg).sort((a, b) => D.drought2562[b] - D.drought2562[a]).slice(0, 10);
      $('dis-title').textContent = 'หมู่บ้านประกาศภัยแล้ง 2562'; $('dis-sub').textContent = 'ปภ. · จำนวนหมู่บ้าน'; $('dis-info').innerHTML = 'ปภ. สถิติภัยแล้งรายปี 2562 (dpm-gd028) เป็นรายชื่อหมู่บ้าน ไม่มีตัวเลขพื้นที่';
      hbar($('disbar'), keys.map(i => ({ name: P[i], code: CODE[i], v: D.drought2562[i], sel: i === S.province })), { unit: 'หมู่บ้าน', scale: [[0, C.warn], [1, C.bad]] });
    } else {
      const keys = Object.keys(D.doae).map(Number).filter(reg).filter(i => sumv(D.doae[i]) > 0).sort((a, b) => sumv(D.doae[b]) - sumv(D.doae[a])).slice(0, 10);
      $('dis-title').textContent = 'ประสบภัย ในเขต vs นอกเขตชลประทาน'; $('dis-sub').textContent = `กสก. · 10 จังหวัดสูงสุด · ไร่ · รวมในเขต ${short(dIn)} นอกเขต ${short(dOut)}`;
      $('dis-info').innerHTML = 'กรมส่งเสริมการเกษตร พื้นที่ประสบภัยรายตำบล แยกในเขต/นอกเขตชลประทาน · <b>ไฟล์ไม่ระบุปีของเหตุการณ์</b> จึงใช้เทียบสัดส่วน ไม่ควรรวมกับข้อมูล ปภ.';
      if (!keys.length) empty($('disbar'), 'ไม่มีข้อมูลในขอบเขตนี้'); else
      Plotly.react($('disbar'), [['น้ำท่วม ในเขต', 0, C.blue], ['น้ำท่วม นอกเขต', 2, C.cyan], ['แล้ง ในเขต', 1, C.warn], ['แล้ง นอกเขต', 3, C.bad]].map(([n, j, col]) => ({ type: 'bar', orientation: 'h', name: n,
        y: keys.map(i => P[i]), x: keys.map(i => D.doae[i][j] || 0), marker: { color: col }, hovertemplate: '%{y}: %{x:,.0f} ไร่<extra>' + n + '</extra>' })),
        layout({ barmode: 'stack', bargap: 0.25, showlegend: true, legend: LEG, margin: { l: 10, r: 10, t: 26, b: 26 }, yaxis: YA, xaxis: axis('ไร่') }), CFG);
    }
    bindClick($('disbar'), pt => P.indexOf(pt.y));
    // household donut
    const hr = D.household[$('h-year').value] || [];
    if (!hr.length) empty($('donut'), 'ไม่มีข้อมูล'); else {
      const farm = sumv(hr.filter(r => !r[0].includes('นอก')).map(r => r[2])), all = sumv(hr.map(r => r[2]));
      Plotly.react($('donut'), [{ type: 'pie', hole: 0.6, domain: { x: [0, 0.48] }, labels: hr.map(r => (r[0].includes('นอก') ? 'นอกเกษตร: ' : 'เกษตร: ') + r[1]), values: hr.map(r => r[2]), sort: false, textinfo: 'percent', textfont: { color: '#fff', size: 11 },
        marker: { colors: [C.magenta, C.violet, C.blue, C.sky, '#3A4080'], line: { color: '#181D45', width: 2 } }, hovertemplate: '%{label}<br>%{value:,.0f} บาท/ครัวเรือน (%{percent})<extra></extra>' }],
        layout({ showlegend: true, legend: { orientation: 'v', x: 0.52, xanchor: 'left', y: 0.5, font: { color: C.fg2, size: 10.5 } }, margin: { l: 4, r: 4, t: 4, b: 4 },
          annotations: [{ text: `<b>${fmt(farm)}</b><br>บาท/ครัวเรือน<br>รายจ่ายเกษตร ${(farm / all * 100).toFixed(0)}%`, x: 0.24, xref: 'paper', y: 0.5, yref: 'paper', showarrow: false, font: { color: C.fg, size: 11 } }] }), CFG);
    }
  }

  // =================== TAB 4 ===================
  const priceNames = Object.keys(D.prices);
  opts($('m-product'), priceNames.map(p => [p, p]), PRICE_FOR[PROD[crop()]] || priceNames[0]);
  opts($('m-range'), [['sel', 'ปีที่เลือก'], ['2561-2562', '2561–2562'], ['52', '52 สัปดาห์ล่าสุด'], ['all', 'ทั้งหมด']], 'sel');
  ['m-product', 'm-range'].forEach(id => $(id).onchange = () => render());
  opts($('k-crop'), PROD.map((p, i) => [i, p]), crop());
  let kTouched = {};
  ['k-area', 'k-yield', 'k-cost', 'k-price'].forEach(id => $(id).oninput = () => { kTouched[id] = true; calc(); });
  $('k-crop').onchange = () => { ['k-yield', 'k-cost', 'k-price'].forEach(id => $(id).value = ''); render(); };
  let REF = {};
  function renderEconomics() {
    const name = $('m-product').value, rng = $('m-range').value, all = D.prices[name] || [];
    const rows = rng === '52' ? all.slice(-52) : rng === 'all' ? all : rng === '2561-2562' ? all.filter(r => r[0] === 2561 || r[0] === 2562) : all.filter(r => r[0] === S.year);
    const v = rows.map(r => r[3]), lab = r => `${r[0]}-${String(r[1]).padStart(2, '0')} ส.${r[2]}`;
    const kc = +$('k-crop').value, cname = PROD[kc], c = COST[cname], last = CY.length - 1;
    const mean = v.length ? sumv(v) / v.length : null;
    $('kpis').innerHTML = kpiBox('m', `ราคาเฉลี่ย ${name}`, mean, 'บาท/กก.', 2, v.length ? `${v.length} สัปดาห์ · ${rng === 'sel' ? 'พ.ศ. ' + S.year : $('m-range').selectedOptions[0].text}` : `ชุดนี้มี พ.ศ. ${all[0][0]}–${all[all.length - 1][0]}`) +
      kpiBox('c', 'ช่วงราคา (ต่ำสุด–สูงสุด)', v.length ? Math.max(...v) - Math.min(...v) : null, 'บาท/กก.', 2, v.length ? `${fmt(Math.min(...v), 2)} – ${fmt(Math.max(...v), 2)}` : '') +
      kpiBox('m', `ต้นทุน สศก. ${CY[last]}: ${cname}`, c ? c.cost[last] / 1000 : null, 'บาท/กก.', 2, c ? `ราคา ${fmt(c.price[last] / 1000, 2)} บาท/กก.` : 'สศก. ไม่ได้เผยแพร่') +
      kpiBox('p', `ผลตอบแทนสุทธิ ${CY[last]}`, c ? c.net[last] : null, 'บาท/ตัน', 0, c ? `${(c.net[last] / c.price[last] * 100).toFixed(0)}% ของราคา` : 'ไม่มีข้อมูล', c ? (c.net[last] >= 0 ? 'up' : 'dn') : '');
    $('price-title').textContent = `ราคารายสัปดาห์: ${name}`;
    if (!rows.length) empty($('price'), `ไม่มีราคาในช่วงที่เลือก (ชุดนี้มี พ.ศ. ${all[0][0]}–${all[all.length - 1][0]})`); else {
      const x = rows.map(lab), ma = v.map((_, i) => i >= 7 ? sumv(v.slice(i - 7, i + 1)) / 8 : null);
      Plotly.react($('price'), [
        { x, y: v, mode: 'lines', line: { shape: 'spline', color: C.cyan, width: 2.5 }, fill: 'tozeroy', fillcolor: 'rgba(0,229,255,0.06)', hovertemplate: '%{x}: %{y:,.2f} บาท/กก.<extra></extra>' },
        { x, y: ma, mode: 'lines', line: { shape: 'spline', color: '#fff', width: 1.5, dash: 'dash' }, hovertemplate: 'เฉลี่ย 8 สัปดาห์: %{y:,.2f}<extra></extra>' },
      ], layout({ margin: { l: 10, r: 10, t: 6, b: 30 }, xaxis: axis(null, { nticks: 5, tickangle: 0 }), yaxis: axis('บาท/กก.', { rangemode: 'tozero' }) }), CFG);
    }
    if (S.costView === 'crop') {
      $('cost-title').textContent = `ต้นทุน ราคา ผลตอบแทนต่อตัน: ${cname}`;
      $('cost-sub').textContent = c ? `สศก. หน้า ${c.page} · ${c.note}` : '';
      if (!c) empty($('costbar'), `สศก. ไม่ได้เผยแพร่ต้นทุนของ${cname} — ไม่มีข้อมูล`);
      else Plotly.react($('costbar'), [['ต้นทุน', 'cost', C.magenta], ['ราคา', 'price', C.cyan], ['สุทธิ', 'net', C.ok]].map(([n, key, col]) => ({ type: 'bar', name: n, x: CY.map(String), y: c[key],
        marker: { color: key === 'net' ? c.net.map(z => z >= 0 ? C.ok : C.bad) : col }, hovertemplate: 'พ.ศ. %{x} · ' + n + ': %{y:,.0f} บาท/ตัน<extra></extra>' })),
        layout({ barmode: 'group', bargap: 0.25, showlegend: true, legend: { orientation: 'h', y: 1.0, yanchor: 'bottom', x: 0, font: { color: C.fg2, size: 11 } }, margin: { l: 10, r: 10, t: 26, b: 26 }, xaxis: axis(null, { type: 'category' }), yaxis: axis('บาท/ตัน') }), CFG);
    } else {
      const list = Object.entries(COST).map(([n, z]) => ({ n, m: z.net[last] / z.price[last] * 100, z })).sort((a, b) => b.m - a.m);
      $('cost-title').textContent = 'อัตราผลตอบแทนสุทธิ ปี 2567 ทุกพืช'; $('cost-sub').textContent = `(ราคา − ต้นทุน) ÷ ราคา · ${list.length} พืชที่ สศก. เผยแพร่ · คลิกเพื่อเลือกพืช`;
      Plotly.react($('costbar'), [{ type: 'bar', orientation: 'h', y: list.map(d => d.n), x: list.map(d => d.m), customdata: list.map(d => [d.z.cost[last], d.z.price[last]]),
        marker: { color: list.map(d => d.m < 0 ? C.bad : C.cyan), line: { width: list.map(d => d.n === cname ? 2 : 0), color: '#fff' } },
        hovertemplate: '<b>%{y}</b><br>ต้นทุน %{customdata[0]:,.0f} · ราคา %{customdata[1]:,.0f} บาท/ตัน<br>%{x:.1f}%<extra></extra>' }],
        layout({ margin: { l: 10, r: 10, t: 6, b: 26 }, yaxis: axis(null, { autorange: 'reversed', tickfont: { color: C.fg2, size: 10.5 }, gridcolor: 'rgba(0,0,0,0)', dtick: 1 }), xaxis: axis('%') }), CFG);
      if (!$('costbar').__cb && $('costbar').on) { $('costbar').__cb = true; $('costbar').on('plotly_click', e => { const n = e.points && e.points[0] && e.points[0].y; if (S.costView === 'all' && PROD.includes(n)) setFilter('product', PROD.indexOf(n)); }); }
    }
    calcRefs(); calc();
  }
  function calcRefs() {
    const k = +$('k-crop').value, cname = PROD[k], c = COST[cname], last = CY.length - 1;
    const nat = totals(rowsFor({ year: S.year, product: k, region: ALL, province: -1 })), loc = S.province >= 0 ? totals(rowsFor({ year: S.year, product: k, region: ALL, province: S.province })) : null;
    const pY = loc && ok(loc.yield) ? loc.yield : nat.yield;
    const pname = PRICE_FOR[cname], same = pname ? (D.prices[pname] || []).filter(r => r[0] === S.year) : [], nabc = same.length ? sumv(same.map(r => r[3])) / same.length : null;
    const oaeCost = c ? c.cost[last] * c.yield[last] / 1000 : null, oaePrice = c ? c.price[last] / 1000 : null;
    REF = c ? { yield: S.province >= 0 && ok(pY) ? pY : c.yield[last], price: oaePrice, cost: oaeCost, src: `ผลผลิต${S.province >= 0 && ok(pY) ? P[S.province] + ' ' + S.year : ' สศก. ' + CY[last]} + ราคาและต้นทุน สศก. ${CY[last]}` }
      : { yield: pY, price: nabc, cost: null, src: `ผลผลิต ${scopeLabel()} ${S.year}${ok(nabc) ? ' + ราคา NABC' : ''} · ไม่มีต้นทุนอ้างอิง` };
    const row = (l, v) => `<div><span>${l}</span><b>${v}</b></div>`;
    $('k-ref').innerHTML = row(`ผลผลิตต่อไร่ ${S.province >= 0 ? P[S.province] : 'ทั้งประเทศ'} ${S.year}`, ok(pY) ? fmt(pY, 0) + ' กก./ไร่' : 'ไม่มีข้อมูล') +
      row(`ราคา NABC เฉลี่ย ${S.year}`, ok(nabc) ? fmt(nabc, 2) + ' บาท/กก.' : 'ไม่มีข้อมูล') +
      row(`ราคา สศก. ${CY[last]}`, ok(oaePrice) ? fmt(oaePrice, 2) + ' บาท/กก.' : 'ไม่มีข้อมูล') +
      row(`ต้นทุน สศก. ${CY[last]} ต่อไร่`, ok(oaeCost) ? fmt(oaeCost, 0) + ' บาท/ไร่' : 'ไม่มีข้อมูล') +
      `<div><span>ปุ่มนำค่าอ้างอิงใช้</span><b style="white-space:normal;font-weight:400;color:var(--fg-2)">${REF.src}</b></div>`;
  }
  $('k-use').onclick = () => { if (ok(REF.yield)) $('k-yield').value = Math.round(REF.yield); if (ok(REF.price)) $('k-price').value = REF.price.toFixed(2); if (ok(REF.cost)) $('k-cost').value = Math.round(REF.cost); calc(); };
  function calc() {
    const num = id => $(id).value === '' ? null : +$(id).value;
    const a = num('k-area'), yl = num('k-yield'), c = num('k-cost'), p = num('k-price');
    const cost = ok(a) && ok(c) ? a * c : null, out = ok(a) && ok(yl) ? a * yl : null, rev = ok(out) && ok(p) ? out * p : null, profit = ok(rev) && ok(cost) ? rev - cost : null;
    const beY = ok(cost) && ok(a) && p ? cost / (a * p) : null, beP = ok(cost) && out ? cost / out : null;
    const box = (l, v, u, cls = '') => `<div><span>${l}</span><b class="${cls}">${ok(v) ? fmt(v, u === 'บาท/กก.' ? 2 : 0) + ' ' + u : '–'}</b></div>`;
    $('k-out').innerHTML = box('Total Cost', cost, 'บาท') + box('Total Yield', out, 'กก.') + box('Revenue', rev, 'บาท') +
      box('Profit', profit, 'บาท', !ok(profit) ? '' : profit >= 0 ? 'pos' : 'neg') + box('Break-even Yield', beY, 'กก./ไร่') + box('Break-even Price', beP, 'บาท/กก.');
    if (!ok(beP) || !ok(p)) { empty($('margin'), 'กรอกต้นทุน ผลผลิต ราคา หรือกด “นำค่าอ้างอิงไปใส่”'); return; }
    const m = p - beP, xs = ['ต้นทุน/กก.', 'ราคาขาย', 'ส่วนต่าง/กก.'], ys = [beP, p, m];
    Plotly.react($('margin'), [{ type: 'bar', x: xs, y: ys, text: ys.map(z => fmt(z, 2)), textposition: 'outside', cliponaxis: false, textfont: { color: C.fg, size: 11 },
      marker: { color: [C.magenta, C.cyan, m >= 0 ? C.ok : C.bad] }, hovertemplate: '%{x}: %{y:,.2f} บาท/กก.<extra></extra>' }],
      layout({ bargap: 0.4, margin: { l: 10, r: 10, t: 16, b: 22 }, yaxis: axis('บาท/กก.') }), CFG);
  }

  // =================== province drawer ===================
  let sparkEl = null;
  function renderDetail() {
    const main = $('main'), i = S.province, open = i >= 0;
    if (main.classList.contains('has-detail') !== open) { main.classList.toggle('has-detail', open); setTimeout(resizeAll, 40); }
    if (!open) return;
    const k = crop(), y = S.year;
    const all = byProvince(rowsFor({ year: y, product: k, region: ALL, province: -1 })).filter(d => ok(d.prod) && d.prod > 0);
    const me = all.find(d => d.p === i), pv = totals(rowsFor({ year: y - 1, product: k, region: ALL, province: i }));
    const rankP = me ? [...all].sort((a, b) => b.prod - a.prod).indexOf(me) + 1 : null, rankY = me && ok(me.yield) ? [...all].filter(d => ok(d.yield)).sort((a, b) => b.yield - a.yield).indexOf(me) + 1 : null;
    const crops = byCrop(i, y).slice(0, 5);
    const c = climate(y), e = climate(y, 'era5'), F = factorDefs(), cc = COST[PROD[k]], last = CY.length - 1;
    const r = (l, v) => `<div class="drow"><span>${l}</span><b>${v}</b></div>`;
    $('d-title').textContent = `${P[i]} (${CODE[i]})`;
    $('d-sub').textContent = `${R[i]} · ${PROD[k]} · พ.ศ. ${y}`;
    $('d-body').innerHTML =
      `<div class="dsec"><h3>การผลิต: ${PROD[k]}</h3>${me ? r('ผลผลิต', `${fmt(me.prod)} ตัน`) + r('อันดับผลผลิต', `${rankP} / ${all.length} จังหวัด`) + r('ผลผลิตต่อไร่', `${fmt(me.yield, 0)} กก./ไร่ ${rankY ? `(อันดับ ${rankY})` : ''}`) +
        r('เนื้อที่เพาะปลูก', `${fmt(me.plant)} ไร่`) + r('เทียบปีก่อน', ok(pv.prod) && pv.prod > 0 ? `${((me.prod / pv.prod - 1) * 100).toFixed(1)}%` : 'ไม่มีข้อมูล') : '<div class="empty-note">จังหวัดนี้ไม่มีการผลิตพืชนี้ในปีที่เลือก</div>'}
        <div class="spark" id="d-spark"></div></div>` +
      `<div class="dsec"><h3>พืชหลักของจังหวัด ${y}</h3>${crops.length ? crops.map(d => r(PROD[d.k], `${short(d.prod)} ตัน`)).join('') : '<div class="empty-note">ไม่มีข้อมูล</div>'}</div>` +
      `<div class="dsec"><h3>สภาพอากาศ ${y}</h3>` +
        r(`ฝนทั้งปี (${c.label})`, ok(c.rain[i]) ? `${fmt(c.rain[i])} มม.` + (c.src === 'hii' && D.provNormal[i] ? ` <span class="tag ${c.rain[i] < D.provNormal[i] ? 'w' : ''}">${((c.rain[i] / D.provNormal[i] - 1) * 100).toFixed(0)}% จากปกติ</span>` : '') : 'ไม่มีข้อมูล') +
        r(`ฝน พ.ค.–ต.ค. (${c.label})`, ok(c.season[i]) ? `${fmt(c.season[i])} มม.` : 'ไม่มีข้อมูล') +
        r(`อุณหภูมิเฉลี่ย (${ok(c.temp[i]) ? c.label : 'ERA5'})`, ok(c.temp[i]) ? `${c.temp[i].toFixed(1)} °C` : ok(e.temp[i]) ? `${e.temp[i].toFixed(1)} °C` : 'ไม่มีข้อมูล') +
        r('สูงสุด / ต่ำสุดของปี', ok(c.tmax[i]) ? `${c.tmax[i]} / ${c.tmin[i]} °C` : ok(e.tmax[i]) ? `${e.tmax[i]} / ${e.tmin[i]} °C (ERA5)` : 'ไม่มีข้อมูล') + `</div>` +
      `<div class="dsec"><h3>ปัจจัยการผลิต</h3>` +
        r('พื้นที่โครงการชลประทาน', D.irr[i] ? `${fmt(D.irr[i][4], 1)}% ของพื้นที่` : 'ไม่มีข้อมูล') + r('ใช้เครื่องจักร', ok(F.mech.get(i)) ? `${F.mech.get(i).toFixed(1)}% ของผู้ถือครอง` : 'ไม่มีข้อมูล') +
        r('ใช้ปุ๋ย', ok(D.fert[i]) ? `${D.fert[i].toFixed(1)}%` : 'ไม่มีข้อมูล') + r(`ดิน S1+S2 (${PROD[k]})`, ok(F.soil.get(i)) ? `${F.soil.get(i).toFixed(1)}%` : 'ไม่มีข้อมูล') +
        r('น้ำท่วม 2562 (ปภ.)', ok(F.flood.get(i)) ? `${fmt(F.flood.get(i))} ไร่` : '0 / ไม่มีรายงาน') + r('ภัยแล้ง 2562 (ปภ.)', D.drought2562[i] ? `${D.drought2562[i]} หมู่บ้าน` : '0 / ไม่มีรายงาน') +
        r('ประสบภัย ใน/นอกเขตชลฯ (กสก.)', D.doae[i] ? `${short(D.doae[i][0] + D.doae[i][1])} / ${short(D.doae[i][2] + D.doae[i][3])} ไร่` : 'ไม่มีข้อมูล') + `</div>` +
      `<div class="dsec"><h3>เศรษฐศาสตร์ (ประมาณการ)</h3>${cc && me && ok(me.yield) ? r('รายได้/ไร่ (ราคา สศก. 2567)', `${fmt(me.yield * cc.price[last] / 1000)} บาท`) + r('ต้นทุน/ไร่ (ต้นทุน สศก./ตัน × ผลผลิตจังหวัด)', `${fmt(me.yield * cc.cost[last] / 1000)} บาท`) +
        r('กำไรประมาณการ/ไร่', `${fmt(me.yield * cc.net[last] / 1000)} บาท`) : '<div class="empty-note">ไม่มีต้นทุน สศก. ของพืชนี้หรือไม่มีผลผลิต</div>'}
        <button class="btn ghost" id="d-calc" type="button">ใช้ผลผลิตจังหวัดนี้ในเครื่องคำนวณ →</button></div>`;
    $('d-calc').onclick = () => { $('k-crop').value = String(k); ['k-yield', 'k-cost', 'k-price'].forEach(id => $(id).value = ''); setTab('economics'); $('k-use').click(); };
    const ser = years.map(yy => ({ y: yy, ...totals(rowsFor({ year: yy, product: k, region: ALL, province: i })) })).filter(d => ok(d.yield));
    if (ser.length) Plotly.react($('d-spark'), [{ x: ser.map(d => d.y), y: ser.map(d => d.yield), mode: 'lines+markers', line: { color: C.cyan, width: 2, shape: 'spline' }, marker: { size: ser.map(d => d.y === y ? 9 : 4), color: ser.map(d => d.y === y ? C.magenta : C.cyan) }, hovertemplate: '%{x}: %{y:,.0f} กก./ไร่<extra></extra>' }],
      layout({ margin: { l: 4, r: 4, t: 4, b: 18 }, xaxis: axis(null, { dtick: 4, tickfont: { size: 10, color: C.muted } }), yaxis: axis(null, { tickfont: { size: 10, color: C.muted } }) }), CFG);
  }
  function byCrop(i, y) { const g = {}; D.ag.forEach(r => { if (r[0] === y && r[2] === i && ok(r[5])) g[r[1]] = (g[r[1]] || 0) + r[5]; }); return Object.entries(g).map(([k, prod]) => ({ k: +k, prod })).sort((a, b) => b.prod - a.prod); }

  // ---------- render ----------
  function render() {
    $('f-product').value = String(S.product); $('f-year').value = String(S.year); $('f-region').value = S.region; $('f-province').value = String(S.province); $('f-metric').value = S.metric;
    if (!LAYERS[S.tab].some(([k]) => k === S.layer[S.tab])) S.layer[S.tab] = LAYERS[S.tab][0][0];
    drawBadges(); drawLayerButtons(); renderDetail();
    if (S.tab === 'overview') renderOverview(); else if (S.tab === 'climate') renderClimate(); else if (S.tab === 'factors') renderFactors(); else renderEconomics();
    mapForTab();
    requestAnimationFrame(resizeAll);
  }
  syncCrops();
  const start = (location.hash || '').replace('#', '');
  setTab(TABS.includes(start) ? start : 'overview');
})();
