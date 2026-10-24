# Cabinet assembly R2

18 × 27 × 6 inch overall cabinet, including its overlay door (excluding the projecting knob). European quartersawn beech case and frame; contrasting walnut panel.

Open `index.html` for the interactive assembly and dimensioned sections. Download `cabinet-r2.step` for exact CAD solids or `cabinet-r2.3mf` for the full-size assembly mesh. The 3MF is a woodworking dimensional reference, not an arranged printer project.

## Confirmed changes

- 457.2 × 685.8 × 152.4 mm overall (18 × 27 × 6 inches).
- 19.05 mm (3/4 inch) case and rails.
- 15.875 mm (5/8 inch) stiles, backs aligned to rails: 3.175 mm (1/8 inch) front shadow line.
- Mortised knife hinges.
- Quarter-inch panel grooves on both stiles and both curved rails.
- Three through-dovetails at each corner: vertical sides carry the tails; top and bottom carry the pins. Twelve tails total.

## Retained geometry and assumptions

The asymmetric rails retain the original exact q=0.95 ellipse family and 3/6 inch end heights. The overlay door remains 17 7/8 inches wide, with assumed 1/16 inch side reveals; the original 15 7/8 inch templates remain unchanged and are not compatible with this wider door. Stile width remains 2 1/4 inches.

The 3 mm face gap is assumed. Case depth is derived, not independently chosen: 152.4 − 19.05 − 3 = 130.35 mm. The back is modeled as 3/4 inch stock. The simple round knob is restored with an 18 mm projection from the stile. The six-inch depth describes the case and door; including the knob, depth is 167.225 mm (6.584 inches).

Walnut is selected for contrast. Grooves are 6.35 mm wide and 6.35 mm deep; groove depth is assumed. They share a common Z position through all four frame members, centered within the thinner stiles. The walnut panel is 6.10 mm thick for 0.25 mm total thickness clearance. Its outline extends 4.35 mm into the grooves, leaving 2 mm at the groove bottoms. The offset follows the curved boundaries and has rounded corners. These are design allowances; actual solid-wood moisture movement and final stock dimensions still need checking. The panel is not glued to the groove walls.

Dovetail slope is user-specified 1:6. Joint surfaces are nominal mating geometry without a machining-fit allowance. Frame corner joinery and back fastening remain unspecified.

## Mortised knife geometry

Both fixed and moving leaves are recessed, with no projecting mounting pads. Fixed leaves are flush to the case top/bottom, and moving leaves sit deeper in edge mortises. Their vertical pivot is inset from the door's right edge by half the 12.7 mm leaf width. Clearance pockets in the rail edges accommodate the stationary leaf over 0–110 degrees. The sweep envelope is sampled at one degree and buffered 0.3 mm; moving-leaf mortises have 0.15 mm lateral clearance. The bearing gap is 0.8 mm and leaves are 3.2 mm thick.

This is custom mounting geometry, not a commercially specified Brusso hinge. Leaf sizes, screw design, stiffness, loading and pivot retention remain unverified. Do not use the model as a drilling template for purchased hardware. The model tests space and movement rather than hardware suitability.

## Validation

`validation.json` records overall dimensions, tail count, groove engagement, mesh watertightness, STEP reimport and sampled full-assembly hinge collisions. Panel/frame and tail/pin solids are checked for volumetric overlap. Mesh geometry is validated through Bambu's importer in `import-check.json`.

## Rebuild

Requires CadQuery 2.8 / OpenCascade, Shapely 2, trimesh, and esbuild. Inputs live in `source/parameters.json`.

```
python source/build_model.py
npx esbuild source/viewer.js --bundle --format=iife --minify --outfile=viewer.js
```

On the original machine use the existing CAD interpreter at `closet-space-saver-hex/.venv/bin/python3` from the repository root. The source generator creates the STEP, STL, 3MF, geometry checks and viewer mesh data together. Update the static datasheet labels if changing parameters. `standalone.html` embeds the current viewer bundle for local use.

R1 remains in the prior chat's output package. No existing routing-template geometry or native Bambu projects were modified. This revision is registered separately in the design manifest and site catalog.

Original curve sources: `projects/cabinet-door-templates/source/generate_ellipse.py`, `generate_stiles.py`, and `front_views.py`. Three.js and OrbitControls are copied from the library's vendored runtime; MIT license retained in `vendor/LICENSE.txt`.

Rendering uses crease-preserving normals. Smoothing across welded CAD corners previously caused false gradients on planar wood faces; the normal check in `source/check_viewer_normals.js` guards against that regression. The pivot guide is off by default.

End grain is shaded from each board’s longitudinal axis, with slightly darker cut ends, fine growth rings and pores. This is procedural material shading, not an image texture. The 1:6 dovetail slope is recorded in the geometry parameters and validation.

Material reference: [European beech, The Wood Database](https://www.wood-database.com/european-beech/), including the user-supplied face-grain sample and 1× endgrain photograph. Warm straw/pink-brown color, lengthwise grain, small ray flecks and endgrain bands are represented procedurally; reference photographs are not redistributed. Grain contrast is increased throughout the model at the user’s request.
