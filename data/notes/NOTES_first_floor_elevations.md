# First-floor elevations — how `building_ffe_estimates.csv` was built

12,479 buildings, each with an estimated finished-floor elevation in ft NAVD88, an uncertainty
band, and a provenance class. **Read the provenance column before you trust any single row.**

## The short version

There is no public register of first-floor elevations. But NFIP policy records carry
`lowestFloorElevation` and `lowestAdjacentGrade` for policies that filed an elevation
certificate, and the difference between them is the *height of the first floor above the dirt
next to the building*. That difference is stable within a building era and flood zone, so it
can be measured locally and applied to buildings that have no certificate.

    FFE = (ground elevation from the 1 m LiDAR DEM)
        + (median slab height for this building's FIRM era × flood zone)

and for post-FIRM buildings with a published BFE, the estimate is raised to the regulatory
floor where that is higher:

    FFE = max(grade + slab, BFE + median freeboard)

## Step 1 — measure ground elevation per building

For each footprint, a 3 m collar outside the wall line was cut from the 1 m 3DEP DEM and the
**5th percentile** of the cells in that collar taken as lowest adjacent grade. The 5th
percentile rather than the minimum, because single-cell minima in a 1 m urban DEM pick up
gutters, tree pits, and stair wells.

Result across downtown: LAG p5 **2.94**, p25 **7.74**, median **9.58**, p95 **14.75** ft NAVD88.
Downtown sits on the Atlantic Coastal Ridge, which is why the median is higher than people
expect; the exposure is concentrated in the p5 tail along the river and bay edges.

## Step 2 — measure slab height from NFIP certificates

14,875 policy-term records across 33128/33130/33131/33132/33137 were deduplicated to 5,461
distinct building signatures (census tract + LFE + LAG + BFE + construction date + occupancy
+ floor count). Of those, 58.2% carry `lowestFloorElevation` and 57.2% carry
`lowestAdjacentGrade`.

The post-FIRM cutoff was **derived, not assumed**. `postFIRMConstructionIndicator` flips
cleanly at construction year 1975 (1974: 2 post / 380 pre; 1975: 186 post / 3 pre), so
**YEAR_BUILT ≥ 1975 = post-FIRM** for these communities.

**LFE − LAG, feet — the slab height table actually applied:**

| Era | Zone | n | p25 | median | p75 |
|---|---|---:|---:|---:|---:|
| post-FIRM | AE | 1,608 | 0.90 | **2.40** | 7.40 |
| pre-FIRM | AE | 1,135 | 0.80 | **1.60** | 2.50 |
| post-FIRM | VE | 134 | 5.50 | **10.10** | 12.80 |
| pre-FIRM | AH | 104 | 0.40 | **1.35** | 1.90 |
| post-FIRM | AH | 38 | 0.80 | **1.30** | 1.80 |
| pre-FIRM | VE | 26 | 0.70 | **1.30** | 4.00 |

`ffe_lower_ft` and `ffe_upper_ft` in the CSV are grade + p25 and grade + p75 — a real
interquartile band, not a guess at ±1 ft.

**LFE − BFE (freeboard), feet:** post-FIRM AE +0.80, pre-FIRM AE +0.40, post-FIRM VE +3.40,
post-FIRM AH +1.30, pre-FIRM AH +1.10, pre-FIRM VE −0.60.

Note the pre-FIRM AE p25 of **−0.70 ft**: a quarter of pre-FIRM buildings carrying flood
policies sit *below* their base flood elevation. That is not an artifact — it is what
pre-1975 construction in a mapped floodplain looks like.

## Step 3 — the honesty problem, stated plainly

**9,636 of 12,479 buildings (77%) are in FEMA zone X.** Elevation certificates are not
required outside the SFHA, so after deduplication there were *fewer than 20* zone-X records
with both LFE and LAG — not enough for a stratum. Those buildings are marked
`ffe_provenance = no_local_observations` and carry a borrowed pre-FIRM AE median (1.60 ft).

| Provenance class | Buildings | Meaning |
|---|---:|---|
| `observed_stratum` | 2,239 | slab height measured on ≥20 local certificates in the same era × zone |
| `no_local_observations` | 9,636 | zone X — no local certificate data exists at all; value borrowed |
| `assumed_default` | 604 | era or zone unknown; value borrowed |

**In the visualizer, `no_local_observations` must render hatched.** Nearly four out of five
downtown buildings fall in it, and that is exactly the population the insurance layer cares
about — outside the SFHA, no mandatory purchase, no elevation requirement, no certificate,
and therefore no data. The uninsured-loss wedge and the unmeasured-elevation wedge are the
same buildings.

## Step 4 — other things worth knowing before you use this

**69.5% of downtown buildings are pre-FIRM** (built before 1975). They were never required to
elevate to anything.

**Zone assignment is by representative point,** not by area-weighted overlay. A large parcel
straddling an AE/X boundary gets one zone.

**`STATIC_BFE` is sparse and sometimes sentinel-valued** in NFHL; values outside ±100 ft were
rejected. Where BFE is absent, the regulatory branch is skipped and the estimate is
grade + slab only — `ffe_method` records which branch was used.

**Tidal-only exposure, for calibration** (buildings whose estimated FFE sits below a still
water level — this is the tidal term alone, before any rainfall ponding):

| Stage (ft NAVD88) | What it is | Buildings below FFE |
|---|---|---:|
| 1.20 | HAT, highest astronomical tide | 9 (0.1%) |
| 2.30 | MHHW + AR6 SSP2-4.5 2100 median | 70 (0.6%) |
| 3.80 | Observed maximum, Irma 2017-09-10 | 245 (2.0%) |
| 4.10 | MHHW + AR6 SSP5-8.5 2100 median | 352 (2.8%) |

These are small numbers, and they should be. Downtown Miami's tidal flooding problem is
concentrated at the water's edge; its *rainfall* flooding problem is everywhere the drainage
fails, which is what the storm scenario models. If a run shows tidal inundation touching
thousands of buildings, something is wrong with the datum handling.

**What would replace this entirely:** actual elevation certificates, held by the City of
Miami floodplain manager and Miami-Dade RER. They are public records but not published in
bulk. A records request naming the AOI would convert 9,636 hatched buildings into solid ones.
