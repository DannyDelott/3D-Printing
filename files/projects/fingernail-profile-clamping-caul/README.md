# Fingernail-profile clamping caul

A printable clamping caul for veneering the centered, profiled 1-1/4 inch face of a board cut with a Magnate 5869 fingernail router bit.

## Status

Ready for a test print. The CAD and meshes are dimensionally and structurally verified; the remaining proof is a physical fit check against the routed board.

## Files

| File | Purpose |
| --- | --- |
| `models/magnate-5869-caul.3mf` | One print-ready caul |
| `models/magnate-5869-caul.stl` | One portable caul mesh |
| `models/magnate-5869-caul.step` | Editable CAD solid |
| `models/magnate-5869-caul-4-pack.3mf` | Four cauls laid out for one print |
| `models/magnate-5869-caul-4-pack.stl` | Portable four-caul print plate |
| `models/magnate-5869-caul-250mm-2x4-backed.3mf` | Lightweight 250 mm caul used beneath a 2x4 |
| `models/magnate-5869-caul-250mm-2x4-backed.stl` | Portable mesh of the lightweight 250 mm caul |
| `models/magnate-5869-caul-250mm-2x4-backed.step` | Editable CAD solid for the lightweight 250 mm caul |
| `models/interchangeable-profile-jig-tote-grip.3mf` | Print-ready tote grip and clamping saddle |
| `models/interchangeable-profile-jig-tote-grip.stl` | Portable tote-grip mesh |
| `models/interchangeable-profile-jig-tote-grip.step` | Editable tote-grip CAD solid in its use orientation |
| `models/profile-jig-tote-saddle-fit-test.3mf` | Small saddle coupon to verify printer clearance first |
| `models/profile-jig-tote-saddle-fit-test.stl` | Portable fit-coupon mesh |
| `source/generate_caul.py` | Parametric source and verification |
| `source/generate_tote_grip.py` | Tote, saddle, fit coupon, preview, and verification source |
| `source/profile_interface.py` | Shared attachment interface for future profile jigs |

## Fit and dimensions

- Target face: 31.75 mm / 1-1/4 inch wide
- Contact profile: centered 38.10 mm / 1-1/2 inch circular radius
- Crown across the face: 3.465 mm / 0.136 inch
- Caul length along the board: 50.8 mm / 2 inches
- Minimum body thickness at the middle: 19.05 mm / 3/4 inch
- Maximum overall thickness at the two edges: 22.515 mm / 0.886 inch

### 250 mm 2x4-backed version

- Length: exactly 250 mm
- Width: 31.75 mm / 1-1/4 inch
- Minimum thickness at the middle: 4 mm
- Maximum thickness at the edges: 7.465 mm
- Continuous flat top for a 2x4 to distribute clamp pressure
- Continuous profiled contact face with no pockets or pressure gaps
- About 74% less modeled material than stretching the original full-height caul to 250 mm

The 2x4 supplies the longitudinal stiffness, allowing the printed caul to act as a thin profile adapter instead of a standalone beam.

## Interchangeable tote grip

The tote grip drops over the existing 250 mm caul and locks with two screws. Future sanding profiles can attach to the same grip by preserving one small interface:

- 31.75 mm overall mounting width
- 1.5 mm chamfers on both top edges
- At least 7.4 mm of side depth through the mounting area
- A straight mounting section at least 100 mm long

The saddle has 0.50 mm total width clearance. Its 45-degree interior roof seats against the matching caul chamfers, so those chamfers locate the tote laterally and vertically. When seated, the saddle remains at least 1.55 mm above the sanding surface.

### Tote hardware

- 2 × M3 hex nuts; ordinary 5.5 mm across-flats nuts fit the 5.7 mm pockets
- 2 × M3 × 8-10 mm thumb screws or knurled screws

Both nuts press into pockets on the same side of the saddle. Set the tote over the jig, tighten the two screws evenly against the jig's side, and loosen them a turn or two to swap profiles. Nylon-tip screws are optional if avoiding small witness marks on the jig matters.

The profile uses the router bit manufacturer's nominal radius. Cutter sharpening, runout, feed technique, and the actual centering of the cut can introduce small differences, so print one caul before committing to the four-pack.

## Print notes

- The files are already oriented with the broad, flat clamp face on the build plate.
- No supports are needed.
- Use 5-6 walls and about 35-40% infill for a stiff caul.
- PLA is adequate for a room-temperature veneer glue-up; PETG is a little tougher.
- Keep the 3MF/STL at 100% scale in millimeters.

The thin 250 mm version can be printed solid or with 4 walls and 15-20% infill because the 2x4 is the structural backer. Its exact 250 mm length leaves no spare bed length, so disable brims or skirts that would extend beyond the model.

Print the saddle fit coupon before the full tote. The tote mesh is already upright, measures about 39 × 100 × 99.3 mm, and uses a 45-degree internal roof so it needs no support. Use a brim for the tall print, 5 walls, and roughly 25-35% gyroid infill. If the coupon is too tight or loose, change `SADDLE_WIDTH_CLEARANCE` in `source/profile_interface.py` and regenerate before printing the tote.

For glue-up, cover the contact face with packing tape so the caul cannot become part of the project. A thin cork or firm rubber layer can even out print texture; ordinary veneer thickness changes the effective 1-1/2 inch radius by less than a tenth of a millimeter over this face width.

## Provenance

- Designer: Danny Delott with Codex
- Router bit: Magnate 5869 Finger Nail with Center Bearing Router Bit
- Product source: https://www.magnate.net/ProductDetails.asp?ProductCode=5869
- Geometry source: original parametric construction from the manufacturer's published 1-1/2 inch radius and the measured 1-1/4 inch board face
