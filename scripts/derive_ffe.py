#!/usr/bin/env python3
"""
Derive a first-floor elevation estimate for every building, with provenance.

There is no public register of first-floor elevations. But NFIP policy records carry
`lowestFloorElevation` and `lowestAdjacentGrade`, and the difference between them is the
height of the first floor above the dirt beside the building. That difference is stable
within a construction era and flood zone, so it can be measured locally and applied to
buildings that have no certificate:

    FFE = grade_from_LiDAR + median(LFE - LAG) for this era x zone

and for post-FIRM buildings with a published BFE, raised to the regulatory floor where that
is higher:

    FFE = max(grade + slab, BFE + median(LFE - BFE))

The honest part is step 3. 77% of downtown buildings are in FEMA zone X, where no elevation
certificate is required, so fewer than twenty usable local observations exist for that entire
population. Those buildings get a borrowed median and are tagged `no_local_observations` —
they must render hatched downstream.

    pip install rasterio shapely pyproj numpy --break-system-packages
    python3 scripts/derive_ffe.py --src /path/to/miami_flood_data

Writes building_ffe_estimates.csv (one row per building) into --src.
"""
import argparse, csv, json, os, statistics as st, sys
from collections import defaultdict

M2FT = 3.28084
ZIPS = ['33128', '33130', '33131', '33132', '33137']
POST_FIRM_YEAR = 1975      # derived, not assumed — see below


def load_nfip(src):
    rows = []
    for z in ZIPS:
        p = os.path.join(src, f'nfip_policies_full_{z}.csv')
        if os.path.exists(p):
            rows += list(csv.DictReader(open(p)))
    if not rows:
        sys.exit('no nfip_policies_full_<zip>.csv found in --src')
    # Records are policy-TERM transactions, not buildings. Collapse to distinct
    # building signatures before computing any statistic, or long-held policies
    # dominate the medians.
    seen, ded = set(), []
    for r in rows:
        sig = (r.get('censusTract'), r.get('lowestFloorElevation'), r.get('lowestAdjacentGrade'),
               r.get('baseFloodElevation'), r.get('originalConstructionDate'),
               r.get('occupancyType'), r.get('numberOfFloorsInInsuredBuilding'))
        if sig in seen:
            continue
        seen.add(sig)
        ded.append(r)
    print(f'nfip: {len(rows)} policy-term records -> {len(ded)} distinct building signatures')
    return ded


def zone_of(r):
    z = (r.get('ratedFloodZone') or r.get('floodZoneCurrent') or '').strip().upper()
    if z.startswith('V'):
        return 'VE'
    if z.startswith('AH'):
        return 'AH'
    if z.startswith('A'):
        return 'AE'
    if z[:1] in ('X', 'B', 'C'):
        return 'X'
    return 'NA'


def verify_firm_cutoff(ded):
    """The post-FIRM cutoff is derived from the data, not assumed. NFIP's own flag flips
    cleanly at construction year 1975 for these communities."""
    by = defaultdict(lambda: [0, 0])
    for r in ded:
        d = r.get('originalConstructionDate') or ''
        if len(d) >= 4 and d[:4].isdigit():
            y = int(d[:4])
            if 1970 <= y <= 1980:
                by[y][0 if str(r.get('postFIRMConstructionIndicator')) == 'True' else 1] += 1
    print('  post/pre-FIRM counts by construction year:')
    for y in sorted(by):
        print(f'    {y}  post={by[y][0]:4d}  pre={by[y][1]:4d}')


def build_strata(ded):
    def f(r, k):
        v = r.get(k)
        try:
            return float(v) if v not in (None, '', 'NA') else None
        except ValueError:
            return None

    slab, free = defaultdict(list), defaultdict(list)
    for r in ded:
        d0 = r.get('originalConstructionDate') or ''
        yr = int(d0[:4]) if len(d0) >= 4 and d0[:4].isdigit() else None
        era = 'post' if (yr and yr >= POST_FIRM_YEAR) else ('pre' if yr else None)
        if not era:
            continue
        z = zone_of(r)
        lfe, lag, bfe = f(r, 'lowestFloorElevation'), f(r, 'lowestAdjacentGrade'), \
            f(r, 'baseFloodElevation')
        if lfe is not None and lag is not None and -5 < lfe - lag < 30:
            slab[(era, z)].append(lfe - lag)
        if lfe is not None and bfe not in (None, 0) and -20 < lfe - bfe < 40:
            free[(era, z)].append(lfe - bfe)

    SLAB, FREE = {}, {}
    print(f'\n  {"era":5s} {"zone":5s} {"n":>6s} {"p25":>7s} {"median":>7s} {"p75":>7s}')
    for k in sorted(slab, key=lambda k: -len(slab[k])):
        v = sorted(slab[k])
        if len(v) < 20:                      # too thin to be a stratum
            continue
        SLAB[k] = (st.median(v), len(v), v[len(v) // 4], v[3 * len(v) // 4])
        print(f'  {k[0]:5s} {k[1]:5s} {len(v):6d} {v[len(v)//4]:7.2f} '
              f'{st.median(v):7.2f} {v[3*len(v)//4]:7.2f}')
    for k in free:
        if len(free[k]) >= 20:
            FREE[k] = st.median(free[k])
    if ('pre', 'AE') not in SLAB:
        sys.exit('no pre-FIRM AE stratum — cannot establish a fallback')
    return SLAB, FREE


def sample_grade(src, fc):
    """Lowest adjacent grade = 5th percentile of 1 m DEM cells in a 3 m collar outside the
    wall line. The 5th percentile rather than the minimum, because single-cell minima in a
    dense urban DEM pick up gutters, tree pits and stairwells."""
    import numpy as np, rasterio, warnings
    from rasterio.mask import mask as rmask
    from shapely.geometry import shape, mapping
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    warnings.filterwarnings('ignore')

    r = rasterio.open(os.path.join(src, 'dem/dem_downtown_miami_1m_navd88m_utm17n.tif'))
    tf = Transformer.from_crs('EPSG:4326', 'EPSG:26917', always_xy=True).transform
    grades = {}
    for i, feat in enumerate(fc['features']):
        key = feat['properties'].get('UBID') or feat['properties'].get('FOLIO')
        if not key:
            continue
        try:
            gu = shp_transform(tf, shape(feat['geometry']))
            collar = gu.buffer(3.0).difference(gu.buffer(-0.5))
            if collar.is_empty:
                collar = gu.buffer(3.0)
            arr, _ = rmask(r, [mapping(collar)], crop=True, filled=True, nodata=-999999.0)
            v = arr[0]
            v = v[v > -1000]
            if v.size < 4:
                continue
            grades[key] = (float(np.percentile(v, 5)) * M2FT, float(np.median(v)) * M2FT)
        except Exception:
            continue
        if i % 2000 == 0:
            print(f'    sampled {i}', flush=True)
    return grades


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', required=True)
    a = ap.parse_args()

    ded = load_nfip(a.src)
    verify_firm_cutoff(ded)
    SLAB, FREE = build_strata(ded)
    fallback = SLAB[('pre', 'AE')]

    print('\nsampling ground elevation from the 1 m DEM…')
    fc = json.load(open(os.path.join(a.src, 'building_footprints_downtown_miami.geojson')))
    grades = sample_grade(a.src, fc)
    print(f'  grade sampled for {len(grades)} buildings')

    from shapely.geometry import shape
    from shapely.strtree import STRtree
    fz = json.load(open(os.path.join(a.src, 'fema_nfhl_flood_zones_downtown.geojson')))
    polys, props = [], []
    for f in fz['features']:
        g = shape(f['geometry'])
        if g.is_valid and not g.is_empty:
            polys.append(g)
            props.append(f['properties'])
    tree = STRtree(polys)

    out = []
    for feat in fc['features']:
        p = feat['properties']
        key = p.get('UBID') or p.get('FOLIO')
        g = grades.get(key)
        if not g:
            continue
        lag, gmed = g
        c = shape(feat['geometry']).representative_point()
        zone, bfe = '', None
        for idx in tree.query(c):
            if polys[idx].contains(c):
                zp = props[idx]
                zone = (zp.get('FLD_ZONE') or '').strip()
                try:
                    b = float(zp.get('STATIC_BFE'))
                    bfe = b if -100 < b < 100 else None
                except (TypeError, ValueError):
                    bfe = None
                break

        try:
            yb = int(p.get('YEAR_BUILT'))
        except (TypeError, ValueError):
            yb = None
        era = 'post' if (yb and yb >= POST_FIRM_YEAR) else ('pre' if yb else '')
        zc = ('VE' if zone.startswith('V') else 'AH' if zone.startswith('AH')
              else 'AE' if zone.startswith('A') else 'X' if zone[:1] in ('X', 'B', 'C') else '')
        k = (era, zc)

        if k in SLAB:
            slab, n, q1, q3 = SLAB[k]
            prov = 'observed_stratum'
            basis = f'NFIP LFE-LAG, {era}-FIRM zone {zc}, n={n}'
        elif zc == 'X':
            slab, n, q1, q3 = fallback[0], 0, fallback[2], fallback[3]
            prov = 'no_local_observations'
            basis = ('NO NFIP elevation data exists for zone X (certificates not required); '
                     'pre-FIRM AE median borrowed')
        else:
            slab, n, q1, q3 = fallback[0], 0, fallback[2], fallback[3]
            prov = 'assumed_default'
            basis = 'era or zone unknown; pre-FIRM AE median borrowed'

        ffe_grade = round(lag + slab, 2)
        ffe_reg = round(bfe + FREE[k], 2) if (bfe is not None and k in FREE) else None
        if ffe_reg is not None and era == 'post':
            ffe, method = round(max(ffe_grade, ffe_reg), 2), 'max(grade+slab, BFE+freeboard)'
        else:
            ffe, method = ffe_grade, 'grade+slab'

        out.append({
            'FOLIO': p.get('FOLIO'), 'UBID': p.get('UBID'), 'ZIP_CODE': p.get('ZIP_CODE'),
            'YEAR_BUILT': p.get('YEAR_BUILT'), 'era_firm': era, 'FLOORS': p.get('FLOORS'),
            'BLDG_HEIGHT_ft': p.get('BLDG_HEIGHT'), 'ACTUAL_AREA_sqft': p.get('ACTUAL_AREA'),
            'BLDG_TYPE': p.get('BLDG_TYPE'),
            'lag_ft_navd88': round(lag, 2), 'grade_median_ft_navd88': round(gmed, 2),
            'fema_zone': zone, 'static_bfe_ft_navd88': bfe if bfe is not None else '',
            'slab_height_applied_ft': round(slab, 2), 'slab_p25_ft': round(q1, 2),
            'slab_p75_ft': round(q3, 2), 'stratum_n': n,
            'ffe_est_ft_navd88': ffe, 'ffe_lower_ft': round(lag + q1, 2),
            'ffe_upper_ft': round(lag + q3, 2),
            'ffe_method': method, 'ffe_provenance': prov, 'ffe_basis': basis,
        })

    path = os.path.join(a.src, 'building_ffe_estimates.csv')
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    print(f'\nwrote {path}  ({len(out)} buildings)')
    for cls, n in Counter(o['ffe_provenance'] for o in out).most_common():
        print(f'  {cls:24s} {n:6d}  ({100*n/len(out):.1f}%)')
    print('\nAnything tagged no_local_observations MUST render hatched downstream.')


if __name__ == '__main__':
    main()
