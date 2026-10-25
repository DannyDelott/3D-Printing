"""R2 component-sized crown jigs; millimetres. Physical fit remains unverified."""
from pathlib import Path
import json, math, zipfile
from xml.etree import ElementTree as ET
import cadquery as cq
import trimesh
OUT=Path(__file__).resolve().parents[1];(OUT/'models').mkdir(exist_ok=True)
R=1362.1411458333334;P=25.4;F=6.35;TOP=22.;S=80.;BR=11.
D=R+P-F-TOP;RC=math.hypot(D,S/2);RT=RC-BR
BACK=50.8;C=BACK+38.1-R;RAIL_BASE=6.35;MID=C+D
door=json.loads((OUT/'source/door-reference.json').read_text())
source_parts={p['name']:p for p in door['parts']}
STILE_LENGTH=max(v[1] for v in source_parts['Right stile']['vertices'])-min(v[1] for v in source_parts['Right stile']['vertices'])
COMMON=dict(revision='R2',units='mm',door_revision='R7 f',crown=19.05,target_radius=R,guide_radius=RT,roller_radius=BR,roller_spacing=S,bridge_floor_thickness=F,truck_top_above_axles=TOP,bit_projection_below_factory_base=P,rail_thickness=18,bridge_width=150,clear_router_lane=114,margin=76.2,material='PLA',datum='Z=0 is the final guide-backer top plane',printer_assumption='All individual parts fit a 180 × 180 mm bed; printer model unconfirmed',critical_unverified=['Exact router base/body fit in 114 mm lane','25.4 mm cutter projection with proper collet engagement','Actual plywood thickness, printed fit and assembled stiffness','Rough blank and joinery allowances before sizing wood bridge','Workholding outside full cutter sweep'])
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
# Shared compact trucks and feet. Four 608 rollers on steel inner-race spacers.
foot=box(-17.5,-30,0,35,60,6.35).fuse(box(-17.5,-14.2,6.35,35,5,15.65)).fuse(box(-17.5,9.2,6.35,35,5,15.65))
for y in [-22,22]:foot=foot.cut(cyl(0,y,-1,2.25,9))
foot=foot.cut(cyl(0,-20,14.35,2.6,40,(0,1,0))).clean();save('rail-foot',foot,quantity=16)
truck=box(-55,-30,12,110,60,10)
for x in [-40,40]:
 for y in [-11,4]:truck=truck.fuse(box(x-10,y,-5,20,7,17))
 truck=truck.cut(cyl(x,-16,0,4.15,32,(0,1,0)))
for y in [-14.3,9.3]:truck=truck.fuse(box(-25,y,-20,50,5,32))
for x in [-15,15]:
 for y in [-23,23]:truck=truck.cut(cyl(x,y,11,2.6,12))
truck=truck.clean();save('bridge-truck',truck,lambda s:s.rotate((0,0,0),(1,0,0),180),2)
save('roller-fit-coupon',truck.intersect(box(25,-15,-6,30,30,29)),lambda s:s.rotate((0,0,0),(1,0,0),180))
coupon=prof([(-20,0),(20,0)]+[(20-j,top(20-j)) for j in range(41)],-9,18).cut(cyl(0,-12,8,2.6,24,(0,1,0)))
save('guide-fit-coupon',coupon,lambda s:s.rotate((0,0,0),(1,0,0),90))
save('alignment-pin',cyl(0,0,0,2.95,22),quantity=6)
save('projection-gauge',box(-35,-15,0,70,30,P).cut(box(-12,-16,-1,24,25,P+2)).clean())
variants={}
for kind,width,length,cx,count,low,high,back,part_name in [('rail',454.025,114.3,0,4,-9.7,9.7,BACK,'Bottom rail'),('stile',57.15,STILE_LENGTH,198.4375,1,7.05,9.7,BACK+3.175,'Right stile')]:
 scene=[];scene_solids=[];used=['rail-foot','bridge-truck','roller-fit-coupon','guide-fit-coupon','projection-gauge'];feet=[]
 ymin=-(length/2+45);ymax=-ymin;total_length=length+152.4;total_width=width+152.4
 xmin=cx-width/2-50;xmax=cx+width/2+50;seg=(xmax-xmin)/count
 config=dict(COMMON,component=kind,component_width=width,component_length=length,component_center_x=cx,flat_back_height=back,guide_centers_y=[ymin,ymax],guide_range=[xmin,xmax],guide_segments_per_rail=count,footprint=[total_width,total_length],bridge_floor=[150,total_length,F],bridge_ribs=[18,total_length,50],bridge_slot=[28,length+32],angle_range=[low,high],rail_foot_quantity=4*count,source_part=part_name,component_envelope_verified=True,rough_stock_allowance='Not included in the model envelope; verify blank and tenon lengths before cutting wood bridge')
 for i in range(count):
  a=xmin+i*seg;b=a+seg
  shape=prof([(a,0),(b,0)]+[(b-(b-a)*j/80,top(b-(b-a)*j/80)) for j in range(81)],-9,18)
  mid=(a+b)/2
  for lo,hi in [(a+12,mid-6),(mid+6,b-12)]:
   shape=shape.cut(prof([(lo,14),(hi,14)]+[(hi-(hi-lo)*j/25,top(hi-(hi-lo)*j/25)-14) for j in range(26)],-10,20))
  for x in [a+25,b-25]:shape=shape.cut(cyl(x,-12,8,2.6,24,(0,1,0)));feet.append(x)
  if count>1:
   for x in [a,b-12]:shape=shape.cut(cyl(x,0,7,3.15,12,(1,0,0)))
  name=f'{kind}-guide-{i+1}';save(name,shape,lambda s:s.rotate((0,0,0),(1,0,0),90),2);used.append(name)
  for y in [ymin,ymax]:addscene(name,shape.translate((0,y,RAIL_BASE)))
 if count>1:used.append('alignment-pin')
 for y in [ymin,ymax]:
  for x in feet:addscene('Rail foot',foot.translate((x,y,0)))
  addscene('Wood backer',box(cx-total_width/2,y-30,-18,total_width,60,18),'wood')
  addscene('Bridge truck',truck.translate((0,y,MID)),group='bridge')
  for x in [-40,40]:addscene('608 roller',cyl(x,y-3.5,MID,11,7,(0,1,0)).cut(cyl(x,y-4,MID,4,8,(0,1,0))),'metal','bridge')
 # Stops sit beyond the track ends and contact the trucks before rollers run off.
 for side,deg in [(-1,low-.1),(1,high+.1)]:
  t=math.radians(deg);inner=(D+12)*math.sin(t)+side*55*math.cos(t)
  far=inner+side*10;height=C+(D+TOP)/math.cos(t)-far*math.tan(t)-3
  stop=box(0,-30,0,15,60,8).fuse(box(0,-5,8,10,10,height-8))
  for y in [-22,22]:stop=stop.cut(cyl(7.5,y,-1,2.25,10))
  name='end-stop' if kind=='rail' or side==1 else 'stile-high-stop'
  if name not in parts:save(name,stop,quantity=4 if name=='end-stop' else 2)
  used.append(name)
  for y in [ymin,ymax]:addscene(name,stop.rotate((0,0,0),(0,0,1),180 if side<0 else 0).translate((inner,y,0)))
 plate=box(-75,-total_length/2,MID+TOP,150,total_length,F).cut(box(-14,-(length+32)/2,MID+TOP-1,28,length+32,F+2))
 for y in [ymin,ymax]:
  for x in [-15,15]:
   for dy in [-23,23]:plate=plate.cut(cyl(x,y+dy,MID+TOP-1,2.6,F+2))
 addscene('Bridge floor',plate,'wood','bridge')
 for x in [-75,57]:addscene('Bridge stiffener',box(x,-total_length/2,MID+TOP+F,18,total_length,50),'wood','bridge')
 addscene('Factory base envelope',cyl(0,0,MID+TOP+F,55,8),'tool','router')
 addscene('Router body envelope',cyl(0,0,MID+TOP+F+8,37,125),'tool','router')
 addscene('Cutter envelope',cyl(0,0,BACK+38.1,9.525,12.7),'metal','router')
 # Conservatively check clearances against a full rectangular component envelope.
 pts=[(cx-width/2,back),(cx+width/2,back)]+[(cx+width/2-width*j/100,math.sqrt(R*R-(cx+width/2-width*j/100)**2)+C) for j in range(101)]
 addscene('Component envelope',prof(pts,-length/2,length),'work')
 addscene('Work carrier',box(cx-width/2,-length/2,-18,width,length,back+18),'wood')
 # Display the actual R7 part in place of the conservative collision envelope.
 actual=source_parts[part_name];ymid=(min(v[1] for v in actual['vertices'])+max(v[1] for v in actual['vertices']))/2
 work=next(p for p in scene if p['name']=='Component envelope');work.update(name=part_name,vertices=[[x-228.6,y-ymid,z-3+back] for x,y,z in actual['vertices']],triangles=actual['triangles'])
 collisions=[];angles=[low,(low+high)/2,high]
 for deg in angles:
  for name,s,group in scene_solids:
   if group not in ['bridge','router']:continue
   moved=s.rotate((0,0,C),(0,1,C),deg);bb=moved.BoundingBox()
   for fn,fs,fg in scene_solids:
    if fg!='fixed':continue
    fb=fs.BoundingBox()
    if bb.xmax<=fb.xmin or fb.xmax<=bb.xmin or bb.ymax<=fb.ymin or fb.ymax<=bb.ymin or bb.zmax<=fb.zmin or fb.zmax<=bb.zmin:continue
    volume=moved.intersect(fs).Volume()
    if volume>.01:collisions.append(dict(angle=deg,moving=name,fixed=fn,volume=volume))
 assert not collisions,(kind,collisions)
 for deg in angles:
  t=math.radians(deg)
  for sign in [-1,1]:
   wheelx=D*math.sin(t)+sign*S/2*math.cos(t);contactx=wheelx*RT/RC
   assert xmin<contactx<xmax,(kind,contactx)
  assert abs(D+TOP+F-P-R)<1e-8
 config['downloads']=list(dict.fromkeys(used));variants[kind]=config
 (OUT/f'{kind}-scene.json').write_text(json.dumps(dict(parameters=config,center_z=C,truck_axle_z=MID,parts=scene),separators=(',',':')))
(OUT/'parameters.json').write_text(json.dumps(dict(common=COMMON,variants=variants),indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps(dict(parts=parts,all_parts_valid=True,all_meshes_watertight=True,all_step_reimports_valid=True,collision_angles={k:[v['angle_range'][0],sum(v['angle_range'])/2,v['angle_range'][1]] for k,v in variants.items()},positive_volume_collisions=[],scope='Bridge and tool at central longitudinal position versus modeled fixtures and component envelopes; clamps, bolts and rough stock excluded',roller_contact_on_tracks=True,cutter_radius_error_mm=0,physical_validation='Not performed; check coupons, router envelope and cutter reach before powered use.'),indent=2)+'\n')
print(json.dumps(variants,indent=2))
