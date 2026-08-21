# Sea Level Rise Scenarios for the Miami Flood Visualizer

**Location:** NOAA tide gauge 8723214, Virginia Key (Biscayne Bay), FL — 25.7317 N, 80.1617 W. PSMSL ID 1858.
**Files this note reconciles:**

| File | Source | Scenarios | Baseline | Units |
|---|---|---|---|---|
| `slr_scenarios_virginia_key_ft.csv` | NOAA 2022 Sea Level Rise Technical Report (via CO-OPS API) | Low, Int-Low, Intermediate, Int-High, High | **year 2005** | ft |
| `ipcc_ar6_slr_virginia_key_ft.csv` | IPCC AR6 WG1 Ch. 9 regional projections (via Zenodo) | SSP1-1.9 … SSP5-8.5, medium + low confidence | **1995–2014 mean** | ft |
| `noaa_high_tide_flooding_8723214.json` | NOAA CO-OPS HTF products | NOAA 2022 scenarios | n/a (flood-day counts) | days/yr |

**Provenance note for the visualizer's colour-coding: every number in this file is measured or published, not interpolated.** The AR6 values were extracted directly from the IPCC's own archived NetCDF at the exact grid entry for PSMSL 1858 (lat 25.73, lon −80.16). No spatial interpolation, no scenario blending, no unit guessing. The one derived quantity is the vertical-land-motion split in §4, which is a difference of two published AR6 files and is labelled as such.

---

## 1. How the AR6 numbers were obtained (reproducibility)

The NASA/JPL AR6 Sea Level Projection Tool front end is a JavaScript app with no public per-station JSON endpoint, so the numbers were taken from the **underlying published dataset** that tool serves:

- **IPCC AR6 Sea Level Projections**, Garner et al., Zenodo, DOI [10.5281/zenodo.6382554](https://doi.org/10.5281/zenodo.6382554)
- File: `ar6-regional-confidence.zip` → `regional/confidence_output_files/{medium,low}_confidence/{ssp}/total_{ssp}_{conf}_values.nc`
- Variable `sea_level_change` (int16, mm), dims `(quantiles=107, years=14, locations=66190)`; `locations == 1858` is Virginia Key (index 952), lat/lon verified 25.73 / −80.16.
- Quantiles 0.05, 0.17, 0.50, 0.83, 0.95 are exact grid values in the file — no interpolation between quantiles.
- Converted mm → ft (× 0.003280839895), rounded to 0.01 ft.

The archive is 9.2 GB, so the eight needed NetCDF files were pulled with HTTP range requests against the ZIP central directory rather than downloading the whole thing.

**Validation:** the same pipeline was run against `ar6.zip` → `ar6/global/confidence_output_files/...` (global mean sea level). It reproduces the published AR6 GMSL table exactly — SSP5-8.5 2100 = **0.77 m [0.62–1.02]**, SSP1-1.9 2100 = **0.38 m [0.28–0.55]**, matching IPCC AR6 WG1 Ch. 9 / Table 9.9 and SPM. That is the check that the station extraction is reading the right axis order and the right location.

AR6 medium-confidence runs to 2150; **low-confidence runs to 2300** (that is why the CSV has 157 rows, not 112).

---

## 2. Baselines — the offset you need, stated as a number

Three different reference points are in play. Getting this wrong is the single easiest way to be off by half a foot.

| Datum | Definition | Used by |
|---|---|---|
| **1995–2014 mean** | 20-yr average, midpoint **2004.5** | IPCC AR6 (all SSP files) |
| **Year 2005** | instantaneous | `slr_scenarios_virginia_key_ft.csv` (NOAA CO-OPS API delivery) |
| **Year 2000** | instantaneous | NOAA 2022 Technical Report **printed tables** |

**The numbers, from NOAA's own offset product** (`slr_projectionOffsets.json?station=8723214`, reportYear 2022):

- `RSL_OFFSET_2000_2005` = **2.0 cm = 0.066 ft ≈ 0.07 ft**
- `RSL_OFFSET_1992_2000` = **3.0 cm = 0.098 ft ≈ 0.10 ft**

**Practical consequences:**

1. **AR6 (1995–2014) vs the folder's NOAA CSV (2005): no correction needed.** The AR6 baseline midpoint is 2004.5; the NOAA CSV is referenced to 2005. The gap is half a year of local rise ≈ 3.2 mm/yr × 0.5 yr ≈ **2 mm ≈ 0.01 ft** — far below the rounding in either file. **Plot them on the same axis directly.**
   *Empirical check:* NOAA 2022 gives 0.30 ft at 2020 (all scenarios); AR6 SSP2-4.5 medium gives 0.26 ft at 2020. A 0.04 ft spread confirms the baselines coincide.
2. **If you ever read numbers off the printed NOAA 2022 report tables instead of this CSV, subtract 0.07 ft** to put them on the AR6/2005 footing.
3. **Neither baseline is NAVD88.** These are *rises*, not elevations. To drive the DEM you must add the rise to a tidal datum expressed in NAVD88. From `virginia_key_datum_crosswalk_navd88.json` (1983–2001 epoch): **MHHW = +0.23 ft NAVD88**, MSL = −0.89 ft NAVD88.
   So: `water_surface_ft_NAVD88 = 0.23 + slr_ft` for a MHHW-referenced still-water plane.
   Caveat: the tidal epoch is 1983–2001 (centred ~1992), so MHHW itself is already ~0.1 ft stale relative to 2005. That is a real but sub-rounding error at the scale of this visualizer — flag it in Assumptions, don't try to correct it.

---

## 3. Mapping NOAA 2022 scenarios onto AR6 SSPs — the honest version

### They are not the same kind of object

- **AR6 SSPs are emissions-driven.** Each is a probabilistic projection *conditional on* a specified emissions pathway. The spread within one SSP is physical/model uncertainty.
- **NOAA 2022 scenarios are outcome-defined.** Low / Int-Low / Intermediate / Int-High / High are simply **0.3 / 0.5 / 1.0 / 1.5 / 2.0 m of GMSL rise in 2100** (relative to 2000), each then regionalised to every US tide gauge. They are chosen for planning convenience, not derived from an emissions pathway.

The NOAA Application Guide is explicit about this:

> "there are no probabilities that can be assigned directly to each of the Sea Level Scenarios"

Probability only enters when you *condition on warming*. The guide's Table 1 gives, for example: at ~1.5 °C (≈SSP1-2.6) the Low scenario is ~92% likely to be exceeded while higher scenarios are <1%; at ~3 °C (SSP2-4.5→SSP3-7.0) Intermediate-Low is ~82% likely to be exceeded; at ~5 °C (SSP5-8.5) the Intermediate scenario is ~23% likely to be exceeded. The guide also states that the Intermediate, Intermediate-High and High scenarios "require high emissions (defined as … SSP3-7.0 and SSP5-8.5)".

### Empirical crosswalk at *this gauge* (ft, 2100, both on the ~2005 datum)

| NOAA 2022 | ft | Nearest AR6 medium-confidence equivalent |
|---|---|---|
| Low | 1.44 | **Below AR6's most optimistic median.** SSP1-1.9 median is 1.78 ft. Low sits near the SSP1-1.9 5th–17th percentile. |
| Intermediate-Low | 2.10 | ≈ SSP1-2.6 median (1.94) / SSP2-4.5 median (2.34) |
| Intermediate | 3.64 | Above SSP5-8.5 **median** (3.01); between its median and 83rd pct (4.02) |
| Intermediate-High | 5.25 | Beyond SSP5-8.5 medium-confidence 95th pct (4.93). Matches SSP5-8.5 **low-confidence** 83rd pct (5.71) |
| High | 6.96 | **No medium-confidence analogue at all.** Only reachable inside the AR6 low-confidence branch (5–95 range reaches 8.39) |

### Where the correspondence breaks down

1. **Before ~2060 the mapping is meaningless.** At 2050, all five AR6 SSP medians at Virginia Key fall within **0.85–1.03 ft** — a 0.18 ft spread, smaller than the uncertainty inside any single scenario (SSP2-4.5 alone spans 0.74–1.23 ft at 17–83%). Emissions choice barely moves mid-century sea level; committed warming and thermal inertia dominate. **A visualizer that lets users toggle emissions scenarios at 2050 and shows a visible difference is overstating what the science supports.**
2. **The top two NOAA scenarios are not AR6 medium-confidence outcomes.** Intermediate-High and High only exist inside AR6's low-confidence, ice-sheet-deep-uncertainty branch. Presenting them beside SSP medians implies a comparability that isn't there.
3. **NOAA Low is not "SSP1-1.9."** It is more optimistic than AR6's most aggressive mitigation median at this location.
4. **Different tails.** NOAA's ranges are conditional percentiles within a fixed GMSL target; AR6's are p-box quantiles across workflows. The 17–83% bands are not constructed the same way and should not be described with identical language.

---

## 4. Why Virginia Key is worse than the global mean

Virginia Key runs **consistently above GMSL in every scenario**, computed from the AR6 regional and global files (medians):

| | GMSL | Virginia Key | Excess |
|---|---|---|---|
| 2050 (all SSPs) | 0.18–0.24 m | 0.26–0.32 m | **+0.08 m (+0.27 ft)** |
| 2100 (all SSPs) | 0.38–0.77 m | 0.54–0.92 m | **+0.15 m (+0.50 ft)** |

The excess is near-constant in absolute terms across scenarios, so in percentage terms it is largest under mitigation: **+41% under SSP1-1.9, +20% under SSP5-8.5** at 2100. Miami does not escape the regional penalty by cutting emissions — it just becomes a bigger share of a smaller number.

**Decomposition** (derived: `ar6-regional-confidence` minus `ar6-regional_novlm-confidence`, same station, same quantile — this is the one computed quantity in this note):

- **Vertical land motion: +0.100 m (0.33 ft) by 2100, +0.154 m (0.51 ft) by 2150**, an implied **1.05 mm/yr of subsidence**, scenario-independent (identical under SSP2-4.5 and SSP5-8.5, as expected for a geological process).
- **Remaining ≈ +0.05 m: sterodynamic + fingerprint.** This is ocean-circulation-driven dynamic sea level — the Gulf Stream / AMOC term — plus the gravitational-rotational-deformational fingerprint of Greenland and Antarctic mass loss. AR6 Ch. 9 assesses AMOC decline over the 21st century as *very likely*, which raises dynamic sea level along the US Southeast and Mid-Atlantic. This is a genuine regional risk amplifier and it is **not** captured by a global-mean bathtub fill.

**Observed rate for sanity-checking:** NOAA's published trend at 8723214 is **1.26 ± 0.04 in/decade (3.20 ± 0.10 mm/yr)** over 1931–2025 (record spliced from stations 8723170 and 8723080). Note the AR6 medians already imply a substantially faster forward rate — ~0.29 m over 2020–2050 under SSP2-4.5 is ~7 mm/yr. Acceleration is the whole story; a linear extrapolation of the historical trend will badly under-predict.

---

## 5. Deep uncertainty and the SSP5-8.5 low-confidence branch

### Why the branch exists

AR6 WG1 Ch. 9 Executive Summary:

> "Higher amounts of GMSL rise before 2100 could be caused by earlier-than-projected disintegration of marine ice shelves, the abrupt, widespread onset of marine ice sheet instability and marine ice cliff instability around Antarctica, and faster-than-projected changes in the surface mass balance and discharge from Greenland. These processes are characterized by deep uncertainty arising from limited process understanding, limited availability of evaluation data, uncertainties in their external forcing and high sensitivity to uncertain boundary conditions and parameters. In a low-likelihood, high-impact storyline, under high emissions such processes could in combination contribute more than one additional metre of sea level rise by 2100." {9.6.3, Box 9.4}

"Deep uncertainty" is a technical term here: the probability distribution itself is not agreed on. That is why AR6 publishes these separately, at *low confidence*, only for SSP1-2.6 / SSP2-4.5 / SSP5-8.5, and declines to fold them into the headline likely ranges.

### What it does to the numbers at Virginia Key (ft)

| Year | SSP5-8.5 medium | SSP5-8.5 **low confidence** |
|---|---|---|
| 2050 | 1.03 [0.81–1.33] | 1.06 [0.80–1.59], 5–95: [0.65–2.11] |
| 2100 | 3.01 [2.37–4.02] | 3.43 [2.37–5.71], 5–95: [2.02–**8.39**] |
| 2150 | 5.05 [3.59–7.22] | 7.50 [3.59–**18.38**], 5–95: [2.99–**20.78**] |

The **median barely moves** (3.01 → 3.43 ft at 2100). The **upper tail explodes** (4.02 → 5.71 ft at 17–83%; 4.93 → 8.39 ft at 5–95%). By 2150 the 83rd percentile is 18 ft. That asymmetry *is* the finding, and it is what a visualizer must communicate.

### How to present it — and how not to

**Do not** add "SSP5-8.5 low confidence" as a sixth notch on the same scenario slider. That silently tells the user it is simply "the worst case," on the same epistemic footing as the others, and invites the reading that everything between Low and it is equally likely.

**Do** present it as a **separate deep-uncertainty band**:

- Render it as a distinct, visually secondary layer — hatched or dashed water surface, desaturated, matching the folder's provenance convention where hatching means "not a solid published value."
- Give it its own toggle, off by default, labelled something like **"Show ice-sheet deep uncertainty (AR6 low confidence)"** — never "worst case."
- When enabled, show the *band*, not a single surface, because the median is nearly unchanged and the tail is the point.
- Caption verbatim: *"AR6 assigns low confidence to these values. The probability distribution itself is disputed — this is not a 95% confidence interval in the usual sense. Source: IPCC AR6 WG1 Ch. 9, Box 9.4."*

---

## 6. Committed and irreversible rise — the part that matters most for Miami

AR6 WG1 Ch. 9 Executive Summary:

> "Beyond 2100, GMSL will continue to rise for centuries due to continuing deep-ocean heat uptake and mass loss of the Greenland and Antarctic ice sheets, and will remain elevated for thousands of years (high confidence)." {9.6.3}

The AR6 low-confidence files extend to 2300, and the Virginia Key values are in the CSV:

| Scenario (low confidence) | 2300 median | 17–83% |
|---|---|---|
| SSP1-2.6 | **6.50 ft** | 3.40 – 11.83 ft |
| SSP5-8.5 | **19.62 ft** | 6.32 – 58.94 ft |

**Even the strong-mitigation branch commits this location to a median ~6.5 ft by 2300.** Mitigation changes the *rate* and the *tail*, not the *direction*. On human timescales this is one-way: there is no scenario in AR6 in which sea level at Virginia Key returns to its 2005 position. Any framing in the visualizer that implies flooding is avoidable rather than *deferrable and manageable* misrepresents the assessment.

---

## 7. Extreme sea level / return-period compression (Task 3)

### The AR6 headline finding

> "Extreme sea levels that occurred once per century in the recent past will occur annually or more frequently at about 19–31% of tide gauges by 2050 and at about 60% (SSP1-2.6) to 82% (SSP5-8.5) of tide gauges by 2100 (medium confidence)." {9.6.4}

This is the mechanism that matters more than mean rise: **a modest shift in the mean produces a very large shift in exceedance frequency**, because the extreme-value distribution is steep. Miami's low tidal range (mean range 2.04 ft, great diurnal range 2.24 ft) makes this compression especially sharp — a small vertical offset consumes a large fraction of the tidal envelope.

AR6 did not publish a per-gauge return-period curve for Virginia Key in a form retrievable here, but NOAA's HTF products give the same signal at station resolution.

### Local flood thresholds (`floodlevels.json`, station 8723214)

| Threshold | ft above station datum | **ft NAVD88** | ft above MHHW |
|---|---|---|---|
| NOS minor | 14.07 | **1.92** | 1.69 |
| NOS moderate | 15.04 | **2.89** | 2.66 |
| NOS major | 16.27 | **4.12** | 3.89 |

(NAVD88 = station datum − 12.15 ft. These are directly usable as water-surface elevations in the visualizer.)

### Observed baseline

Mean **2.2 minor-flood days/yr since 2005**; recent years 2019: 9, 2023: 6, 2024: 5, 2025: 7. Moderate flooding has occurred once in the modern record (2017); **major flooding has never been recorded** at this gauge in the 1994–2025 count record.

### Projected flood days per year (NOAA 2022 scenarios, `htf_projection_decadal`)

**Minor (nuisance) flooding:**

| Decade | Low | Int-Low | Int | Int-High | High |
|---|---|---|---|---|---|
| 2020 | 3 | 3 | 3 | 3 | 3 |
| 2030 | 5 | 6 | 6 | 6 | 7 |
| 2040 | 9 | 10 | 15 | 20 | 25 |
| 2050 | 20 | 25 | **35** | **60** | **95** |
| 2060 | 30 | 55 | 90 | 175 | 270 |
| 2070 | 45 | 100 | 195 | 335 | 365 |
| 2080 | 65 | 160 | 320 | 365 | 365 |
| 2090 | 90 | 230 | 365 | 365 | 365 |
| 2100 | 125 | 300 | **365** | **365** | **365** |

**Moderate flooding:**

| Decade | Low | Int-Low | Int | Int-High | High |
|---|---|---|---|---|---|
| 2050 | 0 | 1 | 1 | 2 | 4 |
| 2070 | 1 | 4 | 15 | 95 | 245 |
| 2100 | 6 | 50 | **350** | 365 | 365 |

**Major flooding** (never observed historically):

| Decade | Low | Int-Low | Int | Int-High | High |
|---|---|---|---|---|---|
| 2070 | 0 | 0 | 0 | 2 | 15 |
| 2080 | 0 | 0 | 1 | 25 | 210 |
| 2100 | 0 | 0 | **70** | **360** | 365 |

### Reading this

Under the **Intermediate** scenario, minor flooding at Virginia Key goes from ~3 days/yr today to **every day of the year by 2090**, and *major* flooding — an event with no precedent in the instrumental record — occurs **70 days/yr by 2100**. That is the return-period compression AR6 describes, expressed in NOAA's station-level terms: today's rare event becomes the ordinary daily condition.

The `htf_likely_decadal_scenarios` product brackets 2050 minor flooding at Virginia Key at **35–60 days/yr** (Intermediate to Intermediate-High), which is NOAA's own "likely" range for mid-century.

**Important limitation:** NOAA HTF counts are driven by *tide + mean sea level* crossing a threshold. They do **not** include storm surge or rainfall. The compound coastal + pluvial event this visualizer is built to explore is worse than these counts imply, and the storm-drain backflow problem begins well before the minor threshold is reached, because outfalls lose gravity drainage when tailwater approaches crown elevation.

---

## 8. Recommendation for the visualizer

### Default slider: **NOAA 2022 scenarios, defaulting to Intermediate-High**

Reasons:

1. **Station-native and datum-consistent.** Computed for gauge 8723214 on the same 2005 footing as the rest of the folder, decadal to 2150, with matching HTF flood-day counts — so the water-surface slider and the flood-frequency panel move together from one scenario family.
2. **It matches regional planning practice.** The Southeast Florida Regional Climate Compact's Unified Sea Level Rise Projection guidance recommends the **NOAA Intermediate-High curve for non-critical infrastructure and the NOAA High curve for critical infrastructure** (nuclear, major roads, bridges, utilities), referenced to the Key West gauge on a 2000 baseline. Southeast Florida does *not* plan to the median. A visualizer that defaults to Intermediate would show users something more optimistic than what their own county uses to design.
3. **Outcome-defined scenarios are the right primitive for a screening tool.** The user's question is "what happens at 2 ft?", not "what happens under SSP3-7.0?"

Default the **year** to **2050**, not 2100 — it is inside the service life of the storm drains and buildings in this dataset, and mid-century is where the scenarios are still close enough that the answer is robust.

### Secondary layer: AR6 SSP medium confidence

Offer an **"emissions view"** toggle exposing the five SSP medians with 17–83% bands. This answers "does cutting emissions help here, and by when?" — and honestly shows that **it barely helps by 2050 (0.85–1.03 ft across all five SSPs) and helps enormously by 2100 (1.78 vs 3.01 ft)**. That is a genuinely useful and underappreciated message, and it is the thing the NOAA scenarios structurally cannot express.

### Third, visually separate: AR6 SSP5-8.5 low confidence

As a hatched deep-uncertainty band, per §5. Off by default.

### Honest captions

For the default slider:

> **Sea level rise at Virginia Key (NOAA gauge 8723214), feet above the 2005 mean.**
> NOAA 2022 scenarios are *outcome-defined*: each is a chosen amount of global rise by 2100, regionalised to this gauge. They are not predictions and carry no probability on their own — NOAA states that "there are no probabilities that can be assigned directly to each of the Sea Level Scenarios." Intermediate-High is shown by default because it is the curve Southeast Florida uses for infrastructure planning.
> This location rises **faster than the global average** — about +0.5 ft above global mean by 2100, of which ~0.33 ft is land subsidence (~1.05 mm/yr) and the rest is ocean circulation and ice-sheet gravitational effects.

For the year control, near 2050:

> Before ~2060, emissions scenario barely matters: all five IPCC SSP pathways give 0.85–1.03 ft at this gauge in 2050. Mid-century sea level is already committed. What emissions change is the *second half* of the century.

For the deep-uncertainty toggle, the §5 caption verbatim.

Never label any layer "worst case." The AR6 SSP5-8.5 low-confidence 95th percentile at 2150 is 20.78 ft and at 2300 the 83rd percentile is 58.94 ft; there is no defensible worst case to draw, and implying one is drawn is the specific dishonesty this panel exists to avoid.

---

## Sources

- IPCC AR6 WG1 Chapter 9, *Ocean, Cryosphere and Sea Level Change* — https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-9/ (ES statements, §9.6.3, §9.6.4, Box 9.4, Table 9.9)
- Garner et al., *IPCC AR6 Sea Level Projections*, Zenodo — https://doi.org/10.5281/zenodo.6382554 (regional + global confidence NetCDF; `ar6-regional-confidence.zip`, `ar6-regional_novlm-confidence.zip`, `ar6.zip`)
- NASA/JPL IPCC AR6 Sea Level Projection Tool — https://sealevel.nasa.gov/ipcc-ar6-sea-level-projection-tool (front end for the above dataset)
- Rutgers-ESSP, *Guide to the IPCC AR6 Sea Level Projections* — https://github.com/Rutgers-ESSP/IPCC-AR6-Sea-Level-Projections (file structure and workflow documentation)
- NOAA 2022 Sea Level Rise Technical Report (NOAA NOS Tech Rpt 01) — https://sealevel.globalchange.gov/internal_resources/756/noaa-nos-techrpt01-global-regional-SLR-scenarios-US.pdf
- NOAA 2022 SLR Technical Report *Application Guide* — https://earth.gov/sealevel/us/internal_resources/784/noaa-nos-techrpt02-global-regional-SLR-scenarios-US-application-guide.pdf (scenario/SSP relationship, exceedance probabilities)
- NOAA CO-OPS API, station 8723214:
  - SLR projections — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/slr_projections.json?station=8723214
  - Baseline offsets — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/slr_projectionOffsets.json?station=8723214
  - Sea level trends — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/sealvltrends.json?station=8723214
  - HTF decadal projections — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/htf/htf_projection_decadal.json?station=8723214
  - HTF likely decadal scenarios — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/htf/htf_likely_decadal_scenarios.json?station=8723214
  - HTF observed annual counts — https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/htf/htf_annual.json?station=8723214
  - Flood thresholds — https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/8723214/floodlevels.json
  - Tidal datums — https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/8723214/datums.json
- Southeast Florida Regional Climate Change Compact, *Unified Sea Level Rise Projection — Guidance Report* (2019/2020 update) — https://southeastfloridaclimatecompact.org/wp-content/uploads/2020/04/Sea-Level-Rise-Projection-Guidance-Report_FINAL_02212020.pdf

*Compiled 2026-08-20.*
