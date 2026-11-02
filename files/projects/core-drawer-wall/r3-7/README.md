# Cardboard core drawer wall · R3.7

[Interactive assembly and print orientation](datasheet.html) · [First-cell 3MF](models/starter-r3-7.3mf) · [Fit sample](models/fit-r3-7.3mf)

Use an 83 mm ID × 88 mm OD × 60 mm cardboard core on a continuous level shelf against ¾″ plywood. Each clip grips one rim with short tapered pads. The example uses two #8 × ¾″ pan-head wood screws, one in a middle rear junction and one in the exposed top tab. The shelf carries the weight.

## Drawers

The open and divided drawers have a flat 1.65 mm rear wall. It spans the full diameter of the drawer body at mid-height. A bevel on the lower rear corner gives the main drawer a broad flat print surface. The midsize pockets and tiny triangle bins have square ends and print open side up. [Rear section](drawer-rear.svg).

The main drawer rides in the original sliding profile. The circular Ø86.8 mm front widens over the projecting nose and overlaps the bore by 1.9 mm all around. At full insertion the back meets the plywood, with the enlarged nose still 0.8 mm ahead of the front jaw. Withdrawal increases that separation. Both divider options now use a straight partition.

| Drawer | Volume to rim | PLA | P1S time |
| --- | ---: | ---: | ---: |
| [open](models/open-r3-7.3mf) | 298.5 mL | 55.15 g | 105 min |
| [left-right](models/left-right-r3-7.3mf) | 291.2 mL | 63.83 g | 115 min |
| [front-back](models/front-back-r3-7.3mf) | 291.9 mL | 63.08 g | 120 min |
| [left-pocket](models/left-pocket-r3-7.3mf) | 166.8 mL | 42.96 g | 81 min |
| [right-pocket](models/right-pocket-r3-7.3mf) | 166.8 mL | 42.95 g | 82 min |
| [triangle-pocket](models/triangle-pocket-r3-7.3mf) | 14.1 mL | 13.66 g | 31 min |

Gap pocket figures include the front frame, rear frame and removable bin. Individual frame and bin files are on each part’s page.

## Installation and fit

1. Test the [foot pair](models/fit-r3-7.3mf) on the actual cardboard. Each local jaw has a tapered grip pad that lightly presses the cardboard. The foot should seat by hand and stay on the rim when the loaded drawer is opened. Core ovality and wall thickness affect this fit.
2. Install the [outside feet](models/dry-ends-r3-7.3mf), then the [shared bases](models/base-mount-r3-7.3mf) and [three-way upper clips](models/upper-mount-r3-7.3mf) independently at the front and rear rims. The side frames hold the outside top cores over the row-two half-gaps. Install them before placing those top cores.
3. At a chosen middle station, pilot the plywood and drive a wood screw through the rear junction before seating the neighboring cores. Use the [complete top set](models/top-tier-r3-7.3mf) for a new top cell or the [top clips](models/top-clips-r3-7.3mf) for an existing upper cell. The top screw enters the backboard through the exposed rear tab. The [eight-row diagram](../r3-2/layout.svg) illustrates possible anchor locations.
4. The 3–2–3 example takes eight main drawers, one set of outside feet, two shared base pairs, two upper junction pairs, one complete top set, one left and one right side pocket kit, three triangle pocket kits and two wood screws. One core is displayed empty in the assembly.

Keep the supplied print orientations. The main drawers print with the slide axis 48° above the bed, on a 1,317 mm² facet. The gap bins print upright on their floors, and the short rim clips print rim-face down. Bambu Studio P1S, PLA, 0.4 mm nozzle, 0.20 mm layers, three walls and 15% gyroid. Supports and brims are off. [CAD clearance and balance checks](checks.json) · [Slice estimates](slice-checks.json). Actual rim retention, drawer operation and loaded stack strength have not been physically tested.
