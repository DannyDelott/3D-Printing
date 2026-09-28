# Sanding plane · tapered lock

Three printed parts: the integral Stanley tote/carrier, a tapered screw knob, and an interchangeable profile shoe. **The tapered coupon passed Danny's physical test with no shifting reported. The full-size shoe and knob now use that same seat.** The carrier is unchanged.

[View assembly, parts and fit coupon](https://dannydelott.github.io/3D-Printing/projects/sanding-plane/)

## Connection and dimensions

Slide the shoe underneath the carrier and align its conical pocket with the knob. Hand-tighten the knob until the matching tapered faces seat. The tip pushes the shoe against the dovetail retaining faces, while the taper locates it along the slide. The blunt tip stays above the pocket floor so the floor cannot bypass the tapered contact. Loosen one full turn to lift the tip clear and slide out the shoe; the knob stays threaded in the carrier during a normal change, but can be fully unscrewed.

| Feature | Dimension |
|---|---|
| Shoe / carrier length | 186 mm each; ends flush |
| Shoe working width / carrier width | 31.75 mm / 40 mm |
| Seat included angle | 90° |
| Pocket mouth / floor diameter | 8 mm / 2 mm |
| Pocket depth | 3 mm |
| Blunt knob tip diameter | 3.2 mm |
| Tip-to-floor gap when seated | 0.6 mm |
| Thread nominal major diameter / pitch | 21.2 mm / 4 mm |
| Thread radial / axial groove allowance | 0.30 mm / 0.20 mm |
| Longitudinal dovetail edge radii | External R0.30 / internal R0.20 mm |
| Starting rail side / cap clearance | 0.25 mm per side / 0.30 mm above cap |

The original Magnate working curve and width are preserved, with a 9 mm minimum profile blank before shoulder relief. The working face is unbroken. A full-length dovetail and 45° shoulder transitions allow rail-down, profile-up shoe printing. The assembly depicts 0.40 mm clearance take-up, not a simulation of deformation or clamping force.

**Use the new tapered shoe and knob together.** The previous straight-pin parts do not form this connection. Your existing full carrier remains reusable; its regenerated mesh was checked vertex-for-vertex and triangle-for-triangle, and the original STL/3MF files were retained.

## Downloads and printing

**Complete build plate:** [Bambu Studio project](print-checks/profile-jig-final-print-plate-supports/profile-jig-final-print-plate-configured.3mf) · [Assembled preview](https://dannydelott.github.io/3D-Printing/projects/sanding-plane/) · [STL](models/profile-jig-final-print-plate.stl) · [Geometry 3MF](models/profile-jig-final-print-plate.3mf).

All three full-size parts are oriented and arranged on one 256 × 256 mm P1S plate, with 8 mm object gaps. The carrier is side-down with supports enabled; the shoe is rail-down/profile-up and the knob crown-down, both with supports disabled. The Bambu project retains three separate objects, one PLA filament, textured PEI, 0.20 mm layers, five walls, 15% infill and printing by layer. **Combined slice: 161.74 g / 3 h 44 min, no warnings.** Generated support extrusion was checked to stay around the carrier. The STL and geometry 3MF do not include printer/support settings; use the Bambu project for the configured build.


| Current part | STL | 3MF | Bambu estimate | Supports |
|---|---|---|---|---|
| 186 mm tapered shoe | [STL](models/profile-jig-profile-up-full-shoe.stl) | [3MF](models/profile-jig-profile-up-full-shoe.3mf) | 40.95 g / 59 min | Off |
| Full tapered knob | [STL](models/profile-jig-profile-up-full-knob.stl) | [3MF](models/profile-jig-profile-up-full-knob.3mf) | 20.44 g / 36 min | Off |
| Unchanged integral tote/carrier | [STL](models/profile-jig-profile-up-full-body.stl) | [3MF](models/profile-jig-profile-up-full-body.3mf) | 100.46 g / 2 h 21 min | On |
| Successful coupon: shoe + knob | [STL](models/profile-jig-taper-lock-coupon-print-plate.stl) | [3MF](models/profile-jig-taper-lock-coupon-print-plate.3mf) | 21.92 g / 39 min | Off |

Print the shoe on its flat rail cap with the shaped sanding profile upward. Print the knob crown-down with the cone upward. The conical pocket closes at 45° to a small 2 mm bridge. The full tote/carrier prints on its side with removable supports. The two-part coupon plate reuses the [existing coupon carrier](models/profile-jig-profile-up-coupon-body.3mf).

New full shoe and knob slices passed Bambu Studio 02.08.02.60 without warnings: P1S / PLA / 0.4 mm nozzle / 0.20 mm layers / five walls / 15% infill. The unchanged carrier retains its verified slice evidence. Public STL/3MF files contain geometry. Configured Bambu projects: [shoe](print-checks/profile-jig-profile-up-full-shoe/profile-jig-profile-up-full-shoe-configured.3mf), [knob](print-checks/profile-jig-profile-up-full-knob/profile-jig-profile-up-full-knob-configured.3mf), [coupon](print-checks/profile-jig-taper-lock-coupon-print-plate/profile-jig-taper-lock-coupon-print-plate-configured.3mf).

## What has been tested

Danny reported that the tapered coupon worked without shifting. Earlier cylindrical pockets (8.6 mm, then 8.3 mm around an 8.0 mm pin) allowed movement; the 8.3 mm version still slid along the dovetail when tightened. The current downloads use the approved taper.

The full tapered design passed solid/mesh validity, assembled collision, seat engagement, tip-floor gap, extra screw travel and released withdrawal checks. The full-sized assembly has not yet been physically tested. Full-tote leverage, comfort, repeated release and long-term wear remain to be checked. Hand-tighten until seated and check retention before sanding.

## Editable source and evidence

- `source/build_full_plate.py` / `source/verify_full_plate.py`: assemble current exported parts without changing their orientation or geometry, package object-specific supports, slice and verify source hashes, bed placement, support toolpaths and live downloads. Evidence: `validation-final-plate.json`.

- `source/generate_profile_up.py`: shared straight/tapered geometry; full sander uses the taper, historical straight coupon remains available.
- `source/generate_taper_lock.py`: successful tapered coupon, exact carrier reuse and seating checks.
- `source/generate_integral_body.py`: supplied Stanley tote import and curved screw-recess fill; no added permanent back block.
- `source/verify_profile_up.py` and `source/verify_taper_lock.py`: watertight exports, STL/3MF correspondence, assembly collisions, slice hashes and live downloads.
- `validation-profile-up.json`, `validation-taper-lock.json` and corresponding `*-exports.json`: dimensions and validation evidence.
- STEP accompanies CAD parts. `profile-jig-profile-up-full-carrier-core.step` excludes the imported mesh tote; the full integral body is provided as STL/3MF.

The tote is Danny's supplied narrow Stanley No. 5 STL by [vikingth0r](https://makerworld.com/en/models/2873652-woodworking-jig-handle-hand-plane-tote-w-mount). Original file and provenance: `source/reference-tote/`.

Rebuild the complete plate from the current part exports with `source/build_full_plate.py`, then run `source/verify_full_plate.py`, using the same CAD Python below.

Regenerate the full-size parts from the project directory:

```sh
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 source/generate_profile_up.py --full-only
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 source/slice_tote.py profile-jig-profile-up-full-shoe
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 source/slice_tote.py profile-jig-profile-up-full-knob
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 source/slice_tote.py profile-jig-profile-up-full-body --supports
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 source/verify_profile_up.py
```

Imported from the completed profile-up sander worktree. The original full carrier, tapered shoe, tapered knob, coupon and configured plate are preserved byte-for-byte; the library assembly STL is derived from the assembled 3MF. The earlier caul and detachable tote remain separate library entries.

## 1/8-inch roundover shoe · R3

[Full shoe and downloads](https://dannydelott.github.io/3D-Printing/projects/sanding-plane/roundover-1-8/) · [Fit coupon](https://dannydelott.github.io/3D-Printing/projects/sanding-plane/roundover-1-8-coupon/) · [Dimensioned datasheet](roundover-1-8/datasheet.html)

R3 adds a cushion allowance while keeping the centered 1/8-inch roundover and 45° sanding position. It retains the **2.5 mm shoulders flared outward 3° per side** (96° opening). The body beyond the shoulders retreats toward the carrier so it clears the adjoining board faces. The dovetail, tapered lock, shoe length and carrier/knob compatibility are unchanged.

The matching bit is the 1/8-inch roundover in the [TOTOWOOD set, ASIN B0C5DVBNLS](https://www.amazon.com/dp/B0C5DVBNLS). The nominal routed radius is 3.175 mm. The printed concave seat is **6.650 mm radius**: 3.175 mm for the wood, **3.175 mm for one layer of [POWERTEC 71014 cushion](https://www.amazon.com/dp/B00NFB81ZC)**, and an assumed **0.30 mm for paper and all adhesive layers**. The cushion thickness is the user-confirmed nominal 1/8 inch; compression under sanding pressure is unmeasured. This assumes a plain quarter-round without a bead or routing shoulder.

**Fit the cushion only inside the curved seat, then apply approximately 5 mm wide sandpaper over it. Leave both shoulders bare.** Start with an approximately 8 mm wide cushion strip, press it into the seat, and trim its installed edges at the arc ends. The cushion's outer arc is 10.45 mm, its nominal mid-thickness arc is 7.95 mm, and the paper backing arc is 5.46 mm; the soft mat must conform between those surfaces. The 8 mm strip is a starting cut, not a verified fit. Keep the paper seated against the cushion and off the adjoining flats. Hold the plane at 45° and sand along the edge.

| Part | Overall size, length × width × height | Bambu estimate |
|---|---|---|
| Full shoe R3 | 186 × 31.75 × 17.62 mm / 7.32 × 1.25 × 0.69 in | 42.80 g / 1 h 5 min |
| Fit coupon R3 | 70 × 31.75 × 17.62 mm / 2.76 × 1.25 × 0.69 in | 16.99 g / 31 min |

Print rail-cap-down with the working profile upward, supports off. Both configured projects use P1S / PLA / 0.4 mm nozzle / 0.20 mm layers / five walls / 15% infill and slice without warnings. Reuse the full carrier and tapered knob for the full shoe; reuse the 70 mm coupon carrier and tapered coupon knob for the coupon.

**R3 has not been physically tested. Print the coupon first and check it on a routed scrap with the intended cushion, adhesive and abrasive under light sanding pressure.** Analytic clearance checks keep the bare shoulders and relieved outer body clear of nominal board flats rotated inward by up to 3° about their tangency points. This is a geometric check, not proof of fit on uneven wood. Pad compression, paper thickness, print accuracy and actual routing still need a physical check. The full 90° abrasive-seat arc retains its exact CAD radius; the rail and pocket match the approved attachment. R1 and R2 files remain as earlier revisions and are no longer the selected downloads.

Rebuild geometry, validation, and the dimensioned datasheet with:

```sh
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 projects/sanding-plane/source/generate_roundover.py
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 projects/sanding-plane/source/slice_tote.py roundover-1-8-r3-shoe
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 projects/sanding-plane/source/slice_tote.py roundover-1-8-r3-coupon
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 projects/sanding-plane/source/build_assembly_previews.py
/Users/danny/Documents/3d/closet-space-saver-hex/.venv/bin/python3 projects/sanding-plane/source/verify_roundover.py
```

`generate_roundover.py` reuses `generate_profile_up.parts` for the attachment. `roundover_datasheet.py` writes the drawing and HTML. `validation-roundover-1-8-r3.json` records geometry checks and file hashes. `verify_roundover.py` independently reads the exported STEP faces, verifies the 90° arc and 2.5 mm / 42° shoulder surfaces, compares configured print geometry, and records slice provenance in `validation-roundover-1-8-r3-exports.json`. Refresh filament estimates and all four roundover thumbnails following `site/README.md`; keep sliced projects and G-code in excluded `work/`.

## Assembly shoe selector

Use the **Shoe profile** cards to choose the Magnate fingernail or 1/8-inch roundover shoe. Assembly selection updates its preview, shoe specifications, instructions, three part downloads, and matching coupon link. **Exploded view** is a checkbox on Assembly and preserves the selected shoe. Switching previews preserves your viewing angle and zoom.

The main navigation is **Assembly, Shoe, Fit coupon, Carrier, and Locking knob**. Shoe and Fit coupon follow the selected profile; Carrier and Locking knob are shared full-size parts. The selection stays in the URL through those pages. Print just the selected shoe when reusing an existing plane, or download all three configured part projects. The combined build plate is available only for the fingernail setup. The roundover coupon downloads separately identify its shoe, 70 mm carrier, and tapered coupon knob.

`source/build_assembly_previews.py` derives each added shoe's viewing meshes from its STEP in assembly coordinates and the approved assembly's unchanged carrier/knob. It checks rail-cap alignment, assembled clearance and three closed bodies, and records source/output hashes in `validation-assembly-previews.json`. New shoes are registered in `site/catalog.json`; see `site/README.md` for the fields and thumbnail workflow. The selector does not change print geometry or establish physical fit.
