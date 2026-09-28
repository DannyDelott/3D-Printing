"""Reusable grip mounts: transverse dovetail tenons with integral release arms.

The grip mounts are independent of the replaceable plate's shoe latch.
All fit and flexure dimensions remain provisional until printed.
"""
import math
from functools import lru_cache
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Pnt, gp_Vec, gp_Pnt2d, gp_Dir2d, gp_Ax3, gp_Ax2, gp_Dir
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone

PLATE_TOP = 13.5
GRIP_SOLE = PLATE_TOP
TOTE_SOLE_START = -3.0
TOTE_SOLE_END = 82.0
TOTE_BED_START = -5.0
TOTE_BED_END = 84.0
KNOB_MOUNT_Y = -65.0
TOTE_MOUNT_YS = (24.0, 66.0)
MOUNT_CLEARANCE = .15
MOUNT_RELEASE = .95
# Leaves a printable receiver lip beside the arm slot from its first layer.
TENON_CAP_HALF_WIDTH = 8.0


def prism_x(points, x0, length):
    wire = BRepBuilderAPI_MakePolygon()
    for y,z in points: wire.Add(gp_Pnt(x0,y,z))
    wire.Close()
    return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(length,0,0)).Shape()


def tenon(g, station):
    return prism_x([(station-TENON_CAP_HALF_WIDTH,9.5),(station+TENON_CAP_HALF_WIDTH,9.5),
        (station+6,13.5),(station+6,14.25),
        (station-6,14.25),(station-6,13.5)],-15,27)


def release_arm(g, station):
    # Bends toward the tenon (-Y); slides in along +X. Root at the entry end.
    outline=[
        ('line',((-15,station+5.5),(-11,station+5.5))),
        ('line',((-11,station+5.5),(-11,station+8.5))),
        ('bezier',((-11,station+8.5),(-11,station+9.3),(-10.4,station+9.8),(-9.5,station+9.8))),
        ('line',((-9.5,station+9.8),(12,station+9.8))),
        ('line',((12,station+9.8),(12,station+11.2))),
        ('line',((12,station+11.2),(-15,station+11.2))),
        ('line',((-15,station+11.2),(-15,station+5.5))),
    ]
    result=g.xy_prism(outline,10,3.5)
    points=[(9,station+11),(9,station+12.2),(10,station+12.2),(12,station+11.2),(12,station+11)]
    tooth=g.xy_prism([('line',(points[i],points[(i+1)%len(points)])) for i in range(len(points))],10,3.5)
    result = g.boolean(BRepAlgoAPI_Fuse,result,tooth,'joining ramped grip retention tooth')
    # Two 0.6 mm end ribs rise at 45 degrees in the side-down orientation.
    # The square locking face bridges the 2.3 mm between them. Matching relief
    # grooves in the receiver let these ribs pass without camming the latch out.
    rib_points=[(7.6,station+11),(8.8,station+12.2),(10,station+12.2),
                (12,station+11.2),(12,station+11)]
    rib_outline=[('line',(rib_points[i],rib_points[(i+1)%len(rib_points)])) for i in range(len(rib_points))]
    for z in (10,12.9):
        result=g.boolean(BRepAlgoAPI_Fuse,result,g.xy_prism(rib_outline,z,.6),'joining catch bridge end rib')
    return result


def socket_cut(g, plate, station, latch):
    c=MOUNT_CLEARANCE
    cutter=prism_x([(station-TENON_CAP_HALF_WIDTH-c,9.5-c),(station+TENON_CAP_HALF_WIDTH+c,9.5-c),
        (station+6+c,13.5),(station+6+c,16),
        (station-6-c,16),(station-6-c,13.5)],-18,30.15)
    result=g.boolean(BRepAlgoAPI_Cut,plate,cutter,'cutting transverse grip mortise')
    if latch:
        # Through-top access keeps the integral release arm reachable.
        for opening in (
            g.block(-18,station+8.65,9.75,30.15,2.8,6.25),
            g.block(-18,station+5.5,9.75,8.75,5.95,6.25),
            g.block(8.85,station+11.45,9.75,3.3,1,6.25),
            prism_x([(station+11.45,9.75),(station+12.45,9.75),
                     (station+12.45,10.8),(station+11.45,11.8)],-18,30.15),
            g.block(-18,station+11.45,12.7,30.15,1,1.05),
        ):
            result=g.boolean(BRepAlgoAPI_Cut,result,opening,'clearing grip arm and catch pocket')
    return result


def grip_foot(g, station, latch):
    result=tenon(g,station)
    # A bearing pad carries downward pressure directly to the plate.
    pad=g.block(-15,station-12,GRIP_SOLE,30,24,2)
    result=g.boolean(BRepAlgoAPI_Fuse,result,pad,'joining grip bearing pad')
    if latch:
        result=g.boolean(BRepAlgoAPI_Fuse,result,release_arm(g,station),'joining captive grip retention latch')
    return result


def rounded_bearing(g, half_width, start, end, bottom, height, bevel_corners=False):
    """Broad, flat bearing with rounded plan corners, not rounded contact faces."""
    w, r = half_width, 2.0
    k = .55228475*r
    outline = [
        ('line', ((-w+r,start),(w-r,start))),
        ('bezier', ((w-r,start),(w-r+k,start),(w,start+r-k),(w,start+r))),
        ('line', ((w,start+r),(w,end-r))),
        ('bezier', ((w,end-r),(w,end-r+k),(w-r+k,end),(w-r,end))),
        ('line', ((w-r,end),(-w+r,end))),
        ('bezier', ((-w+r,end),(-w+r-k,end),(-w,end-r+k),(-w,end-r))),
        ('line', ((-w,end-r),(-w,start+r))),
        ('bezier', ((-w,start+r),(-w,start+r-k),(-w+r-k,start),(-w+r,start))),
    ]
    if bevel_corners:
        outline=[('line',(points[0],points[-1])) if kind=='bezier' else (kind,points)
                 for kind,points in outline]
    return g.xy_prism(outline,bottom,height)


def clear_above_arm(g, grip, station):
    # Leave the arm clear of both the pedestal and the grip above it.
    return g.boolean(BRepAlgoAPI_Cut,grip,
        g.block(-10.75,station+8.75,13.5,27,7,6),
        'opening finger access above grip release arm')


THREAD_PITCH = 4.0
THREAD_MAJOR_DIAMETER = 21.2
THREAD_RADIAL_CLEARANCE = .30
THREAD_AXIAL_CLEARANCE = .20
THREAD_TOP = PLATE_TOP + 10


def cylinder(radius, z, height):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,KNOB_MOUNT_Y,z),gp_Dir(0,0,1)),radius,height).Shape()


@lru_cache(maxsize=2)
def thread_ridge(g, female=False):
    radial = THREAD_RADIAL_CLEARANCE if female else 0
    axial = THREAD_AXIAL_CLEARANCE if female else 0
    start_z = PLATE_TOP-2
    # Explicit ruled sections preserve radial/axial profiles through every
    # turn and avoid sweep-frame/tolerance failures during thread booleans.
    loft = BRepOffsetAPI_ThruSections(True, True, 1e-6)
    loft.CheckCompatibility(False)
    sections_per_turn = 48
    for index in range(4*sections_per_turn+1):
        angle = 2*math.pi*index/sections_per_turn
        center_z = start_z+THREAD_PITCH*index/sections_per_turn
        polygon = BRepBuilderAPI_MakePolygon()
        for radius,z in [(9.2+radial,center_z-1.7-axial),(10.6+radial,center_z-.3-axial),
                         (10.6+radial,center_z+.3+axial),(9.2+radial,center_z+1.7+axial)]:
            polygon.Add(gp_Pnt(radius*math.cos(angle),KNOB_MOUNT_Y+radius*math.sin(angle),z))
        polygon.Close()
        loft.AddWire(polygon.Wire())
    loft.Build()
    if not loft.IsDone(): raise RuntimeError('Could not build printed knob thread')
    return loft.Shape()


@lru_cache(maxsize=1)
def male_thread(g):
    core = cylinder(9.4,PLATE_TOP-.2,10.2)
    ridge = g.boolean(BRepAlgoAPI_Common,thread_ridge(g),cylinder(11,PLATE_TOP,9),'trimming male thread runout')
    return g.boolean(BRepAlgoAPI_Fuse,core,ridge,'joining printed knob stud')


def cut_female_thread(g, blank):
    bore = cylinder(9.7,PLATE_TOP-1,12.75)
    ridge = g.boolean(BRepAlgoAPI_Common,thread_ridge(g,True),cylinder(11.2,PLATE_TOP-1,12.75),'trimming female thread')
    # Cut separately: fusing the trimmed helical cutter to a coplanar bore
    # can drop its outside faces in OpenCascade despite a valid final solid.
    result = g.boolean(BRepAlgoAPI_Cut,blank,bore,'cutting knob bore')
    result = g.boolean(BRepAlgoAPI_Cut,result,ridge,'cutting actual helical female groove')
    # A lead-in at the open end helps start the coarse thread squarely.
    lead = BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,KNOB_MOUNT_Y,PLATE_TOP-.1),gp_Dir(0,0,1)),11.3,9.7,1.6).Shape()
    return g.boolean(BRepAlgoAPI_Cut,result,lead,'cutting thread lead-in')


def thread_coupon(g):
    male = g.boolean(BRepAlgoAPI_Fuse,cylinder(16,PLATE_TOP-3,3.0),male_thread(g),'joining thread test base')
    female = cut_female_thread(g,cylinder(16,PLATE_TOP,14))
    return male,female


def make_parts(g):
    plate=g.carrier_base(g.CARRIER_LENGTH,g.LATCH_Y,g.RAIL_LENGTH)
    bed=rounded_bearing(g,17,TOTE_BED_START,TOTE_BED_END,
        g.CARRIER_TOP-.2,PLATE_TOP-g.CARRIER_TOP+.2)
    clearance=g.block(12.7,g.LATCH_Y-8,-1,12,g.LATCH_RELIEF_END+8,16)
    bed=g.boolean(BRepAlgoAPI_Cut,bed,clearance,'preserving shoe flexure beside tote support bed')
    plate=g.boolean(BRepAlgoAPI_Fuse,plate,bed,'joining continuous tote support bed')
    for station in TOTE_MOUNT_YS:
        plate=socket_cut(g,plate,station,station==TOTE_MOUNT_YS[0])
    knob_seat=cylinder(16,g.CARRIER_TOP-.2,PLATE_TOP-g.CARRIER_TOP+.2)
    plate=g.boolean(BRepAlgoAPI_Fuse,plate,knob_seat,'joining knob seating shoulder')
    plate=g.boolean(BRepAlgoAPI_Fuse,plate,male_thread(g),'joining male knob thread to latch plate')
    knob=g.shifted(g.make_knob(),z=PLATE_TOP+6-8)
    knob=g.boolean(BRepAlgoAPI_Fuse,knob,cylinder(16,PLATE_TOP,14),'joining threaded knob pedestal')
    knob=cut_female_thread(g,knob)
    tote=g.shifted(g.make_handle_blank(),y=g.TOTE_Y,z=GRIP_SOLE+1.5)
    sole=rounded_bearing(g,15,TOTE_SOLE_START,TOTE_SOLE_END,GRIP_SOLE,2,bevel_corners=True)
    tote=g.boolean(BRepAlgoAPI_Fuse,tote,sole,'joining continuous load-spreading tote sole')
    for station in TOTE_MOUNT_YS:
        tote=g.boolean(BRepAlgoAPI_Fuse,tote,grip_foot(g,station,station==TOTE_MOUNT_YS[0]),'joining reusable tote feet')
    tote=clear_above_arm(g,tote,TOTE_MOUNT_YS[0])
    return plate,tote,knob


def tote_coupon(g):
    station=TOTE_MOUNT_YS[0]
    socket=socket_cut(g,g.block(-17,station-15,5.3,34,30,PLATE_TOP-5.3),station,True)
    foot=clear_above_arm(g,grip_foot(g,station,True),station)
    return socket,foot
