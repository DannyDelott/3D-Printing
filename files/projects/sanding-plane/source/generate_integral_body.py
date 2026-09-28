"""Revision C: integral tote/carrier, interchangeable shoe and threaded knob.

Removes the tote mount entirely. Preserves revision B's knob/collar interface.
Uses the supplied vikingth0r Stanley No. 5 tote STL; keeps its curved face and silhouette.
Assembly coordinates in mm; exports select print orientation separately.
"""
import json, math, hashlib, sys
import numpy as np
import manifold3d
import trimesh
import cadquery as cq
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
import generate_screw_lock as b
from generate_screw_lock import g,m,fuse,cut,cyl,common

PREFIX='profile-jig-integral'
COLORS={'shoe':[188,117,70,255],'body':[66,88,105,255],'knob':[202,163,76,255]}
SLIDE_EXTERNAL_RADIUS=.30
SLIDE_INTERNAL_RADIUS=.20


def round_slide(shape, socket=False):
    """Round the rail/socket edges before the stud and entry slot interrupt them.

    Match the cabinet templates' external/internal radii, preserving the straight
    mating planes and square stop. This is shared by the full part and coupon.
    """
    solid=cq.Shape.cast(shape)
    operation=BRepFilletAPI_MakeFillet(shape)
    limit=g.RAIL_CAP_WIDTH/2+(g.RAIL_SIDE_CLEARANCE if socket else 0)
    height=g.RAIL_HEIGHT+(g.RAIL_TOP_CLEARANCE if socket else 0)
    edges=[]
    for edge in solid.Edges():
        box=edge.BoundingBox()
        if (box.xmin < -limit-.001 or box.xmax > limit+.001 or
                box.zmin < -.001 or box.zmax > height+.001):continue
        assert edge.geomType()=='LINE'
        faces=[f for f in solid.Faces() if any(e.isSame(edge) for e in f.Edges())]
        assert len(faces)==2 and all(f.geomType()=='PLANE' for f in faces)
        internal=faces[0].normalAt().dot(faces[1].Center()-edge.Center())>.0001
        radius=SLIDE_INTERNAL_RADIUS if internal else SLIDE_EXTERNAL_RADIUS
        operation.Add(radius,edge.wrapped)
        edges.append(dict(radius_mm=radius,type='internal' if internal else 'external',
                          midpoint_mm=edge.Center().toTuple(),length_mm=edge.Length()))
    assert len(edges)==(17 if socket else 12),edges
    assert sum(e['type']=='internal' for e in edges)==(9 if socket else 4)
    operation.Build()
    assert operation.IsDone(),'Sliding dovetail fillet failed'
    result=cq.Shape.cast(operation.Shape())
    assert result.isValid() and len(result.Solids())==1
    return result.wrapped,edges


def parts(coupon=False, edge_report=None):
    length,rail_length,plate_length,knob_y=(70,50,70,-10) if coupon else (250,170,186,-65)
    base=g.block(-15.875,-length/2,-3,31.75,length,3) if coupon else g.profile_blank(length,g.SHOE_MINIMUM_THICKNESS)
    shoe=fuse(base,g.dovetail(rail_length))
    shoe,shoe_edges=round_slide(shoe)
    shoe=fuse(shoe,cyl(9.4,-.1,13.6,knob_y))
    shoe=fuse(shoe,g.shifted(m.male_thread(g),y=knob_y-m.KNOB_MOUNT_Y))
    body=m.rounded_bearing(g,20,-plate_length/2,plate_length/2,.2,13.3,True)
    start,end=-plate_length/2-1,rail_length/2+.25
    body=cut(body,g.shifted(g.dovetail(end-start,True),y=(start+end)/2))
    body,body_edges=round_slide(body,True)
    if edge_report is not None:edge_report.update(shoe=shoe_edges,body=body_edges)
    body=cut(body,g.block(-b.SLOT_HALF,start,-1,2*b.SLOT_HALF,knob_y-start,26))
    body=cut(body,cyl(b.SLOT_HALF,-1,26,knob_y))
    body=cut(body,cyl(b.COLLAR_RADIUS+b.COLLAR_CLEARANCE,10.3,5,knob_y))
    # The coupon carrier is large enough to hold directly; omit any dummy grip.
    blank=m.cylinder(16,13.5,14)
    if not coupon: blank=fuse(blank,g.shifted(g.make_knob(),z=11.5))
    knob=m.cut_female_thread(g,blank)
    collar=cut(m.cylinder(b.COLLAR_RADIUS,b.COLLAR_BOTTOM,3.2),m.cylinder(11.35,10.4,3.5))
    knob=g.shifted(fuse(knob,collar),y=knob_y-m.KNOB_MOUNT_Y)
    return dict(shoe=shoe,body=body,knob=knob),knob_y


def cad_mesh(shape):
    path=g.MODELS/'.integral-temp.stl';g.write_stl(shape,path)
    mesh=trimesh.load_mesh(path,process=True);path.unlink();return mesh


def fill_screw_recess(mesh):
    """Close the source STL's blind counterbore to match its curved top.

    Fit the original top's extruded curve from its surrounding surface vertices.
    Trim a plug to that curve so no raised cylinder or flat cap remains.
    """
    centers=np.array([np.average(mesh.triangles_center[f],axis=0,weights=mesh.area_faces[f]) for f in mesh.facets])
    floor=int(np.argmin(np.linalg.norm(centers-[90.71283,88.27761,11.90693],axis=1)))
    top=int(np.argmin(np.linalg.norm(centers-[96.07079,90.89991,11.90703],axis=1)))
    assert abs(mesh.facets_area[floor]-103.884)<.05
    assert abs(mesh.facets_area[top]-361.479)<.05
    center=centers[floor];axis=mesh.facets_normal[floor]
    surface=np.unique(mesh.triangles[mesh.facets[top]].reshape(-1,3),axis=0)
    coefficients=np.polynomial.polynomial.polyfit(surface[:,0]-93,surface[:,1],5)
    residual=float(np.max(np.abs(np.polynomial.polynomial.polyval(surface[:,0]-93,coefficients)-surface[:,1])))
    assert residual<.002,residual
    transform=trimesh.geometry.align_vectors([0,0,1],axis)
    transform[:3,3]=center+axis*5.875
    plug=trimesh.creation.cylinder(radius=7,height=12.25,sections=128,transform=transform)
    xs=np.linspace(107,84,185)
    contour=[[84,75],[107,75]]+[[float(x),float(np.polynomial.polynomial.polyval(x-93,coefficients))] for x in xs]
    solid=manifold3d.CrossSection([np.array(contour)]).extrude(35).translate([0,0,-5])
    raw=solid.to_mesh()
    below_top=trimesh.Trimesh(np.array(raw.vert_properties)[:,:3],np.array(raw.tri_verts),process=True)
    plug=trimesh.boolean.intersection([plug,below_top],engine='manifold')
    filled=trimesh.boolean.union([mesh,plug],engine='manifold')
    added=filled.volume-mesh.volume
    removed=trimesh.boolean.difference([mesh,filled],engine='manifold').volume
    assert 300<added<1000 and abs(removed)<.01,(added,removed)
    assert filled.is_watertight and len(filled.split())==1
    return filled,dict(filled_volume_mm3=float(added),original_material_removed_mm3=float(removed),
                       top_surface_fit_max_error_mm=residual,finish='Follows the original top curvature; no raised plug.')


def imported_body(core):
    source=g.PROJECT/'source/reference-tote/stanley-no5-narrow-original.stl'
    tote=trimesh.load_mesh(source,process=True)
    tote.apply_translation(-tote.bounds[0])
    width=float(tote.extents[2])
    tote,recess_report=fill_screw_recess(tote)
    # Keep the supplied grip contours; only the obsolete screw recess is filled.
    # Any bed gap is filled by
    # removable slicer support, never by a permanent extension of the tote.
    # Original source X runs heel to toe. Source Y is height, source Z width.
    transform=np.array([[0,0,1,-width/2],[-1,0,0,85],[0,1,0,8],[0,0,0,1]],dtype=float)
    tote.apply_transform(transform)
    coremesh=cad_mesh(core)
    overlap=trimesh.boolean.intersection([tote,coremesh],engine='manifold').volume
    assert overlap>1000,overlap
    result=trimesh.boolean.union([tote,coremesh],engine='manifold')
    assert result.is_watertight and len(result.split())==1
    return result,dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        source_width_mm=width,flat_back_extension_mm=0,screw_recess=recess_report,
        tote_core_overlap_mm3=float(overlap),scale=1,
        source='vikingth0r / MakerWorld 2873652, supplied by Danny')


def shifted(shape,**kwargs):
    if isinstance(shape,trimesh.Trimesh):
        result=shape.copy();result.apply_translation([kwargs.get(k,0) for k in ('x','y','z')]);return result
    return g.shifted(shape,**kwargs)


def print_shape(name,shape,coupon=False):
    if isinstance(shape,trimesh.Trimesh):
        mesh=shape.copy()
        angle=-math.pi/2 if name=='body' else math.pi if name=='knob' else 0
        axis=[0,1,0] if name=='body' else [1,0,0]
        mesh.apply_transform(trimesh.transformations.rotation_matrix(angle,axis));return mesh
    if name=='body': return g.socket_print_orientation(shape) if coupon else g.tote_print_orientation(shape)
    if name=='knob': return g.socket_print_orientation(shape)
    return shape


def export_piece(name,shape,stem,coupon=False):
    if not isinstance(shape,trimesh.Trimesh):g.write_step(shape,g.MODELS/f'{stem}.step')
    path=g.MODELS/f'{stem}.stl';oriented=print_shape(name,shape,coupon)
    if isinstance(oriented,trimesh.Trimesh):mesh=oriented
    else:g.write_stl(oriented,path);mesh=trimesh.load_mesh(path,process=True)
    mesh.apply_translation(-mesh.bounds[0]);mesh.export(path)
    g.stl_to_3mf(path,path.with_suffix('.3mf'))
    print(g.verify_mesh(path),flush=True)
    return dict(dimensions_mm=mesh.extents.round(3).tolist(),watertight=bool(mesh.is_watertight))


def assembly(p,stem,offsets=None,layout=False,coupon=False):
    offsets=offsets or {}
    shapes=[(name.title(),shifted(shape,**offsets.get(name,{})),COLORS[name]) for name,shape in p.items()]
    if layout: shapes=[(name,print_shape(name.lower(),shape,coupon),color) for name,shape,color in shapes]
    g.export_assembly(shapes,stem,layout_on_plate=layout)


def validate(p,y):
    report={}
    def clear(label,a,c):
        v=common(a,c);report[label]=round(v,6);assert v<.01,(label,v)
    def blocked(label,a,c):
        v=common(a,c);report[label]=round(v,6);assert v>1,(label,v)
    for i,(name,a) in enumerate(p.items()):
        it=TopExp_Explorer(a,TopAbs_SOLID);n=0
        while it.More(): n+=1;it.Next()
        assert n==1,(name,n)
        report[name+'_solids']=n
        for name2,c in list(p.items())[i+1:]:clear(name+'_'+name2+'_intersection_mm3',a,c)
    shoe,body,knob=[p[n] for n in ('shoe','body','knob')]
    for degrees in (90,180,270,360):
        tr=gp_Trsf();tr.SetRotation(gp_Ax1(gp_Pnt(0,y,0),gp_Dir(0,0,1)),math.radians(degrees))
        moved=g.shifted(BRepBuilderAPI_Transform(knob,tr,True).Shape(),z=degrees/360*m.THREAD_PITCH)
        clear(f'unscrew_{degrees}_shoe_mm3',moved,shoe)
        clear(f'unscrew_{degrees}_body_mm3',moved,body)
    for d in (0,1,4,10,25,50,100,200):
        clear(f'shoe_withdraw_{d}_mm3',g.shifted(shoe,y=-d),body)
        clear(f'knob_withdraw_{d}_mm3',g.shifted(knob,y=-d,z=4),body)
    blocked('locked_withdrawal_2mm',g.shifted(knob,y=-2),body)
    blocked('rear_stop_1mm',g.shifted(shoe,y=1),body)
    blocked('lift_stop_1mm',g.shifted(shoe,z=-1),body)
    blocked('left_stop_1mm',g.shifted(shoe,x=-1),body)
    blocked('right_stop_1mm',g.shifted(shoe,x=1),body)
    return report


def main():
    report={'status':'Three-part assembly with supplied Stanley tote. Physical strength, retention and comfort remain untested.','geometry':{},'meshes':{}}
    if '--full-only' in sys.argv or '--coupon-only' in sys.argv:
        report=json.loads((g.PROJECT/'validation-integral.json').read_text())
    variants=(True,) if '--coupon-only' in sys.argv else (False,) if '--full-only' in sys.argv else (True,False)
    for coupon in variants:
        label='coupon' if coupon else 'full';stem=f'{PREFIX}-{label}'
        print('Building '+label,flush=True);edges={};p,y=parts(coupon,edges)
        report['geometry'][label]=validate(p,y)
        report.setdefault('sliding_dovetail',{})[label]=dict(
            external_radius_mm=SLIDE_EXTERNAL_RADIUS,internal_radius_mm=SLIDE_INTERNAL_RADIUS,
            side_clearance_mm=g.RAIL_SIDE_CLEARANCE,top_clearance_mm=g.RAIL_TOP_CLEARANCE,
            end_clearance_mm=.25,stop='Square bearing face with rounded perimeter',edges=edges)
        if not coupon:
            g.write_step(p['body'],g.MODELS/f'{stem}-carrier-core.step')
            p['body'],report['imported_tote']=imported_body(p['body'])
            shoe_mesh,knob_mesh=cad_mesh(p['shoe']),cad_mesh(p['knob'])
            report['integrated_mesh_collisions_mm3']={}
            for d in (0,25,200):
                for name,mesh in (('shoe',shoe_mesh),('knob',knob_mesh)):
                    moved=shifted(mesh,y=-d,z=4 if name=='knob' and d else 0)
                    overlap=trimesh.boolean.intersection([p['body'],moved],engine='manifold').volume
                    report['integrated_mesh_collisions_mm3'][f'{name}_{d}']=float(overlap)
                    assert overlap<.1,(name,d,overlap)
        for name,shape in p.items():report['meshes'][f'{label}-{name}']=export_piece(name,shape,f'{stem}-{name}',coupon)
        assembly(p,f'{stem}-preview')
        assembly(p,f'{stem}-exploded-preview',{'shoe':dict(z=-25),'knob':dict(z=35)})
        assembly(p,f'{stem}-unlocked-preview',{'shoe':dict(y=-25),'knob':dict(y=-25,z=4)})
        cutter=g.block(0,-300,-30,50,600,200)
        section={name:trimesh.boolean.difference([shape,cad_mesh(cutter)],engine='manifold')
                 if isinstance(shape,trimesh.Trimesh) else cut(shape,cutter) for name,shape in p.items()}
        assembly(section,f'{stem}-section-preview')
        if coupon: assembly(p,f'{stem}-print-plate',layout=True,coupon=True)
        (g.PROJECT/'validation-integral.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
