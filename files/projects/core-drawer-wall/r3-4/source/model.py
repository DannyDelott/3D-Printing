"""R3.4 monolithic drawers. x = lateral, y = up, w = depth; dimensions in mm."""
from pathlib import Path
import importlib.util,json,math,numpy as np
P=Path(__file__).resolve().parents[1];out=P/'models'
spec=importlib.util.spec_from_file_location('mount',P.parent/'r3-2/source/model.py')
mount=importlib.util.module_from_spec(spec);spec.loader.exec_module(mount)
s=mount.s;r=s.r;extr=r.extr;f=s.f;rad=43.4;k=2**-.5
# The plain face and its lowerbevel form a single bent skin, clipped to the
# complete disk silhouette. Unlike the earlier ledge, nothing projects from the
# front plane. Extending the tub up to this face makes the new depth usable.
bevel=14.0
angle=math.radians(38);sn,cs=math.sin(angle),math.cos(angle)
bevel_rise=bevel*math.tan(angle)
ff=f-bevel; nose=s.front-bevel
profile=r.poly([(-rad,f),(-rad,s.front),(-rad+bevel_rise,nose),(rad,nose),(rad,ff),(-rad+bevel_rise,ff)])
disk=extr(profile,-rad-1,rad+1).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]]) ^ extr(r.circle(rad),ff-.1,s.front+.1)
# Trim the lower forward corner at the same bevel; rim at the core stays unchanged.
limit=r.poly([(-rad,f),(-rad,65),(50,65),(50,ff),(-rad+bevel_rise,ff)])
limit=extr(limit,-50,50).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
outer=extr(r.section,ff+.2,r.L-1)^limit
cut=s.cut.transform([[1,0,0,0],[0,1,0,0],[0,0,(s.back-nose)/(s.back-s.front),-bevel*s.back/(s.back-s.front)]])
# Retain the thickness of the bevel even where the longer cavity meets it.
void=outer^cut.translate((0,0,.04))^limit.translate((0,0,2.4))
def cup_loft(extra,back_extra):
 rings=[]
 for w,dy in [(ff-.06,0.),(ff+6.,3.2),(ff+9.+back_extra,3.2)]:
  cs=r.rnd(-17-extra,9+dy-extra,17+extra,23+dy+extra,5+extra)
  xy=np.asarray(cs.to_polygons()[0]);rings.append(np.column_stack([xy,np.full(len(xy),w)]))
 return mount.M.hull_points(np.concatenate(rings))
pocket=cup_loft(0.,0.);cupwall=cup_loft(1.7,1.7)^extr(r.circle(rad),ff,s.front+6)
blank=outer+disk
bin=((blank-void)+cupwall)-pocket
# The blind cup is accessible from the outside but never opens into storage.
storage=void-cupwall
assert (storage^pocket).volume()<1e-6
def drawer(n):
 if n=='open':return bin
 h=r.top;a=.8; sec=r.box(-a,-45,a,h-a)+r.circle(a,0,h-a)
 fence=extr(sec,nose+.1,r.L-1-.25) if n=='left-right' else extr(sec,-44,44).transform([[0,0,1,0],[0,1,0,0],[1,0,0,(nose+s.back)/2]])
 return bin+(fence^storage)
def print_pose(m):return m.transform([[1,0,0,0],[0,-sn,cs,0],[0,cs,sn,0]])
from spacers import build
triangle,edge,spacer_tie=build(r)
def main():
 out.mkdir(exist_ok=True);data={};colors=[];parts=[];installed=[]
 def add(m,x,y,w,group,key,kit=None):
  placed=m.translate((x,y,w));installed.append((placed,key));mesh=r.mesh(r.world(placed));parts.append(mesh);colors.append([len(mesh.faces),group,key,kit])
 loc=[(-r.pitch,0,'open',0),(0,0,'front-back',-27),(r.pitch,0,None,0),(-r.half,r.rise,'open',0),(r.half,r.rise,'left-right',-41),(-r.pitch,2*r.rise,'open',-12),(0,2*r.rise,'front-back',0),(r.pitch,2*r.rise,'open',0)]
 for n in ['open','left-right','front-back']:
  d=drawer(n);shape=print_pose(d)
  plate=r.plate([(n+' finger-cup drawer',shape)]);m=plate[0][1]
  assert m.is_volume and m.is_watertight and len(m.split())==1
  footprint=shape.slice(shape.bounding_box()[2]+.01).area()
  assert footprint>380
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
  margins=[]
  for z in np.arange(lo+2,hi,3):
   partial=shape.trim_by_plane((0,0,-1),-z)
   projected=Point(r.mesh(partial).center_mass[:2]);assert bed.contains(projected),(n,z)
   margins.append(bed.boundary.distance(projected))


  # Check lower face coverage and full extraction relative to rear/front jaw and cores.
  assert (r.circle(r.ID/2)-disk.project()).area()<1e-6
  for deg in range(0,360,60):
   a=math.radians(deg);assert (d^d.translate((r.pitch*math.cos(a),r.pitch*math.sin(a),0))).volume()<1e-6
  for flag in (True,False):
   for role in ('front','rear'):
    part=r.junction(flag,role)
    for x,y in (r.centers[:2] if flag else r.centers):
     for fixed in [part,r.rear(part)]:
      assert (d.translate((x,y,0))^fixed).volume()<1e-5
  assert (d^r.core).volume()<1e-5
  r.OUT=out;r.write3(n,plate);(out/(n+'-r3.3mf')).rename(out/(n+'-r3-4.3mf'))
  m.export(out/(n+'-r3-4.stl'));r.mesh(r.world(d)).export(out/(n+'-in-use.stl'))
  cavity=storage-d
  data[n]=dict(ml=round(cavity.volume()/1000,1),bounds=m.extents.round(2).tolist(),bed_mm2=round(footprint),balance_margin_mm=round(bed.boundary.distance(cog),1),min_sampled_balance_margin_mm=round(min(margins),1))
 starter=r.plate([('Open one-piece drawer',print_pose(drawer('open')))]+[(('Rear' if b else 'Front')+' outside foot',mount.tied_end(sign,b)) for sign in (-1,1) for b in (False,True)])
 r.OUT=out;r.write3('starter',starter);(out/'starter-r3.3mf').rename(out/'starter-r3-4.3mf')
 combined=r.trimesh.util.concatenate([m for _,m in starter]);combined.export(out/'starter-r3-4.stl')
 data['starter']=dict(bounds=combined.extents.round(2).tolist(),bodies=5)
 # Pair designed for the inverted triangular gap; edge profiles mirror left/right.
 def spacer_plate(key,objects):
  plate=r.plate(objects);mm=r.trimesh.util.concatenate([m for _,m in plate])
  r.OUT=out;r.write3(key,plate);(out/(key+'-r3.3mf')).rename(out/(key+'-r3-4.3mf'));mm.export(out/(key+'-r3-4.stl'))
  data[key]=dict(bounds=mm.extents.round(2).tolist(),bodies=len(plate))
 spacer_plate('triangle-spacer',[('Triangle front',triangle(False)),('Triangle rear',triangle(True))])
 for side,sign in [('left',1),('right',-1)]:
  spacer_plate('edge-'+side,[(side+' '+role,edge(b) if sign==1 else edge(b).mirror((1,0,0))) for b,role in [(False,'front'),(True,'rear')]])
 # Model identification uses each named solid's triangle range, not screen hotspots.
 for x,y,n,w in loc:
  add(r.core,x,y,0,0,'core')
  if n:add(drawer(n),x,y,w,1,'one-piece-'+n)
 def anchor_fasteners(x,y,bolt_y,wood_y):
  add(mount.shaft(0,bolt_y),x,y,0,4,'bolt')
  washer=extr(r.circle(3.45,0,bolt_y)-r.circle(1.6,0,bolt_y),-r.lip-.55,-r.lip)
  nut=extr(r.CS.circle(3.18,6).translate((0,bolt_y))-r.circle(1.6,0,bolt_y),-r.lip-4.55,-r.lip-.55)
  add(washer+nut,x,y,0,4,'bolt')
  wood=extr(r.circle(2.1,0,wood_y),-14.85,4.2)+extr(r.circle(4.55,0,wood_y),2.8,5.1)
  add(r.rear(wood),x,y,0,4,'wood-screw')
 for x,sign in [(-1.5*r.pitch,1),(1.5*r.pitch,-1)]:
  for b in (False,True):
   foot=mount.tied_end(sign,b);add(r.rear(foot) if b else foot,x,0,0,2,'dry-ends')
  a,b=sorted([sign*2.7,sign*9.6]);loop=r.rnd(-r.lip-1.1,a-.45,r.L+r.lip-.07,b+.45,.44)
  wire=extr(loop-loop.offset(-.9),-32.25,-29.75).transform([[0,1,0,0],[0,0,1,0],[1,0,0,0]])
  add(wire,x,0,0,4,'tie')
 for x,y,ground,middle,kit in [(-r.half,0,True,False,None),(r.half,0,True,False,None),(-r.half,0,False,True,None),(r.half,0,False,False,None),(0,r.rise,False,False,'top-tier')]:
  key='middle-mount' if middle else ('base-mount' if ground else 'upper-mount')
  for b in (False,True):
   j=mount.mid(b) if middle else r.junction(ground,'rear' if b else 'front')
   add(r.rear(j) if b else j,x,y,0,3 if middle else 2,key,kit)
  if middle:anchor_fasteners(x,y,r.rise/3-3.7,r.rise/3+2.9)
  else:add(r.cable(ground),x,y,0,4,'tie')
 x=0;y=2*r.rise
 for b in (False,True):add(r.rear(mount.top_clip(True)) if b else mount.top_clip(False),x,y,0,3,'top-clips','top-tier')
 anchor_fasteners(x,y,48.5,56.5)
 # Inverted empty triangles: one above the center bottom core and two above the middle row.
 for x,y in [(0,0),(-r.half,r.rise),(r.half,r.rise)]:
  for b in (False,True):add(r.rear(triangle(b)) if b else triangle(b),x,y,0,2,'triangle-spacer')
  add(spacer_tie(0,2*r.rise/3),x,y,0,4,'tie')
 for sign,side in [(1,'left'),(-1,'right')]:
  x=-sign*r.pitch
  for b in (False,True):
   m=edge(b);m=m if sign==1 else m.mirror((1,0,0))
   add(r.rear(m) if b else m,x,0,0,2,'edge-'+side)
  add(spacer_tie(-14*sign,r.rise),x,0,0,4,'tie')
 # Check new components in the complete 3–2–3 assembly, including both rim
 # faces, seats, ties, neighbors and the straight drawer body's swept envelope.
 fillers=['triangle-spacer','edge-left','edge-right']
 sweep=extr(r.section,-80,r.L-1)
 for i,(m,key) in enumerate(installed):
  if key not in fillers:continue
  for j,(other,name) in enumerate(installed):
   if j!=i:assert abs((m^other).volume())<.001,(key,name,round((m^other).volume(),3))
  for x,y,n,w in loc:
   assert abs((m^sweep.translate((x,y,0))).volume())<.001,(key,x,y,'body sweep')
   assert abs((m^drawer('open').translate((x,y,0))).volume())<.001,(key,x,y,'closed')
 r.trimesh.util.concatenate(parts).export(out/'mock-assembly.stl')
 items=json.loads((P/'parts.json').read_text())
 assert {key for _,_,primary,kit in colors for key in (primary,kit) if key}==set(items)
 (P/'colors.json').write_text(json.dumps(dict(rows=[3,2,3],groups=colors,items=items),indent=2)+'\n')
 (P/'checks.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
