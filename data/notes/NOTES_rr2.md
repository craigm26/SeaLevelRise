# GAP B — NFIP Risk Rating 2.0 Florida profile: what worked, what didn't

Output: `nfip_rr2_florida_profile.csv` (120 rows; `metric,geography,value,unit,source_url`)
Raw JSON kept in `_raw/rr2_fl_state.json` and `_raw/rr2_miami_zips.json`.

## Which route worked

| # | Route attempted | Result |
|---|---|---|
| a | `curl` the April-2025 FL state profile PDF with a browser User-Agent + `-L` | **Failed.** HTTP 403 from Akamai (`Access Denied`, `errors.edgesuite.net` reference), 474-byte HTML body. Retried with `Referer`, `Accept`, `Accept-Language`, `Sec-Fetch-*` and `Upgrade-Insecure-Requests` headers — identical 403. |
| a2 | Same for `fema_rr-2.0_04-2025.pdf` and the older `fema_florida-state-profile_03-2021.pdf` | **Failed**, 403. The block is on the whole `www.fema.gov/sites/default/files/...` path from this egress, not on one file. |
| b | `WebFetch` on the PDF URL | **Failed**, 403 passed through from origin. |
| c | `WebFetch` on `fema.gov/flood-insurance/risk-rating/profiles` and `/risk-rating` to find a newer profile link | **Failed**, 403 on the HTML pages too. All of `www.fema.gov` except `/api/open/...` is blocked from here. |
| c2 | Mirrors: `agents.floodsmart.gov` and `www.floodsmart.gov` under both `/sites/default/files/documents/` and `/sites/default/files/` | **Failed**, 404 — FEMA does not mirror state profiles there. |
| c3 | `agents.floodsmart.gov` RR2 fact sheet (Aug 2025) | **Worked** (`rr2_factsheet.pdf`, 255 KB). National figures only — no state breakdown. |
| **d** | **FEMA's own zip-code-level RR2 premium-change analysis, republished as ArcGIS feature services by the ASFPM Flood Science Center** | **Worked — this is the route that produced the CSV.** |

### How route (d) was found
`WebSearch` surfaced the ArcGIS dashboard *"State Totals: Projected Risk Rating 2.0 Premium
Changes - All NFIP & SFH Policies"*. Its item description credits the data to
[FEMA's analysis of NFIP policyholder data](https://www.fema.gov/flood-insurance/risk-rating/profiles).
Drilling the dashboard JSON → web-map items → operational layers gave two services:

* State level — `https://services3.arcgis.com/PwSEIra0zgvwmApz/arcgis/rest/services/All_and_SFH_Policies_by_State/FeatureServer/0`
* ZIP level — `https://services3.arcgis.com/PwSEIra0zgvwmApz/arcgis/rest/services/SFH_and_All_Policies_by_Zip_Code/FeatureServer/1`

Both answer normal ArcGIS REST `query` calls and are **not** behind the Akamai block.

## What was obtained

**Florida, all NFIP policies (n = 1,727,811)**

| Measure | Policies | Percent |
|---|---:|---:|
| Premium **decrease** | 342,109 | 19.80 % |
| Premium **increase** | 1,385,702 | 80.20 % |
| Increase **> $20/month** | 72,842 | 4.22 % |

**Florida, single-family-home policies (n = 921,339)**

| Measure | Policies | Percent |
|---|---:|---:|
| Premium **decrease** | 114,617 | 12.44 % |
| Increase $0–$10/month | 663,931 | — |
| Increase $10–$20/month | 93,940 | — |
| Increase **> $20/month** | 48,851 | 5.30 % |

All 22 individual bands ($100+ decrease through $100+ increase), as counts **and**
percents, for both the all-policy and SFH series, are in the CSV.

**Downtown Miami study-area ZIPs (SFH policies only):**

| ZIP | SFH policies | Decrease | > $20/mo increase |
|---|---:|---:|---:|
| 33128 | 24 | 8 | 0 |
| 33130 | 32 | 8 | 0 |
| 33131 | *suppressed* (`-9999` = unknown/withheld ZIP aggregate) | | |
| 33132 | *suppressed* (`-5555` = fewer than 5 policies) | | |
| 33137 | 349 | 115 | 24 |

The small counts are real and expected: this layer covers **single-family homes only**, and
downtown Miami's NFIP book is overwhelmingly condominium/RCBAP and commercial. Use the
GAP C extract (`nfip_policies_full_<zip>.csv`) for the full policy picture in these ZIPs.

## What could NOT be obtained

1. **Florida current average premium (dollars).** Not in the ArcGIS services, which carry
   only *change* distributions. Requires the blocked state-profile PDF.
2. **Florida full-risk average premium (dollars).** Same reason. Note that
   `FimaNfipPolicies` has **no** full-risk-rate field — the closest proxies are
   `rateMethod` and `subsidizedRateType`, which flag *how* a policy is rated, not what its
   full-risk rate would be. So OpenFEMA cannot produce a true "full-risk average premium"
   even with unlimited query budget.
3. **Miami-Dade county-level RR2 figures.** FEMA published RR2 profiles at state and ZIP
   granularity, not county. County-level numbers would have to be aggregated up from ZIPs.

### Only dollar figures obtained (national, from the fact sheet — included in the CSV, clearly marked)
* Legacy method: average increase **$8/month/year**.
* Under RR2.0, **96 %** of policyholders see a decrease or an increase ≤ $20/month.
* Policies that decreased did so by **$86/month** on average.
* Statutory cap: **18 %/year** until the full-risk rate is reached.

## Vintage caveat — read before using

The state and ZIP band data are FEMA's **projected/pre-implementation** analysis: they
compare **May 2020 premiums (legacy rating)** against modelled RR2.0 full-risk rates. The
underlying ArcGIS items were last modified **October 2021**. They are therefore *not* the
April-2025 profile and will not match it exactly — RR2.0 has been phasing in under the
18 %/year cap since October 2021, so realised 2025–26 premiums sit somewhere between the
two. Treat these as **direction and distribution of change, not current premium levels**,
and mark them as interpolated/older-vintage in any provenance colour-coding.
