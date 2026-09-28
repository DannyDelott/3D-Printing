#!/usr/bin/env python3
"""Generate clamping cauls for a 1-1/4 inch face cut with a Magnate 5869 bit.

The cutter's nominal profile is a 1-1/2 inch circular radius.  This model uses
the centered 1-1/4 inch segment of that circle and extrudes it into a 2 inch
long caul.  The flat clamp face is placed on Z=0 so the files print in their
intended orientation without supports.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from OCP.BRep import BRep_Builder
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon, BRepBuilderAPI_Transform
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.StlAPI import StlAPI_Writer
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shape
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec

from profile_interface import ATTACHMENT_TOP_CHAMFER, ATTACHMENT_WIDTH


INCH = 25.4
FACE_WIDTH = ATTACHMENT_WIDTH
PROFILE_RADIUS = 1.5 * INCH
CAUL_LENGTH = 2.0 * INCH
MINIMUM_THICKNESS = 0.75 * INCH
BACKED_CAUL_LENGTH = 250.0
BACKED_MINIMUM_THICKNESS = 4.0
CLAMP_FACE_CHAMFER = ATTACHMENT_TOP_CHAMFER
ARC_SEGMENTS = 96
PACK_GAP = 8.0

PROJECT = Path(__file__).resolve().parents[1]
MODELS = PROJECT / "models" / "clamping-cauls"
IMAGES = PROJECT / "images"


def crown_height(x: float) -> float:
    """Height of the centered circular crown above the board's two edges."""
    half_width = FACE_WIDTH / 2.0
    edge_height = math.sqrt(PROFILE_RADIUS**2 - half_width**2)
    return math.sqrt(PROFILE_RADIUS**2 - x**2) - edge_height


def make_caul(
    length: float = CAUL_LENGTH,
    minimum_thickness: float = MINIMUM_THICKNESS,
) -> TopoDS_Shape:
    half_width = FACE_WIDTH / 2.0
    sagitta = crown_height(0.0)
    overall_height = minimum_thickness + sagitta

    # Cross-section in X/Z.  Z=0 is the broad, flat clamp face and therefore
    # the build-plate face.  The circular contact surface faces upward while
    # printing; flip the finished part over for use.
    points: list[tuple[float, float]] = [
        (-half_width + CLAMP_FACE_CHAMFER, 0.0),
        (half_width - CLAMP_FACE_CHAMFER, 0.0),
        (half_width, CLAMP_FACE_CHAMFER),
        (half_width, overall_height),
    ]
    for index in range(1, ARC_SEGMENTS + 1):
        x = half_width - FACE_WIDTH * index / ARC_SEGMENTS
        points.append((x, overall_height - crown_height(x)))
    points.append((-half_width, CLAMP_FACE_CHAMFER))

    polygon = BRepBuilderAPI_MakePolygon()
    for x, z in points:
        polygon.Add(gp_Pnt(x, 0.0, z))
    polygon.Close()
    face = BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
    shape = BRepPrimAPI_MakePrism(face, gp_Vec(0.0, length, 0.0)).Shape()
    if not BRepCheck_Analyzer(shape).IsValid():
        raise RuntimeError("Generated caul is not a valid BREP solid")
    return shape


def translated(shape: TopoDS_Shape, x: float, y: float) -> TopoDS_Shape:
    transform = gp_Trsf()
    transform.SetTranslation(gp_Vec(x, y, 0.0))
    return BRepBuilderAPI_Transform(shape, transform, True).Shape()


def compound(shapes: list[TopoDS_Shape]) -> TopoDS_Compound:
    result = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(result)
    for shape in shapes:
        builder.Add(result, shape)
    return result


def make_four_pack(single: TopoDS_Shape) -> TopoDS_Compound:
    pitch_x = FACE_WIDTH + PACK_GAP
    pitch_y = CAUL_LENGTH + PACK_GAP
    return compound(
        [
            translated(single, 0.0, 0.0),
            translated(single, pitch_x, 0.0),
            translated(single, 0.0, pitch_y),
            translated(single, pitch_x, pitch_y),
        ]
    )


def write_step(shape: TopoDS_Shape, path: Path) -> None:
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError(f"Could not write {path}")


def write_stl(shape: TopoDS_Shape, path: Path) -> None:
    BRepMesh_IncrementalMesh(shape, 0.04, False, math.radians(0.35), True)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    if not writer.Write(shape, str(path)):
        raise RuntimeError(f"Could not write {path}")


def stl_to_3mf(stl_path: Path, output_path: Path) -> None:
    mesh = trimesh.load_mesh(stl_path, force="mesh", process=True)
    output_path.write_bytes(mesh.export(file_type="3mf"))


def bounds(shape: TopoDS_Shape) -> tuple[float, float, float, float, float, float]:
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    return box.Get()


def volume(shape: TopoDS_Shape) -> float:
    properties = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, properties)
    return properties.Mass()


def write_preview(single_stl: Path, path: Path) -> None:
    # Read the exported mesh as part of the preview path, then render the exact
    # generating surfaces rather than exposing a triangulation wire pattern.
    trimesh.load_mesh(single_stl, force="mesh", process=False)
    fig = plt.figure(figsize=(12, 7), facecolor="#f3efe7")
    grid = fig.add_gridspec(1, 2, width_ratios=[1.15, 1.0])

    ax3d = fig.add_subplot(grid[0, 0], projection="3d")
    half_width = FACE_WIDTH / 2.0
    overall_height = MINIMUM_THICKNESS + crown_height(0.0)
    x_surface = np.linspace(-half_width, half_width, 120)
    y_surface = np.linspace(0.0, CAUL_LENGTH, 32)
    x_grid, y_grid = np.meshgrid(x_surface, y_surface)
    z_line = np.array([overall_height - crown_height(float(x)) for x in x_surface])
    z_grid = np.tile(z_line, (len(y_surface), 1))
    ax3d.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        color="#e58b49",
        edgecolor="none",
        shade=True,
        antialiased=True,
    )
    bottom_x, bottom_y = np.meshgrid(
        np.linspace(-half_width, half_width, 2), np.linspace(0.0, CAUL_LENGTH, 2)
    )
    ax3d.plot_surface(
        bottom_x,
        bottom_y,
        np.zeros_like(bottom_x),
        color="#9e552d",
        edgecolor="none",
        shade=True,
    )
    wall_y, wall_z = np.meshgrid(
        np.linspace(0.0, CAUL_LENGTH, 2), np.linspace(0.0, overall_height, 2)
    )
    for wall_x in (-half_width, half_width):
        ax3d.plot_surface(
            np.full_like(wall_y, wall_x),
            wall_y,
            wall_z,
            color="#ba6733",
            edgecolor="none",
            shade=True,
        )
    # End caps are drawn as narrow quads to keep the shallow circular profile
    # visually legible in a headless matplotlib render.
    cap_quads = []
    for end_y in (0.0, CAUL_LENGTH):
        for index in range(len(x_surface) - 1):
            cap_quads.append(
                [
                    (x_surface[index], end_y, 0.0),
                    (x_surface[index + 1], end_y, 0.0),
                    (x_surface[index + 1], end_y, z_line[index + 1]),
                    (x_surface[index], end_y, z_line[index]),
                ]
            )
    ax3d.add_collection3d(
        Poly3DCollection(cap_quads, facecolor="#c86f35", edgecolor="none", alpha=1.0)
    )
    ax3d.set_xlim(-half_width, half_width)
    ax3d.set_ylim(0.0, CAUL_LENGTH)
    ax3d.set_zlim(0, overall_height * 1.15)
    ax3d.set_box_aspect((FACE_WIDTH, CAUL_LENGTH, MINIMUM_THICKNESS * 1.6))
    ax3d.view_init(elev=27, azim=-58)
    ax3d.set_axis_off()
    ax3d.set_title("Print orientation · flat clamp face down", fontsize=13, pad=12)

    ax = fig.add_subplot(grid[0, 1])
    xs = np.linspace(-FACE_WIDTH / 2.0, FACE_WIDTH / 2.0, 400)
    crown = np.array([crown_height(float(x)) for x in xs])
    contact = MINIMUM_THICKNESS + crown_height(0.0) - crown
    ax.fill_between(xs, 0, contact, color="#e58b49", alpha=0.95)
    ax.plot(xs, contact, color="#743d27", linewidth=2.0, label="1½″ radius contact arc")
    ax.plot(xs, np.full_like(xs, MINIMUM_THICKNESS), "--", color="#3c6e71", linewidth=1.3)
    ax.annotate(
        f"crown = {crown_height(0.0):.2f} mm",
        xy=(0, MINIMUM_THICKNESS),
        xytext=(0, MINIMUM_THICKNESS - 6.0),
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#3c6e71"},
        color="#2f5557",
    )
    ax.set_xlim(-FACE_WIDTH / 2.0 - 2.0, FACE_WIDTH / 2.0 + 2.0)
    ax.set_ylim(-1.0, contact.max() + 2.0)
    ax.set_aspect("equal")
    ax.set_xlabel("31.75 mm / 1¼″ face")
    ax.set_ylabel("mm")
    ax.set_title("Centered profile cross-section", fontsize=13, pad=12)
    ax.grid(alpha=0.18)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Magnate 5869 profile clamping caul", fontsize=18, fontweight="bold")
    fig.text(
        0.5,
        0.025,
        "50.8 mm / 2″ long · 19.05 mm / ¾″ minimum body thickness · support-free",
        ha="center",
        fontsize=11,
        color="#4f4a43",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def write_backed_preview(path: Path, reduction_percent: float) -> None:
    """Show the 250 mm profile adapter as used beneath a stiff 2x4 backer."""
    fig, (ax_plan, ax_profile) = plt.subplots(
        1,
        2,
        figsize=(13, 6.5),
        facecolor="#f3efe7",
        gridspec_kw={"width_ratios": [1.2, 1.0]},
    )
    for axis in (ax_plan, ax_profile):
        axis.set_facecolor("#fbfaf7")

    ax_plan.add_patch(
        Rectangle(
            (0.0, 0.0),
            BACKED_CAUL_LENGTH,
            FACE_WIDTH,
            facecolor="#e58b49",
            edgecolor="#743d27",
            linewidth=2.0,
        )
    )
    ax_plan.annotate(
        "250 mm",
        xy=(0.0, FACE_WIDTH + 6.0),
        xytext=(BACKED_CAUL_LENGTH, FACE_WIDTH + 6.0),
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "<->", "color": "#3c6e71"},
        color="#2f5557",
        fontsize=12,
    )
    ax_plan.annotate(
        "31.75 mm",
        xy=(BACKED_CAUL_LENGTH + 7.0, 0.0),
        xytext=(BACKED_CAUL_LENGTH + 7.0, FACE_WIDTH),
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "<->", "color": "#3c6e71"},
        color="#2f5557",
        fontsize=11,
    )
    ax_plan.text(
        BACKED_CAUL_LENGTH / 2.0,
        FACE_WIDTH / 2.0,
        "continuous caul",
        ha="center",
        va="center",
        color="white",
        fontsize=13,
        fontweight="bold",
    )
    ax_plan.set_xlim(-8.0, BACKED_CAUL_LENGTH + 24.0)
    ax_plan.set_ylim(-10.0, FACE_WIDTH + 19.0)
    ax_plan.set_aspect("equal")
    ax_plan.set_axis_off()
    ax_plan.set_title("Bed-maximizing plan view", fontsize=14, pad=14)

    half_width = FACE_WIDTH / 2.0
    overall_height = BACKED_MINIMUM_THICKNESS + crown_height(0.0)
    xs = np.linspace(-half_width, half_width, 300)
    contact = -np.array([overall_height - crown_height(float(x)) for x in xs])
    caul_points = [(-half_width, 0.0), (half_width, 0.0)]
    caul_points.extend((float(x), float(y)) for x, y in zip(xs[::-1], contact[::-1]))
    ax_profile.add_patch(
        MplPolygon(caul_points, closed=True, facecolor="#e58b49", edgecolor="#743d27", linewidth=2.0)
    )

    # A 2x4 laid flat is shown at its 3.5 inch width; the caul also works with
    # the 2x4 on edge because only the centered flat contact is important.
    two_by_four_width = 3.5 * INCH
    ax_profile.add_patch(
        Rectangle(
            (-two_by_four_width / 2.0, 0.0),
            two_by_four_width,
            13.0,
            facecolor="#d7b47b",
            edgecolor="#7f6540",
            linewidth=1.8,
        )
    )
    ax_profile.text(0.0, 6.5, "2×4 stiff backer", ha="center", va="center", color="#4b3925", fontsize=12)
    ax_profile.fill_between(xs, contact - 8.0, contact, color="#9eaaa8", alpha=0.9)
    ax_profile.plot(xs, contact, color="#f7d36d", linewidth=2.5, label="veneer / contact face")
    ax_profile.annotate(
        "4 mm minimum",
        xy=(0.0, -BACKED_MINIMUM_THICKNESS),
        xytext=(25.0, -2.0),
        arrowprops={"arrowstyle": "->", "color": "#3c6e71"},
        color="#2f5557",
        fontsize=11,
    )
    ax_profile.set_xlim(-two_by_four_width / 2.0 - 4.0, two_by_four_width / 2.0 + 4.0)
    ax_profile.set_ylim(contact.min() - 10.0, 16.0)
    ax_profile.set_aspect("equal")
    ax_profile.set_axis_off()
    ax_profile.set_title("Glue-up cross-section", fontsize=14, pad=14)

    fig.suptitle("250 mm lightweight profile caul for a 2×4 backer", fontsize=19, fontweight="bold")
    fig.text(
        0.5,
        0.025,
        f"Exact 1½″ radius contact · support-free · {reduction_percent:.0f}% less modeled material than the full-height version",
        ha="center",
        fontsize=11,
        color="#4f4a43",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.93))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


def verify_mesh(path: Path, expected_bodies: int) -> str:
    # STL stores independent triangle vertices; merge coincident vertices before
    # asking topology questions so the check reflects the actual closed shell.
    mesh = trimesh.load_mesh(path, force="mesh", process=True)
    body_count = len(mesh.split(only_watertight=False))
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise RuntimeError(f"Mesh verification failed for {path.name}")
    if body_count != expected_bodies:
        raise RuntimeError(f"Expected {expected_bodies} bodies in {path.name}, got {body_count}")
    extents = mesh.extents
    return (
        f"{path.name}: {extents[0]:.3f} x {extents[1]:.3f} x {extents[2]:.3f} mm, "
        f"bodies={body_count}, watertight={mesh.is_watertight}, "
        f"winding={mesh.is_winding_consistent}"
    )


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)

    single = make_caul()
    four_pack = make_four_pack(single)
    backed = make_caul(BACKED_CAUL_LENGTH, BACKED_MINIMUM_THICKNESS)
    full_height_250 = make_caul(BACKED_CAUL_LENGTH, MINIMUM_THICKNESS)
    single_step = MODELS / "magnate-5869-caul.step"
    single_stl = MODELS / "magnate-5869-caul.stl"
    single_3mf = MODELS / "magnate-5869-caul.3mf"
    pack_stl = MODELS / "magnate-5869-caul-4-pack.stl"
    pack_3mf = MODELS / "magnate-5869-caul-4-pack.3mf"
    backed_step = MODELS / "magnate-5869-caul-250mm-2x4-backed.step"
    backed_stl = MODELS / "magnate-5869-caul-250mm-2x4-backed.stl"
    backed_3mf = MODELS / "magnate-5869-caul-250mm-2x4-backed.3mf"

    write_step(single, single_step)
    write_stl(single, single_stl)
    stl_to_3mf(single_stl, single_3mf)
    write_stl(four_pack, pack_stl)
    stl_to_3mf(pack_stl, pack_3mf)
    write_preview(single_stl, IMAGES / "magnate-5869-caul-preview.png")

    write_step(backed, backed_step)
    write_stl(backed, backed_stl)
    stl_to_3mf(backed_stl, backed_3mf)
    reduction_percent = 100.0 * (1.0 - volume(backed) / volume(full_height_250))
    write_backed_preview(
        IMAGES / "magnate-5869-caul-250mm-2x4-backed-preview.png",
        reduction_percent,
    )

    print(f"Nominal profile radius: {PROFILE_RADIUS:.3f} mm")
    print(f"Face width: {FACE_WIDTH:.3f} mm")
    print(f"Centered crown: {crown_height(0.0):.3f} mm")
    print(f"BREP valid: {BRepCheck_Analyzer(single).IsValid()}")
    print(f"BREP volume: {volume(single):.1f} mm^3")
    print(f"BREP bounds: {tuple(round(value, 3) for value in bounds(single))}")
    print(verify_mesh(single_stl, 1))
    print(verify_mesh(pack_stl, 4))
    print(f"250 mm backed caul BREP valid: {BRepCheck_Analyzer(backed).IsValid()}")
    print(f"250 mm backed caul volume: {volume(backed):.1f} mm^3")
    print(f"250 mm full-height baseline volume: {volume(full_height_250):.1f} mm^3")
    print(f"Modeled material reduction: {reduction_percent:.1f}%")
    print(verify_mesh(backed_stl, 1))


if __name__ == "__main__":
    main()
