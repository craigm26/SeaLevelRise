# GAP B — Biscayne aquifer water table, downtown Miami

**AOI (WGS84):** `-80.215, 25.75, -80.17, 25.82` · centre `25.785, -80.1925`
**Compiled:** 2026-08-20 · all values from USGS observations, no modelled data

---

## Files produced

| File | Records | Notes |
|---|---|---|
| `groundwater_wells_miami_dade.csv` | 669 wells | full Miami-Dade GW inventory; 125 have level observations |
| `groundwater_levels_downtown.csv` | 14,841 obs | 31 sites within 8 km of AOI centre, 1940–2026 |

---

## What the data shows

### Typical water-table elevation near downtown (ft NAVD88)

From 1,643 direct NAVD88 observations (parameter **62611**) at wells within 8 km, 2015–2026:

| period | median | p10 | p90 |
|---|---|---|---|
| **Dry season** (Dec–Apr) | **0.38** | −0.15 | ~1.05 |
| **Wet season** (Jun–Oct) | **0.84** | +0.18 | ~2.15 |
| All year | 0.59 | p05 −0.24 | p95 **1.86**, max **4.00** |

Monthly medians rise smoothly from a March low of **0.32 ft** to an October peak of
**1.13 ft NAVD88**. Seasonal swing ≈ **0.46 ft** on medians.

Corroborated independently by the one continuous recorder near downtown,
**USGS F-45** (5.01 km, daily *maxima*, 5,775 days 2010–2026):

| period | median | p90 |
|---|---|---|
| Dry (Dec–Apr) | **0.40** | ~1.05 |
| Wet (Jun–Oct) | **1.07** | ~2.2 |
| All | 0.71 | p95 **2.11**, max **6.18**, min −0.30 |

Daily-maximum framing gives the higher numbers — appropriate for flood work. Seasonal
swing ≈ **0.67 ft**.

### How close the water table sits to the ground

Depth-to-water (parameter **72019**), 21 wells within 8 km, 2015–2026, n = 1,643:

* median **7.93 ft** below land surface
* p05 **3.79 ft**, **shallowest observed 1.65 ft**
* nearest wells: G-3704 (3.28 km) median 8.44 ft, shallowest 6.69 ft;
  G-3603 (4.39 km, **the only well inside the AOI**) median 7.91 ft, shallowest **4.76 ft**;
  F-45 (5.01 km) median 7.44 ft, shallowest **4.65 ft**

Those medians are measured at well head elevations of 10–13 ft NAVD88. Downtown Miami street
grades are substantially lower — City of Miami storm structure rims have a **median of 8.02 ft
NAVD88, with p10 at 2.78 ft and 359 rims below 3 ft**. At a 3 ft NAVD88 ground surface and a
wet-season water table of 0.84–1.07 ft NAVD88, **unsaturated thickness is roughly 2 ft.**

### Wells inside / nearest the AOI

Only **one** USGS groundwater well falls inside the AOI:

| site_no | name | distance | alt | depth | aquifer |
|---|---|---|---|---|---|
| `254908080125201` | G-3603 | 4.39 km from centre (NE corner) | 10.2 ft NGVD29 | 169 ft | Biscayne (112BSCNN) |

Nearest others: G-3704 `254822080125501` (3.28 km, 327 obs, 2000–2026),
G-5015 `254903080131301` (4.56 km), **F-45 `254943080121501` (5.01 km, 638 obs, 1959–2026,
the long record and the only useful continuous gauge)**, G-3605 `254629080143101` (5.06 km).

All are completed in the **Biscayne aquifer** (`112BSCNN` / national `N400BISCYN`),
aquifer type `U` = **unconfined**.

---

## Datum conversion (derived, not assumed)

The USGS publishes the same readings in both NGVD29 (62610) and NAVD88 (62611). Pairing them
on site + timestamp across **10,042 paired observations** in this dataset gives:

> **NAVD88 = NGVD29 − 1.56 ft** (median; mean −1.564, p05 −1.68, p95 −1.50, range −1.73 to −1.33)

This is an empirical result from the data itself, and it matches the published ~−1.5 ft
Miami-area conversion. It is applied in `groundwater_levels_downtown.csv` wherever
`navd88_source = converted_from_NGVD29`; rows with `navd88_source = measured` are native
NAVD88 and should be preferred.

---

## How a modeller should use this

**1. As a floor on the water surface, not a boundary condition to ignore.**
The bathtub surface should never be allowed to fall below the water table. In the wet season
that floor is **≈ +0.85 to +1.1 ft NAVD88** near downtown, and **≈ +2.1 ft at p95**. Any cell
whose ground elevation is below that is already saturated before a drop of rain falls.

**2. As a rejected-infiltration condition — this is the big one for downtown Miami.**
Downtown does not discharge to surface outfalls; it discharges *downward* into this aquifer
through **2,594 Class V drainage wells inside the AOI** (see `NOTES_outfalls.md`). Those wells
work on the head difference between the inlet and the potentiometric surface. As the water
table rises:

* available head collapses, injection rate falls toward zero;
* **infiltration/soil-storage terms in the runoff model must be set to zero**, not to a
  typical Green-Ampt or SCS value for sandy limestone. Treating downtown's porous limestone
  as freely draining is the single most common way to under-predict flooding here.

A defensible screening approach: make effective subsurface storage a function of
(ground elevation − water table elevation), and drive it to **zero** in the wet-season and
p95 scenarios.

**3. As a hard constraint on storm-drain capacity.**
Cross-referencing the City of Miami structure elevations against these water levels:
**54.8 % of the 1,382 structures with a known bottom elevation have that bottom below the
wet-season median water table** (51.2 % below even the dry-season median; 66.4 % below p95).
Those structures are permanently submerged. Their effective storage and conveyance is far
below nominal, and under high water table they become *sources* of water, not sinks.

**4. Compounding with sea level rise — do not treat these as independent sliders.**
The Biscayne aquifer is unconfined and hydraulically connected to Biscayne Bay. Sea level
rise raises the water table roughly in step with MHHW in the near-shore zone. A 2 ft SLR
scenario should raise the groundwater floor by an amount approaching 2 ft near the shoreline
(tapering inland), *not* leave it at today's 0.84 ft. Applying the SLR slider only to the
surface water body while holding groundwater fixed will materially under-predict inundation.
Flag this explicitly in the Assumptions & Limitations panel.

**5. Known limits of this dataset.**
Only 1 well inside the AOI and 31 within 8 km — the downtown water table is **interpolated,
not observed**, and should be rendered as such (hatched/desaturated) in the visualiser. Well
head elevations sit at 10–13 ft NAVD88, higher than much of the downtown street grid, so
depth-to-water figures from these wells are **not** transferable to downtown ground surface;
use the NAVD88 *elevations*, not the depths, and subtract from the DEM.

---

## Sources

* **USGS NWIS site inventory** — `https://waterservices.usgs.gov/nwis/site/?format=rdb&countyCd=12086&siteType=GW&hasDataTypeCd=gw&siteStatus=all&siteOutput=expanded` (669 GW sites; still live)
* **USGS Water Data OGC API** — `https://api.waterdata.usgs.gov/ogcapi/v0/collections/`
  * `monitoring-locations` — 611 GW sites in bbox `-80.30,25.70,-80.10,25.87`
  * `field-measurements` — 30,334 obs (10,145 × 62611 NAVD88; 10,145 × 72019 depth; 10,044 × 62610 NGVD29), 127 sites, 1940–2026
  * `daily` — 5,775 daily maxima for F-45, 2010–2026 (62610, statistic 00001)
  * `aquifer-codes`, `national-aquifer-codes`, `altitude-datums` lookups
* Parameter codes: **62611** GW elevation above NAVD88 · **62610** above NGVD29 · **72019** depth to water below land surface

> **API migration note.** The legacy `waterservices.usgs.gov/nwis/gwlevels/` endpoint named in
> the task brief is **decommissioned** (frozen 2025-11-01, 301-redirecting since 2026-02-01,
> per the USGS *"Decommissioning Legacy gwlevels and SensorThings APIs – Fall 2025"* notice).
> It now redirects to a blog post and returns HTML, not data. All groundwater levels here come
> from the replacement **`field-measurements`** collection on `api.waterdata.usgs.gov`.
> The `site` service still works.

### Not used / not reachable

* **SFWMD DBHYDRO** — the ArcGIS front door `gis.sfwmd.gov/arcgis/rest/services` returns
  empty and `geoweb.sfwmd.gov/agsext1/...` returns an **HTML login page (auth required)**.
  DBHYDRO itself remains available interactively at `my.sfwmd.gov/dbhydroplsql/` for
  well-by-well export if denser coverage is needed. USGS coverage was sufficient here.
* **FDEP `OpenData/SAS_DTW`** (`ca.dep.state.fl.us/arcgis`) — a **30 m raster of Surficial
  Aquifer System depth-to-water**, described as "the water table surface grid subtracted from
  the DEM". Not downloaded (raster, and it is a *modelled* surface rather than observations),
  but it is the natural cross-check if you want a continuous water-table field instead of
  interpolating from 31 point wells. Also `OpenData/FGS_POTMAP_*` (potentiometric surface,
  May & Sept 2012–2019) and `External_Services/FGS_Potentiometric_WaterLevels`.
* **Miami-Dade County** publishes `GroundwaterMonitoringWellsReadOnlyView` and
  `PublicGroundWaterSamplesResult_gdb` on its AGOL org (`8Pc9XBTAsYuxx9Ny`) — water-quality
  monitoring rather than water-level time series.

---

## Column reference

**`groundwater_wells_miami_dade.csv`** — `site_no`, `station_name`, `lat`, `lon`,
`land_surface_alt_ft`, `land_surface_alt_datum`, `well_depth_ft`, `hole_depth_ft`,
`aquifer_code`, `aquifer`, `national_aquifer_code`, `aquifer_type_code`, `datum`,
`construction_date`, `huc`, `distance_from_AOI_center_km`, `inside_AOI`, `n_level_obs`,
`period_of_record`

**`groundwater_levels_downtown.csv`** — `site_no`, `station_name`, `date`, `time_utc`,
`water_level_value`, `units`, `datum`, `parameter`, `parameter_name`, `value_navd88_ft`,
`navd88_source`, `approval_status`, `distance_km`, `series`

`series` distinguishes `USGS_field_measurement` (discrete, 9,066 rows) from
`USGS_daily_max_continuous` (F-45 daily maxima, 5,775 rows).
Use `value_navd88_ft` for modelling; prefer rows where `navd88_source = measured`.
