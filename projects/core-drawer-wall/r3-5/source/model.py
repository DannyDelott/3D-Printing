"""R3.5 monolithic drawers. x = lateral, y = up, w = depth; dimensions in mm."""
from pathlib import Path
import importlib.util,json,math,numpy as np
P=Path(__file__).resolve().parents[1];out=P/'models'
spec=importlib.util.spec_from_file_location('mount',P.parent/'r3-2/source/model.py')
mount=importlib.util.module_from_spec(spec);spec.loader.exec_module(mount)
s=mount.s;r=s.r;extr=r.extr;f=s.f;rad=43.4;k=2**-.5
# All visible faces are planar. The disk is the first layer, and lies at the
# core rim when installed. A smooth pitched back closes from both sides as
# each layer rises, meeting over a short bridge hidden inside the core.
ff=s.f-14;nose=ff+2.4;rc=r.L-1
def cap(region):return extr(region,-60,60).transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
def rear_limit(w,bridge=6.):
 return cap(r.poly([(-48,-45),(48,-45),(48,w-48+bridge),(bridge,w),(-bridge,w),(-48,w-48+bridge)]))
disk=extr(r.circle(rad),ff,nose)
outer=extr(r.section,ff+.1,rc)^rear_limit(rc)
long_cut=s.cut.transform([[1,0,0,0],[0,1,0,0],[0,0,(s.back-nose-.04)/(s.back-s.front),(nose+.04-s.front)*s.back/(s.back-s.front)]])
hood=extr(r.section^r.box(-50,r.top-1.35,50,r.top+.1),ff,-r.lip)
void=(outer^long_cut^rear_limit(rc-1.8))-hood
def cup_loft(extra,back_extra):
 rings=[]
 for depth,low,high,width in [(-.05,8,23,17),(4.,9,26,17),(6.,10,26,16.5),(13.5+back_extra,17.25,18.75,11)]:
  cs=r.rnd(-width-extra,low-extra,width+extra,high+extra,min(4.8+extra,(high-low)/2+extra-.06))
  xy=np.asarray(cs.to_polygons()[0]);rings.append(np.column_stack([xy,np.full(len(xy),ff+depth)]))
 return mount.M.hull_points(np.concatenate(rings))
pocket=cup_loft(0,0);cupwall=cup_loft(1.7,1.7)^extr(r.circle(rad),ff,rc)
bin=((outer+disk-void)+cupwall)-pocket
storage=void-cupwall
assert (storage^pocket).volume()<1e-5
def drawer(n):
 if n=='open':return bin
 if n=='left-right':
  sec=r.box(-.8,-45,.8,r.top-.8)+r.circle(.8,0,r.top-.8);fence=extr(sec,nose,rc)
 else:
  # Chevron follows the same self-supporting print path as the rear wall.
  fence=rear_limit(34)-rear_limit(32.4)
 return bin+(((fence^outer)-pocket) if n=='left-right' else fence^storage)
def print_pose(m):return m
from spacers import build
triangle,edge,spacer_tie=build(r)
from pockets import make
pk=make(r,mount.M,edge,ff)
from top import build as top_parts
top_clip,top_tie=top_parts(r)
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
  bed=Polygon(max(shape.slice(lo+.01).to_polygons(),key=lambda p:abs(Polygon(p).area)));cog=Point(raw.center_mass[:2])
  assert bed.contains(cog),(n,'off-balance',bed.distance(cog))
  margins=[]
  for z in np.arange(lo+2,hi,3):
   partial=shape.trim_by_plane((0,0,-1),-z)
   projected=Point(r.mesh(partial).center_mass[:2]);assert bed.contains(projected),(n,z)
   margins.append(bed.boundary.distance(projected))


  # Check lower face coverage and full extraction relative to rear/front jaw and cores.
  assert (r.circle(r.ID/2)-disk.slice(ff+.15)).area()<1e-6
  for deg in range(0,360,60):
   a=math.radians(deg);assert (d^d.translate((r.pitch*math.cos(a),r.pitch*math.sin(a),0))).volume()<1e-6
  for flag in (True,False):
   for role in ('front','rear'):
    part=r.junction(flag,role)
    for x,y in (r.centers[:2] if flag else r.centers):
     for fixed in [part,r.rear(part)]:
      assert (d.translate((x,y,0))^fixed).volume()<1e-5
  assert (d^r.core).volume()<1e-5
  r.OUT=out;r.write3(n,plate);(out/(n+'-r3.3mf')).rename(out/(n+'-r3-5.3mf'))
  m.export(out/(n+'-r3-5.stl'));r.mesh(r.world(d)).export(out/(n+'-in-use.stl'))
  cavity=storage-d
  data[n]=dict(ml=round(cavity.volume()/1000,1),bounds=m.extents.round(2).tolist(),bed_mm2=round(footprint),balance_margin_mm=round(bed.boundary.distance(cog),1),min_sampled_balance_margin_mm=round(min(margins),1))
 starter=r.plate([('Open one-piece drawer',print_pose(drawer('open')))]+[(('Rear' if b else 'Front')+' outside foot',mount.tied_end(sign,b)) for sign in (-1,1) for b in (False,True)])
 r.OUT=out;r.write3('starter',starter);(out/'starter-r3.3mf').rename(out/'starter-r3-5.3mf')
 combined=r.trimesh.util.concatenate([m for _,m in starter]);combined.export(out/'starter-r3-5.stl')
 data['starter']=dict(bounds=combined.extents.round(2).tolist(),bodies=5)
 # Pair designed for the inverted triangular gap; edge profiles mirror left/right.
 def spacer_plate(key,objects):
  plate=r.plate(objects);mm=r.trimesh.util.concatenate([m for _,m in plate])
  r.OUT=out;r.write3(key,plate);(out/(key+'-r3.3mf')).rename(out/(key+'-r3-5.3mf'));mm.export(out/(key+'-r3-5.stl'))
  data[key]=dict(bounds=mm.extents.round(2).tolist(),bodies=len(plate))
 # Storage replaces the solid panels. Each kit prints a front frame, rear
 # frame and removable drawer. All drawers print directly on their flat faces.
 for ident,side in [('triangle-pocket',0),('left-pocket',1),('right-pocket',-1)]:
  tr=side==0;frame=pk['tri_frame' if tr else 'side_frame'];d=pk['tri_bin' if tr else 'side_bin'];space=pk['tri_space' if tr else 'side_space']
  def handed(m):return m.mirror((1,0,0)) if side==-1 else m
  parts3=[('Fixed front',handed(frame(False))),('Fixed rear',handed(frame(True))),('Removable pocket',handed(d))]
  spacer_plate(ident,parts3)
  data[ident]['ml']=round(space.volume()/1000,1)
  for suffix,arr in [('frame',parts3[:2]),('bin',parts3[2:])]:spacer_plate(ident+'-'+suffix,arr)
  # Every layer of the pocket grows from the preceding one. The front and
  # rear guides clear its path for full withdrawal, including at the stop.
  low,high=d.bounding_box()[2],d.bounding_box()[5];prev=None
  for z in np.arange(low+.1,high,.2):
   layer=d.slice(z)
   if prev is not None:assert all((piece^prev).area()>1e-7 for piece in layer.decompose()),(ident,z)
   prev=layer
  travel=extr(pk['tri_sweep' if tr else 'side_sweep'],-90,56)
  for fixed in [frame(False),r.rear(frame(True))]:
   assert (fixed^travel).volume()<.001 and (fixed^d).volume()<.001,(ident,'guide clearance')
 clips=[('Front rim keeper',top_clip(False)),('Rear screw tab',top_clip(True))]
 spacer_plate('top-clips',clips)
 spacer_plate('top-tier',[('Upper front junction',r.junction(False,'front')),('Upper rear junction',r.junction(False,'rear'))]+clips)
 for obj in [top_clip(False),r.rear(top_clip(True)),r.core,extr(r.section,-90,59),drawer('open')]:
  assert (obj^top_tie).volume()<.001,'top tie clearance'
 for b in (False,True):
  assert (r.junction(False,'rear' if b else 'front')^(r.rear(r.cable(False)) if b else r.cable(False))).volume()<.001,'middle tie clearance'
 # Model identification uses each named solid's triangle range, not screen hotspots.
 for x,y,n,w in loc:
  add(r.core,x,y,0,0,'core')
  if n:add(drawer(n),x,y,w,1,'one-piece-'+n)
 def anchor_fasteners(x,y,wood_y):
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
   j=r.junction(ground,'rear' if b else 'front')
   add(r.rear(j) if b else j,x,y,0,3 if middle else 2,key,kit)
  if middle:anchor_fasteners(x,y,r.rise/3+2.8)
  add(r.cable(ground),x,y,0,4,'tie')
 x=0;y=2*r.rise
 for b in (False,True):add(r.rear(top_clip(True)) if b else top_clip(False),x,y,0,3,'top-clips','top-tier')
 anchor_fasteners(x,y,56.5);add(top_tie,x,y,0,4,'tie')
 # Inverted empty triangles: one above the center bottom core and two above the middle row.
 for x,y in [(0,0),(-r.half,r.rise),(r.half,r.rise)]:
  for b in (False,True):add(r.rear(pk['tri_frame'](b)) if b else pk['tri_frame'](b),x,y,0,2,'triangle-pocket-frame','triangle-pocket')
  add(pk['tri_tie'](),x,y,0,4,'tie')
  add(pk['tri_bin'],x,y,-16 if x==0 else 0,1,'triangle-pocket')
 for sign,side in [(1,'left'),(-1,'right')]:
  x=-sign*r.pitch
  for b in (False,True):
   m=pk['side_frame'](b);m=m if sign==1 else m.mirror((1,0,0))
   add(r.rear(m) if b else m,x,0,0,2,side+'-pocket-frame',side+'-pocket')
  tray=pk['side_bin'] if sign==1 else pk['side_bin'].mirror((1,0,0))
  add(tray,x,0,-23 if sign==1 else 0,1,side+'-pocket')
  add(spacer_tie(-14*sign,r.rise),x,0,0,4,'tie')
 # Check new components in the complete 3–2–3 assembly, including both rim
 # faces, seats, ties, neighbors and the straight drawer body's swept envelope.
 fillers=['triangle-pocket-frame','left-pocket-frame','right-pocket-frame','triangle-pocket','left-pocket','right-pocket']
 sweep=extr(r.section,-80,r.L-1)
 for i,(m,key) in enumerate(installed):
  if key not in fillers:continue
  for j,(other,name) in enumerate(installed):
   if j!=i:assert abs((m^other).volume())<.001,(key,name,round((m^other).volume(),3))
  for x,y,n,w in loc:
   assert abs((m^sweep.translate((x,y,0))).volume())<.001,(key,x,y,'body sweep')
   assert abs((m^drawer('open').translate((x,y,0))).volume())<.001,(key,x,y,'closed')
 # Test withdrawal through the entire bank, including the pocket lip as it
 # passes the plane of the eight full-size round faces.
 for m,key in installed:
  if key not in ('left-pocket','right-pocket','triangle-pocket'):continue
  dx,dy,w=next(((x,y,w) for x,y,w in
     ([(-r.pitch,0,-23)] if key=='left-pocket' else [(r.pitch,0,0)] if key=='right-pocket' else [(0,0,-16),(-r.half,r.rise,0),(r.half,r.rise,0)])
     if abs((pk['tri_bin'] if key=='triangle-pocket' else pk['side_bin'] if key=='left-pocket' else pk['side_bin'].mirror((1,0,0))).translate((x,y,w)).bounding_box()[0]-m.bounding_box()[0])<.01))
  sh=pk['tri_sweep' if key=='triangle-pocket' else 'side_sweep']
  if key=='right-pocket':sh=sh.mirror((1,0))
  body_path=extr(sh,-100,56).translate((dx,dy,0))
  lip_path=extr(m.project(),-100,-r.lip-.01)
  for other,name in installed:
   if other is m:continue
   assert abs((body_path^other).volume())<.001 and abs((lip_path^other).volume())<.001,(key,name,'extraction',round((body_path^other).volume(),2),round((lip_path^other).volume(),2))
 r.trimesh.util.concatenate(parts).export(out/'mock-assembly.stl')
 items=json.loads((P/'parts.json').read_text())
 assert {key for _,_,primary,kit in colors for key in (primary,kit) if key}==set(items)
 (P/'colors.json').write_text(json.dumps(dict(rows=[3,2,3],groups=colors,items=items),indent=2)+'\n')
 (P/'checks.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
