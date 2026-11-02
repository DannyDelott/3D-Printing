# Cardboard core drawer wall · R3.9

[Interactive assembly and print orientation](datasheet.html) · [First-cell 3MF](../r3-8/models/starter-r3-8.3mf) · [Fit sample](../r3-7/models/fit-r3-7.3mf)

Use an 83 mm ID × 88 mm OD × 60 mm cardboard core on a continuous level shelf against ¾″ plywood. Each clip grips one rim with short tapered pads. The example uses two #8 × ¾″ pan-head wood screws, one in a middle rear junction and one in the exposed top tab. The shelf carries the weight.

## Pass-through cubbies

Leave the three inverted triangular gaps empty. The cardboard walls form the sides, and there is no front frame, rear frame or pocket to print. The [assembly clearance check](checks.json) measures a 16.38 mm centered circular passage through each gap. The plywood stops items at the back; with 60 mm cores, longer pencils project at the front. Keep the load-bearing three-way connectors in the other gaps. The main drawers, side pockets and first-cell plate retain their original print files.

## Drawers

Print each one-piece main drawer flat on its circular label face. The body floor sits higher than the bottom of the face when installed, so the floor is not the print bed. The 86.8 mm front, blind finger cup and lower dust overlap all remain. The flat 1.65 mm rear wall spans the whole body; it has no beveled corner. The enlarged front stays 0.8 mm ahead of the rim clips at full insertion. The gap pockets still print open side up.

Five 1.4 mm ribs grow diagonally from the inner sidewalls and meet just ahead of the rear panel. They slope down toward the bin floor so they do not form level shelves. They provide landing lines for the final bridging layer. The front/back divider uses the same construction. These are part of the print and stay inside the drawer. [Section in print orientation](../r3-8/drawer-rear.svg).

| Drawer | Volume to rim | PLA | P1S time |
| --- | ---: | ---: | ---: |
| [open](../r3-8/models/open-r3-8.3mf) | 301.2 mL | 61.03 g | 93 min |
| [left-right](../r3-8/models/left-right-r3-8.3mf) | 293.7 mL | 69.92 g | 101 min |
| [front-back](../r3-8/models/front-back-r3-8.3mf) | 288.6 mL | 76.04 g | 120 min |
| [left-pocket](../r3-7/models/left-pocket-r3-7.3mf) | 166.8 mL | 42.96 g | 81 min |
| [right-pocket](../r3-7/models/right-pocket-r3-7.3mf) | 166.8 mL | 42.95 g | 82 min |

Gap pocket figures include the front frame, rear frame and removable bin. Individual frame and bin files are on each part’s page.

## Installation and fit

1. Test the [foot pair](../r3-7/models/fit-r3-7.3mf) on the actual cardboard. Each local jaw has a tapered grip pad that lightly presses the cardboard. The foot should seat by hand and stay on the rim when the loaded drawer is opened. Core ovality and wall thickness affect this fit.
2. Install the [outside feet](../r3-7/models/dry-ends-r3-7.3mf), then the [shared bases](../r3-7/models/base-mount-r3-7.3mf) and [three-way upper clips](../r3-7/models/upper-mount-r3-7.3mf) independently at the front and rear rims. The side frames hold the outside top cores over the row-two half-gaps. Install them before placing those top cores.
3. At a chosen middle station, pilot the plywood and drive a wood screw through the rear junction before seating the neighboring cores. Use the [complete top set](../r3-7/models/top-tier-r3-7.3mf) for a new top cell or the [top clips](../r3-7/models/top-clips-r3-7.3mf) for an existing upper cell. The top screw enters the backboard through the exposed rear tab. The [eight-row diagram](../r3-2/layout.svg) illustrates possible anchor locations.
4. The 3–2–3 example takes eight main drawers, one set of outside feet, two shared base pairs, two upper junction pairs, one complete top set, one left and one right side pocket kit and two wood screws. One core is displayed empty in the assembly.

Keep the supplied print orientations. The round front gives approximately 5,425 mm² of bed contact. The exported 3MFs preserve that orientation. The gap bins print upright on their floors, and the short rim clips print rim-face down. Bambu Studio P1S, PLA, 0.4 mm nozzle, 0.20 mm layers, three walls and 15% gyroid. Supports and brims are off. [CAD clearance and balance checks](../r3-8/checks.json) · [Slice estimates](../r3-8/slice-checks.json). The main drawers and first-cell plate sliced without warnings. The longest unsupported stretch measured on tagged bridge extrusions for the individual drawers was approximately 12 mm. Actual bridge finish, rim retention, drawer operation and loaded stack strength have not been physically tested.
