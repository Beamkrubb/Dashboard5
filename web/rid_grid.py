"""Irrigation-project area per province: rasterise RID virrarea_all polygons on a 0.01° grid and assign each cell to a province."""
import json, sys, numpy as np
from matplotlib.path import Path
rid=json.load(open(sys.argv[1])); geo=json.load(open(sys.argv[2]))
def paths(geom):
    out=[]
    polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        verts=[];codes=[]
        for ring in poly:
            r=np.asarray(ring)[:, :2]; verts.append(r); c=np.full(len(r),Path.LINETO); c[0]=Path.MOVETO; codes.append(c)
        out.append(Path(np.vstack(verts),np.concatenate(codes)))
    return out
step=0.01
lon=np.arange(97.3,105.7,step)+step/2; lat=np.arange(5.6,20.5,step)+step/2
LON,LAT=np.meshgrid(lon,lat); pts=np.column_stack([LON.ravel(),LAT.ravel()])
prov=np.full(len(pts),-1,dtype=int); names=[f['properties']['n'] for f in geo['features']]
for i,f in enumerate(geo['features']):
    for p in paths(f['geometry']):
        b=p.get_extents(); m=(pts[:,0]>=b.x0)&(pts[:,0]<=b.x1)&(pts[:,1]>=b.y0)&(pts[:,1]<=b.y1)&(prov<0)
        idx=np.where(m)[0]
        if len(idx): prov[idx[p.contains_points(pts[idx])]]=i
irr=np.zeros(len(pts),bool); big=np.zeros(len(pts),bool)
for f in rid['features']:
    isbig='ใหญ่' in (f['properties'].get('project_type') or '')
    for p in paths(f['geometry']):
        b=p.get_extents(); m=(pts[:,0]>=b.x0)&(pts[:,0]<=b.x1)&(pts[:,1]>=b.y0)&(pts[:,1]<=b.y1)
        idx=np.where(m)[0]
        if len(idx):
            hit=idx[p.contains_points(pts[idx])]; irr[hit]=True
            if isbig: big[hit]=True
cell_rai=(step*111.32)**2*np.cos(np.radians(pts[:,1]))*625
res={}
for i,n in enumerate(names):
    m=prov==i
    res[n]={"prov_rai":round(float(cell_rai[m].sum())),"irr_rai":round(float(cell_rai[m&irr].sum())),"irr_large_rai":round(float(cell_rai[m&big].sum()))}
json.dump(res,open(sys.argv[3],'w'),ensure_ascii=False,indent=0)
tot=sum(v['irr_rai'] for v in res.values()); print('provinces',len(res),'irrigation-project rai',f'{tot:,}','Thailand rai',f"{sum(v['prov_rai'] for v in res.values()):,}")
