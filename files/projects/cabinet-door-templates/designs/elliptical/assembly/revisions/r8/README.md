# Adjustable Broad Center crown · R8

The front-crown slider selects flat through ¾ inch in ⅛-inch increments. Each setting loads an exact CAD variant with matching STEP, 3MF, parameters and validation downloads. Camera angle, opening angle, materials and display controls stay in place while changing the curve. The selected setting is retained in the page URL. Flat retains the R5 B proportions with the updated channel and cleats; earlier revisions remain available.

| Setting | Crown | Case + door depth | Rail maximum thickness | Panel maximum thickness* |
| --- | --- | --- | --- | --- |
| Flat | 0 | 6″ / 152.400 mm | ¾″ / 19.050 mm | 6.100 mm |
| A | ⅛″ / 3.175 mm | 6⅛″ / 155.575 mm | ⅞″ / 22.225 mm | 9.275 mm |
| B | ¼″ / 6.350 mm | 6¼″ / 158.750 mm | 1″ / 25.400 mm | 12.450 mm |
| C | ⅜″ / 9.525 mm | 6⅜″ / 161.925 mm | 1⅛″ / 28.575 mm | 15.625 mm |
| D | ½″ / 12.700 mm | 6½″ / 165.100 mm | 1¼″ / 31.750 mm | 18.800 mm |
| E | ⅝″ / 15.875 mm | 6⅝″ / 168.275 mm | 1⅜″ / 34.925 mm | 21.975 mm |
| F | ¾″ / 19.050 mm | 6¾″ / 171.450 mm | 1½″ / 38.100 mm | 25.150 mm |

All depths exclude the knob. Width and height remain 18 × 27 inches (457.2 × 685.8 mm). Case depth stays 130.35 mm, rail outside edges remain ¾ inch thick, and all backs and groove/lap planes remain flat. Crowns are circular across the door width with no vertical curvature. The selected crown is ¾″; the slider retains the earlier comparison settings. The profile drawing exaggerates depth 2.5× and is labeled; 3D geometry and downloads use actual dimensions. Stock requires machining allowance beyond the listed finished maximums.

## Construction

Use thicker beech blanks and plane or rout the exposed front to the crown, keeping the rear face flat. The original flat grooves and hinge mortises remain. The same crown is applied to the rails, stiles and three maple faces, preserving the rail/stile step without a separate raised middle panel. Blank stock needs additional machining allowance beyond the finished maximums above.

For the veneer-over-core panels, shape the thicker core before applying the 0.6 mm quilted-maple face veneer and 0.6 mm maple backing. Do not remove the front crown from an already flat 0.6 mm veneer: that would exceed its thickness. CAD represents the finished composite surface; core material, veneer-forming method, adhesive and edge treatment remain unspecified. This shallow geometry does not establish whether the actual quilted veneer can conform without cracking; make a shop sample. Groove tongues and rear lap planes stay at the original dimensions, with the extra face thickness confined to the visible opening. There is no need for coopered staves in this geometry.

The 6-inch center bay and original asymmetric rail silhouette are retained. Side bays are approximately 3¾ inches before fitting. The ¾-inch module still controls major proportions; crown, reveals, stock thicknesses and fitting details are explicit exceptions.

## Perimeter channel and fit

The perimeter channel follows the front crown and curved opening: 1/16 inch (1.5875 mm) wide and 0.2 mm deep, measured in the front-to-back direction. With nominal 0.6 mm face veneer, approximately 0.4 mm remains below the channel. It does not extend along the two internal seams. Thicknesses are measured front-to-back; the very shallow local surface angle makes normal thickness slightly smaller.

*The 6.10 mm base panel, ¼-inch groove depth, 2 mm outer clearance, 1 mm face gaps, ¼-inch lap length, 0.10 mm lap-face clearance and 0.15 mm shoulder clearance remain assumptions. The groove width is ¼ inch. Frame joints, panel retention, thin lap strength, cleat attachment and hardware strength require physical detailing. Nine sampled hinge angles are checked; this is not a continuous mechanical or load certification.

## French cleat

The mating pair occupies 3″ / 76.2 mm vertically and ¾″ / 19.05 mm front-to-back. It is modeled as a 3″ blank split centrally with a 45° bevel. Each member has a 1⅞″ / 47.625 mm long edge, 1⅛″ / 28.575 mm short edge and 1½″ / 38.1 mm height at mid-thickness. The bevels overlap vertically by ¾″, leaving exactly 3″ for the assembled pair.

Both cleats span the full 16½″ / 419.1 mm clear width between the case sides. This is nominal edge-to-edge geometry, with no fitting clearance, screws or kerf allowance modeled. The upper cleat touches the underside of the case top; the wall remains visible below the 3″ band. Wall fasteners, cabinet attachment, anti-lift retention and racking resistance still require detailing.

## Dovetail proportions

The three-tail, 1:6 layout retains the outside half-pins. The two interior full pins are halved at their narrow faces: 15.375 mm to 7.6875 mm (approximately 0.605 to 0.303 inch). Their wide ends are 14.0375 mm; outside half-pins remain 7.6875 mm at their narrow ends. Only the interior-facing boundaries of the adjacent tails move, so the middle tail grows on both sides and the outer tails grow inward. This preserves the case envelope and all corner slopes.

## Materials

The default face veneer is quilted maple, using the user's supplied photograph; curly maple remains selectable. The quilted photograph is mapped at its original aspect ratio with an illustrative 350 mm image width. It is a visual sample, not a scan of selected stock or a physical simulation of chatoyance. Color and figure continuity between boards depend on the eventual stock and finish.

European beech uses the straighter, ray-flecked left strip (2–38% of image width) of the user's full-board scan, oriented along each member. This is a visual selection for the requested quartersawn appearance; a face scan alone does not establish growth-ring orientation. The approximately 75 mm strip mirrors across wider members; grain length is mapped at an illustrative 764.54 mm. Linear RGB scaling matches the scan's average color to the user's amber finished sample. Procedural end grain remains on actual cut ends, including exposed dovetails. Both reference images are retained under `textures/`. No AI imagery is used. The tiger's-eye-style stone retains its procedural material and assumed 1½-inch diameter.

## Files and checks

All seven settings include editable parameters, STEP, 3MF, STL, preview mesh and geometry report. The builder checks valid solids, watertight meshes, STEP reimport, exact body envelope, panel/frame and board overlaps, dovetails, cleats and nine hinge positions between 0 and 110 degrees. Compare the selected dimensions and validation files for exact radii and knob envelopes. All crown settings use the revised channel and cleats; other case and frame proportions are retained. Physical fit, veneer forming and hardware strength remain unverified.

Rebuild from this directory with CadQuery 2.8, Shapely and trimesh:

```
python source/build_model.py a
python source/build_model.py b
# Other folders: flat, c, d, e, f
Serve index.html over HTTP; it loads source/viewer.js as an ES module.
```

Three.js license: `vendor/LICENSE.txt`.
