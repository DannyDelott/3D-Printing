# Broad Center crown comparison · R7

Compare the previous ⅛-inch front crown with a fuller ¼-inch crown. Both use the same approved Broad Center layout, flat backs, flat grooves/laps and unchanged case. The saved flat door remains in R5 B and R6 A; R6 is preserved unchanged.

| Dimension | A · Previous crown | B · Fuller crown |
| --- | --- | --- |
| Front crown (proposed) | ⅛ inch / 3.175 mm | ¼ inch / 6.35 mm |
| Case + door W × H × D | 18 × 27 × 6⅛ inches | 18 × 27 × 6¼ inches |
| Metric envelope | 457.2 × 685.8 × 155.575 mm | 457.2 × 685.8 × 158.75 mm |
| Case depth | 130.35 mm | 130.35 mm |
| Rails at crown | ⅞ inch / 22.225 mm | 1 inch / 25.4 mm |
| Rails at outside edges | ¾ inch / 19.05 mm | ¾ inch / 19.05 mm |
| Panel at crown* | 9.275 mm | 12.450 mm |
| Panel base / groove tongue* | 6.10 mm | 6.10 mm |

Depth excludes the knob. Both crowns are circular across the 17⅞-inch width, with no vertical curvature. The quarter-inch crown and corresponding 6¼-inch depth are proposed in response to the previous curve being too subtle. The user confirmed the flat-back construction and retaining the case; the greater depth is shown for comparison. The profile drawing exaggerates depth 2.5× and is labeled; 3D and downloads are at actual scale. Maximum finished thicknesses exclude machining allowance.

## Construction

Use thicker beech blanks and plane or rout the exposed front to the crown, keeping the rear face flat. The original flat grooves and hinge mortises remain. The same crown is applied to the rails, stiles and three maple faces, preserving the rail/stile step without a separate raised middle panel. Blank stock needs additional machining allowance beyond the finished maximums above.

For the veneer-over-core panels, shape the thicker core before applying the 3/32-inch quilted-maple veneer. Do not remove the front crown from an already flat 3/32-inch veneer: that would exceed its thickness. CAD represents the finished composite surface; core material, balancing back, veneer-forming method, adhesive and edge treatment remain unspecified. This shallow geometry does not establish whether the actual quilted veneer can conform without cracking; make a shop sample. Groove tongues and rear lap planes stay at the original dimensions, with the extra face thickness confined to the visible opening. There is no need for coopered staves in this geometry.

The 6-inch center bay and original asymmetric rail silhouette are retained. Side bays are approximately 3¾ inches before fitting. The ¾-inch module still controls major proportions; crown, reveals, stock thicknesses and fitting details are explicit exceptions.

## Perimeter channel and fit

The perimeter channel follows the front crown and curved opening: 1/16 inch (1.5875 mm) wide and 1/64 inch (0.396875 mm) deep, measured in the front-to-back direction. With 3/32-inch (2.38125 mm) face veneer, the nominal remaining thickness is 5/64 inch (1.984375 mm). It does not extend along the two internal seams. Thicknesses are measured front-to-back; the very shallow local surface angle makes normal thickness slightly smaller.

*The 6.10 mm base panel, ¼-inch groove depth, 2 mm outer clearance, 1 mm face gaps, ¼-inch lap length, 0.10 mm lap-face clearance and 0.15 mm shoulder clearance remain assumptions. The groove width is ¼ inch. Frame joints, panel retention, thin lap strength, cleat attachment and hardware strength require physical detailing. Nine sampled hinge angles are checked; this is not a continuous mechanical or load certification.

## Dovetail proportions

The three-tail, 1:6 layout retains the outside half-pins. The two interior full pins are halved at their narrow faces: 15.375 mm to 7.6875 mm (approximately 0.605 to 0.303 inch). Their wide ends are 14.0375 mm; outside half-pins remain 7.6875 mm at their narrow ends. Only the interior-facing boundaries of the adjacent tails move, so the middle tail grows on both sides and the outer tails grow inward. This preserves the case envelope and all corner slopes.

## Materials

The default face veneer is quilted maple, using the user's supplied photograph; curly maple remains selectable. The quilted photograph is mapped at its original aspect ratio with an illustrative 350 mm image width. It is a visual sample, not a scan of selected stock or a physical simulation of chatoyance. Color and figure continuity between boards depend on the eventual stock and finish.

European beech uses the straighter, ray-flecked left strip (2–38% of image width) of the user's full-board scan, oriented along each member. This is a visual selection for the requested quartersawn appearance; a face scan alone does not establish growth-ring orientation. The approximately 75 mm strip mirrors across wider members; grain length is mapped at an illustrative 764.54 mm. Linear RGB scaling matches the scan's average color to the user's amber finished sample. Procedural end grain remains on actual cut ends, including exposed dovetails. Both reference images are retained under `textures/`. No AI imagery is used. The tiger's-eye-style stone retains its procedural material and assumed 1½-inch diameter.

## Files and checks

Both options include editable parameters, STEP, 3MF, STL, preview mesh and geometry report. The builder checks valid solids, watertight meshes, STEP reimport, exact body envelope, panel/frame and board overlaps, dovetails, cleats and nine hinge positions between 0 and 110 degrees. Compare the selected dimensions and validation files for exact radii and knob envelopes. A preserves the R6 B geometry. Physical fit, veneer forming and hardware strength remain unverified.

Rebuild from this directory with CadQuery 2.8, Shapely and trimesh:

```
python source/build_model.py a
python source/build_model.py b
npx esbuild source/viewer.js --bundle --format=iife --minify --outfile=viewer.js
```

Three.js license: `vendor/LICENSE.txt`.
