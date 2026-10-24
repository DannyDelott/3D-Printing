"""R2 exact CAD: six-inch overlay cabinet, through dovetails and grooved panel.
Run with CadQuery 2.8, Shapely 2 and trimesh. Input/output units: millimetres.
"""
import json, math, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import cadquery as cq
import trimesh
from shapely.geometry import Polygon, Point
from shapely.affinity import rotate
from shapely.ops import unary_union
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.Geom import Geom_Ellipse
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Vec
OUT=Path(__file__).resolve().parents[1]
p=json.loads((OUT/'source/parameters.json').read_text())
W,H,S=p['case_width'],p['case_height'],p['case_side_thickness']
T,ST,G=p['door_thickness'],p['stile_thickness'],p['door_gap']
D=p['overall_depth']-T-G;p['case_depth']=D
R=p['side_reveal'];DW=W-2*R;DH=p['door_height'];SW=p['stile_width'];Q=p['ellipse_q']
A=DW/Q;B=(p['rail_deep']-p['rail_shallow'])/(1-math.sqrt(1-Q*Q));CY=p['rail_shallow']+B
GW,GD=p['groove_width'],p['groove_depth'];GZ=(ST-GW)/2
LW,LT,BG=p['knife_leaf_width'],p['knife_leaf_thickness'],p['knife_bearing_gap']
PX=W-R-LW/2;PZ=G+T/2
parts=[]
def box(x,y,z,w,h,d):return cq.Solid.makeBox(w,h,d,cq.Vector(x,y,z))
def bottom(x):return CY-B*math.sqrt(1-(x/A)**2)
def add(name,shape,group='case',grain='y',material='wood'):
    assert shape.isValid() and shape.Volume()>0,name
    parts.append(dict(name=name,shape=shape,group=group,grain=grain,material=material))
def rail():
    curve=Geom_Ellipse(gp_Ax2(gp_Pnt(0,CY,0),gp_Dir(0,0,-1),gp_Dir(1,0,0)),A,B)
    wire=BRepBuilderAPI_MakeWire()
    for a,b in [((0,0),(DW,0)),((DW,0),(DW,p['rail_deep']))]:wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(*a,0),gp_Pnt(*b,0)).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(curve,math.acos(Q),math.pi/2).Edge())
    wire.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(0,p['rail_shallow'],0),gp_Pnt(0,0,0)).Edge())
    return cq.Shape.cast(BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(0,0,T)).Shape())
def prism_xz(points,y,height):
    wire=cq.Wire.makePolygon([cq.Vector(x,y,z) for x,z in points],close=True)
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(0,height,0))
def cyl_y(x,y,z,r,h):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,1,0))
# Vertical sides carry three through-tails at each end. Top/bottom are pin boards.
case_left=box(0,S,-D,S,H-2*S,D);case_right=box(W-S,S,-D,S,H-2*S,D)
case_h=[box(0,0,-D,W,S,D),box(0,H-S,-D,W,S,D)];tails=[]
for side,x in [('left',0),('right',W-S)]:
    for j,top in enumerate([False,True]):
        for i in range(p['tails_per_corner']):
            c=-D+(i+.5)*D/p['tails_per_corner'];neck=D/6;flare=S/p['dovetail_slope']
            yz=[(S,c-neck/2),(0,c-neck/2-flare),(0,c+neck/2+flare),(S,c+neck/2)]
            if top:yz=[(H-y,z) for y,z in yz][::-1]
            wire=cq.Wire.makePolygon([cq.Vector(x,y,z) for y,z in yz],close=True)
            tail=cq.Solid.extrudeLinear(wire,[],cq.Vector(S,0,0));tails.append(tail)
            if side=='left':case_left=case_left.fuse(tail)
            else:case_right=case_right.fuse(tail)
            case_h[j]=case_h[j].cut(tail)
case_shapes=[case_left,case_right,case_h[0],case_h[1],box(S,S,-D,W-2*S,H-2*S,p['back_thickness'])]
# Exact asymmetric frame. Stiles have flush backs and 1/8-inch front setback.
low=rail();high=low.rotate((DW/2,DH/2,0),(DW/2,DH/2,1),180)
left=box(0,0,0,SW,DH,ST).cut(low).cut(high)
right=box(DW-SW,0,0,SW,DH,ST).cut(low).cut(high)
opening=box(SW,0,0,DW-2*SW,DH,T).cut(low).cut(high)
wire=cq.Workplane(obj=opening).faces('<Z').val().outerWire()
# Offset all four boundaries, including the elliptical rails, normal to their edges.
def offset_prism(distance,z,depth):
    expanded=wire.offset2D(distance,'arc')
    assert len(expanded)==1
    # Convert offset-ellipse curves to exchange-safe splines before extrusion.
    # STEP otherwise reimports these offset-surface solids as open shells.
    exchange_wire=expanded[0].toSplines(degree=8,tolerance=1e-5)
    return cq.Solid.extrudeLinear(exchange_wire,[],cq.Vector(0,0,depth)).translate((0,0,z))
groove=offset_prism(GD,GZ,GW)
panel=offset_prism(GD-p['panel_edge_clearance'],GZ+(GW-p['panel_thickness'])/2,p['panel_thickness'])
frame=[s.cut(groove).translate((R,0,G)) for s in [low,high,left,right]]
panel=panel.translate((R,0,G))
# Both knife leaves are recessed. The stationary leaf is flush with the case's
# top/bottom; the moving leaf is one bearing gap and one leaf thickness deeper.
# Door clearance mortises follow the stationary-leaf swept envelope (0–110°),
# buffered 0.3 mm. No external mounting pad remains.
fixed_outline=unary_union([Polygon([(PX-LW/2,-32),(PX+LW/2,-32),(PX+LW/2,PZ),(PX-LW/2,PZ)]),Point(PX,PZ).buffer(LW/2,quad_segs=32)])
swept=unary_union([rotate(fixed_outline,a,origin=(PX,PZ),use_radians=False) for a in range(0,p['hinge_open_limit']+1)]).buffer(.3,quad_segs=16)
sweep_pts=list(swept.exterior.coords)[:-1]
for top in [False,True]:
    label='Upper' if top else 'Lower'
    fy=H-LT if top else 0
    my=H-2*LT-BG if top else LT+BG
    fixed=prism_xz(list(fixed_outline.exterior.coords)[:-1],fy,LT)
    for z in [-22,-10]:fixed=fixed.cut(cyl_y(PX,fy,z,1.8,LT))
    moving=box(PX-44,my,PZ-LW/2,44,LT,LW).fuse(cyl_y(PX,my,PZ,LW/2,LT))
    moving=moving.cut(cyl_y(PX,my,PZ,2.15,LT))
    for x in [PX-32,PX-18]:moving=moving.cut(cyl_y(x,my,PZ,1.8,LT))
    # Mortise open from the outside edge for access to the recessed moving leaf.
    access_y=my if top else 0
    access=box(PX-44-.15,access_y,PZ-LW/2-.15,44+.15,2*LT+BG,LW+.3).fuse(cyl_y(PX,access_y,PZ,LW/2+.15,2*LT+BG))
    clearance=prism_xz(sweep_pts,fy-.1 if top else 0,LT+.1)
    case_shapes=[s.cut(fixed) for s in case_shapes]
    frame=[s.cut(access).cut(clearance) for s in frame]
    add(label+' mortised fixed leaf',fixed,'knifeFixed',material='brass')
    add(label+' mortised door leaf',moving,'knifeDoor',material='brass')
    add(label+' pivot pin',cyl_y(PX,H-2*LT-BG if top else 0,PZ,2,2*LT+BG),'knifeFixed',material='brass')
for name,shape,grain in zip(['Case left','Case right','Case bottom','Case top','Back'],case_shapes,['y','y','x','x','y']):add(name,shape,grain=grain)
# Restore a conventional round knob. The specified 6-inch depth is case + door;
# the knob is separately dimensioned, as projecting cabinet hardware.
KX=R+SW/2;KY=(bottom(SW/2)+DH-bottom(DW-SW/2))/2
for name,shape,grain in zip(['Bottom rail','Top rail','Left stile','Right stile'],frame,['x','x','y','y']):add(name,shape,'door',grain)
add('Walnut panel',panel,'door','y','walnut')
stem=cq.Solid.makeCylinder(5,10,cq.Vector(KX,KY,G+ST),cq.Vector(0,0,1))
head=cq.Solid.makeCylinder(15.875,8,cq.Vector(KX,KY,G+ST+10),cq.Vector(0,0,1))
head=cq.Workplane(obj=head).edges().fillet(2).val()
add('Round knob',stem.fuse(head),'door',material='bronze')
# CAD and mesh exports derive from the same solids.
assembly=cq.Assembly(name='Cabinet_R2');meshes=[]
colors={'wood':cq.Color(.78,.65,.52),'walnut':cq.Color(.30,.16,.085),'brass':cq.Color(.67,.48,.22),'bronze':cq.Color(.28,.22,.15)}
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}model',unit='millimeter',attrib={'xml:lang':'en-US'});resources=ET.SubElement(root,'{'+ns+'}resources');build=ET.SubElement(root,'{'+ns+'}build')
for i,part in enumerate(parts,1):
    s=part['shape'];assembly.add(s,name=part['name'].replace(' ','_'),color=colors[part['material']])
    vertices,faces=s.tessellate(.045,.07);mesh=trimesh.Trimesh([[v.x,v.y,v.z] for v in vertices],faces,process=True);mesh.fix_normals()
    assert mesh.is_watertight and mesh.volume>0,part['name']
    bb=s.BoundingBox();meshes.append({k:v for k,v in part.items() if k!='shape'}|{'vertices':mesh.vertices.tolist(),'triangles':mesh.faces.tolist(),'bounds':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],'volume_mm3':s.Volume()})
    obj=ET.SubElement(resources,'{'+ns+'}object',id=str(i),type='model',name=part['name']);m=ET.SubElement(obj,'{'+ns+'}mesh');v=ET.SubElement(m,'{'+ns+'}vertices');f=ET.SubElement(m,'{'+ns+'}triangles')
    for xyz in mesh.vertices:ET.SubElement(v,'{'+ns+'}vertex',**dict(zip('xyz',map(lambda n:format(n,'.9f'),xyz))))
    for face in mesh.faces:ET.SubElement(f,'{'+ns+'}triangle',**{f'v{k+1}':str(n) for k,n in enumerate(face)})
    ET.SubElement(build,'{'+ns+'}item',objectid=str(i))
compound=cq.Compound.makeCompound([a['shape'].Solids()[0] for a in parts]);compound.exportStep(str(OUT/'cabinet-r2.step'),write_pcurves=False);cq.exporters.export(compound,str(OUT/'cabinet-r2.stl'),tolerance=.045,angularTolerance=.07)
# Z-up derived mesh for the library's standard preview camera.
cq.exporters.export(compound.rotate((0,0,0),(1,0,0),90),str(OUT/'cabinet-r2-preview.stl'),tolerance=.045,angularTolerance=.07)
with zipfile.ZipFile(OUT/'cabinet-r2.3mf','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
# Verify solid envelope, groove fit, dovetail mating and selected hinge swing samples.
body=cq.Compound.makeCompound([a['shape'] for a in parts if a['name']!='Round knob']);exact=Bnd_Box();BRepBndLib.AddOptimal_s(body.wrapped,exact,False,False);bb=cq.BoundBox(exact);assert abs(bb.xlen-W)<1e-5 and abs(bb.ylen-H)<1e-5 and abs(bb.zlen-p['overall_depth'])<1e-5,(bb.xlen,bb.ylen,bb.zlen)
for f in frame:assert f.intersect(panel).Volume()<1e-5
for c in case_shapes[:2]:
    for horizontal in case_shapes[2:4]:assert c.intersect(horizontal).Volume()<1e-5
fixed=cq.Compound.makeCompound([a['shape'] for a in parts if a['group'] in ['case','knifeFixed']]);moving=cq.Compound.makeCompound([a['shape'] for a in parts if a['group'] in ['door','knifeDoor']])
samples=[]
for angle in [0,15,30,45,60,75,90,100,110]:
    volume=moving.rotate((PX,0,PZ),(PX,1,PZ),angle).intersect(fixed).Volume();samples.append({'angle':angle,'overlap_mm3':volume});assert volume<1e-4,(angle,volume)
reimport=cq.importers.importStep(str(OUT/'cabinet-r2.step')).val();assert reimport.isValid() and len(reimport.Solids())==len(parts)
validation={'revision':'R2','units':'mm','case_and_door_size':[bb.xlen,bb.ylen,bb.zlen],'depth_including_knob':D+G+ST+18,'knob_projection_from_stile':18,'tail_boards':'vertical sides','pin_boards':'top and bottom','case_depth':D,'stile_shadow_line':T-ST,'groove_width':GW,'groove_depth':GD,'panel_thickness':p['panel_thickness'],'panel_edge_clearance':p['panel_edge_clearance'],'panel_engagement':GD-p['panel_edge_clearance'],'dovetails_per_corner':3,'total_tails':len(tails),'part_count':len(parts),'step_reimport_valid':True,'all_meshes_watertight':True,'panel_frame_overlap_mm3':0,'dovetail_overlap_mm3':0,'hinge_sweep_samples':samples,'hardware':'Custom mortised knives; sizing, screws, strength and bearing retention not manufacturer-validated','assumptions':p['provenance']['assumptions']}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
(OUT/'source/model-data.js').write_text('export const MODEL = '+json.dumps({'parameters':p,'derived':{'doorWidth':DW,'axisX':PX,'axisZ':PZ,'grooveZ':G+GZ,'ellipseA':A,'ellipseB':B,'ellipseCy':CY},'parts':meshes,'validation':validation},separators=(',',':'))+';\n')
print(json.dumps(validation,indent=2))
