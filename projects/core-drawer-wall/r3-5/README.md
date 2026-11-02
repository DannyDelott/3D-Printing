# Cardboard core drawer wall · R3.5

[Interactive three-row assembly](datasheet.html). Eight nominal 83 mm ID × 88 mm OD × 60 mm cardboard cores sit in rows of 3, 2 and 3. The assembly uses cable ties to capture the rims and two short wood screws into the backboard. The shelf carries the weight. No through-bolts, nuts, washers or adhesive.

## Drawers

| Print | Storage to rim | PLA | P1S time |
| --- | ---: | ---: | ---: |
| [First cell: open drawer + four outside feet](models/starter-r3-5.3mf) | 245.4 mL | 50.81 g | 1 h 28 min |
| [Open drawer](models/open-r3-5.3mf) | 245.4 mL | 42.11 g | 1 h 10 min |
| [Left / right](models/left-right-r3-5.3mf) | 238.2 mL total | 50.64 g | 1 h 17 min |
| [Front / back](models/front-back-r3-5.3mf) | 238.8 mL total | 49.98 g | 1 h 26 min |

Each drawer is one piece. Print its **flat Ø86.8 mm circular face directly on the bed**. There is no bevel across the bottom. The 34 × 15 mm opening has a closed finger cup behind it; the rest of the face is flat for writing. It overlaps the nominal bore by 1.9 mm all around. A short solid roof covers the mouth between the face and the core rim so the forward extension does not admit dust when closed. A pitched back wall and, in the front/back version, one chevron divider grow inward from the sidewalls. This trades 48.4 mL from the R3.4 open drawer for the flat front and a shorter print. The face sits at the same depth as the previous version. Leave the supplied orientation unchanged.

## Side and triangle storage

| Installed location | Complete three-piece 3MF | CAD volume per bin | Complete PLA / time | Fixed frames only |
| --- | --- | ---: | ---: | ---: |
| Outer left of row two | [Left pocket](models/left-pocket-r3-5.3mf) | 88.6 mL | 33.43 g / 66 min | [9.42 g](models/left-pocket-frame-r3-5.3mf) |
| Outer right of row two | [Right pocket](models/right-pocket-r3-5.3mf) | 88.6 mL | 33.43 g / 66 min | [9.42 g](models/right-pocket-frame-r3-5.3mf) |
| Each inverted three-core gap | [Triangle pocket](models/triangle-pocket-r3-5.3mf) | 13.8 mL | 12.67 g / 45 min | [4.40 g](models/triangle-pocket-frame-r3-5.3mf) |

Each file contains a front frame, a rear frame and an open-top pocket with a blind finger or nail grip. The frames remain on the rims when you pull the pocket forward. Leave the lower rim seated in the side uprights; the pocket itself does not support the outside top core. Install each side pair before loading that core. The triangular frames use a narrow tie loop above the tray; feed the same 2.5 × 200 mm tie through the two front and two rear slots. Keep its head clear of the moving pocket. Do not use the older solid spacers as the pocket frames. These bins can be removed completely; support them when extended. Extra bins: [left](models/left-pocket-bin-r3-5.3mf), [right](models/right-pocket-bin-r3-5.3mf), [triangle](models/triangle-pocket-bin-r3-5.3mf).

## Build and anchor

1. Test the [3.57 g fit sample](../r3/models/fit-r3.3mf) in actual cores. Use a level continuous shelf and backboard fastened to its supporting structure.
2. Use one set of four [outside feet](../r3-2/models/dry-ends-r3-2.3mf) per bottom row and a [shared base pair](../r3/models/base-mount-r3.3mf) for each new bottom seam. Use one 2.5 × 200 mm tie per front/rear pair.
3. Seat each middle core on a pair of [tied upper junctions](../r3/models/upper-mount-r3.3mf). To anchor a middle position, pilot the ¾″ plywood for one #8 × ¾″ pan-head wood screw and drive it through the rear eye **before installing the front junction**. Then thread the tie through both end pieces, keeping its head at the front. The anchored and unanchored junction use the same printed plate.
4. A new anchored top core takes one [top set](models/top-tier-r3-5.3mf) (9.21 g, 29 min). Tie its upper junction normally; then put the small keeper at the exposed front rim and the taller tab at the rear. Loop a second tie through their slots above the core, and drive one #8 × ¾″ screw through the upper rear eye. For an upper cell already joined below, use [top clips only](models/top-clips-r3-5.3mf) (1.87 g, 12 min). Snug ties without crushing the cardboard. [Mount detail](mount.svg).
5. For the displayed 3–2–3 example: eight main drawers, one outside-feet set, two shared base pairs, two upper junction pairs (one with its optional middle wood screw), one complete top set, one left pocket kit, one right pocket kit, and three triangle pocket kits. Total **13 ties and 2 wood screws**, including the two exterior ends and both sets on the top cell. The [eight-row mounting elevation](../r3-2/layout.svg) illustrates a different stepped bank; it does not establish safe screw spacing or a load rating. Try a single loaded cell and side frame before scaling up.

Bambu Studio P1S, PLA, 0.4 mm nozzle, 0.20 mm layers, 3 walls, 15% gyroid, no supports or brim. Times are slicer estimates. [CAD checks](checks.json) cover full withdrawal of the main and gap drawers, installed core/frame/tie clearance, and layer continuity. [Slice checks](slice-checks.json) record the original file hashes. Fit, grip comfort and loaded strength have not been physically tested.
