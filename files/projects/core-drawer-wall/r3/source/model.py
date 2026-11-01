"""R3, mm. Original shared junctions for a staggered cardboard-core wall."""
import math,json,sys
from pathlib import Path
import numpy as np
import trimesh
from manifold3d import CrossSection as CS
from zipfile import ZipFile,ZIP_DEFLATED,ZipInfo
from xml.etree import ElementTree as ET
P=Path(__file__).resolve().parents[1];OUT=P/'models'
ID,OD,L=83.,88.,60.; pitch=90.4; half=pitch/2; rise=pitch*math.sqrt(3)/2
R=39.3; floor=-35.5;top=31.;lip=1.4; jaw=4.4; ri=OD/2-3.1; ro=OD/2+.5
def circle(r,x=0,y=0):return CS.circle(r,192).translate((x,y))
def box(x,y,X,Y):return CS.square((X-x,Y-y)).translate((x,y))
def rnd(x,y,X,Y,r):return box(x+r,y+r,X-r,Y-r).offset(r,circular_segments=48)
def poly(points):
 p=np.array(points);area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
 return CS([p if area>0 else p[::-1]])
def extr(s,a,b):return s.extrude(b-a).translate((0,0,a))
def world(m):return m.transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
def rear(m):return m.mirror((0,0,1)).translate((0,0,L))
def mesh(m):
 raw=m.to_mesh();return clean(trimesh.Trimesh(raw.vert_properties[:,:3],raw.tri_verts))
def clean(m):
 m=trimesh.Trimesh(np.round(m.vertices,4).astype('float32'),m.faces,process=True)
 m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices();return m
def halfplane(nx,ny,dist):
 tx,ty=-ny,nx
 return poly([(nx*d+tx*t,ny*d+ty*t) for d,t in [(-160,-160),(dist,-160),(dist,160),(-160,160)]])
def notch(s,dist):
 for sign in [-1,1]:s=s ^ halfplane(sign/2**.5,-1/2**.5,dist)
 return s
# Flat bed, 45-degree lower bearings, and a pair of 45-degree upper
# shoulders. The latter open the mouth without curling unsupported over it.
upper=(top+math.sqrt(R*R-top*top)-.3)/math.sqrt(2)
wall=1.35;thick=1.8
def trimmed(rad,level,diag,up):
 s=notch(circle(rad)^box(-50,level,50,top),diag)
 for sign in [-1,1]:s=s ^ halfplane(sign/2**.5,1/2**.5,up)
 return s
def cavity_at(level):
 return trimmed(R-wall,level+thick,36.5-wall,upper-wall)
def tray(level):
 sec=trimmed(R,level,36.5,upper); inner=cavity_at(level)
 face=notch(circle(ID/2+1.5)^box(-50,level,50,top),38.6)
 d=extr(face,-lip-2.4,-lip)+extr(sec-inner,-lip,L-1)+extr(sec,L-1-wall,L-1)
 # External pinch ledge: no finger notch through the storage wall. The
 # underside grows at 45 degrees from the front. The ends taper in plan.
 vw=poly([(top-9,-lip-2.4),(top-9,-lip-2.3),(top-2,-lip-2.3),
          (top-2,-lip-8.0),(top-3.4,-lip-8.0)])
 pull=extr(vw,-16,16).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
 taper=rnd(-16,-lip-8,16,-lip-1.5,2)
 pull=pull ^ extr(taper,top-10,top).transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
 return d+pull
section=trimmed(R,floor,36.5,upper);cavity=cavity_at(floor)
drawer=tray(floor);dropin=tray(-29.5)
core=extr(circle(OD/2)-circle(ID/2),0,L)
centers=[(-half,0),(half,0),(0,rise)]
def profile(base):
 if base:return poly([(-half,0),(half,0),(half/2+2,-31),(12,-44.8),(-12,-44.8),(-half/2-2,-31)])
 return poly([(-half,0),(half,0),(0,rise)])
def guide():
 # Axial rise under the drawer: the face retains its circular edge and
 # the two small ledges build upward at 45 degrees in print orientation.
 y=rise
 vw=poly([(y-40.6,-.2),(y-39.6,-.2),(y+floor-.35,4.2),(y+floor-.35,9.2),(y+floor-3.5,9.2),(y-40.6,4)])
 def rib(x):
  return extr(vw,x,x+3.8).transform([[0,0,1,0],[1,0,0,0],[0,1,0,0]])
 return rib(-7.8)+rib(4)
def junction(base,mode='plain',edge=0):
    zone=profile(base);cs=centers[:2] if base else centers
    apert=CS();seats=CS();inner=CS();outer=CS()
    for i,(x,y) in enumerate(cs):
        hole=circle(40.,x,y)
        if base:
            # Matching local 45-degree ledge. The front skin stays circular.
            relieved=(circle(40.) ^ halfplane((1 if i==0 else -1)/2**.5,-1/2**.5,36.85)).translate((x,y))
        else:relieved=hole
        apert+=(relieved if base else hole); seats+=circle(ro,x,y);inner+=circle(ri,x,y)-relieved;outer+=circle(ro+1.45,x,y)
    skin=zone-apert
    # Core contact and stiffness come from thin ribs behind the face.
    ribs=zone ^ ((outer-seats)+inner)
    m=extr(skin,-lip,0)+extr(ribs,0,jaw)
    if base:
        # Flat sole and internal V ribs; hollow between these ribs.
        m+=extr(zone ^ box(-35,-44.8,35,-42.6),0,6)
        for sign in [-1,1]:
            bar=CS.square((2.0,25),center=True).rotate(sign*27).translate((sign*7,-34.))
            m+=extr((zone-seats)^bar,0,jaw)
    else:m+=guide()
    cy=-31 if base else rise/3
    if mode!='plain':
        # Front and rear tie slots are in the triangle of air BETWEEN tubes.
        # The tie crosses behind the rear plate BELOW its screw hole.
        slots=CS()
        for x in [-4.3,4.3]:slots+=rnd(x-.95,cy-5.5,x+.95,cy-2.3,.48)
        if mode=='rear':
            pad=rnd(-7.5,cy-6.4,7.5,cy+7.5,2.4)
            m+=extr(pad-seats,0,2.8)
            m-=extr(circle(2.4,0,cy+2.8),-lip-1,20)
            # Counterbore through nearby jaw ribs so a pan head seats flat.
            m-=extr(circle(4.85,0,cy+2.8),2.8,22)
            m-=extr(rnd(-5.4,cy-5.7,5.4,cy-2.1,.55),-lip-.1,-lip+1.2)
        m-=extr(slots,-lip-1,20)
    if edge:m=m ^ extr(box(-100 if edge<0 else 0,-100,0 if edge<0 else 100,100),-lip-1,18)
    return m
def write3(name,parts):
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    root=ET.Element('model',unit='millimeter',xmlns=ns); res=ET.SubElement(root,'resources'); build=ET.SubElement(root,'build')
    for i,(label,m) in enumerate(parts,1):
        assert m.is_watertight and m.is_volume and len(m.split())==1,(label,m.is_watertight)
        obj=ET.SubElement(res,'object',id=str(i),name=label,type='model'); data=ET.SubElement(obj,'mesh'); vs=ET.SubElement(data,'vertices');fs=ET.SubElement(data,'triangles')
        for v in m.vertices: ET.SubElement(vs,'vertex',**dict(zip('xyz',(f'{a:.7f}' for a in v))))
        for f in m.faces: ET.SubElement(fs,'triangle',**{f'v{j+1}':str(a) for j,a in enumerate(f)})
        ET.SubElement(build,'item',objectid=str(i))
    contents={'[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>','_rels/.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>','3D/3dmodel.model':ET.tostring(root)}
    with ZipFile(OUT/(name+'-r3.3mf'),'w') as z:
        for k,v in contents.items():z.writestr(ZipInfo(k),v,compress_type=ZIP_DEFLATED)
def cable(baseflag):
    cy=-31 if baseflag else rise/3
    p=rnd(-lip-1.1,-4.95,L+lip-.08,4.95,1.4)
    return extr(p-p.offset(-.9),cy-5.2,cy-2.7).transform([[0,1,0,0],[0,0,1,0],[1,0,0,0]])
def plate(parts):
    # Bed-facing skin down, jaws up. Greedy shelf packing on a P1S-sized bed.
    placed=[];x=y=row=0.
    for label,m in parts:
        m=mesh(m);w,d,_=m.extents
        if x and x+w>220:x=0;y+=row+5;row=0
        m.apply_translation([x-m.bounds[0,0],y-m.bounds[0,1],-m.bounds[0,2]])
        placed.append((label,clean(m)));x+=w+5;row=max(row,d)
    return placed
def main():
    OUT.mkdir(exist_ok=True);base=junction(True);Y=junction(False);edgeL=junction(True,edge=-1);edgeR=junction(True,edge=1)
    D=world(drawer);sample=extr(section-cavity,0,5)
    # Curve ends are the slots; the carrier's tip must be captured both front and back.
    sets={'base':[('Shared base - front',base),('Shared base - rear',base)],
        'upper':[('Three-way junction - front',Y),('Three-way junction - rear',Y)],
        'ends':[('Left edge',edgeR),('Right edge',edgeL)]*2,
        'base-mount':[('Base tie face',junction(True,'front')),('Base screw face',junction(True,'rear'))],
        'upper-mount':[('Three-way tie face',junction(False,'front')),('Three-way screw face',junction(False,'rear'))],
        'drawer':[('Deep drawer',D)],'drop-in':[('R2 compatible drawer',world(dropin))],'fit':[('Drawer section',sample),('Short base jaw',base ^ extr(box(-18,-29,18,-9),-lip,5))],
        'starter':[('Drawer',D),('Left edge - front',edgeR),('Left edge - rear',edgeR),('Right edge - front',edgeL),('Right edge - rear',edgeL)]}
    checks={}
    for name,parts in sets.items():
        items=plate(parts);combined=trimesh.util.concatenate([m for _,m in items]);combined.export(OUT/(name+'-r3.stl'));write3(name,items)
        checks[name]={'bounds':combined.extents.round(2).tolist(),'bodies':len(items)}
    sweep=extr(section,-L-12,L)
    for baseflag in [True,False]:
        for mode in ['plain','front','rear']:
            f=junction(baseflag,mode)
            for x,y in (centers[:2] if baseflag else centers):
                for hardware in [f,rear(f)]:
                    for moving in [sweep,core]:
                        assert abs((hardware ^ moving.translate((x,y,0))).volume())<1e-5,(baseflag,mode,x,y)
    for baseflag in [True,False]:
        cy=-31 if baseflag else rise/3
        axis=(0,cy+2.8)
        head=extr(circle(4.6,*axis),2.801,26)
        shank=extr(circle(2.35,*axis),-20,26)
        anchor=junction(baseflag,'rear')
        assert abs((head ^ anchor).volume())<1e-6 and abs((shank ^ anchor).volume())<1e-6
        strap=cable(baseflag)
        assert all(abs((strap ^ m).volume())<1e-6 for m in [junction(baseflag,'front'),rear(anchor)])
        for x,y in (centers[:2] if baseflag else centers):
            assert abs((strap ^ core.translate((x,y,0))).volume())<1e-6
            assert abs((head ^ core.translate((x,y,0))).volume())<1e-6
    checks['nominal']={'core_ID_OD_L':[ID,OD,L],'pitch':pitch,'rise':round(rise,2),'socket':round(ro-ri,2),'cavity_ml':round(cavity.area()*(L+lip-1-wall)/1000,1),'dropin_ml':round(cavity_at(-29.5).area()*(L+lip-1-wall)/1000,1),'headspace_5mm_ml':round((cavity^box(-50,-50,50,top-5)).area()*(L+lip-1-wall)/1000,1),'mouth_width_mm':round(float(np.ptp(np.vstack(cavity.to_polygons())[np.isclose(np.vstack(cavity.to_polygons())[:,1],top),0])),1),'gross_core_ml':round(math.pi*(ID/2)**2*L/1000,1),'drawer_rim_above_center':top,'sweep_intersection_mm3':0}
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    cells=[];groups=[]
    def add(m,x,y,k):
        obj=mesh(world(m.translate((x,y,0))));cells.append(obj);groups.append([len(obj.faces),k])
    for i,(x,y) in enumerate([(-pitch,0),(0,0),(pitch,0),(-half,rise),(half,rise)]):
        add(core,x,y,2);add(drawer.translate((0,0,-29 if i==4 else 0)),x,y,3)
    for seam,f in [(-pitch-half,edgeR),(-half,base),(half,base),(pitch+half,edgeL)]:
        add(f,seam,0,0);add(rear(f),seam,0,0)
    for x in [-half,half]:
        add(junction(False,'front'),x,0,0);add(rear(junction(False,'rear')),x,0,1)
        # Non-printing reference hardware: strap around both connector webs.
        add(cable(False),x,0,4)
    trimesh.util.concatenate(cells).export(OUT/'wall-example-r3.stl');(P/'preview-groups.json').write_text(json.dumps(groups)+'\n')
if __name__=='__main__':main()
