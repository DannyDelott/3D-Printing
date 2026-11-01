# Cardboard core drawer wall · R3.3

[Mock assembly, print orientation and mounting diagram](datasheet.html). The clickable mock assembly has three bottom cores, two in the middle and one on top. Click a solid to identify it, or select a parts-list entry to highlight every matching piece. Reveal connectors hides the drawers and makes the cardboard translucent; orbit to the back to see where the plywood screws go. One drawer per nominal **83 ID × 88 OD × 60 mm** bare cardboard core. The bin, lower pull and full circular front are one solid, including an optional fixed divider. No screws, glue or hinges in any drawer. The Ø86.8 mm face overlaps the nominal bore by 1.9 mm around its whole circumference. It covers the lower opening; the 3.6 mm clearance between adjacent fronts remains for withdrawal.

| Print | Capacity to rim | P1S PLA | Time |
| --- | ---: | ---: | ---: |
| [First cell: open drawer + four feet](models/starter-r3-3.3mf) | 241.8 mL | 54.85 g | 1 h 44 min |
| [Open drawer](models/open-r3-3.3mf) | 241.8 mL | 46.15 g | 1 h 26 min |
| [Left/right drawer](models/left-right-r3-3.3mf) | 235.7 mL combined | 53.38 g | 1 h 34 min |
| [Front/back drawer](models/front-back-r3-3.3mf) | 235.2 mL combined | 53.99 g | 1 h 41 min |

**First print.** Try the [3.57 g core fit sample](../r3/models/fit-r3.3mf) if your tube is oval or its size is uncertain. Print the starter at 100%, leaving the drawer tilted as supplied. The new lower pull is the flat first layer, about 692 mm². The front and rear walls rise at 45° and the screw boss is gone. PLA, P1S, 0.4 mm nozzle, 0.20 mm layers, three walls, 15% gyroid, supports and brim off. Do not use auto-orient. Two ordinary 2.5 × 200 mm ties connect the feet front to rear; slide the completed drawer in level. Drawer hardware: none. Against the 82.4 g / 2 h 12 min cardboard-can baseline the complete starter saves 27.55 g and 28 minutes (slicer estimates).

**Add a bottom cell.** Reuse the outside feet at the new end; add a [shared base](../r3/models/base-mount-r3.3mf) and one tie at the new seam. Use one drawer of your choice.
**Add an upper cell.** Nest it between two cores underneath; tie one [upper connector pair](../r3/models/upper-mount-r3.3mf) front to rear. At selected joints substitute the [middle mount](../r3-2/models/middle-mount-r3-2.3mf). For a new anchored top cell, print the [complete top set](../r3-2/models/top-tier-r3-2.3mf); for an existing top cell use [top clips only](../r3-2/models/top-clips-r3-2.3mf).
**At the wall.** Use one M3 × 70 mm flat-head machine screw, washer and locknut plus one #8 × ¾″ wood screw per anchored station. The bank rests on a continuous shelf. [Hardware assembly and eight-row parts list](../r3-2/README.md#connector-plates-and-hardware) · [eight-row layout](../r3-2/layout.svg) · [mount detail](../r3-2/mount.svg). Use the R3.3 drawers in place of the old two-piece ones; only the wall mounts take screws. The layout illustrates positions, not an established eight-row load rating. Support drawers near full extension.

**Digital checks.** Drawer 3MFs each contain one closed volume; every sampled 0.2 mm layer region intersects material below it. Projected centers of mass fall inside the first-layer footprint for each drawer. The selected starter and all three individual plates sliced without supports, brim or slicer warnings. Fit and strength have not been physically tested. [Geometry and balance checks](checks.json) · [slice records](slice-checks.json).
