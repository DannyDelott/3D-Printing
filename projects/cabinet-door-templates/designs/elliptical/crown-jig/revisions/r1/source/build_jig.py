"""Crown jig R1. Millimetres. CAD dimensions are proposals pending bench fit.
Two four-section rails, four 608 rollers, two printed trucks and wood bridge.
"""
from pathlib import Path
import json,math,zipfile
from xml.etree import ElementTree as ET
import cadquery as cq
import trimesh
OUT=Path(__file__).resolve().parents[1];(OUT/'models').mkdir(exist_ok=True)
R=1362.1411458333334;P=25.4;F=6.35;TOP=22.;S=100.;BR=11.
D=R+P-F-TOP;RC=math.hypot(D,S/2);RT=RC-BR
BACK=50.8;C=BACK+38.1-R;RAIL_BASE=6.35;MID=C+D
config=dict(revision='R1',units='mm',datum='Z=0 is the top of the guide backers at the final cut setting',door_revision='R7 f',crown=19.05,target_radius=R,guide_radius=RT,roller_radius=BR,roller_spacing=S,bridge_floor_thickness=F,truck_top_above_axles=TOP,bit_projection_below_factory_base=P,rail_back_height=BACK,stile_back_height=BACK+3.175,panel_finished_back_height=BACK+12.95,rail_length=600,segment_length=150,rail_thickness=18,rail_centers_y=[-400,400],bridge_floor=[220,900,F],bridge_ribs=[18,900,70],bridge_slot=[28,740],bearing='608: 22 OD × 8 ID × 7 wide; four required',bearing_spacers='Eight steel inner-race shims: 8.2 mm ID, 11.5 mm OD, 0.5 mm thick; verify actual bearing inner-race land',printer_assumption='Parts fit a 180 × 180 mm bed individually; printer model unconfirmed',material='PLA',bit='Proposed Freud 16-104 / 16-10425P: 19.05 mm diameter, 6.35 mm shank, approximately 12.7 mm cutting height',router='Ryobi ONE+ brushless; PBLRR01 manual consulted, exact user model unconfirmed',critical_unverified=['25.4 mm bit projection with full manufacturer-required collet engagement','Actual bridge plywood thickness','Router base and dust-port clearance within 184 mm lane','Printed fit, bearing retention, assembled stiffness and workholding','Panel core layup and depth allowance'])
(OUT/'parameters.json').write_text(json.dumps(config,indent=2)+'\n')
def box(x,y,z,w,d,h):return cq.Solid.makeBox(w,d,h,cq.Vector(x,y,z))
def cyl(x,y,z,r,l,axis=(0,0,1)):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(*axis))
def prof(points,y,thick):return cq.Solid.extrudeLinear(cq.Wire.makePolygon([cq.Vector(x,y,z) for x,z in points],close=True),[],cq.Vector(0,thick,0))
def top(x):return math.sqrt(RT*RT-x*x)+C-RAIL_BASE
parts={};scene=[];scene_solids=[]
def addscene(name,s,kind='printed',group='fixed'):
 assert s.isValid() and s.Volume()>0,name
 vs,fs=s.tessellate(.07,.07);m=trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True);m.fix_normals();assert m.is_watertight,name
 scene_solids.append((name,s,group))
 scene.append(dict(name=name,kind=kind,group=group,vertices=m.vertices.tolist(),triangles=m.faces.tolist()))
def save(name,s,orientation=None,quantity=1):
 assert s.isValid() and len(s.Solids())==1,name
 ss=orientation(s) if orientation else s
 bb=ss.BoundingBox();ss=ss.translate((-bb.xmin,-bb.ymin,-bb.zmin));bb=ss.BoundingBox()
 assert bb.xlen<=180.01 and bb.ylen<=180.01 and bb.zlen<=180.01,(name,bb.xlen,bb.ylen,bb.zlen)
 ss.exportStep(str(OUT/'models'/f'{name}.step'),write_pcurves=False)
 cq.exporters.export(ss,str(OUT/'models'/f'{name}.stl'),tolerance=.04,angularTolerance=.06)
 vs,fs=ss.tessellate(.04,.06);m=trimesh.Trimesh([v.toTuple() for v in vs],fs,process=True);m.fix_normals();assert m.is_watertight and m.volume>0,name
 ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
 root=ET.Element('{'+ns+'}model',unit='millimeter');res=ET.SubElement(root,'{'+ns+'}resources');ob=ET.SubElement(res,'{'+ns+'}object',id='1',type='model',name=name);me=ET.SubElement(ob,'{'+ns+'}mesh');vv=ET.SubElement(me,'{'+ns+'}vertices');ff=ET.SubElement(me,'{'+ns+'}triangles')
 for xyz in m.vertices:ET.SubElement(vv,'{'+ns+'}vertex',**dict(zip('xyz',map(str,xyz))))
 for f in m.faces:ET.SubElement(ff,'{'+ns+'}triangle',**{f'v{i+1}':str(v) for i,v in enumerate(f)})
 build=ET.SubElement(root,'{'+ns+'}build');ET.SubElement(build,'{'+ns+'}item',objectid='1')
 with zipfile.ZipFile(OUT/'models'/f'{name}.3mf','w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>');z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>');z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 re=cq.importers.importStep(str(OUT/'models'/f'{name}.step')).val();assert re.isValid() and len(re.Solids())==1,name
 parts[name]=dict(quantity=quantity,size=[bb.xlen,bb.ylen,bb.zlen],volume_mm3=ss.Volume(),watertight=True,step_reimport=True)
for i in range(4):
 a=-300+i*150;b=a+150
 pts=[(a,0),(b,0)]+[(b-(b-a)*j/80,top(b-(b-a)*j/80)) for j in range(81)]
 rail=prof(pts,-9,18)
 for lo,hi in [(a+12,a+69),(a+81,b-12)]:
  window=[(lo,14),(hi,14)]+[(hi-(hi-lo)*j/25,top(hi-(hi-lo)*j/25)-14) for j in range(26)]
  rail=rail.cut(prof(window,-10,20))
 for x in [a+30,b-30]:rail=rail.cut(cyl(x,-12,8,2.6,24,(0,1,0)))
 for x in [a,b-12]:rail=rail.cut(cyl(x,0,7,3.15,12,(1,0,0)))
 save(f'guide-{i+1}',rail,lambda s:s.rotate((0,0,0),(1,0,0),90),2)
 for y in [-400,400]:addscene(f'Guide {i+1}',rail.translate((0,y,RAIL_BASE)))
foot=box(-17.5,-35,0,35,70,6.35).fuse(box(-17.5,-14.2,6.35,35,5,15.65)).fuse(box(-17.5,9.2,6.35,35,5,15.65))
for y in [-26,26]:foot=foot.cut(cyl(0,y,-1,2.25,9))
foot=foot.cut(cyl(0,-20,14.35,2.6,40,(0,1,0))).clean();save('rail-foot',foot,quantity=16)
for y in [-400,400]:
 for x in [-270,-180,-120,-30,30,120,180,270]:addscene('Rail foot',foot.translate((x,y,0)))
truck=box(-70,-30,12,140,60,10)
for x in [-50,50]:
 for y in [-11,4]:truck=truck.fuse(box(x-10,y,-5,20,7,17))
 truck=truck.cut(cyl(x,-16,0,4.15,32,(0,1,0)))
for y in [-14.3,9.3]:truck=truck.fuse(box(-35,y,-20,70,5,32))
for x in [-25,25]:
 for y in [-23,23]:truck=truck.cut(cyl(x,y,11,2.6,12))
truck=truck.clean();save('bridge-truck',truck,lambda s:s.rotate((0,0,0),(1,0,0),180),2)
roller_coupon=truck.intersect(box(35,-15,-6,30,30,29));save('roller-fit-coupon',roller_coupon,lambda s:s.rotate((0,0,0),(1,0,0),180))
for y in [-400,400]:
 addscene('Bridge truck',truck.translate((0,y,MID)),group='bridge')
 for x in [-50,50]:addscene('608 roller',cyl(x,y-3.5,MID,11,7,(0,1,0)).cut(cyl(x,y-4,MID,4,8,(0,1,0))),'metal','bridge')
# Coupon includes actual jaw clearance, M5 retention and one rail profile section.
coupon=prof([(-20,0),(20,0)]+[(20-j,top(20-j)) for j in range(41)],-9,18).cut(cyl(0,-12,8,2.6,24,(0,1,0)))
save('guide-fit-coupon',coupon,lambda s:s.rotate((0,0,0),(1,0,0),90))
pin=cyl(0,0,0,2.95,22);save('alignment-pin',pin,quantity=6)
# Safe dry-fit setup gauge: unpowered tool only, cutter positioned in open notch.
gauge=box(-35,-15,0,70,30,P).cut(box(-12,-16,-1,24,25,P+2)).clean();save('projection-gauge',gauge)
stop=box(-15,-35,0,30,70,8).fuse(box(-15,-5,8,10,10,65))
for y in [-26,26]:stop=stop.cut(cyl(0,y,-1,2.25,10))
save('travel-stop',stop,quantity=4)
for x in [-319,319]:
 for y in [-400,400]:addscene('Travel stop',stop.rotate((0,0,0),(0,0,1),180 if x<0 else 0).translate((x,y,0)))
for y in [-400,400]:addscene('Wood backer',box(-345,y-50,-18,690,100,18),'wood')
plate=box(-110,-450,MID+22,220,900,F).cut(box(-14,-370,MID+21,28,740,F+2))
for y in [-400,400]:
 for x in [-25,25]:
  for dy in [-23,23]:plate=plate.cut(cyl(x,y+dy,MID+21,2.6,F+2))
addscene('Bridge floor',plate,'wood','bridge')
for x in [-110,92]:addscene('Bridge stiffener',box(x,-450,MID+22+F,18,900,70),'wood','bridge')
# Tool is an envelope, not a measured Ryobi model; factory base rests on floor.
addscene('Factory router base envelope',cyl(0,0,MID+22+F,55,8),'tool','router')
addscene('Router body envelope',cyl(0,0,MID+30+F,37,125),'tool','router')
addscene('19.05 mm cutter envelope',cyl(0,0,BACK+38.1,9.525,12.7),'metal','router')
# Back-flat finished rail, only to illustrate actual target surface.
pts=[(-227.0125,BACK),(227.0125,BACK)]+[(227.0125-454.025*j/100,math.sqrt(R*R-(227.0125-454.025*j/100)**2)+C) for j in range(101)]
addscene('Finished rail example',prof(pts,-57.15,114.3),'work')
addscene('Work support example',box(-227,-57.15,0,454,114.3,BACK),'wood')
(OUT/'scene.json').write_text(json.dumps(dict(parameters=config,center_z=C,truck_axle_z=MID,parts=scene),separators=(',',':')))
# Kinematic check: rollers lie on guide+wheel circle, cutter center lies on R.
checks=[]
for deg in range(-10,11):
 t=math.radians(deg);normal=(math.sin(t),math.cos(t));tangent=(math.cos(t),-math.sin(t))
 for side in [-1,1]:
  x=D*normal[0]+side*S/2*tangent[0];z=D*normal[1]+side*S/2*tangent[1]
  assert abs(math.hypot(x,z)-(RT+BR))<1e-8
 tip_radius=D+TOP+F-P;assert abs(tip_radius-R)<1e-8
 checks.append({'angle':deg,'tip_radius_mm':tip_radius,'roller_contact_error_mm':0})
# Check motion against fixed geometry; intentional tangent contacts have zero volume.
collisions=[]
for deg in [-9.7,-5,0,5,9.7]:
 for name,s,group in scene_solids:
  if group not in ['bridge','router']:continue
  moved=s.rotate((0,0,C),(0,1,C),deg);b=moved.BoundingBox()
  for fn,fs,fg in scene_solids:
   if fg!='fixed':continue
   f=fs.BoundingBox()
   if b.xmax<=f.xmin or f.xmax<=b.xmin or b.ymax<=f.ymin or f.ymax<=b.ymin or b.zmax<=f.zmin or f.zmax<=b.zmin:continue
   volume=moved.intersect(fs).Volume()
   if volume>0.01:collisions.append(dict(angle=deg,moving=name,fixed=fn,volume_mm3=volume))
assert not collisions,collisions
validation=dict(motion_collision_check=dict(angles_degrees=[-9.7,-5,0,5,9.7],positive_volume_collisions=collisions,scope='Bridge and tool at centered longitudinal position against modeled fixed parts; excludes unmodeled clamps, bolts and rough stock'),parts=parts,all_parts_valid=True,all_meshes_watertight=True,all_step_reimports_valid=True,kinematics=checks,physical_validation='Not performed. Print fit coupon and foot first; check router reach and bridge dimensions before powered use.',guide_segments_per_rail=4,rails=2,largest_print_xy=max(max(v['size'][:2]) for v in parts.values()))
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({'guide_radius':RT,'target_radius':R,'parts':parts},indent=2))
