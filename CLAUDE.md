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

## Status as of 2026-08-20

Live at **https://sealevelrise.pages.dev** (Cloudflare Pages, direct upload — pushing to
GitHub does NOT redeploy; run wrangler by hand). Repo is pushed. Since the first release:

* `ice.html` + `ice-monitor/` — an upstream ice monitor (Worker + KV, 6-hourly cron) at
  `https://sealevelrise-ice.craigm26.workers.dev`. Read the ice section below before touching it.
* Licences added: MIT code, CC BY 4.0 derived data, third-party notice for Three.js.
* Viewer: WebGL capability check with a real fallback, and the coupling coefficient is a slider.
* Charts: `role=img` + title/desc + a visually-hidden data table each.
* OpenFEMA v3 migration verified — **and it moves numbers**. See below.
* Homepage now leads with finding 7 rather than "here is a dataset".

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
- Water table = observed seasonal median, raised with sea level at a coupling coefficient
  defaulting to **0.85 — a screening assumption, not a calibrated value**. It is now exposed
  as a slider (0.40–1.00) so the reader can see the spread, which is the honest minimum.
  **Calibrating it is still the single highest-value improvement left.** The data to try is
  already in the repo: 31 USGS sites in `viz/wells.json` plus the Virginia Key tide record.
  Caveat before anyone claims it is calibrated: regressing head against tidal stage measures
  *tidal efficiency* — response to a twice-daily oscillation — which is related to but not the
  same as response to a mean-level shift, and attenuates inland faster. Treat a measured value
  as a constrained lower bound and say so.
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

## The ice monitor — read before modifying

It exists to answer one question: is there observational evidence that the **p95 = 8.39 ft**
tail already published in this package is being realised? That tail is West Antarctic marine
ice sheet instability, so the monitor is the *upstream* of a number the package already has.
It is not a general-purpose cryosphere dashboard and should not drift into being one.

**The trap it is built around — do not undo this.** What updates fastest contributes least.
Sea ice extent is daily and adds **nothing** directly to sea level; it is floating. Ice sheet
*mass* is what raises sea level, is monthly, and is **unavailable** — GRACE-FO mascons need
NASA Earthdata auth and there is no anonymous endpoint. Every indicator therefore carries
`raisesSeaLevel`, an observation date, and a lag. Never place a daily number next to a
sea level narrative without that context.

**Staleness is cadence-relative.** Each adapter sets `expectedLagDays`. A flat threshold marks
a monthly series permanently late and trains the reader to ignore the badge.

**Tripwires are pre-registered, not consensus science.** They state in advance what would and
would not count as evidence. The GRACE-FO one ships as `unarmed` rather than dropped — a stated
impossibility is more useful than a quiet absence, exactly as with NFIP full-risk premium.

**ENSO has no single sign.** Strong El Niño tends to raise Amundsen shelf *height* (snowfall)
while lowering *mass* (basal melt from warm Circumpolar Deep Water). An altimetry-height
dashboard would show thickening during the episodes that thin them. The Paolo et al. 2018
citation on the page is **flagged for verification** — confirm it before relying on it.

**Antarctic imagery is dark April–September.** Optical returns a black frame. The page says so
rather than showing an empty panel. An embedded microwave layer for that region was attempted
and did not work through the Worldview snapshot API; that is a stated gap.

Live sources: NSIDC Sea Ice Index v4.0 — note **v4.0, not v3.0**, the path silently moved —
NOAA CPC Niño 3.4, NOAA CO-OPS 8723214. NSIDC daily CSVs are fetched by HTTP **range request**
(last 4 KB of a 1.8 MB file); keep that.

## OpenFEMA v3 — migrated, and the numbers moved

`scripts/fetch_nfip_v3.py` re-extracts NFIP claims from v3 and diffs against the v2 figures in
this repo. Exit status is non-zero on any drift, so it doubles as a drift check.

**v2 is frozen at 2026-06-01 and removed after 2026-10-15.** Querying v2 live today returns
exactly what this package published; v3 has kept ingesting. So the package's insurance figures
are an **as-of-2026-06-01 snapshot**, which was invisible before this was run. Two real changes:
33128 total paid rose $134,102 on an *existing* claim (NFIP claims are supplemented for years
after they first appear), and 33132 gained one 2026 claim at $0 paid.

`data.json` still carries the v2 numbers, so the site is internally consistent but three months
stale. Promoting v3 means regenerating the claims-by-year payload too — do both or neither.
Full detail in `data/notes/NOTES_openfema_v3_migration.md`.

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
- OpenFEMA v2 removed after 2026-10-15. **Migration to v3 is done and verified** — see above.
- NSIDC Sea Ice Index moved from `v3.0` to `v4.0` filenames. The old path 404s silently.
- Whitespace-only strings (`" "`) are the null placeholder throughout Miami-Dade's GIS. Treating
  them as populated inflates the completeness audit from 2.2% to 100%.
