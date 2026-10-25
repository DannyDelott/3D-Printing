# Broad maple center R5

Three vertical boards, with a broad center and two narrower side boards. R5 retains the preferred R3 A curved rails, the ⅛-inch rail/stile shadow line, the 18 × 27 × 6-inch case-and-door envelope, open back, French cleat, three 1:6 dovetails per corner and mortised knife hinges. R4 remains available separately.

| Option | Layout | Depth |
| --- | --- | --- |
| A · Flat panel | R4's three boards; 4½-inch center bay | All maple faces in one plane |
| B · Broad center | 6-inch center bay; side bays approximately 3¾ inches before fitting | All three panel faces flush |

The 6-inch center is measured between seam centers. The fixed opening is 13⅜ inches wide, so outer bays fit the existing reveal and stile dimensions rather than forcing a 13½-inch opening. The 1 mm seams reduce visible board widths. There are no added horizontal or vertical beech dividers.

## Depth and construction

The panels are quilted-maple veneer over a core. CAD represents their finished composite envelopes, not separate veneer/core laminations. All three faces are flush, with 6.10 mm finished panel thickness. The ¼-inch grooves, groove engagement, outside faces and vertical half-laps retain their R4 positions. The shallow perimeter channel is retained.

Closed-door face positions, measured from the front of the case:

| Surface | Position |
| --- | --- |
| Rail fronts | 22.050 mm |
| Stile fronts | 18.875 mm |
| Center face | 13.9875 mm |
| Side panel faces | 13.9875 mm |

All three panel faces sit 4.8875 mm behind the stiles. The existing ⅛-inch rail/stile step remains. Overall cabinet depth stays 152.4 mm / 6 inches, excluding the knob. The 6-inch center bay and retained frame dimensions use the ¾-inch design module; fitting clearances remain exceptions.

The proposed board layout, stock thickness and clearances are assumptions. The existing 6.35 mm wide/deep grooves, 2 mm outer clearance, 1 mm face gaps, nominal 6.35 mm laps, 0.10 mm lap-face clearance and 0.15 mm shoulder clearance remain provisional. The nominal ¼-inch tongues and approximately 3 mm half-laps require actual stock and machining checks. Seasonal movement, panel retention, rail/stile joinery, cleat attachment, wall fasteners, anti-lift retention and hardware strength are not validated by this geometry.

## Perimeter channel

A 1/16-inch-wide (1.5875 mm), 1/64-inch-deep (0.396875 mm) channel follows the whole panel opening along the curved rails and straight stiles. Its floor sits below the ordinary panel face, and it does not run down the internal seams. The dimensions are user-specified. The user confirmed 3/32-inch (2.38125 mm) face veneer, leaving 5/64 inch (1.984375 mm) below the channel. The cutter setup still needs confirmation before machining. The core material, balancing back veneer, adhesive and edge lippings remain unspecified. Both comparison options include the channel.

## Dovetail proportions

The three-tail, 1:6 layout retains the outside half-pins. The two interior full pins are halved at their narrow faces: 15.375 mm to 7.6875 mm (approximately 0.605 to 0.303 inch). Their wide ends are 14.0375 mm; outside half-pins remain 7.6875 mm at their narrow ends. Only the interior-facing boundaries of the adjacent tails move, so the middle tail grows on both sides and the outer tails grow inward. This preserves the case envelope and all corner slopes.

## Materials

The default face veneer is quilted maple, using the user's supplied photograph; curly maple remains selectable. The quilted photograph is mapped at its original aspect ratio with an illustrative 350 mm image width. It is a visual sample, not a scan of selected stock or a physical simulation of chatoyance. Color and figure continuity between boards depend on the eventual stock and finish.

European beech uses the straighter, ray-flecked left strip (2–38% of image width) of the user's full-board scan, oriented along each member. This is a visual selection for the requested quartersawn appearance; a face scan alone does not establish growth-ring orientation. The approximately 75 mm strip mirrors across wider members; grain length is mapped at an illustrative 764.54 mm. Linear RGB scaling matches the scan's average color to the user's amber finished sample. Procedural end grain remains on actual cut ends, including exposed dovetails. Both reference images are retained under `textures/`. No AI imagery is used. The tiger's-eye-style stone retains its procedural material and assumed 1½-inch diameter.

## Files and checks

Each option has its own editable parameters, STEP, 3MF, STL, preview mesh and geometry report. Checks cover valid solids, watertight meshes, STEP reimport, panel/frame and board overlaps, case dovetails, cleat fit and nine hinge positions from 0 to 110 degrees. Visual normals are checked on planar faces. Neither CAD nor slicer import proves physical fit or structural capacity.

Rebuild with CadQuery 2.8, Shapely and trimesh:

```
python source/build_model.py a
python source/build_model.py b
npx esbuild source/viewer.js --bundle --format=iife --minify --outfile=viewer.js
```

Three.js and its helpers retain their license under `vendor/LICENSE.txt`.
