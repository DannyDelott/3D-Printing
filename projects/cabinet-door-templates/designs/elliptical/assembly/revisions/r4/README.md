# Vertical maple panels R4

R4 retains the preferred R3 A rails (2¼ / 4½ inch ends) and replaces walnut with vertically segmented maple, with curly and quilted figure options. Two panel layouts share the same case, door frame, mortised knives, tiger's-eye-style knob, open back and recessed French cleat. Previous revisions are unchanged.

| Layout | Boards | Nominal seam layout |
| --- | --- | --- |
| Broad verticals | Three | 4½ inch center bay; two outer boards fitted to the retained opening |
| Narrow center | Five | 1½ inch center bay, 3 inch adjacent bays, outer boards fitted to the retained opening |

These are seam-center dimensions. The 1 mm face gaps reduce visible board widths. The outer boards absorb the original door reveal and panel-groove engagement; they are not forced to an exact module at the expense of fit. No horizontal crossbar or contrasting center inlay is used. The narrow center suggests the vertical pupil of the user's dragon-eye inspiration through proportion alone.

## Retained dimensions

- Case and door: 18 × 27 × 6 in (457.2 × 685.8 × 152.4 mm), knob excluded.
- Case and rails: ¾ in thick; stiles 2¼ in wide × ⅝ in thick, with ⅛ in recessed fronts.
- Three 1:6 dovetails at each corner; tails on the vertical sides, pins on top and bottom.
- Original q=0.95 asymmetric ellipse family; R3 A's lighter rail proportions.
- Open back; recessed ¾ inch thick, 2¼ inch high cabinet cleat and mating 45-degree wall member. Interior depth below it is 130.35 mm, recovering the prior back's 19.05 mm thickness.
- Assumed stone diameter 1½ in; projection ¾ in from the stile. Total including knob: 6⅝ in.

## Panel construction represented

The maple field is divided into separate, overlapping solids. Each vertical joint has opposing half-depth rabbets: the front seam and rear shoulder are staggered. The remaining overlap is 5.70 mm, so the modeled seam does not form a straight opening through to the wall. The curved ends engage the existing top and bottom grooves; the outside boards engage the stile grooves. Interior boards do not have separate four-sided beech frames.

The panel remains the prior assumed 6.10 mm thick stock in 6.35 mm wide × 6.35 mm deep grooves. Face gaps are assumed 1 mm; nominal lap length is 6.35 mm; face clearance is 0.10 mm and shoulder clearance is 0.15 mm. Outer perimeter clearance remains 2 mm at the groove bottoms. The approximately 3 mm lap tongues are thin. This is an editable joinery study, not a verified machining schedule: confirm lap durability, actual stock, moisture movement, board retention and groove allowance before fabrication. Do not infer a seasonal-movement allowance from the appearance of the seams alone.

The ¾ inch module governs the new board layout and retained major design proportions. Machining clearances, panel thickness and previously specified grooves/stiles remain exceptions. Rail/stile corner joinery, cleat attachment and wall fasteners remain unspecified.

## Material reference

[Curly maple, The Wood Database](https://www.wood-database.com/curly-maple/) describes curl as a figure pattern rather than a separate species, generally running perpendicular to the longitudinal grain. The viewer uses pale cream/honey color, vertical fibers and restrained transverse curl based on the user's reference. Figure is continuous across the modeled field for visual comparison; actual board matching, figure, species and finish remain to be selected. This is procedural shading, not a scan of chosen stock or AI-generated imagery. The curly-maple reference photographs are not redistributed. The quilted option uses the user-supplied photograph in `textures/quilted-maple-reference.png`, mapped at its original aspect ratio on the broad panel faces. A nominal 350 mm image width is an illustrative figure scale, not a verified board dimension. The image repeats with mirrored edges; it is not a scan of selected stock, and its baked lighting does not simulate real chatoyance. The CAD downloads represent the same maple-board geometry for either figure choice; existing CAD metadata records the original curly-maple study.

Beech and the stone retain the previous revision's procedural materials. Three.js and OrbitControls retain the MIT license in `vendor/LICENSE.txt`.

## Checks and files

Each layout has its own STEP, 3MF, STL, mesh data, parameters, geometry report and Bambu Studio importer report. Geometry checks cover cabinet size, valid solids, watertight meshes, STEP reimport, board-to-board and panel-to-frame overlap, cleat fit, dovetails and nine sampled hinge positions through 110 degrees. They do not establish structural capacity or physical machining fit.

Open `index.html` for the interactive comparison. Panel detail and exploded views expose the seam and overlap. These are full-size woodworking references, not arranged printer projects.

Rebuild using CadQuery 2.8, Shapely 2 and trimesh:

```
python source/build_model.py a
python source/build_model.py b
npx esbuild source/viewer.js --bundle --format=iife --minify --outfile=viewer.js
```

On the original machine, the interpreter is `closet-space-saver-hex/.venv/bin/python3` from the repository root. Refresh the viewer's version hash, front screenshots and catalog/download thumbnails after regeneration.
