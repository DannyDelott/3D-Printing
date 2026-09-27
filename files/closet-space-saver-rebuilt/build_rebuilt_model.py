#!/usr/bin/env python3
"""Clean parametric rebuild of a hanging closet space-saver basket.

This does not import or boolean-edit the MakerWorld mesh. It constructs simple
planar panels from the published 250 x 220 x 220 mm envelope and 25 degree
basket angle, then perforates only the end, back, and angled basket panels.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet2d
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.StlAPI import StlAPI_Writer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_VERTEX
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS, TopoDS_Compound, TopoDS_Face, TopoDS_Shape
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

# Published envelope and basket angle.
WIDTH = 250.0
DEPTH = 220.0
HEIGHT = 220.0
ANGLE_DEG = 25.0

# Clean rebuilt construction.
WALL = 1.4
TOP_WALL = 2.0
END_PANEL = 1.4
BOTTOM_FLAT = 50.0
FRAME = 10.0

# Point-up regular hexagon. An 18 mm flat-to-flat width gives a 10.392 mm
# side length and a 20.785 mm point-to-point height; every edge is identical.
HEX_FLAT_TO_FLAT = 18.0
HEX_SIDE = HEX_FLAT_TO_FLAT / math.sqrt(3.0)
HEX_HALF_WIDTH = HEX_FLAT_TO_FLAT / 2.0
HEX_SIDE_HALF_HEIGHT = HEX_SIDE / 2.0
HEX_HALF_HEIGHT = HEX_SIDE
HEX_CORNER_RADIUS = 1.5
HEX_PITCH_H = 21.5
HEX_PITCH_V = 20.0

ANGLE = math.radians(ANGLE_DEG)
TANGENT = (math.cos(ANGLE), math.sin(ANGLE), 0.0)
NORMAL = (-math.sin(ANGLE), math.cos(ANGLE), 0.0)
ANGLED_LENGTH = (DEPTH - BOTTOM_FLAT) / math.cos(ANGLE)
ANGLED_RISE = (DEPTH - BOTTOM_FLAT) * math.tan(ANGLE)

# The long-wall section is a single clean 2 mm U-profile: top shelf contact,
# back, short flat bottom, angled basket floor, and small front return.
CROSS_SECTION = [
    (0.0, 0.0),
    (0.0, HEIGHT),
    (DEPTH, HEIGHT),
    (DEPTH, HEIGHT - TOP_WALL),
    (WALL, HEIGHT - TOP_WALL),
    (WALL, WALL),
    (BOTTOM_FLAT - WALL * math.sin(ANGLE), WALL),
    (DEPTH, ANGLED_RISE + WALL / math.cos(ANGLE)),
    (DEPTH, ANGLED_RISE),
    (BOTTOM_FLAT, 0.0),
]

SIDE_OUTLINE = [
    (0.0, 0.0),
    (0.0, HEIGHT),
    (DEPTH, HEIGHT),
    (DEPTH, ANGLED_RISE),
    (BOTTOM_FLAT, 0.0),
]


def face_xy(points: list[tuple[float, float]], z: float = 0.0):
    wire = BRepBuilderAPI_MakePolygon()
    for x, y in points:
        wire.Add(gp_Pnt(x, y, z))
    wire.Close()
    return BRepBuilderAPI_MakeFace(wire.Wire()).Face()


def compound(shapes: list[TopoDS_Shape]) -> TopoDS_Compound:
    result = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(result)
    for shape in shapes:
        builder.Add(result, shape)
    return result


def boolean(operation, left: TopoDS_Shape, right: TopoDS_Shape, label: str) -> TopoDS_Shape:
    print(label, flush=True)
    algo = operation(left, right)
    algo.SetFuzzyValue(1e-5)
    algo.Build()
    if not algo.IsDone():
        raise RuntimeError(f"Boolean failed: {label}")
    algo.SimplifyResult(True, True)
    result = algo.Shape()
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError(f"Invalid solid after: {label}")
    return result


def plane_prism(
    center: tuple[float, float, float],
    horizontal: tuple[float, float, float],
    vertical: tuple[float, float, float],
    points: list[tuple[float, float]],
    start_offset: tuple[float, float, float],
    extrusion: tuple[float, float, float],
    corner_radius: float = 0.0,
) -> TopoDS_Shape:
    wire = BRepBuilderAPI_MakePolygon()
    for h, v in points:
        wire.Add(
            gp_Pnt(
                center[0] + horizontal[0] * h + vertical[0] * v + start_offset[0],
                center[1] + horizontal[1] * h + vertical[1] * v + start_offset[1],
                center[2] + horizontal[2] * h + vertical[2] * v + start_offset[2],
            )
        )
    wire.Close()
    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    if corner_radius > 0.0:
        face = fillet_face_vertices(face, corner_radius)
    return BRepPrimAPI_MakePrism(
        face, gp_Vec(*extrusion)
    ).Shape()


def fillet_face_vertices(face: TopoDS_Face, radius: float) -> TopoDS_Face:
    """Apply an exact tangent radius to every corner of a planar face."""
    vertices = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(face, TopAbs_VERTEX, vertices)
    fillet = BRepFilletAPI_MakeFillet2d(face)
    for index in range(1, vertices.Extent() + 1):
        edge = fillet.AddFillet(TopoDS.Vertex_s(vertices.FindKey(index)), radius)
        if edge.IsNull():
            raise RuntimeError(f"Could not apply {radius:g} mm hex corner radius")
    fillet.Build()
    if not fillet.IsDone():
        raise RuntimeError(f"Could not build {radius:g} mm hex corner radii")
    return TopoDS.Face_s(fillet.Shape())


def hex_prism(
    center: tuple[float, float, float],
    horizontal: tuple[float, float, float],
    vertical: tuple[float, float, float],
    start_offset: tuple[float, float, float],
    extrusion: tuple[float, float, float],
) -> TopoDS_Shape:
    return plane_prism(
        center,
        horizontal,
        vertical,
        hex_points(),
        start_offset,
        extrusion,
        corner_radius=HEX_CORNER_RADIUS,
    )


def hex_points() -> list[tuple[float, float]]:
    """Return a point-up regular hexagon centered on the origin."""
    return [
        (0.0, HEX_HALF_HEIGHT),
        (HEX_HALF_WIDTH, HEX_SIDE_HALF_HEIGHT),
        (HEX_HALF_WIDTH, -HEX_SIDE_HALF_HEIGHT),
        (0.0, -HEX_HALF_HEIGHT),
        (-HEX_HALF_WIDTH, -HEX_SIDE_HALF_HEIGHT),
        (-HEX_HALF_WIDTH, HEX_SIDE_HALF_HEIGHT),
    ]


def centered_positions(low: float, high: float, pitch: float) -> list[float]:
    count = max(1, math.floor((high - low) / pitch) + 1)
    used = (count - 1) * pitch
    start = (low + high - used) / 2.0
    return [start + i * pitch for i in range(count)]


def point_inside_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def distance_to_segment(p, a, b) -> float:
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def side_hex_fits(center: tuple[float, float]) -> bool:
    cx, cy = center
    vertices = [(cx + h, cy + v) for h, v in hex_points()]
    edges = list(zip(SIDE_OUTLINE, SIDE_OUTLINE[1:] + SIDE_OUTLINE[:1]))
    for vertex in vertices:
        if not point_inside_polygon(vertex, SIDE_OUTLINE):
            return False
        if min(distance_to_segment(vertex, a, b) for a, b in edges) < FRAME:
            return False
    return True


def build_shell() -> TopoDS_Shape:
    long_walls = BRepPrimAPI_MakePrism(face_xy(CROSS_SECTION), gp_Vec(0.0, 0.0, WIDTH)).Shape()
    left = BRepPrimAPI_MakePrism(face_xy(SIDE_OUTLINE, 0.0), gp_Vec(0.0, 0.0, END_PANEL)).Shape()
    right = BRepPrimAPI_MakePrism(
        face_xy(SIDE_OUTLINE, WIDTH - END_PANEL), gp_Vec(0.0, 0.0, END_PANEL)
    ).Shape()
    return boolean(BRepAlgoAPI_Fuse, long_walls, compound([left, right]), "Fusing the clean planar shell...")


def end_panel_cutters() -> list[TopoDS_Shape]:
    cutters: list[TopoDS_Shape] = []
    ys = centered_positions(FRAME + HEX_HALF_HEIGHT, HEIGHT - FRAME - HEX_HALF_HEIGHT, HEX_PITCH_V)
    xs_base = centered_positions(FRAME + HEX_HALF_WIDTH, DEPTH - FRAME - HEX_HALF_WIDTH, HEX_PITCH_H)
    for z, start_z, extrusion_z in ((0.0, -1.0, 4.0), (WIDTH, 1.0, -4.0)):
        for row, y in enumerate(ys):
            for x0 in xs_base:
                x = x0 + (HEX_PITCH_H / 2.0 if row % 2 else 0.0)
                if side_hex_fits((x, y)):
                    cutters.append(
                        hex_prism(
                            (x, y, z),
                            (1.0, 0.0, 0.0),
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, start_z),
                            (0.0, 0.0, extrusion_z),
                        )
                    )
    return cutters


def back_cutters() -> list[TopoDS_Shape]:
    cutters: list[TopoDS_Shape] = []
    ys = centered_positions(FRAME + HEX_HALF_HEIGHT, HEIGHT - FRAME - HEX_HALF_HEIGHT, HEX_PITCH_V)
    zs = centered_positions(FRAME + HEX_HALF_WIDTH, WIDTH - FRAME - HEX_HALF_WIDTH, HEX_PITCH_H)
    for row, y in enumerate(ys):
        for z0 in zs:
            z = z0 + (HEX_PITCH_H / 2.0 if row % 2 else 0.0)
            if z + HEX_HALF_WIDTH <= WIDTH - FRAME:
                cutters.append(
                    hex_prism(
                        (0.0, y, z),
                        (0.0, 0.0, 1.0),
                        (0.0, 1.0, 0.0),
                        (-1.0, 0.0, 0.0),
                        (4.0, 0.0, 0.0),
                    )
                )
    return cutters


def bottom_cutters() -> list[TopoDS_Shape]:
    cutters: list[TopoDS_Shape] = []
    # Keep one centered row on this 50 mm face so both 10 mm rails remain
    # straight and structurally continuous.
    xs = [BOTTOM_FLAT / 2.0]
    zs = centered_positions(FRAME + HEX_HALF_WIDTH, WIDTH - FRAME - HEX_HALF_WIDTH, HEX_PITCH_H)
    for row, x in enumerate(xs):
        for z0 in zs:
            z = z0 + (HEX_PITCH_H / 2.0 if row % 2 else 0.0)
            if z + HEX_HALF_WIDTH <= WIDTH - FRAME:
                cutters.append(
                    hex_prism(
                        (x, 0.0, z),
                        (0.0, 0.0, 1.0),
                        (1.0, 0.0, 0.0),
                        (0.0, -1.0, 0.0),
                        (0.0, 4.0, 0.0),
                    )
                )
    return cutters


def angled_cutters() -> list[TopoDS_Shape]:
    cutters: list[TopoDS_Shape] = []
    ts = centered_positions(FRAME + HEX_HALF_HEIGHT, ANGLED_LENGTH - FRAME - HEX_HALF_HEIGHT, HEX_PITCH_V)
    zs = centered_positions(FRAME + HEX_HALF_WIDTH, WIDTH - FRAME - HEX_HALF_WIDTH, HEX_PITCH_H)
    origin = (BOTTOM_FLAT, 0.0, 0.0)
    for row, t in enumerate(ts):
        center_xy = (origin[0] + TANGENT[0] * t, origin[1] + TANGENT[1] * t)
        for z0 in zs:
            z = z0 + (HEX_PITCH_H / 2.0 if row % 2 else 0.0)
            if z + HEX_HALF_WIDTH <= WIDTH - FRAME:
                cutters.append(
                    hex_prism(
                        (center_xy[0], center_xy[1], z),
                        (0.0, 0.0, 1.0),
                        TANGENT,
                        tuple(-1.0 * n for n in NORMAL),
                        tuple(4.0 * n for n in NORMAL),
                    )
                )
    return cutters


def top_contact_cutters() -> list[TopoDS_Shape]:
    """Honeycomb the shelf-contact panel, preserving frame and hole pads."""
    cutters: list[TopoDS_Shape] = []
    xs = centered_positions(FRAME + HEX_HALF_HEIGHT, DEPTH - FRAME - HEX_HALF_HEIGHT, HEX_PITCH_V)
    zs = centered_positions(FRAME + HEX_HALF_WIDTH, WIDTH - FRAME - HEX_HALF_WIDTH, HEX_PITCH_H)
    hole_centers = [(x, z) for x in (25.0, 194.1) for z in (25.0, 225.0)]
    local_vertices = hex_points()
    for row, x in enumerate(xs):
        for z0 in zs:
            z = z0 + (HEX_PITCH_H / 2.0 if row % 2 else 0.0)
            if z + HEX_HALF_WIDTH > WIDTH - FRAME:
                continue
            # Keep a solid 12 mm-radius pad around every 5 mm mounting hole.
            vertices = [(x + v, z + h) for h, v in local_vertices]
            if any(math.hypot(vx - hx, vz - hz) < 12.0 for vx, vz in vertices for hx, hz in hole_centers):
                continue
            cutters.append(
                hex_prism(
                    (x, HEIGHT, z),
                    (0.0, 0.0, 1.0),
                    (1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, -4.0, 0.0),
                )
            )
    return cutters


def mounting_holes() -> TopoDS_Compound:
    holes = []
    for x in (25.0, 194.1):
        for z in (25.0, 225.0):
            holes.append(
                BRepPrimAPI_MakeCylinder(
                    gp_Ax2(gp_Pnt(x, HEIGHT - WALL - 1.0, z), gp_Dir(0.0, 1.0, 0.0)),
                    2.5,
                    WALL + 2.0,
                ).Shape()
            )
    return compound(holes)


def bounds(shape: TopoDS_Shape):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    return box.Get()


def volume(shape: TopoDS_Shape) -> float:
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def solid_count(shape: TopoDS_Shape) -> int:
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    result = 0
    while explorer.More():
        result += 1
        explorer.Next()
    return result


def print_ready(shape: TopoDS_Shape) -> TopoDS_Shape:
    rotation = gp_Trsf()
    rotation.SetValues(
        1.21599462e-05, 6.12724601e-08, 1.0, 0.0,
        -0.999987305, -0.00503881194, 1.21601006e-05, 0.0,
        0.00503881194, -0.999987305, 5.55111512e-17, 0.0,
    )
    rotated = BRepBuilderAPI_Transform(shape, rotation, True).Shape()
    xmin, ymin, zmin, _, _, _ = bounds(rotated)
    move = gp_Trsf()
    move.SetTranslation(gp_Vec(-xmin, -ymin, -zmin))
    return BRepBuilderAPI_Transform(rotated, move, True).Shape()


def write_step(shape: TopoDS_Shape, path: Path) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"Could not write {path}")


def write_stl(shape: TopoDS_Shape, path: Path) -> None:
    import trimesh

    BRepMesh_IncrementalMesh(shape, 0.12, False, 0.35, True).Perform()
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape, str(path)):
        raise RuntimeError(f"Could not write {path}")
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    mesh.process(validate=True)
    path.write_bytes(mesh.export(file_type="stl"))


def render_preview(stl_path: Path, output_path: Path) -> None:
    """Render flat CAD-like surfaces without exposing STL triangulation."""
    from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
    from vtkmodules.vtkIOGeometry import vtkSTLReader
    from vtkmodules.vtkIOImage import vtkPNGWriter
    from vtkmodules.vtkRenderingCore import (
        vtkActor,
        vtkPolyDataMapper,
        vtkRenderer,
        vtkRenderWindow,
        vtkWindowToImageFilter,
    )
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401

    reader = vtkSTLReader()
    reader.SetFileName(str(stl_path))
    normals = vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.SplittingOff()
    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.72, 0.78, 0.70)
    actor.GetProperty().SetInterpolationToFlat()
    actor.GetProperty().SetSpecular(0.12)
    actor.GetProperty().SetSpecularPower(25)
    renderer = vtkRenderer()
    renderer.SetBackground(0.95, 0.94, 0.91)
    renderer.AddActor(actor)
    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1400, 1000)
    window.AddRenderer(renderer)
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.Azimuth(-45)
    camera.Elevation(24)
    camera.Zoom(1.25)
    renderer.ResetCameraClippingRange()
    window.Render()
    capture = vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.Update()
    writer = vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()


def main() -> None:
    import trimesh

    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = build_shell()
    for label, cutters in (
        ("Cutting small hexes in both end panels...", end_panel_cutters()),
        ("Cutting small hexes in the back wall...", back_cutters()),
        ("Cutting hexes in the short bottom face...", bottom_cutters()),
        ("Cutting small hexes in the angled basket floor...", angled_cutters()),
        ("Cutting reinforced hexes in the mounting face...", top_contact_cutters()),
    ):
        result = boolean(BRepAlgoAPI_Cut, result, compound(cutters), label)
    result = boolean(BRepAlgoAPI_Cut, result, mounting_holes(), "Cutting four mounting holes...")

    if solid_count(result) != 1:
        raise RuntimeError(f"Expected one solid, found {solid_count(result)}")

    brep = OUTPUT / "closet-space-saver-simple-small-hex.brep"
    step = OUTPUT / "closet-space-saver-simple-small-hex.step"
    design_stl = OUTPUT / "closet-space-saver-simple-small-hex-design.stl"
    ready_stl = OUTPUT / "closet-space-saver-simple-small-hex-print-ready.stl"
    ready_3mf = OUTPUT / "closet-space-saver-simple-small-hex-print-ready.3mf"
    preview = OUTPUT / "closet-space-saver-simple-small-hex-preview.png"

    BRepTools.Write_s(result, str(brep))
    write_step(result, step)
    write_stl(result, design_stl)
    write_stl(print_ready(result), ready_stl)
    mesh = trimesh.load_mesh(ready_stl, force="mesh", process=True)
    ready_3mf.write_bytes(mesh.export(file_type="3mf"))
    render_preview(ready_stl, preview)

    vol = volume(result)
    pla_grams = vol / 1000.0 * 1.24
    print(
        f"Done: valid one-piece solid; volume={vol:.1f} mm^3; "
        f"solid-PLA equivalent={pla_grams:.1f} g",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
