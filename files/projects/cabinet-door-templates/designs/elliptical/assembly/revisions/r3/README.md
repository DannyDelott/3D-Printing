# Cabinet door options R3

Three separate woodworking assemblies for comparison. The approved R2 remains unchanged. Open `index.html` to switch options while retaining the camera and door angle. Each option has its own full-size 3MF, STEP, STL, source parameters and validation report.

| Option | Rail end heights | Walnut panels | New proportions |
| --- | --- | --- | --- |
| A · Lighter curves | 2¼ / 4½ in | One | 25% less rail face area than R2 |
| B · Slim curves | 1½ / 3¾ in | One | Smallest rail ends; confirm final hinge/joint details |
| C · Divided panel | 2¼ / 4½ in | Two | ¾ in crossbar starts 9 in above the door bottom |

All rail profiles retain the q=0.95 ellipse family. The reduction for A compares the unmachined rail outlines, before grooves and hardware mortises. Option C uses A's outlines plus the divider.

## Confirmed constraints

- Case and door: 18 × 27 × 6 in (457.2 × 685.8 × 152.4 mm); knob excluded from depth.
- Case and rails: ¾ in thick. Stiles remain 2¼ in wide and ⅝ in thick, with their backs aligned to the rails for a ⅛ in front shadow line.
- Three 1:6 through-dovetails at each corner; vertical sides are tail boards, top and bottom are pin boards.
- European quartersawn beech case/frame; contrasting walnut floating panels in ¼ in grooves.
- Open back with top French cleat. No full back or lower back rail.
- Tiger's eye stone knob direction, based on the user's reference image.
- New visible design proportions use a ¾ in module. Existing ⅝ in stiles, ¼ in grooves, fitting clearances and hardware details are exceptions.

## Open back and cleat

The cleat is recessed into the existing case envelope. The cabinet cleat is 16½ in long, 2¼ in high at its long face, and ¾ in thick. The wall member is 15 in long with the same cross section and a mating 45-degree bevel. Its shorter length leaves ¾ in lateral clearance at each end relative to the cabinet member. Both are included as separate CAD parts. The wall plane shown in the viewer is environmental context and is not exported.

Removing the ¾ in back increases interior depth below the cleat from 111.3 mm to 130.35 mm (4.382 to 5.132 in), measured from the rear wall plane to the case front. The pair occupies the top 3¾ in band below the top panel. Cleat height, thickness and bevel are assumptions; wall fasteners, cabinet attachment, anti-lift retention and resistance to racking are not designed or load-rated. The wall should be flat and the final mount designed for its substrate and load.

Construction reference: [Collins, French Cleat Installation](https://support.collins.co/french-cleat-installation). Its hardware instructions apply to Collins products, not a rating for this cabinet.

## Panels and knob

Grooves are assumed ¼ in deep as well as ¼ in wide. Panel thickness is 6.10 mm, with 2 mm perimeter clearance at groove bottoms and 4.35 mm engagement. Each C panel has its own four-sided groove, including an edge in the crossbar. The crossbar is ¾ in high and ¾ in thick. Corner and divider tenons, glue areas and grain-movement allowance for actual stock remain to be detailed.

The stone is a rounded, polished cabochon approximation, assumed 1½ in in diameter. Its mount and stone together project ¾ in from the stile, bringing total depth including the knob to 6⅝ in (168.275 mm). Tiger's eye banding is a procedural material inspired by the user-provided reference; it is not a product match or a downloaded texture. Stone pattern, size, mounting and screw geometry are not specified by the reference image.

Beech material reference: [The Wood Database, European Beech](https://www.wood-database.com/european-beech/). All viewer materials are procedural; no AI-generated images are used. Three.js and OrbitControls retain their MIT license in `vendor/LICENSE.txt`.

## Verification and rebuilding

Each option's `validation.json` records dimensions, panel count, cleat fit, watertight meshes, STEP reimport, panel/frame and dovetail overlap, and nine sampled door positions through 110 degrees. These are geometry checks, not structural or hardware qualification. `import-check.json` records Bambu Studio's 3MF importer results; these are reference assemblies, not arranged print jobs.

Use CadQuery 2.8, Shapely 2 and trimesh:

```
python source/build_model.py a
python source/build_model.py b
python source/build_model.py c
npx esbuild source/viewer.js --bundle --format=iife --minify --outfile=viewer.js
```

The generator takes an option directory, reads its `parameters.json` and exports all geometry and mesh data into that directory. On the original machine, use the repository's `closet-space-saver-hex/.venv/bin/python3` interpreter. Update the viewer asset's hash in `index.html` after bundling. Refresh the three front-view images and shared catalog/download previews with the current meshes. Existing routing templates are unchanged and do not match these wider overlay doors.
