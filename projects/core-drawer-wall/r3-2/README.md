# Cardboard core drawer wall · R3.2

[Compare the three drawers and see the mounting layout](datasheet.html). All three fit the same fixed housing; each has a smooth writable circular front. The cardboard is the enclosure. No adhesive or tube liner is needed. Use nominal **83 mm ID × 88 mm OD × 60 mm** cores. Try the [R3 fit print](../r3/models/fit-r3.3mf) with actual cores first.

| Drawer plate | CAD capacity to rim | PLA | P1S slice |
| --- | ---: | ---: | ---: |
| [Open](models/open-r3-2.3mf) | 235.0 mL | 48.55 g | 1 h 23 min |
| [Left / right](models/left-right-r3-2.3mf), two long lanes | 114.7 + 114.5 mL | 55.61 g | 1 h 31 min |
| [Front / back](models/front-back-r3-2.3mf), two short bins | 114.2 + 114.3 mL | 56.35 g | 1 h 31 min |

Print the bin floor down and the face flat with the grip up as supplied. Align the two molded keys and drive **one #4 × ⅜″ pan-head sheet-metal screw** from the outside of the disk into the blind printed pilot. Hand-tighten just until the face seats; do not substitute a longer screw. The tip stays enclosed in a low rounded lug at the floor. The fixed dividers have rounded crowns and no insert channels. The disk covers the nominal core bore with 1.9 mm overlap all around, including the former 6 mm bottom opening; adjacent disks have 3.6 mm clearance. This is a dust cover, not a seal.

## Connector plates and hardware

| Print | When to use it | PLA | Time | Off-the-shelf parts |
| --- | --- | ---: | ---: | --- |
| [Outside feet](models/dry-ends-r3-2.3mf) | One set of four for the entire bottom row | 8.79 g | 24 min | 2 ties |
| [Shared base](../r3/models/base-mount-r3.3mf) | One pair at each joint between two bottom cores | 9.09 g | 23 min | 1 tie |
| [Upper junction](../r3/models/upper-mount-r3.3mf) | One pair per unanchored upper cell | 7.43 g | 24 min | 1 tie |
| [Middle mount](models/middle-mount-r3-2.3mf) | Replaces the regular upper pair where attaching to plywood | 7.64 g | 24 min | 1 bolt set + 1 wood screw |
| [Anchored top tier](models/top-tier-r3-2.3mf) | One complete new anchored top cell, including tied upper junction and rim clips | 9.35 g | 29 min | 1 tie + 1 bolt set + 1 wood screw |
| [Top clips only](models/top-clips-r3-2.3mf) | Retrofit an exposed core that already has its upper junction | 2.01 g | 12 min | 1 bolt set + 1 wood screw |

A tie is **2.5 × 200 mm**. A bolt set is an **M3 × 70 mm 90° countersunk machine screw**, M3 washer and nylon-insert locknut. Use a **#8 × ¾″ pan-head wood screw** for each rear anchor on the ¾″ plywood backboard. The R3 base and upper files linked above already have tie slots. The rear screw hole is optional at ordinary joints. Use these tied plates rather than the older plain jaws.

1. Stand the bank on a continuous shelf or bench with the plywood fixed to its supporting structure. Match core lengths and discard crushed or soft tubes. Start with one drawer and two neighboring rims; check full drawer removal and closing before building a row.
2. Seat the front and rear jaws over the rims. At each ordinary pair, loop the tie down both sides of the gap between cores, through both slots in the rear and front jaws, with the rear crosspiece in the relief. Bring the head to the front and trim the tail. At the outside feet, place the tie head in the slot farther from the core. Snug gently: the tie captures the jaws without squeezing the bore oval. Move the outside feet outward when extending the bottom row.
3. Put each upper core between the two below, with a junction at both ends. At an intermediate **anchored** joint, seat the M3 screw head in the plywood-side countersink and drive the wood screw into a suitable pilot **before** fitting the front jaw. Fit the front jaw, washer and locknut. At the **top**, tie its upper junction normally and install the rim clips across the exposed top of the core. The rear eye sits above the rim for driver access. Use the same through-bolt and wood screw. Snug without crushing cardboard. [Mount detail](mount.svg).
4. [Eight-row example](layout.svg): 9, 8, 7, 6, 5, 4, 3 and 2 cores: **44 drawers**, about **813.6 mm wide × 654.6 mm high** over the feet and top tabs. The drawing shows two separated row-4 attachments and two above row 8. Print one outside-foot set, eight shared bases, 31 regular upper pairs, two middle mounts and two top-tier sets. This uses 43 ties, four bolt sets, four wood screws, plus one face screw per drawer. The shelf carries the weight; the tabs restrain the bank. The four locations illustrate installation, not tested anchor spacing or an eight-row load rating. Keep heavy items low. Check a loaded cell and its connection before filling a bank. Support drawers by hand near full extension.
5. For falling dust in the valleys above the bank, an optional single plywood hood is easier to wipe than many individual plugs. For the illustrated bank, an **824 × 90 mm** scrap board on its own continuous backboard cleat spans the bank; set it at least **15 mm above the top tabs**, after installing the screws. It does not carry the drawers.

## Comparison to the 82.4 g, 2 h 12 min cardboard can

| One complete added cell | Open | Left / right | Front / back |
| --- | ---: | ---: | ---: |
| First cell on outside feet | 57.34 g / 1:47 | 64.40 g / 1:55 | 65.14 g / 1:55 |
| Added bottom cell (shared base) | 57.64 g / 1:46 | 64.70 g / 1:54 | 65.44 g / 1:54 |
| Ordinary upper cell | 55.98 g / 1:47 | 63.04 g / 1:55 | 63.78 g / 1:55 |
| Middle anchored cell | 56.19 g / 1:47 | 63.25 g / 1:55 | 63.99 g / 1:55 |
| Anchored top cell | 57.90 g / 1:52 | 64.96 g / 2:00 | 65.70 g / 2:00 |

Hours:minutes, based on sums of rounded standalone plate estimates. Metal hardware and ties are not filament; assembly is not included in print time. The reference can's original print profile is unknown. One tube, one drawer per cell; cardboard is reused. Sliced on a Bambu P1S, 0.4 mm nozzle, PLA, 0.20 mm layers, 3 walls, 15% gyroid, supports and brim off. Supplied 3MFs contain geometry in print orientation; select your printer profile. See [slice records](slice-checks.json) and [CAD checks](checks.json). Parts have not been physically fit- or load-tested.

Original modeled geometry, drawing on the [curved shared junctions](https://makerworld.com/en/models/1940593-filament-spool-paper-tubes-modular-storage-drawer#profileId-2084214) and the [minimal rim hardware](https://makerworld.com/en/models/3338387-infinite-stackable-empty-spool-core-drawer#profileId-3792190). R3.2 source imports the R3.1 cavity and R3 junction geometry from this project.
