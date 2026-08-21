# SeaLevelRise — downtown Miami flood risk

A screening-level, provenance-tagged dataset and interactive 3D visualiser for combined
rainfall and sea-level flood risk in downtown Miami (Brickell → CBD → Edgewater), plus a
stated account of where the public record runs out.

**Data folder:** https://drive.google.com/drive/folders/1sJkjULZLFaTLHJrNBzs_BzJ0kvTjMNbL

| | |
|---|---|
| `index.html` | Data catalogue, method, provenance audit, sea-level scenarios, insurer-exit analysis |
| `viewer.html` | **3D visualiser** — LiDAR terrain, Biscayne aquifer, drainage, injection wells, buildings |
| `CLAUDE.md` | Handoff context — read this before modifying anything |
| `DEPLOY.md` | Push and Cloudflare Pages steps |

Static, no build step, no framework. Three.js is vendored. `npx wrangler pages deploy .`

---

## The numbers that anchor everything

| Quantity | Value |
|---|---|
| MHHW, Virginia Key | **+0.23 ft NAVD88** |
| HAT — the honest king tide | **+1.20 ft NAVD88** (MHHW + 0.97) |
| Observed maximum — Irma, 10 Sep 2017 | **+3.80 ft NAVD88** |
| NOAA minor / moderate / major thresholds | **1.92 / 2.89 / 4.12 ft NAVD88** |
| Building ground elevation | median **9.58**, p5 **2.94** ft NAVD88 |
| Water table | dry **0.38**, wet **0.84**, p95 **1.86** ft NAVD88 |
| 100-yr 24-hr rainfall | **14.5 in** |

**Sea level at Virginia Key, ft above ~2005:**

| | 2050 | 2100 |
|---|---|---|
| NOAA 2022 Intermediate | 1.05 | 3.64 |
| NOAA 2022 Intermediate-High | 1.25 | 5.25 |
| IPCC AR6 SSP2-4.5 | 0.95 [0.74–1.23] | 2.34 [1.79–3.17] |
| IPCC AR6 SSP5-8.5 | 1.03 [0.81–1.33] | 3.01 [2.37–4.02] |
| AR6 SSP5-8.5 low confidence | 1.06 [0.80–1.59] | 3.43 [2.37–5.71], p95 **8.39** |

NOAA's 2005 baseline and AR6's 1995–2014 mean differ by about two millimetres. They plot on
one axis with no correction.

---

## Seven findings

**1. Over half the drainage is underwater before it rains.** Cross-referencing 3,034 surveyed
structure elevations against 14,841 groundwater observations: **54.8% of structures with a
known bottom sit below the wet-season median water table**; 51.2% below even the dry-season
median. They relieve aquifer pressure rather than accepting inlet flow. Any model that treats
the storm system as available capacity at t=0 is wrong from the first timestep.

**2. Downtown doesn't drain to the bay — it drains down.** No surface outfall exists inside the
study area; the nearest real discharge point is 4 km away. Downtown discharges through **2,594
FDEP Class V injection wells**, median depth 120 ft, into the Biscayne aquifer. Rejected
infiltration is co-dominant with tailwater locking, which makes findings 1 and 2 the same
finding — and both groundwater problems rather than pipe problems.

**3. The pipe-capacity layer can't be built honestly from county data.** Of 6,612 pipe
segments: **2.2% carry a diameter, 0.1% carry inverts, 0% carry depth.** The county's outfall
`ELEVATION` field is 0.0% populated. What does exist is **3,034 surveyed rim elevations, 2,590
explicitly NAVD88** — the only real vertical control in the drainage layer.

**4. 77% of buildings have no measurable floor elevation.** 9,636 of 12,479 sit in FEMA zone X,
where no elevation certificate is required, so fewer than twenty usable local observations
exist for that whole population. 69.5% of downtown buildings are pre-FIRM. **The
unmeasured-elevation wedge and the uninsured-loss wedge are the same buildings.**

**5. Virginia Key runs +0.50 ft above global mean at 2100 — and 0.33 ft of that is the land
sinking**, about 1.05 mm/yr, scenario-independent. Because the excess is near-constant in
absolute terms it is proportionally *largest under successful mitigation*: +41% on top of
SSP1-1.9, only +20% on top of SSP5-8.5. Quoting global numbers for Miami understates it.

**6. At 2050 the emissions scenario barely matters.** All five AR6 SSP medians span 0.85–1.03
ft — less than the spread within any single scenario. They diverge after 2070. Before then the
uncertainty lives in the ice sheets, not the emissions pathway.

**7. No insurer has ever cited sea level rise as a reason for leaving a market.** Searched six
independent ways, including the Senate Budget Committee's 2024 investigation covering **249
million policy records from ~24 insurers**. Every documented US exit 2018–2026 traces to a
realised loss year, rate-approval friction, or litigation. This is the model's prediction, not
a gap in the evidence: one-year contracts mean a slow hazard gets quietly repriced, never
announced. Over the exact period sea level rise became most visible, Citizens' Miami-Dade book
fell **69%** — private carriers taking risk *back* in the most exposed large county in America.

---

## Repository layout

```
index.html              docs + charts (hand-rolled SVG, no chart library)
viewer.html             3D visualiser (Three.js, WebGL)
data.json               chart payloads for index.html
viz/                    browser payloads for the 3D visualiser (~2.3 MB)
  terrain.png/.json     280×478 heightmap, R = high byte, G = low byte
  buildings.json        12,479 footprints + floor elevation + provenance class
  pipes.json            6,620 drain segments
  structures.json       7,235 catch basins / manholes / drainage wells
  rims.json             3,054 surveyed rim + bottom elevations
  wells.json            2,532 Class V injection wells
  zones.json            142 FEMA flood-zone rings
  groundwater.json      31 USGS sites + seasonal water-table statistics
data/
  README.md             authoritative data dictionary
  notes/                method write-ups — read NOTES_first_floor_elevations.md first
  tide/                 datums, extremes, NOAA 2022 + IPCC AR6 scenarios, HTF projections
  rainfall/             NOAA Atlas 14 depth-duration-frequency
  buildings/            floor-elevation summary by ZIP × zone
  drainage/             attribute-completeness audit, groundwater well inventory
  insurance/            Citizens PIF, RR2.0 bands, NFIP claims, 59-row insurer-exit timeline
scripts/
  fetch_large_datasets.sh   rebuilds the 1 m DEM mosaic from USGS
  derive_ffe.py             the first-floor-elevation derivation
  build_viz_payloads.py     regenerates everything in viz/
.github/workflows/deploy.yml   optional CI deploy (disabled by default)
```

The **large** source files — the 58 MB 1 m DEM and ~52 MB of parcel, footprint, and drainage
GeoJSON — are deliberately not in git. They're in the Drive folder, and the scripts rebuild
the derived products from them.

## Coordinates and units

Horizontal **EPSG:26917** (UTM 17N), origin `578681, 2848232`, extent 4,561 × 7,781 m.
Vertical **NAVD88**. The DEM is in **metres**; every tide, scenario, and elevation table is in
**feet**. Convert once, at the boundary. In a city with ten feet of relief a unit slip produces
a plausible-looking wrong answer rather than an obvious one.

## What the visualiser models

Bathtub-plus-drainage-capacity — **not** MIKE, HEC-RAS, or XPSWMM.

- **Tidal stage** = MHHW + the sea level rise slider + king tide if enabled.
- **Water table** = observed seasonal median, raised with sea level at a **0.85 coupling
  coefficient — a screening assumption, not a calibrated value.**
- **Storm ponding** = Atlas 14 24-hour depth less surviving drainage capacity, where capacity
  shrinks as the water table nears the surface. Uniform; does not route downhill.
- **Pipe elevations are inferred** — grade minus an assumed 5 ft cover.

Toggle ground opacity down to see the aquifer sitting a few feet below the surface with the
drainage network already inside it. That view is the point of the whole build.

## Sources

USGS 3DEP and NWIS · NOAA CO-OPS, Atlas 14, and the 2022 Sea Level Rise Technical Report ·
IPCC AR6 WG1 Chapter 9 via Zenodo (`10.5281/zenodo.6382554`) · FEMA NFHL and OpenFEMA ·
Miami-Dade County GIS and Property Appraiser · City of Miami RPW · FDEP UIC · Citizens
Property Insurance · FLOIR and FIGA · California Department of Insurance and the CA FAIR Plan.

Every derived file carries its own provenance columns or a notes file. All source data is public.

## Disclaimer

This is a screening-level visualisation and documentation project. It is not an engineered
hydraulic model, and nothing in it is a substitute for a site-specific flood study, an
elevation certificate, or professional engineering or insurance advice.
