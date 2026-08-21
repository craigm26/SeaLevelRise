#!/usr/bin/env python3
"""
Build the browser payloads in viz/ from the source geospatial data.

Reads the large source files (DEM GeoTIFF, parcel/footprint/drainage GeoJSON) that live in
the Drive folder rather than in git, and writes the compact quantised payloads the 3D
visualiser loads.

    pip install rasterio shapely pyproj pillow numpy --break-system-packages
    python3 scripts/build_viz_payloads.py --src /path/to/miami_flood_data --out viz/

Everything is projected into a local metric frame: EPSG:26917 (UTM 17N) minus the origin
578681, 2848232. Coordinates are rounded to whole metres, elevations to 0.1 ft. That
quantisation is what keeps the payloads at ~2.3 MB instead of ~60 MB.

Units: the DEM is metres NAVD88; every elevation written out is FEET NAVD88.
"""
import argparse, json, os, sys

M2FT = 3.28084
OX, OY = 578681.0, 2848232.0          # UTM 17N origin of the study area
SPAN_X, SPAN_Y = 4561, 7781           # metres
GRID_W, GRID_H = 280, 478             # terrain grid (~16 m posts)


def q(v, d=1):
    return int(round(v * d))


def build_terrain(src, out):
    import numpy as np, rasterio
    from rasterio.enums import Resampling
    from PIL import Image

    r = rasterio.open(os.path.join(src, 'dem/dem_downtown_miami_1m_navd88m_utm17n.tif'))
    b = r.bounds
    a = r.read(1, out_shape=(GRID_H, GRID_W), resampling=Resampling.average).astype('float64')
    mask = a < -1000
    valid = a[~mask]
    # clip the tails: rooftop returns at the top, the dredged channel at the bottom
    lo, hi = np.percentile(valid, 0.2), np.percentile(valid, 99.8)
    a = np.clip(a, lo, hi)
    a[mask] = lo
    zmin, zmax = float(a.min()), float(a.max())

    # 16-bit height packed into two 8-bit channels, because canvas gives us 8-bit RGBA
    qv = np.round((a - zmin) / (zmax - zmin) * 65535).astype('uint32')
    rgb = np.zeros((GRID_H, GRID_W, 3), dtype='uint8')
    rgb[:, :, 0] = (qv >> 8) & 0xFF
    rgb[:, :, 1] = qv & 0xFF
    Image.fromarray(rgb, 'RGB').save(os.path.join(out, 'terrain.png'))

    json.dump({
        'gw': GRID_W, 'gh': GRID_H,
        'encoding': 'R=high byte, G=low byte; q=(R*256+G)/65535; elev_ft=zmin+q*(zmax-zmin)',
        'width_m': float(b.right - b.left), 'height_m': float(b.top - b.bottom),
        'zmin_ft': zmin * M2FT, 'zmax_ft': zmax * M2FT,
        'origin_utm17n': [b.left, b.bottom], 'crs': 'EPSG:26917',
    }, open(os.path.join(out, 'terrain.json'), 'w'), indent=1)
    print(f'terrain  {GRID_W}x{GRID_H}  {zmin*M2FT:.1f}..{zmax*M2FT:.1f} ft NAVD88')


def build_vectors(src, out):
    from pyproj import Transformer
    tf = Transformer.from_crs('EPSG:4326', 'EPSG:26917', always_xy=True)

    def P(lon, lat):
        x, y = tf.transform(lon, lat)
        return x - OX, y - OY

    # ---- pipes ----
    L = json.load(open(os.path.join(src, 'storm_drains_stormwater_lines.geojson')))
    pipes = []
    for f in L['features']:
        g, p = f['geometry'], f['properties']
        parts = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        try:
            dia = float(str(p.get('DIAMETER')).strip())
        except (TypeError, ValueError):
            dia = None
        for cs in parts:
            if len(cs) < 2:
                continue
            pts = [P(c[0], c[1]) for c in cs]
            keep = [pts[0]] + pts[1:-1:3] + [pts[-1]]     # decimate interior vertices
            flat = [c for xy in keep for c in (q(xy[0]), q(xy[1]))]
            pipes.append({'c': flat, 'd': dia,
                          't': 1 if (p.get('TYPE') or '').strip() == 'PIPE' else 0})
    json.dump({'origin': [OX, OY], 'pipes': pipes},
              open(os.path.join(out, 'pipes.json'), 'w'), separators=(',', ':'))
    print(f'pipes    {len(pipes)}')

    # ---- structures ----
    S = json.load(open(os.path.join(src, 'storm_drains_stormwater_points.geojson')))
    TYPES = {'CATCH BASIN': 0, 'MANHOLE': 1, 'DRAINAGE WELL': 2, 'HYDRAULIC STRUCTURE': 3}
    sts = []
    for f in S['features']:
        c = f['geometry']['coordinates']
        x, y = P(c[0], c[1])
        sts.append([q(x), q(y), TYPES.get((f['properties'].get('TYPE') or '').strip(), 4)])
    json.dump({'t': ['catch basin', 'manhole', 'drainage well', 'hydraulic structure', 'other'],
               's': sts}, open(os.path.join(out, 'structures.json'), 'w'), separators=(',', ':'))
    print(f'struct   {len(sts)}')

    # ---- surveyed rims: the only real vertical control in the drainage layer ----
    C = json.load(open(os.path.join(src, 'storm_structure_elevations_city_of_miami.geojson')))
    rims = []
    for f in C['features']:
        c, p = f['geometry']['coordinates'], f['properties']

        def num(k):
            try:
                v = float(p.get(k))
                return v if -30 < v < 50 else None      # reject sentinels (one reads 1075 ft)
            except (TypeError, ValueError):
                return None

        rim, bot, inv = num('RIMELEV'), num('BOTTOMELEV'), num('INVERT')
        if rim is None and bot is None and inv is None:
            continue
        x, y = P(c[0], c[1])
        base = bot if bot is not None else (inv if inv is not None else rim)
        rims.append([q(x), q(y),
                     q(rim, 10) if rim is not None else -9999,
                     q(base, 10) if base is not None else -9999,
                     1 if (p.get('RIM_VERTDATUM') or '').upper().startswith('NAVD') else 0])
    json.dump({'r': rims}, open(os.path.join(out, 'rims.json'), 'w'), separators=(',', ':'))
    print(f'rims     {len(rims)}')

    # ---- Class V injection wells: how downtown actually drains ----
    W = json.load(open(os.path.join(src, 'outfalls_fdep_uic_drainage_wells.geojson')))
    wells = []
    for f in W['features']:
        c, p = f['geometry']['coordinates'], f['properties']
        x, y = P(c[0], c[1])
        if not (0 <= x <= SPAN_X and 0 <= y <= SPAN_Y):
            continue
        try:
            d = float(p.get('well_depth_ft_bls'))
        except (TypeError, ValueError):
            d = None
        wells.append([q(x), q(y), int(d) if d and 0 < d < 600 else 120])
    json.dump({'w': wells}, open(os.path.join(out, 'wells.json'), 'w'), separators=(',', ':'))
    print(f'wells    {len(wells)}')


def build_buildings(src, out):
    import csv
    from shapely.geometry import shape
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    tf = Transformer.from_crs('EPSG:4326', 'EPSG:26917', always_xy=True).transform

    PROV = {'observed_stratum': 0, 'no_local_observations': 1, 'assumed_default': 2}
    ZONE = {'X': 0, 'AE': 1, 'AH': 2, 'VE': 3}

    ffe = {}
    for r in csv.DictReader(open(os.path.join(src, 'building_ffe_estimates.csv'))):
        k = r['UBID'] or r['FOLIO']
        if k:
            ffe[k] = r

    fc = json.load(open(os.path.join(src, 'building_footprints_downtown_miami.geojson')))
    out_b, skipped = [], 0
    for f in fc['features']:
        p = f['properties']
        r = ffe.get(p.get('UBID') or p.get('FOLIO'))
        if not r:
            skipped += 1
            continue
        try:
            g = shp_transform(tf, shape(f['geometry']))
            if g.geom_type == 'MultiPolygon':
                g = max(g.geoms, key=lambda a: a.area)
            g = g.simplify(1.5, preserve_topology=True)
            ring = list(g.exterior.coords)[:-1]
            if len(ring) < 3:
                skipped += 1
                continue
            if len(ring) > 14:                              # cap vertices for payload size
                step = len(ring) / 14.0
                ring = [ring[int(i * step)] for i in range(14)]
            flat = [c for xy in ring for c in (int(round(xy[0] - OX)), int(round(xy[1] - OY)))]
        except Exception:
            skipped += 1
            continue

        try:
            h = float(p.get('BLDG_HEIGHT'))
        except (TypeError, ValueError):
            h = None
        if not h or h <= 2 or h > 900:                      # BLDG_HEIGHT null on 5.2%
            try:
                h = max(float(p.get('FLOORS')), 1) * 11.0
            except (TypeError, ValueError):
                h = 11.0
        try:
            yb = int(p.get('YEAR_BUILT'))
        except (TypeError, ValueError):
            yb = 0

        out_b.append({
            'p': flat, 'h': int(round(h)),
            'g': int(round(float(r['lag_ft_navd88']) * 10)),
            'f': int(round(float(r['ffe_est_ft_navd88']) * 10)),
            'v': PROV.get(r['ffe_provenance'], 2),
            'z': ZONE.get(r['fema_zone'], 0),
            'e': 1 if r['era_firm'] == 'post' else 0,
            'y': yb,
        })
    json.dump({'origin': [OX, OY], 'b': out_b,
               'prov': ['observed', 'no local observations', 'assumed'],
               'zone': ['X', 'AE', 'AH', 'VE']},
              open(os.path.join(out, 'buildings.json'), 'w'), separators=(',', ':'))
    print(f'bldgs    {len(out_b)} (skipped {skipped})')


def build_zones_and_gw(src, out):
    import csv, numpy as np
    from shapely.geometry import shape
    from shapely.ops import transform as shp_transform
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:4326', 'EPSG:26917', always_xy=True)
    tf = tr.transform

    fz = json.load(open(os.path.join(src, 'fema_nfhl_flood_zones_downtown.geojson')))
    Z = []
    for f in fz['features']:
        g = shp_transform(tf, shape(f['geometry'])).simplify(6, preserve_topology=True)
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        zn = (f['properties'].get('FLD_ZONE') or '').strip()
        try:
            bfe = float(f['properties'].get('STATIC_BFE'))
            bfe = round(bfe, 2) if -100 < bfe < 100 else None
        except (TypeError, ValueError):
            bfe = None
        for pl in polys:
            if pl.area < 400:
                continue
            ring = [[int(round(x - OX)), int(round(y - OY))] for x, y in pl.exterior.coords]
            if len(ring) < 4:
                continue
            Z.append({'r': [c for xy in ring for c in xy], 'z': zn, 'b': bfe})
    json.dump({'z': Z}, open(os.path.join(out, 'zones.json'), 'w'), separators=(',', ':'))
    print(f'zones    {len(Z)}')

    sites = {r['site_no']: r for r in
             csv.DictReader(open(os.path.join(src, 'groundwater_wells_miami_dade.csv')))}
    levels = {}
    for r in csv.DictReader(open(os.path.join(src, 'groundwater_levels_downtown.csv'))):
        if 'NAVD' not in (r.get('datum') or '').upper():
            continue                                        # NGVD29 = NAVD88 + 1.56 ft here
        try:
            levels.setdefault(r['site_no'], []).append(float(r['water_level_value']))
        except (TypeError, ValueError):
            pass
    gw = []
    for s, vals in levels.items():
        si = sites.get(s)
        if not si:
            continue
        try:
            x, y = tr.transform(float(si['lon']), float(si['lat']))
        except (TypeError, ValueError):
            continue
        a = np.array(vals)
        gw.append({'id': si.get('station_name', '').strip(),
                   'x': round(x - OX, 1), 'y': round(y - OY, 1), 'n': len(vals),
                   'med': round(float(np.median(a)), 2),
                   'p05': round(float(np.percentile(a, 5)), 2),
                   'p95': round(float(np.percentile(a, 95)), 2),
                   'inside': si.get('inside_AOI') == 'Y',
                   'dist_km': float(si.get('distance_from_AOI_center_km', 0))})
    gw.sort(key=lambda g: g['dist_km'])
    json.dump({'wells': gw, 'summary': {
        'dry_median': 0.38, 'wet_median': 0.84, 'p95': 1.86,
        'note': 'ft NAVD88; only one USGS well sits inside the AOI, so the downtown surface '
                'is interpolated and should render hatched'}},
        open(os.path.join(out, 'groundwater.json'), 'w'), separators=(',', ':'))
    print(f'gw sites {len(gw)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', required=True, help='directory holding the source geospatial files')
    ap.add_argument('--out', default='viz', help='output directory (default: viz)')
    a = ap.parse_args()
    if not os.path.isdir(a.src):
        sys.exit(f'source directory not found: {a.src}')
    os.makedirs(a.out, exist_ok=True)
    build_terrain(a.src, a.out)
    build_vectors(a.src, a.out)
    build_buildings(a.src, a.out)
    build_zones_and_gw(a.src, a.out)
    total = sum(os.path.getsize(os.path.join(a.out, f)) for f in os.listdir(a.out))
    print(f'\n{a.out}/ total {total/1e6:.1f} MB')


if __name__ == '__main__':
    main()
