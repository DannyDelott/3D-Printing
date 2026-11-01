# Cardboard core drawer wall · R1

Make a staggered bank of drawers on a shelf against a plywood backboard. The cardboard is the housing. Only short shoes and clips touch its rims. The drawer has a plain writable face, a finger scallop and a lip 14 mm above the tube centerline.

[Design sheet, assembly drawing and interactive model](datasheet.html)

## Print quantities

| For each added core | Printed parts | PLA (g) | P1S time |
| --- | --- | ---: | ---: |
| Bottom-row hardware | 2 flat shoes + 2 seam clips (one new lateral seam) | 8.74 | 23 min |
| Upper-row hardware | 2 small glides + 6 seam clips (two seams below, one lateral) | 6.05 | 23 min |
| Bottom hardware including a wall tab + guard | Same as bottom, plus anchor kit | 11.55 | 29 min |
| Upper hardware including a wall tab + guard | Same as upper, plus anchor kit | 8.86 | 28 min |
| Drawer only | Print one per core | 32.56 | 43 min |
| Starter | Drawer + anchored bottom hardware | 44.02 | 65 min |
| Fit print | Drawer cross section, working glide and working seam clip | 3.63 | 13 min |

A seam is counted once, when its second core is added. Use a clip at each end. Keep surplus clips from an edge cell for the next row. At a separated upper anchor point substitute the anchored hardware plate; choose the regular plate everywhere else. Moving an anchor to a higher row doesn't require replacing any glued part.

The estimates come from Bambu Studio slices of the R1 geometries on a P1S: PLA, 0.4 mm nozzle, 0.20 mm layers, 3 walls, 15% gyroid, supports off, no brim, $20/kg. Files are millimetre geometry with parts arranged in print orientation. Use the matching 3MF to keep individual parts selectable. The five-core assembled STL is a dimensional preview including cardboard and ties; it is not a print plate.

## Fit and assembly

1. Use bare, round cores of similar length. The design assumes 83 mm ID, 88 mm OD and 60 mm length. The existing cardboard-can ring uses an 83/89 mm mating groove; these drawer dimensions are nominal, not measurements of the linked print profiles. The second reference reports core walls from 2.1 to 3.0 mm. The 3.6 mm jaw slot leaves room for variation and glue. Test two real core ends before printing a row.
2. Seat the test glide at six o’clock, then slide the short drawer cross section past it and through the whole core. Check the seam fork with two cores side by side, one wall in each slot. Use the coupons to detect ovality, binding, a loose joint or cardboard that buckles. Use full scale; edit the source for materially different cores.
3. Put a flat shoe at the front and rear of each bottom core with the sole down. Upper cores nest between the two below and use the small glide in place of each shoe. Join every touching pair at the front and rear, keeping core ends aligned. The 2.4 mm gap between nominal ODs is set by the seam forks. Check drawer travel, then bond contact faces of shoes/glides and forks to the cardboard using small drops of CA; keep glue off the sliding surfaces.
4. To restrain tipping, select separated top cores. Place the front guard over the top front rim and the rear tab against the backboard, eye up, recessed face toward the plywood. Feed a **4.8 × 200 mm cable tie** under the top of the tube, through the lower tab slot, up the shallow recess, out the upper slot, and forward over the tube and guard. Cinch gently, with the head outside above the core. The tie captures both rims; the rear tab does not rely on glue. Use one **#8 × ¾-inch pan-head wood screw** per tab, piloted for the screw. The 4.8 mm thick tab leaves about 14 mm in a 19 mm board. Install tabs where there is driver access above the row. If adding more rows above, move the tabs to the new top and reconnect.
5. The base must stand on a shelf or bench; the tabs are anti-tip restraints. This is not a hanging cabinet. Support the drawer by hand near full extension: it lifts completely out without a catch. Test one cell with its intended contents before multiplying it. No physical fit, load rating, anchor spacing or maximum wall height is established.

## Source and validation

Run the repository CAD Python on [source/model.py](source/model.py), then [source/drawing.py](source/drawing.py). The templates are original geometry; no third-party mesh is included. CAD checks cover straight extraction against nominal core, both shoes, upper glides, the top rim guard, and seam clips at all six possible neighbor positions. Each printable solid was checked for one closed, positive-volume shell. Slice results and source hashes are in slice-checks.json; no G-code is supplied.

Design references: [shiyin’s minimal rim clips](https://makerworld.com/en/models/3338387-infinite-stackable-empty-spool-core-drawer#profileId-3792190) and [实用至上’s staggered drawer bank and flat base](https://makerworld.com/en/models/2095928-filament-spool-cardboard-core-parts-storage-box-sp#profileId-2266223).
