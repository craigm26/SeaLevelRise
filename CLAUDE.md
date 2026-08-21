# Context for Claude Code

Read this first. It's the handoff note for whoever (or whatever) picks this repo up next.

## What this is

A screening-level flood-risk data package for downtown Miami — Brickell through the CBD to
Edgewater — plus a docs site and an interactive 3D visualiser. It was assembled to answer a
public argument about whether Miami's sea level exposure is "manageable," and it ended up
producing several findings that contradicted the assumptions the project started with.

Two static pages, no build step, no framework:

- `index.html` — data catalogue, method, provenance audit, insurer-exit analysis. Charts are
  hand-rolled SVG reading from `data.json`. No chart library.
- `viewer.html` — Three.js 3D visualiser reading the payloads in `viz/`. Three.js is vendored,
  not CDN-loaded.

## Immediate next steps

1. `git push -u origin main` — the repo is already initialised and committed.
2. Deploy to Cloudflare Pages. See `DEPLOY.md`. Framework preset **None**, empty build command,
   output directory `/`.

That's it. There is nothing to install or compile.

## Non-negotiables if you modify this

**Units.** The DEM is in **metres**; every tide, scenario, and elevation table is in **feet**.
Both are NAVD88. The viewer converts once, at the boundary, in `Y()`. Downtown Miami has about
ten feet of usable relief, so a unit slip produces a plausible-looking wrong answer rather than
an obvious one. This has already bitten the project once — an early draft assumed MHHW was
−0.16 ft NAVD88 when the published value is **+0.23**.

**Provenance is the product.** The entire point of this package is that inference is visible.
2.2% of storm drain segments have a measured diameter and 0.1% have measured inverts; 77% of
buildings have no locally-observed floor elevation. Anything inferred renders hatched or dimmed
and carries a count in the legend. If you add a layer, add its provenance class too. A confident
map built on 98% inference is worse than no map.

**Don't blend the two insurance markets.** Florida's wind market is recovering (Citizens
Miami-Dade down 69% since 2022) while flood cost pressure rises under NFIP Risk Rating 2.0.
They move in opposite directions. A single "fragility index" would misrepresent both.

## The findings that shaped the build

1. **54.8% of drainage structures with a known bottom sit below the wet-season median water
   table.** The storm system does not start empty — it starts as pressure relief for the
   Biscayne aquifer. Any model with full capacity at t=0 is wrong from the first timestep.
2. **There is no surface outfall inside the study area.** The nearest real discharge point is
   4 km away. Downtown drains *down*, through 2,594 Class V injection wells, median depth
   120 ft. Rejected infiltration is co-dominant with tailwater locking. Findings 1 and 2 are
   the same finding, and both are groundwater problems.
3. **Virginia Key runs +0.50 ft above global mean sea level at 2100 — and 0.33 ft of that is
   the land sinking.** Scenario-independent, ~1.05 mm/yr. This is why quoting global numbers
   for Miami understates it.
4. **At 2050 the emissions scenario barely matters.** All five AR6 SSP medians span 0.85–1.03 ft
   — less than the spread within any single scenario. They diverge after 2070. An emissions
   toggle showing visible mid-century difference overstates the science.
5. **No insurer has ever cited sea level rise as a reason for leaving a market.** Searched six
   ways, including the Senate Budget Committee's 249-million-policy-record investigation. Every
   documented US exit 2018–2026 traces to a realised loss year, rate-approval friction, or
   litigation. This is the model's prediction, not a gap: one-year contracts mean a slow hazard
   gets quietly repriced, never announced.

## What the visualiser actually models

Bathtub-plus-drainage-capacity. **Not** MIKE, HEC-RAS, or XPSWMM. Specifically:

- Tidal stage = MHHW (+0.23 ft NAVD88) + SLR slider + king tide (HAT, +0.97 ft over MHHW).
- Water table = observed seasonal median, raised with sea level at a **0.85 coupling
  coefficient — a screening assumption, not a calibrated value**. If you improve one thing,
  improve this.
- Storm ponding = Atlas 14 24-hour depth less surviving drainage capacity, where capacity
  shrinks as the water table nears the surface. Uniform depth; does not route downhill.
- **Pipe elevations are inferred** — grade minus an assumed 5 ft cover — because the county's
  invert field is populated on 8 of 6,612 segments.

## Where the data lives

Small analysis outputs and all the notes files are in `data/`. The **large** source files
(58 MB 1 m DEM, 52 MB of parcel/footprint/drainage GeoJSON) are deliberately **not** in git —
they're in the Drive folder linked from `README.md`, and `scripts/fetch_large_datasets.sh`
rebuilds the DEM mosaic from USGS.

`data/README.md` is the authoritative data dictionary. `data/notes/` holds the method write-ups;
`NOTES_first_floor_elevations.md` and `NOTES_outfalls.md` are the two most load-bearing.

## Known gaps, with routes

- **Elevation certificates** (City of Miami floodplain management / Miami-Dade RER) would
  convert 9,636 hatched buildings to solid. Highest-value acquisition remaining.
- **Storm drain inverts** — full Cartegraph export from City of Miami RPW; MS4 outfall
  inventory from RER-DERM under FDEP permit FLS000003.
- **Permanently closed:** NFIP full-risk premium in dollars (no such field exists in any public
  API) and NFIP record counts (`$inlinecount` 503s under a ZIP filter).
- `ASSESSED_VAL_CUR` is null service-wide in the Property Appraiser services — use `PRICE_1`
  (last sale) with a provenance flag if you need exposure value.

## Traps that already cost time

- An ArcGIS Online search for "outfall Miami" returns **Miami, Oklahoma** (longitude −94.9).
- USGS `waterservices.usgs.gov/nwis/gwlevels/` was decommissioned in early 2026 — use the
  `field-measurements` collection on `api.waterdata.usgs.gov`.
- OpenFEMA v2 was frozen 2026-06-01 and is removed after 2026-10-15. Migrate to v3.
- Whitespace-only strings (`" "`) are the null placeholder throughout Miami-Dade's GIS. Treating
  them as populated inflates the completeness audit from 2.2% to 100%.
