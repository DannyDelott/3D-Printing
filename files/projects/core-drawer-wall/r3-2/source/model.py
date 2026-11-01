"""R3.2 fixed drawer wall. Cross section XY, axial W front-to-back, millimetres."""
from pathlib import Path
import importlib.util, math,json
import numpy as np
from manifold3d import Manifold as M
P=Path(__file__).resolve().parents[1];OUT=P/'models'
spec=importlib.util.spec_from_file_location('shield',P.parent/'r3-1/source/model.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
r=s.r;extr=r.extr;box=r.box;circle=r.circle;front=s.front;end=s.back; center=(front+1.6+end)/2
# Keep a closed, 1.6 mm front wall; the disk screws to the outside face.
# Move the existing radiused cavity's front end rearward, keeping the rear fixed.
cut=s.cut.transform([[1,0,0,0],[0,1,0,0],[0,0,(end-front-1.6)/(end-front),1.6*end/(end-front)]])
outside=extr(r.section,front,r.L-1);void=cut^outside
body=outside-cut
rad=43.4
shield=extr(circle(rad),s.f,front)+s.pull
# Key the face position without a separate alignment jig. The triangular
# locating keys grow from the closed front wall; the matching blind pockets
# face the bin and never open into either compartment.
for x in [-19,19]:
 for recess in [False,True]:
  margin=.22 if recess else 0.
  section=r.poly([(-20-margin,front+.06),(-17,front-.8-margin),(-14+margin,front+.06)])
  key=extr(section,x-2.5-margin,x+2.5+margin).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
  if recess:shield-=key
  else:body+=key
# One accessible #4 x 3/8 in sheet-metal screw enters from the disk front.
# A low rounded lug merges into the floor; the pilot is blind behind the screw.
sx,sy=12.,r.floor+1.9
lug=extr(circle(4.4,sx,sy),front,front+5.7)+M.sphere(4.4,48).translate((sx,sy,front+5.7))
body+=lug^outside
pilot=extr(circle(1.19,sx,sy),front-1,front+8.1)
body-=pilot;shield-=extr(circle(1.7,sx,sy),s.f-1,front+.3)
void=void-body
# The 9.525 mm screw has >0.9 mm of unused pilot at its tip.
assert s.f+9.525 < front+8.1
assert abs((shield^body).volume())<1e-5

# Divider strips overlap the body at walls and floor. Rounded crown; straight
# integral fences have no loose inserts or slot pockets to collect small parts.
def fence(along):
 h=r.top; a=.8
 xz=box(-a,-45,a,h-a)+circle(a,0,h-a)
 if along:return extr(xz,front+.25,r.L-1-.25)
 return extr(xz,-44,44).transform([[0,0,1,0],[0,1,0,0],[1,0,0,center]])
def divider_body(mode):
 if mode=='open':return body
 return body+(fence(mode=='left-right') ^ outside)
def top_clip(back):
 # Two local curved rim jaws; the bolt is above the cardboard. Both clips
 # print board/front-face down and use the same stock screw at every anchor.
 zone=box(-9,37,9,49)
 cap=(circle(46.4)-circle(39.8))^zone
 prongs=((circle(46.4)-circle(44.55))+(circle(40.9)-circle(39.8)))^zone
 pad=r.rnd(-7.5,43.6,7.5,61.8 if back else 52.6,2.4)
 m=extr(cap+pad,-r.lip,0)+extr(prongs,0,4.2)
 # A thin ear, thick locally at the bolt and wood screw.
 m+=extr(pad-circle(44.55),0,1.0)
 m+=extr(circle(4.15,0,48.5),0,2.5)
 m-=extr(circle(1.8,0,48.5),-3,8)
 if back:
  m+=extr(circle(4.9,0,56.5),0,2.8)
  m-=extr(circle(2.4,0,56.5),-3,9)
  m-=M.cylinder(1.7,3.5,1.8,80).translate((0,48.5,-r.lip))
 return m
def mid(back):
 m=r.junction(False);cy=r.rise/3
 holes=r.rnd(-6.6,cy-8.2,6.6,cy+8.8,2)
 for x,y in r.centers:holes-=circle(r.ro,x,y)
 m+=extr(holes,0,2.8 if back else 1)
 m-=extr(circle(1.8,0,cy-3.7),-2,18)
 if back:
  m-=M.cylinder(1.7,3.5,1.8,80).translate((0,cy-3.7,-r.lip))
  m-=extr(circle(2.4,0,cy+2.9),-3,18)
  m-=extr(circle(4.85,0,cy+2.9),2.8,18)
 return m
def tied_end(sign,back):
 # Pair both rim pieces with one small cable tie, including on a lone core.
 m=r.junction(True,edge=sign)
 xs=[sign*2.7,sign*9.6];cy=-31.
 for x in xs:m-=extr(r.rnd(x-.95,cy-1.65,x+.95,cy+1.65,.45),-3,12)
 if back:m-=extr(r.rnd(min(xs)-1,max(-33.,cy-1.7),max(xs)+1,cy+1.7,.55),-r.lip-.1,-r.lip+1.1)
 return m
def shaft(x,y):
 # Installed fastener: M3 x 70, 90 degree countersunk head at the board.
 local=M.cylinder(1.55,3.05,1.5,72).translate((x,y,-r.lip))+extr(circle(1.5,x,y),-r.lip+1.55,70-r.lip)
 return r.rear(local)
def print_part(name,items,checks):
 parts=r.plate(items);mesh=r.trimesh.util.concatenate([m for _,m in parts]);mesh.export(OUT/(name+'-r3-2.stl'))
 r.OUT=OUT;r.write3(name,parts);(OUT/(name+'-r3.3mf')).rename(OUT/(name+'-r3-2.3mf'))
 checks[name]=dict(print_bounds=mesh.extents.round(2).tolist(),objects=len(parts))
def main():
 OUT.mkdir(exist_ok=True);checks={}
 # Turn the shield so its flat keyed face lies on the bed and pull grows up.
 face_up=shield.mirror((0,0,1))
 cap=void.volume()/1000
 for mode in ['open','left-right','front-back']:
  tub=divider_body(mode)
  print_part(mode,[(mode+' bin',r.world(tub)),('Full dust face - pull up',face_up)],checks)
  checks[mode]['capacity_ml']=round(cap-(tub-body).volume()/1000,1)
  if mode!='open':
   halves=[extr(box(-70,-70,0,70),front,end),extr(box(0,-70,70,70),front,end)] if mode=='left-right' else [extr(box(-70,-70,70,70),front,center),extr(box(-70,-70,70,70),center,end)]
   checks[mode]['cell_ml']=[round(((void-tub)^half).volume()/1000,1) for half in halves]
  closed=tub+shield
  for deg in range(0,360,60):
   shift=(r.pitch*math.cos(math.radians(deg)),r.pitch*math.sin(math.radians(deg)),0)
   assert abs((closed ^ closed.translate(shift)).volume())<1e-6
  assert abs((circle(r.ID/2)-circle(rad)).area())<1e-6
 print_part('middle-mount',[('Middle front',mid(False)),('Middle screw mount',mid(True))],checks)
 print_part('top-clips',[('Top front keeper',top_clip(False)),('Top screw tab',top_clip(True))],checks)
 print_part('dry-ends',[(('Rear' if b else 'Front')+' outside foot',tied_end(sn,b)) for sn in [-1,1] for b in [False,True]],checks)
 print_part('top-tier',[('Upper front Y - tie slots',r.junction(False,'front')),('Upper rear Y - tie slots',r.junction(False,'rear')),('Top front keeper',top_clip(False)),('Top screw tab',top_clip(True))],checks)
 # Verify actual washer/nut envelopes, countersunk bolt, wood screw access,
 # rear board plane, stationary cardboard and the straight drawer sweep.
 sweep=extr(r.section,-r.L-15,r.L-1)
 for top in [True,False]:
  F=top_clip(False) if top else mid(False); B=top_clip(True) if top else mid(True)
  y=48.5 if top else r.rise/3-3.7; wood=56.5 if top else r.rise/3+2.9
  bolt=shaft(0,y);washer=extr(circle(3.7,0,y),-r.lip-3.6,-r.lip-.01)
  shank=extr(circle(2.31,0,wood),-20,25);driver=extr(circle(4.65,0,wood),2.81,90)
  for m in [F,r.rear(B)]:assert abs((bolt^m).volume())<1e-5
  assert all(abs((m^B).volume())<1e-5 for m in [shank,driver])
  for x,y0 in ([(0,0)] if top else r.centers):
   core=r.core.translate((x,y0,0));d=(body+shield).translate((x,y0,0))
   assert abs((driver^core).volume())<1e-5
   for a in [F,r.rear(B),bolt,washer]:
    for v in [core,d,sweep.translate((x,y0,0))]:
     assert abs((a^v).volume())<1e-5,(top,x,y0,(a^v).volume())
   # During withdrawal the disk only moves toward the user. Check its full
   # circular extrusion against forward bolt/nut projections as well.
   assert abs((extr(circle(rad,x,y0),-80,front)^washer).volume())<1e-5
 checks['layout']=dict(rows=8,counts=[9,8,7,6,5,4,3,2],width_mm=round(9*r.pitch,1),height_with_tab_mm=round(44.8+7*r.rise+61.8,1),disk_overlap_mm=round(rad-r.ID/2,1),disk_clearance_mm=round(r.pitch-2*rad,1))
 (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
 # Joined individual drawer previews keep accurate assembled positions.
 for mode in ['open','left-right','front-back']:
  m=r.mesh(r.world(divider_body(mode)+shield));m.export(OUT/(mode+'-assembled-r3-2.stl'))
if __name__=='__main__':main()
