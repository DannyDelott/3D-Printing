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
| `source/generate_caul.py` | Parametric source and verification |
| `source/profile_interface.py` | Caul width and top-edge chamfer dimensions |

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

The profile uses the router bit manufacturer's nominal radius. Cutter sharpening, runout, feed technique, and the actual centering of the cut can introduce small differences, so print one caul before committing to the four-pack.

## Print notes

- The files are already oriented with the broad, flat clamp face on the build plate.
- No supports are needed.
- Use 5-6 walls and about 35-40% infill for a stiff caul.
- PLA is adequate for a room-temperature veneer glue-up; PETG is a little tougher.
- Keep the 3MF/STL at 100% scale in millimeters.

The thin 250 mm version can be printed solid or with 4 walls and 15-20% infill because the 2x4 is the structural backer. Its exact 250 mm length leaves no spare bed length, so disable brims or skirts that would extend beyond the model.


For glue-up, cover the contact face with packing tape so the caul cannot become part of the project. A thin cork or firm rubber layer can even out print texture; ordinary veneer thickness changes the effective 1-1/2 inch radius by less than a tenth of a millimeter over this face width.

## Provenance

- Designer: Danny Delott with Codex
- Router bit: Magnate 5869 Finger Nail with Center Bearing Router Bit
- Product source: https://www.magnate.net/ProductDetails.asp?ProductCode=5869
- Geometry source: original parametric construction from the manufacturer's published 1-1/2 inch radius and the measured 1-1/4 inch board face
