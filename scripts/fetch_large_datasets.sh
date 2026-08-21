#!/usr/bin/env bash
# Re-fetch the large binary datasets that are too big to keep in Drive.
# Requires: curl, python3 with rasterio (pip install rasterio --break-system-packages)
set -euo pipefail
mkdir -p dem && cd dem

BASE="https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/FL_MiamiDade_D23/TIFF"
for t in x57y285 x57y286 x58y285 x58y286; do
  echo "Fetching USGS_1M_17_${t}_FL_MiamiDade_D23.tif"
  curl -fL --retry 3 -O "${BASE}/USGS_1M_17_${t}_FL_MiamiDade_D23.tif"
done

python3 - << 'PY'
import rasterio, numpy as np, glob
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from rasterio.transform import from_origin
L,B,R,T = transform_bounds('EPSG:4326','EPSG:26917',-80.215,25.75,-80.17,25.82)
L,B,R,T = np.floor(L),np.floor(B),np.ceil(R),np.ceil(T)
W,H = int(R-L),int(T-B)
out = np.full((H,W),-999999.0,dtype='float32')
for f in sorted(glob.glob('USGS_1M_17_*.tif')):
    with rasterio.open(f) as s:
        b=s.bounds
        il,ib,ir,it = max(L,b.left),max(B,b.bottom),min(R,b.right),min(T,b.top)
        if il>=ir or ib>=it: continue
        a=s.read(1,window=from_bounds(il,ib,ir,it,s.transform))
        out[int(round(T-it)):int(round(T-it))+a.shape[0],
            int(round(il-L)):int(round(il-L))+a.shape[1]]=a
prof=dict(driver='GTiff',height=H,width=W,count=1,dtype='float32',crs='EPSG:26917',
          transform=from_origin(L,T,1.0,1.0),nodata=-999999.0,compress='deflate',
          predictor=3,tiled=True,blockxsize=512,blockysize=512,BIGTIFF='IF_SAFER')
with rasterio.open('dem_downtown_miami_1m_navd88m_utm17n.tif','w',**prof) as d: d.write(out,1)
print('wrote dem_downtown_miami_1m_navd88m_utm17n.tif')
PY
