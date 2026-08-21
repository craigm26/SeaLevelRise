#!/usr/bin/env python3
"""Re-extract the NFIP claims summary from OpenFEMA v3 and diff it against the
v2-derived file already in the repo.

Why this exists
---------------
OpenFEMA v2 (`FimaNfipClaims`, `FimaNfipPolicies`) is frozen and is removed
after **2026-10-15**. After that date every insurance figure in this package
becomes unreproducible from its stated source, which for a package whose whole
claim is "every number traces to a primary source" is the worst available
failure mode. The successor entities are `NfipClaims` and `NfipPolicies` (v3).

This script does not assume the migration is clean. It rebuilds the summary
from v3 and prints a field-by-field diff against
`data/insurance/nfip_claims_summary_by_zip.csv`. A migration is only finished
when you can show the numbers did not move -- or say exactly where they did.

Usage:  python3 scripts/fetch_nfip_v3.py [--write]
        --write also emits data/insurance/nfip_claims_summary_by_zip_v3.csv
"""
import argparse, csv, json, os, sys, urllib.parse, urllib.request

API = "https://www.fema.gov/api/open/v3/NfipClaims"
ZIPS = ["33128", "33130", "33131", "33132", "33137"]
PAGE = 1000
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2_CSV = os.path.join(REPO, "data", "insurance", "nfip_claims_summary_by_zip.csv")
V3_CSV = os.path.join(REPO, "data", "insurance", "nfip_claims_summary_by_zip_v3.csv")

FIELDS = ("reportedZipCode,yearOfLoss,amountPaidOnBuildingClaim,"
          "amountPaidOnContentsClaim,amountPaidOnIncreasedCostOfComplianceClaim,"
          "ratedFloodZone")


def fetch_zip(z):
    """Page through every claim for one ZIP. v3 keeps the v2 $skip behaviour,
    so keep the page size at 1000; larger pages 503 after ~60 s."""
    out, skip = [], 0
    while True:
        q = urllib.parse.urlencode({
            "$filter": f"reportedZipCode eq '{z}'",
            "$select": FIELDS,
            "$top": PAGE,
            "$skip": skip,
            "$metadata": "off",
        })
        with urllib.request.urlopen(f"{API}?{q}", timeout=120) as r:
            rows = json.load(r).get("NfipClaims", [])
        out.extend(rows)
        if len(rows) < PAGE:
            return out
        skip += PAGE


def summarise(rows):
    """Total paid = building + contents + ICC, matching the v2 derivation."""
    paid = []
    years, zones = [], {}
    for r in rows:
        p = sum(float(r.get(k) or 0) for k in (
            "amountPaidOnBuildingClaim",
            "amountPaidOnContentsClaim",
            "amountPaidOnIncreasedCostOfComplianceClaim"))
        paid.append(p)
        y = r.get("yearOfLoss")
        if y:
            years.append(int(y))
        z = (r.get("ratedFloodZone") or "").strip()
        if z:
            zones[z] = zones.get(z, 0) + 1
    n = len(paid)
    tot = sum(paid)
    return {
        "claims": n,
        "total_paid_usd": round(tot),
        "mean_paid_usd": round(tot / n) if n else 0,
        "max_paid_usd": round(max(paid)) if paid else 0,
        "first_year": min(years) if years else "",
        "last_year": max(years) if years else "",
        "top_rated_zone": max(zones, key=zones.get) if zones else "",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    new = {}
    for z in ZIPS:
        rows = fetch_zip(z)
        new[z] = summarise(rows)
        print(f"  {z}: {len(rows)} claim records from v3", file=sys.stderr)

    old = {}
    if os.path.exists(V2_CSV):
        with open(V2_CSV, newline="") as f:
            for r in csv.DictReader(f):
                old[r["zip"]] = r

    cols = ["claims", "total_paid_usd", "mean_paid_usd", "max_paid_usd",
            "first_year", "last_year", "top_rated_zone"]
    drift = 0
    print(f"\n{'zip':<7}{'field':<18}{'v2 (in repo)':>16}{'v3 (live)':>16}   status")
    print("-" * 74)
    for z in ZIPS:
        for c in cols:
            o = str(old.get(z, {}).get(c, "")).strip()
            n = str(new[z][c])
            same = (o == n)
            if not same:
                drift += 1
            print(f"{z:<7}{c:<18}{o:>16}{n:>16}   {'ok' if same else 'DRIFT'}")

    if args.write:
        with open(V3_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["zip"] + cols)
            for z in ZIPS:
                w.writerow([z] + [new[z][c] for c in cols])
        print(f"\nwrote {V3_CSV}", file=sys.stderr)

    print(f"\n{drift} field(s) differ between v2 and v3.")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
