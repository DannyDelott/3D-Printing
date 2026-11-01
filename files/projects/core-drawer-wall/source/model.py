"""R1. Millimetres. Cross sections drawn looking into the open core.
Run with the repository's CAD Python (manifold3d, numpy and trimesh).
Change ID/OD/L together for a different core. Generate a fresh fit print first.
"""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from manifold3d import CrossSection as CS, Manifold as M
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from xml.etree import ElementTree as ET

P=Path(__file__).resolve().parents[1]; OUT=P/'models'
ID,OD,L=83.,88.,60.
gap=2.4; pitch=OD+gap; half=pitch/2; R=ID/2-3.
sill=-29.5; top=14.
lip=1.6; seat=6.4; length=L+lip-1.
floor=2.; wall=1.6; flange=2.4
# Common jaw: 89.0 mm outer seat, 81.8 mm inner seat = 3.6 mm wall slot.
outside=OD/2+.5; inside=OD/2-3.1
def disk(r,x=0,y=0): return CS.circle(r,192).translate((x,y))
def box(x0,y0,x1,y1): return CS.square((x1-x0,y1-y0)).translate((x0,y0))
def rnd(x0,y0,x1,y1,r):
    return box(x0+r,y0+r,x1-r,y1-r).offset(r,circular_segments=64)
def extr(shape,start,end): return shape.extrude(end-start).translate((0,0,start))
def world(m): return m.transform([[1,0,0,0],[0,0,1,0],[0,1,0,0]])
# Edge shoes capture only a short arc of the rim at six o'clock.
# The starter foot and the upper-row glide share exactly the same guide.
def shoe(base):
    zone=box(-8,-OD,8,sill-.35)
    inner=(zone ^ disk(inside))-rnd(-5.3,-38,5.3,sill-2.1,.8)
    outer=(disk(outside+2.5)-disk(outside)) ^ zone
    cap=(disk(outside+2.5) ^ zone)
    m=extr(cap,-lip,0)+extr(inner+outer,0,seat)
    if base:
        # Low, wide feet bear at BOTH ends of every bottom core.
        y0=-OD/2-5.2
        cradle=rnd(-25,y0,25,y0+13,1.6)-disk(outside)
        m+=extr(cradle,-lip,seat+1.6)
    return m
foot=shoe(True); glide=shoe(False)
# Reversible two-rim fork. Mid-prong runs between the cores, two
# independent inner prongs catch the inner walls; cap stops on both rims.
zone=rnd(-5.85,-4.1,5.85,4.1,1)
left=disk(outside,-half);right=disk(outside,half)
fingers=(zone-left-right)+(zone ^ (disk(inside,-half)+disk(inside,half)))
clip=extr(zone,-lip,0)+extr(fingers,0,seat)
section=disk(R) ^ box(-half,sill,half,top)
cavity=disk(R-wall) ^ box(-half,sill+floor,half,half)
shell=section-cavity
face=(disk(ID/2+1.5) ^ box(-half,sill,half,top+1))-disk(11.5,0,top+4)
drawer=extr(face,-lip-flange,-lip)+extr(shell,-lip,L-1)+extr(section,L-1-wall,L-1)
sample=extr(shell,0,5)
core=extr(disk(OD/2)-disk(ID/2),0,L)
# Rear keeper lies on the plywood, above the top row. The strap passes
# through the two slots, around the web (recessed on its board side), and
# around both tube rims; no screw load is carried by glue on the rear edge.
def keeper():
    z=OD/2
    outline=rnd(-9,z-10,9,z+23,3)
    slots=rnd(-2.95,z-6.6,2.95,z-3.9,.8)+rnd(-2.95,z+2,2.95,z+4.7,.8)
    flat=outline-slots-disk(2.4,0,z+14)
    return extr(flat,0,4.8)-extr(rnd(-3.2,z-6.9,3.2,z+5.1,.6),3.2,4.9)
tab=keeper()
# Broad bearing area at the front fold of the tie.
guard_zone=box(-8,0,8,OD)
cap=(disk(outside+2.3)-disk(inside-1.5)) ^ guard_zone
jaws=((disk(outside+2.3)-disk(outside))+(disk(inside)-disk(inside-1.5))) ^ guard_zone
guard=extr(cap,-lip,0)+extr(jaws,0,6)

def mesh(m):
    raw=m.to_mesh()
    m=trimesh.Trimesh(raw.vert_properties[:,:3],raw.tri_verts,process=True)
    m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
    return m
def print_draw(m):return world(m).translate((0,0,-sill))
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
    with ZipFile(OUT/(name+'-r1.3mf'),'w') as z:
        for k,v in contents.items():z.writestr(ZipInfo(k),v,compress_type=ZIP_DEFLATED)
def main():
    OUT.mkdir(exist_ok=True); checks={}
    def orient(m):
        obj=mesh(m); obj.apply_translation([0,0,-obj.bounds[0,2]]);return obj
    def positioned(m,x,y):
        m=m.copy();m.apply_translation([x-m.bounds.mean(axis=0)[0],y-m.bounds.mean(axis=0)[1],0]);return m
    parts={'drawer':[('Drawer',mesh(print_draw(drawer)))],
           'foot':[('Base shoe',orient(foot))], 'glide':[('Upper glide',orient(glide))],
           'clip':[('Seam clip',orient(clip))],
           'anchor':[('Wall tab',positioned(orient(tab),0,0)),('Front guard',positioned(orient(guard),22,0))],
           'fit':[('Working glide',positioned(orient(glide),0,0)),('Drawer sample',positioned(orient(sample),0,40)),('Working seam clip',positioned(orient(clip),27,0))]}
    kit=[('Drawer',positioned(parts['drawer'][0][1],0,0))]
    for i,x in enumerate([-31,31]):
        kit.append((f'Base shoe {i+1}',positioned(orient(foot),x,52)))
        kit.append((f'Seam clip {i+1}',positioned(orient(clip),x,76)))
    kit.append(('Wall tab',positioned(orient(tab),-60,0)));kit.append(('Front guard',positioned(orient(guard),-60,27)))
    parts['starter']=kit
    for name,guide,n in [('bottom-hardware',foot,2),('upper-hardware',glide,6)]:
        hardware=[(f'Guide {i+1}',positioned(orient(guide),0,i*22)) for i in range(2)]
        hardware.extend((f'Seam clip {i+1}',positioned(orient(clip),38+(i%2)*16,(i//2)*14)) for i in range(n))
        hardware.extend(parts['anchor'][j][:1]+(positioned(parts['anchor'][j][1],-42,[-6,24][j]),) for j in range(2))
        parts[name]=hardware
    for name in ("bottom-hardware","upper-hardware"):
        parts[name+"-anchored"]=parts[name]; parts[name]=parts[name][:-2]
    for name,items in parts.items():
        # STL stores float32. Quantize AFTER placement and remove triangles
        # collapsed by the conversion, including on repeated clips.
        for index,(label,m) in enumerate(items):
            m=trimesh.Trimesh(np.round(m.vertices,4).astype('float32'),m.faces,process=True)
            m.update_faces(m.nondegenerate_faces());m.update_faces(m.unique_faces());m.remove_unreferenced_vertices()
            items[index]=(label,m)
        combined=trimesh.util.concatenate([m for _,m in items]);combined.export(OUT/(name+'-r1.stl'));write3(name,items)
        checks[name]={'print_bounds_mm':combined.extents.round(3).tolist(),'bodies':len(items)}
    def aft(m):return m.mirror((0,0,1)).translate((0,0,L))
    # Lower edge glides, every possible neighbor clip and the top strap
    # stay clear of drawer envelope along its ENTIRE straight extraction.
    sweep=extr(section,-length,L)
    seam_local=clip.translate((half,0,0))
    for label,solid in [('core',core),('foot',foot),('rear foot',aft(foot)),('glide',glide),('rear glide',aft(glide)),('guard',guard)]+[(f'seam {a}',seam_local.rotate((0,0,a))) for a in range(0,360,60)]:
        assert abs((sweep ^ solid).volume())<1e-6,label
        if label!='core':assert abs((core ^ solid).volume())<1e-6,label
    # Both feet stop on the cardboard edges. The drawer flange stops at the
    # front seam cap in a bank; on a standalone cell it stops on the tube.
    assert (face ^ (disk(OD/2)-disk(ID/2))).area()>1
    checks['nominal']={'core_ID_OD_length_mm':[ID,OD,L],'horizontal_pitch_mm':pitch,'staggered_row_rise_mm':round(pitch*3**.5/2,2),'clip_slot_mm':round(outside-inside,2),'shoe_axial_engagement_mm':seat,'drawer_top_above_center_mm':top,'drawer_body_length_mm':length,'cavity_ml':round((section ^ cavity).area()*(length-wall)/1000,1),'sweep_intersection_mm3':0}
    (P/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    # Three bottom tubes + two upper. Interstitial hardware occurs ONCE per seam.
    coords=[(0,0),(pitch,0),(2*pitch,0),(half,pitch*3**.5/2),(3*half,pitch*3**.5/2)]
    cells=[];groups=[]
    def add(m,x,z,kind):
        obj=mesh(world(m).translate((x,0,z)));cells.append(obj);groups.append([len(obj.faces),kind])
    # Illustration of the separate 4.8 mm cable tie (not a print file).
    # Section is in axial/radial coordinates; map its width to the X axis.
    z=OD/2; loop=rnd(-lip-1.2,z-6,L+lip+4.5,z+4.1,2.3)
    strap=extr(loop-loop.offset(-1.05),-2.4,2.4).transform([[0,0,1,0],[0,1,0,0],[1,0,0,0]])
    for i,(x,z) in enumerate(coords):
        for m,kind in [(core,2),(drawer.translate((0,0,-30 if i==4 else 0)),3),(foot if i<3 else glide,0),(aft(foot if i<3 else glide),0)]:
            add(m,x,z,kind)
        if i in (3,4):
            add(tab.translate((0,0,L+lip)),x,z,1);add(guard,x,z,0);add(strap,x,z,4)
    for i,(x,z) in enumerate(coords):
        for X,Z in coords[i+1:]:
            if abs(math.hypot(X-x,Z-z)-pitch)>1e-6:continue
            a=math.degrees(math.atan2(Z-z,X-x));join=clip.rotate((0,0,a))
            for m in [join,aft(join)]:add(m,(x+X)/2,(z+Z)/2,0)
    trimesh.util.concatenate(cells).export(OUT/'wall-example-r1.stl')
    (P/'preview-groups.json').write_text(json.dumps(groups)+'\n')
if __name__=='__main__':main()
