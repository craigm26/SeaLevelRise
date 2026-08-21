# OpenFEMA v2 → v3 migration

**Run:** 2026-08-20 · **Script:** `scripts/fetch_nfip_v3.py` · **Status:** verified, numbers move

## Why

OpenFEMA v2 (`FimaNfipClaims`, `FimaNfipPolicies`) is **removed after 2026-10-15**.
Confirmed against FEMA's own registry rather than documentation:

```
GET /api/open/v1/OpenFemaDataSets?$top=1000
```

| Entity | Version | depDate | Records |
|---|---|---|---|
| `FimaNfipClaims` | v2 | **2026-10-15** | 2,721,780 |
| `NfipClaims` | v3 | none | 2,724,656 |
| `FimaNfipPolicies` | v2 | **2026-10-15** | 73,601,802 |
| `NfipPolicies` | v3 | none | 74,349,525 |

After that date every insurance figure in this package becomes unreproducible from
its stated source unless the extract runs against v3.

## The finding: this migration is not cosmetic

The point of migrating early was to run both versions side by side and prove the
numbers did not move. **They moved.** Re-extracting the five downtown ZIPs:

| ZIP | Field | v2 (repo) | v3 (live) |
|---|---|---|---|
| 33128 | total_paid_usd | 1,866,406 | **2,000,508** |
| 33128 | mean_paid_usd | 39,711 | **42,564** |
| 33132 | claims | 89 | **90** |
| 33132 | mean_paid_usd | 14,059 | **13,903** |
| 33132 | last_year | 2022 | **2026** |

Everything else — all of 33130, 33131, 33137, every claim count elsewhere, every
max payment, every rated zone — is identical.

### It is a freeze artifact, not a schema difference

The decisive test was querying **v2 live today** with identical logic:

```
33128  v2-LIVE claims=47 paid=1,866,406 last=2025   <- matches this repo exactly
33128  v3-LIVE claims=47 paid=2,000,508 last=2025
33132  v2-LIVE claims=89 paid=1,251,284 last=2022   <- matches this repo exactly
33132  v3-LIVE claims=90 paid=1,251,284 last=2026
```

v2 still returns exactly what this package published, because **v2 has been frozen
since 2026-06-01**. v3 has kept ingesting. So the deltas are not a v2/v3 field
semantics problem and not an extraction bug — they are three months of real NFIP
activity that the frozen endpoint cannot see:

1. **33128** — a payment was revised *upward* by $134,102 on an already-recorded
   claim, with no new claim. NFIP claims are settled and supplemented over years;
   a claim's paid amount is not final when it first appears.
2. **33132** — one new claim with loss year 2026 and $0 paid to date, so the total
   is unchanged while the count and the mean both move. Either open or denied.

### What this means for the package

The insurance figures published on the site are an **as-of-2026-06-01 snapshot**,
not current. That was invisible before this run. Any figure derived from NFIP
claims needs an as-of date attached to be honest, and the v3 entities expose an
`asOfDate` field for exactly this.

Headline effect: the site's claims total across the five ZIPs becomes **761, not
760**, and total paid rises by $134,102.

## Not yet done — an open decision

`data/insurance/nfip_claims_summary_by_zip_v3.csv` is written alongside the v2
file rather than replacing it, and **`data.json` still carries the v2 figures**, so
the site is internally consistent but three months stale. Promoting v3 means
regenerating the claims-by-year payload too, or the summary and the detail chart
will disagree. Do both or neither.

## Reproduce

```bash
python3 scripts/fetch_nfip_v3.py           # diff only
python3 scripts/fetch_nfip_v3.py --write   # also writes the v3 CSV
```

Exit status is non-zero when any field differs, so it works as a drift check.

## Carried-over v3 gotchas

* `$skip` paging still 503s above ~1000 rows per page. Page size stays at 1000.
* Field names are unchanged between v2 and v3 for every field used here
  (`reportedZipCode`, `yearOfLoss`, `amountPaidOn*Claim`, `ratedFloodZone`).
* Total paid = building + contents + ICC, matching the original v2 derivation.
* `www.fema.gov` remains 403 for everything except `/api/open/...` from this host.
