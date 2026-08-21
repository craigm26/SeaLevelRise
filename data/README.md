# Data dictionary — downtown Miami flood risk

> Small analysis outputs and notes live in this `data/` tree. The **large** source files
> (58 MB 1 m DEM, ~52 MB of parcel / footprint / drainage GeoJSON) are in the Drive folder
> below, not in git — `scripts/` rebuilds the derived products from them.

Public folder: https://drive.google.com/drive/folders/1sJkjULZLFaTLHJrNBzs_BzJ0kvTjMNbL

Assembled August 2026 for a screening-level 3D flood visualizer of downtown Miami
(Brickell → CBD → Edgewater). All public data, primary sources, every file cited.

**AOI (WGS84):** lon −80.215 to −80.170, lat 25.750 to 25.820
**Horizontal:** EPSG:4326 (vectors), EPSG:26917 / UTM 17N (rasters)
**Vertical:** NAVD88. DEM is in **meters**; every tide, scenario, and elevation table is in
**feet**. Convert once, at the boundary, and label the axis.

---

## 1. The numbers that anchor every scenario

| Quantity | Value | Source |
|---|---|---|
| **MHHW, Virginia Key** | **+0.23 ft NAVD88** (1983–2001 epoch) | NOAA CO-OPS 8723214 |
| **HAT** (honest king tide) | **+1.20 ft NAVD88** = MHHW + 0.97 ft | same |
| **Observed max** | **+3.80 ft NAVD88**, Irma, 2017-09-10 | same |
| NOAA minor / moderate / major flood thresholds | **1.92 / 2.89 / 4.12 ft NAVD88** | NOAA HTF |
| **Ground elevation, buildings** | median **9.58**, p5 **2.94** ft NAVD88 | USGS 3DEP 1 m |
| **100-yr 24-hr rainfall** | **14.5 in** (2-yr 5.32, 500-yr 20.0) | Atlas 14 Vol. 9 |
| **Water table** | dry **0.38**, wet **0.84**, p95 **1.86** ft NAVD88 | USGS, 14,841 obs |

**Sea level rise, ft above ~2005, Virginia Key:**

| Source | 2050 | 2100 |
|---|---|---|
| NOAA 2022 Intermediate | 1.05 | 3.64 |
| NOAA 2022 Intermediate-High | 1.25 | 5.25 |
| IPCC AR6 SSP2-4.5 (median) | 0.95 [0.74–1.23] | 2.34 [1.79–3.17] |
| IPCC AR6 SSP5-8.5 (median) | 1.03 [0.81–1.33] | 3.01 [2.37–4.02] |
| AR6 SSP5-8.5 **low confidence** | 1.06 [0.80–1.59] | 3.43 [2.37–5.71], p95 **8.39** |

NOAA's 2005 baseline and AR6's 1995–2014 mean (midpoint 2004.5) differ by ~2 mm — **these
plot on the same axis with no correction.** See `NOTES_slr_scenarios.md`.

---

## 2. Files

### Tide, sea level, rainfall
`virginia_key_datum_crosswalk_navd88.json` · `tide_extremes_virginia_key.json` ·
`slr_scenarios_virginia_key_ft.csv` (NOAA 2022, 5 scenarios × 15 years) ·
`ipcc_ar6_slr_virginia_key_ft.csv` (AR6, 5 SSPs + low-confidence branch, to 2300) ·
`noaa_high_tide_flooding_8723214.json` · `NOTES_slr_scenarios.md` ·
`atlas14_downtown_miami_pds_depth.csv` · `virginia_key_8723214_datums.json`

### Terrain
`dem/dem_downtown_miami_1m_navd88m_utm17n.tif` (4561×7781, source of truth) ·
`dem/dem_downtown_miami_2m…tif` · `dem/dem_downtown_miami_13arcsec…tif` ·
`dem/terrain_heightmap_4m.png` + `.json` (browser-ready) · `dem/NOTES_dem.md`

### Buildings, parcels, first-floor elevations
| File | Rows | What |
|---|---:|---|
| `parcels_downtown_miami.geojson` | 12,936 | parcel polygons, year built, floors, units, DOR code |
| `property_points_downtown_miami.geojson` | 68,110 | incl. 55,424 condo units; roll up via PARENT_FOLIO |
| `building_footprints_downtown_miami.geojson` | 12,480 | footprints + BLDG_HEIGHT, 99.9% folio-linked |
| `building_ffe_estimates.csv` | 12,479 | **estimated first-floor elevation + provenance** |
| `building_ffe_summary_by_zip_zone.csv` | 55 | the same, aggregated |
| `NOTES_first_floor_elevations.md` | | **read before using the FFE layer** |

### Flood zones, drainage, groundwater
`fema_nfhl_flood_zones_downtown.geojson` (163 polys) ·
`storm_drains_stormwater_lines.geojson` (6,612) · `storm_drains_stormwater_points.geojson` (7,235) ·
`storm_drain_data_provenance_audit.csv` · `outfalls_downtown_miami.geojson` (6,645) ·
`outfalls_fdep_uic_drainage_wells.geojson` (6,137) · `outfalls_mdc_stormwaterpoint.geojson` ·
`storm_structure_elevations_city_of_miami.geojson` (3,054, **3,034 surveyed rims**) ·
`NOTES_outfalls.md` · `groundwater_wells_miami_dade.csv` (669) ·
`groundwater_levels_downtown.csv` (14,841 obs) · `NOTES_groundwater.md`

### Insurance
`citizens_pif_miami_dade.csv` (county PIF + exposure, 2022-12 → 2026-07) ·
`nfip_rr2_florida_profile.csv` · `NOTES_rr2.md` ·
`nfip_policies_full_<zip>.csv` × 5 (14,875 records) · `nfip_policies_extract_log.md` ·
`nfip_policies_full_summary_by_zip.csv` · `nfip_claims_<zip>.csv` × 5 ·
`nfip_claims_summary_by_zip.csv` · `nfip_claims_by_zip_year.csv` ·
`insurance_market_stress_miami.md` / `.csv`

---

## 3. Six findings that change what you build

**1. Over half of downtown's drainage is underwater before it rains.**
Cross-referencing 3,034 surveyed structure elevations against 14,841 groundwater
observations: **54.8% of structures with a known bottom sit below the wet-season median
water table**; 51.2% below even the dry-season median. They are not accepting inlet flow —
they are relieving aquifer pressure. Any model treating the storm system as available
capacity at t=0 is wrong from the first timestep.

**2. Downtown doesn't drain to the bay — it drains *down*.**
There is no surface outfall inside the AOI; the nearest real discharge point is 4 km away.
Downtown discharges through **2,594 FDEP Class V injection wells**, median depth 120 ft,
straight into the Biscayne aquifer. Tailwater locking is real but secondary. **Rejected
infiltration is the co-dominant failure mode**, and it is a groundwater problem — which
means finding 1 and finding 2 are the same finding.

**3. The pipe-capacity layer cannot be built honestly from county data.**
Of 6,612 pipe segments: **2.2% have a diameter, 0.1% have inverts, 0% have depth.** DERM's
outfall `ELEVATION` field is 0.0% populated; City of Miami's `INVERT` is 1.9%. What *does*
exist is vertical control — 3,034 surveyed rim elevations, 2,590 explicitly NAVD88. Build on
rims and known bottoms; render everything inferred hatched with the count in the legend.

**4. 77% of downtown buildings have no measurable first-floor elevation.**
9,636 of 12,479 buildings sit in FEMA zone X. No SFHA means no elevation certificate, which
means **fewer than 20 usable local observations for that entire population**. Their FFE is a
borrowed pre-FIRM AE median. 69.5% of all downtown buildings are pre-FIRM (pre-1975, derived
from the data, not assumed). The unmeasured-elevation wedge and the uninsured-loss wedge are
the same buildings.

**5. Miami-Dade's wind market shrank 69% in under four years.**
Citizens PIF: 218,947 (Dec 2022) → 210,019 → 170,873 → 88,973 → **67,353 (Jul 2026)**;
exposure $76.85 B → **$19.22 B**. That is depopulation working — a *recovering* wind market.
Meanwhile 80.2% of Florida's 1.73 M NFIP policies are on an upward Risk Rating 2.0 glide
path. **Two markets, same water, opposite directions.** One blended "fragility index" would
misrepresent both. And 33137 (Edgewater) is 30.4% zone X, only 23.9% post-FIRM, only 41.7%
with a filed elevation — the oldest buildings, the most voluntary coverage, the thinnest data.

**6. At 2050 the emissions scenario barely matters.**
All five AR6 SSP medians span 0.85–1.03 ft at 2050 — less than the spread *within* any single
scenario. An emissions toggle that shows visible mid-century differences overstates the
science. The scenarios diverge after 2070; before that, the uncertainty is in the ice sheets,
not the emissions.

---

## 4. Remaining gaps — all documented, none silent

1. **Elevation certificates** — would convert 9,636 hatched buildings to solid. Public
   records held by City of Miami floodplain management and Miami-Dade RER, not published in
   bulk. A records request naming the AOI is the fix.
2. **Storm drain inverts** — request the full Cartegraph export from City of Miami RPW (the
   served layer is a reference extract) and the MS4 outfall inventory from Miami-Dade
   RER-DERM under FDEP permit **FLS000003**.
3. **Drainage-well connectivity** — which inlets feed which of the 2,594 injection wells is
   not published. FDEP UIC permit files per `FACILITY_ID` hold completion reports with cased
   intervals and static water levels — the closest thing to an invert that exists downtown.
4. **NFIP full-risk premium in dollars** — `FimaNfipPolicies` has no full-risk field, so this
   is not obtainable from any public API, not merely un-fetched. FEMA's state profile PDFs
   return Akamai 403 to every automated route.
5. **NFIP record counts** — `$inlinecount` 503s under a zip filter, so "% complete" has an
   unknowable denominator. 14,875 records is 2.2–3.9× the pagination ceiling, not a census.
   **v2 is deprecated: frozen 2026-06-01, removed after 2026-10-15.**
6. **Parcel values** — `ASSESSED_VAL_CUR` is null service-wide. `PRICE_1` (last sale) is
   populated and would need a provenance flag.
7. **Groundwater interpolation** — exactly one USGS well (G-3603) sits inside the AOI. The
   downtown water table is interpolated from 31 sites within 8 km. Render it hatched.
8. **SE Florida Compact guidance vintage** — the recommendation to default to
   Intermediate-High rests on the 2019/2020 guidance, itself built on NOAA 2017 curves.
   Confirm the current regional update before treating it as regulatory practice.

## 5. Reproducing this

`fetch_large_datasets.sh` rebuilds the 1 m DEM mosaic. Every other file records its source
URL in its own header, notes file, or a `source_url` column. Two traps worth naming:
AGOL search for "outfall Miami" surfaces **Miami, Oklahoma** (lon −94.9), and USGS's
`waterservices.usgs.gov/nwis/gwlevels/` endpoint was decommissioned in early 2026 — use the
`field-measurements` collection on `api.waterdata.usgs.gov`.
