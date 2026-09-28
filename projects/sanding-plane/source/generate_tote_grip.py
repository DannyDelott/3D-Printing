#!/usr/bin/env python3
"""Generate a modular two-hand sander, reusable grips, and integral latches.

The open rear tote slides into keyed mounts; the front knob screws onto the latch plate.
A dovetail secures the replaceable shoe against lift; an integral flexure
latch and a rear stop restrain longitudinal movement. Printed fit and load capacity need physical tests.
"""

from __future__ import annotations

import math
import sys
import grip_mounts
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_Transform,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.Geom import Geom_BezierCurve
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.StlAPI import StlAPI_Writer
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

from profile_interface import (
    ATTACHMENT_WIDTH, SHOE_MINIMUM_THICKNESS, RAIL_LENGTH, RAIL_HEIGHT,
    RAIL_ROOT_WIDTH, RAIL_CAP_WIDTH, RAIL_SIDE_CLEARANCE, RAIL_TOP_CLEARANCE,
    CARRIER_WIDTH, CARRIER_LENGTH, CARRIER_BOTTOM, CARRIER_TOP,
    LATCH_Y, LATCH_BEAM_INNER_X, LATCH_BEAM_THICKNESS,
    LATCH_ROOT_START, LATCH_ROOT_END, LATCH_RELIEF_END,
    LATCH_TOOTH_INNER_X, LATCH_TOOTH_BOTTOM, LATCH_TOOTH_TOP, LATCH_PAD_OUTER_X,
    LATCH_RELEASE_TRAVEL, LATCH_GUARD_INNER_X, LATCH_NOTCH_CLEARANCE,
    RAIL_END_CLEARANCE, COUPON_LENGTH, COUPON_RAIL_LENGTH, COUPON_LATCH_Y,
)
from generate_caul import make_caul

PROJECT = Path(__file__).resolve().parents[1]
MODELS = PROJECT / "models"
IMAGES = PROJECT / "images"
HANDLE_X_MIN = -15.0
HANDLE_X_MAX = 15.0
HANDLE_WIDTH = HANDLE_X_MAX - HANDLE_X_MIN
HANDLE_EDGE_RADIUS = 3.5
SHOE_LENGTH = 250.0
TOTE_Y = 44.0
KNOB_Y = -65.0

Point2 = tuple[float, float]
Segment = tuple[str, tuple[Point2, ...]]

# One open S-shaped outline: projecting toe, curved grip, and upper horn.
# There is no inner wire or connecting front strut.
OUTER_SEGMENTS: list[Segment] = [
    ("line", ((-46.0, 0.0), (36.0, 0.0))),
    ("bezier", ((36.0, 0.0), (43.0, 3.0), (43.0, 15.0), (38.0, 28.0))),
    ("bezier", ((38.0, 28.0), (35.0, 40.0), (27.0, 53.0), (15.0, 68.0))),
    ("bezier", ((15.0, 68.0), (10.0, 76.0), (14.0, 88.0), (26.0, 101.0))),
    ("bezier", ((26.0, 101.0), (9.0, 106.0), (-17.0, 101.0), (-32.0, 91.0))),
    ("bezier", ((-32.0, 91.0), (-44.0, 82.0), (-34.0, 66.0), (-17.0, 51.0))),
    ("bezier", ((-17.0, 51.0), (-4.0, 37.0), (9.0, 29.0), (8.0, 23.0))),
    ("bezier", ((8.0, 23.0), (8.0, 15.0), (-17.0, 13.0), (-34.0, 13.0))),
    ("bezier", ((-34.0, 13.0), (-44.0, 13.0), (-49.0, 8.0), (-46.0, 0.0))),
]


def edge_for_segment(segment: Segment, x: float):
    kind, points = segment
    if kind == "line":
        start, end = points
        return BRepBuilderAPI_MakeEdge(
            gp_Pnt(x, start[0], start[1]), gp_Pnt(x, end[0], end[1])
        ).Edge()
    poles = TColgp_Array1OfPnt(1, 4)
    for index, (y, z) in enumerate(points, start=1):
        poles.SetValue(index, gp_Pnt(x, y, z))
    return BRepBuilderAPI_MakeEdge(Geom_BezierCurve(poles)).Edge()


def wire_for_segments(segments: list[Segment], x: float):
    wire = BRepBuilderAPI_MakeWire()
    for segment in segments:
        wire.Add(edge_for_segment(segment, x))
    if not wire.IsDone():
        raise RuntimeError("Could not build tote outline wire")
    return wire.Wire()


def make_handle_blank() -> TopoDS_Shape:
    face_builder = BRepBuilderAPI_MakeFace(wire_for_segments(OUTER_SEGMENTS, HANDLE_X_MIN))
    face = face_builder.Face()
    handle = BRepPrimAPI_MakePrism(face, gp_Vec(HANDLE_WIDTH, 0.0, 0.0)).Shape()
    if not BRepCheck_Analyzer(handle).IsValid():
        raise RuntimeError("Raw tote handle is invalid")
    return soften_handle_edges(handle)


def soften_handle_edges(handle: TopoDS_Shape) -> TopoDS_Shape:
    """Keep the bed-facing side flat; round the upward-facing perimeter."""
    fillet = BRepFilletAPI_MakeFillet(handle)
    explorer = TopExp_Explorer(handle, TopAbs_EDGE)
    selected = 0
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        box = Bnd_Box()
        BRepBndLib.Add_s(edge, box)
        xmin, _, _, xmax, _, _ = box.Get()
        if xmax - xmin < 0.01 and abs(xmax-HANDLE_X_MAX) < .01:
            fillet.Add(HANDLE_EDGE_RADIUS, edge)
            selected += 1
        explorer.Next()
    fillet.Build()
    if selected == 0 or not fillet.IsDone():
        raise RuntimeError("Could not round tote grip edges")
    result = fillet.Shape()
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError("Rounded tote grip is invalid")
    return result


def boolean(operation, left: TopoDS_Shape, right: TopoDS_Shape, label: str) -> TopoDS_Shape:
    algo = operation(left, right)
    algo.SetFuzzyValue(1e-5)
    algo.Build()
    if not algo.IsDone():
        raise RuntimeError(f"Boolean failed: {label}")
    algo.SimplifyResult(True, True)
    result = algo.Shape()
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError(f"Invalid result after: {label}")
    return result


def shifted(shape: TopoDS_Shape, x=0.0, y=0.0, z=0.0) -> TopoDS_Shape:
    transform = gp_Trsf()
    transform.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, transform, True).Shape()


def xz_prism(points: list[tuple[float, float]], length: float) -> TopoDS_Shape:
    polygon = BRepBuilderAPI_MakePolygon()
    for x, z in points:
        polygon.Add(gp_Pnt(x, -length / 2, z))
    polygon.Close()
    return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(polygon.Wire()).Face(), gp_Vec(0, length, 0)).Shape()


def dovetail(length: float, socket: bool = False) -> TopoDS_Shape:
    side = RAIL_SIDE_CLEARANCE if socket else 0.0
    root, cap = RAIL_ROOT_WIDTH / 2 + side, RAIL_CAP_WIDTH / 2 + side
    if socket:
        # Extend below the carrier and above the rail to make an open socket.
        points = [(-root, -1), (root, -1), (root, 0), (cap, RAIL_HEIGHT),
                  (cap, RAIL_HEIGHT + RAIL_TOP_CLEARANCE),
                  (-cap, RAIL_HEIGHT + RAIL_TOP_CLEARANCE), (-cap, RAIL_HEIGHT), (-root, 0)]
    else:
        points = [(-root, -0.1), (root, -0.1), (root, 0),
                  (cap, RAIL_HEIGHT), (-cap, RAIL_HEIGHT), (-root, 0)]
    return xz_prism(points, length)


def block(x, y, z, width, length, height) -> TopoDS_Shape:
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), width, length, height).Shape()


def xy_prism(segments, z, height) -> TopoDS_Shape:
    wire = BRepBuilderAPI_MakeWire()
    for kind, points in segments:
        if kind == "line":
            start, end = points
            edge = BRepBuilderAPI_MakeEdge(gp_Pnt(*start, z), gp_Pnt(*end, z)).Edge()
        else:
            poles = TColgp_Array1OfPnt(1, 4)
            for index, (x, y) in enumerate(points, 1):
                poles.SetValue(index, gp_Pnt(x, y, z))
            edge = BRepBuilderAPI_MakeEdge(Geom_BezierCurve(poles)).Edge()
        wire.Add(edge)
    return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(), gp_Vec(0, 0, height)).Shape()


def tooth(station: float) -> TopoDS_Shape:
    # Negative Y is the insertion side: its ramp cams the arm outward.
    # The square positive-Y face prevents withdrawal after the tooth seats.
    points = [(12.5, station-5), (14.5, station-5), (14.5, station+2.5),
              (LATCH_TOOTH_INNER_X, station+2.5), (LATCH_TOOTH_INNER_X, station)]
    segments = [("line", (points[i], points[(i+1)%len(points)])) for i in range(len(points))]
    blank = xy_prism(segments, LATCH_TOOTH_BOTTOM, CARRIER_TOP-LATCH_TOOTH_BOTTOM)
    # With the socket channel facing up on the bed, this 45-degree upper
    # surface becomes the tooth's self-supporting underside.
    ramp = shifted(xz_prism([
        (LATCH_TOOTH_INNER_X, LATCH_TOOTH_BOTTOM),
        (14.5, LATCH_TOOTH_BOTTOM), (14.5, CARRIER_TOP),
        (LATCH_BEAM_INNER_X, CARRIER_TOP),
        (LATCH_TOOTH_INNER_X, LATCH_TOOTH_TOP),
    ], 20), y=station)
    return boolean(BRepAlgoAPI_Common, blank, ramp, "sloping latch tooth for support-free coupon")


def notch_tool(station: float) -> TopoDS_Shape:
    clearance = LATCH_NOTCH_CLEARANCE
    return block(LATCH_TOOTH_INNER_X-clearance, station-5-clearance,
        LATCH_TOOTH_BOTTOM-clearance, 15,
        7.5+2*clearance, CARRIER_TOP-LATCH_TOOTH_BOTTOM+2*clearance)


def rail_notch(shape: TopoDS_Shape, station: float) -> TopoDS_Shape:
    return boolean(BRepAlgoAPI_Cut, shape, notch_tool(station), "cutting snap-latch notch")


def make_latch(station: float) -> TopoDS_Shape:
    inner, outer = LATCH_BEAM_INNER_X, LATCH_BEAM_INNER_X+LATCH_BEAM_THICKNESS
    # Smooth root flares spread the transition into the carrier. The long
    # thin section bends sideways; it is not a separate inserted spring.
    segments = [
        ("line", ((inner,station-3),(outer,station-3))),
        ("line", ((outer,station-3),(outer,station+LATCH_ROOT_START))),
        ("bezier", ((outer,station+LATCH_ROOT_START),(outer,station+LATCH_ROOT_START+4),(17,station+LATCH_ROOT_START+6),(17,station+LATCH_ROOT_END))),
        ("line", ((17,station+LATCH_ROOT_END),(12.7,station+LATCH_ROOT_END))),
        ("bezier", ((12.7,station+LATCH_ROOT_END),(12.7,station+LATCH_ROOT_START+6),(inner,station+LATCH_ROOT_START+4),(inner,station+LATCH_ROOT_START))),
        ("line", ((inner,station+LATCH_ROOT_START),(inner,station-3))),
    ]
    beam = xy_prism(segments, CARRIER_BOTTOM, CARRIER_TOP-CARRIER_BOTTOM)
    result = boolean(BRepAlgoAPI_Fuse, beam, tooth(station), "joining latch tooth to flexure")
    pad = block(13.8, station-3, CARRIER_BOTTOM,
        LATCH_PAD_OUTER_X-13.8, 6, CARRIER_TOP-CARRIER_BOTTOM)
    return boolean(BRepAlgoAPI_Fuse, result, pad, "joining integral outward-press thumb pad")


def carrier_base(length: float, station: float, rail_length: float) -> TopoDS_Shape:
    base = block(-CARRIER_WIDTH/2, -length/2, CARRIER_BOTTOM,
        CARRIER_WIDTH, length, CARRIER_TOP-CARRIER_BOTTOM)
    fillet = BRepFilletAPI_MakeFillet(base)
    edges = TopExp_Explorer(base, TopAbs_EDGE)
    while edges.More():
        edge = TopoDS.Edge_s(edges.Current())
        xmin, ymin, zmin, xmax, ymax, zmax = bounds(edge)
        if xmax-xmin < .01 and ymax-ymin < .01:
            fillet.Add(3.0, edge)
        edges.Next()
    fillet.Build()
    if not fillet.IsDone() or not BRepCheck_Analyzer(fillet.Shape()).IsValid():
        raise RuntimeError("Carrier corner rounding failed")
    start, end = -length/2-1, rail_length/2+RAIL_END_CLEARANCE
    socket = shifted(dovetail(end-start, True), y=(start+end)/2)
    result = boolean(BRepAlgoAPI_Cut, fillet.Shape(), socket, "cutting socket with rear insertion stop")
    relief = block(12.7, station-8, -1, 12, LATCH_RELIEF_END+8, 16)
    result = boolean(BRepAlgoAPI_Cut, result, relief, "opening flexure clearance")
    # Open all the way through this wall. A shallow pocket would leave a
    # horizontal shelf over the tooth opening when printed channel-up.
    clearance = LATCH_NOTCH_CLEARANCE
    access = block(LATCH_TOOTH_INNER_X-clearance, station-5-clearance,
        -1, 15, 7.5+2*clearance, CARRIER_TOP+2)
    result = boolean(BRepAlgoAPI_Cut, result, access, "opening latch-tooth access window")
    # The outside guard joins the carrier ahead of the arm and limits travel.
    guard = block(LATCH_GUARD_INNER_X, station-8, CARRIER_BOTTOM,
        2, 14, CARRIER_TOP-CARRIER_BOTTOM)
    tie = block(16, station-10, CARRIER_BOTTOM,
        LATCH_GUARD_INNER_X+2-16, 3, CARRIER_TOP-CARRIER_BOTTOM)
    result = boolean(BRepAlgoAPI_Fuse, result, tie, "joining latch guard bridge")
    result = boolean(BRepAlgoAPI_Fuse, result, guard, "joining overtravel stop")
    return boolean(BRepAlgoAPI_Fuse, result, make_latch(station), "joining integral thumb latch")


def make_knob() -> TopoDS_Shape:
    # A turned pear-shaped knob, modeled as one revolved Bezier section.
    outline = [
        ("line", ((0, 8), (13, 8))),
        ("bezier", ((13, 8), (14, 13), (8, 18), (10, 23))),
        ("bezier", ((10, 23), (12, 26), (21, 25), (22, 34))),
        ("bezier", ((22, 34), (25, 48), (13, 59), (0, 59))),
        ("line", ((0, 59), (0, 8))),
    ]
    wire = BRepBuilderAPI_MakeWire()
    for kind, points in outline:
        if kind == "line":
            (r1, z1), (r2, z2) = points
            edge = BRepBuilderAPI_MakeEdge(gp_Pnt(r1, KNOB_Y, z1), gp_Pnt(r2, KNOB_Y, z2)).Edge()
        else:
            poles = TColgp_Array1OfPnt(1, 4)
            for i, (r, z) in enumerate(points, 1):
                poles.SetValue(i, gp_Pnt(r, KNOB_Y, z))
            edge = BRepBuilderAPI_MakeEdge(Geom_BezierCurve(poles)).Edge()
        wire.Add(edge)
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    return BRepPrimAPI_MakeRevol(face, gp_Ax1(gp_Pnt(0, KNOB_Y, 0), gp_Dir(0, 0, 1)), math.tau).Shape()


def profile_blank(length: float, thickness: float) -> TopoDS_Shape:
    raw = make_caul(length, thickness)
    flip = gp_Trsf()
    flip.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), math.pi)
    return shifted(BRepBuilderAPI_Transform(raw, flip, True).Shape(), y=length / 2)


def make_shoe(length: float = SHOE_LENGTH) -> TopoDS_Shape:
    shoe = profile_blank(length, SHOE_MINIMUM_THICKNESS)
    joined = boolean(BRepAlgoAPI_Fuse, shoe, dovetail(RAIL_LENGTH), "joining shoe and dovetail rail")
    return rail_notch(joined, LATCH_Y)


def make_fit_coupon() -> tuple[TopoDS_Shape, TopoDS_Shape]:
    rail_base = block(-ATTACHMENT_WIDTH/2, -COUPON_LENGTH/2, -3,
        ATTACHMENT_WIDTH, COUPON_LENGTH, 3)
    rail = boolean(BRepAlgoAPI_Fuse, rail_base, dovetail(COUPON_RAIL_LENGTH), "joining coupon rail")
    return (rail_notch(rail, COUPON_LATCH_Y),
            carrier_base(COUPON_LENGTH, COUPON_LATCH_Y, COUPON_RAIL_LENGTH))


def bounds(shape: TopoDS_Shape) -> tuple[float, float, float, float, float, float]:
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    return box.Get()


def volume(shape: TopoDS_Shape) -> float:
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, properties)
    return properties.Mass()


def orient_upright(shape: TopoDS_Shape) -> TopoDS_Shape:
    xmin, ymin, zmin, _, _, _ = bounds(shape)
    translation = gp_Trsf()
    translation.SetTranslation(gp_Vec(-xmin, -ymin, -zmin))
    return BRepBuilderAPI_Transform(shape, translation, True).Shape()


def socket_print_orientation(shape: TopoDS_Shape) -> TopoDS_Shape:
    """Place the flat back on the bed with the dovetail channel facing up."""
    rotation = gp_Trsf()
    rotation.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), math.pi)
    return BRepBuilderAPI_Transform(shape, rotation, True).Shape()


def tote_print_orientation(shape: TopoDS_Shape) -> TopoDS_Shape:
    """Left broad side down: assembly +X becomes print +Z."""
    rotation = gp_Trsf()
    rotation.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), -math.pi/2)
    return BRepBuilderAPI_Transform(shape, rotation, True).Shape()


def write_step(shape: TopoDS_Shape, path: Path) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"Could not write {path}")


def write_stl(shape: TopoDS_Shape, path: Path) -> None:
    # OCP expects angular deflection in radians.  A sub-degree value explodes
    # smooth tote fillets into millions of triangles with no printable gain.
    BRepTools.Clean_s(shape)
    BRepMesh_IncrementalMesh(shape, 0.15, False, 0.18, True)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape, str(path)):
        raise RuntimeError(f"Could not write {path}")
    # A revolved pole can export a zero-area triangle with repeated vertices.
    # Remove only numerical degeneracy; topology verification still must pass.
    mesh = trimesh.load_mesh(path, force="mesh", process=True)
    mask = mesh.nondegenerate_faces(height=1e-10)
    if not mask.all():
        mesh.update_faces(mask)
        mesh.remove_unreferenced_vertices()
        mesh.export(path)


def stl_to_3mf(stl_path: Path, output_path: Path) -> None:
    mesh = trimesh.load_mesh(stl_path, force="mesh", process=True)
    output_path.write_bytes(mesh.export(file_type="3mf"))


def sample_segment(segment: Segment, count: int = 24) -> list[Point2]:
    kind, points = segment
    if kind == "line":
        return [points[0], points[-1]]
    p0, p1, p2, p3 = np.array(points, dtype=float)
    sampled: list[Point2] = []
    for t in np.linspace(0.0, 1.0, count):
        point = (
            (1.0 - t) ** 3 * p0
            + 3.0 * (1.0 - t) ** 2 * t * p1
            + 3.0 * (1.0 - t) * t**2 * p2
            + t**3 * p3
        )
        sampled.append((float(point[0]), float(point[1])))
    return sampled


def sample_outline(segments: list[Segment]) -> list[Point2]:
    result: list[Point2] = []
    for segment in segments:
        points = sample_segment(segment)
        result.extend(points if not result else points[1:])
    return result


def write_preview(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#f3efe7")
    ax.set_facecolor("#f3efe7")
    ax.add_patch(Rectangle((-125, -8.465), 250, 8.465, facecolor="#bc7546"))
    ax.add_patch(Rectangle((-CARRIER_LENGTH/2, CARRIER_BOTTOM), CARRIER_LENGTH,
        CARRIER_TOP-CARRIER_BOTTOM, facecolor="#547466"))
    points = [(y+TOTE_Y, z+CARRIER_TOP-.5) for y,z in sample_outline(OUTER_SEGMENTS)]
    ax.add_patch(MplPolygon(points, closed=True, facecolor="#547466"))
    ax.add_patch(plt.Circle((KNOB_Y, 39), 21, color="#547466"))
    ax.add_patch(Rectangle((KNOB_Y-11, 8),22,23,facecolor="#547466"))
    ax.annotate("Front knob", xy=(KNOB_Y,59), xytext=(-115,84), arrowprops={"arrowstyle":"->"})
    ax.annotate("Open rear tote", xy=(TOTE_Y,84), xytext=(75,110), arrowprops={"arrowstyle":"->"})
    ax.plot([LATCH_Y-3,LATCH_Y+3],[6,6],color="#bfa051",lw=7)
    ax.annotate("Press thumb paddle outward to release",xy=(LATCH_Y,6),xytext=(-115,-25),arrowprops={"arrowstyle":"->"})
    ax.set_aspect("equal"); ax.set_xlim(-135,135); ax.set_ylim(-35,125); ax.axis("off")
    fig.suptitle("Two-handed profile sander · no metal hardware",fontsize=21)
    fig.text(.5,.04,"Schematic · reusable tote and threaded knob · replaceable latch plate and shoe",ha="center")
    fig.savefig(path,dpi=180,facecolor=fig.get_facecolor()); plt.close(fig)


def verify_mesh(path: Path) -> str:
    mesh = trimesh.load_mesh(path, force="mesh", process=True)
    bodies = len(mesh.split(only_watertight=False))
    if not mesh.is_watertight or not mesh.is_winding_consistent or bodies != 1:
        raise RuntimeError(f"Mesh verification failed for {path.name}")
    return (
        f"{path.name}: {tuple(round(float(value), 3) for value in mesh.extents)} mm, "
        f"watertight={mesh.is_watertight}, winding={mesh.is_winding_consistent}, bodies={bodies}"
    )


def export_part(shape: TopoDS_Shape, name: str, flip_for_print: bool = False) -> trimesh.Trimesh:
    write_step(shape, MODELS / f"{name}.step")
    # STEP preserves assembly coordinates; printable meshes carry the selected
    # build orientation. The full plate, knob and shoe still need support review.
    print_shape = shape
    if flip_for_print:
        print_shape = socket_print_orientation(shape)
    if name in ('profile-jig-reusable-tote', 'profile-jig-tote-mount-test-foot'):
        print_shape = tote_print_orientation(shape)
    stl_path = MODELS / f"{name}.stl"
    write_stl(orient_upright(print_shape), stl_path)
    # CAD bounding boxes include conservative meshing margins. Seat the actual
    # exported vertices on the build plane, not that expanded bounding box.
    print_mesh = trimesh.load_mesh(stl_path, force="mesh", process=True)
    print_mesh.apply_translation(-print_mesh.bounds[0])
    print_mesh.export(stl_path)
    stl_to_3mf(MODELS / f"{name}.stl", MODELS / f"{name}.3mf")
    print(verify_mesh(MODELS / f"{name}.stl"))
    return trimesh.load_mesh(MODELS / f"{name}.stl", force="mesh", process=True)


def export_assembly(named_shapes: list[tuple[str, TopoDS_Shape, list[int]]], output_stem="profile-jig-assembled-preview", layout_on_plate=False) -> None:
    parts = []
    meshes = []
    names = []
    next_x = 0.0
    for name, shape, color in named_shapes:
        temporary = MODELS / ".assembly-part.stl"
        if isinstance(shape, trimesh.Trimesh):
            mesh = shape.copy()
        else:
            write_stl(shape, temporary)
            mesh = trimesh.load_mesh(temporary, force="mesh", process=True)
        if layout_on_plate:
            mesh.apply_translation(-mesh.bounds[0] + np.array([next_x, 0, 0]))
            next_x = mesh.bounds[1, 0] + 8
        meshes.append(mesh)
        temporary.unlink(missing_ok=True)
        parts.append((shape, color)); names.append(name)
    assembly = trimesh.Scene(meshes)
    if layout_on_plate:
        # A single STL preserves the coupon's separate bodies and bed layout,
        # so multiple tests can be imported into one existing slicer project.
        stl_output = MODELS / f"{output_stem}.stl"
        temporary = stl_output.with_suffix('.stl.tmp')
        temporary.write_bytes(trimesh.util.concatenate(meshes).export(file_type='stl'))
        temporary.replace(stl_output)
    # trimesh's exporter omits display colors. Add standard 3MF base materials
    # so the assembly keeps its part colors in the browser and other viewers.
    with ZipFile(BytesIO(assembly.export(file_type="3mf"))) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    namespace = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", namespace)
    ET.register_namespace("p", "http://schemas.microsoft.com/3dmanufacturing/production/2015/06")
    for filename, data in list(entries.items()):
        if not filename.endswith(".model"):
            continue
        root = ET.fromstring(data)
        resources = root.find(f"{{{namespace}}}resources")
        objects = resources.findall(f"{{{namespace}}}object")
        assert len(objects) == len(parts)
        materials = ET.Element(f"{{{namespace}}}basematerials", {"id": "100"})
        for index, (obj, (_, color), name) in enumerate(zip(objects, parts, names)):
            ET.SubElement(materials, f"{{{namespace}}}base", {
                "name": name, "displaycolor": "#" + "".join(f"{value:02X}" for value in color)})
            obj.set("pid", "100")
            obj.set("pindex", str(index))
            obj.set("name", name)
        resources.insert(0, materials)
        entries[filename] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    output = MODELS / f"{output_stem}.3mf"
    with ZipFile(output.with_suffix(".tmp"), "w", ZIP_DEFLATED) as archive:
        for filename, data in entries.items():
            archive.writestr(filename, data)
    output.with_suffix(".tmp").replace(output)


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    carrier, tote, knob = grip_mounts.make_parts(sys.modules[__name__])
    shoe = make_shoe()
    rail_coupon, socket_coupon = make_fit_coupon()
    thread_male, thread_female = grip_mounts.thread_coupon(sys.modules[__name__])
    tote_socket, tote_foot = grip_mounts.tote_coupon(sys.modules[__name__])
    for name, shape in (
        ("profile-jig-latch-plate", carrier),
        ("profile-jig-reusable-tote", tote),
        ("profile-jig-reusable-knob", knob),
        ("magnate-5869-sanding-shoe-250mm", shoe),
        ("profile-jig-dovetail-coupon-rail", rail_coupon),
        ("profile-jig-dovetail-coupon-socket", socket_coupon),
        ("profile-jig-knob-thread-test-stud", thread_male),
        ("profile-jig-knob-thread-test-cap", thread_female),
        ("profile-jig-tote-mount-test-socket", tote_socket),
        ("profile-jig-tote-mount-test-foot", tote_foot),
    ):
        export_part(shape, name, flip_for_print=name in ("profile-jig-dovetail-coupon-socket", "profile-jig-knob-thread-test-cap"))
    export_assembly([
        ("Replaceable latch plate", carrier, [84,116,102,255]),
        ("Reusable rear tote", tote, [66,88,105,255]),
        ("Reusable front knob", knob, [66,88,105,255]),
        ("Sliding profile shoe", shoe, [188,117,70,255]),
    ])
    export_assembly([
        ("Replaceable latch plate", carrier, [84,116,102,255]),
        ("Reusable rear tote", shifted(tote,x=-45,z=35), [66,88,105,255]),
        ("Reusable front knob", shifted(knob,x=-45,z=35), [66,88,105,255]),
        ("Sliding profile shoe", shifted(shoe,z=-25), [188,117,70,255]),
    ], "profile-jig-exploded-preview")
    export_assembly([
        ("Socket with integral thumb latch", socket_coupon, [84,116,102,255]),
        ("Coupon rail", rail_coupon, [188,117,70,255]),
    ], "profile-jig-latch-coupon-preview")
    export_assembly([
        ("Socket with integral thumb latch", socket_print_orientation(socket_coupon), [84,116,102,255]),
        ("Coupon rail", rail_coupon, [188,117,70,255]),
    ], "profile-jig-latch-coupon-print-plate", layout_on_plate=True)
    export_assembly([
        ("Thread test stud", thread_male, [84,116,102,255]),
        ("Thread test cap", socket_print_orientation(thread_female), [66,88,105,255]),
    ], "profile-jig-knob-thread-test-print-plate", layout_on_plate=True)
    export_assembly([
        ("Tote test socket", tote_socket, [84,116,102,255]),
        ("Tote test foot", tote_foot, [66,88,105,255]),
    ], "profile-jig-tote-mount-test-preview")
    export_assembly([
        ("Tote test socket", tote_socket, [84,116,102,255]),
        ("Tote test foot, side down", tote_print_orientation(tote_foot), [66,88,105,255]),
    ], "profile-jig-tote-mount-test-print-plate", layout_on_plate=True)
    # Section model is inspection-only; it exposes the actual thread flanks.
    section = block(0, KNOB_Y-30, 0, 30, 60, 120)
    export_assembly([
        ("Knob section", boolean(BRepAlgoAPI_Cut,knob,section,"sectioning female knob thread"), [66,88,105,255]),
        ("Stud section", boolean(BRepAlgoAPI_Cut,grip_mounts.male_thread(sys.modules[__name__]),section,"sectioning male stud"), [84,116,102,255]),
    ], "profile-jig-knob-section-preview")
    write_preview(IMAGES / "interchangeable-profile-jig-tote-grip-preview.png")
    print("CAD valid:",all(BRepCheck_Analyzer(s).IsValid() for s in (carrier,tote,knob,shoe,rail_coupon,socket_coupon)))


if __name__ == "__main__":
    main()
