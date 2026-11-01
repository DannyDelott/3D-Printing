"""R3.3 monolithic drawers. x = lateral, y = up, w = depth; dimensions in mm."""
from pathlib import Path
import importlib.util,json,math,numpy as np
P=Path(__file__).resolve().parents[1];out=P/'models'
spec=importlib.util.spec_from_file_location('mount',P.parent/'r3-2/source/model.py')
mount=importlib.util.module_from_spec(spec);spec.loader.exec_module(mount)
s=mount.s;r=s.r;extr=r.extr;f=s.f;rad=43.4;k=2**-.5
# Sloped lower pull is the bed contact. Clip its width to the face outline, so
# extending a drawer cannot catch its neighbors or expose the lower bore.
prof=r.poly([(-rad,f+.02),(-rad,f),(-30,f-13.4),(-28,f-13.4),(-20,f+.02)])
lower=extr(prof,-21,21).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]]) ^ extr(r.circle(rad),f-14,f+.03)
face=extr(r.circle(rad),f,s.front)+lower
outer=extr(r.section,s.front,r.L-1)
void=outer ^ s.cut
bin=outer-s.cut
def drawer(n):
 d=bin+face
 if n!='open':d+=mount.fence(n=='left-right') ^ outer
 return d
def print_pose(m):return m.transform([[1,0,0,0],[0,-k,k,0],[0,k,k,0]])
def main():
 out.mkdir(exist_ok=True);data={};colors=[];parts=[]
 def add(m,x,y,w,group):
  mesh=r.mesh(r.world(m.translate((x,y,w))));parts.append(mesh);colors.append([len(mesh.faces),group])
 loc=[(-r.pitch,0,'open',0),(0,0,'front-back',-27),(r.pitch,0,None,0),(-r.half,r.rise,'open',0),(r.half,r.rise,'left-right',-41)]
 for n in ['open','left-right','front-back']:
  d=drawer(n);shape=print_pose(d)
  plate=r.plate([(n+' one-piece drawer',shape)]);m=plate[0][1]
  assert m.is_volume and m.is_watertight and len(m.split())==1
  footprint=shape.slice(shape.bounding_box()[2]+.01).area()
  assert footprint>450
  # One connected path grows off the pull throughout the print.
  lo,hi=shape.bounding_box()[2],shape.bounding_box()[5]
  previous=None
  for z in np.arange(lo+.10,hi,.20):
   layer=shape.slice(z)
   if previous is not None:
    for region in layer.decompose():
     assert (region^previous).area()>1e-8,('Floating island',n,z)
   previous=layer
  # Project the center of mass onto the first-layer footprint.
  raw=r.mesh(shape);from shapely.geometry import Polygon,Point
  bed=Polygon(shape.slice(lo+.01).to_polygons()[0]);cog=Point(raw.center_mass[:2])
  assert bed.contains(cog),(n,'off-balance',bed.distance(cog))

  # Check lower face coverage and full extraction relative to rear/front jaw and cores.
  assert (r.circle(r.ID/2)-face.slice((f+s.front)/2)).area()<1e-6
  for deg in range(0,360,60):
   a=math.radians(deg);assert (d^d.translate((r.pitch*math.cos(a),r.pitch*math.sin(a),0))).volume()<1e-6
  for flag in (True,False):
   for role in ('front','rear'):
    part=r.junction(flag,role)
    for x,y in (r.centers[:2] if flag else r.centers):
     for fixed in [part,r.rear(part)]:
      assert (d.translate((x,y,0))^fixed).volume()<1e-5
  assert (d^r.core).volume()<1e-5
  r.OUT=out;r.write3(n,plate);(out/(n+'-r3.3mf')).rename(out/(n+'-r3-3.3mf'))
  m.export(out/(n+'-r3-3.stl'));r.mesh(r.world(d)).export(out/(n+'-in-use.stl'))
  cavity=void-d
  data[n]=dict(ml=round(cavity.volume()/1000,1),bounds=m.extents.round(2).tolist(),bed_mm2=round(footprint),balance_margin_mm=round(bed.boundary.distance(cog),1))
 starter=r.plate([('Open one-piece drawer',print_pose(drawer('open')))]+[(('Rear' if b else 'Front')+' outside foot',mount.tied_end(sign,b)) for sign in (-1,1) for b in (False,True)])
 r.OUT=out;r.write3('starter',starter);(out/'starter-r3.3mf').rename(out/'starter-r3-3.3mf')
 combined=r.trimesh.util.concatenate([m for _,m in starter]);combined.export(out/'starter-r3-3.stl')
 data['starter']=dict(bounds=combined.extents.round(2).tolist(),bodies=5)
 for x,y,n,w in loc:
  add(r.core,x,y,0,0)
  if n:add(drawer(n),x,y,w,1)
 for x,sign in [(-1.5*r.pitch,1),(1.5*r.pitch,-1)]:
  for b in (False,True):
   foot=mount.tied_end(sign,b);add(r.rear(foot) if b else foot,x,0,0,2)
 for x in [-r.half,r.half]:
  for ground in [True,False]:
   for b in (False,True):
    j=mount.mid(b) if (not ground and x<0) else r.junction(ground,'rear' if b else 'front')
    add(r.rear(j) if b else j,x,0,0,3 if not ground and x<0 else 2)
 x=r.half;y=r.rise
 for b in (False,True):add(r.rear(mount.top_clip(True)) if b else mount.top_clip(False),x,y,0,3)
 add(mount.shaft(0,48.5),x,y,0,4);add(mount.shaft(0,r.rise/3-3.7),-r.half,0,0,4)
 r.trimesh.util.concatenate(parts).export(out/'mock-assembly.stl')
 (P/'colors.json').write_text(json.dumps(colors))
 (P/'checks.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
