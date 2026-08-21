# GAP C — NFIP policy extract for downtown Miami ZIPs

ZIPs: 33128, 33130, 33131, 33132, 33137 (City of Miami / Brickell / Edgewater).
Source: OpenFEMA **v2** `FimaNfipPolicies` — <https://www.fema.gov/api/open/v2/FimaNfipPolicies>
Files: `nfip_policies_full_<zip>.csv`, one row per policy record, 30 columns.

## 1. What the endpoint will actually do (measured, not assumed)

The dataset holds **73,601,802** records behind a ~60 s gateway budget. Every shape below was tested against a `reportedZipCode` filter, spaced out to rule out rate limiting:

| Query shape | Result |
|---|---|
| `$top=1` / `$top=10`, narrow `$select` | OK, ~3 s |
| **`$top=500`, `$skip=0`, 30-field `$select`, no `$orderby`** | **OK, 10–70 s — the shape used** |
| `$top=500`, `$skip=500` | OK, 40–90 s |
| `$top=1000`, any `$select` | 503 at ~61 s |
| `$top=2000` | 503 |
| `$orderby=id`, any `$top` (incl. 500) | 503 at ~61 s — sorting 73.6 M rows exceeds the budget |
| `$skip>=900` | 503 — either instant load-shed or a 61 s timeout |
| `$inlinecount=allpages` **with** a ZIP filter | 503 — **no server-side count is available** |
| `$inlinecount=allpages` **without** a filter | OK — this is how the 73.6 M total was read |

Also tested and rejected as alternatives:

* **`NfipPolicies` v3** (`/api/open/v3/NfipPolicies`, 74,349,525 records, the non-deprecated successor): identical limits — `$skip=1000` still 503s at 61 s. No benefit today. Worth revisiting because **v2 is deprecated: frozen at 2026-06-01 and removed after 2026-10-15.**
* **Partitioning by `policyEffectiveDate`** (windowed `ge`/`lt` filters at `$skip=0`): *slower*, not faster — adding date comparisons to the filter pushed single windows past the 170 s client timeout. Abandoned.

## 2. Consequences for completeness — read this before trusting the row counts

**a. There is no denominator.** `$inlinecount` with a ZIP filter always 503s, so FEMA will not tell us how many policy records exist for a ZIP. Every '% complete' figure below is therefore *unknowable from the API*, not merely unmeasured.

**b. `$skip` pagination dead-ends at 1000.** Straight pagination stopped hard at `$skip=1000` on every ZIP.

**c. But the result order is unstable, and that is exploitable.** Because `$orderby` cannot be used, repeated identical calls return *different* row sets. Re-issuing the same `$skip=0` / `$skip=500` pair therefore keeps surfacing new records. The extract was run as **3 repeat-sampling rounds over all five ZIPs, plus a 4th targeted round on the three still yielding new records**, merged and de-duplicated on `id`, which pushed each ZIP well past the 1000-record pagination ceiling.

**d. Marginal yield is the only completeness signal available.** If a fresh 500-row draw is still ~100 % new records, the pool is far larger than what we hold. As the share of new records falls, we are approaching the reachable set. Those per-draw figures are reported below so the coverage claim can be audited.

## 3. Per-ZIP results

| ZIP | Server count | Records retrieved | % complete | Last draw: new / sampled | Reached end of results |
|---|---|---:|---|---:|---|
| 33128 | not obtainable (`$inlinecount` 503s) | 2,355 | unknown — no server count obtainable; still accumulating | 141 / 500 | False |
| 33130 | not obtainable (`$inlinecount` 503s) | 3,933 | unknown — no server count obtainable; still accumulating | 433 / 500 | False |
| 33131 | not obtainable (`$inlinecount` 503s) | 2,758 | unknown — no server count obtainable; still accumulating | 344 / 500 | False |
| 33132 | not obtainable (`$inlinecount` 503s) | 2,216 | unknown — no server count obtainable; still accumulating | 0 / 500 | False |
| 33137 | not obtainable (`$inlinecount` 503s) | 3,613 | unknown — no server count obtainable; still accumulating | 500 / 500 | False |

Because the last draw for most ZIPs was still returning a high share of new records, these extracts should be read as **large samples, not censuses**. They are, however, unbiased in the sense that nothing in the query selects on flood zone, elevation, premium or date — the only filter is the ZIP itself.

## 4. Fields included

30 fields per record:

`id`, `elevationCertificateIndicator`, `lowestFloorElevation`, `baseFloodElevation`, `elevationDifference`, `lowestAdjacentGrade`, `elevatedBuildingIndicator`, `originalConstructionDate`, `postFIRMConstructionIndicator`, `reportedZipCode`, `reportedCity`, `censusTract`, `latitude`, `longitude`, `floodZoneCurrent`, `ratedFloodZone`, `crsClassCode`, `rateMethod`, `occupancyType`, `numberOfFloorsInInsuredBuilding`, `construction`, `buildingReplacementCost`, `primaryResidenceIndicator`, `totalBuildingInsuranceCoverage`, `totalContentsInsuranceCoverage`, `totalInsurancePremiumOfThePolicy`, `policyCost`, `policyCount`, `policyEffectiveDate`, `policyTerminationDate`

## 5. Populated-ness of the high-value elevation fields (% non-null)

These are the only public signal about first-floor elevation, so they were prioritised in the `$select` list.

| ZIP | n | `lowestFloorElevation` | `elevationCertificateIndicator` | `baseFloodElevation` | `elevationDifference` | `lowestAdjacentGrade` | `originalConstructionDate` | `elevatedBuildingIndicator` | `latitude` | `longitude` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 33128 | 2,355 | 69.8% | 14.0% | 67.7% | 67.7% | 69.1% | 100.0% | 100.0% | 100.0% | 100.0% |
| 33130 | 3,933 | 62.8% | 10.5% | 58.0% | 57.9% | 61.8% | 100.0% | 100.0% | 100.0% | 100.0% |
| 33131 | 2,758 | 65.5% | 12.7% | 62.6% | 62.5% | 64.8% | 100.0% | 100.0% | 100.0% | 100.0% |
| 33132 | 2,216 | 69.6% | 12.5% | 69.4% | 69.5% | 69.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 33137 | 3,613 | 41.7% | 14.8% | 40.9% | 41.3% | 40.7% | 100.0% | 100.0% | 100.0% | 100.0% |

### Verdict on the fields that matter

* `lowestFloorElevation` — **60.3%** populated (8,971 of 14,875).
* `elevationCertificateIndicator` — **12.8%** populated (1,899 of 14,875).
* `baseFloodElevation` — **57.9%** populated (8,618 of 14,875).
* `elevationDifference` — **58.0%** populated (8,628 of 14,875).
* `lowestAdjacentGrade` — **59.5%** populated (8,845 of 14,875).
* `originalConstructionDate` — **100.0%** populated (14,873 of 14,875).
* `elevatedBuildingIndicator` — **100.0%** populated (14,875 of 14,875).
* `latitude` — **100.0%** populated (14,875 of 14,875).
* `longitude` — **100.0%** populated (14,875 of 14,875).

**`lowestFloorElevation`, `baseFloodElevation`, `elevationDifference` and `lowestAdjacentGrade` are populated on ~58-60% of records overall** (62-70% in ZIPs 33128/33130/33131/33132, but only ~41% in 33137) — this is a genuinely usable first-floor-elevation signal for the study area, and it is the single most valuable thing in this extract. `elevationCertificateIndicator` is much sparser (~1 in 5), so treat an absent certificate flag as unknown, not as 'no certificate'.

### Caveats on those fields

* Elevations are integers/one-decimal values in **feet**, and the vertical datum is not carried in the API. Do not mix them with NAVD88 LiDAR values without checking.
* **`latitude`/`longitude` are redacted to one decimal place** (every downtown record reads ~`25.8, -80.2`, i.e. ~11 km precision). They are useless for building-level placement — use `censusTract` for geographic joins instead.
* Records are **policy-term transactions**, not unique buildings: one building re-insured over many years appears many times. De-duplicate before counting structures.
