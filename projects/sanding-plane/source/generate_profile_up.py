"""Profile-up sander: carrier female thread and coupon-proven tapered seat.
Assembly Z points toward the handles. Shoes print inverted on their full-length
rail cap. One interface builds the 70 mm coupon and full 186 mm shoe.
"""
import json, math, sys
import cadquery as cq
import trimesh
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone
from OCP.gp import gp_Trsf,gp_Ax1,gp_Ax2,gp_Pnt,gp_Dir
import generate_integral_body as c
from generate_integral_body import g,m,fuse,cut,cyl,common
PREFIX='profile-jig-profile-up'
PIN_RADIUS=4.0
POCKET_RADIUS=4.15
POCKET_FLOOR=2.0
THREAD_SHIFT=-5.2
PRELOAD_TRAVEL=.40
RELEASE_LIFT=4.0
PROFILE_THICKNESS=9.0
FULL_LENGTH=186.0
TAPER_FLOOR_RADIUS=1.0
TAPER_TIP_GAP=.6
TAPER_TOP=5.0


def screw_move(shape,y,degrees):
    tr=gp_Trsf();tr.SetRotation(gp_Ax1(gp_Pnt(0,y,0),gp_Dir(0,0,1)),math.radians(degrees))
    return g.shifted(BRepBuilderAPI_Transform(shape,tr,True).Shape(),z=degrees/360*m.THREAD_PITCH)


def round_interface(shape,socket=False):
    """R0.30 outer / R0.20 inner edges on the continuous sliding interface."""
    s=cq.Shape.cast(shape);op=BRepFilletAPI_MakeFillet(shape);selected=[]
    xmax=12.25 if socket else 12;zmax=5.3 if socket else 5
    for e in s.Edges():
        b=e.BoundingBox()
        if b.xmin < -xmax-.001 or b.xmax>xmax+.001 or b.zmin<-.001 or b.zmax>zmax+.001:continue
        if b.ylen<1 or b.xlen>.001 or b.zlen>.001:continue
        fs=[f for f in s.Faces() if any(a.isSame(e) for a in f.Edges())]
        if e.geomType()!='LINE' or len(fs)!=2 or any(f.geomType()!='PLANE' for f in fs):continue
        internal=fs[0].normalAt().dot(fs[1].Center()-e.Center())>.0001
        r=.2 if internal else .3;op.Add(r,e.wrapped)
        selected.append(dict(radius_mm=r,midpoint_mm=e.Center().toTuple()))
    assert len(selected)>=4,selected
    op.Build();assert op.IsDone(),'Interface fillet failed'
    out=cq.Shape.cast(op.Shape());assert out.isValid() and len(out.Solids())==1
    return out.wrapped,selected


def parts(coupon=False, tapered=False, profile_blank=None):
    length,plate_length,y=(70,70,-10) if coupon else (FULL_LENGTH,FULL_LENGTH,-65)
    # The shoulder expands 1 mm horizontally per 1 mm of print height.
    base=(profile_blank or g.profile_blank)(length,PROFILE_THICKNESS)
    envelope=g.xz_prism([(-16,-30),(16,-30),(16,-7),(9,0),(-9,0),(-16,-7)],length+2)
    base=g.boolean(g.BRepAlgoAPI_Common,base,envelope,'slope profile shoe shoulders')
    shoe,rail_edges=round_interface(fuse(base,g.dovetail(length)))
    if tapered:
        # Matching 45-degree flanks locate under axial screw load. The blunt
        # tip stays above the pocket floor so it cannot bypass the conical seat.
        pocket=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,y,POCKET_FLOOR),gp_Dir(0,0,1)),
            TAPER_FLOOR_RADIUS,PIN_RADIUS,TAPER_TOP-POCKET_FLOOR).Shape()
        shoe=cut(shoe,fuse(pocket,cyl(PIN_RADIUS,TAPER_TOP-.01,1.01,y)))
    else:
        shoe=cut(shoe,cyl(POCKET_RADIUS,POCKET_FLOOR,4,y))
    body=m.rounded_bearing(g,20,-plate_length/2,plate_length/2,.2,16.8 if coupon else 13.3,True)
    body=cut(body,g.dovetail(plate_length+2,True))
    body,socket_edges=round_interface(body,True)
    body=fuse(body,cyl(15.5,13.3,3.7,y))
    native=g.shifted(body,y=m.KNOB_MOUNT_Y-y,z=-THREAD_SHIFT)
    body=g.shifted(m.cut_female_thread(g,native),y=y-m.KNOB_MOUNT_Y,z=THREAD_SHIFT)
    body=cut(body,cyl(4.6,4.8,3,y))
    lead=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,y,15.5),gp_Dir(0,0,1)),9.7,11.3,1.6).Shape()
    body=cut(body,lead)
    knob=g.shifted(m.male_thread(g),y=y-m.KNOB_MOUNT_Y,z=THREAD_SHIFT)
    if tapered:
        tip_z=POCKET_FLOOR+TAPER_TIP_GAP
        tip=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,y,tip_z),gp_Dir(0,0,1)),
            TAPER_FLOOR_RADIUS+TAPER_TIP_GAP,PIN_RADIUS,TAPER_TOP-tip_z).Shape()
        knob=fuse(knob,fuse(tip,cyl(PIN_RADIUS,TAPER_TOP,3.3,y)))
    else:
        knob=fuse(knob,cyl(PIN_RADIUS,POCKET_FLOOR,6.3,y))
    if coupon:head=cyl(16,18.1,6,y)
    else:
        # Flat crown gives the reusable knob a broad print base.
        head=g.shifted(g.make_knob(),y=y-g.KNOB_Y,z=10.1)
        head=cut(head,g.block(-30,y-30,58.1,60,60,30))
    knob=fuse(knob,head)
    shoe=g.shifted(shoe,z=-PRELOAD_TRAVEL)
    knob=screw_move(knob,y,-360*PRELOAD_TRAVEL/m.THREAD_PITCH)
    return dict(shoe=shoe,body=body,knob=knob),y,dict(rail=rail_edges,socket=socket_edges)


def validate(p,y):
    report={}
    def clear(label,a,b):
        v=common(a,b);report[label]=round(v,6);assert v<.01,(label,v)
    def blocked(label,a,b):
        v=common(a,b);report[label]=round(v,6);assert v>.05,(label,v)
    for name,s in p.items():
        solid=cq.Shape.cast(s);assert solid.isValid() and len(solid.Solids())==1,name
    shoe,body,knob=[p[n] for n in ('shoe','body','knob')]
    clear('shoe_body',shoe,body);clear('shoe_knob',shoe,knob);clear('knob_body',knob,body)
    for degrees in (90,180,270,360):
        moved=screw_move(knob,y,degrees)
        clear(f'unscrew_{degrees}_body',moved,body);clear(f'unscrew_{degrees}_shoe',moved,shoe)
    released=screw_move(knob,y,360)
    for d in (0,1,4,10,25,70,200,300):
        moved=g.shifted(shoe,y=-d)
        clear(f'withdraw_{d}_body',moved,body);clear(f'withdraw_{d}_knob',moved,released)
    blocked('locked_forward_1mm',g.shifted(shoe,y=-1),knob)
    blocked('locked_backward_1mm',g.shifted(shoe,y=1),knob)
    blocked('rail_vertical_stop',g.shifted(shoe,z=-.2),body)
    blocked('rail_left_stop',g.shifted(shoe,x=-1),body)
    blocked('rail_right_stop',g.shifted(shoe,x=1),body)
    return report


def orientation(name,shape,coupon):
    if name=='body' and not coupon:return c.print_shape(name,shape)
    return g.socket_print_orientation(shape)


def validate_taper(p,y):
    checks={}
    for delta in (-.1,.1):
        volume=common(g.shifted(p['shoe'],y=delta),p['knob'])
        assert volume>.01,(delta,volume)
        checks[f'seat_blocks_slide_{delta}_mm']=volume
    tip_z=cq.Shape.cast(p['knob']).BoundingBox().zmin
    gap=tip_z-(POCKET_FLOOR-PRELOAD_TRAVEL)
    assert abs(gap-TAPER_TIP_GAP)<.001,gap
    checks['seated_tip_floor_gap_mm']=round(gap,3)
    checks['extra_quarter_mm_screw_travel_body']=common(screw_move(p['knob'],y,-22.5),p['body'])
    assert checks['extra_quarter_mm_screw_travel_body']<.01
    return checks


def export(p,stem,coupon,print_parts=None):
    meshes={}
    for name,shape in p.items():
        if not isinstance(shape,trimesh.Trimesh):g.write_step(shape,g.MODELS/f'{stem}-{name}.step')
        rotated=orientation(name,shape,coupon)
        mesh=rotated if isinstance(rotated,trimesh.Trimesh) else c.cad_mesh(rotated)
        mesh.apply_translation(-mesh.bounds[0]);assert mesh.is_watertight and len(mesh.split())==1
        meshes[name]=mesh
        mesh.export(g.MODELS/f'{stem}-{name}.stl')
        (g.MODELS/f'{stem}-{name}.3mf').write_bytes(mesh.export(file_type='3mf'))
        print(name,mesh.extents.round(3),flush=True)
    c.assembly(p,stem+'-preview')
    c.assembly(p,stem+'-exploded-preview',{'shoe':dict(z=-25),'knob':dict(z=30)})
    c.assembly(p,stem+'-unlocked-preview',{'shoe':dict(y=-25),'knob':dict(z=RELEASE_LIFT)})
    cutter=g.block(0,-300,-35,60,600,200)
    section={name:trimesh.boolean.difference([shape,c.cad_mesh(cutter)],engine='manifold')
             if isinstance(shape,trimesh.Trimesh) else cut(shape,cutter) for name,shape in p.items()}
    c.assembly(section,stem+'-section-preview')
    if coupon:g.export_assembly([(name.title(),mesh,c.COLORS[name]) for name,mesh in meshes.items()
        if print_parts is None or name in print_parts],stem+'-print-plate',layout_on_plate=True)
    return {name:dict(dimensions_mm=mesh.extents.round(3).tolist(),watertight=bool(mesh.is_watertight)) for name,mesh in meshes.items()}


def main():
    report={'status':'Tapered coupon physically tested with no shifting reported. The full sander now uses that same tapered seat; full-size loading and long-term wear are untested.',
            'interface':dict(type='Matching conical seat on full sander',included_angle_degrees=90,
                seat_mouth_diameter_mm=2*PIN_RADIUS,pocket_floor_diameter_mm=2*TAPER_FLOOR_RADIUS,
                blunt_tip_diameter_mm=2*(TAPER_FLOOR_RADIUS+TAPER_TIP_GAP),
                seated_tip_floor_gap_mm=TAPER_TIP_GAP,pocket_depth_mm=3,
                pitch_mm=4,nominal_thread_diameter_mm=21.2,preload_travel_mm=.4,
                release_lift_mm=4,profile_minimum_blank_thickness_mm=9,
                shoulder_slope_degrees=45,rail_length='Full shoe length',
                thread_location='Carrier female, knob male; shoe unthreaded',
                retention='Conical seat blocks both longitudinal directions; no separate rear wall stop'),
            'full_length_mm':FULL_LENGTH,
            'straight_coupon_interface':dict(pin_diameter_mm=8,pocket_diameter_mm=8.3,status='Historical: slipped when tightened'),
            'geometry':{},'meshes':{}}
    if '--coupon-only' in sys.argv or '--full-only' in sys.argv:
        previous=json.loads((g.PROJECT/'validation-profile-up.json').read_text())
        previous.update({k:v for k,v in report.items() if k not in ('geometry','meshes')})
        report=previous
    kinds=(True,) if '--coupon-only' in sys.argv else (False,) if '--full-only' in sys.argv else (True,False)
    for coupon in kinds:
        label='coupon' if coupon else 'full';stem=f'{PREFIX}-{label}'
        print('Building '+label,flush=True);p,y,edges=parts(coupon,tapered=not coupon)
        report['geometry'][label]=validate(p,y);report.setdefault('rounded_edges',{})[label]=edges
        if not coupon:
            report['geometry'][label].update(validate_taper(p,y))
            g.write_step(p['body'],g.MODELS/f'{stem}-carrier-core.step')
            p['body'],report['imported_tote']=c.imported_body(p['body'])
        report['meshes'][label]=export(p,stem,coupon)
        (g.PROJECT/'validation-profile-up.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
