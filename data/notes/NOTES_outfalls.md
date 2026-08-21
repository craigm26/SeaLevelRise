# GAP A — Stormwater outfalls, downtown Miami

**AOI (WGS84):** `-80.215, 25.75, -80.17, 25.82`
**Compiled:** 2026-08-20 · all data pulled live from public ArcGIS REST / OGC endpoints

---

## Headline finding

**There is no public NPDES/MS4 outfall inventory carrying invert elevations for downtown
Miami.** I checked every endpoint listed below. What exists instead is two real, official,
downloadable layers that together describe how downtown actually discharges:

1. **Miami-Dade County DERM `StormWaterPoint_gdb`** — contains genuine
   `DISCHARGE POINT` / `ENERGY DISSIPATOR OUTFALL` / `DISCHARGE CHAMBER` features with a
   populated **receiving water body**, but **all 37 of them sit outside the AOI** (nearest is
   4.03 km from AOI centre, along the C-7/Little River and North Biscayne Bay shoreline).
   Its `ELEVATION` (invert) field is **0.0 % populated** across all 508 features retrieved.

2. **FDEP UIC Class V well inventory** — **2,594 drainage wells inside the AOI**. This is the
   important one. Downtown Miami does not primarily drain to surface outfalls; it drains
   *downward* into the Biscayne aquifer through gravity injection wells. This is the dominant
   failure mode and it is fully coupled to GAP B (groundwater).

The "tailwater locking" mechanism you're modelling is therefore only half the story for this
AOI. The other half — arguably the dominant half — is **rejected infiltration**: when the
water table rises, the drainage wells lose head and stop accepting water. See
`NOTES_groundwater.md`.

---

## Files produced

| File | Features | In AOI | Source |
|---|---|---|---|
| `outfalls_downtown_miami.geojson` | 6,645 | 2,660 | combined, normalised schema |
| `outfalls_mdc_stormwaterpoint.geojson` | 508 | 138 | Miami-Dade DERM |
| `outfalls_fdep_uic_drainage_wells.geojson` | 6,137 | 2,522 | FDEP UIC Class V |
| `storm_structure_elevations_city_of_miami.geojson` | 3,054 | 3,054 | City of Miami RPW |

Extraction bbox for the two outfall layers was widened to `-80.28,25.70,-80.10,25.87` so the
Biscayne Bay / Miami River shoreline discharges are captured; every feature carries an
`in_AOI` boolean and `km_from_AOI_center`.

### Structure class breakdown (combined file)

| structure_class | total | in AOI |
|---|---|---|
| drainage_well | 6,329 | 2,594 |
| hydraulic_structure_generic | 232 | 65 |
| outfall | 37 | **0** |
| pump | 20 | 0 |
| control_structure | 19 | 0 |
| outfall_appurtenance | 8 | 1 |

---

## Attribute completeness

### Miami-Dade DERM `StormWaterPoint_gdb` (n = 508)

| attribute | populated | % |
|---|---|---|
| `basin` (BASIN_NAME) | 508 | 100.0 % |
| `vert_datum` | 96 | 18.9 % |
| `drainage_system_id` | 93 | 18.3 % |
| `src_survey` | 91 | 17.9 % |
| `grate_elev_ft` | 80 | 15.7 % |
| `inside_dim` (diameter) | 73 | 14.4 % |
| `bottom_elev_ft` | 49 | 9.6 % |
| `receiving_water` (CANAL) | 48 | 9.4 % |
| `weir_elev_ft` | 31 | 6.1 % |
| **`invert_ft` (ELEVATION)** | **0** | **0.0 %** |

Receiving waters on the 37 true outfalls: Biscayne Bay (17), Lake Belmar (5), Little River
Canal (3+2), Miami Shores Bay Park Estates Waterway (3), Dry Pons (2), Sliver Blue Lake (1),
Tamiami Canal C-4 (1), Comfort Canal South Fork (1), null (2).
Only 5 of 37 carry a vertical datum.

### FDEP UIC Class V drainage wells (n = 6,137)

| attribute | populated | % |
|---|---|---|
| `well_status` | 6,137 | 100.0 % |
| `address` | 6,071 | 98.9 % |
| `construction_date` | 5,240 | 85.4 % |
| `well_depth_ft_bls` | 5,236 | 85.3 % |
| `casing_depth_ft_bls` | 5,121 | 83.4 % |

Within the AOI (n = 2,522): 2,252 STORMWATER DRAINAGE WELL + 270 DEWATERING WELL;
2,040 ACTIVE, 295 PROPOSED, 78 INACTIVE, 76 permanently abandoned.
Median well depth **120 ft** below land surface (p10 82, p90 160); median casing depth 96 ft.

> **Provenance caveat:** these depths are *below land surface*, with **no vertical datum and
> no land-surface elevation attached**. To place a well screen in NAVD88 you must subtract
> from the DEM — that is an interpolated value, not surveyed. Every such feature is tagged
> `provenance_elev = DEPTH_BLS_ONLY_NO_DATUM`.

### City of Miami RPW storm structures (n = 3,054, all inside AOI)

This is the **only real vertical control** I found for the downtown drainage network.

| attribute | populated | % |
|---|---|---|
| `RIMELEV` | 3,034 | 99.3 % |
| `RIM_VERTDATUM` | 2,657 | 87.0 % (2,590 explicitly NAVD88) |
| `BOTTOMELEV` | 1,382 | 45.3 % |
| `DEPTH` | 1,058 | 34.6 % |
| **`INVERT`** | **58** | **1.9 %** |
| `INVERT_VERTDATUM` | 21 | 0.7 % |

Valid-range statistics (NAVD88 ft): rim median **8.02** (p10 2.78, p90 12.35);
bottom median **0.27**; invert median **1.64** (n = 58).
359 rims sit below 3 ft NAVD88 and 884 below 5 ft.

> **Data errors to filter:** 2 records have `RIMELEV > 50 ft` (max 1075.00) — clearly bad.
> Filter to −10 … 50 ft before use. `LOCDESC` is 0 % populated despite existing in the schema.

---

## The GAP A ↔ GAP B coupling (most important number in this file)

Comparing City of Miami structure bottom elevations against observed water-table elevations
from `groundwater_levels_downtown.csv`:

| water table (ft NAVD88) | condition | structure bottoms below it |
|---|---|---|
| 0.38 | dry-season median | 707 / 1,382 — **51.2 %** |
| 0.71 | annual median (F-45 daily) | 746 — **54.0 %** |
| 0.84 | wet-season median | 758 — **54.8 %** |
| 2.11 | p95 (F-45 daily) | 917 — **66.4 %** |

**Over half of downtown Miami's mapped drainage structures have their bottoms permanently
below the water table, even in the dry season.** 19 of the 58 known inverts are below the
wet-season median water table. These structures are not draining — they are already flooded
from below, and they are acting as pressure-relief points for the aquifer, not as inlets.

---

## Every endpoint checked

### Found and used

| URL | Contents |
|---|---|
| `https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services?f=json` | Miami-Dade County AGOL org, **932 services** enumerated |
| `.../StormWaterPoint_gdb/FeatureServer/0` | 34 structure TYPEs incl. DISCHARGE POINT, DRAINAGE WELL, CONTROL STRUCTURE. **Used.** |
| `https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/WRM_UIC_PUBLIC/MapServer/2` | FDEP UIC Class V Non-ASR wells; 5,553 STORMWATER DRAINAGE WELL in bbox. **Used.** |
| `https://gis.miami.gov/gis/rest/services/PublicWorks/RPW_swStru_4Ref_in_Cartegraph/MapServer/0,1` | City of Miami INLET + MH with RIMELEV/INVERT. **Used.** |

### Checked, nothing relevant

| URL | Result |
|---|---|
| `https://gisweb.miamidade.gov/arcgis/rest/services?f=json` | 22 folders enumerated. `RER` = EEL registration only. `PW` = PWhorizontal / PWstreetmaint / PWvertical (no stormwater). `DAE` and `EOC` **empty**. `Utilities` = geometry/print GP services only. `LandManagement` = zoning/land use only. **No outfall layer anywhere on this server.** |
| `.../Stormwater_Management_System_Contents/FeatureServer/0` | Misleading name — it is a **waste-hauler permit table** (WASTE_CATEGORY, HAULER_NAME, PERMIT_NUMBER). No geometry. |
| `.../UtilCoordStormwater_gdb` | Utility-coordination **polygons**, not structures. |
| `https://gis.miami.gov/gis/rest/services?f=json` | 12 folders. `PublicWorks` has only the Cartegraph structure service (used above) + street/permit/aerial reference layers. `Utilities` = GP/geometry services only. No outfall layer. |
| `https://geodata.dep.state.fl.us/arcgis/rest/services?f=json` | **Not an ArcGIS server** — returns the FDEP Hub HTML site. Real server is `ca.dep.state.fl.us/arcgis`. |
| `https://ca.dep.state.fl.us/arcgis/rest/services/OpenData` | 95 services enumerated. **No MS4 / NPDES / outfall layer.** Nearest relevant: `SURFACE_WATER`, `IMPAIRED_WATERS`, `DRAINAGE_BASINS`, `WBIDS`. |
| `.../services/ProgramData` | **0 services.** |
| `.../services/External_Services` | 30 services. No outfalls. (`FGS_Potentiometric_WaterLevels`, `DEAR_TrendMonitoring_GroundWater` are GAP-B relevant.) |
| `https://gis.sfwmd.gov/arcgis/rest/services?f=json` | **Empty response.** |
| `https://geoweb.sfwmd.gov/agsext1/rest/services/WaterManagementSystem/All_Structures/FeatureServer/4` | SFWMD "AHED Structures" exists but the endpoint **returns an HTML login page — authentication required**, not public. |
| `https://geo-sfwmd.hub.arcgis.com/api/feed/all/v1.json` | 404 `Cannot GET`. |
| ArcGIS Online public search — `outfall Miami`, `MS4 outfall Florida`, `stormwater outfall Miami-Dade`, `NPDES outfall Florida` | 30/5/8/6 hits. The only true MS4 outfall service (`services.arcgis.com/ptvDyBs1KkcwzQNJ/.../MS4_Outfall`, owner `gudemanc`) is **not Florida**. |

### False lead worth recording

`services.arcgis.com/JXkZZiyztQP1WU91` (owner **`MiamiOKIT`**) publishes
`Miami_Stormwater_Sewer_View` and `Storm_Water_View`, each with a **layer 8 literally named
"Outfalls"** with `Name` + `ReceivingWaterBdy` fields — 43 features.

**This is Miami, _Oklahoma_.** Coordinates are lon −94.86 to −94.90, lat 36.84 to 36.90.
It ranks highly in AGOL search for "outfall Miami" and would be very easy to ingest by
mistake. **Do not use it.**

---

## What remains missing, and how to get it

The single highest-value missing item is **invert elevations on the drainage network**
(0.0 % from the county, 1.9 % from the city). Without them any pipe-capacity or
surcharge calculation is an assumption, not a measurement.

Also missing: pipe diameters at outfalls (14.4 % via `INSIDE_DIM`), tide-gate/flap-valve
presence, and any as-built connectivity between the drainage wells and the inlet network.

**Best request-by-email / public-records sources, in priority order:**

1. **Miami-Dade County RER–DERM, Stormwater Utility / NPDES MS4 Program.**
   They hold the MS4 permit outfall inventory (FDEP permit **FLS000003**, Miami-Dade
   county-wide MS4). Public records: `publicrecords@miamidade.gov`;
   DERM main line (305) 372-6789. Ask specifically for *"the MS4 outfall inventory and
   outfall reconnaissance data submitted under NPDES permit FLS000003, including invert
   elevations and receiving water body"*.

2. **City of Miami, Resilience & Public Works (RPW), Stormwater Section.**
   Owner of the Cartegraph asset database behind the layer used here — the served copy is a
   *reference* extract, and the master Cartegraph records hold substantially more inverts.
   Public records portal: `miamigov.com/Government/Public-Records`. Ask for the
   *"full Cartegraph stormwater structure and conduit export including INVERT and
   INVERT_VERTDATUM"*.

3. **FDEP Southeast District NPDES Stormwater**, West Palm Beach — holds the MS4 annual
   reports for FLS000003, which contain outfall tables. `SED@FloridaDEP.gov`.

4. **EPA ECHO / NPDES** — I found **no geospatial outfall layer** for FL MS4s. ECHO exposes
   permit-level facilities only (`echo.epa.gov/tools/web-services`), not outfall points.
   Not worth pursuing for geometry.

5. For the drainage wells specifically, FDEP UIC permit files (per `FACILITY_ID` in
   `outfalls_fdep_uic_drainage_wells.geojson`) contain **well completion reports with
   cased/open-hole intervals and static water levels** — these are the closest thing to an
   invert that exists for downtown, and they are obtainable per-facility from FDEP UIC.

---

## Schema of `outfalls_downtown_miami.geojson`

Normalised across both sources. Provenance fields are designed for the visualiser's
"solid = official / hatched = assumed" colour coding.

`source`, `source_layer`, `feature_id`, `label`, `structure_class`, `type_raw`,
`receiving_water`, `basin`, `maintained_by`, `municipality`, `invert_ft`, `bottom_elev_ft`,
`grate_elev_ft`, `weir_elev_ft`, `vert_datum`, `inside_dim`, `drainage_system_id`,
`src_survey`, `src_date`, `well_depth_ft_bls`, `casing_depth_ft_bls`, `well_status`,
`construction_date`, `address`, `horiz_accuracy`, `provenance_elev`, `provenance_geom`,
`in_AOI`, `km_from_AOI_center`

`provenance_elev` takes three values:

* `OFFICIAL_SURVEYED` (81 features) — carries at least one surveyed elevation
* `DEPTH_BLS_ONLY_NO_DATUM` (5,236) — depth below land surface, datum must be assumed from DEM
* `NO_ELEVATION_MUST_ASSUME` (1,328) — **no vertical information at all; flag these in the UI**
