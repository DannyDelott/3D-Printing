"""Build the no-insert assembly from the unchanged, positioned R3.8 components."""
import json, struct
from pathlib import Path
import numpy as np
import shapely

here=Path(__file__).resolve().parents[1]
previous=here.parent/'r3-8'
meta=json.loads((previous/'colors.json').read_text())
raw=(previous/'models/mock-assembly.stl').read_bytes()
facets=[]; groups=[]; cursor=84
for group in meta['groups']:
    size=50*group[0]; end=cursor+size
    if not group[2].startswith('triangle-pocket'):
        facets.append(raw[cursor:end]); groups.append(group)
    cursor=end
assert cursor==len(raw)
count=sum(g[0] for g in groups)
out=raw[:80]+struct.pack('<I',count)+b''.join(facets)
(here/'models/mock-assembly.stl').write_bytes(out)
items={k:v.copy() for k,v in meta['items'].items() if not k.startswith('triangle-pocket')}
for v in items.values():
    if v[2] and v[2].startswith('models/'):v[2]='../r3-8/'+v[2]
assert set(items)=={k for g in groups for k in g[2:4] if k}
(here/'colors.json').write_text(json.dumps(dict(rows=meta['rows'],groups=groups,items=items),indent=2)+'\n')
# In the viewer, X is across the shelf, Z is up and Y is front-to-back.
# Project all triangles along the insertion axis. Distance to their nearest
# projected point limits a circular gauge through the whole assembled bank.
record=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
tri=np.frombuffer(out,dtype=record,offset=84)['vertices'][:,:,[0,2]]
pitch=90.4; rise=pitch*3**.5/2
holes=[]
for x,z in [(0,2*rise/3),(-pitch/2,5*rise/3),(pitch/2,5*rise/3)]:
    center=np.array([x,z])
    nearby=tri[np.all((tri.min(axis=1)<center+18)&(tri.max(axis=1)>center-18),axis=1)]
    radius=shapely.distance(shapely.polygons(nearby),shapely.Point(x,z)).min()
    assert radius>4,('8 mm pencil obstructed',x,z,radius)
    holes.append(dict(center_xz_mm=center.round(2).tolist(),clear_diameter_mm=round(2*radius,2)))
(here/'checks.json').write_text(json.dumps(dict(cubbies=holes,removed_groups=len(meta['groups'])-len(groups)),indent=2)+'\n')
# Front elevation: mark the free gauge circles, not extra printed components.
def xy(x,z):
    return 164+x,220-z
circles=[]
for z,xs in [(0,[-pitch,0,pitch]),(rise,[-pitch/2,pitch/2]),(2*rise,[-pitch,0,pitch])]:
    for x in xs:
        a,b=xy(x,z)
        circles.append(f'<circle cx="{a}" cy="{b}" r="44" fill="#cfb58c"/>')
        circles.append(f'<circle cx="{a}" cy="{b}" r="41.5" fill="#e4ece5"/>')
for h in holes:
    a,b=xy(*h['center_xz_mm'])
    circles.append(f'<circle cx="{a}" cy="{b}" r="{h["clear_diameter_mm"]/2}" fill="none" stroke="#1468a4" stroke-width="1.6" stroke-dasharray="3 2"/>')
(here/'cubbies.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 325 292" role="img" aria-label="Front elevation highlighting three clear pencil passages"><rect width="325" height="292" fill="#fafbf8"/>'+''.join(circles)+'<text x="164" y="285" text-anchor="middle" font-family="system-ui" font-size="12" fill="#245b7b">Dashed circles: Ø16.38 mm clear through the cores</text></svg>')
