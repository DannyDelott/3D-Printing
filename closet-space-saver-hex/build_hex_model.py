#!/usr/bin/env python3
"""Build a hex-cutout remix of EmrakulVs15Squirtles' Closet Space Saver.

The script reuses the author's valid 5 mm-fillet and pre-grid BREP bodies from
the original FreeCAD document.  It restores only the material removed by the
three square patterns, makes new point-up hexagonal cuts, and reapplies the
source mounting-hole tool.  The source's later 0.9 mm fillet is deliberately
omitted because that feature is already topologically invalid in the FCStd and
is the likely cause of the published model's "floating regions" slicer warning.
"""

from __future__ import annotations

import math
import shutil
import sys
import zipfile
from pathlib import Path

from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_Transform,
)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.StlAPI import StlAPI_Writer
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shape


ROOT = Path(__file__).resolve().parent
SOURCE_FCSTD = ROOT / "source" / "spacesaver9000.FCStd"
WORK = ROOT / "work" / "build"
OUTPUT = ROOT / "output"

# Original pattern geometry recovered from Document.xml.
BIG_Y_CENTERS = [188.0 - i * (158.0 / 7.0) for i in range(8)]
BIG_Z_CENTERS = [220.0 - i * (190.0 / 8.0) for i in range(9)]
BOTTOM_X_CENTERS = [15.0, 35.0]
BOTTOM_Z_CENTERS = [235.0 - i * 22.0 for i in range(11)]

ANGLE_DEG = 25.0
TANGENT = (math.cos(math.radians(ANGLE_DEG)), math.sin(math.radians(ANGLE_DEG)), 0.0)
NORMAL = (-math.sin(math.radians(ANGLE_DEG)), math.cos(math.radians(ANGLE_DEG)), 0.0)
ANGLED_SEED_SKETCH_CENTER = (
    62.53807115119821 - 2.5 * NORMAL[0],
    8.605043393702028 - 2.5 * NORMAL[1],
    235.0,
)
ANGLED_T0 = ANGLED_SEED_SKETCH_CENTER[0] * TANGENT[0] + ANGLED_SEED_SKETCH_CENTER[1] * TANGENT[1]
ANGLED_T_CENTERS = [ANGLED_T0 + i * (157.0 / 7.0) for i in range(8)]
ANGLED_Z_CENTERS = [235.0 - i * 22.0 for i in range(11)]

# Hex dimensions.  The roof rise equals half-width, giving a 45-degree roof
# on vertical faces.  This is deliberately more printable than a regular
# point-up hex, whose upper edges are only 30 degrees above the build plate.
BACK_HALF_WIDTH = 10.75
BACK_SIDE_HALF_HEIGHT = 3.75
BACK_HALF_HEIGHT = BACK_HALF_WIDTH + BACK_SIDE_HALF_HEIGHT
BACK_ROW_CENTERS = [34.5 + i * ((184.0 - 34.5) / 5.0) for i in range(6)]

SMALL_HALF_WIDTH = 5.0
SMALL_SIDE_HALF_HEIGHT = 2.0
SMALL_HALF_HEIGHT = SMALL_HALF_WIDTH + SMALL_SIDE_HALF_HEIGHT


def read_brep(path: Path) -> TopoDS_Shape:
    shape = TopoDS_Shape()
    builder = BRep_Builder()
    if not BRepTools.Read_s(shape, str(path), builder):
        raise RuntimeError(f"Could not read BREP: {path}")
    return shape


def compound(shapes: list[TopoDS_Shape]) -> TopoDS_Compound:
    result = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(result)
    for shape in shapes:
        builder.Add(result, shape)
    return result


def run_boolean(operation, left: TopoDS_Shape, right: TopoDS_Shape, label: str) -> TopoDS_Shape:
    print(label, flush=True)
    algo = operation(left, right)
    algo.SetFuzzyValue(1e-5)
    algo.Build()
    if not algo.IsDone():
        raise RuntimeError(f"Boolean operation failed: {label}")
    algo.SimplifyResult(True, True)
    return algo.Shape()


def axis_box(x0: float, y0: float, z0: float, dx: float, dy: float, dz: float) -> TopoDS_Shape:
    return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), dx, dy, dz).Shape()


def prism_from_plane_polygon(
    center: tuple[float, float, float],
    horizontal: tuple[float, float, float],
    vertical: tuple[float, float, float],
    points_2d: list[tuple[float, float]],
    extrusion: tuple[float, float, float],
    start_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> TopoDS_Shape:
    polygon = BRepBuilderAPI_MakePolygon()
    for h, v in points_2d:
        polygon.Add(
            gp_Pnt(
                center[0] + horizontal[0] * h + vertical[0] * v + start_offset[0],
                center[1] + horizontal[1] * h + vertical[1] * v + start_offset[1],
                center[2] + horizontal[2] * h + vertical[2] * v + start_offset[2],
            )
        )
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(*extrusion)).Shape()


def rectangle_prism(
    center: tuple[float, float, float],
    horizontal: tuple[float, float, float],
    vertical: tuple[float, float, float],
    half_width: float,
    half_height: float,
    extrusion: tuple[float, float, float],
    start_offset: tuple[float, float, float],
) -> TopoDS_Shape:
    points = [
        (-half_width, -half_height),
        (half_width, -half_height),
        (half_width, half_height),
        (-half_width, half_height),
    ]
    return prism_from_plane_polygon(center, horizontal, vertical, points, extrusion, start_offset)


def hex_prism(
    center: tuple[float, float, float],
    horizontal: tuple[float, float, float],
    vertical: tuple[float, float, float],
    half_width: float,
    side_half_height: float,
    half_height: float,
    extrusion: tuple[float, float, float],
    start_offset: tuple[float, float, float],
) -> TopoDS_Shape:
    # Clockwise point-up hex: two vertical sides and 45-degree roof facets.
    points = [
        (0.0, half_height),
        (half_width, side_half_height),
        (half_width, -side_half_height),
        (0.0, -half_height),
        (-half_width, -side_half_height),
        (-half_width, side_half_height),
    ]
    return prism_from_plane_polygon(center, horizontal, vertical, points, extrusion, start_offset)


def original_grid_fillers(side_grid_tool: TopoDS_Shape) -> list[TopoDS_Shape]:
    # The first source pocket cuts 56 rounded-square prisms through both end
    # panels.  Reuse its exact tool so clipped cells along the angled outline
    # restore cleanly too.
    fillers: list[TopoDS_Shape] = [side_grid_tool]

    # x=0 back wall: original 20 x 20 mm rounded squares.
    for y in BIG_Y_CENTERS:
        for z in BIG_Z_CENTERS:
            fillers.append(axis_box(-0.5, y - 10.0, z - 10.0, 6.0, 20.0, 20.0))

    # y=0 bottom wall: original 10 x 10 mm rounded squares.
    for x in BOTTOM_X_CENTERS:
        for z in BOTTOM_Z_CENTERS:
            fillers.append(axis_box(x - 5.0, -0.5, z - 5.0, 10.0, 6.0, 10.0))

    # 25-degree wall: original 10 x 10 mm rounded squares.
    for t in ANGLED_T_CENTERS:
        for z in ANGLED_Z_CENTERS:
            center = (TANGENT[0] * t + NORMAL[0] * (-21.13091308703498),
                      TANGENT[1] * t + NORMAL[1] * (-21.13091308703498),
                      z)
            fillers.append(
                rectangle_prism(
                    center,
                    (0.0, 0.0, 1.0),
                    TANGENT,
                    5.0,
                    5.0,
                    tuple(6.0 * n for n in NORMAL),
                    tuple(-0.5 * n for n in NORMAL),
                )
            )
    return fillers


def hex_cutters() -> tuple[list[TopoDS_Shape], list[TopoDS_Shape], list[TopoDS_Shape], list[TopoDS_Shape]]:
    sides: list[TopoDS_Shape] = []
    back: list[TopoDS_Shape] = []
    bottom: list[TopoDS_Shape] = []
    angled: list[TopoDS_Shape] = []

    # Both z end panels.  The cell grid is clipped naturally by the basket's
    # angled cross-section, just like the author's original 8 x 8 pattern.
    side_x_centers = [30.0 + i * (160.0 / 7.0) for i in range(8)]
    for z, start_z, extrusion_z in ((0.0, -1.0, 7.0), (250.0, 1.0, -7.0)):
        for row, y in enumerate(BACK_ROW_CENTERS):
            xs = side_x_centers if row % 2 == 0 else [(a + b) / 2.0 for a, b in zip(side_x_centers, side_x_centers[1:])]
            for x in xs:
                sides.append(
                    hex_prism(
                        (x, y, z),
                        (1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                        BACK_HALF_WIDTH,
                        BACK_SIDE_HALF_HEIGHT,
                        BACK_HALF_HEIGHT,
                        (0.0, 0.0, extrusion_z),
                        (0.0, 0.0, start_z),
                    )
                )

    # Back wall.  Rows alternate between 9 and 8 openings for a honeycomb layout.
    for row, y in enumerate(BACK_ROW_CENTERS):
        zs = BIG_Z_CENTERS if row % 2 == 0 else [(a + b) / 2.0 for a, b in zip(BIG_Z_CENTERS, BIG_Z_CENTERS[1:])]
        for z in zs:
            back.append(
                hex_prism(
                    (0.0, y, z),
                    (0.0, 0.0, 1.0),
                    (0.0, 1.0, 0.0),
                    BACK_HALF_WIDTH,
                    BACK_SIDE_HALF_HEIGHT,
                    BACK_HALF_HEIGHT,
                    (7.0, 0.0, 0.0),
                    (-1.0, 0.0, 0.0),
                )
            )

    # Bottom wall.  The second row is offset half a cell along z.
    for row, x in enumerate(BOTTOM_X_CENTERS):
        zs = BOTTOM_Z_CENTERS if row == 0 else [(a + b) / 2.0 for a, b in zip(BOTTOM_Z_CENTERS, BOTTOM_Z_CENTERS[1:])]
        for z in zs:
            bottom.append(
                hex_prism(
                    (x, 0.0, z),
                    (0.0, 0.0, 1.0),
                    (1.0, 0.0, 0.0),
                    SMALL_HALF_WIDTH,
                    SMALL_SIDE_HALF_HEIGHT,
                    SMALL_HALF_HEIGHT,
                    (0.0, 7.0, 0.0),
                    (0.0, -1.0, 0.0),
                )
            )

    # Angled wall.  Rows run along its 25-degree tangent and alternate in z.
    for row, t in enumerate(ANGLED_T_CENTERS):
        zs = ANGLED_Z_CENTERS if row % 2 == 0 else [(a + b) / 2.0 for a, b in zip(ANGLED_Z_CENTERS, ANGLED_Z_CENTERS[1:])]
        center_xy = (
            TANGENT[0] * t + NORMAL[0] * (-21.13091308703498),
            TANGENT[1] * t + NORMAL[1] * (-21.13091308703498),
        )
        for z in zs:
            angled.append(
                hex_prism(
                    (center_xy[0], center_xy[1], z),
                    (0.0, 0.0, 1.0),
                    TANGENT,
                    SMALL_HALF_WIDTH,
                    SMALL_SIDE_HALF_HEIGHT,
                    SMALL_HALF_HEIGHT,
                    tuple(7.0 * n for n in NORMAL),
                    tuple(-1.0 * n for n in NORMAL),
                )
            )
    return sides, back, bottom, angled


def bounds(shape: TopoDS_Shape) -> tuple[float, float, float, float, float, float]:
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


def write_step(shape: TopoDS_Shape, path: Path) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"Could not write STEP: {path}")


def write_stl(shape: TopoDS_Shape, path: Path) -> None:
    BRepMesh_IncrementalMesh(shape, 0.12, False, 0.35, True).Perform()
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape, str(path)):
        raise RuntimeError(f"Could not write STL: {path}")
    # OCCT can emit a handful of coincident triangles at face seams.  They are
    # geometrically harmless but make mesh-only validators report non-manifold
    # edges.  Remove duplicate/degenerate faces before slicer handoff.
    import trimesh

    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    mesh.process(validate=True)
    path.write_bytes(mesh.export(file_type="stl"))


def print_ready(shape: TopoDS_Shape) -> TopoDS_Shape:
    # Exact rotation from the author's MakerWorld 3MF; translation is replaced
    # below so the result lands cleanly at the origin in any slicer.
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


def make_3mf(stl_path: Path, output_path: Path) -> None:
    import trimesh

    mesh = trimesh.load_mesh(stl_path, force="mesh")
    output_path.write_bytes(mesh.export(file_type="3mf"))


def main() -> None:
    if not SOURCE_FCSTD.exists():
        raise FileNotFoundError(f"Missing original source: {SOURCE_FCSTD}")

    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE_FCSTD) as archive:
        for name in (
            "Thickness.Shape.brp",
            "Pocket001.AddSubShape.brp",
            "Fillet.Shape.brp",
            "Hole.AddSubShape.brp",
        ):
            (WORK / name).write_bytes(archive.read(name))

    pregrid = read_brep(WORK / "Thickness.Shape.brp")
    side_grid_tool = read_brep(WORK / "Pocket001.AddSubShape.brp")
    source_fillet = read_brep(WORK / "Fillet.Shape.brp")
    source_hole_tool = read_brep(WORK / "Hole.AddSubShape.brp")

    filler_stock = run_boolean(
        BRepAlgoAPI_Common,
        pregrid,
        compound(original_grid_fillers(side_grid_tool)),
        "Restoring all five original square-grid regions...",
    )
    restored = run_boolean(
        BRepAlgoAPI_Fuse,
        source_fillet,
        filler_stock,
        "Merging restored wall material with the final source body...",
    )
    side_cutters, back_cutters, bottom_cutters, angled_cutters = hex_cutters()
    result = run_boolean(
        BRepAlgoAPI_Cut,
        restored,
        compound(side_cutters),
        "Cutting staggered 45-degree-roof hexagons in both end panels...",
    )
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError("End-panel hex cuts produced an invalid BREP")
    result = run_boolean(
        BRepAlgoAPI_Cut,
        result,
        compound(back_cutters),
        "Cutting staggered 45-degree-roof hexagons in the back wall...",
    )
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError("Back-wall hex cut produced an invalid BREP")
    result = run_boolean(
        BRepAlgoAPI_Cut,
        result,
        compound(bottom_cutters),
        "Cutting staggered hexagons in the bottom wall...",
    )
    if not BRepCheck_Analyzer(result).IsValid():
        raise RuntimeError("Bottom-wall hex cut produced an invalid BREP")
    result = run_boolean(
        BRepAlgoAPI_Cut,
        result,
        compound(angled_cutters),
        "Cutting staggered 45-degree-roof hexagons in the angled wall...",
    )
    result = run_boolean(
        BRepAlgoAPI_Cut,
        result,
        source_hole_tool,
        "Reapplying the four source mounting holes...",
    )

    analyzer = BRepCheck_Analyzer(result)
    if not analyzer.IsValid():
        raise RuntimeError("Generated BREP failed OpenCascade validity checks")
    if solid_count(result) != 1:
        raise RuntimeError(f"Expected one connected solid, found {solid_count(result)}")

    design_brep = OUTPUT / "closet-space-saver-hex-design.brep"
    design_step = OUTPUT / "closet-space-saver-hex-design.step"
    design_stl = OUTPUT / "closet-space-saver-hex-design.stl"
    ready_stl = OUTPUT / "closet-space-saver-hex-print-ready.stl"
    ready_3mf = OUTPUT / "closet-space-saver-hex-print-ready.3mf"

    BRepTools.Write_s(result, str(design_brep))
    write_step(result, design_step)
    write_stl(result, design_stl)
    write_stl(print_ready(result), ready_stl)
    make_3mf(ready_stl, ready_3mf)

    shutil.copy2(SOURCE_FCSTD, OUTPUT / "original-spacesaver9000.FCStd")
    xmin, ymin, zmin, xmax, ymax, zmax = bounds(result)
    print(
        f"Done: valid single solid, volume={volume(result):.1f} mm^3, "
        f"size=({xmax-xmin:.3f}, {ymax-ymin:.3f}, {zmax-zmin:.3f}) mm",
        flush=True,
    )
    print(f"Outputs: {OUTPUT}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
