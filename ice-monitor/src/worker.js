/**
 * SeaLevelRise — upstream ice monitor.
 *
 * Watches the physical drivers of the high-end sea level tail that the Miami
 * package already publishes (AR6 SSP5-8.5 low confidence, p95 = 8.39 ft at
 * Virginia Key in 2100). That tail is driven almost entirely by marine ice
 * sheet instability in West Antarctica, so this worker exists to answer one
 * question: is there observational evidence that the tail is being realised?
 *
 * Design rule inherited from the parent project: PROVENANCE IS THE PRODUCT.
 * Every indicator carries its own observation date, retrieval time, and the lag
 * between them. A source we cannot reach is rendered as an explicit gap, never
 * silently omitted. The failure to obtain a number is itself a published fact.
 *
 * The latency trap this is built around: the indicators that update fastest
 * (sea ice extent, daily) contribute NOTHING to sea level, while the indicator
 * that matters most (ice sheet mass, GRACE-FO) is monthly and gated behind
 * authentication. Any dashboard that puts those side by side without saying so
 * is lying by layout. Each record therefore carries `raisesSeaLevel`.
 */

const UA = 'SeaLevelRise-IceMonitor/1.0 (+https://sealevelrise.pages.dev)';
const KEY = 'snapshot:v1';
const HIST = 'history:v1';
const HIST_MAX = 720; // ~6 months at 6-hourly

const iso = (d) => new Date(d).toISOString();
const dayDiff = (a, b) => Math.floor((new Date(a) - new Date(b)) / 86400000);

async function get(url, opts = {}) {
  const r = await fetch(url, {
    headers: { 'User-Agent': UA, ...(opts.headers || {}) },
    cf: { cacheTtl: 300, cacheEverything: false },
  });
  if (!r.ok && r.status !== 206) throw new Error(`HTTP ${r.status} from ${url}`);
  return r.text();
}

/* ------------------------------------------------------------------ *
 * NSIDC Sea Ice Index — daily extent, both poles.
 * Fetched by HTTP range: the full CSV is ~1.8 MB and we need the tail.
 * ------------------------------------------------------------------ */
function parseClimatology(txt) {
  const out = {};
  for (const line of txt.split('\n')) {
    const p = line.split(',').map((s) => s.trim());
    if (p.length < 3 || !/^\d+$/.test(p[0])) continue;
    out[parseInt(p[0], 10)] = { mean: parseFloat(p[1]), sd: parseFloat(p[2]) };
  }
  return out;
}

function doyOf(y, m, d) {
  const start = Date.UTC(y, 0, 0);
  return Math.floor((Date.UTC(y, m - 1, d) - start) / 86400000);
}

async function seaIce(pole, now) {
  const P = pole === 'north' ? 'N' : 'S';
  const base = `https://noaadata.apps.nsidc.org/NOAA/G02135/${pole}/daily/data`;
  const dailyUrl = `${base}/${P}_seaice_extent_daily_v4.0.csv`;
  const climUrl = `${base}/${P}_seaice_extent_climatology_1981-2010_v4.0.csv`;

  const [tail, clim] = await Promise.all([
    get(dailyUrl, { headers: { Range: 'bytes=-4000' } }),
    get(climUrl),
  ]);

  let last = null;
  for (const line of tail.split('\n')) {
    const p = line.split(',').map((s) => s.trim());
    if (p.length < 4) continue;
    const [y, m, d, e] = [p[0], p[1], p[2], p[3]].map(Number);
    if (!y || !m || !d || !isFinite(e) || e <= 0) continue;
    last = { y, m, d, extent: e };
  }
  if (!last) throw new Error('no parseable row in NSIDC tail');

  const c = parseClimatology(clim)[doyOf(last.y, last.m, last.d)];
  const observed = `${last.y}-${String(last.m).padStart(2, '0')}-${String(last.d).padStart(2, '0')}`;
  const anomaly = c ? +(last.extent - c.mean).toFixed(3) : null;
  const sigma = c && c.sd ? +((last.extent - c.mean) / c.sd).toFixed(2) : null;

  return {
    id: `seaice_${pole}`,
    group: 'Sea ice (context, not sea level)',
    label: `${pole === 'north' ? 'Arctic' : 'Antarctic'} sea ice extent`,
    value: last.extent,
    unit: 'million km²',
    observed,
    lagDays: dayDiff(now, observed),
    anomaly,
    sigma,
    anomalyNote: c
      ? `${anomaly > 0 ? '+' : ''}${anomaly} vs 1981–2010 mean for this day (${sigma}σ)`
      : 'no climatology for this day-of-year',
    raisesSeaLevel: false,
    caveat:
      'Sea ice is floating. Its loss adds nothing directly to sea level. It matters here only ' +
      'indirectly: less sea ice means ocean swell reaches ice shelf fronts that buttress ' +
      'grounded ice. Do not read this as a sea level signal.',
    cadence: 'daily',
    expectedLagDays: 7,
    source: { name: 'NSIDC Sea Ice Index v4.0', url: dailyUrl },
  };
}

/* ------------------------------------------------------------------ *
 * NOAA CPC — Niño 3.4 SST anomaly.
 * Monthly by construction. ONI proper is a 3-month running mean, so it can
 * never be "live"; presenting it as such would be its own small lie.
 * ------------------------------------------------------------------ */
async function nino34(now) {
  const url =
    'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/detrend.nino34.ascii.txt';
  const txt = await get(url);
  let last = null;
  for (const line of txt.split('\n')) {
    const p = line.trim().split(/\s+/);
    if (p.length < 5 || !/^\d{4}$/.test(p[0])) continue;
    last = { y: +p[0], m: +p[1], anom: parseFloat(p[4]) };
  }
  if (!last) throw new Error('no parseable Niño 3.4 row');

  const observed = `${last.y}-${String(last.m).padStart(2, '0')}-01`;
  const a = last.anom;
  const phase =
    a >= 1.5 ? 'strong El Niño' :
    a >= 1.0 ? 'moderate El Niño' :
    a >= 0.5 ? 'weak El Niño' :
    a <= -1.5 ? 'strong La Niña' :
    a <= -1.0 ? 'moderate La Niña' :
    a <= -0.5 ? 'weak La Niña' : 'neutral';

  return {
    id: 'nino34',
    group: 'Ocean forcing',
    label: 'Niño 3.4 SST anomaly',
    value: a,
    unit: '°C',
    observed,
    lagDays: dayDiff(now, observed),
    phase,
    raisesSeaLevel: null,
    caveat:
      'ENSO does not act on Antarctica with a single sign. During strong El Niño, Amundsen Sea ' +
      'ice shelves tend to GAIN height from increased snowfall while LOSING mass to warmer ' +
      'Circumpolar Deep Water at the base. A dashboard built on altimetric height would show ' +
      'those shelves thickening during exactly the episodes that are thinning them. ' +
      'See Paolo et al., Nature Geoscience 2018 — verify before citing.',
    cadence: 'monthly (ONI is a 3-month running mean and cannot be live)',
    expectedLagDays: 62,
    source: { name: 'NOAA CPC detrended Niño 3.4', url },
  };
}

/* ------------------------------------------------------------------ *
 * NOAA CO-OPS — Virginia Key. The downstream end of the whole chain, and the
 * only indicator here measured at the place the parent project is about.
 * ------------------------------------------------------------------ */
async function virginiaKey(now) {
  const url =
    'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&station=8723214' +
    '&product=water_level&datum=NAVD&units=english&time_zone=gmt&format=json' +
    '&application=SeaLevelRise-IceMonitor';
  const j = JSON.parse(await get(url));
  const d = j?.data?.[0];
  if (!d) throw new Error('no CO-OPS observation returned');
  const observed = d.t.replace(' ', 'T') + ':00Z';

  return {
    id: 'virginia_key_wl',
    group: 'Downstream — Miami',
    label: 'Virginia Key observed water level',
    value: +parseFloat(d.v).toFixed(3),
    unit: 'ft NAVD88',
    observed,
    lagDays: dayDiff(now, observed),
    raisesSeaLevel: true,
    reference: { MHHW: 0.23, HAT: 1.2, minorFlood: 1.92, moderateFlood: 2.89, majorFlood: 4.12 },
    caveat:
      'A single six-minute observation, dominated by tide and weather. It is not a sea level ' +
      'trend and must never be read as one. It is here to close the loop: this is the gauge ' +
      'every scenario in the parent package is referenced to.',
    cadence: '6-minutely',
    expectedLagDays: 1,
    source: { name: 'NOAA CO-OPS station 8723214', url },
  };
}

/* ------------------------------------------------------------------ *
 * GRACE-FO — the number that actually matters, and the one we cannot get.
 * Published as a declared gap rather than omitted. This mirrors the parent
 * project's treatment of NFIP full-risk premium: a stated impossibility is
 * more useful than a quiet absence.
 * ------------------------------------------------------------------ */
function graceGap() {
  return {
    id: 'grace_fo_mass',
    group: 'Ice sheet mass (the number that matters)',
    label: 'Greenland & Antarctica mass anomaly',
    value: null,
    unit: 'Gt',
    observed: null,
    lagDays: null,
    status: 'unavailable',
    raisesSeaLevel: true,
    caveat:
      'GRACE-FO mascon solutions are the only direct measurement of ice sheet MASS, and mass is ' +
      'what raises sea level. They are distributed through NASA PO.DAAC behind Earthdata Login. ' +
      'There is no anonymous endpoint, so this monitor cannot show the single most important ' +
      'indicator it tracks. That is a real limitation of this dashboard, not of the data: the ' +
      'measurement exists and is excellent. Supply Earthdata credentials to close this gap. ' +
      'Native latency is roughly 1–2 months regardless.',
    cadence: 'monthly, 1–2 month processing lag',
    source: { name: 'NASA PO.DAAC GRACE-FO mascons (auth required)', url: 'https://podaac.jpl.nasa.gov/' },
  };
}

/* ------------------------------------------------------------------ *
 * Tripwires — stated in advance, arguable on purpose.
 *
 * These are NOT consensus scientific thresholds. They are this project's
 * pre-registered positions on what would count as evidence, published before
 * the fact so they cannot be moved afterwards. Each says what it would mean
 * and, just as importantly, what it would not.
 * ------------------------------------------------------------------ */
function tripwires(byId) {
  const wires = [
    {
      id: 'tw_antarctic_seaice',
      label: 'Antarctic sea ice extent below −2σ',
      threshold: -2,
      unit: 'σ vs 1981–2010',
      current: byId.seaice_south?.sigma ?? null,
      test: (v) => v !== null && v <= -2,
      means:
        'Sustained multi-year excursions expose more ice shelf front to open-ocean swell, which ' +
        'removes buttressing from grounded ice that does raise sea level.',
      doesNotMean:
        'Not sea level rise. Sea ice is floating and its melt adds nothing directly. A single ' +
        'day below threshold is weather, not a trend.',
    },
    {
      id: 'tw_enso_strong',
      label: 'Niño 3.4 at or above +1.5 °C (strong El Niño)',
      threshold: 1.5,
      unit: '°C',
      current: byId.nino34?.value ?? null,
      test: (v) => v !== null && v >= 1.5,
      means:
        'Elevated basal melt risk for Amundsen Sea ice shelves via warm Circumpolar Deep Water, ' +
        'the mechanism most directly tied to the marine ice sheet instability behind the p95 tail.',
      doesNotMean:
        'Not an ice loss measurement. Surface snowfall rises at the same time, so shelf HEIGHT ' +
        'may increase while mass falls. The two signals oppose each other.',
    },
    {
      id: 'tw_vk_minor_flood',
      label: 'Virginia Key at or above NOAA minor flood threshold',
      threshold: 1.92,
      unit: 'ft NAVD88',
      current: byId.virginia_key_wl?.value ?? null,
      test: (v) => v !== null && v >= 1.92,
      means: 'Downtown Miami is in a high-tide flooding event at this instant.',
      doesNotMean:
        'Nothing about ice sheets or long-term sea level. This is tide plus weather, and it is ' +
        'included to close the loop to the place the parent package is about.',
    },
    {
      id: 'tw_mass_loss',
      label: 'Ice sheet mass loss acceleration',
      threshold: null,
      unit: 'Gt/yr²',
      current: null,
      test: () => null,
      means: 'The decisive indicator for the high-end tail.',
      doesNotMean: '',
      blocked:
        'Cannot be evaluated. GRACE-FO requires NASA Earthdata authentication, so the most ' +
        'important tripwire in this list is unarmed. Stated rather than dropped.',
    },
  ];
  return wires.map((w) => {
    const state = w.blocked ? 'unarmed' : w.test(w.current) ? 'tripped' : 'not tripped';
    const { test, ...rest } = w;
    return { ...rest, state };
  });
}

async function build(env) {
  const now = new Date();
  const tasks = [
    ['seaice_north', () => seaIce('north', now)],
    ['seaice_south', () => seaIce('south', now)],
    ['nino34', () => nino34(now)],
    ['virginia_key_wl', () => virginiaKey(now)],
  ];

  const indicators = [];
  for (const [id, fn] of tasks) {
    try {
      const rec = await fn();
      // Staleness is judged against each source's OWN cadence. A flat threshold
      // would mark a monthly series permanently late and train the reader to
      // ignore the badge -- the opposite of what it is for.
      const overdue = rec.lagDays > (rec.expectedLagDays ?? 7);
      indicators.push({ ...rec, status: overdue ? 'stale' : 'ok', retrieved: iso(now) });
    } catch (e) {
      // A failed fetch is published, not swallowed. Silent omission would make
      // the wall look complete when it is not.
      indicators.push({
        id, status: 'error', error: String(e.message || e), retrieved: iso(now),
        label: id, value: null, observed: null, lagDays: null,
      });
    }
  }
  indicators.push({ ...graceGap(), retrieved: iso(now) });

  const byId = Object.fromEntries(indicators.map((i) => [i.id, i]));
  return {
    generated: iso(now),
    context: {
      question:
        'Is there observational evidence that the high-end sea level tail is being realised?',
      tail:
        'IPCC AR6 SSP5-8.5 low confidence at Virginia Key: 3.43 ft median at 2100, p95 8.39 ft. ' +
        'That p95 is driven almost entirely by marine ice sheet instability in West Antarctica.',
      latencyWarning:
        'What updates fastest here contributes least to sea level. What matters most (ice sheet ' +
        'mass) is monthly and currently unavailable. Read the lag on every tile.',
    },
    indicators,
    tripwires: tripwires(byId),
    sourceHealth: {
      ok: indicators.filter((i) => i.status === 'ok').length,
      stale: indicators.filter((i) => i.status === 'stale').length,
      error: indicators.filter((i) => i.status === 'error').length,
      unavailable: indicators.filter((i) => i.status === 'unavailable').length,
    },
  };
}

async function refresh(env) {
  const snap = await build(env);
  await env.ICE.put(KEY, JSON.stringify(snap));
  // Keep a rolling series so revisions are visible. Upstream products get
  // reprocessed; showing that is a feature, not noise.
  try {
    const prev = JSON.parse((await env.ICE.get(HIST)) || '[]');
    prev.push({
      t: snap.generated,
      v: Object.fromEntries(snap.indicators.filter((i) => i.value !== null).map((i) => [i.id, i.value])),
    });
    await env.ICE.put(HIST, JSON.stringify(prev.slice(-HIST_MAX)));
  } catch (_) { /* history is best-effort; never fail a refresh over it */ }
  return snap;
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Cache-Control': 'public, max-age=300',
};

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(refresh(env));
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });

    if (url.pathname === '/api/ice/history') {
      const h = (await env.ICE.get(HIST)) || '[]';
      return new Response(h, { headers: { 'Content-Type': 'application/json', ...CORS } });
    }

    if (url.pathname === '/api/ice/refresh') {
      const snap = await refresh(env);
      return new Response(JSON.stringify(snap, null, 1), {
        headers: { 'Content-Type': 'application/json', ...CORS, 'Cache-Control': 'no-store' },
      });
    }

    // Default: serve the cached snapshot. Build on demand only if the cron has
    // never run, so a cold start never shows an empty wall.
    let body = await env.ICE.get(KEY);
    if (!body) body = JSON.stringify(await refresh(env));
    return new Response(body, { headers: { 'Content-Type': 'application/json', ...CORS } });
  },
};
