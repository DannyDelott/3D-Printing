#!/usr/bin/env python3
"""Generate a rounded, single-body eighth-circle drawing stencil."""

from __future__ import annotations

import math
from pathlib import Path

import trimesh
from shapely.affinity import affine_transform, translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


INCH = 25.4
RADII_INCHES = range(1, 11)
RAIL_WIDTH = 0.5 * INCH
SPINE_WIDTH = 6.0
BODY_HEIGHT = 3.2
LABEL_HEIGHT = 0.4
ARC_START_DEGREES = 22.5
ARC_DEGREES = 45.0
ARC_SEGMENTS = 180
CORNER_RADIUS = 1.5
LABEL_GLYPH_HEIGHT = 4.0
LABEL_EDGE_MARGIN = 1.2

PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_DIR / "models" / "eighth-circle-stencil-1-to-10-inch.stl"
PREVIEW_PATH = PROJECT_DIR / "images" / "eighth-circle-stencil-preview.svg"

Point2 = tuple[float, float]


def cross_2d(a: Point2, b: Point2) -> float:
    return a[0] * b[1] - a[1] * b[0]


def annular_sector(outer_radius: float, width: float) -> Polygon:
    inner_radius = outer_radius - width
    angles = [
        math.radians(ARC_START_DEGREES + ARC_DEGREES * i / ARC_SEGMENTS)
        for i in range(ARC_SEGMENTS + 1)
    ]
    outer = [(outer_radius * math.cos(a), outer_radius * math.sin(a)) for a in angles]
    inner = [(inner_radius * math.cos(a), inner_radius * math.sin(a)) for a in reversed(angles)]
    return Polygon(outer + inner)


def boundary_spine(
    boundary_degrees: float, opposite_degrees: float, inward_side: float, radius: float
) -> Polygon:
    """Create a constant-width radial spine clipped inside the sector."""
    boundary_angle = math.radians(boundary_degrees)
    opposite_angle = math.radians(opposite_degrees)
    direction = (math.cos(boundary_angle), math.sin(boundary_angle))
    opposite = (math.cos(opposite_angle), math.sin(opposite_angle))
    inward_normal = (
        inward_side * -math.sin(boundary_angle),
        inward_side * math.cos(boundary_angle),
    )
    offset = (SPINE_WIDTH * inward_normal[0], SPINE_WIDTH * inward_normal[1])
    denominator = cross_2d(direction, opposite)
    intersection_distance = cross_2d((-offset[0], -offset[1]), direction) / denominator
    near_inner = (intersection_distance * opposite[0], intersection_distance * opposite[1])
    parallel_length = math.sqrt(radius**2 - SPINE_WIDTH**2)
    far_inner = (
        parallel_length * direction[0] + offset[0],
        parallel_length * direction[1] + offset[1],
    )
    far_boundary = (radius * direction[0], radius * direction[1])
    return Polygon([(0.0, 0.0), far_boundary, far_inner, near_inner])


STROKE_DIGITS: dict[str, list[list[Point2]]] = {
    "0": [[(0.5, 0.3), (0.1, 0.8), (0.1, 3.2), (0.5, 3.7), (2.2, 3.7), (2.6, 3.2), (2.6, 0.8), (2.2, 0.3), (0.5, 0.3)]],
    "1": [[(0.5, 3.1), (1.3, 3.7), (1.3, 0.3)], [(0.5, 0.3), (2.1, 0.3)]],
    "2": [[(0.1, 3.2), (0.5, 3.7), (2.2, 3.7), (2.6, 3.2), (2.6, 2.5), (0.1, 0.3), (2.6, 0.3)]],
    "3": [[(0.1, 3.7), (2.2, 3.7), (2.6, 3.3), (2.6, 2.4), (2.2, 2.0), (1.1, 2.0), (2.2, 2.0), (2.6, 1.6), (2.6, 0.7), (2.2, 0.3), (0.1, 0.3)]],
    "4": [[(0.2, 3.7), (0.2, 2.0), (2.6, 2.0)], [(2.2, 3.7), (2.2, 0.3)]],
    "5": [[(2.6, 3.7), (0.2, 3.7), (0.2, 2.0), (2.1, 2.0), (2.6, 1.5), (2.6, 0.8), (2.2, 0.3), (0.2, 0.3)]],
    "6": [[(2.5, 3.5), (2.1, 3.7), (0.6, 3.7), (0.2, 3.2), (0.2, 0.8), (0.6, 0.3), (2.1, 0.3), (2.6, 0.8), (2.6, 1.5), (2.1, 2.0), (0.2, 2.0)]],
    "7": [[(0.1, 3.7), (2.6, 3.7), (1.0, 0.3)]],
    "8": [[(0.6, 2.0), (0.2, 2.4), (0.2, 3.2), (0.6, 3.7), (2.1, 3.7), (2.5, 3.2), (2.5, 2.4), (2.1, 2.0), (0.6, 2.0), (0.2, 1.6), (0.2, 0.8), (0.6, 0.3), (2.1, 0.3), (2.5, 0.8), (2.5, 1.6), (2.1, 2.0)]],
    "9": [[(2.5, 2.0), (0.6, 2.0), (0.2, 2.5), (0.2, 3.2), (0.6, 3.7), (2.1, 3.7), (2.5, 3.2), (2.5, 0.8), (2.1, 0.3), (0.4, 0.3)]],
}


def digit_shapes(digit: str, x: float) -> list[Polygon]:
    stroke_radius = 0.34
    return [
        translate(
            LineString(path).buffer(
                stroke_radius, cap_style="round", join_style="round", quad_segs=6
            ),
            xoff=x,
        )
        for path in STROKE_DIGITS[digit]
    ]


def label_shapes(text: str) -> tuple[list[Polygon], float]:
    glyphs: list[Polygon] = []
    cursor = 0.0
    for character in text:
        if character.isdigit():
            glyphs.extend(digit_shapes(character, cursor))
            cursor += 3.35
        elif character == ".":
            glyphs.append(Point(cursor + 0.35, 0.35).buffer(0.35, quad_segs=8))
            cursor += 1.05
        else:
            raise ValueError(f"Unsupported label character: {character}")
    return glyphs, cursor


def place_shape(
    shape: Polygon, baseline_radius: float, angle_degrees: float, total_width: float
) -> Polygon:
    angle = math.radians(angle_degrees)
    tangent = (-math.sin(angle), math.cos(angle))
    radial = (math.cos(angle), math.sin(angle))
    centered = translate(shape, xoff=-total_width / 2.0)
    return affine_transform(
        centered,
        [
            tangent[0],
            radial[0],
            tangent[1],
            radial[1],
            baseline_radius * radial[0],
            baseline_radius * radial[1],
        ],
    )


def round_corners(shape: Polygon) -> Polygon:
    # Opening rounds exposed convex corners; closing rounds the corners of the
    # open spaces between rails. Smooth circular tracing edges remain unchanged.
    opened = shape.buffer(-CORNER_RADIUS, join_style="round", quad_segs=10).buffer(
        CORNER_RADIUS, join_style="round", quad_segs=10
    )
    return opened.buffer(CORNER_RADIUS, join_style="round", quad_segs=10).buffer(
        -CORNER_RADIUS, join_style="round", quad_segs=10
    )


def build_profiles() -> tuple[Polygon, Polygon]:
    maximum_radius = max(RADII_INCHES) * INCH
    end_degrees = ARC_START_DEGREES + ARC_DEGREES
    pieces = [annular_sector(radius * INCH, RAIL_WIDTH) for radius in RADII_INCHES]
    pieces.extend(
        [
            boundary_spine(ARC_START_DEGREES, end_degrees, 1.0, maximum_radius),
            boundary_spine(end_degrees, ARC_START_DEGREES, -1.0, maximum_radius),
        ]
    )

    body = round_corners(unary_union(pieces))

    # Raised labels begin at a single layer boundary, making a color change easy.
    label_angle = ARC_START_DEGREES + ARC_DEGREES / 2.0
    cutouts: list[Polygon] = []
    for radius_inches in RADII_INCHES:
        radius = radius_inches * INCH
        labels = [(f"{radius_inches}", radius - LABEL_EDGE_MARGIN - LABEL_GLYPH_HEIGHT)]
        if radius_inches > 1:
            labels.append(
                (f"{radius_inches - 0.5:.1f}", radius - RAIL_WIDTH + LABEL_EDGE_MARGIN)
            )
        for text, baseline_radius in labels:
            glyphs, width = label_shapes(text)
            cutouts.extend(
                place_shape(glyph, baseline_radius, label_angle, width) for glyph in glyphs
            )

    label_profile = unary_union(cutouts)

    profile = body
    if profile.geom_type != "Polygon" or not profile.is_valid or not label_profile.is_valid:
        raise ValueError("Generated profiles are invalid")

    min_x, min_y, _, _ = profile.bounds
    offset = (-min_x, -min_y)
    return (
        translate(profile, xoff=offset[0], yoff=offset[1]),
        translate(label_profile, xoff=offset[0], yoff=offset[1]),
    )


def geometry_paths(geometry, ring_path) -> list[str]:
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    paths: list[str] = []
    for polygon in polygons:
        paths.append(ring_path(list(polygon.exterior.coords)))
        paths.extend(ring_path(list(interior.coords)) for interior in polygon.interiors)
    return paths


def write_preview(profile: Polygon, labels, path: Path) -> None:
    canvas = 760
    margin = 34
    min_x, min_y, max_x, max_y = profile.bounds
    scale = (canvas - 2 * margin) / max(max_x - min_x, max_y - min_y)

    def ring_path(coords: list[Point2]) -> str:
        points = [(margin + x * scale, margin + y * scale) for x, y in coords]
        return "M " + " L ".join(f"{x:.3f} {y:.3f}" for x, y in points) + " Z"

    body_paths = geometry_paths(profile, ring_path)
    label_paths = geometry_paths(labels, ring_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas}" height="{canvas}" viewBox="0 0 {canvas} {canvas}">',
                f'<rect width="{canvas}" height="{canvas}" fill="#f4f0e8"/>',
                f'<g transform="translate(0 {canvas}) scale(1 -1)">',
                f'<path d="{" ".join(body_paths)}" fill="#3f4850" fill-rule="evenodd"/>',
                f'<path d="{" ".join(label_paths)}" fill="#eadb9b" fill-rule="evenodd"/>',
                "</g>",
                "</svg>",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def validate(profile: Polygon, mesh: trimesh.Trimesh) -> None:
    width = profile.bounds[2] - profile.bounds[0]
    height = profile.bounds[3] - profile.bounds[1]
    if width > 245.0 or height > 245.0:
        raise ValueError(f"Footprint {width:.3f} x {height:.3f} mm exceeds 245 mm target")
    if not mesh.is_watertight:
        raise ValueError("Generated mesh is not watertight")
    print(
        f"footprint: {width:.3f} x {height:.3f} x "
        f"{BODY_HEIGHT + LABEL_HEIGHT:.3f} mm"
    )
    print(f"triangles: {len(mesh.faces):,}")
    print("watertight bodies: 1")


def extrude_geometries(geometry, height: float) -> list[trimesh.Trimesh]:
    polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    return [
        trimesh.creation.extrude_polygon(polygon, height=height, engine="earcut")
        for polygon in polygons
    ]


def main() -> None:
    profile, labels = build_profiles()
    base_mesh = trimesh.creation.extrude_polygon(profile, height=BODY_HEIGHT, engine="earcut")
    label_meshes = extrude_geometries(labels, LABEL_HEIGHT + 0.05)
    for label_mesh in label_meshes:
        label_mesh.apply_translation((0.0, 0.0, BODY_HEIGHT - 0.05))
    mesh = trimesh.boolean.union([base_mesh, *label_meshes], engine="manifold")
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    validate(profile, mesh)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(MODEL_PATH, file_type="stl")
    write_preview(profile, labels, PREVIEW_PATH)
    print(f"wrote: {MODEL_PATH}")
    print(f"wrote: {PREVIEW_PATH}")


if __name__ == "__main__":
    main()
