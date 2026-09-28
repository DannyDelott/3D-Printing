"""Prototype B: screw-operated collar + shoe-blocked rigid tote tab.

No flexible catches. The thread profile is identical to the physically successful
knob coupon. All other fits and retention loads need a new physical test.
Coordinates are millimeters; assembled shoe top is Z=0.
"""
from pathlib import Path
import json, math
import numpy as np
import trimesh
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
import generate_tote_grip as g
import grip_mounts as m

PREFIX='profile-jig-screw-lock'
COLORS=[[188,117,70,255],[84,116,102,255],[66,88,105,255],[202,163,76,255]]
COLLAR_RADIUS=14.5
COLLAR_BOTTOM=10.5
COLLAR_CLEARANCE=.30
SLOT_HALF=10.9
TAB_HALF=3.0
TAB_BOTTOM=1.75
TAB_CLEARANCE=.25


def fuse(a,b): return g.boolean(BRepAlgoAPI_Fuse,a,b,'prototype union')
def cut(a,b): return g.boolean(BRepAlgoAPI_Cut,a,b,'prototype clearance')
def common(a,b): return g.volume(BRepAlgoAPI_Common(a,b).Shape())
def cyl(radius,z,height,y): return g.shifted(m.cylinder(radius,z,height),y=y-m.KNOB_MOUNT_Y)
def side_down(shape):
    # Left face against bed: closed end of transverse tote socket builds first.
    tr=gp_Trsf(); tr.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,1,0)),-math.pi/2)
    return BRepBuilderAPI_Transform(shape,tr,True).Shape()


def parts(coupon=False):
    length,rail_length,plate_length,knob_y=(110,90,110,-30) if coupon else (250,170,186,-65)
    stations=(24,) if coupon else m.TOTE_MOUNT_YS
    base=g.block(-15.875,-length/2,-3,31.75,length,3) if coupon else g.profile_blank(length,g.SHOE_MINIMUM_THICKNESS)
    shoe=fuse(base,g.dovetail(rail_length))
    # This slot is open along Y: the tote tab passes through it as the shoe slides.
    # It stops lateral tote withdrawal once the shoe is installed.
    shoe=cut(shoe,g.block(-16,stations[0]-TAB_HALF-TAB_CLEARANCE,1.5,
                         16+TAB_HALF+TAB_CLEARANCE,length,4))
    # The stud belongs to the shoe, not the carrier. Smooth shank crosses the plate.
    shoe=fuse(shoe,cyl(9.4,-.1,13.6,knob_y))
    shoe=fuse(shoe,g.shifted(m.male_thread(g),y=knob_y-m.KNOB_MOUNT_Y))
    plate=m.rounded_bearing(g,20,-plate_length/2,plate_length/2,.2,13.3,True)
    start,end=-plate_length/2-1,rail_length/2+.25
    plate=cut(plate,g.shifted(g.dovetail(end-start,True),y=(start+end)/2))
    plate=cut(plate,g.block(-SLOT_HALF,start,-1,2*SLOT_HALF,knob_y-start,26))
    plate=cut(plate,cyl(SLOT_HALF,-1,26,knob_y))
    plate=cut(plate,cyl(COLLAR_RADIUS+COLLAR_CLEARANCE,10.3,5,knob_y))
    for station in stations:
        c=m.MOUNT_CLEARANCE
        pocket=m.prism_x([(station-8-c,9.5-c),(station+8+c,9.5-c),
                          (station+6+c,13.5),(station+6+c,16),
                          (station-6-c,16),(station-6-c,13.5)],-15.15,36.15)
        plate=cut(plate,pocket)
    tab_y=stations[0]
    plate=cut(plate,g.block(-15.25,tab_y-TAB_HALF-TAB_CLEARANCE,1.5,
                           37,2*(TAB_HALF+TAB_CLEARANCE),8.25))
    if coupon:
        tote=m.grip_foot(g,tab_y,False)
    else:
        tote=g.shifted(g.make_handle_blank(),y=g.TOTE_Y,z=15)
        tote=fuse(tote,m.rounded_bearing(g,15,-3,82,13.5,2,True))
        for station in stations: tote=fuse(tote,m.grip_foot(g,station,False))
    tote=fuse(tote,g.block(-15,tab_y-TAB_HALF,TAB_BOTTOM,18,2*TAB_HALF,9.7-TAB_BOTTOM))
    # Keep the tested thread unchanged; add a solid, unthreaded collar below it.
    blank=m.cylinder(16,13.5,14)
    if not coupon: blank=fuse(blank,g.shifted(g.make_knob(),z=11.5))
    knob=m.cut_female_thread(g,blank)
    collar=cut(m.cylinder(COLLAR_RADIUS,COLLAR_BOTTOM,3.2),m.cylinder(11.35,10.4,3.5))
    knob=fuse(knob,collar)
    knob=g.shifted(knob,y=knob_y-m.KNOB_MOUNT_Y)
    return dict(shoe=shoe,plate=plate,tote=tote,knob=knob),knob_y


def print_shape(name,shape):
    if name=='tote': return g.tote_print_orientation(shape)
    if name=='plate': return g.socket_print_orientation(shape)
    if name=='knob': return g.socket_print_orientation(shape)
    return shape


def export_piece(name,shape,stem):
    g.write_step(shape,g.MODELS/f'{stem}.step')
    path=g.MODELS/f'{stem}.stl'
    g.write_stl(print_shape(name,shape),path)
    mesh=trimesh.load_mesh(path,process=True)
    mesh.apply_translation(-mesh.bounds[0]); mesh.export(path)
    g.stl_to_3mf(path,path.with_suffix('.3mf'))
    print(g.verify_mesh(path),flush=True)
    return dict(dimensions_mm=mesh.extents.round(3).tolist(),watertight=bool(mesh.is_watertight))


def assembly(p,stem,offsets=None,layout=False):
    offsets=offsets or {}
    shapes=[(name.title(),g.shifted(shape,**offsets.get(name,{})),color)
            for (name,shape),color in zip(p.items(),COLORS)]
    if layout: shapes=[(name,print_shape(name.lower(),shape),color) for name,shape,color in shapes]
    g.export_assembly(shapes,stem,layout_on_plate=layout)


def validate(p,knob_y):
    report={}
    def clear(label,a,b):
        value=common(a,b); report[label]=round(value,6)
        assert value<.01,(label,value)
    def blocked(label,a,b):
        value=common(a,b); report[label]=round(value,6)
        assert value>1,(label,value)
    for i,(name,a) in enumerate(p.items()):
        solids=TopExp_Explorer(a,TopAbs_SOLID); n=0
        while solids.More(): n+=1; solids.Next()
        assert n==1,(name,n)
        for name2,b in list(p.items())[i+1:]: clear(f'assembled_{name}_{name2}_mm3',a,b)
    shoe,plate,tote,knob=[p[n] for n in ('shoe','plate','tote','knob')]
    # Real screw motion, rather than lifting a still-engaged thread straight up.
    for degrees in (90,180,270,360):
        tr=gp_Trsf(); tr.SetRotation(gp_Ax1(gp_Pnt(0,knob_y,0),gp_Dir(0,0,1)),math.radians(degrees))
        moved=g.shifted(BRepBuilderAPI_Transform(knob,tr,True).Shape(),z=degrees/360*m.THREAD_PITCH)
        clear(f'unscrew_{degrees}_thread_mm3',moved,shoe)
        clear(f'unscrew_{degrees}_plate_mm3',moved,plate)
    released=g.shifted(knob,z=4)
    # Withdrawal in -Y; knob remains threaded to shoe after one turn.
    for d in (0,1,4,10,25,50,100,200):
        movedshoe=g.shifted(shoe,y=-d); movedknob=g.shifted(released,y=-d)
        clear(f'shoe_slide_{d}_plate_mm3',movedshoe,plate)
        clear(f'shoe_slide_{d}_tote_mm3',movedshoe,tote)
        clear(f'knob_slide_{d}_plate_mm3',movedknob,plate)
        clear(f'knob_slide_{d}_tote_mm3',movedknob,tote)
    for d in (0,1,5,15,36): clear(f'tote_slide_{d}_plate_mm3',g.shifted(tote,x=d),plate)
    blocked('locked_shoe_withdrawal_2mm_mm3',g.shifted(knob,y=-2),plate)
    blocked('locked_tote_withdrawal_1mm_mm3',g.shifted(tote,x=1),shoe)
    blocked('tote_other_side_stop_1mm_mm3',g.shifted(tote,x=-1),plate)
    blocked('shoe_rear_stop_1mm_mm3',g.shifted(shoe,y=1),plate)
    blocked('shoe_lift_stop_1mm_mm3',g.shifted(shoe,z=-1),plate)
    return report


def main():
    report={'status':'Prototype: requires a new physical test. Previous snap catches failed retention.',
            'thread':'Same pitch, diameters and clearances as the physically successful knob coupon.',
            'geometry':{},'meshes':{}}
    for coupon in (True,False):
        label='coupon' if coupon else 'full'; stem=f'{PREFIX}-{label}'
        print('Building '+label,flush=True)
        p,y=parts(coupon)
        report['geometry'][label]=validate(p,y)
        for name,shape in p.items(): report['meshes'][f'{label}-{name}']=export_piece(name,shape,f'{stem}-{name}')
        assembly(p,f'{stem}-preview')
        assembly(p,f'{stem}-exploded-preview',{'shoe':dict(z=-25),'tote':dict(x=43,z=24),'knob':dict(z=35)})
        assembly(p,f'{stem}-unlocked-preview',{'shoe':dict(y=-25),'knob':dict(y=-25,z=4)})
        # Section through X=0 reveals the collar pocket, thread and solid tote tab.
        section={name:cut(shape,g.block(0,-300,-30,50,600,200)) for name,shape in p.items()}
        assembly(section,f'{stem}-section-preview')
        if coupon: assembly(p,f'{stem}-print-plate',layout=True)
        (g.PROJECT/'validation-screw-lock.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': main()
