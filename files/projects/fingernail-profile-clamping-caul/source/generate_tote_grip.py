#!/usr/bin/env python3
"""Generate a handplane-tote grip for interchangeable profile cauls.

The grip uses the shared mounting land defined in profile_interface.py.  A
shallow saddle locates on the caul and two captive-nut M3 thumb screws clamp
its sides.  A 45-degree gabled channel lets the one-piece tote print upright
without supports while keeping the attachment recess open and clean.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
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
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
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
from OCP.TopoDS import TopoDS, TopoDS_Compound, TopoDS_Shape
from OCP.gp import gp_Ax1, gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

from profile_interface import (
    ATTACHMENT_MINIMUM_SIDE_DEPTH,
    ATTACHMENT_TOP_CHAMFER,
    ATTACHMENT_WIDTH,
    SADDLE_TOP_CLEARANCE,
    SADDLE_WIDTH_CLEARANCE,
)


PROJECT = Path(__file__).resolve().parents[1]
MODELS = PROJECT / "models"
IMAGES = PROJECT / "images"

SADDLE_LENGTH = 100.0
SADDLE_OUTER_WIDTH = 39.0
SADDLE_BOTTOM = -3.8
SADDLE_TOP = 18.0
CHANNEL_HALF_WIDTH = (ATTACHMENT_WIDTH + SADDLE_WIDTH_CLEARANCE) / 2.0
CHANNEL_GABLE_APEX = SADDLE_TOP_CLEARANCE + CHANNEL_HALF_WIDTH

HANDLE_X_MIN = -12.5
HANDLE_X_MAX = SADDLE_OUTER_WIDTH / 2.0
HANDLE_WIDTH = HANDLE_X_MAX - HANDLE_X_MIN
HANDLE_EDGE_RADIUS = 2.5

SCREW_DIAMETER = 3.4
SCREW_Z = -0.95
SCREW_POSITIONS = (-29.0, 29.0)
NUT_ACROSS_FLATS = 5.7
NUT_TRAP_DEPTH = 2.7

# The matching 45-degree roof and caul chamfers create a self-centering datum.
SEATED_CAUL_TOP_Z = (
    SADDLE_TOP_CLEARANCE
    + CHANNEL_HALF_WIDTH
    - (ATTACHMENT_WIDTH / 2.0 - ATTACHMENT_TOP_CHAMFER)
)

FIT_COUPON_LENGTH = 30.0

Point2 = tuple[float, float]
Segment = tuple[str, tuple[Point2, ...]]


OUTER_SEGMENTS: list[Segment] = [
    ("line", ((-48.0, 6.0), (44.0, 6.0))),
    ("bezier", ((44.0, 6.0), (46.0, 11.0), (45.0, 18.0), (36.0, 22.0))),
    ("bezier", ((36.0, 22.0), (29.0, 34.0), (25.0, 58.0), (18.0, 80.0))),
    ("bezier", ((18.0, 80.0), (13.0, 95.0), (0.0, 100.0), (-11.0, 91.0))),
    ("bezier", ((-11.0, 91.0), (-22.0, 82.0), (-28.0, 65.0), (-35.0, 47.0))),
    ("bezier", ((-35.0, 47.0), (-40.0, 34.0), (-48.0, 25.0), (-48.0, 16.0))),
    ("line", ((-48.0, 16.0), (-48.0, 6.0))),
]

# Clockwise so OpenCascade recognizes this wire as the handle opening.
INNER_SEGMENTS: list[Segment] = [
    ("bezier", ((-31.0, 22.0), (-29.0, 31.0), (-27.0, 38.0), (-25.0, 44.0))),
    ("bezier", ((-25.0, 44.0), (-20.0, 60.0), (-16.0, 72.0), (-8.0, 79.0))),
    ("bezier", ((-8.0, 79.0), (-1.0, 85.0), (8.0, 82.0), (12.0, 73.0))),
    ("bezier", ((12.0, 73.0), (17.0, 56.0), (21.0, 34.0), (29.0, 22.0))),
    ("line", ((29.0, 22.0), (-31.0, 22.0))),
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
    face_builder.Add(wire_for_segments(INNER_SEGMENTS, HANDLE_X_MIN))
    face = face_builder.Face()
    handle = BRepPrimAPI_MakePrism(face, gp_Vec(HANDLE_WIDTH, 0.0, 0.0)).Shape()
    if not BRepCheck_Analyzer(handle).IsValid():
        raise RuntimeError("Raw tote handle is invalid")
    return soften_handle_edges(handle)


def soften_handle_edges(handle: TopoDS_Shape) -> TopoDS_Shape:
    """Round the two broad-side perimeters for a more comfortable grip."""
    fillet = BRepFilletAPI_MakeFillet(handle)
    explorer = TopExp_Explorer(handle, TopAbs_EDGE)
    selected = 0
    while explorer.More():
        edge = TopoDS.Edge_s(explorer.Current())
        box = Bnd_Box()
        BRepBndLib.Add_s(edge, box)
        xmin, _, _, xmax, _, _ = box.Get()
        if xmax - xmin < 0.01:
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


def compound(shapes: list[TopoDS_Shape]) -> TopoDS_Compound:
    result = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(result)
    for shape in shapes:
        builder.Add(result, shape)
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


def saddle_block(length: float) -> TopoDS_Shape:
    return BRepPrimAPI_MakeBox(
        gp_Pnt(-SADDLE_OUTER_WIDTH / 2.0, -length / 2.0, SADDLE_BOTTOM),
        SADDLE_OUTER_WIDTH,
        length,
        SADDLE_TOP - SADDLE_BOTTOM,
    ).Shape()


def channel_cutter(length: float) -> TopoDS_Shape:
    y_start = -length / 2.0 - 1.0
    polygon = BRepBuilderAPI_MakePolygon()
    for x, z in (
        (-CHANNEL_HALF_WIDTH, SADDLE_BOTTOM - 1.0),
        (CHANNEL_HALF_WIDTH, SADDLE_BOTTOM - 1.0),
        (CHANNEL_HALF_WIDTH, SADDLE_TOP_CLEARANCE),
        (0.0, CHANNEL_GABLE_APEX),
        (-CHANNEL_HALF_WIDTH, SADDLE_TOP_CLEARANCE),
    ):
        polygon.Add(gp_Pnt(x, y_start, z))
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0.0, length + 2.0, 0.0)).Shape()


def hex_nut_cutter(y: float) -> TopoDS_Shape:
    radius = NUT_ACROSS_FLATS / math.sqrt(3.0)
    x_start = SADDLE_OUTER_WIDTH / 2.0 - NUT_TRAP_DEPTH
    polygon = BRepBuilderAPI_MakePolygon()
    for index in range(6):
        # Vertices left/right minimize the nut pocket's vertical envelope so
        # the saddle jaws stay clear of the sanding surface when seated.
        angle = math.radians(60.0 * index)
        polygon.Add(
            gp_Pnt(
                x_start,
                y + radius * math.cos(angle),
                SCREW_Z + radius * math.sin(angle),
            )
        )
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(NUT_TRAP_DEPTH + 0.3, 0.0, 0.0)).Shape()


def screw_hole_cutter(y: float) -> TopoDS_Shape:
    return BRepPrimAPI_MakeCylinder(
        gp_Ax2(
            gp_Pnt(CHANNEL_HALF_WIDTH - 0.4, y, SCREW_Z),
            gp_Dir(1.0, 0.0, 0.0),
        ),
        SCREW_DIAMETER / 2.0,
        SADDLE_OUTER_WIDTH / 2.0 - CHANNEL_HALF_WIDTH + 1.0,
    ).Shape()


def cut_saddle_features(shape: TopoDS_Shape, length: float, screws: tuple[float, ...]) -> TopoDS_Shape:
    # The screw bore overlaps its nut trap.  Cutting a compound of overlapping
    # tools can leave tiny 42 mm3 sliver solids in OpenCascade, so apply these
    # cutters sequentially and keep the result as one connected solid.
    result = boolean(BRepAlgoAPI_Cut, shape, channel_cutter(length), "cutting saddle channel")
    for y in screws:
        result = boolean(BRepAlgoAPI_Cut, result, screw_hole_cutter(y), "cutting M3 screw bore")
        result = boolean(BRepAlgoAPI_Cut, result, hex_nut_cutter(y), "cutting M3 nut trap")
    return result


def make_tote_grip() -> TopoDS_Shape:
    joined = boolean(
        BRepAlgoAPI_Fuse,
        saddle_block(SADDLE_LENGTH),
        make_handle_blank(),
        "joining tote to saddle",
    )
    return cut_saddle_features(joined, SADDLE_LENGTH, SCREW_POSITIONS)


def make_fit_coupon() -> TopoDS_Shape:
    return cut_saddle_features(saddle_block(FIT_COUPON_LENGTH), FIT_COUPON_LENGTH, (0.0,))


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
    fig, (ax_side, ax_front) = plt.subplots(
        1,
        2,
        figsize=(13, 7),
        facecolor="#f3efe7",
        gridspec_kw={"width_ratios": [1.45, 0.8]},
    )
    for axis in (ax_side, ax_front):
        axis.set_facecolor("#fbfaf7")

    ax_side.add_patch(Rectangle((-125.0, -7.465), 250.0, 7.465, facecolor="#e58b49", edgecolor="#743d27"))
    ax_side.add_patch(
        Rectangle(
            (-SADDLE_LENGTH / 2.0, SADDLE_BOTTOM),
            SADDLE_LENGTH,
            SADDLE_TOP - SADDLE_BOTTOM,
            facecolor="#455560",
            edgecolor="#26333b",
        )
    )
    outer = sample_outline(OUTER_SEGMENTS)
    inner = sample_outline(INNER_SEGMENTS)
    ax_side.add_patch(MplPolygon(outer, closed=True, facecolor="#667985", edgecolor="#26333b", linewidth=2.0))
    ax_side.add_patch(MplPolygon(inner, closed=True, facecolor="#fbfaf7", edgecolor="#26333b", linewidth=1.7))
    ax_side.text(0.0, -4.0, "replaceable profile jig", ha="center", va="center", color="white", fontsize=11)
    ax_side.set_xlim(-135.0, 135.0)
    ax_side.set_ylim(-14.0, 108.0)
    ax_side.set_aspect("equal")
    ax_side.set_axis_off()
    ax_side.set_title("Tote mounted at the jig center", fontsize=14, pad=12)

    half_outer = SADDLE_OUTER_WIDTH / 2.0
    ax_front.add_patch(
        Rectangle(
            (-half_outer, SADDLE_BOTTOM),
            SADDLE_OUTER_WIDTH,
            SADDLE_TOP - SADDLE_BOTTOM,
            facecolor="#455560",
            edgecolor="#26333b",
            linewidth=2.0,
        )
    )
    ax_front.add_patch(
        MplPolygon(
            [
                (-CHANNEL_HALF_WIDTH, SADDLE_BOTTOM - 0.1),
                (CHANNEL_HALF_WIDTH, SADDLE_BOTTOM - 0.1),
                (CHANNEL_HALF_WIDTH, SADDLE_TOP_CLEARANCE),
                (0.0, CHANNEL_GABLE_APEX),
                (-CHANNEL_HALF_WIDTH, SADDLE_TOP_CLEARANCE),
            ],
            closed=True,
            facecolor="#fbfaf7",
            edgecolor="#26333b",
            linewidth=1.5,
        )
    )
    crown = 3.464839
    xs = np.linspace(-ATTACHMENT_WIDTH / 2.0, ATTACHMENT_WIDTH / 2.0, 240)
    radius = 38.1
    edge_circle = math.sqrt(radius**2 - (ATTACHMENT_WIDTH / 2.0) ** 2)
    profile = -(4.0 + crown - (np.sqrt(radius**2 - xs**2) - edge_circle))
    caul_polygon = [(-ATTACHMENT_WIDTH / 2.0, 0.0), (ATTACHMENT_WIDTH / 2.0, 0.0)]
    caul_polygon.extend((float(x), float(z)) for x, z in zip(xs[::-1], profile[::-1]))
    ax_front.add_patch(MplPolygon(caul_polygon, closed=True, facecolor="#e58b49", edgecolor="#743d27", linewidth=1.8))
    ax_front.annotate(
        "",
        xy=(ATTACHMENT_WIDTH / 2.0, SCREW_Z),
        xytext=(half_outer + 6.0, SCREW_Z),
        arrowprops={"arrowstyle": "-|>", "color": "#c7a35c", "lw": 2.2},
    )
    ax_front.text(0.0, 12.5, "45° locating / print roof", ha="center", va="center", color="#4f4a43", fontsize=10)
    ax_front.text(0.0, -10.0, "two M3 thumb screws along the saddle\nclamp the shared mounting land", ha="center", va="top", color="#4f4a43", fontsize=10)
    ax_front.set_xlim(-29.0, 29.0)
    ax_front.set_ylim(-18.0, 17.0)
    ax_front.set_aspect("equal")
    ax_front.set_axis_off()
    ax_front.set_title("Shared attachment interface", fontsize=14, pad=12)

    fig.suptitle("Interchangeable profile-jig tote grip", fontsize=20, fontweight="bold")
    fig.text(
        0.5,
        0.025,
        "Upright support-free print · 0.50 mm saddle clearance · captive M3 nuts",
        ha="center",
        fontsize=11,
        color="#4f4a43",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def verify_mesh(path: Path) -> str:
    mesh = trimesh.load_mesh(path, force="mesh", process=True)
    bodies = len(mesh.split(only_watertight=False))
    if not mesh.is_watertight or not mesh.is_winding_consistent or bodies != 1:
        raise RuntimeError(f"Mesh verification failed for {path.name}")
    return (
        f"{path.name}: {tuple(round(float(value), 3) for value in mesh.extents)} mm, "
        f"watertight={mesh.is_watertight}, winding={mesh.is_winding_consistent}, bodies={bodies}"
    )


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    tote = make_tote_grip()
    coupon = make_fit_coupon()
    tote_print = orient_upright(tote)
    coupon_print = orient_upright(coupon)

    tote_step = MODELS / "interchangeable-profile-jig-tote-grip.step"
    tote_stl = MODELS / "interchangeable-profile-jig-tote-grip.stl"
    tote_3mf = MODELS / "interchangeable-profile-jig-tote-grip.3mf"
    coupon_step = MODELS / "profile-jig-tote-saddle-fit-test.step"
    coupon_stl = MODELS / "profile-jig-tote-saddle-fit-test.stl"
    coupon_3mf = MODELS / "profile-jig-tote-saddle-fit-test.3mf"

    write_step(tote, tote_step)
    write_stl(tote_print, tote_stl)
    stl_to_3mf(tote_stl, tote_3mf)
    write_step(coupon, coupon_step)
    write_stl(coupon_print, coupon_stl)
    stl_to_3mf(coupon_stl, coupon_3mf)
    write_preview(IMAGES / "interchangeable-profile-jig-tote-grip-preview.png")

    print(f"Tote BREP valid: {BRepCheck_Analyzer(tote).IsValid()}")
    print(f"Tote use-orientation bounds: {tuple(round(value, 3) for value in bounds(tote))}")
    print(f"Tote volume: {volume(tote):.1f} mm^3")
    print(f"Seated caul-top datum: Z={SEATED_CAUL_TOP_Z:.3f} mm")
    print(
        "Minimum workpiece clearance: "
        f"{ATTACHMENT_MINIMUM_SIDE_DEPTH - (SEATED_CAUL_TOP_Z - SADDLE_BOTTOM):.3f} mm"
    )
    print(verify_mesh(tote_stl))
    print(f"Fit coupon BREP valid: {BRepCheck_Analyzer(coupon).IsValid()}")
    print(verify_mesh(coupon_stl))


if __name__ == "__main__":
    main()
